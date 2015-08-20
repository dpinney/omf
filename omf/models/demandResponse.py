''' Calculate the costs and benefits of Time of Use (TOU) program from a distribution utility perspective. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, csv, warnings, calendar, math 
from os.path import join as pJoin
from  dateutil.parser import parse
from numpy import npv
from jinja2 import Template
import omf
from omf.models import __metaModel__
from __metaModel__ import *

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder

def calcTimes(schedule):
	''' Part of PRISM. '''
	start_date = datetime.date(2009,schedule["startmonth"],1)
	last_day = calendar.monthrange(2009, schedule["stopmonth"])
	stop_date = datetime.date(2009,schedule["stopmonth"],last_day[1])
	day_count = stop_date - start_date
	schedule['day_count']= day_count.days
	start_index = start_date - datetime.date(2009,1,1)
	schedule['start_index'] = start_index.days * 24
	schedule['stop_index'] = schedule['start_index'] + ((schedule['day_count']+1) * 24) - 1
	schedule['hrs_on_peak'] = (schedule['stophour'] - schedule['starthour']) * schedule['day_count']
	schedule['hrs_off_peak'] = (schedule['day_count'] * 24) - schedule['hrs_on_peak']
	schedule['num_months'] = schedule["stopmonth"]- schedule["startmonth"] + 1
	schedule['num_hours_on'] = schedule['stophour']- schedule['starthour'] + 1
	schedule['num_hours_off'] = (24 - schedule['num_hours_on'])
	schedule['hrs_on_peak_per_month'] = float(schedule['hrs_on_peak']) / float(schedule['num_months'])
	schedule['hrs_off_peak_per_month'] = float(schedule['hrs_off_peak']) / float(schedule['num_months'])

def calcEnergy(energyProfile, schedule, load_profile):
	''' Part of PRISM. '''
	for idx, load in enumerate(load_profile[schedule['start_index']:schedule['stop_index']+1]):
		if ((idx % 24) < schedule['starthour']) or ((idx % 24 > schedule['stophour'])):
			energyProfile['off_peak'] += load
		else:
			energyProfile['on_peak'] += load
		energyProfile['total'] = energyProfile['off_peak'] + energyProfile['on_peak']

def calcOffPeak(rates, energyProfile):
	''' Part of PRISM. '''
	original_bill = rates['flat'] * energyProfile['total']
	rates['off_peak'] = (original_bill - (rates['on_peak'] * energyProfile['on_peak']))/energyProfile['off_peak']

def calcImpactFactors(rates, schedule, elastcity, energyProfile):
	''' Part of PRISM. '''
	impact_factors = dict()
	kWh_per_hr_old_on_peak = energyProfile['on_peak']/schedule['hrs_on_peak_per_month']
	kWh_per_hr_old_off_peak = energyProfile['off_peak']/schedule['hrs_off_peak_per_month']
	log_factor = math.log(kWh_per_hr_old_on_peak/kWh_per_hr_old_off_peak) + elastcity['SubstitutionPriceElasticity']*   \
								(math.log(rates['on_peak']/rates['off_peak']) - math.log(rates['flat']/rates['flat']))
	kWh_per_hr_old_daily = ((kWh_per_hr_old_on_peak * schedule['num_hours_on']) +
								(kWh_per_hr_old_off_peak * schedule['num_hours_off']))/24
	rates['daily_new_peak'] = ((rates['on_peak'] * schedule['num_hours_on'] * kWh_per_hr_old_on_peak) +  \
								(rates['off_peak'] * schedule['num_hours_off'] * kWh_per_hr_old_off_peak))/  \
								((schedule['num_hours_on']*kWh_per_hr_old_on_peak)+(schedule['num_hours_off']*kWh_per_hr_old_off_peak))
	rates['daily_old_peak'] = ((rates['flat'] * schedule['num_hours_on'] * kWh_per_hr_old_on_peak) +  \
								(rates['flat'] * schedule['num_hours_off'] * kWh_per_hr_old_off_peak))/  \
								((schedule['num_hours_on']*kWh_per_hr_old_on_peak)+(schedule['num_hours_off']*kWh_per_hr_old_off_peak))
	kWh_per_hr_new_daily = math.exp(math.log(kWh_per_hr_old_daily) -  \
								(elastcity["DailyPriceElasticity"] * (math.log(rates['daily_old_peak']) - math.log(rates['daily_new_peak']))))
	kWh_per_hr_new_off_peak = ((24/float(schedule['num_hours_off'])) * kWh_per_hr_new_daily)/ \
								(1+((schedule['num_hours_on']/float(schedule['num_hours_off'])) * math.exp(log_factor)))
	kWh_per_hr_new_on_peak = kWh_per_hr_new_off_peak  * math.exp(log_factor)
	kWh_delta_on_peak = kWh_per_hr_new_on_peak - kWh_per_hr_old_on_peak
	kWh_delta_off_peak = kWh_per_hr_new_off_peak - kWh_per_hr_old_off_peak
	impact_factors['on_peak'] = kWh_delta_on_peak/kWh_per_hr_old_on_peak
	impact_factors['off_peak'] = kWh_delta_off_peak/kWh_per_hr_old_off_peak
	return impact_factors

def applyDR(load_profile, rates, schedule, impact_factors):
	''' Part of PRISM. '''
	modifiedLoad = list(load_profile)
	for idx, load in enumerate(load_profile[schedule['start_index']:schedule['stop_index']+1]):
		if ((idx % 24) < schedule['starthour']) or ((idx % 24 > schedule['stophour'])):
			modifiedLoad[idx + schedule['start_index']] = load * (1 + impact_factors['off_peak'])
		else:
			modifiedLoad[idx + schedule['start_index']] = load * (1 + impact_factors['on_peak'])
	return modifiedLoad

def writeCSV(filepath, data):
	outfile = open(filepath, 'wb')
	for row in data:
		outfile.write(str(row) + '\n')
	outfile.close

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"demandResponse.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))	
	except Exception, e:
		pass
	# Check whether model exist or not
	try:
		if not os.path.isdir(modelDir):
			os.makedirs(modelDir)
			inputDict["created"] = str(datetime.datetime.now())
		with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
			json.dump(inputDict, inputFile, indent = 4)
		# Ready to run.
		startTime = datetime.datetime.now()
		outData = {}
		# Get variables.
		lifeSpan = int(inputDict.get("lifeSpan",25))
		lifeYears = range(1, 1 + lifeSpan)
		hours = range(0, 24) 
		DrTechCost = float(inputDict.get('DrPurchInstallCost'))
		demandCharge = float(inputDict.get('DemandChargeCost'))
		retailCost = float(inputDict.get('RetailEnergyCost'))
		AnnDROM = float(inputDict.get('AnnualDROperationCost'))
		SubElas = float(inputDict.get("SubstitutionPriceElasticity")) 
		DayElas= float(inputDict.get("DailyPriceElasticity"))
		wholesaleCost = float(inputDict.get('WholesaleEnergyCost'))
		ManagLoad = float(inputDict.get('LoadunderManagement')) / 100.0
		DiscountRate = float(inputDict.get("DiscountRate")) / 100
		ScalingAnnual = float(inputDict.get("ScalingAnnual"))/ 100
		PeakRate = float(inputDict.get("PeakRate"))
		OffPeakRate = float(inputDict.get("OffPeakRate"))
		startmonth= int(inputDict.get("startMonth"))
		stopmonth = int(inputDict.get("stopMonth"))
		starthour = int(inputDict.get("startHour"))
		stophour = int(inputDict.get("stopHour"))

		OffPeakDailyPrice1 = [OffPeakRate for x in hours[0:starthour]]
		PeakDailyPrice = [PeakRate for x in hours[starthour-1:stophour]]
		OffPeakDailyPrice2 = [OffPeakRate for x in hours[stophour+1:24]]
		ProgramPrices =[]
		ProgramPrices.extend(OffPeakDailyPrice1)
		ProgramPrices.extend(PeakDailyPrice)
		ProgramPrices.extend(OffPeakDailyPrice2)

		# Setting up the demand curve.
		with open(pJoin(modelDir,"demand.csv"),"w") as demandFile:
			demandFile.write(inputDict['demandCurve'])
		outData['fileName'] = inputDict.get("fileName", 0)
		demandList = [{'datetime': parse(row['timestamp']), 'power': float(row['power'])} for row in csv.DictReader(open(pJoin(modelDir,"demand.csv")))]
		demandCurve = [x['power'] for x in demandList]
		outData['startDate'] = demandList[0]['datetime'].isoformat()

		# Run the PRISM model.
		schedule = {"startmonth": startmonth, "starthour": starthour, "stophour": stophour, "stopmonth": stopmonth}
		calcTimes(schedule) # WHY DO THEY MUTATE IN PLACE!?!?
		energyProfile = {'off_peak':0, 'on_peak':0}
		calcEnergy(energyProfile, schedule, demandCurve)
		rates = {'flat': OffPeakRate, 'on_peak': PeakRate}
		calcOffPeak(rates, energyProfile)
		elasticity = {"SubstitutionPriceElasticity": SubElas, "DailyPriceElasticity": DayElas}
		impact_factors = calcImpactFactors(rates, schedule, elasticity, energyProfile)
		fullParticipationModLoad = applyDR(demandCurve, rates, schedule, impact_factors)
		modifiedLoad = [x*ManagLoad+y*(1-ManagLoad) for x,y in zip(fullParticipationModLoad,demandCurve)]	

		# writeCSV('modifiedLoad.csv', modifiedLoad)
		diff = [x-y for x,y in zip(modifiedLoad,demandCurve)]	

		# Demand Before and After Program Plot
		outData['modifiedLoad'] = modifiedLoad
		outData['demandLoad'] = demandCurve
		outData['difference'] = diff

		# Getting the hourly prices for the whole year (8760 prices)
		ProgPricesArrayYear = ProgramPrices*365
		OneYearwholesaleCost = [wholesaleCost for x in range(8760)]	
		AnnualEnergy = sum(demandCurve)
		demandCurveJanuary = max(demandCurve[0:744])
		demandCurveFebruary = max(demandCurve[745:1416])
		demandCurveMarch = max(demandCurve[1417:2160])
		demandCurveApril = max(demandCurve[2161:2880])
		demandCurveMay = max(demandCurve[2881:3624])
		demandCurveJune = max(demandCurve[3625:4344])
		demandCurveJuly = max(demandCurve[4345:5088])
		demandCurveAugust = max(demandCurve[5089:5832])
		demandCurveSeptember = max(demandCurve[5833:6552])
		demandCurveOctober = max(demandCurve[6553:7296])
		demandCurveNovmber = max(demandCurve[6553:7296])
		demandCurveDecember = max(demandCurve[7297:8760])
		maxMontlyDemand = [demandCurveJanuary,demandCurveFebruary,demandCurveMarch,
			demandCurveApril,demandCurveMay,demandCurveJune,demandCurveJuly,
			demandCurveAugust,demandCurveSeptember,demandCurveOctober,
			demandCurveNovmber,demandCurveDecember]
		annualDemandCost = demandCharge * sum(maxMontlyDemand)
		PowerCost = - (AnnualEnergy * wholesaleCost + annualDemandCost)

		# Calculating the maximum montly peaks after applying DR 
		modifiedLoadJanuary = max(modifiedLoad[0:744])
		modifiedLoadFebruary = max(modifiedLoad[745:1416])
		modifiedLoadMarch = max(modifiedLoad[1417:2160])
		modifiedLoadApril = max(modifiedLoad[2161:2880])
		modifiedLoadMay = max(modifiedLoad[2881:3624])
		modifiedLoadJune = max(modifiedLoad[3625:4344])
		modifiedLoadJuly = max(modifiedLoad[4345:5088])
		modifiedLoadAugust = max(modifiedLoad[5089:5832])
		modifiedLoadSeptember = max(modifiedLoad[5833:6552])
		modifiedLoadOctober = max(modifiedLoad[6553:7296])
		modifiedLoadNovmber = max(modifiedLoad[6553:7296])
		modifiedLoadDecember = max(modifiedLoad[7297:8760])	
		maxMontlyDemandDR = [modifiedLoadJanuary,modifiedLoadFebruary,modifiedLoadMarch,
			modifiedLoadApril,modifiedLoadMay,modifiedLoadJune,modifiedLoadJuly,
			modifiedLoadAugust,modifiedLoadSeptember,modifiedLoadOctober,
			modifiedLoadNovmber,modifiedLoadDecember]

		# Calculating the Base Case Profit
		EnergySale = sum(demandCurve) * retailCost
		EnergyCost = sum(demandCurve) * wholesaleCost
		PeakDemandCharge = sum([x*demandCharge for x in maxMontlyDemand])	
		BaseCaseProfit = EnergySale - EnergyCost - PeakDemandCharge

		# Calculating the DR Case Profit
		EnergySaleDR = sum([z[0]*z[1] for z in zip(modifiedLoad,ProgPricesArrayYear)])
		PeakDemandChargeDR = sum([x*demandCharge for x in maxMontlyDemandDR])	  
		energyCostDR = sum(modifiedLoad) * wholesaleCost
		DRCaseProfit = EnergySaleDR - PeakDemandChargeDR

		# Outputs of First Year Financial Impact table.
		outData["BaseCase"] = [AnnualEnergy, EnergySale, abs(EnergyCost), PeakDemandCharge, 0]
		outData["DRCase"] = [sum(modifiedLoad),EnergySaleDR, abs(energyCostDR), PeakDemandChargeDR, DrTechCost]

		# Calculating the Benefit Cashflow and Total benefit
		energySaleDRyear = [x*y for x,y in zip(ProgPricesArrayYear, demandCurve)] 
		oneYearRetail = [retailCost for x in range(8760)]
		energySaleArray = [x*y for x,y in zip(oneYearRetail, demandCurve)]
		energySaleChange = sum(energySaleDRyear) - sum(energySaleArray)
		peakDemandRed = PeakDemandCharge - PeakDemandChargeDR

		# Calculating the Purchase Cost, Operation and Maint. Cost and Total Cost
		outData["AnnualOpCost"] = [- AnnDROM for x in lifeYears[0:]]
		LifetimeOperationCost = (sum(outData["AnnualOpCost"]))
		outData["LifetimeOperationCost"] = abs(LifetimeOperationCost)
		outData["lifePurchaseCosts"] = [-1.0 * DrTechCost] + [0 for x in lifeYears[1:]]
		outData['TotalCost'] = abs(outData["LifetimeOperationCost"] + DrTechCost)

		# Outputs of the Program Lifetime Cash Flow figure
		outData["EnergySaleChangeBenefit"] = [energySaleChange * ScalingAnnual ** x for x in range(lifeSpan)]
		outData["PeakDemandReduction"] = [peakDemandRed * ScalingAnnual ** x for x in range(lifeSpan)]
		BenefitCurve = [x+y for x,y in zip(outData["EnergySaleChangeBenefit"], outData["PeakDemandReduction"])]
		outData["TotalBenefit"] = sum(BenefitCurve)
		outData["BenefittoCostRatio"] = float(outData["TotalBenefit"] / outData["TotalCost"]) 
		netBenefit = [x+y+z for x,y,z in zip(outData["AnnualOpCost"],outData["lifePurchaseCosts"],BenefitCurve)]
		outData["npv"] = npv(DiscountRate, netBenefit)
		outData["cumulativeNetBenefit"] = [sum(netBenefit[0:i+1]) for i,d in enumerate(netBenefit)]
		outData["SimplePaybackPeriod"] = DrTechCost / (outData["TotalBenefit"] / lifeSpan)

		# Stdout/stderr.
		outData["stdout"] = "Success"
		outData["stderr"] = ""

		# Write the output.
		with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
			json.dump(outData, outFile, indent=4)

		# Update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
	except:
		# If input range wasn't valid delete output, write error to disk.
		thisErr = traceback.format_exc()
		print 'ERROR IN MODEL', modelDir, thisErr
		inputDict['stderr'] = thisErr
		with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
		try:
			os.remove(pJoin(modelDir,"allOutputData.json"))
		except Exception, e:
			pass

def cancel(modelDir):
	''' This model runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# Variables Those have been change based on the input in the .html 
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	inData = {
		"modelType":"demandResponse",
		"RetailEnergyCost": "0.1", 
		"WholesaleEnergyCost": "0.07", 
		"demandCurve": open(pJoin(__metaModel__._omfDir,"uploads","OlinBeckenhamScada.csv")).read(), 
		"DrPurchInstallCost": "100000", 
		"runTime": "0:00:03", 
		"SubstitutionPriceElasticity": "-0.09522",
		"DailyPriceElasticity": "-0.02302",
		"DemandChargeCost": "10",
		"DiscountRate":"3",
		"ScalingAnnual":"102",
		"LoadunderManagement":"2",
		"AnnualDROperationCost":"1000",
		"PeakRate": "0.20",
		"OffPeakRate": "0.083",
		"startMonth": "2",
		"stopMonth": "4",
		"startHour": "6",
		"stopHour": "9"}
	modelLoc = pJoin(workDir,"admin","Automated Demand Response Testing")
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	# renderAndShow(template)
	# Run the model.
	run(modelLoc, inData)
	# Show the output.
	renderAndShow(template, modelDir = modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
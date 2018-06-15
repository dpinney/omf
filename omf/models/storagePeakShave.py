''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess, traceback, csv
import multiprocessing
import numpy as np
from os.path import join as pJoin
from  dateutil.parser import parse
from numpy import npv
from jinja2 import Template
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "The storagePeakShave model calculates the value of a distribution utility deploying energy storage based on three possible battery dispatch strategies."

# # NOTE: used for debugging don't delete.
# import matplotlib.pyplot as plt

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName+".html"),"r") as tempFile:
	template = Template(tempFile.read())

def work(modelDir, inputDict):
	''' Model processing done here. '''
	outData = {}
	# Get variables.
	cellCapacity = float(inputDict['cellCapacity'])
	(cellCapacity, dischargeRate, chargeRate, cellQuantity, demandCharge, cellCost) = \
		[float(inputDict[x]) for x in ('cellCapacity', 'dischargeRate', 'chargeRate', 'cellQuantity', 'demandCharge', 'cellCost')]
	battEff	= float(inputDict.get("batteryEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0
	discountRate = float(inputDict.get('discountRate', 2.5)) / 100.0
	retailCost = float(inputDict.get('retailCost', 0.07))
	dodFactor = float(inputDict.get('dodFactor', 85)) / 100.0
	projYears = int(inputDict.get('projYears',10))
	startPeakHour = int(inputDict.get('startPeakHour',18))
	endPeakHour = int(inputDict.get('endPeakHour',24))
	dispatchStrategy = str(inputDict.get('dispatchStrategy'))
	batteryCycleLife = int(inputDict.get('batteryCycleLife',5000))
	# Put demand data in to a file for safe keeping.
	with open(pJoin(modelDir,"demand.csv"),"w") as demandFile:
		demandFile.write(inputDict['demandCurve'])
	# If dispatch is custom, write the strategy to a file in the model directory
	if dispatchStrategy == 'customDispatch':
		with open(pJoin(modelDir,"dispatchStrategy.csv"),"w") as customDispatchFile:
			customDispatchFile.write(inputDict['customDispatchStrategy'])
	# Start running battery simulation.
	battCapacity = cellQuantity * cellCapacity * dodFactor
	battDischarge = cellQuantity * dischargeRate
	battCharge = cellQuantity * chargeRate
	dates = [(datetime.datetime(2011,1,1,0,0) + datetime.timedelta(hours=1)*x).strftime("%m/%d/%Y %H:%M:%S") for x in range(8760)]
	# Most of our data goes inside the dc "table"
	try:
		dc = []
		with open(pJoin(modelDir,"demand.csv")) as inFile:
			reader = csv.reader(inFile)
			x = 0
			for row in reader:
				dc.append({'datetime': parse(dates[x]), 'power': float(row[0])})
				x += 1
			# print dc
			if len(dc) != 8760: raise Exception
	except:
			e = sys.exc_info()[0]
			if str(e) == "<type 'exceptions.SystemExit'>":
				pass
			else:
				errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href = 'https://github.com/dpinney/omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>\nOMF Wiki storagePeakShave - Demand File CSV Format</a>"
				raise Exception(errorMessage)
	for row in dc:
		row['month'] = row['datetime'].month-1
		row['hour'] = row['datetime'].hour
		# row['weekday'] = row['datetime'].weekday() # TODO: figure out why we care about this.
	if dispatchStrategy == "optimal":
		outData['startDate'] = dc[0]['datetime'].isoformat()
		ps = [battDischarge for x in range(12)]
		dcGroupByMonth = [[t['power'] for t in dc if t['datetime'].month-1==x] for x in range(12)]
		monthlyPeakDemand = [max(dcGroupByMonth[x]) for x in range(12)]
		capacityLimited = True
		while capacityLimited:
			battSoC = battCapacity # Battery state of charge; begins full.
			battDoD = [battCapacity for x in range(12)]  # Depth-of-discharge every month, depends on dodFactor.
			for row in dc:
				month = int(row['datetime'].month)-1
				powerUnderPeak  = monthlyPeakDemand[month] - row['power'] - ps[month]
				isCharging = powerUnderPeak > 0
				isDischarging = powerUnderPeak <= 0
				charge = isCharging * min(
					powerUnderPeak * battEff, # Charge rate <= new monthly peak - row['power']
					battCharge, # Charge rate <= battery maximum charging rate.
					battCapacity - battSoC) # Charge rage <= capacity remaining in battery.
				discharge = isDischarging * min(
					abs(powerUnderPeak), # Discharge rate <= new monthly peak - row['power']
					abs(battDischarge), # Discharge rate <= battery maximum charging rate.
					abs(battSoC+.001)) # Discharge rate <= capacity remaining in battery.
				# (Dis)charge battery
				battSoC += charge
				battSoC -= discharge
				# Update minimum state-of-charge for this month.
				battDoD[month] = min(battSoC,battDoD[month])
				row['netpower'] = row['power'] + charge/battEff - discharge
				row['battSoC'] = battSoC
			capacityLimited = min(battDoD) < 0
			ps = [ps[month]-(battDoD[month] < 0) for month in range(12)]
		peakShaveSum = sum(ps)
	elif dispatchStrategy == "daily":
		outData['startDate'] = dc[0]['datetime'].isoformat()
		battSoC = battCapacity
		for row in dc:
			month = int(row['datetime'].month)-1
			discharge = min(battDischarge,battSoC)
			charge = min(battCharge, battCapacity-battSoC)
			#If hour is within peak hours and the battery has charge
			if row['hour'] >= startPeakHour and row['hour'] <= endPeakHour and battSoC >= 0:
				row['netpower'] = row['power'] - discharge
				battSoC -= discharge
			else:
			#If hour is outside peak hours and the battery isnt fully charged, charge it
				if battSoC < battCapacity:
					battSoC += charge
					row['netpower'] = row['power'] + charge/battEff
				else:
					row['netpower'] = row['power']
			row['battSoC'] = battSoC
		dcGroupByMonth = [[t['power'] for t in dc if t['datetime'].month-1==x] for x in range(12)]
		simpleDCGroupByMonth = [[t for t in dc if t['datetime'].month-1==x] for x in range(12)]
		#Finding rows with max power
		monthlyPeakDemand =  [max(dVals, key=lambda x: x['power']) for dVals in simpleDCGroupByMonth]
		ps = []
		#Determining monthly peak shave
		for row in monthlyPeakDemand:
			ps.append(row['power']-row['netpower'])
		peakShaveSum = sum(ps)
	else: # Custom dispatch.
		try:
			with open(pJoin(modelDir,'dispatchStrategy.csv')) as strategyFile:
				reader = csv.DictReader(strategyFile)
				rowCount = 0
				for i, row in enumerate(reader):
					dc[i]['dispatch'] = int(row['dispatch'])
					rowCount+=1
				if rowCount!= 8760: raise Exception
		except:
			e = sys.exc_info()[0]
			if str(e) == "<type 'exceptions.SystemExit'>":
				pass
			else:
				errorMessage = "Dispatch Strategy file is in an incorrect format. Please see valid format definition at <a target = '_blank' href = 'https://github.com/dpinney/omf/wiki/Models-~-storagePeakShave#custom-dispatch-strategy-file-csv-format'>\nOMF Wiki storagePeakShave - Custom Dispatch Strategy File Format</a>"
				raise Exception(errorMessage)
		outData['startDate'] = dc[0]['datetime'].isoformat()
		battSoC = battCapacity
		for row in dc:
			month = int(row['datetime'].month) - 1
			discharge = min(battDischarge, battSoC)
			charge = min(battCharge, battCapacity - battSoC)
			# If there is a 1 in the dispatch strategy csv, the battery discharges
			if row['dispatch'] == 1:
				row['netpower'] = row['power'] - discharge
				battSoC -= discharge
			else:
				# Otherwise charge the battery.
				if battSoC < battCapacity:
					battSoC += charge
					row['netpower'] = row['power'] + charge/battEff
				else:
					row['netpower'] = row['power']
			row['battSoC'] = battSoC
		dcGroupByMonth = [[t['power'] for t in dc if t['datetime'].month-1==x] for x in range(12)]
		# Calculating how much the battery discharges each month
		dischargeGroupByMonth = [[t['netpower']-t['power'] for t in dc if t['datetime'].month-1==x] for x in range(12)]
		simpleDCGroupByMonth = [[t for t in dc if t['datetime'].month-1==x] for x in range(12)]
		monthlyPeakDemand =  [max(dVals, key=lambda x: x['power']) for dVals in simpleDCGroupByMonth]
		ps = []
		for row in monthlyPeakDemand:
			ps.append(row['power']-row['netpower'])
		peakShaveSum = sum(ps)
		chargePerMonth = []
		# Calculate how much the battery charges per year for cashFlowCurve, SPP calculation, kWhToRecharge
		for row in dischargeGroupByMonth:
			total = 0
			for num in row:
				if num > 0:
					total += num
			chargePerMonth.append(total)
		totalYearlyCharge = sum(chargePerMonth)
	# Calculations
	dcThroughTheMonth = [[t for t in iter(dc) if t['datetime'].month-1<=x] for x in range(12)]
	hoursThroughTheMonth = [len(dcThroughTheMonth[month]) for month in range(12)]
	if peakShaveSum == 0:
		peakShaveSum = -1
		#peakShave of 0 means no benefits, so make it -1
	if dispatchStrategy == 'optimal':
		cashFlowCurve = [peakShaveSum * demandCharge for year in range(projYears)]
		outData['SPP'] = (cellCost*cellQuantity)/(peakShaveSum*demandCharge)
	elif dispatchStrategy == 'daily':
		#cashFlowCurve is $ in from peak shaving minus the cost to recharge the battery every day of the year
		cashFlowCurve = [(peakShaveSum * demandCharge)-(battCapacity*365*retailCost) for year in range(projYears)]
		#simplePayback is also affected by the cost to recharge the battery every day of the year
		outData['SPP'] = (cellCost*cellQuantity)/((peakShaveSum*demandCharge)-(battCapacity*365*retailCost))
	else:
		cashFlowCurve = [(peakShaveSum * demandCharge)-(totalYearlyCharge*retailCost) for year in range(projYears)]
		outData['SPP'] = (cellCost*cellQuantity)/((peakShaveSum*demandCharge)-(totalYearlyCharge*retailCost))		
	cashFlowCurve[0]-= (cellCost * cellQuantity)
	outData['netCashflow'] = cashFlowCurve
	outData['cumulativeCashflow'] = [sum(cashFlowCurve[0:i+1]) for i,d in enumerate(cashFlowCurve)]
	outData['NPV'] = npv(discountRate, cashFlowCurve)
	outData['demand'] = [t['power']*1000.0 for t in dc]
	outData['demandAfterBattery'] = [t['netpower']*1000.0 for t in dc]
	outData['batterySoc'] = [t['battSoC']/battCapacity*100.0*dodFactor + (100-100*dodFactor) for t in dc]
	# Estimate number of cyles the battery went through.
	SoC = outData['batterySoc']
	cycleEquivalents = sum([SoC[i]-SoC[i+1] for i,x in enumerate(SoC[0:-1]) if SoC[i+1] < SoC[i]]) / 100.0
	outData['cycleEquivalents'] = cycleEquivalents
	outData['batteryLife'] = batteryCycleLife/cycleEquivalents
	# # Output some matplotlib results as well.
	# plt.plot([t['power'] for t in dc])
	# plt.plot([t['netpower'] for t in dc])
	# plt.plot([t['battSoC'] for t in dc])
	# for month in range(12):
	#   plt.axvline(hoursThroughTheMonth[month])
	# plt.savefig(pJoin(modelDir,"plot.png"))
	# Summary of results
	outData['months'] = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
	totMonNum = []
	monthlyDemand = []
	for x in range (0, len(dcGroupByMonth)):
		totMonNum.append(sum(dcGroupByMonth[x])/1000)
		monthlyDemand.append([outData['months'][x], totMonNum[x]])
	outData['monthlyDemand'] = totMonNum
	outData['ps'] = ps
	outData['monthlyDemandRed'] = [totMonNum - ps for totMonNum, ps in zip(totMonNum, ps)]
	outData['benefitMonthly'] = [x * demandCharge for x in outData['ps']]
	if dispatchStrategy == 'optimal':
		outData['kWhtoRecharge'] = [battCapacity - x for x in outData['ps']]
	elif dispatchStrategy == 'daily':
		#Battery is dispatched and charged everyday, ~30 days per month
		kWhtoRecharge = [battCapacity * 30 -x for x in range(12)]
		outData['kWhtoRecharge'] = kWhtoRecharge
	else:
		#
		kWhtoRecharge = []
		for num in chargePerMonth:
			kWhtoRecharge.append(num)
		outData['kWhtoRecharge'] = kWhtoRecharge
	outData['costtoRecharge'] = [retailCost * x for x in outData['kWhtoRecharge']]
	benefitMonthly = outData['benefitMonthly']
	costtoRecharge = outData['costtoRecharge']
	outData['benefitNet'] = [benefitMonthly - costtoRecharge for benefitMonthly, costtoRecharge in zip(benefitMonthly, costtoRecharge)]
	# Battery KW
	demandAfterBattery = outData['demandAfterBattery']
	demand = outData['demand']
	outData['batteryDischargekW'] = [demand - demandAfterBattery for demand, demandAfterBattery in zip(demand, demandAfterBattery)]
	outData['batteryDischargekWMax'] = max(outData['batteryDischargekW'])
	battCostPerCycle =  cellQuantity * cellCapacity * cellCost / batteryCycleLife
	lcoeTotCost = (cycleEquivalents *  cellQuantity * cellCapacity * retailCost) + (battCostPerCycle * cycleEquivalents)
	loceTotEnergy = cycleEquivalents * cellQuantity * cellCapacity
	LCOE = lcoeTotCost / loceTotEnergy
	outData['LCOE'] = LCOE
	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	# Return the output.
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		'batteryEfficiency': '92',
		'inverterEfficiency': '97.5',
		'cellCapacity': '7',
		'discountRate': '2.5',
		'created': '2015-06-12 17:20:39.308239',
		'dischargeRate': '5',
		'modelType': modelName,
		'chargeRate': '5000',
		'demandCurve': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','FrankScadaValidCSV_Copy.csv')).read(),
		'fileName': 'FrankScadaValidCSV_Copy.csv',
		'dispatchStrategy': 'optimal',
		'cellCost': '7140',
		'cellQuantity': '10',
		'runTime': '0:00:03',
		'projYears': '15',
		'demandCharge': '20',
		'dodFactor':'100',
		'retailCost': '0.06',
		'startPeakHour': '18',
		'endPeakHour': '22',
		'batteryCycleLife': '5000'
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc, json.load(open(modelLoc + '/allInputData.json')))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
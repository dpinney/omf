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
tooltip = "The storageArbitrage model calculates the costs and benefits of using energy storage to buy energy in times of low prices and sell that energy at times of high prices."

# # NOTE: used for debugging don't delete.
# import matplotlib.pyplot as plt

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName+".html"),"r") as tempFile:
	template = Template(tempFile.read())

def work(modelDir, inputDict):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Delete output file every run if it exists
	outData = {}
	# Get variables.
	cellCapacity = float(inputDict['cellCapacity'])
	(cellCapacity, dischargeRate, chargeRate, cellQuantity, cellCost) = \
		[float(inputDict[x]) for x in ('cellCapacity', 'dischargeRate', 'chargeRate', 'cellQuantity', 'cellCost')]
	battEff	= float(inputDict.get("batteryEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0
	discountRate = float(inputDict.get('discountRate', 2.5)) / 100.0
	dodFactor = float(inputDict.get('dodFactor', 85)) / 100.0
	projYears = int(inputDict.get('projYears',10))
	dischargePriceThreshold	= float(inputDict.get('dischargePriceThreshold',0.15))
	chargePriceThreshold = float(inputDict.get('chargePriceThreshold',0.07))
	batteryCycleLife = int(inputDict.get('batteryCycleLife',5000))
	# Put demand data in to a file for safe keeping.
	with open(pJoin(modelDir,"demand.csv"),"w") as demandFile:
		demandFile.write(inputDict['demandCurve'])
	with open(pJoin(modelDir,"priceCurve.csv"),"w") as priceCurve:
		priceCurve.write(inputDict['priceCurve'])
	# Start running battery simulation.
	battCapacity = cellQuantity * cellCapacity * dodFactor
	battDischarge = cellQuantity * dischargeRate
	battCharge = cellQuantity * chargeRate
	# Most of our data goes inside the dc "table"
	dates = [(datetime.datetime(2011,1,1,0,0) + datetime.timedelta(hours=1)*x).strftime("%m/%d/%Y %H:%M:%S") for x in range(8760)]
	try:
		dc = []
		with open(pJoin(modelDir,"demand.csv")) as inFile:
			reader = csv.reader(inFile)
			x = 0
			for row in reader:
				dc.append({'datetime': parse(dates[x]), 'power': float(row[0])})
				x += 1
			if len(dc)!=8760: raise Exception
	except:
			e = sys.exc_info()[0]
			if str(e) == "<type 'exceptions.SystemExit'>":
				pass
			else:
				errorMessage = "Demand CSV file is incorrect format."
				raise Exception(errorMessage)
	#Add price to dc table
	try:
		with open(pJoin(modelDir,'priceCurve.csv')) as priceFile:
			reader = csv.reader(priceFile)
			rowCount = 0
			i = 0
	 		for row in reader:
	 			dc[i]['price'] = float(row[0])
	 			i += 1
	 		if i!= 8760: raise Exception
	except:
	 	e = sys.exc_info()[0]
		if str(e) == "<type 'exceptions.SystemExit'>":
			pass
		else:
			errorMessage = "Price Curve File is in an incorrect format."
			raise Exception(errorMessage)
	for row in dc:
		row['month'] = row['datetime'].month-1
		row['hour'] = row['datetime'].hour
		# row['weekday'] = row['datetime'].weekday() # TODO: figure out why we care about this.
	battSoC = battCapacity
	for row in dc:
		outData['startDate'] = dc[0]['datetime'].isoformat()
		month = int(row['datetime'].month)-1
		discharge = min(battDischarge,battSoC)
		charge = min(battCharge, battCapacity-battSoC)
		#If price of energy is above price threshold and battery has charge, discharge battery
		if row['price'] >= dischargePriceThreshold and battSoC > 0:
			row['netpower'] = row['power'] - discharge
			battSoC -= discharge
		#If battery has no charge but price is still above charge threshold, dont charge it
		elif row['price'] > chargePriceThreshold and battSoC == 0:
			row['netpower'] = row['power']
		elif row['price'] <= chargePriceThreshold and battSoC < battCapacity:
			row['netpower'] = row['power'] + charge/battEff
			battSoC += charge
		else:
			row['netpower'] = row['power']
		row['battSoC'] = battSoC
	dischargeGroupByMonth = [[t['netpower']-t['power'] for t in dc if t['datetime'].month-1==x] for x in range(12)]
	dcGroupByMonth = [[t for t in dc if t['datetime'].month-1==x] for x in range(12)]
	monthlyCharge = []
	monthlyDischarge = []
	#Calculate the monthly energy discharged/charged 
	for row in dischargeGroupByMonth:
		chargePower = 0
		dischargePower = 0
		for n in row:
			if n > 0:
				chargePower += n
			else:
				dischargePower += n * -1
		monthlyCharge.append(chargePower)
		monthlyDischarge.append(dischargePower)
	monthlyDischargeSavings = []
	monthlyChargeCost = []
	#Calculate the monthly cost to charge and savings by discharging 
	for row in dcGroupByMonth:
		chargeCost = 0
		dischargeSavings = 0
		for n in row:
			if n['netpower'] - n['power'] > 0:
				chargeCost += (n['netpower'] - n['power']) * n['price']
			if n['netpower'] - n['power'] < 0:
				dischargeSavings += (n['netpower'] - n['power']) * n['price'] * -1
		monthlyDischargeSavings.append(dischargeSavings)
		monthlyChargeCost.append(chargeCost)
	yearlyDischargeSavings = sum(monthlyDischargeSavings)
	yearlyChargeCost = sum(monthlyChargeCost)
	cashFlowCurve = [yearlyDischargeSavings - yearlyChargeCost for year in range(projYears)]
	outData['demand'] = [t['power']*1000.0 for t in dc]
	outData['demandAfterBattery'] = [t['netpower']*1000.0 for t in dc]
	demandAfterBattery = outData['demandAfterBattery']
	demand = outData['demand']
	outData['batteryDischargekW'] = [demand - demandAfterBattery for demand, demandAfterBattery in zip(demand, demandAfterBattery)]
	batteryDischargekWMax = max(outData['batteryDischargekW'])
	outData['batteryDischargekWMax'] = batteryDischargekWMax
	outData['energyOffset'] = monthlyDischarge
	outData['kWhtoRecharge'] = monthlyCharge
	outData['costToRecharge'] = monthlyChargeCost
	outData['dischargeSavings'] = monthlyDischargeSavings
	outData['benefitNet'] = [monthlyDischargeSavings - monthlyChargeCost for monthlyChargeCost, monthlyDischargeSavings in zip(monthlyChargeCost, monthlyDischargeSavings)]
	outData['batterySoc'] = [t['battSoC']/battCapacity*100.0*dodFactor + (100-100*dodFactor) for t in dc]
	SoC = outData['batterySoc']
	cycleEquivalents = sum([SoC[i]-SoC[i+1] for i,x in enumerate(SoC[0:-1]) if SoC[i+1] < SoC[i]]) / 100.0
	outData['cycleEquivalents'] = cycleEquivalents
	outData['batteryLife'] = batteryCycleLife/cycleEquivalents
	cashFlowCurve[0]-= (cellCost * cellQuantity)
	outData['netCashflow'] = cashFlowCurve
	outData['cumulativeCashflow'] = [sum(cashFlowCurve[0:i+1]) for i,d in enumerate(cashFlowCurve)]
	outData['NPV'] = npv(discountRate, cashFlowCurve)
	outData['SPP'] = (cellCost*cellQuantity)/(yearlyDischargeSavings - yearlyChargeCost)
	battCostPerCycle =  cellQuantity * cellCapacity  * cellCost / batteryCycleLife
	lcoeTotCost = (cycleEquivalents * cellQuantity * cellCapacity * chargePriceThreshold) + (battCostPerCycle * cycleEquivalents)
	loceTotEnergy = cycleEquivalents * cellCapacity * cellQuantity
	LCOE = lcoeTotCost / loceTotEnergy
	outData['LCOE'] = LCOE
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"batteryEfficiency": "92",
		"inverterEfficiency": "97.5",
		"cellCapacity": "7",
		"discountRate": "2.5",
		"created": "2015-06-12 17:20:39.308239",
		"dischargeRate": "5",
		"modelType": modelName,
		"chargeRate": "5",
		"demandCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","FrankScadaValidCSV_Copy.csv")).read(),
		"fileName": "FrankScadaValidCSV_Copy.csv",
		"priceCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","priceCurve_Copy.csv")).read(),
		"fileNamed":"priceCurve_Copy.csv",
		"cellCost": "7140",
		"cellQuantity": "10",
		"runTime": "0:00:03",
		"projYears": "15",
		"chargePriceThreshold": "0.07",
		"dischargePriceThreshold":"0.15",
		"dodFactor":"100",
		"batteryCycleLife": "5000"
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
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
	runForeground(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
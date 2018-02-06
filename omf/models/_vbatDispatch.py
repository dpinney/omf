''' VBAT Evaluation
Requirements: GNU octave
'''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, math
import multiprocessing, platform,collections
from os.path import join as pJoin
from jinja2 import Template
import __neoMetaModel__
from __neoMetaModel__ import *
import random
import csv
import matplotlib.pyplot as plt
import numpy as np
	
# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "Calculate the virtual battery capacity for a collection of thermostically controlled loads."

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName + ".html"),"r") as tempFile:
	template = Template(tempFile.read())

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	outData = {}
	# Run VBAT code.
	vbatPath = os.path.join(omf.omfDir,'solvers','vbat')
	plat = platform.system()
	if inputDict['load_type'] == '4':
		numDevices = int(inputDict['number_devices'])
		if numDevices == 1:
			runTimeDuration = 2
		elif numDevices > 1 and numDevices < 10:
			runTimeDuration = 3.5
		elif numDevices >= 10 and numDevices < 50:
			runTimeDuration = 6
		else :
			runTimeDuration = (numDevices-numDevices%50)*.2
		inputDict['runTimeEstimate'] = 'This configuration will take an approximate run time of: ' + str(runTimeDuration) +' minutes.'
		#HACK: dump input immediately to show runtime estimate.
	else:
		inputDict['runTimeEstimate'] = 'This configuration will take an approximate run time of: 0.5 minutes.'
	with open(pJoin(modelDir,'allInputData.json'), 'w') as dictFile:
		json.dump(inputDict, dictFile, indent=4)
	if plat == 'Windows':
		octBin = 'c:\\Octave\\Octave-4.2.1\\bin\\octave-cli'
	elif plat == 'Darwin':
		octBin = 'octave --no-gui'
	else:
		octBin = 'octave --no-window-system'
	with open(pJoin(modelDir,"temp.csv"),"w") as tempFile:
		tempFile.write(inputDict['tempCurve'])
	try:
		with open(pJoin(modelDir,"temp.csv")) as inFile:
			reader = csv.DictReader(inFile)
			tempFilePath = modelDir
	except:
		errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href = 'https://github.com/dpinney/omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>\nOMF Wiki storagePeakShave - Demand File CSV Format</a>"
		raise Exception(errorMessage)
	command = 'OCTBIN --eval "addpath(genpath(\'FULLPATH\'));VB_func(ARGS)"'\
	 	.replace('FULLPATH', vbatPath)\
	 	.replace('OCTBIN',octBin)\
		.replace('ARGS', "'" + str(tempFilePath) + "/temp.csv'," + inputDict['load_type'] +',[' + inputDict['capacitance'] + ','+ inputDict['resistance'] + 
			',' + inputDict['power'] + ',' + inputDict['cop'] + ',' + inputDict['deadband'] + ',' + inputDict['setpoint'] + ',' +
			inputDict['number_devices'] + ']')
	demandList = []
	demandAdjustedList = []
	dates = []
	with open(pJoin(modelDir,"demand.csv"),"w") as demandFile:
		demandFile.write(inputDict['demandCurve'].replace('\r',''))
	try:
		with open(pJoin(modelDir,"demand.csv")) as inFile:
			reader = csv.reader(inFile)
			for row in reader:
				demandList.append(float(row[0]))
	 		if len(demandList) != 8760:
	 			raise Exception
	except:
		errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href = 'https://github.com/dpinney/omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>\nOMF Wiki storagePeakShave - Demand File CSV Format</a>"
		raise Exception(errorMessage)
	peakDemand = [0]*12
	peakAdjustedDemand = [0]*12
	energyMonthly = [0]*12
	energyAdjustedMonthly = [0]*12
	energyCost = [0]*12
	energyCostAdjusted = [0]*12
	demandCharge = [0]*12
	demandChargeAdjusted = [0]*12
	totalCost = [0]*12
	totalCostAdjusted = [0]*12
	savings = [0]*12
	cashFlow = 0
	cashFlowList = [0]*int(inputDict["projectionLength"])
	cumulativeCashflow = [0]*int(inputDict["projectionLength"])
	NPV = 0
	#netCashflow = [0]*(int(inputDict["projectionLength"])+1)
	calendar = collections.OrderedDict()
	calendar['1'] = 31
	calendar['2'] = 28
	calendar['3'] = 31
	calendar['4'] = 30
	calendar['5'] = 31
	calendar['6'] = 30
	calendar['7'] = 31
	calendar['8'] = 31
	calendar['9'] = 30
	calendar['10'] = 31
	calendar['11'] = 30
	calendar['12'] = 31
	dayCount = -1
	for monthNum in calendar:					#month number in year
		for x in range(calendar[monthNum]):		#day number-1 in number of days in month
			for y in range(24):					#hour of the day-1 out of 24
				dayCount += 1					#hour out of the year-1 
				if demandList[dayCount] > peakDemand[int(monthNum)-1]:
					peakDemand[int(monthNum)-1] = demandList[dayCount]
				energyMonthly[int(monthNum)-1] += demandList[dayCount]
	if plat == 'Windows':
		# myOut = subprocess.check_output(command, shell=True, cwd=vbatPath)
		proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		with open(pJoin(modelDir, "PID.txt"),"w") as pidFile:
			pidFile.write(str(proc.pid))
		(myOut, err) = proc.communicate()
	else:
		proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
		with open(pJoin(modelDir, "PID.txt"),"w") as pidFile:
			pidFile.write(str(proc.pid))
		(myOut, err) = proc.communicate()
	try:
		P_lower = myOut.partition("P_lower =\n\n")[2]
		P_lower = P_lower.partition("\n\nn")[0]
		P_lower = map(float,P_lower.split('\n'))
		P_upper = myOut.partition("P_upper =\n\n")[2]
		P_upper = P_upper.partition("\n\nn")[0]
		P_upper = map(float,P_upper.split('\n'))
		E_UL = myOut.partition("E_UL =\n\n")[2]
		E_UL = E_UL.partition("\n\n")[0]
		E_UL = map(float,E_UL.split('\n'))
	except:
		raise Exception('Parsing error, check power data')
	outData["minPowerSeries"] = [-1*x for x in P_lower]
	outData["maxPowerSeries"] = P_upper
	outData["minEnergySeries"] = [-1*x for x in E_UL]
	outData["maxEnergySeries"] = E_UL
	for x,y in zip(E_UL,demandList):
		demandAdjustedList.append(y-x)
	dayCount = -1
	for monthNum in calendar:					#month number in year
		for x in range(calendar[monthNum]):		#day number-1 in number of days in month
			for y in range(24):					#hour of the day-1 out of 24
				dayCount += 1					#hour out of the year-1 
				if demandAdjustedList[dayCount] > peakAdjustedDemand[int(monthNum)-1]:
					peakAdjustedDemand[int(monthNum)-1] = demandAdjustedList[dayCount]
				energyAdjustedMonthly[int(monthNum)-1] += demandAdjustedList[dayCount]
	rms = 0
	for each in P_lower:
		rms = rms + (each**2)**0.5
	for each in P_upper:
		rms = rms + (each**2)**0.5
	if rms == 0:
		outData["dataCheck"] = 'VBAT returns no values for your inputs'
	else:
		outData["dataCheck"] = ''
	outData["demand"] = demandList
	outData["peakDemand"] = peakDemand
	outData["energyMonthly"] = energyMonthly
	outData["demandAdjusted"] = demandAdjustedList
	outData["peakAdjustedDemand"] = peakAdjustedDemand
	outData["energyAdjustedMonthly"] = energyAdjustedMonthly
	for x in range(12):
		energyCost[x] = energyMonthly[x]*float(inputDict["electricityCost"])
		energyCostAdjusted[x] = energyAdjustedMonthly[x]*float(inputDict["electricityCost"])
		demandCharge[x] = peakDemand[x]*float(inputDict["demandChargeCost"])
		demandChargeAdjusted[x] = peakAdjustedDemand[x]*float(inputDict["demandChargeCost"])
		totalCost[x] = energyCost[x] + demandCharge[x]
		totalCostAdjusted[x] = energyCostAdjusted[x] + demandChargeAdjusted[x]
		savings[x] = totalCost[x] - totalCostAdjusted[x]
		cashFlow += savings[x]
	cashFlowList[0] = cashFlow
	if cashFlow ==0:
		SPP = 0
	else:
		SPP = (float(inputDict["unitDeviceCost"])+float(inputDict["unitUpkeepCost"]))*float(inputDict["number_devices"])/cashFlow
	for x in range(int(inputDict["projectionLength"])):
		if x >0:
			cashFlowList[x] = (cashFlowList[x-1])/(1+float(inputDict["discountRate"])/100)
	for x in cashFlowList:
		NPV +=x
	NPV -= float(inputDict["unitDeviceCost"])*float(inputDict["number_devices"])
	cashFlowList[0] -= float(inputDict["unitDeviceCost"])*float(inputDict["number_devices"])
	for x in range(int(inputDict["projectionLength"])):
		if x == 0:
			cumulativeCashflow[x] = cashFlowList[x]
		else:
			cumulativeCashflow[x] = cumulativeCashflow[x-1] + cashFlowList[x]
	for x in cumulativeCashflow:
		x -= float(inputDict["unitUpkeepCost"])
	for x in cashFlowList:
		x -= float(inputDict["unitUpkeepCost"])
	outData["energyCost"] = energyCost
	outData["energyCostAdjusted"] = energyCostAdjusted
	outData["demandCharge"] = demandCharge
	outData["demandChargeAdjusted"] = demandChargeAdjusted
	outData["totalCost"] = totalCost
	outData["totalCostAdjusted"] = totalCostAdjusted
	outData["savings"] = savings
	outData["NPV"] = NPV
	outData["SPP"] = SPP
	outData["netCashflow"] = cashFlowList
	outData["cumulativeCashflow"] = cumulativeCashflow
	# Stdout/stderr.
	outData["stdout"] = "Success"
	return outData

def carpetPlot(tempData): #tempData is a 8760 list that contains the temperature data to be displayed in a carpet plot
#takes about one minute to run
	calendar = collections.OrderedDict()
	calendar['0'] = 31
	calendar['1'] = 28
	calendar['2'] = 31
	calendar['3'] = 30
	calendar['4'] = 31
	calendar['5'] = 30
	calendar['6'] = 31
	calendar['7'] = 31
	calendar['8'] = 30
	calendar['9'] = 31
	calendar['10'] = 30
	calendar['11'] = 31
	f, axarr = plt.subplots(12, 31, sharex=True, sharey=True)
	f.suptitle('Carpet Plot of VBAT energy potential')
	f.text(0.5, 0.05, 'Days', ha='center', va='center')
	f.text(0.04, 0.5, 'Months', ha='center', va='center', rotation='vertical')
	f.text(0.095,0.86, 'Jan', ha='center', va='center')
	f.text(0.095,0.79, 'Feb', ha='center', va='center')
	f.text(0.095,0.72, 'Mar', ha='center', va='center')
	f.text(0.095,0.66, 'Apr', ha='center', va='center')
	f.text(0.095,0.59, 'May', ha='center', va='center')
	f.text(0.095,0.525, 'Jun', ha='center', va='center')
	f.text(0.095,0.47, 'Jul', ha='center', va='center')
	f.text(0.095,0.40, 'Aug', ha='center', va='center')
	f.text(0.095,0.335, 'Sep', ha='center', va='center')
	f.text(0.095,0.265, 'Oct', ha='center', va='center')
	f.text(0.095,0.195, 'Nov', ha='center', va='center')
	f.text(0.095,0.135, 'Dec', ha='center', va='center')
	dayNum = -24
	for month in calendar:
		for day in range(calendar[month]):
			dayNum += 24
			dayValues = []
			for z in range(24):
				dayValues.append(tempData[dayNum + z])
			axarr[int(month),day].plot(dayValues)
			axarr[int(month),day].axis('off')
	axarr[1,28].plot(0,0)
	axarr[1,29].plot(0,0)
	axarr[1,30].plot(0,0)
	axarr[3,30].plot(0,0)
	axarr[5,30].plot(0,0)
	axarr[8,30].plot(0,0)
	axarr[10,30].plot(0,0)
	axarr[1,28].axis('off')
	axarr[1,29].axis('off')
	axarr[1,30].axis('off')
	axarr[3,30].axis('off')
	axarr[5,30].axis('off')
	axarr[8,30].axis('off')
	axarr[10,30].axis('off')
	plt.savefig('vbatDispatchCarpetPlot.png')

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"load_type": "1",
		"number_devices": "100",
		"power": "5.6",
		"capacitance": "2",
		"resistance": "2",
		"cop": "2.5",
		"setpoint": "22.5",
		"deadband": "0.625",
		"demandChargeCost":"20",
		"electricityCost":"0.06",
		"projectionLength":"15",
		"discountRate":"2",
		"unitDeviceCost":"200",
		"unitUpkeepCost":"5",
		"demandCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","FrankScadaValidVBAT.csv")).read(),
		"tempCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","weatherNoaaTemp.csv")).read(),
		"fileName": "FrankScadaValidVBAT.csv",
		"tempFileName": "weatherNoaaTemp.csv",
		"modelType":modelName}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

def _simpleTest():
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
	_simpleTest ()
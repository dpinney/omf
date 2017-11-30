''' VBAT Evaluation
Requirements: GNU octave
'''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, math
import multiprocessing, platform
from os.path import join as pJoin
from jinja2 import Template
import __neoMetaModel__
from __neoMetaModel__ import *
import random
import csv
	
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
	command = 'OCTBIN --eval "addpath(genpath(\'FULLPATH\'));VB_func(ARGS)"'\
	 	.replace('FULLPATH', vbatPath)\
	 	.replace('OCTBIN',octBin)\
		.replace('ARGS', inputDict['zipcode'] + ',' + inputDict['load_type'] +',[' + inputDict['capacitance'] + ','+ inputDict['resistance'] + 
			',' + inputDict['power'] + ',' + inputDict['cop'] + ',' + inputDict['deadband'] + ',' + inputDict['setpoint'] + ',' +
			inputDict['number_devices'] + ']')
	script_dir = os.path.dirname(os.path.dirname(__file__))
	rel_path = 'static/testFiles/FrankScadaValidCSV.csv'
	abs_file_path = os.path.join(script_dir, rel_path)
	demandList = []
	demandAdjustedList = []
	dates = []
	with open(abs_file_path, 'r') as f:
		for line in f.readlines():
			demand = line.partition(',')[2]
			demand = demand.partition('\n')[0]
			try:
				demand = float(demand)
				demandList.append(demand)
				dates.append(line.partition(' ')[0])
			except:
				print 'Skipped header'
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
	for x in range(8760):
		if demandList[x] > peakDemand[int(dates[x][:2])-1]: #month number, -1 gives the index of peakDemand
			peakDemand[int(dates[x][:2])-1] = demandList[x]
		energyMonthly[int(dates[x][:2])-1] += demandList[x]
	try:
		myOut = subprocess.check_output(command, shell=True, cwd=vbatPath)
		P_lower = myOut.partition("P_lower =\n\n")[2]
		P_lower = P_lower.partition("\n\nn")[0]
		P_lower = map(float,P_lower.split('\n'))
		P_upper = myOut.partition("P_upper =\n\n")[2]
		P_upper = P_upper.partition("\n\nn")[0]
		P_upper = map(float,P_upper.split('\n'))
		E_UL = myOut.partition("E_UL =\n\n")[2]
		E_UL = E_UL.partition("\n\n")[0]
		E_UL = map(float,E_UL.split('\n'))
		for x,y in zip(P_upper,demandList):
			demandAdjustedList.append(y-x)
		for x in range(8760):
			if demandAdjustedList[x] > peakAdjustedDemand[int(dates[x][:2])-1]:
				peakAdjustedDemand[int(dates[x][:2])-1] = demandAdjustedList[x]
			energyAdjustedMonthly[int(dates[x][:2])-1] += demandAdjustedList[x]
		# Format results to go in chart.
		outData["minPowerSeries"] = [-1*x for x in P_lower]
		outData["maxPowerSeries"] = P_upper
		outData["minEnergySeries"] = [-1*x for x in E_UL]
		outData["maxEnergySeries"] = E_UL
		outData["demand"] = demandList
		outData["demandAdjusted"] = demandAdjustedList
		outData["peakDemand"] = peakDemand
		outData["peakAdjustedDemand"] = peakAdjustedDemand
		outData["energyMonthly"] = energyMonthly
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
		outData["netCashflow"] = cashFlowList	#netCashflow
		outData["cumulativeCashflow"] = cumulativeCashflow
		# Stdout/stderr.
		outData["stdout"] = "Success"
		#inputDict["stderr"] = ""
	except:
		outData["stdout"] = "Failure"
		inputDict["stderr"] = myOut
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"load_type": "1",
		"zipcode": "'default'",
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
		"unitDeviceCost":"100",
		"unitUpkeepCost":"5",
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
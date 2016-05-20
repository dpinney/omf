''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess, traceback, csv, math, copy
import multiprocessing
import numpy as np
from os.path import join as pJoin
from  dateutil.parser import parse
from numpy import npv
from jinja2 import Template
import __metaModel__
from __metaModel__ import *

# # NOTE: used for debugging don't delete.
# import matplotlib.pyplot as plt

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"storageDeferral.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def quickRender(template, modelDir="", absolutePaths=False, datastoreNames={}):
	''' Presence of this function indicates we can run the model quickly via a public interface. '''
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames, quickRender=True)

def run(modelDir, inputDict):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(datetime.datetime.now())
	# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	# If we are re-running, remove output and old GLD run:
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
	except Exception, e:
		pass
	# Start background process.
	backProc = multiprocessing.Process(target = heavyProcessing, args = (modelDir, inputDict,))
	backProc.start()
	print "SENT TO BACKGROUND", modelDir
	with open(pJoin(modelDir, "PPID.txt"),"w+") as pPidFile:
		pPidFile.write(str(backProc.pid))


def runForeground(modelDir, inputDict):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(datetime.datetime.now())
	# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	# If we are re-running, remove output and old GLD run:
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
	except Exception, e:
		pass
	# Start background process.
	with open(pJoin(modelDir, "PPID.txt"),"w+") as pPidFile:
		pPidFile.write('-999')
	heavyProcessing(modelDir, inputDict)

def heavyProcessing(modelDir, inputDict):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Delete output file every run if it exists
	try:
		# Ready to run.
		startTime = datetime.datetime.now()
		outData = {}
		# Get variables.
		cellCapacity = float(inputDict['cellCapacity'])
		(cellCapacity, dischargeRate, chargeRate, cellCost) = \
			[float(inputDict[x]) for x in ('cellCapacity', 'dischargeRate', 'chargeRate', 'cellCost')]
		battEff	= float(inputDict.get("batteryEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0
		discountRate = float(inputDict.get('discountRate', 2.5)) / 100.0
		dodFactor = float(inputDict.get('dodFactor', 85)) / 100.0
		projYears = int(inputDict.get('projYears',10))
		transformerThreshold = float(inputDict.get('transformerThreshold',6.5)) * 1000
		avoidedCost = int(inputDict.get('avoidedCost',2000000))
		batteryCycleLife = int(inputDict.get('batteryCycleLife', 5000))
		# Put demand data in to a file for safe keeping.
		with open(pJoin(modelDir,"demand.csv"),"w") as demandFile:
			demandFile.write(inputDict['demandCurve'])
		# Start running battery simulation.
		battCapacity = cellCapacity * dodFactor
		battDischarge = dischargeRate
		battCharge = chargeRate
		# Most of our data goes inside the dc "table"
		try:
			dc = []
			with open(pJoin(modelDir,"demand.csv")) as inFile:
				reader = csv.DictReader(inFile)
				for row in reader:
					dc.append({'datetime': parse(row['timestamp']), 'power': float(row['power'])})
				if len(dc)!=8760: raise Exception
		except:
				e = sys.exc_info()[0]
				if str(e) == "<type 'exceptions.SystemExit'>":
					pass
				else:
					errorMessage = "Demand CSV file is incorrect format."
					raise Exception(errorMessage)
		for row in dc:
			row['excessDemand'] = row['power'] - transformerThreshold
		excessDemand = 0
		rechargePotential = 0
		excessDemandArray = []
		#Determine the max excess demand/energy
		for row in dc:
			if row['excessDemand'] > 0:
				excessDemand += row['excessDemand']
				if rechargePotential < 0:	
					excessDemandArray.append(rechargePotential)
				rechargePotential = 0
			elif row['excessDemand'] < 0:
				rechargePotential += row['excessDemand']
				if excessDemand > 0:
					excessDemandArray.append(excessDemand)
				excessDemand = 0
		finalDC = copy.deepcopy(dc)
		excessDemandMax = max(excessDemandArray)
		#Calculate the number of units needed to cover the max demand/energy
		numOfUnits = math.ceil(excessDemandMax/(cellCapacity))
		totalCost = numOfUnits * cellCost
		newBattCapacity = numOfUnits *cellCapacity * dodFactor
		newBattDischarge = numOfUnits * dischargeRate
		newBattCharge = numOfUnits * chargeRate
		run = True
		counter = 0
		#Iterate through the demand curve, if the battery runs out of charge and there is still excess demand: add more batteries
		while run == True:
			newBattCapacity = numOfUnits *cellCapacity * dodFactor
			battSoC = newBattCapacity
			for row in dc:
				month = int(row['datetime'].month)-1
				discharge = min(numOfUnits * dischargeRate,battSoC, row['power'] - transformerThreshold)
				charge = min(numOfUnits * chargeRate, newBattCapacity-battSoC, (transformerThreshold - row['power'])*battEff)
				if counter == 8760:
					run = False
				else:
					if row['power'] > transformerThreshold and battSoC > (row['power'] - transformerThreshold):
						battSoC -= discharge
						counter += 1
					elif row['power'] <= transformerThreshold and battSoC < newBattCapacity:
						battSoC += charge
						counter += 1
					elif row['power'] > transformerThreshold and battSoC < (row['power'] - transformerThreshold):
						numOfUnits += math.ceil((row['power']-transformerThreshold-battSoC)/cellCapacity)
						counter = 0
						break
					else:
						counter += 1
		afterBattCapacity = numOfUnits *cellCapacity * dodFactor
		afterBattDischarge = numOfUnits * dischargeRate
		afterBattCharge = numOfUnits * chargeRate
		battSoC = afterBattCapacity
		#Battery dispatch loop, determine net power, battery state of charge.
		for row in finalDC:
			outData['startDate'] = finalDC[0]['datetime'].isoformat()
			month = int(row['datetime'].month)-1
			discharge = min(afterBattDischarge,battSoC, row['power'] - transformerThreshold)
			charge = min(afterBattCharge, afterBattCapacity-battSoC, (transformerThreshold - row['power'])*battEff)
			if row['power'] > transformerThreshold and battSoC > 0:
				row['netpower'] = row['power'] - discharge
				battSoC -= discharge
			elif row['power'] <= transformerThreshold and battSoC < afterBattCapacity:
				row['netpower'] = row['power'] + charge/battEff
				battSoC += charge
			else:
				row['netpower'] = row['power']
			row['battSoC'] = battSoC
		#Calculations
		outData['numOfBatteries'] = numOfUnits
		outData['batteryCost'] = numOfUnits * cellCost
		outData['avoidedCost'] = avoidedCost
		outData['netAvoidedCost'] = avoidedCost - (numOfUnits * cellCost)
		outData['demand'] = [t['power']*1000.0 for t in finalDC]
		outData['demandAfterBattery'] = [t['netpower']*1000.0 for t in finalDC]
		demandAfterBattery = outData['demandAfterBattery']
		demand = outData['demand']
		outData['batteryDischargekW'] = [demand - demandAfterBattery for demand, demandAfterBattery in zip(demand, demandAfterBattery)]
		outData['batteryDischargekWMax'] = max(outData['batteryDischargekW'])
		outData['transformerThreshold'] = transformerThreshold * 1000.0
		outData['batterySoc'] = [t['battSoC']/newBattCapacity*100.0*dodFactor + (100-100*dodFactor) for t in finalDC]
		SoC = outData['batterySoc']
		cycleEquivalents = sum([SoC[i]-SoC[i+1] for i,x in enumerate(SoC[0:-1]) if SoC[i+1] < SoC[i]]) / 100.0
		outData['cycleEquivalents'] = cycleEquivalents
		outData['batteryLife'] = batteryCycleLife/cycleEquivalents
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
		try:
			os.remove(pJoin(modelDir,"PPID.txt"))
		except:
			pass
	except:
		# If input range wasn't valid delete output, write error to disk.
		cancel(modelDir)
		thisErr = traceback.format_exc()
		print 'ERROR IN MODEL', modelDir, thisErr
		inputDict['stderr'] = thisErr
		with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)

def _tests():
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	inData = {
		"batteryEfficiency": "92",
		"inverterEfficiency": "97.5",
		"cellCapacity": "7",
		"discountRate": "2.5",
		"created": "2015-06-12 17:20:39.308239",
		"dischargeRate": "5",
		"modelType": "storageDeferral",
		"chargeRate": "5",
		"demandCurve": open(pJoin(__metaModel__._omfDir,"uploads","FrankScadaValidCSV.csv")).read(),
		"fileName": "FrankScadaValidCSV.csv",
		"cellCost": "7140",
		"cellQuantity": "10",
		"dodFactor":"100",
		"avoidedCost":"2000000",
		"transformerThreshold":"6500",
		"batteryCycleLife": "5000"
		}
	modelLoc = pJoin(workDir,"admin","Automated storageDeferral Testing")
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow(template)
	# Run the model.
	runForeground(modelLoc, inData)
	# Show the output.
	renderAndShow(template, modelDir = modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
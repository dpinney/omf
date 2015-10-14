''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess, traceback, csv
import multiprocessing
from os.path import join as pJoin
from  dateutil.parser import parse
from numpy import npv
from jinja2 import Template
import __metaModel__
from __metaModel__ import *

# TODO remove this later.
import matplotlib.pyplot as plt

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"energyStorage.html"),"r") as tempFile:
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
		(cellCapacity, dischargeRate, chargeRate, cellQuantity, demandCharge, cellCost) = \
			[float(inputDict[x]) for x in ('cellCapacity', 'dischargeRate', 'chargeRate', 'cellQuantity', 'demandCharge', 'cellCost')]
		battEff	= float(inputDict.get("batteryEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0 * float(inputDict.get("inverterEfficiency", 92)) / 100.0
		discountRate = float(inputDict.get('discountRate', 2.5)) / 100.0
		retailCost = float(inputDict.get('retailCost', 0.07))
		# CHANGE: dodFactor, DEMANDCHARGEMONTHLY
		dodFactor = float(inputDict.get('dodFactor', 85)) / 100.0
		projYears = int(inputDict.get('projYears',10))
		# Put demand data in to a file for safe keeping.
		with open(pJoin(modelDir,"demand.csv"),"w") as demandFile:
			demandFile.write(inputDict['demandCurve'])
		# Start running battery simulation.
		# CHANGE
		# battCapacity = cellQuantity * cellCapacity
		battCapacity = cellQuantity * cellCapacity * dodFactor
		battDischarge = cellQuantity * dischargeRate
		battCharge = cellQuantity * chargeRate
		# Most of our data goes inside the dc "table"
		dc = [{'datetime': parse(row['timestamp']), 'power': int(row['power'])} for row in csv.DictReader(open(pJoin(modelDir,"demand.csv")))]
		for row in dc:
			row['month'] = row['datetime'].month-1
			row['weekday'] = row['datetime'].weekday
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
		dcThroughTheMonth = [[t for t in iter(dc) if t['datetime'].month-1<=x] for x in range(12)]
		hoursThroughTheMonth = [len(dcThroughTheMonth[month]) for month in range(12)]
		peakShaveSum = sum(ps)
		outData['SPP'] = (cellCost*cellQuantity)/(peakShaveSum*demandCharge)
		cashFlowCurve = [peakShaveSum * demandCharge for year in range(projYears)]
		cashFlowCurve[0]-= (cellCost * cellQuantity)
		outData['netCashflow'] = cashFlowCurve
		outData['cumulativeCashflow'] = [sum(cashFlowCurve[0:i+1]) for i,d in enumerate(cashFlowCurve)]
		outData['NPV'] = npv(discountRate, cashFlowCurve)
		outData['demand'] = [t['power']*1000.0 for t in dc]
		outData['demandAfterBattery'] = [t['netpower']*1000.0 for t in dc]
		# outData['batterySoc'] = [t['battSoC']/battCapacity*100.0 for t in dc]
		outData['batterySoc'] = [t['battSoC']/battCapacity*100.0*dodFactor + (100-100*dodFactor) for t in dc]
		# Estimate number of cyles the battery went through.
		SoC = outData['batterySoc']
		outData['cycleEquivalents'] = sum([SoC[i]-SoC[i+1] for i,x in enumerate(SoC[0:-1]) if SoC[i+1] < SoC[i]]) / 100.0
		# Output some matplotlib results as well.
		plt.plot([t['power'] for t in dc])
		plt.plot([t['netpower'] for t in dc])
		plt.plot([t['battSoC'] for t in dc])
		for month in range(12):
		  plt.axvline(hoursThroughTheMonth[month])
		plt.savefig(pJoin(modelDir,"plot.png"))
		# DRDAN: Summary of results
		outData['months'] = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
		totMonNum = []
		monthlyDemand = []
		for x in range (0, len(dcGroupByMonth)):
			totMonNum.append(sum(dcGroupByMonth[x])/1000)
			monthlyDemand.append([outData['months'][x], totMonNum[x]])
		outData['monthlyDemand'] = totMonNum
		outData['ps'] = ps		# TODO: [Battery Capacity Left]
		outData['monthlyDemandRed'] = [totMonNum - ps for totMonNum, ps in zip(totMonNum, ps)]
		outData['benefitMonthly'] = [x * demandCharge for x in outData['ps']]
		outData['kWhtoRecharge'] = [battCapacity - x for x in outData['ps']]
		outData['costtoRecharge'] = [retailCost * x for x in outData['kWhtoRecharge']]
		benefitMonthly = outData['benefitMonthly']
		costtoRecharge = outData['costtoRecharge']
		outData['benefitNet'] = [benefitMonthly - costtoRecharge for benefitMonthly, costtoRecharge in zip(benefitMonthly, costtoRecharge)]
		# Battery KW
		demandAfterBattery = outData['demandAfterBattery']
		demand = outData['demand']
		outData['batteryDischargekW'] = [demand - demandAfterBattery for demand, demandAfterBattery in zip(demand, demandAfterBattery)]
		outData['batteryDischargekWMax'] = max(outData['batteryDischargekW'])
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

def cancel(modelDir):
	''' This model runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	inData = {
		"batteryEfficiency": "92",
		"cellCapacity": "100",
		"discountRate": "2.5",
		"created": "2015-06-12 17:20:39.308239",
		"dischargeRate": "50",
		"modelType": "energyStorage",
		"chargeRate": "50",
		"demandCurve": open(pJoin(__metaModel__._omfDir,"uploads","OlinBeckenhamScada.csv")).read(),
		"fileName": "OlinBeckenhamScada.csv",
		"cellCost": "25000",
		"cellQuantity": "3",
		"runTime": "0:00:03",
		"projYears": "10",
		"demandCharge": "50",
		"retailCost": "0.07"}
	modelLoc = pJoin(workDir,"admin","Automated energyStorage Testing")
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
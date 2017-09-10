''' Powerflow results for one Gridlab instance. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess, math
import multiprocessing
from os.path import join as pJoin
from os.path import split as pSplit
from jinja2 import Template
import traceback
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# OMF imports
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf.weather import zipCodeToClimateName
from flask import session
import web

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "The gridlabMulti model allows you to run multiple instances of GridLAB-D and compare their output visually."

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName+".html"),"r") as tempFile:
	template = Template(tempFile.read())

def work(modelDir, inputDict):
	''' Run the model in its directory. WARNING: GRIDLAB CAN TAKE HOURS TO COMPLETE. '''
	beginTime = datetime.datetime.now()
	feederList = []
	# Get each feeder, prepare data in separate folders, and run there.
	for key in sorted(inputDict, key=inputDict.get):
		if key.startswith("feederName"):
			feederName = inputDict[key]
			feederList.append(feederName)
			try:
				os.remove(pJoin(modelDir, feederName, "allOutputData.json"))
			except Exception, e:
				pass
			if not os.path.isdir(pJoin(modelDir, feederName)):
				os.makedirs(pJoin(modelDir, feederName)) # create subfolders for feeders
			shutil.copy(pJoin(modelDir, feederName + ".omd"),
				pJoin(modelDir, feederName, "feeder.omd"))
			inputDict["climateName"], latforpvwatts = zipCodeToClimateName(inputDict["zipCode"])
			shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"),
				pJoin(modelDir, feederName, "climate.tmy2"))
			feederJson = json.load(open(pJoin(modelDir, feederName, "feeder.omd")))
			tree = feederJson["tree"]
			# Set up GLM with correct time and recorders:
			feeder.attachRecorders(tree, "Regulator", "object", "regulator")
			feeder.attachRecorders(tree, "Capacitor", "object", "capacitor")
			feeder.attachRecorders(tree, "Inverter", "object", "inverter")
			feeder.attachRecorders(tree, "Windmill", "object", "windturb_dg")
			feeder.attachRecorders(tree, "CollectorVoltage", None, None)
			feeder.attachRecorders(tree, "Climate", "object", "climate")
			feeder.attachRecorders(tree, "OverheadLosses", None, None)
			feeder.attachRecorders(tree, "UndergroundLosses", None, None)
			feeder.attachRecorders(tree, "TriplexLosses", None, None)
			feeder.attachRecorders(tree, "TransformerLosses", None, None)
			feeder.groupSwingKids(tree)
			feeder.adjustTime(tree=tree, simLength=float(inputDict["simLength"]),
				simLengthUnits=inputDict["simLengthUnits"], simStartDate=inputDict["simStartDate"])
			# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
			rawOut = gridlabd.runInFilesystem(tree, attachments=feederJson["attachments"],
				keepFiles=True, workDir=pJoin(modelDir, feederName))
			cleanOut = {}
			# Std Err and Std Out
			cleanOut['stderr'] = rawOut['stderr']
			cleanOut['stdout'] = rawOut['stdout']
			# Time Stamps
			for key in rawOut:
				if '# timestamp' in rawOut[key]:
					cleanOut['timeStamps'] = rawOut[key]['# timestamp']
					break
				elif '# property.. timestamp' in rawOut[key]:
					cleanOut['timeStamps'] = rawOut[key]['# property.. timestamp']
				else:
					cleanOut['timeStamps'] = []
			# Day/Month Aggregation Setup:
			stamps = cleanOut.get('timeStamps',[])
			level = inputDict.get('simLengthUnits','hours')
			# Climate
			for key in rawOut:
				if key.startswith('Climate_') and key.endswith('.csv'):
					cleanOut['climate'] = {}
					cleanOut['climate']['Rain Fall (in/h)'] = hdmAgg(rawOut[key].get('rainfall'), sum, level)
					cleanOut['climate']['Wind Speed (m/s)'] = hdmAgg(rawOut[key].get('wind_speed'), avg, level)
					cleanOut['climate']['Temperature (F)'] = hdmAgg(rawOut[key].get('temperature'), max, level)
					cleanOut['climate']['Snow Depth (in)'] = hdmAgg(rawOut[key].get('snowdepth'), max, level)
					cleanOut['climate']['Direct Insolation (W/m^2)'] = hdmAgg(rawOut[key].get('solar_direct'), sum, level)
			# Voltage Band
			if 'VoltageJiggle.csv' in rawOut:
				cleanOut['allMeterVoltages'] = {}
				cleanOut['allMeterVoltages']['Min'] = hdmAgg([(i / 2) for i in rawOut['VoltageJiggle.csv']['min(voltage_12.mag)']], min, level)
				cleanOut['allMeterVoltages']['Mean'] = hdmAgg([(i / 2) for i in rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)']], avg, level)
				cleanOut['allMeterVoltages']['StdDev'] = hdmAgg([(i / 2) for i in rawOut['VoltageJiggle.csv']['std(voltage_12.mag)']], avg, level)
				cleanOut['allMeterVoltages']['Max'] = hdmAgg([(i / 2) for i in rawOut['VoltageJiggle.csv']['max(voltage_12.mag)']], max, level)
			cleanOut['allMeterVoltages']['stdDevPos'] = [(x+y/2) for x,y in zip(cleanOut['allMeterVoltages']['Mean'], cleanOut['allMeterVoltages']['StdDev'])]
			cleanOut['allMeterVoltages']['stdDevNeg'] = [(x-y/2) for x,y in zip(cleanOut['allMeterVoltages']['Mean'], cleanOut['allMeterVoltages']['StdDev'])]
			# Total # of meters
			count = 0
			with open(pJoin(modelDir, feederName, "feeder.omd")) as f:
				for line in f:
					if "\"objectType\": \"triplex_meter\"" in line:
						count+=1
			cleanOut['allMeterVoltages']['triplexMeterCount'] = float(count)
			# Power Consumption
			cleanOut['Consumption'] = {}
			# Set default value to be 0, avoiding missing value when computing Loads
			cleanOut['Consumption']['Power'] = [0] * int(inputDict["simLength"])
			cleanOut['Consumption']['Losses'] = [0] * int(inputDict["simLength"])
			cleanOut['Consumption']['DG'] = [0] * int(inputDict["simLength"])
			for key in rawOut:
				if key.startswith('SwingKids_') and key.endswith('.csv'):
					oneSwingPower = hdmAgg(vecPyth(rawOut[key]['sum(power_in.real)'],rawOut[key]['sum(power_in.imag)']), avg, level)
					if 'Power' not in cleanOut['Consumption']:
						cleanOut['Consumption']['Power'] = oneSwingPower
					else:
						cleanOut['Consumption']['Power'] = vecSum(oneSwingPower,cleanOut['Consumption']['Power'])
				elif key.startswith('Inverter_') and key.endswith('.csv'):
					realA = rawOut[key]['power_A.real']
					realB = rawOut[key]['power_B.real']
					realC = rawOut[key]['power_C.real']
					imagA = rawOut[key]['power_A.imag']
					imagB = rawOut[key]['power_B.imag']
					imagC = rawOut[key]['power_C.imag']
					oneDgPower = hdmAgg(vecSum(vecPyth(realA,imagA),vecPyth(realB,imagB),vecPyth(realC,imagC)), avg, level)
					if 'DG' not in cleanOut['Consumption']:
						cleanOut['Consumption']['DG'] = oneDgPower
					else:
						cleanOut['Consumption']['DG'] = vecSum(oneDgPower,cleanOut['Consumption']['DG'])
				elif key.startswith('Windmill_') and key.endswith('.csv'):
					vrA = rawOut[key]['voltage_A.real']
					vrB = rawOut[key]['voltage_B.real']
					vrC = rawOut[key]['voltage_C.real']
					viA = rawOut[key]['voltage_A.imag']
					viB = rawOut[key]['voltage_B.imag']
					viC = rawOut[key]['voltage_C.imag']
					crB = rawOut[key]['current_B.real']
					crA = rawOut[key]['current_A.real']
					crC = rawOut[key]['current_C.real']
					ciA = rawOut[key]['current_A.imag']
					ciB = rawOut[key]['current_B.imag']
					ciC = rawOut[key]['current_C.imag']
					powerA = vecProd(vecPyth(vrA,viA),vecPyth(crA,ciA))
					powerB = vecProd(vecPyth(vrB,viB),vecPyth(crB,ciB))
					powerC = vecProd(vecPyth(vrC,viC),vecPyth(crC,ciC))
					# HACK: multiply by negative one because turbine power sign is opposite all other DG:
					oneDgPower = [-1.0 * x for x in hdmAgg(vecSum(powerA,powerB,powerC), avg, level)]
					if 'DG' not in cleanOut['Consumption']:
						cleanOut['Consumption']['DG'] = oneDgPower
					else:
						cleanOut['Consumption']['DG'] = vecSum(oneDgPower,cleanOut['Consumption']['DG'])
				elif key in ['OverheadLosses.csv', 'UndergroundLosses.csv', 'TriplexLosses.csv', 'TransformerLosses.csv']:
					realA = rawOut[key]['sum(power_losses_A.real)']
					imagA = rawOut[key]['sum(power_losses_A.imag)']
					realB = rawOut[key]['sum(power_losses_B.real)']
					imagB = rawOut[key]['sum(power_losses_B.imag)']
					realC = rawOut[key]['sum(power_losses_C.real)']
					imagC = rawOut[key]['sum(power_losses_C.imag)']
					oneLoss = hdmAgg(vecSum(vecPyth(realA,imagA),vecPyth(realB,imagB),vecPyth(realC,imagC)), avg, level)
					if 'Losses' not in cleanOut['Consumption']:
						cleanOut['Consumption']['Losses'] = oneLoss
					else:
						cleanOut['Consumption']['Losses'] = vecSum(oneLoss,cleanOut['Consumption']['Losses'])
			# Aggregate up the timestamps:
			if level=='days':
				cleanOut['timeStamps'] = aggSeries(stamps, stamps, lambda x:x[0][0:10], 'days')
			elif level=='months':
				cleanOut['timeStamps'] = aggSeries(stamps, stamps, lambda x:x[0][0:7], 'months')
			# Write the output.
			with open(pJoin(modelDir, feederName, "allOutputData.json"),"w") as outFile:
				json.dump(cleanOut, outFile, indent=4)
			# Clean up the PID file.
			os.remove(pJoin(modelDir, feederName,"PID.txt"))
	finishTime = datetime.datetime.now()
	inputDict["runTime"] = str(datetime.timedelta(seconds = int((finishTime - beginTime).total_seconds())))
	with open(pJoin(modelDir, "allInputData.json"),"w") as inFile:
		json.dump(inputDict, inFile, indent = 4)
	# Integrate data into allOutputData.json, if error happens, cancel it
	outData = {}
	outData["failures"] = {}
	numOfFeeders = 0
	for root, dirs, files in os.walk(modelDir):
		# dump error info into dict
		if "stderr.txt" in files:
			with open(pJoin(modelDir, root, "stderr.txt"), "r") as stderrFile:
				tempString = stderrFile.read()
				if "ERROR" in tempString or "FATAL" in tempString or "Traceback" in tempString:
					outData["failures"]["feeder_" + str(os.path.split(root)[-1])] = {"stderr": tempString}
					continue
		# dump simulated data into dict
		if "allOutputData.json" in files:
			with open(pJoin(modelDir, root, "allOutputData.json"), "r") as feederOutputData:
				numOfFeeders += 1
				feederOutput = json.load(feederOutputData)
				# TODO: a better feeder name
				outData["feeder_"+str(os.path.split(root)[-1])] = {}
				outData["feeder_"+str(os.path.split(root)[-1])]["Consumption"] = feederOutput["Consumption"]
				outData["feeder_"+str(os.path.split(root)[-1])]["allMeterVoltages"] = feederOutput["allMeterVoltages"]
				outData["feeder_"+str(os.path.split(root)[-1])]["stderr"] = feederOutput["stderr"]
				outData["feeder_"+str(os.path.split(root)[-1])]["stdout"] = feederOutput["stdout"]
				# outData[root] = {feederOutput["Consumption"], feederOutput["allMeterVoltages"], feederOutput["stdout"], feederOutput["stderr"]}
	outData["numOfFeeders"] = numOfFeeders
	outData["timeStamps"] = feederOutput.get("timeStamps", [])
	outData["climate"] = feederOutput.get("climate", [])
	# Add feederNames to output so allInputData feederName changes don't cause output rendering to disappear.
	for key, feederName in inputDict.iteritems():
		if 'feederName' in key:
			outData[key] = feederName
	with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
		json.dump(outData, outFile, indent=4)
	# # Send email to user on model success.
	# emailStatus = inputDict.get('emailStatus', 0)
	# if (emailStatus == "on"):
	# 	print "\n    EMAIL ALERT ON"
	# 	email = session['user_id']
	# 	try:
	# 		user = json.load(open("data/User/" + email + ".json"))
	# 		modelPath, modelName = pSplit(modelDir)
	# 		message = "The model " + "<i>" + str(modelName) + "</i>" + " has successfully completed running. It ran for a total of " + str(inputDict["runTime"]) + " seconds from " + str(beginTime) + ", to " + str(finishTime) + "."
	# 		return web.send_link(email, message, user)
	# 	except Exception, e:
	# 		print "ERROR: Failed sending model status email to user: ", email, ", with exception: \n", e
	# # Send email to user on model failure.
	# email = session['user_id']
	# try:
	# 	user = json.load(open("data/User/" + email + ".json"))
	# 	modelPath, modelName = pSplit(modelDir)
	# 	message = "The model " + "<i>" + str(modelName) + "</i>" + " has failed to complete running. It ran for a total of " + str(inputDict["runTime"]) + " seconds from " + str(beginTime) + ", to " + str(finishTime) + "."
	# 	return web.send_link(email, message, user)
	# except Exception, e:
	# 	print "ERROR: Failed sending model status email to user: ", email, ", with exception: \n", e
	return outData


def avg(inList):
	''' Average a list. Really wish this was built-in. '''
	return sum(inList)/len(inList)

def hdmAgg(series, func, level):
	''' Simple hour/day/month aggregation for Gridlab. '''
	if level in ['days','months']:
		return aggSeries(stamps, series, func, level)
	else:
		return series

def aggSeries(timeStamps, timeSeries, func, level):
	''' Aggregate a list + timeStamps up to the required time level. '''
	# Different substring depending on what level we aggregate to:
	if level=='months': endPos = 7
	elif level=='days': endPos = 10
	combo = zip(timeStamps, timeSeries)
	# Group by level:
	groupedCombo = _groupBy(combo, lambda x1,x2: x1[0][0:endPos]==x2[0][0:endPos])
	# Get rid of the timestamps:
	groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
	return map(func, groupedRaw)

def _pyth(x,y):
	''' Compute the third side of a triangle--BUT KEEP SIGNS THE SAME FOR DG. '''
	sign = lambda z:(-1 if z<0 else 1)
	fullSign = sign(sign(x)*x*x + sign(y)*y*y)
	return fullSign*math.sqrt(x*x + y*y)

def vecPyth(vx,vy):
	''' Pythagorean theorem for pairwise elements from two vectors. '''
	rows = zip(vx,vy)
	return map(lambda x:_pyth(*x), rows)

def vecSum(*args):
	''' Add n vectors. '''
	return map(sum,zip(*args))

def _prod(inList):
	''' Product of all values in a list. '''
	return reduce(lambda x,y:x*y, inList, 1)

def vecProd(*args):
	''' Multiply n vectors. '''
	return map(_prod, zip(*args))

def threePhasePowFac(ra,rb,rc,ia,ib,ic):
	''' Get power factor for a row of threephase volts and amps. Gridlab-specific. '''
	pfRow = lambda row:math.cos(math.atan((row[0]+row[1]+row[2])/(row[3]+row[4]+row[5])))
	rows = zip(ra,rb,rc,ia,ib,ic)
	return map(pfRow, rows)

def roundSeries(ser):
	''' Round everything in a vector to 4 sig figs. '''
	return map(lambda x:roundSig(x,4), ser)

def _groupBy(inL, func):
	''' Take a list and func, and group items in place comparing with func. Make sure the func is an equivalence relation, or your brain will hurt. '''
	if inL == []: return inL
	if len(inL) == 1: return [inL]
	newL = [[inL[0]]]
	for item in inL[1:]:
		if func(item, newL[-1][0]):
			newL[-1].append(item)
		else:
			newL.append([item])
	return newL

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"simStartDate": "2012-04-01",
		"simLengthUnits": "hours",
		"feederName1": "Simple Market System",
		"feederName2": "Simple Market System Indy Solar",
		"modelType": modelName,
		"zipCode": "64735",
		"simLength": "24",
		"runTime": ""}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	feederKeys = [key for key in defaultInputs if key.startswith("feederName")]
	for key in feederKeys:
		try:
			shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "scratch", "publicFeeders", defaultInputs[key]+'.omd'), pJoin(modelDir, defaultInputs[key] + '.omd'))
		except:
			return False
	return creationCode

def _tests():
	# Variables
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		pass # No previous test results.
	# Create new model.
	new(modelLoc)
	# No-input template.
	renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc, json.load(open(pJoin(modelLoc,"allInputData.json"))))
	## Cancel the model.
	# time.sleep(2)
	# cancel(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
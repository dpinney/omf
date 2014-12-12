''' Calculate solar engineering impacts using GridLabD. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
import multiprocessing
from __metaModel__ import *

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import gridlabd

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"_solarEngineering.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(datetime.datetime.now())
	feederDir, feederName = inputDict['feederName'].split("___")
	# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	shutil.copy(pJoin(__metaModel__._omfDir, "data", "Feeder", feederDir, feederName + ".json"),
				pJoin(modelDir, "feeder.json"))
	# Copy spcific climate data into model directory
	shutil.copy(pJoin(__metaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"), 
		pJoin(modelDir, "climate.tmy2"))
	# Ready to run
	simLengthUnits = inputDict.get("simLengthUnits","")
	simStartDate = inputDict.get("simStartDate","")
	startDateTime = simStartDate + " 00:00:00 UTC"
	startTime = datetime.datetime.now()
	
	###############################
	# TODO: INSERT RUNNING CODE HERE
	# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
	feederJson = json.load(open(pJoin(modelDir, "feeder.json")))
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
	rawOut = gridlabd.runInFilesystem(tree, attachments=feederJson["attachments"], 
		keepFiles=True, workDir=modelDir)
	###############################
	# Timestamp output.
	outData = {}
	outData["timeStamps"] = [datetime.datetime.strftime(
		datetime.datetime.strptime(startDateTime[0:19],"%Y-%m-%d %H:%M:%S") + 
		datetime.timedelta(**{simLengthUnits:x}),"%Y-%m-%d %H:%M:%S") + " UTC" for x in range(int(inputDict["simLength"]))]
	level = inputDict.get('simLengthUnits','hours')
	# Weather output.
	for key in rawOut:
		if key.startswith('Climate_') and key.endswith('.csv'):
			outData['climate'] = {}
			outData['climate']['Rain Fall (in/h)'] = hdmAgg(rawOut[key].get('rainfall'), sum, level)
			outData['climate']['Wind Speed (m/s)'] = hdmAgg(rawOut[key].get('wind_speed'), avg, level)
			outData['climate']['Temperature (F)'] = hdmAgg(rawOut[key].get('temperature'), max, level)
			outData['climate']['Snow Depth (in)'] = hdmAgg(rawOut[key].get('snowdepth'), max, level)
			outData['climate']['Direct Insolation (W/m^2)'] = hdmAgg(rawOut[key].get('solar_direct'), sum, level)
	# Voltage Band
	if 'VoltageJiggle.csv' in rawOut:
		outData['allMeterVoltages'] = {}
		outData['allMeterVoltages']['Min'] = hdmAgg([float(i / 2) for i in rawOut['VoltageJiggle.csv']['min(voltage_12.mag)']], min, level)
		outData['allMeterVoltages']['Mean'] = hdmAgg([float(i / 2) for i in rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)']], avg, level)
		outData['allMeterVoltages']['StdDev'] = hdmAgg([float(i / 2) for i in rawOut['VoltageJiggle.csv']['std(voltage_12.mag)']], avg, level)
		outData['allMeterVoltages']['Max'] = hdmAgg([float(i / 2) for i in rawOut['VoltageJiggle.csv']['max(voltage_12.mag)']], max, level)
	# Power Consumption
	outData['Consumption'] = {}
	# Set default value to be 0, avoiding missing value when computing Loads
	outData['Consumption']['Power'] = [0] * int(inputDict["simLength"])
	outData['Consumption']['Losses'] = [0] * int(inputDict["simLength"])
	outData['Consumption']['DG'] = [0] * int(inputDict["simLength"])
	outData['Consumption']['Load'] = [0] * int(inputDict["simLength"])
	for key in rawOut:
		if key.startswith('SwingKids_') and key.endswith('.csv'):
			oneSwingPower = hdmAgg(vecPyth(rawOut[key]['sum(power_in.real)'],rawOut[key]['sum(power_in.imag)']), avg, level)
			if 'Power' not in outData['Consumption']:
				outData['Consumption']['Power'] = oneSwingPower
			else:
				outData['Consumption']['Power'] = vecSum(oneSwingPower,outData['Consumption']['Power'])
		elif key.startswith('Inverter_') and key.endswith('.csv'): 	
			realA = rawOut[key]['power_A.real']
			realB = rawOut[key]['power_B.real']
			realC = rawOut[key]['power_C.real']
			imagA = rawOut[key]['power_A.imag']
			imagB = rawOut[key]['power_B.imag']
			imagC = rawOut[key]['power_C.imag']
			oneDgPower = hdmAgg(vecSum(vecPyth(realA,imagA),vecPyth(realB,imagB),vecPyth(realC,imagC)), avg, level)
			if 'DG' not in outData['Consumption']:
				outData['Consumption']['DG'] = oneDgPower
			else:
				outData['Consumption']['DG'] = vecSum(oneDgPower,outData['Consumption']['DG'])
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
			oneDgPower = hdmAgg(vecSum(powerA,powerB,powerC), avg, level)
			if 'DG' not in outData['Consumption']:
				outData['Consumption']['DG'] = oneDgPower
			else:
				outData['Consumption']['DG'] = vecSum(oneDgPower,outData['Consumption']['DG'])
		elif key in ['OverheadLosses.csv', 'UndergroundLosses.csv', 'TriplexLosses.csv', 'TransformerLosses.csv']:
			realA = rawOut[key]['sum(power_losses_A.real)']
			imagA = rawOut[key]['sum(power_losses_A.imag)']
			realB = rawOut[key]['sum(power_losses_B.real)']
			imagB = rawOut[key]['sum(power_losses_B.imag)']
			realC = rawOut[key]['sum(power_losses_C.real)']
			imagC = rawOut[key]['sum(power_losses_C.imag)']
			oneLoss = hdmAgg(vecSum(vecPyth(realA,imagA),vecPyth(realB,imagB),vecPyth(realC,imagC)), avg, level)
			if 'Losses' not in outData['Consumption']:
				outData['Consumption']['Losses'] = oneLoss
			else:
				outData['Consumption']['Losses'] = vecSum(oneLoss,outData['Consumption']['Losses'])
	outData['Consumption']['Load'] = [i-j+k for i, j, k in zip(outData['Consumption']['Power'], outData['Consumption']['Losses'], outData['Consumption']['DG'])]
	# TODO: Stdout/stderr.
	# Write the output.
	with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
		json.dump(outData, outFile, indent=4)
	# Update the runTime in the input file.
	endTime = datetime.datetime.now()
	inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
	with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
		json.dump(inputDict, inFile, indent=4)

def runForeground(modelDir, inputDict):
	''' Run the model in its directory. WARNING: GRIDLAB CAN TAKE HOURS TO COMPLETE. '''
	pass

def cancel(modelDir):
	''' TODO: INSERT CANCEL CODE HERE '''
	pass

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

def _aggData(key, aggFun, simStartDate, simLength, simLengthUnits, ssc, dat):
	''' Function to aggregate output if we need something other than hour level. '''
	u = simStartDate
	# pick a common year, ignoring the leap year, it won't affect to calculate the initHour
	d = datetime.datetime(2013, int(u[5:7]),int(u[8:10])) 
	# first day of the year	
	sd = datetime.datetime(2013, 01, 01) 
	# convert difference of datedelta object to number of hours 
	initHour = int((d-sd).total_seconds()/3600)
	fullData = ssc.ssc_data_get_array(dat, key)
	if simLengthUnits == "days":
		multiplier = 24
	else:
		multiplier = 1
	hourData = [fullData[(initHour+i)%8760] for i in xrange(simLength*multiplier)]
	if simLengthUnits == "minutes":
		pass
	elif simLengthUnits == "hours":
		return hourData
	elif simLengthUnits == "days":
		split = [hourData[x:x+24] for x in xrange(simLength)]
		return map(aggFun, split)

def _tests():
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	inData = {"simStartDate": "2012-04-01",
		"simLengthUnits": "hours",
		"feederName": "public___Olin Barre Geo",
		"modelType": "_solarEngineering",
		"climateName": "AL-HUNTSVILLE",
		"simLength": "100",
		"systemSize":"10",
		"derate":"0.97",
		"trackingMode":"0",
		"azimuth":"180",
		"runTime": "",
		"rotlim":"45.0",
		"t_noct":"45.0",
		"t_ref":"25.0",
		"gamma":"-0.5",
		"inv_eff":"0.92",
		"fd":"1.0",
		"i_ref":"1000",
		"poa_cutin":"0",
		"w_stow":"0"}
	modelLoc = pJoin(workDir,"admin","Automated _solarEngineering Testing")
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow(template)
	# Run the model.
	run(modelLoc, inData)
	# Show the output.
	renderAndShow(template, modelDir = modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
''' Calculate solar engineering impacts using GridLabD. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, csv
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
import multiprocessing
from __metaModel__ import *
from matplotlib import pyplot as plt
import networkx as nx

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
	tree = json.load(open(pJoin(modelDir,"feeder.json"))).get("tree",{})
	# TODO: nodename list
	# for key in tree:
	# 	if tree[key].get("name", "") == inputDict.get("nodename1"):
	# 		meterIndex = findIndex(str(int(max(tree.keys()))+1), 'name', tree[key]['parent'])
	# 		newInverter = makeNewInverter(tree, tree[key]['phases'])
	# 		newPanels = newPanel(str(int(max(tree.keys()))+2), inputDict.get('nodesize1', '100'))
	# 		# newchildatlocation
	# 		newName = newInverter['object'] + str(index)
	# 		newInverter['parent'] = tree[index]['name']
	# 		if (tree[treeIndex].latitude != undefined and tree[treeIndex].longitude != undefined):
	# 			newInverter['latitude'] = tree[treeIndex].latitude + Math.random() * 4 - 2
	# 			newInverter['longitude'] = tree[treeIndex].longitude + Math.random() * 4 - 2
	# 			tree[index] = newInverter
	# 			tree[index].name = newName

	# 		inverterIndex = findIndex(tree, 'name', newInverter['name'])
	# 		newChildAtLocation(newPanels, inverterIndex)

	if inputDict.get("layoutAlgorithm", "geospatial") == "geospatial":
		neato = False
	else:
		neato = True 
	chart = voltPlot(tree, workDir=modelDir, neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"output.png"))
	with open(pJoin(modelDir,"output.png"),"rb") as inFile:
		outData["voltageDrop"] = inFile.read().encode("base64")
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

def makeNewInverter(index, phases):
	newInverter = {}
	newInverter['object'] = 'inverter'
	newInverter['phases'] = phases
	newInverter['generator_status'] = 'ONLINE'
	newInverter['inverter_type'] = 'PWM'
	newInverter['generator_mode'] = 'CONSTANT_PF'
	treeNewIndex = index
	newInverter['name'] = 'synInverter' + treeNewIndex
	return newInverter

def newPanel(index, size):
	newPanels = {}
	newPanels['object'] = 'solar'
	newPanels['generator_mode'] = 'SUPPLY_DRIVEN'
	newPanels['generator_status'] = 'ONLINE'
	newPanels['panel_type'] = 'SINGLE_CRYSTAL_SILICON'
	newPanels['efficiency'] = '0.1' + randomInt(0, 5)
	newPanels['area'] = str(size) + ' sf'
	treeNewIndex = index
	newInverter['name'] = 'synSolar' + treeNewIndex
	return newPanels

def newChildAtLocation(tree, component, treeIndex):
	newName = component['object'] + str(index)
	component['parent'] = tree[treeIndex]['name']
	if (tree[treeIndex].latitude != undefined and tree[treeIndex].longitude != undefined):
		component['latitude'] = tree[treeIndex].latitude + Math.random() * 4 - 2
		component['longitude'] = tree[treeIndex].longitude + Math.random() * 4 - 2
		tree[index] = component
		tree[index].name = newName

def findIndex(inOb, field, val) :
	for key in inOb: 
		if inOb[key][field] == val:
			return key
	return ''

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

def voltPlot(tree, workDir=None, neatoLayout=False):
	''' Draw a color-coded map of the voltage drop on a feeder.
	Returns a matplotlib object. '''
	# Get rid of schedules and climate:
	for key in tree.keys():
		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
			del tree[key]
	# Make sure we have a voltDump:
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	tree[str(biggestKey*10)] = {"object":"voltdump","filename":"voltDump.csv"}
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print "gridlabD runInFilesystem with no specified workDir. Working in", workDir
	gridlabOut = gridlabd.runInFilesystem(tree, attachments=[], workDir=workDir)
	with open(pJoin(workDir,'voltDump.csv'),'r') as dumpFile:
		reader = csv.reader(dumpFile)
		reader.next() # Burn the header.
		keys = reader.next()
		voltTable = []
		for row in reader:
			rowDict = {}
			for pos,key in enumerate(keys):
				rowDict[key] = row[pos]
			voltTable.append(rowDict)
	# Calculate average node voltage deviation. First, helper functions.
	def pythag(x,y):
		''' For right triangle with sides a and b, return the hypotenuse. '''
		return math.sqrt(x**2+y**2)
	def digits(x):
		''' Returns number of digits before the decimal in the float x. '''
		return math.ceil(math.log10(x+1))
	def avg(l):
		''' Average of a list of ints or floats. '''
		return sum(l)/len(l)
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	# Tot it all up.
	nodeVolts = {}
	for row in voltTable:
		allVolts = []
		for phase in ['A','B','C']:
			phaseVolt = pythag(float(row['volt'+phase+'_real']),
							   float(row['volt'+phase+'_imag']))
			if phaseVolt != 0.0:
				if digits(phaseVolt)>3:
					# Normalize to 120 V standard
					phaseVolt = phaseVolt*(120/feedVoltage)
				allVolts.append(phaseVolt)
		nodeVolts[row.get('node_name','')] = avg(allVolts)
	# Color nodes by VOLTAGE.
	fGraph = feeder.treeToNxGraph(tree)
	voltChart = plt.figure(figsize=(10,10))
	plt.axes(frameon = 0)
	plt.axis('off')
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = nx.graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
	edgeIm = nx.draw_networkx_edges(fGraph, positions)
	nodeIm = nx.draw_networkx_nodes(fGraph,
		pos = positions,
		node_color = [nodeVolts.get(n,0) for n in fGraph.nodes()],
		linewidths = 0,
		node_size = 30,
		cmap = plt.cm.jet)
	plt.sci(nodeIm)
	plt.clim(110,130)
	plt.colorbar()
	return voltChart

def _tests():
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	inData = {"simStartDate": "2012-04-01",
		"simLengthUnits": "hours",
		"feederName": "public___Olin Barre Geo",
		"modelType": "_solarEngineering",
		"climateName": "AL-HUNTSVILLE",
		"scadaFile": "FrankScada",
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
		"w_stow":"0",
		"nodename1":"62462057655",
		"nodesize1":"200"}
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
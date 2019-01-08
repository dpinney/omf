''' perform analysis pertaining to the addition of a DER interconnection on a feeder. '''
import json, os, sys, tempfile, webbrowser, time, shutil, subprocess
import datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import matplotlib
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
import random, copy
plt.switch_backend('Agg')

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# Model metadata:
modelName, template = metadata(__file__)
tooltip = ("The derInterconnection model runs the key modeling and analysis steps involved "
	"in a DER Impact Study including Load Flow, Short Circuit, "
	"and Effective Grounding screenings.")

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	outData = {}

	# feederName = inputDict["feederName1"]
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	
	# print "*DEBUG: feederName:", feederName
	omd = json.load(open(pJoin(modelDir,feederName + '.omd')))
	if inputDict.get("layoutAlgorithm", "geospatial") == "geospatial":
		neato = False
	else:
		neato = True 

	path = pJoin(modelDir,feederName + '.omd')
	if path.endswith('.glm'):
		tree = omf.feeder.parse(path)
		attachments = []
	elif path.endswith('.omd'):
		omd = json.load(open(path))
		tree = omd.get('tree', {})
		attachments = omd.get('attachments',[])
	else:
		raise Exception('Invalid input file type. We require a .glm or .omd.')
	# dictionary to hold info on lines present in glm
	edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator', 'fuse', 'switch'], False)
	# Get rid of schedules and climate and check for all edge types:
	for key in tree.keys():
		obtype = tree[key].get("object","")
		if obtype == 'underground_line':
			edge_bools['underground_line'] = True
		elif obtype == 'overhead_line':
			edge_bools['overhead_line'] = True
		elif obtype == 'triplex_line':
			edge_bools['triplex_line'] = True
		elif obtype == 'transformer':
			edge_bools['transformer'] = True
		elif obtype == 'regulator':
			edge_bools['regulator'] = True
		elif obtype == 'fuse':
			edge_bools['fuse'] = True
		elif obtype == 'switch':
			edge_bools['switch'] = True
		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
			del tree[key]
			
	# Make sure we have a voltDump:
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	tree[str(biggestKey*10)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + 1)] = {"object":"currdump","filename":"currDump.csv"}
	# Line rating dumps
	tree[omf.feeder.getMaxKey(tree) + 1] = {
		'module': 'tape'
	}

	for key in edge_bools.keys():
		if edge_bools[key]:
			tree[omf.feeder.getMaxKey(tree) + 1] = {
				'object':'group_recorder', 
				'group':'"class='+key+'"',
				'limit':1,
				'property':'continuous_rating',
				'file':key+'_cont_rating.csv'
			}

	#create second tree without the der generation
	treeNoDer = copy.deepcopy(tree)
	for key in treeNoDer.keys():
		name = treeNoDer[key].get("name","")
		if name == inputDict["newGeneration"]:
			del treeNoDer[key]
			break

	#create a version of both trees under min load
	if inputDict['peakLoadData'] is not '':
		peakLoadData = inputDict['peakLoadData'].split('\r\n')
		for data in peakLoadData:
			if str(data) is not '':
				key = data.split(',')[0]
				val = data.split(',')[1]
				tree[key]['power_12'] = val
				treeNoDer[key]['power_12'] = val
	
	treeMinLoad = copy.deepcopy(tree)
	treeNoDerMinLoad = copy.deepcopy(treeNoDer)
	
	if inputDict['minLoadData'] is not '':
		minLoadData = inputDict['minLoadData'].split('\r\n')
		for data in minLoadData:
			if str(data) is not '':
				key = data.split(',')[0]
				val = data.split(',')[1]
				treeMinLoad[key]['power_12'] = val
				treeNoDerMinLoad[key]['power_12'] = val
				
	else:
		for key in treeMinLoad.keys():
			obtype = treeMinLoad[key].get("object","")
			if obtype == 'triplex_node':
				load = float(treeMinLoad[key].get("power_12",""))
				minLoad = (load/3)+(load*0.1*random.triangular(-1,1))
				treeMinLoad[key]['power_12'] = str(minLoad)
				treeNoDerMinLoad[key]['power_12'] = str(minLoad)


	# create and save all of the plots for all 4 scenarios

	#DER on, Peak load
	dataPeak = runGridlabAndProcessData(tree, attachments, edge_bools, workDir=modelDir)

	chart = drawPlot(tree,nodeDict=dataPeak["nodeVolts"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"voltageDerOnPeakChart.png"))
	with open(pJoin(modelDir,"voltageDerOnPeakChart.png"),"rb") as inFile:
		outData["voltageDerOnPeak"] = inFile.read().encode("base64")
	chart = drawPlot(tree,edgeDict=dataPeak["edgeCurrentSum"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"currentDerOnPeakChart.png"))
	with open(pJoin(modelDir,"currentDerOnPeakChart.png"),"rb") as inFile:
		outData["currentDerOnPeak"] = inFile.read().encode("base64")
	chart = drawPlot(tree,edgeDict=dataPeak["edgeValsPU"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"thermalDerOnPeakChart.png"))
	with open(pJoin(modelDir,"thermalDerOnPeakChart.png"),"rb") as inFile:
		outData["thermalDerOnPeak"] = inFile.read().encode("base64")

	#DER off, Peak load
	dataPeakNoDer = runGridlabAndProcessData(treeNoDer, attachments, edge_bools, workDir=modelDir)
	
	chart = drawPlot(treeNoDer,nodeDict=dataPeakNoDer["nodeVolts"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"voltageDerOffPeakChart.png"))
	with open(pJoin(modelDir,"voltageDerOffPeakChart.png"),"rb") as inFile:
		outData["voltageDerOffPeak"] = inFile.read().encode("base64")
	chart = drawPlot(treeNoDer,edgeDict=dataPeakNoDer["edgeCurrentSum"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"currentDerOffPeakChart.png"))
	with open(pJoin(modelDir,"currentDerOffPeakChart.png"),"rb") as inFile:
		outData["currentDerOffPeak"] = inFile.read().encode("base64")
	chart = drawPlot(treeNoDer,edgeDict=dataPeakNoDer["edgeValsPU"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"thermalDerOffPeakChart.png"))
	with open(pJoin(modelDir,"thermalDerOffPeakChart.png"),"rb") as inFile:
		outData["thermalDerOffPeak"] = inFile.read().encode("base64")

	#DER on, Min load
	dataMin = runGridlabAndProcessData(treeMinLoad, attachments, edge_bools, workDir=modelDir)
	
	chart = drawPlot(treeMinLoad,nodeDict=dataMin["nodeVolts"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"voltageDerOnMinChart.png"))
	with open(pJoin(modelDir,"voltageDerOnMinChart.png"),"rb") as inFile:
		outData["voltageDerOnMin"] = inFile.read().encode("base64")
	chart = drawPlot(treeMinLoad,edgeDict=dataMin["edgeCurrentSum"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"currentDerOnMinChart.png"))
	with open(pJoin(modelDir,"currentDerOnMinChart.png"),"rb") as inFile:
		outData["currentDerOnMin"] = inFile.read().encode("base64")
	chart = drawPlot(treeMinLoad,edgeDict=dataMin["edgeValsPU"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"thermalDerOnMinChart.png"))
	with open(pJoin(modelDir,"thermalDerOnMinChart.png"),"rb") as inFile:
		outData["thermalDerOnMin"] = inFile.read().encode("base64")
	
	#DER off, Min load
	dataMinNoDer = runGridlabAndProcessData(treeNoDerMinLoad, attachments, edge_bools, workDir=modelDir)

	chart = drawPlot(treeNoDerMinLoad,nodeDict=dataMinNoDer["nodeVolts"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"voltageDerOffMinChart.png"))
	with open(pJoin(modelDir,"voltageDerOffMinChart.png"),"rb") as inFile:
		outData["voltageDerOffMin"] = inFile.read().encode("base64")
	chart = drawPlot(treeNoDerMinLoad,edgeDict=dataMinNoDer["edgeCurrentSum"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"currentDerOffMinChart.png"))
	with open(pJoin(modelDir,"currentDerOffMinChart.png"),"rb") as inFile:
		outData["currentDerOffMin"] = inFile.read().encode("base64")
	chart = drawPlot(treeNoDerMinLoad,edgeDict=dataMinNoDer["edgeValsPU"], neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"thermalDerOffMinChart.png"))
	with open(pJoin(modelDir,"thermalDerOffMinChart.png"),"rb") as inFile:
		outData["thermalDerOffMin"] = inFile.read().encode("base64")

	#calculate flicker when DER is switched off under peak and min load
	[maxFlickerLocationPeak, maxFlickerValPeak] = ['',0]
	[maxFlickerLocationMin, maxFlickerValMin] = ['',0]
	peakFlicker = copy.deepcopy(dataPeakNoDer['nodeVolts'])
	minFlicker = copy.deepcopy(dataMinNoDer['nodeVolts'])
	for key in peakFlicker.keys():
		voltsPeakDerOff = float(dataPeakNoDer['nodeVolts'][key])
		voltsPeakDerOn = float(dataPeak['nodeVolts'][key])
		voltsMinDerOff = float(dataMinNoDer['nodeVolts'][key])
		voltsMinDerOn = float(dataMin['nodeVolts'][key])
		peakFlicker[key] = 100*abs(voltsPeakDerOn-voltsPeakDerOff)/(voltsPeakDerOn)
		minFlicker[key] = 100*abs(voltsMinDerOn-voltsMinDerOff)/(voltsMinDerOn)

		#print('peak:', 'max', maxFlickerValPeak, 'current', peakFlicker[key])
		if maxFlickerValPeak <= peakFlicker[key]:
			maxFlickerValPeak = peakFlicker[key]
			maxFlickerLocationPeak = key

		if maxFlickerValMin <= minFlicker[key]:
			maxFlickerValMin = minFlicker[key]
			maxFlickerLocationMin = key

	outData['maxFlickerPeak'] = [maxFlickerLocationPeak, maxFlickerValPeak]
	outData['maxFlickerMin'] = [maxFlickerLocationMin, maxFlickerValMin]
	
	#peak flicker
	chart = drawPlot(treeNoDerMinLoad,nodeDict=peakFlicker, neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"flickerPeakChart.png"))
	with open(pJoin(modelDir,"flickerPeakChart.png"),"rb") as inFile:
		outData["flickerPeak"] = inFile.read().encode("base64")
	
	#min flicker
	chart = drawPlot(treeNoDerMinLoad,nodeDict=minFlicker, neatoLayout=neato)
	chart.savefig(pJoin(modelDir,"flickerMinChart.png"))
	with open(pJoin(modelDir,"flickerMinChart.png"),"rb") as inFile:
		outData["flickerMin"] = inFile.read().encode("base64")	

	# get min and max volts for each scenario
	[maxVoltsLocationPeakDerOn, maxVoltsValPeakDerOn] = ['',0]
	[maxVoltsLocationPeakDerOff, maxVoltsValPeakDerOff] = ['',0]
	[maxVoltsLocationMinDerOn, maxVoltsValMinDerOn] = ['',0]
	[maxVoltsLocationMinDerOff, maxVoltsValMinDerOff] = ['',0]
	[minVoltsLocationPeakDerOn, minVoltsValPeakDerOn] = ['',float('inf')]
	[minVoltsLocationPeakDerOff, minVoltsValPeakDerOff] = ['',float('inf')]
	[minVoltsLocationMinDerOn, minVoltsValMinDerOn] = ['',float('inf')]
	[minVoltsLocationMinDerOff, minVoltsValMinDerOff] = ['',float('inf')]

	for key in dataPeakNoDer['nodeVolts'].keys():
		
		if maxVoltsValPeakDerOn < float(dataPeak['nodeVolts'][key]):
			maxVoltsValPeakDerOn = dataPeak['nodeVolts'][key]
			maxVoltsLocationPeakDerOn = key

		if maxVoltsValPeakDerOff < float(dataPeakNoDer['nodeVolts'][key]):
			maxVoltsValPeakDerOff = dataPeakNoDer['nodeVolts'][key]
			maxVoltsLocationPeakDerOff = key
		
		if maxVoltsValMinDerOn < float(dataMin['nodeVolts'][key]):
			maxVoltsValMinDerOn = dataMin['nodeVolts'][key]
			maxVoltsLocationMinDerOn = key
		
		if maxVoltsValMinDerOff < float(dataMinNoDer['nodeVolts'][key]):
			maxVoltsValMinDerOff = dataMinNoDer['nodeVolts'][key]
			maxVoltsLocationMinDerOff = key
		
		if minVoltsValPeakDerOn > float(dataPeak['nodeVolts'][key]):
			minVoltsValPeakDerOn = dataPeak['nodeVolts'][key]
			minVoltsLocationPeakDerOn = key
		
		if minVoltsValPeakDerOff > float(dataPeakNoDer['nodeVolts'][key]):
			minVoltsValPeakDerOff = dataPeakNoDer['nodeVolts'][key]
			minVoltsLocationPeakDerOff = key
		
		if minVoltsValMinDerOn > float(dataMin['nodeVolts'][key]):
			minVoltsValMinDerOn = dataMin['nodeVolts'][key]
			minVoltsLocationMinDerOn = key
		
		if minVoltsValMinDerOff > float(dataMinNoDer['nodeVolts'][key]):
			minVoltsValMinDerOff = dataMinNoDer['nodeVolts'][key]
			minVoltsLocationMinDerOff = key
		
	outData['maxVoltsPeakDerOn'] = [maxVoltsLocationPeakDerOn, maxVoltsValPeakDerOn]
	outData['maxVoltsPeakDerOff'] = [maxVoltsLocationPeakDerOff, maxVoltsValPeakDerOff]
	outData['maxVoltsMinDerOn'] = [maxVoltsLocationMinDerOn, maxVoltsValMinDerOn]
	outData['maxVoltsMinDerOff'] = [maxVoltsLocationMinDerOff, maxVoltsValMinDerOff]
	outData['minVoltsPeakDerOn'] = [minVoltsLocationPeakDerOn, minVoltsValPeakDerOn]
	outData['minVoltsPeakDerOff'] = [minVoltsLocationPeakDerOff, minVoltsValPeakDerOff]
	outData['minVoltsMinDerOn'] = [minVoltsLocationMinDerOn, minVoltsValMinDerOn]
	outData['minVoltsMinDerOff'] = [minVoltsLocationMinDerOff, minVoltsValMinDerOff]

	#check for thermal violations
	thermalThreshold = float(inputDict['thermalThreshold'])/100
	thermalViolations = []
	for key in dataPeak['edgeValsPU'].keys():
		
		thermalVal = float(dataPeak['edgeValsPU'][key])
		content = [key, 100*thermalVal,'Peak Load, DER On',(thermalVal>=thermalThreshold)]
		thermalViolations.append(content)

		thermalVal = float(dataPeakNoDer['edgeValsPU'][key])
		content = [key, 100*thermalVal,'Peak Load, DER Off',(thermalVal>=thermalThreshold)]
		thermalViolations.append(content)

		thermalVal = float(dataMin['edgeValsPU'][key])
		content = [key, 100*thermalVal,'Min Load, DER On',(thermalVal>=thermalThreshold)]
		thermalViolations.append(content)

		thermalVal = float(dataMinNoDer['edgeValsPU'][key])
		content = [key, 100*thermalVal,'Min Load, DER Off',(thermalVal>=thermalThreshold)]
		thermalViolations.append(content)

	outData['thermalViolations'] = thermalViolations

	
	#check for reverse powerflow and tap changes
	reversePowerFlow = []
	tapDifferences = []
 	tapThresh = float(inputDict['tapThreshold'])

	for key in tree.keys():
		
		obtype = tree[key].get("object","")	
		obname = tree[key].get("name","")
		
		if obtype == 'regulator':

			# check tap positions at Peak Load
			tapAPeakDerOn = tree[key].get("tap_A","Unspecified")
			tapBPeakDerOn = tree[key].get("tap_B","Unspecified")
			tapCPeakDerOn = tree[key].get("tap_C","Unspecified")
			tapAPeakDerOff = treeNoDer[key].get("tap_A","Unspecified")
			tapBPeakDerOff = treeNoDer[key].get("tap_B","Unspecified")
			tapCPeakDerOff = treeNoDer[key].get("tap_C","Unspecified")


			tapDiff = 0
			if (tapAPeakDerOn is not "Unspecified") and (tapAPeakDerOff is not "Unspecified"):
				tapDiff = abs(tapAPeakDerOn - tapAPeakDerOff)
			tapDifferences.append(['Peak', obname+' Tap A', tapAPeakDerOn, tapAPeakDerOff, tapDiff,(tapDiff >= tapThresh)])
			
			tapDiff = 0
			if (tapBPeakDerOn is not "Unspecified") and (tapBPeakDerOff is not "Unspecified"):
				tapDiff = abs(tapBPeakDerOn - tapBPeakDerOff)
			tapDifferences.append(['Peak', obname+' Tap B', tapBPeakDerOn, tapBPeakDerOff, tapDiff,(tapDiff >= tapThresh)])
			
			tapDiff = 0
			if (tapCPeakDerOn is not "Unspecified") and (tapCPeakDerOff is not "Unspecified"):
				tapDiff = abs(tapCPeakDerOn - tapCPeakDerOff)
			tapDifferences.append(['Peak', obname+' Tap C', tapCPeakDerOn, tapCPeakDerOff, tapDiff,(tapDiff >= tapThresh)])


			# check tap positions at Min Load
			tapAMinDerOn = treeMinLoad[key].get("tap_A","Unspecified")
			tapBMinDerOn = treeMinLoad[key].get("tap_B","Unspecified")
			tapCMinDerOn = treeMinLoad[key].get("tap_C","Unspecified")
			tapAMinDerOff = treeNoDerMinLoad[key].get("tap_A","Unspecified")
			tapBMinDerOff = treeNoDerMinLoad[key].get("tap_B","Unspecified")
			tapCMinDerOff = treeNoDerMinLoad[key].get("tap_C","Unspecified")

			tapDiff = 0
			if (tapAMinDerOn is not "Unspecified") and (tapAMinDerOff is not "Unspecified"):
				tapDiff = abs(tapAMinDerOn - tapAMinDerOff)
			tapDifferences.append(['Min', obname+' Tap A', tapAMinDerOn, tapAMinDerOff, tapDiff,(tapDiff >= tapThresh)])
			
			tapDiff = 0
			if (tapBMinDerOn is not "Unspecified") and (tapBMinDerOff is not "Unspecified"):
				tapDiff = abs(tapBMinDerOn - tapBMinDerOff)
			tapDifferences.append(['Min', obname+' Tap B', tapBMinDerOn, tapBMinDerOff, tapDiff,(tapDiff >= tapThresh)])
			
			tapDiff = 0
			if (tapCMinDerOn is not "Unspecified") and (tapCMinDerOff is not "Unspecified"):
				tapDiff = abs(tapCMinDerOn - tapCMinDerOff)
			tapDifferences.append(['Min', obname+' Tap C', tapCMinDerOn, tapCMinDerOff, tapDiff,(tapDiff >= tapThresh)])


			#check for reverse powerflow
			powerVal = float(dataPeak['edgeCurrentSum'][obname])
			content = [obname, powerVal,'Peak Load, DER On',(powerVal<0)]
			reversePowerFlow.append(content)

			powerVal = float(dataPeakNoDer['edgeCurrentSum'][obname])
			content = [obname, powerVal,'Peak Load, DER Off',(powerVal<0)]
			reversePowerFlow.append(content)

			powerVal = float(dataMin['edgeCurrentSum'][obname])
			content = [obname, powerVal,'Min Load, DER On',(powerVal<0)]
			reversePowerFlow.append(content)

			powerVal = float(dataMinNoDer['edgeCurrentSum'][obname])
			content = [obname, powerVal,'Min Load, DER Off',(powerVal<0)]
			reversePowerFlow.append(content)

	outData['reversePowerFlow'] = reversePowerFlow	
	outData['tapDifferences'] = tapDifferences	

	return outData
	

def runGridlabAndProcessData(tree, attachments, edge_bools, workDir=False):
	
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		# print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

	# read voltDump values into a dictionary.
	try:
		dumpFile = open(pJoin(workDir,'voltDump.csv'),'r')
	except:
		raise Exception('GridLAB-D failed to run with the following errors:\n' + gridlabOut['stderr'])
	reader = csv.reader(dumpFile)
	reader.next() # Burn the header.
	keys = reader.next()
	voltTable = []
	for row in reader:
		rowDict = {}
		for pos,key in enumerate(keys):
			rowDict[key] = row[pos]
		voltTable.append(rowDict)

	# read currDump values into a dictionary
	with open(pJoin(workDir,'currDump.csv'),'r') as currDumpFile:
		reader = csv.reader(currDumpFile)
		reader.next() # Burn the header.
		keys = reader.next()
		currTable = []
		for row in reader:
			rowDict = {}
			for pos,key in enumerate(keys):
				rowDict[key] = row[pos]
			currTable.append(rowDict)

	# read line rating values into a single dictionary
	lineRatings = {}
	rating_in_VA = []
	for key1 in edge_bools.keys():
		if edge_bools[key1]:		
			with open(pJoin(workDir,key1+'_cont_rating.csv'),'r') as ratingFile:
				reader = csv.reader(ratingFile)
				# loop past the header, 
				keys = []
				vals = []
				for row in reader:
					if '# timestamp' in row:
						keys = row
						i = keys.index('# timestamp')
						keys.pop(i)
						vals = reader.next()
						vals.pop(i)
				for pos,key2 in enumerate(keys):
					lineRatings[key2] = abs(float(vals[pos]))

	#edgeTupleRatings = lineRatings copy with to-from tuple as keys for labeling
	edgeTupleRatings = {}
	for edge in lineRatings:
		for obj in tree.values():
			if obj.get('name','').replace('"','') == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				ratingVal = lineRatings.get(edge)
				edgeTupleRatings[coord] = ratingVal

	# Calculate average node voltage deviation. First, helper functions.
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
	voltImbalances = {}
	for row in voltTable:
		allVolts = []
		allDiffs = []
		for phase in ['A','B','C']:
			realVolt = abs(float(row['volt'+phase+'_real']))
			imagVolt = abs(float(row['volt'+phase+'_imag']))
			phaseVolt = math.sqrt((realVolt ** 2) + (imagVolt ** 2))
			if phaseVolt != 0.0:
				## Normalize to 120 V standard
				# phaseVolt = (phaseVolt/feedVoltage)
				allVolts.append(phaseVolt)
		avgVolts = avg(allVolts)
		nodeVolts[row.get('node_name','')] = float("{0:.2f}".format(avgVolts))
		if len(allVolts) == 3:
			voltA = allVolts.pop()
			voltB = allVolts.pop()
			voltC = allVolts.pop()
			allDiffs.append(abs(float(voltA-voltB)))
			allDiffs.append(abs(float(voltA-voltC)))
			allDiffs.append(abs(float(voltB-voltC)))
			maxDiff = max(allDiffs)
			voltImbal = maxDiff/avgVolts
			voltImbalances[row.get('node_name','')] = float("{0:.2f}".format(voltImbal))
		# Use float("{0:.2f}".format(avg(allVolts))) if displaying the node labels
	
	nodeNames = {}
	for key in nodeVolts.keys():
		nodeNames[key] = key
	
	# find edge currents by parsing currdump
	edgeCurrentSum = {}
	edgeCurrentMax = {}
	for row in currTable:
		allCurr = []
		for phase in ['A','B','C']:
			realCurr = abs(float(row['curr'+phase+'_real']))
			imagCurr = abs(float(row['curr'+phase+'_imag']))
			phaseCurr = math.sqrt((realCurr ** 2) + (imagCurr ** 2))
			allCurr.append(phaseCurr)
		edgeCurrentSum[row.get('link_name','')] = sum(allCurr)
		edgeCurrentMax[row.get('link_name','')] = max(allCurr)
	# When just showing current as labels, use sum of the three lines' current values, when showing the per unit values (current/rating), use the max of the three
	

	#edgeValsPU = current values normalized per unit by line ratings
	edgeValsPU = {}
	#edgeTupleCurrents = edgeCurrents copy with to-from tuple as keys for labeling
	edgeTupleCurrents = {}
	#edgeTupleValsPU = edgeValsPU copy with to-from tuple as keys for labeling
	edgeTupleValsPU = {}
	#edgeTuplePower = dict with to-from tuples as keys and sim power as values for debugging
	edgeTuplePower = {}
	edgePower = {}
	#edgeTupleNames = dict with to-from tuples as keys and names as values for debugging
	edgeTupleNames = {}

	for edge in edgeCurrentSum:
		for obj in tree.values():
			obname = obj.get('name','').replace('"','')
			if obname == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				currVal = edgeCurrentSum.get(edge)
				voltVal = avg([nodeVolts.get(nodeFrom), nodeVolts.get(nodeTo)])
				lineRatings[edge] = lineRatings.get(edge, 10.0**9)
				edgePerUnitVal = (edgeCurrentMax.get(edge))/lineRatings[edge]
				
				edgeValsPU[edge] = edgePerUnitVal
				edgeTupleValsPU[coord] = "{0:.2f}".format(edgePerUnitVal)
				edgeTupleNames[coord] = edge
				edgeTupleCurrents[coord] = "{0:.2f}".format(currVal)
				edgePower[edge] = ((currVal * voltVal)/1000)
				edgeTuplePower[coord] = "{0:.2f}".format(edgePower[edge])

	return {"nodeNames":nodeNames, "nodeVolts":nodeVolts, "nodeVoltImbalances":voltImbalances, 
	"edgeTupleNames":edgeTupleNames, "edgeCurrentSum":edgeCurrentSum, "edgeCurrentMax":edgeCurrentMax,
	"edgeTupleCurrents":edgeTupleCurrents, "edgePower":edgePower, "edgeTuplePower":edgeTuplePower,
	"edgeLineRatings":lineRatings, "edgeTupleLineRatings":edgeTupleRatings, "edgeValsPU":edgeValsPU, 
	"edgeTupleValsPU":edgeTupleValsPU }

def drawPlot(tree, nodeDict=None, edgeDict=None, edgeLabsDict=None, displayLabs=False, customColormap=False, 
	perUnitScale=False, rezSqIn=400, neatoLayout=False):
	''' Draw a color-coded map of the voltage drop on a feeder.
	path is the full path to the GridLAB-D .glm file or OMF .omd file.
	workDir is where GridLAB-D will run, if it's None then a temp dir is used.
	neatoLayout=True means the circuit is displayed using a force-layout approach.
	edgeLabs property must be either 'Name', 'Current', 'Power', 'Rating', 'PercentOfRating', or None
	nodeLabs property must be either 'Name', 'Voltage', 'VoltageImbalance', or None
	edgeCol and nodeCol can be set to false to avoid coloring edges or nodes
	customColormap=True means use a one that is nicely scaled to perunit values highlighting extremes.
	Returns a matplotlib object.'''
	# Be quiet matplotlib:
	warnings.filterwarnings("ignore")

	# Build the graph.
	fGraph = omf.feeder.treeToNxGraph(tree)
	# TODO: consider whether we can set figsize dynamically.
	wlVal = int(math.sqrt(float(rezSqIn)))

	chart = plt.figure(figsize=(wlVal, wlVal))
	plt.axes(frameon = 0)
	plt.axis('off')
	chart.gca().set_aspect('equal')
	plt.tight_layout()

	# Need to get edge names from pairs of connected node names.
	edgeNames = []
	for e in fGraph.edges():
		edgeNames.append((fGraph.edge[e[0]][e[1]].get('name','BLANK')).replace('"',''))
	
	#set axes step equal
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
	
	#create custom colormap
	if customColormap:
		custom_cm = matplotlib.colors.LinearSegmentedColormap.from_list('custColMap',[(0.0,'blue'),(0.15,'darkgray'),(0.7,'darkgray'),(1.0,'red')])
		custom_cm.set_under(color='black')
	else:
		custom_cm = plt.cm.get_cmap('viridis')
	
	drawColorbar = False
	emptyColors = {}
	
	#draw edges with or without colors
	if edgeDict != None:
		drawColorbar = True
		edgeList = [edgeDict.get(n,1) for n in edgeNames]
	else:
		edgeList = [emptyColors.get(n,.6) for n in edgeNames]

	edgeIm = nx.draw_networkx_edges(fGraph,
		pos = positions,
		edge_color = edgeList,
		width = 1,
		edge_cmap = custom_cm)

	#draw edge labels
	if displayLabs:
		edgeLabelsIm = nx.draw_networkx_edge_labels(fGraph,
			pos = positions,
			edge_labels = edgeLabsDict,
			font_size = 8)

	# draw nodes with or without color
	if nodeDict != None:
		nodeList = [nodeDict.get(n,1) for n in fGraph.nodes()]
		drawColorbar = True
	else:
		nodeList = [emptyColors.get(n,.6) for n in fGraph.nodes()]
	
	if perUnitScale:
		vmin = 0
		vmax = 1.25
	else:
		vmin = None
		vmax = None

	nodeIm = nx.draw_networkx_nodes(fGraph,
		pos = positions,
		node_color = nodeList,
		linewidths = 0,
		node_size = 30,
		vmin = vmin,
		vmax = vmax,
		cmap = custom_cm)

	#draw node labels
	if displayLabs and nodeDict != None:
		nodeLabelsIm = nx.draw_networkx_labels(fGraph,
			pos = positions,
			labels = nodeDict,
			font_size = 8)
	
	plt.sci(nodeIm)
	# plt.clim(110,130)
	if drawColorbar:
		plt.colorbar()
	return chart

def glmToModel(glmPath, modelDir):
	''' One shot model creation from glm. '''
	tree = omf.feeder.parse(glmPath)
	# Run powerflow. First name the folder for it.
	# Remove old copy of the model.
	shutil.rmtree(modelDir, ignore_errors=True)
	# Create the model directory.
	omf.models.derInterconnection.new(modelDir)
	# Create the .omd.
	os.remove(modelDir + '/Olin Barre Geo.omd')
	with open(modelDir + '/Olin Barre Geo.omd','w') as omdFile:
		omd = dict(omf.feeder.newFeederWireframe)
		omd['tree'] = tree
		json.dump(omd, omdFile, indent=4)

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "Olin Barre Geo",
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "geospatial",
		"flickerThreshold": "2"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

# Testing for variable combinations
def _testAllVarCombos():
	edgeLabsList = {None : "None", "Name" : "N", "Current" : "C", "Power" : "P", "Rating" : "R", "PercentOfRating" : "Per"}
	nodeLabsList = {None : "None", "Name" : "N", "Voltage" : "V", "VoltageImbalance" : "VI"}
	boolList = {True : "T", False : "F"}
	testNum = 1
	for edgeLabVal in edgeLabsList.keys():
		for nodeLabVal in nodeLabsList.keys():
			for edgeColVal in boolList.keys():
				for nodeColVal in boolList.keys():
					for customColormapVal in boolList.keys():
						for perUnitScaleVal in boolList.keys():
							testName = edgeLabsList.get(edgeLabVal) + "_" + nodeLabsList.get(nodeLabVal) + "_" + boolList.get(edgeColVal) + "_" + boolList.get(nodeColVal) + "_" + boolList.get(customColormapVal) + "_" + boolList.get(perUnitScaleVal)
							#print testName
							pngName = "./drawPlotTest/drawPlot_" + testName + ".png"
							for i in range(10):
								try:
									chart = drawPlot(FNAME, neatoLayout=True, edgeLabs=edgeLabVal, nodeLabs=nodeLabVal, edgeCol=edgeColVal, nodeCol=nodeColVal, customColormap=customColormapVal, perUnitScale=perUnitScaleVal)
								except IOError, e:
									if e.errno == 2: #catch temporary IOError and retry until it passes
										print "IOError [Errno 2] for drawPlot_" + testName + ". Retrying..."
										continue #retry
								except:
									print "!!!!!!!!!!!!!!!!!! Error for drawPlot_" + testName + " !!!!!!!!!!!!!!!!!!"
									pass
								else:
									chart.savefig(pngName)
									break
							else:
								print "****************** Couldn't run drawPlot_" + testName + " ******************"
							print "Test " + testNum + " of 384 completed." #384 total combinations based on current variable sets
							testNum += 1

def _testingPlot():
	PREFIX = omf.omfDir + '/scratch/CIGAR/'
	FNAME = 'test_base_R4-25.00-1.glm_CLEAN.glm'
	# FNAME = 'test_Exercise_4_2_1.glm'
	# FNAME = 'test_ieee37node.glm'
	# FNAME = 'test_ieee123nodeBetter.glm'
	# FNAME = 'test_large-R5-35.00-1.glm_CLEAN.glm'c
	# FNAME = 'test_medium-R4-12.47-1.glm_CLEAN.glm'
	# FNAME = 'test_smsSingle.glm'
	# Hack: Agg backend doesn't work for interactivity. Switch to something we can use:
	# plt.switch_backend('MacOSX')
	#chart = drawPlot(PREFIX + FNAME, neatoLayout=True, edgeCol=True, nodeLabs="Voltage", edgeLabs="Current", perUnitScale=False, rezSqIn=400)
	#chart.savefig(PREFIX + "YO_WHATS_GOING_ON.png")
	#plt.show()

def _debugging():
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
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()
	# _testingPlot()
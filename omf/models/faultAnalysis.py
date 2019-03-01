''' Graph the voltage drop on a feeder. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import matplotlib
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
plt.switch_backend('Agg')

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *
# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Injects faults in to circuits and measures fault currents, voltages, and protective device response."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	# feederName = inputDict["feederName1"]
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	# Create voltage drop plot.
	# print "*DEBUG: feederName:", feederName
	omd = json.load(open(pJoin(modelDir,feederName + '.omd')))
	if inputDict.get("layoutAlgorithm", "geospatial") == "geospatial":
		neato = False
	else:
		neato = True
	# None check for edgeCol
	if inputDict.get("edgeCol", "None") == "None":
		edgeColValue = None
	else:
		edgeColValue = inputDict["edgeCol"]
	# None check for nodeCol
	if inputDict.get("nodeCol", "None") == "None":
		nodeColValue = None
	else:
		nodeColValue = inputDict["nodeCol"]
	# None check for edgeLabs
	if inputDict.get("edgeLabs", "None") == "None":
		edgeLabsValue = None
	else:
		edgeLabsValue = inputDict["edgeLabs"]
	# None check for nodeLabs
	if inputDict.get("nodeLabs", "None") == "None":
		nodeLabsValue = None
	else:
		nodeLabsValue = inputDict["nodeLabs"]
	# Type correction for colormap input
	if inputDict.get("customColormap", "True") == "True":
		customColormapValue = True
	else:
		customColormapValue = False
	if inputDict.get("simTime", "") == "":
		simTimeValue = '2000-01-01 0:00:00'
	else:
		simTimeValue = inputDict["simTime"]
	if inputDict.get("faultType", "None") == "None":
		faultTypeValue = None
	else:
		faultTypeValue = inputDict["faultType"]
	# chart = voltPlot(omd, workDir=modelDir, neatoLayout=neato)
	chart = drawPlotFault(
		pJoin(modelDir,feederName + ".omd"),
		neatoLayout = neato,
		edgeCol = edgeColValue,
		nodeCol = nodeColValue,
		nodeLabs = nodeLabsValue,
		edgeLabs = edgeLabsValue,
		customColormap = customColormapValue,
		faultLoc = inputDict["faultLoc"],
		faultType = faultTypeValue,
		rezSqIn = int(inputDict["rezSqIn"]),
		simTime = simTimeValue,
		workDir = modelDir)
	chart.savefig(pJoin(modelDir,"output.png"))
	with open(pJoin(modelDir,"output.png"),"rb") as inFile:
		outData["voltageDrop"] = inFile.read().encode("base64")
	return outData

def drawPlotFault(path, workDir=None, neatoLayout=False, edgeLabs=None, nodeLabs=None, edgeCol=None, nodeCol=None, faultLoc=None, faultType=None, customColormap=False, rezSqIn=400, simTime='2000-01-01 0:00:00'):
	''' Draw a color-coded map of the voltage drop on a feeder.
	path is the full path to the GridLAB-D .glm file or OMF .omd file.
	workDir is where GridLAB-D will run, if it's None then a temp dir is used.
	neatoLayout=True means the circuit is displayed using a force-layout approach.
	edgeCol property must be either 'Current', 'Power', 'Rating', 'PercentOfRating', or None
	nodeCol property must be either 'Voltage', 'VoltageImbalance', 'perUnitVoltage', 'perUnit120Voltage', or None
	edgeLabs and nodeLabs properties must be either 'Name', 'Value', or None
	edgeCol and nodeCol can be set to false to avoid coloring edges or nodes
	customColormap=True means use a one that is nicely scaled to perunit values highlighting extremes.
	faultType and faultLoc are the type of fault and the name of the line that it occurs on.
	Returns a matplotlib object.'''
	# Be quiet matplotlib:
	warnings.filterwarnings("ignore")
	if path.endswith('.glm'):
		tree = omf.feeder.parse(path)
		attachments = []
	elif path.endswith('.omd'):
		omd = json.load(open(path))
		tree = omd.get('tree', {})
		attachments = omd.get('attachments',[])
	else:
		raise Exception('Invalid input file type. We require a .glm or .omd.')

	# add fault object to tree
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	# Add Reliability module
	tree[str(biggestKey*10)] = {"module":"reliability","maximum_event_length":"18000","report_event_log":"true"}
	CLOCK_START = simTime
	dt_start = parser.parse(CLOCK_START)
	dt_end = dt_start + relativedelta(seconds=+20)
	CLOCK_END = str(dt_end)
	CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END
	if faultType != None:
		# Add eventgen object (the fault)
		tree[str(biggestKey*10 + 1)] = {"object":"eventgen","name":"ManualEventGen","parent":"RelMetrics", "fault_type":faultType, "manual_outages":faultLoc + ',' + CLOCK_RANGE} # TODO: change CLOCK_RANGE to read the actual start and stop time, not just hard-coded
		# Add fault_check object
		tree[str(biggestKey*10 + 2)] = {"object":"fault_check","name":"test_fault","check_mode":"ONCHANGE", "eventgen_object":"ManualEventGen", "output_filename":"Fault_check_out.txt"}
		# Add reliabilty metrics object
		tree[str(biggestKey*10 + 3)] = {"object":"metrics", "name":"RelMetrics", "report_file":"Metrics_Output.csv", "module_metrics_object":"PwrMetrics", "metrics_of_interest":'"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"', "customer_group":'"groupid=METERTEST"', "metric_interval":"5 h", "report_interval":"5 h"}
		# Add power_metrics object
		tree[str(biggestKey*10 + 4)] = {"object":"power_metrics","name":"PwrMetrics","base_time_value":"1 h"}
		
		# HACK: set groupid for all meters so outage stats are collected.
		noMeters = True
		for key in tree:
			if tree[key].get('object','') in ['meter', 'triplex_meter']:
				tree[key]['groupid'] = "METERTEST"
				noMeters = False
		if noMeters:
			raise Exception("No meters detected on the circuit. Please add at least one meter to allow for collection of outage statistics.")
	for key in tree:
		if 'clock' in tree[key]:
			tree[key]['starttime'] = "'" + CLOCK_START + "'"
			tree[key]['stoptime'] = "'" + CLOCK_END + "'"
	
	# dictionary to hold info on lines present in glm
	edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator', 'fuse', 'switch'], False)
	# Map to speed up name lookups.
	nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}
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
	# Make sure we have a voltage dump and current dump:
	tree[str(biggestKey*10 + 5)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + 6)] = {"object":"currdump","filename":"currDump.csv"}
	# Line rating dumps
	tree[omf.feeder.getMaxKey(tree) + 1] = {
		'module': 'tape'
	}
	for key in edge_bools.keys():
		if edge_bools[key]:
			tree[omf.feeder.getMaxKey(tree) + 1] = {
				'object':'group_recorder', 
				'group':'"class='+key+'"',
				'property':'continuous_rating',
				'file':key+'_cont_rating.csv'
			}
	#Record initial status readout of each fuse/recloser/switch/sectionalizer before running
	protDeviceValues = {}
	for key in tree:
		if tree[key].get('object','') in ['fuse', 'recloser', 'switch', 'sectionalizer']:
			protDeviceValues[tree[key].get('name','')] = [tree[key].get('status','')]
	#print protDeviceValues
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)
	# read voltDump values into a dictionary.
	try:
		dumpFile = open(pJoin(workDir,'voltDump.csv'),'r')
	except:
		raise Exception('GridLAB-D failed to run with the following errors:\n' + gridlabOut['stderr'])
	reader = csv.reader(dumpFile)
	reader.next() # Burn the header.
	keys = reader.next()
	#Record final status readout of each fuse/recloser/switch/sectionalizer before running
	for key in tree:
		if tree[key].get('object','') in ['fuse', 'recloser', 'switch', 'sectionalizer']:
			protDeviceValues[tree[key].get('name','')].append(tree[key].get('status',''))
	print protDeviceValues

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
		# HACK: add a small value to the denominator to avoid divide by zero for out of service locations (i.e. zero voltage).
		return sum(l)/(len(l) + 0.00000000000000001)
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	# Tot it all up.
	nodeVolts = {}
	nodeVoltsPU = {}
	nodeVoltsPU120 = {}
	voltImbalances = {}
	for row in voltTable:
		allVolts = []
		allVoltsPU = []
		allDiffs = []
		nodeName = row.get('node_name','')
		for phase in ['A','B','C']:
			realVolt = abs(float(row['volt'+phase+'_real']))
			imagVolt = abs(float(row['volt'+phase+'_imag']))
			phaseVolt = math.sqrt((realVolt ** 2) + (imagVolt ** 2))
			if phaseVolt != 0.0:
				treeKey = nameToIndex.get(nodeName, 0)
				nodeObj = tree.get(treeKey, {})
				try:
					nominal_voltage = float(nodeObj['nominal_voltage'])
				except:
					nominal_voltage = feedVoltage
				allVolts.append(phaseVolt)
				normVolt = (phaseVolt/nominal_voltage)
				allVoltsPU.append(normVolt)
		avgVolts = avg(allVolts)
		avgVoltsPU = avg(allVoltsPU)
		avgVoltsPU120 = 120 * avgVoltsPU
		nodeVolts[nodeName] = float("{0:.2f}".format(avgVolts))
		nodeVoltsPU[nodeName] = float("{0:.2f}".format(avgVoltsPU))
		nodeVoltsPU120[nodeName] = float("{0:.2f}".format(avgVoltsPU120))
		if len(allVolts) == 3:
			voltA = allVolts.pop()
			voltB = allVolts.pop()
			voltC = allVolts.pop()
			allDiffs.append(abs(float(voltA-voltB)))
			allDiffs.append(abs(float(voltA-voltC)))
			allDiffs.append(abs(float(voltB-voltC)))
			maxDiff = max(allDiffs)
			voltImbal = maxDiff/avgVolts
			voltImbalances[nodeName] = float("{0:.2f}".format(voltImbal))
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
	#edgeTupleCurrents = edgeCurrents copy with to-from tuple as keys for labeling
	edgeTupleCurrents = {}
	#edgeValsPU = values normalized per unit by line ratings
	edgeValsPU = {}
	#edgeTupleValsPU = edgeValsPU copy with to-from tuple as keys for labeling
	edgeTupleValsPU = {}
	#edgeTuplePower = dict with to-from tuples as keys and sim power as values for debugging
	edgeTuplePower = {}
	#edgeTupleNames = dict with to-from tuples as keys and names as values for debugging
	edgeTupleNames = {}
	#edgeTupleFaultNames = dict with to-from tuples as keys and the name of the Fault as the only value
	edgeTupleFaultNames = {}
	#linePhases = dictionary containing the number of phases on each line for line-width purposes
	linePhases = {}
	edgePower = {}
	for edge in edgeCurrentSum:
		for obj in tree.values():
			obname = obj.get('name','').replace('"','')
			if obname == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				currVal = edgeCurrentSum.get(edge)
				voltVal = avg([nodeVolts.get(nodeFrom), nodeVolts.get(nodeTo)])
				power = (currVal * voltVal)/1000
				lineRating = lineRatings.get(edge, 10.0**9)
				edgePerUnitVal = (edgeCurrentMax.get(edge))/lineRating
				edgeTupleCurrents[coord] = "{0:.2f}".format(currVal)
				edgeTuplePower[coord] = "{0:.2f}".format(power)
				edgePower[edge] = power
				edgeValsPU[edge] = edgePerUnitVal
				edgeTupleValsPU[coord] = "{0:.2f}".format(edgePerUnitVal)
				edgeTupleNames[coord] = edge
				if faultLoc == edge:
					edgeTupleFaultNames[coord] = "FAULT: " + edge
				phaseStr = obj.get('phases','').replace('"','').replace('N','').replace('S','')
				numPhases = len(phaseStr)
				if (numPhases < 1) or (numPhases > 3):
					numPhases = 1
				linePhases[edge] = numPhases
	#define which dict will be used for edge line color
	edgeColors = edgeValsPU
	#define which dict will be used for edge label
	edgeLabels = edgeTupleValsPU
	# Build the graph.
	fGraph = omf.feeder.treeToNxGraph(tree)
	# TODO: consider whether we can set figsize dynamically.
	wlVal = int(math.sqrt(float(rezSqIn)))
	voltChart = plt.figure(figsize=(wlVal, wlVal))
	plt.axes(frameon = 0)
	plt.axis('off')
	voltChart.gca().set_aspect('equal')
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
		vmin = 0
		vmax = 1.25
	else:
		custom_cm = plt.cm.get_cmap('viridis')
		vmin = None
		vmax = None
	drawColorbar = False
	emptyColors = {}
	#draw edges with or without colors
	if edgeCol != None:
		drawColorbar = True
		if edgeCol == "Current":
			edgeList = [edgeCurrentSum.get(n,1) for n in edgeNames]
			drawColorbar = True
		elif edgeCol == "Power":
			edgeList = [edgePower.get(n,1) for n in edgeNames]
			drawColorbar = True
		elif edgeCol == "Rating":
			edgeList = [lineRatings.get(n, 10.0**9) for n in edgeNames]
			drawColorbar = True
		elif edgeCol == "PercentOfRating":
			edgeList = [edgeValsPU.get(n,.5) for n in edgeNames]
			drawColorbar = True
		else:
			edgeList = [emptyColors.get(n,.6) for n in edgeNames]
			print "WARNING: edgeCol property must be 'Current', 'Power', 'Rating', 'PercentOfRating', or None"
	else:
		edgeList = [emptyColors.get(n,.6) for n in edgeNames]
	edgeIm = nx.draw_networkx_edges(fGraph,
		pos = positions,
		edge_color = edgeList,
		width = [linePhases.get(n,1) for n in edgeNames],
		edge_cmap = custom_cm)
	#draw edge labels
	if edgeLabs != None:
		if edgeLabs == "Name":
			edgeLabels = edgeTupleNames
		elif edgeLabs == "Fault":
			edgeLabels = edgeTupleFaultNames
		elif edgeLabs == "Value":
			if edgeCol == "Current":
				edgeLabels = edgeTupleCurrents
			elif edgeCol == "Power":
				edgeLabels = edgeTuplePower
			elif edgeCol == "Rating":
				edgeLabels = edgeTupleRatings
			elif edgeCol == "PercentOfRating":
				edgeLabels = edgeTupleValsPU
			else:
				edgeLabels = None
				print "WARNING: edgeCol property cannot be set to None when edgeLabs property is set to 'Value'"
		else:
			edgeLabs = None
			print "WARNING: edgeLabs property must be either 'Name', 'Value', or None"
	if edgeLabs != None:
		edgeLabelsIm = nx.draw_networkx_edge_labels(fGraph,
			pos = positions,
			edge_labels = edgeLabels,
			font_size = 8)
	# draw nodes with or without color
	if nodeCol != None:
		if nodeCol == "Voltage":
			nodeList = [nodeVolts.get(n,1) for n in fGraph.nodes()]
			drawColorbar = True
		elif nodeCol == "VoltageImbalance":
			nodeList = [voltImbalances.get(n,1) for n in fGraph.nodes()]
			drawColorbar = True
		elif nodeCol == "perUnitVoltage":
			nodeList = [nodeVoltsPU.get(n,.5) for n in fGraph.nodes()]
			drawColorbar = True
		elif nodeCol == "perUnit120Voltage":
			nodeList = [nodeVoltsPU120.get(n,60) for n in fGraph.nodes()]
			drawColorbar = True
		else:
			nodeList = [emptyColors.get(n,1) for n in fGraph.nodes()]
			print "WARNING: nodeCol property must be 'Voltage', 'VoltageImbalance', 'perUnitVoltage', 'perUnit120Voltage', or None"
	else:
		nodeList = [emptyColors.get(n,.6) for n in fGraph.nodes()]

	nodeIm = nx.draw_networkx_nodes(fGraph,
		pos = positions,
		node_color = nodeList,
		linewidths = 0,
		node_size = 30,
		vmin = vmin,
		vmax = vmax,
		cmap = custom_cm)
	#draw node labels
	nodeLabels = {}
	if nodeLabs != None:
		if nodeLabs == "Name":
			nodeLabels = nodeNames
		elif nodeLabs == "Value":
			if nodeCol == "Voltage":
				nodeLabels = nodeVolts
			elif nodeCol == "VoltageImbalance":
				nodeLabels = voltImbalances
			elif nodeCol == "perUnitVoltage":
				nodeLabels = nodeVoltsPU
			elif nodeCol == "perUnit120Voltage":
				nodeLabels = nodeVoltsPU120
			else:
				nodeLabels = None
				print "WARNING: nodeCol property cannot be set to None when nodeLabs property is set to 'Value'"
		else:
			nodeLabs = None
			print "WARNING: nodeLabs property must be either 'Name', 'Value', or None"
	if nodeLabs != None:
		nodeLabelsIm = nx.draw_networkx_labels(fGraph,
			pos = positions,
			labels = nodeLabels,
			font_size = 8)
	plt.sci(nodeIm)
	# plt.clim(110,130)
	if drawColorbar:
		plt.colorbar()
	return voltChart

def voltPlot(omd, workDir=None, neatoLayout=False):
	''' Draw a color-coded map of the voltage drop on a feeder.
	Returns a matplotlib object. '''
	tree = omd.get('tree',{})
	# # Get rid of schedules and climate:
	for key in tree.keys():
		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
			del tree[key]
	# Map to speed up name lookups.
	nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}
	# Make sure we have a voltDump:
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	tree[str(biggestKey*10)] = {"object":"voltdump","filename":"voltDump.csv"}
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
	gridlabOut = gridlabd.runInFilesystem(tree, attachments=omd.get('attachments',{}), workDir=workDir)
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
	def digits(x):
		''' Returns number of digits before the decimal in the float x. '''
		return math.ceil(math.log10(x+1))
	def avg(l):
		''' Average of a list of ints or floats. '''
		return sum(l)/len(l)
	# Use the swing bus voltage as a reasonable default voltage.
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			swingVoltage = float(ob.get('nominal_voltage',1))
	# Tot it all up.
	nodeVolts = {}
	for row in voltTable:
		allVolts = []
		for phase in ['A','B','C']:
			realV = float(row['volt'+phase+'_real'])
			imagV = float(row['volt'+phase+'_imag'])
			phaseVolt = math.hypot(realV, imagV)
			if phaseVolt != 0.0:
				if digits(phaseVolt)>3:
					nodeName = row.get('node_name','')
					treeKey = nameToIndex.get(nodeName, 0)
					nodeObj = tree.get(treeKey, {})
					try:
						nominal_voltage = float(nodeObj['nominal_voltage'])
					except:
						nominal_voltage = swingVoltage
					# Normalize to 120 V standard
					phaseVolt = phaseVolt*(120/nominal_voltage)
				allVolts.append(phaseVolt)
		# Hack: average across phases.
		nodeVolts[row.get('node_name','')] = avg(allVolts)
	# Color nodes by VOLTAGE.
	fGraph = feeder.treeToNxGraph(tree)
	voltChart = plt.figure(figsize=(20,20))
	plt.axes(frameon = 0)
	plt.axis('off')
	plt.tight_layout()
	#set axes step equal
	voltChart.gca().set_aspect('equal')
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
	edgeIm = nx.draw_networkx_edges(fGraph, positions)
	nodeIm = nx.draw_networkx_nodes(
		fGraph,
		pos = positions,
		node_color = [nodeVolts.get(n,0) for n in fGraph.nodes()],
		linewidths = 0,
		node_size = 30,
		cmap = plt.cm.viridis
	)
	plt.sci(nodeIm)
	plt.clim(110,130)
	plt.colorbar(orientation='horizontal', fraction=0.05)
	return voltChart

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "Olin Barre Fault",
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "geospatial",
		"edgeCol" : "Current",
		"nodeCol" : "Voltage",
		"nodeLabs" : "None",
		"edgeLabs" : "None",
		"faultLoc" : "17720",
		"faultType" : "SLG-A",
		"customColormap" : "False",
		"rezSqIn" : "400",
		"simTime" : '2000-01-01 0:00:00'
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

# Testing for variable combinations
# TODO: Add additional values for drawPlotFault (currently testing drawPlot)
def _testAllVarCombos():
	edgeColsList = {None : "None", "Current" : "C", "Power" : "P", "Rating" : "R", "PercentOfRating" : "Per"}
	nodeColsList = {None : "None", "Voltage" : "V", "VoltageImbalance" : "VI", "perUnitVoltage" : "PUV", "perUnit120Voltage" : "PUV120"}
	labsList = {None : "None", "Name" : "N", "Value" : "Val"}
	boolList = {True : "T", False : "F"}
	testNum = 1
	for edgeColVal in edgeColsList.keys():
		for nodeColVal in nodeColsList.keys():
			for edgeLabVal in labsList.keys():
				for nodeLabVal in labsList.keys():
					for customColormapVal in boolList.keys():
						testName = edgeColsList.get(edgeColVal) + "_" + nodeColsList.get(nodeColVal) + "_" + labsList.get(edgelabVal) + "_" + labsList.get(nodelabVal) + "_" + boolList.get(customColormapVal)
						#print testName
						pngName = "./drawPlotTest/drawPlot_" + testName + ".png"
						for i in range(10):
							try:
								chart = drawPlot(FNAME, neatoLayout=True, edgeLabs=edgeLabVal, nodeLabs=nodeLabVal, edgeCol=edgeColVal, nodeCol=nodeColVal, customColormap=customColormapVal)
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
	# FNAME = 'test_base_R4-25.00-1.glm_CLEAN.glm'
	# FNAME = 'test_Exercise_4_2_1.glm'
	# FNAME = 'test_ieee37node.glm'
	FNAME = 'test_ieee37nodeFaultTester.glm'
	# FNAME = 'test_ieee123nodeBetter.glm'
	# FNAME = 'test_large-R5-35.00-1.glm_CLEAN.glm'
	# FNAME = 'test_medium-R4-12.47-1.glm_CLEAN.glm'
	# FNAME = 'test_smsSingle.glm'
	# Hack: Agg backend doesn't work for interactivity. Switch to something we can use:
	# plt.switch_backend('MacOSX')
	chart = drawPlotFault(PREFIX + FNAME, neatoLayout=True, edgeCol="Current", nodeCol=None, nodeLabs="Name", edgeLabs=None, faultLoc="node713-704", faultType="TLG", customColormap=False, rezSqIn=225, simTime='2000-01-01 0:00:00')
	chart.savefig(PREFIX + "YO_WHATS_GOING_ON.png")
	# plt.show()

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
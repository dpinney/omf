''' Run micot-GFM, micot-RDT, and GridLAB-D to determine an optimal distribution resiliency investment. '''
import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback
import platform, re
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
import subprocess, random, webbrowser, multiprocessing
import pprint as pprint
import copy
import os.path

# OMF imports
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf.weather import zipCodeToClimateName

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Model extreme weather and determine optimal investment for distribution resiliency."
hidden = True

def getNodePhases(obj, maxRealPhase):
	''' Convert phase info in GridLAB-D obj (e.g. ABC) to GFM phase format (e.g. [True,True,True].'''
	numPhases = 0
	hasphaseA, hasphaseB, hasphaseC = False, False, False
	maxRealPhaseA, maxRealPhaseB, maxRealPhaseC = 0.0, 0.0, 0.0
	maxReactivePhaseA, maxReactivePhaseB, maxReactivePhaseC = 0.0, 0.0, 0.0
	phases = obj.get('phases','').strip('S').strip('N')
	if phases != '': 
		if 'A' in phases: 
			hasphaseA = True
			maxRealPhaseA = float(maxRealPhase)
			maxReactivePhaseA = float(maxRealPhase)*0.1
			numPhases+=1
		if 'B' in phases: 
			hasphaseB = True
			maxRealPhaseB = float(maxRealPhase)
			maxReactivePhaseB = float(maxRealPhase)*0.1
			numPhases+=1
		if 'C' in phases: 
			hasphaseC = True
			maxRealPhaseC = float(maxRealPhase)
			maxReactivePhaseC = float(maxRealPhase)*0.1
			numPhases+=1
	return numPhases, [hasphaseA, hasphaseB, hasphaseC], [maxRealPhaseA, maxRealPhaseB, maxRealPhaseC], [maxReactivePhaseA, maxReactivePhaseB, maxReactivePhaseC]

def convertToGFM(gfmInputTemplate, feederModel):
	'''Read a omd.json feeder and convert it to GFM format.'''
	# Create GFM dict.
	gfmJson = {
		'buses' : [],
		'loads' : [],
		'generators' : [],
		'line_codes' : [],
		'lines' : [],
		'critical_load_met' : gfmInputTemplate.get('critical_load_met',0.98),
		'total_load_met' : gfmInputTemplate.get('total_load_met',0.9),
		'chance_constraint' : gfmInputTemplate.get('chance_constraint', 1.0),
		'phase_variation' : gfmInputTemplate.get('phase_variation', 0.15),
	}
	# Get necessary data from .omd.
	jsonTree = feederModel.get('tree',{})
	jsonNodes = feederModel.get('nodes',[])
	#Line Creation
	critLoads = gfmInputTemplate["criticalLoads"].strip().replace(' ', '').split(',')
	objToFind = ['transformer', 'regulator', 'underground_line', 'overhead_line', 'fuse', 'switch']
	lineCount = 0
	for key, line in jsonTree.iteritems():
		if line.get('object','') in objToFind:
			phases = line.get('phases')
			if 'S' in phases:
				continue # We don't support secondary system transformers.
			newLine = {
				'id' : line.get('name',''),
				'node1_id' : line.get('from','')+'_bus',
				'node2_id' : line.get('to','')+'_bus',
				'length' : float(line.get('length',100)), #* Units match line code entries.
			}
 			gfmJson['lines'].append(newLine)
			lineCount+=1
	# Bus creation:
	objToFind = ['node', 'load', 'triplex_meter']
	for key, bus in jsonTree.iteritems():
		objType = bus.get('object','')
		# HACK: some loads can be parented to other things. Don't make buses for them.
		hasParent = 'parent' in bus
		if objType in objToFind and not hasParent:
			newBus = dict({
				'id': '', #*
				# 'min_voltage': 0.8, # in p.u.
				# 'max_voltage': 1.2, # in p.u.
				'y': float(bus.get('latitude',0.0))/5000.0,
				'x': float(bus.get('longitude',0.0))/5000.0,
				# 'has_phase': [True, True, True],
				# 'ref_voltage': [1.0, 1.0, 1.0]
				# 'ref_voltage': 1.0 # From github.
			})
			newBus['id'] = bus.get('name','')+'_bus'
			numPhases, newBus['has_phase'], max_real_phase, max_reactive_phase = getNodePhases(bus, 0.0)
			gfmJson['buses'].append(newBus)
			if len(jsonNodes) != 0:
				# HACK: no lat/lon data in tree, so use data from jsonNodes instead.
				for busNode in jsonNodes:
					# HACK: sometimes keys are strings. Sometimes not.
					if int(key) == busNode.get('treeIndex',0):
						# HACK: nice coords for GFM which wants lat/lon.
						newBus['y'] = busNode.get('y')/5000.0
						newBus['x'] = busNode.get('x')/5000.0
	# Load creation:
	objToFind = ['load']
	phaseNames = {'A':0, 'B':1, 'C':2}
	for key, load in jsonTree.iteritems():
		objType = load.get('object','')
		hasParent = 'parent' in load
		if objType in objToFind:
			newLoad = dict({
				'id': '', #*
				'node_id': '', #*
				'is_critical': False, 
				'max_real_phase': [0,0,0], #*
				'max_reactive_phase': [0,0,0], #*
				'has_phase': [False, False, False] #*
			})
			if load.get('name','') in critLoads:
				newLoad['is_critical'] = True
			newLoad['id'] = load.get('name','')+'_lod'
			# Associate the new load with the bus it is attached to.
			if hasParent:
				newLoad['node_id'] = load['parent'] + '_bus'
			else: #no parent, i.e. we created a bus for the load.
				newLoad['node_id'] = load['name'] + '_bus'
			voltage = float(load.get('nominal_voltage','4800'))
			for phaseName, index in phaseNames.iteritems():
				impedance = 'constant_impedance_' + phaseName
				power = 'constant_power_' + phaseName
				current = 'constant_current_' + phaseName
				if impedance in load:
					constImpedRaw = load.get(impedance,'').replace(' ','')
					constImped = complex(constImpedRaw)
					realImpedance = constImped.real
					reactiveImpedance = constImped.imag
					newLoad['max_real_phase'][index] = abs((voltage*voltage)/realImpedance)/1000000
					newLoad['max_reactive_phase'][index] = abs((voltage*voltage)/reactiveImpedance)/1000000
					newLoad['has_phase'][index] = True
				if current in load:
					constCurrRaw = load.get(current,'').replace(' ','')
					constCurr = complex(constCurrRaw)
					realCurr = constCurr.real
					reactiveCurr = constCurr.imag
					newLoad['max_real_phase'][index] = abs(voltage*realCurr)/1000000
					newLoad['max_reactive_phase'][index] = abs(voltage*reactiveCurr)/1000000
					newLoad['has_phase'][index] = True
				if power in load:
					constPowerRaw = load.get(power,'').replace(' ','')
					constPower = complex(constPowerRaw)
					realPower = constPower.real
					reactivePower = constPower.imag
					newLoad['max_real_phase'][index] = abs(realPower)/1000000
					newLoad['max_reactive_phase'][index] = abs(reactivePower)/1000000
					newLoad['has_phase'][index] = True
			gfmJson['loads'].append(newLoad)
	# Generator creation:
	genCands = gfmInputTemplate['generatorCandidates'].strip().replace(' ', '').split(',')
	for key, glmOb in jsonTree.iteritems():
		# Check for a swing node:
		isSwing = glmOb.get('bustype','') == 'SWING'
		if glmOb.get('name','') in genCands or isSwing:
			genID = glmOb.get('name','')+'_gen'
			for elem in gfmJson['buses']:
				if elem['id'][0:-4] == genID[0:-4]:
					busID = elem['id']
			numPhases, has_phase, max_real_phase, max_reactive_phase = getNodePhases(glmOb, gfmInputTemplate['maxDGPerGenerator'])
			if isSwing:
				# HACK: swing buses get "infinitely large", i.e. 5 TW, generator capacity.
				genSize = 5.0 * 1000.0 * 1000.0
				isNew = False
				has_phase = [True, True, True]
			else:
				# Non swing buses get 1 MW generators.
				genSize = gfmInputTemplate['maxDGPerGenerator']
				isNew = True
			genObj = {
	 			'id': glmOb.get('name','')+'_gen', #*
				'node_id': busID, #*
				'is_new': isNew, # Whether or not new generation can be built.
				'microgrid_cost': gfmInputTemplate['dgUnitCost'], # Per MW capacity of building DG.
				'max_microgrid': genSize, # Max additional capacity for this gen.
				'microgrid_fixed_cost': 0, # One-time fixed cost for building DG.
				'has_phase': has_phase, #*
				'max_reactive_phase': [genSize,genSize,genSize], #*
				'max_real_phase': [genSize,genSize,genSize] #*
			}
			gfmJson['generators'].append(genObj)
	return gfmJson

def genDiagram(outputDir, feederJson, damageDict):
	# Load required data.
	tree = feederJson.get("tree",{})
	links = feederJson.get("links",{})
	# Generate lat/lons from nodes and links structures.
	for link in links:
		for typeLink in link.keys():
			if typeLink in ['source', 'target']:
				for key in link[typeLink].keys():
					if key in ['x', 'y']:
						objName = link[typeLink]['name']
						for x in tree:
							leaf = tree[x]
							if leaf.get('name','')==objName:
								if key=='x': leaf['latitude'] = link[typeLink][key]
								else: leaf['longitude'] = link[typeLink][key]
	# Remove even more things (no lat, lon or from = node without a position).
	for key in tree.keys():
		aLat = tree[key].get('latitude')
		aLon = tree[key].get('longitude')
		aFrom = tree[key].get('from')
		if aLat is None and aLon is None and aFrom is None:
			 tree.pop(key)
	# Create and save the graphic.
	inGraph = feeder.treeToNxGraph(tree)
	#feeder.latLonNxGraph(nxG) # This function creates a .plt reference which can be saved here.
	labels=False
	neatoLayout=False 
	showPlot=False
	plt.axis('off')
	plt.tight_layout()
	plt.gca().invert_yaxis()
	plt.gca().set_aspect('equal')
	# Layout the graph via GraphViz neato. Handy if there's no lat/lon data.
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(inGraph.edges())
		# HACK2: might miss nodes without edges without the following.
		cleanG.add_nodes_from(inGraph)
		pos = nx.nx_agraph.graphviz_layout(cleanG, prog='neato')
	else:
		pos = {n:inGraph.node[n].get('pos',(0,0)) for n in inGraph}
	# Draw all the edges.
	for e in inGraph.edges():
		edgeName = inGraph.edge[e[0]][e[1]].get('name')
		edgeColor = 'black'
		if edgeName in damageDict:
			if damageDict[edgeName] == 1:
				edgeColor = 'yellow'
			if damageDict[edgeName] == 2:
				edgeColor = 'orange'
			if damageDict[edgeName] >= 3:
				edgeColor = 'red'
		eType = inGraph.edge[e[0]][e[1]].get('type','underground_line')
		ePhases = inGraph.edge[e[0]][e[1]].get('phases',1)
		standArgs = {'edgelist':[e],
					 'edge_color':edgeColor,
					 'width':2,
					 'style':{'parentChild':'dotted','underground_line':'dashed'}.get(eType,'solid') }
		if ePhases==3:
			standArgs.update({'width':5})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':3,'edge_color':'white'})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':1,'edge_color':feeder._obToCol(eType)})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
		if ePhases==2:
			standArgs.update({'width':3})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':1,'edge_color':'white'})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
		else:
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
	# Draw nodes and optional labels.
	nx.draw_networkx_nodes(inGraph,pos,
						   nodelist=pos.keys(),
						   node_color=[feeder._obToCol(inGraph.node[n].get('type','underground_line')) for n in inGraph],
						   linewidths=0,
						   node_size=10)
	if labels:
		nx.draw_networkx_labels(inGraph,pos,
								font_color='black',
								font_weight='bold',
								font_size=0.25)
	if showPlot: plt.show()
	plt.savefig(pJoin(outputDir,"feederChart.png"), dpi=800, pad_inches=0.0)

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	with open(pJoin(modelDir,inputDict['weatherImpactsFileName']),'w') as hazardFile:
		hazardFile.write(inputDict['weatherImpacts'])
	with open(pJoin(modelDir, feederName + '.omd'), "r") as jsonIn:
		feederModel = json.load(jsonIn)
	# Create GFM input file.
	print "RUNNING GFM FOR", modelDir
	gfmInputTemplate = {
		'phase_variation' : float(inputDict['phaseVariation']),
		'chance_constraint' : float(inputDict['chanceConstraint']),
		'critical_load_met' : float(inputDict['criticalLoadMet']),
		'total_load_met' : float(inputDict['nonCriticalLoadMet']),
		'maxDGPerGenerator' : float(inputDict['maxDGPerGenerator']),
		'dgUnitCost' : float(inputDict['dgUnitCost']),
		'generatorCandidates' : inputDict['generatorCandidates'],
		'criticalLoads' : inputDict['criticalLoads']
	}
	gfmJson = convertToGFM(gfmInputTemplate, feederModel)
	gfmInputFilename = 'gfmInput.json'
	with open(pJoin(modelDir, gfmInputFilename), 'w') as outFile:
		json.dump(gfmJson, outFile, indent=4)
	# Run GFM
	gfmBinaryPath = pJoin(__neoMetaModel__._omfDir,'solvers','gfm', 'Fragility.jar')
	rdtInputName = 'rdtInput.json'
	if platform.system() == 'Darwin':
		#HACK: force use of Java8 on MacOS.
		javaCmd = '/Library/Java/JavaVirtualMachines/jdk1.8.0_181.jdk/Contents/Home/bin/java'
	else:
		javaCmd = 'java'
	proc = subprocess.Popen([javaCmd,'-jar', gfmBinaryPath, '-r', gfmInputFilename, '-wf', inputDict['weatherImpactsFileName'],'-num','3','-ro',rdtInputName], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=modelDir)
	(stdout,stderr) = proc.communicate()
	with open(pJoin(modelDir, "gfmConsoleOut.txt"), "w") as gfmConsoleOut:
		gfmConsoleOut.write(stdout)
	rdtInputFilePath = pJoin(modelDir,'rdtInput.json')
	# Pull GFM input data on lines and generators for HTML presentation.
	with open(rdtInputFilePath, 'r') as rdtInputFile:
		# HACK: we use rdtInput as a string in the frontend.
		rdtJsonAsString = rdtInputFile.read()
		rdtJson = json.loads(rdtJsonAsString)
	rdtJson["power_flow"] = inputDict["power_flow"]
	rdtJson["solver_iteration_timeout"] = 300.0
	rdtJson["algorithm"] = "miqp"
	# Calculate line costs.
	lineData = {}
	for line in rdtJson["lines"]:
		lineData[line["id"]] = '{:,.2f}'.format(float(line["length"]) * float(inputDict["lineUnitCost"]))
	outData["lineData"] = lineData
	outData["generatorData"] = '{:,.2f}'.format(float(inputDict["dgUnitCost"]) * float(inputDict["maxDGPerGenerator"]))
	outData['gfmRawOut'] = rdtJsonAsString
	# Insert user-specified scenarios block into RDT input
	if inputDict['scenarios'] != "":
		rdtJson['scenarios'] = json.loads(inputDict['scenarios'])
		with open(pJoin(rdtInputFilePath), "w") as rdtInputFile:
			json.dump(rdtJson, rdtInputFile, indent=4)
	# Run GridLAB-D first time to generate xrMatrices.
	print "RUNNING 1ST GLD RUN FOR", modelDir
	omdPath = pJoin(modelDir, feederName + ".omd")
	with open(omdPath, "r") as omd:
		omd = json.load(omd)
	# Remove new line candidates to get normal system powerflow results.
	deleteList = []
	newLines = inputDict["newLineCandidates"].strip().replace(' ', '').split(',')
	for newLine in newLines:
		for omdObj in omd["tree"]:
			if ("name" in omd["tree"][omdObj]):
				if (newLine == omd["tree"][omdObj]["name"]):
					deleteList.append(omdObj)
	for delItem in deleteList:
		del omd["tree"][delItem]
	#Load a blank glm file and use it to write to it
	feederPath = pJoin(modelDir, 'feeder.glm')
	with open(feederPath, 'w') as glmFile:
		toWrite =  omf.feeder.sortedWrite(omd['tree']) + "object jsondump {\n\tfilename_dump_reliability JSON_dump_line.json;\n\twrite_system_info true;\n\twrite_per_unit true;\n\tsystem_base 100.0 MVA;\n};\n"
		glmFile.write(toWrite)		
	#Write attachments from omd, if no file, one will be created
	for fileName in omd['attachments']:
		with open(os.path.join(modelDir, fileName),'w') as file:
			file.write(omd['attachments'][fileName])
	#Wire in the file the user specifies via zipcode.
	climateFileName, latforpvwatts = zipCodeToClimateName(inputDict["simulationZipCode"])
	shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", climateFileName + ".tmy2"), pJoin(modelDir, 'climate.tmy2'))
	# Platform specific binaries for GridLAB-D First Run.
	if platform.system() == "Linux":
		myEnv = os.environ.copy()
		myEnv['GLPATH'] = omf.omfDir + '/solvers/gridlabdv990/'
		commandString = omf.omfDir + '/solvers/gridlabdv990/gridlabd.bin feeder.glm'  
	elif platform.system() == "Windows":
		myEnv = os.environ.copy()
		commandString =  '"' + pJoin(omf.omfDir, "solvers", "gridlabdv990", "gridlabd.exe") + '"' + " feeder.glm"
	elif platform.system() == "Darwin":
		myEnv = os.environ.copy()
		myEnv['GLPATH'] = omf.omfDir + '/solvers/gridlabdv990/MacRC4p1_std8/'
		commandString = '"' + omf.omfDir + '/solvers/gridlabdv990/MacRC4p1_std8/gld.sh" feeder.glm'
	# Run GridLAB-D First Time.
	proc = subprocess.Popen(commandString, stdout=subprocess.PIPE, shell=True, cwd=modelDir, env=myEnv)
	(out, err) = proc.communicate()
	with open(pJoin(modelDir, "gldConsoleOut.txt"), "w") as gldConsoleOut:
		gldConsoleOut.write(out)
	with open(pJoin(modelDir, "JSON_dump_line.json"), "r") as gldOut:
		gld_json_line_dump = json.load(gldOut)
	outData['gridlabdRawOut'] = gld_json_line_dump
	# Add GridLAB-D line objects and line codes in to the RDT model.
	rdtJson["line_codes"] = gld_json_line_dump["properties"]["line_codes"]
	rdtJson["lines"] = gld_json_line_dump["properties"]["lines"]
	hardCands = inputDict['hardeningCandidates'].strip().replace(' ', '').split(',')
	newLineCands = inputDict['newLineCandidates'].strip().replace(' ', '').split(',')
	switchCands = inputDict['switchCandidates'].strip().replace(' ', '').split(',')
	for line in rdtJson["lines"]:
		line['node1_id'] = line['node1_id'] + "_bus"
		line['node2_id'] = line['node2_id'] + "_bus"
		line['capacity'] = 10000
		line['construction_cost'] = float(inputDict['lineUnitCost'])
		line['harden_cost'] = float(inputDict['hardeningUnitCost'])
		line['switch_cost'] = float(inputDict['switchCost'])
		line_id = line.get('id','')
		object_type = line.get('object','')
		if line_id in hardCands:
			line['can_harden'] = True
		if line_id in switchCands:
			line['can_add_switch'] = True
		if line_id in newLineCands:
			line['is_new'] = True
		if object_type in ['transformer','regulator']: 
			line['is_transformer'] = True
		if object_type == 'switch':
			line['has_switch'] = True
	with open(rdtInputFilePath, "w") as outFile:
		json.dump(rdtJson, outFile, indent=4)
	# Run RDT.
	print "RUNNING RDT FOR", modelDir
	rdtOutFile = modelDir + '/rdtOutput.json'
	rdtSolverFolder = pJoin(__neoMetaModel__._omfDir,'solvers','rdt')
	rdtJarPath = pJoin(rdtSolverFolder,'micot-rdt.jar')
	proc = subprocess.Popen(['java', "-Djna.library.path=" + rdtSolverFolder, '-jar', rdtJarPath, '-c', rdtInputFilePath, '-e', rdtOutFile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout,stderr) = proc.communicate()
	with open(pJoin(modelDir, "rdtConsoleOut.txt"), "w") as rdtConsoleOut:
		rdtConsoleOut.write(stdout)
	rdtRawOut = open(rdtOutFile).read()
	outData['rdtRawOut'] = rdtRawOut
	# Indent the RDT output nicely.
	with open(pJoin(rdtOutFile),"w") as outFile:
		rdtOut = json.loads(rdtRawOut)
		json.dump(rdtOut, outFile, indent = 4)
	# Generate and run 2nd copy of GridLAB-D model with changes specified by RDT.
	print "RUNNING 2ND GLD RUN FOR", modelDir
	feederCopy = copy.deepcopy(feederModel)
	lineSwitchList = []
	for line in rdtOut['design_solution']['lines']:
		if('switch_built' in line):
			lineSwitchList.append(line['id'])
	# Remove nonessential lines in second model as indicated by RDT output.
	for key in feederCopy['tree'].keys():
		value = feederCopy['tree'][key]
		if('object' in value):
			if (value['object'] == 'underground_line') or (value['object'] == 'overhead_line'):
				if value['name'] not in lineSwitchList:
					del feederCopy['tree'][key]
	# Add generators to second model.
	maxTreeKey = int(max(feederCopy['tree'], key=int)) + 1
	maxTreeKey = max(feederCopy['tree'], key=int)
	# Load a blank glm file and use it to write to it
	feederPath = pJoin(modelDir, 'feederSecond.glm')
	with open(feederPath, 'w') as glmFile:
		toWrite =  "module generators;\n\n" + omf.feeder.sortedWrite(feederCopy['tree']) + "object voltdump {\n\tfilename voltDump2ndRun.csv;\n};\nobject jsondump {\n\tfilename_dump_reliability test_JSON_dump.json;\n\twrite_system_info true;\n\twrite_per_unit true;\n\tsystem_base 100.0 MVA;\n};\n"# + "object jsonreader {\n\tfilename " + insertRealRdtOutputNameHere + ";\n};"
		glmFile.write(toWrite)
	# Run GridLAB-D second time.
	if platform.system() == "Windows":
		proc = subprocess.Popen(['gridlabd', 'feederSecond.glm'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=modelDir)
		(out, err) = proc.communicate()
		outData["secondGLD"] = str(os.path.isfile(pJoin(modelDir,"voltDump2ndRun.csv")))
	else:
		# TODO: make 2nd run of GridLAB-D work on Unixes.
		outData["secondGLD"] = str(False)
	# Draw the feeder.
	damageDict = {}
	for scenario in rdtJson["scenarios"]:
		for line in scenario["disable_lines"]:
			if line in damageDict:
				damageDict[line] = damageDict[line] + 1
			else:
				damageDict[line] = 1
	genDiagram(modelDir, feederModel, damageDict)
	with open(pJoin(modelDir,"feederChart.png"),"rb") as inFile:
		outData["oneLineDiagram"] = inFile.read().encode("base64")
	# And we're done.
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "trip37", # "trip37" "UCS Winter 2017 Fixed" "SVECNoIslands"
		"modelType": modelName,
		"layoutAlgorithm": "geospatial",
		"modelName": modelDir,
		"user": "admin",
		"created": str(dt.datetime.now()),
		"lineUnitCost": "3000.0",
		"switchCost": "10000.0",
		"dgUnitCost": "1000000.0",
		"hardeningUnitCost": "1000.0",
		"maxDGPerGenerator": "0.5",
		"hardeningCandidates": "A_node705-742,A_node705-712,A_node706-725,SCL33937,SCL33938,SCL38094",
		"newLineCandidates": "TIE_A_to_C,TIE_C_to_B,TIE_B_to_A",
		"generatorCandidates": "A_node706,A_node707,A_node708,B_node704,B_node705,B_node703",
		"switchCandidates" : "A_node705-742,A_node705-712",
		"criticalLoads": "C_load722",
		"criticalLoadMet": "0.98",
		"nonCriticalLoadMet": "0.5",
		"chanceConstraint": "1.0",
		"phaseVariation": "0.15",
		"weatherImpacts": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","wf_clip.asc")).read(),
		"weatherImpactsFileName": "wf_clip.asc", # "wf_clip.asc" "wind_grid_1UCS.asc" "wf_clipSVEC.asc"
		"scenarios": "",
		"scenariosFileName": "",
		"simulationDate": "2012-01-01",
		"simulationZipCode": "64735",
		"power_flow": "network_flow"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		# Copy the feeder from one place to another
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _runModel():
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
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_runModel()
	
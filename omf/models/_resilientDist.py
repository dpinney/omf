''' Run micot-GFM, micot-RDT, and GridLAB-D to determine an optimal distribution resiliency investment. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback, copy, platform
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import networkx as nx
from omf.models import __metaModel__
from __metaModel__ import *
import subprocess, random, webbrowser
import pprint as pprint

# OMF imports
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf.weather import zipCodeToClimateName

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "Model extreme weather and determine optimal investment for distribution resiliency."

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,modelName+".html"),"r") as tempFile:
	template = Template(tempFile.read())

def createObj(objToRet):
	'''Creates rdt input file objects.'''
	if objToRet=='scenario':
		# scenario: an rdt input has multiple unique scenarios.
		# required: id.		
		scenarioObj = {
			'id' : "1", #*
			'disable_line' : [],
			'hardened_disabled_lines' : []
		}
		return scenarioObj
	elif objToRet=='line_code':	
		# line_code: impedenance and resistance values of lines, may be unique for each line.
		# required: all.
		# TODO: read and give transformer specific line codes to transformer lines.
		line_codeObj = {
			'line_code': '', #*
			'num_phases': '', #*
			'xmatrix': [[],[],[]], #* reactance terms: phaseA, phaseB, and phaseC.
			'rmatrix': [[],[],[]] #* resistance terms: phaseA/B/C.
		}
		return line_codeObj
	elif objToRet=='line':
		# lines: a line in the model. 
		# required: id, node1, node2, length, line_code, num_phases, has_phase, harden_cost: 1.
		lineObj = {
			'id' : '', #*
			'node1_id' : '', #*
			'node2_id' : '', #*
			'line_code' : '', #*
			'length' : 1.0, #* Units match line code entries.
			# 'has_switch' : False,
			# 'construction_cost': 100,
			'harden_cost': 100000, # Russel: this exists unless its a trans.
			# 'switch_cost': 15, # taken from rdtInTrevor.json.
			# 'can_harden': False, # Not seen in rdtInTrevor.json.
			# 'can_add_switch': False, # Not seen in rdtInTrevor.json.
			# 'num_poles' : 2,
			# 'capacity' : 5780, # MVA capacity.
			# 'is_transformer' : False,
			'num_phases' : 3, #*
			# 'is_new' : False,
			'has_phase' : [True, True, True] #*
		}
		return lineObj
	elif objToRet=='bus':
		# bus: node data.
		# req: id.
		busObj = {
			'id': '', #*
			# 'min_voltage': 0.8, # in p.u.
			# 'max_voltage': 1.2, # in p.u.
			# 'y': '', # not in schema.
			# 'x': '', # not in schema.
			# 'has_generator': False,
			# 'has_phase': [True, True, True],
			# 'ref_voltage': [1.0, 1.0, 1.0]
			# 'ref_voltage': 1.0 # From github.
		}
		return busObj
	elif objToRet=='load':
		# load: load data.
		# req: id, node_id, max_real_phase, max_reac_phase, has_phase.
		loadObj = {
			'id': '', #*
			'node_id': '', #*
			'is_critical': False, 
			'max_real_phase': [], #*
			'max_reactive_phase': [], #*
			'has_phase': [] #*
		}
		return loadObj
	elif objToRet=='gen':
		# generator: generator data.
		# req: id, node_id, has_phase, max_reac_phase, max_real_phase.
		genObj = {
			'id': '', #*
			'node_id': '', #*
			# 'is_new': False, # Whether or not new generation can be built.
			# 'microgrid_cost': 1.5, # Per MW capacity of building DG.
			# 'max_microgrid': 0, # Max additional capacity for this gen.
			# 'microgrid_fixed_cost': 0, # One-time fixed cost for building DG.
			'has_phase': [True, True, True], #*
			'max_reactive_phase': [1.7976931348623e+308, 1.7976931348623e+308, 1.7976931348623e+308], #*
			'max_real_phase': [1.7976931348623e+308, 1.7976931348623e+308, 1.7976931348623e+308] #*
		}		
		return genObj
	else:
		# Incorrectly entered object.
		print "The object: %s doesn't exist."%(str(objToRet))
		return {}

def getNodePhases(obj, defReal=1.7976931348623e+308, defReact=1.7976931348623e+308):
	'''read omd., 10json obj's phases and convert to rdt format.
	'''
	numPhases = 0
	hasphaseA, hasphaseB, hasphaseC = False, False, False
	maxRealPhaseA, maxRealPhaseB, maxRealPhaseC = 0, 0, 0
	maxReactivePhaseA, maxReactivePhaseB, maxReactivePhaseC = 0, 0, 0
	phases = obj.get('phases','').strip('S').strip('N')
	if phases != '': 
		if 'A' in phases: 
			hasphaseA = True
			maxRealPhaseA = defReal
			maxReactivePhaseA = defReact
			numPhases+=1
		if 'B' in phases: 
			hasphaseB = True
			maxRealPhaseB = defReal
			maxReactivePhaseB = defReact
			numPhases+=1
		if 'C' in phases: 
			hasphaseC = True
			maxRealPhaseC = defReal
			maxReactivePhaseC = defReact
			numPhases+=1
	else:
		print "NO PHASES FOUND FOR OBJ:", obj	
	return numPhases, [hasphaseA, hasphaseB, hasphaseC], [maxRealPhaseA, maxRealPhaseB, maxRealPhaseC], [maxReactivePhaseA, maxReactivePhaseB, maxReactivePhaseC]

def makeLines(rdtJson, jsonTree, debug):
	''' lines.
	TODO: Put in accurate num_poles, ask if has_phase corresponds to a,b,c.
	TODO: Insert harden_cost calc.
	'''
	objToFind, lineCount = ['triplex_line','transformer', 'regulator'], 0
	for key, line in jsonTree.iteritems():
		if line.get('object','') in objToFind:
			newLine = createObj('line')
			newLine['id'], newLine['node1_id'], newLine['node2_id'], newLine['length'], newLine['line_code'] = \
				line.get('name',''), line.get('from','')+'_bus', line.get('to','')+'_bus', float(line.get('length',100))/100, lineCount
			newLine['num_phases'], newLine['has_phase'], maxRealPhase, maxReactivePhase = getNodePhases(line)
			# Calculate harden_cost, 10.
			# newLine['capacity'] = 1000000000 # Set it arbitrarily high.
			if line.get('object','') == 'transformer': 
				newLine['is_transformer'] = True
				newLine.pop('harden_cost',None)
 			rdtJson['lines'].append(newLine)
			# print "Added newLine: %s (TOTAL: %s)\n"%(newLine, str(lineCount+1))
			lineCount+=1
	if debug: 
		print "Created %s lines"%(str(len(rdtJson['lines'])))
		if debug==2:
			for elem in rdtJson['lines']: 
				print "   Line:"
				for a,val in elem.iteritems():
					print "      %s: %s"%(str(a), str(val))				
	return lineCount

def makeLineCodes(rdtJson, jsonTree, lineCount, dataDir, debug):
	'''line_codes: create one for each line.
	For now, use values from rdtInputTrevor.json.
	TODO*: keep track of which matrices have 0 for which phases, and use appropriate ones.
	TODO: Give special x/r matrices for transformers.
	TODO: Read x/r matrices from gridlabD csv recorder file.
	'''
	xMatrices, rMatrices = readXRMatrices(dataDir, 'xrMatrices.json', 100)
	for lineCode in range(0,lineCount):
		newLineCode = createObj('line_code')
		newLineCode['line_code'] = lineCode
		# Get phases and which phase a/b/c exists.
		newLineCode['num_phases'] = rdtJson['lines'][lineCode]['num_phases']
		if int(newLineCode['num_phases']) < 3: 
			phasesExist = rdtJson['lines'][lineCode]['has_phase']
		if int(newLineCode['num_phases']) == 3: 	
			# Set right x/r matrices for 3 phase.
			newLineCode['xmatrix'] = xMatrices[3][0]
			newLineCode['rmatrix'] = rMatrices[3][0]
			if len(xMatrices[3])>1: xMatrices[3].pop(0)
			if len(rMatrices[3])>1: rMatrices[3].pop(0)
		elif int(newLineCode['num_phases']) == 2: 
			# Set it for 2 phase.
			xMatrix = [[0.26732955, 0.12200757999999999, 0.0], [0.12200757999999999, 0.27047349, 0.0], [0.0, 0.0, 0.0]]
			rMatrix = [[0.36553030, 0.04407197, 0.0], [0.04407197, 0.36282197, 0.0], [0.0, 0.0, 0.0]]
			newLineCode['xmatrix'] = xMatrix
			newLineCode['rmatrix'] = rMatrix				
			print "      ****THIS LINECODE:\n      %s\n      ISNT TESTED FOR THIS OBJECT:\n      %s\n      NEED A 2 PHASE LINE FEEDER."%(rdtJson['lines'][lineCode], newLineCode)
		else:
			# Set it for 1 phase.
			xMatrix = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
			rMatrix = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
			for i,exists in enumerate(phasesExist):
				if exists:
					# Set xmatrix.
					for xSubMatrix in xMatrices[1][0]:
						for val in xSubMatrix:
							if float(val) != 0.0: 
								xMatrix[0][i] = val
								break
					# Set rmatrix.
					for rSubMatrix in rMatrices[1][0]:
						for val in rSubMatrix:
							if float(val) != 0.0: 
								rMatrix[0][i] = val
								break
			newLineCode['xmatrix'] = xMatrix
			newLineCode['rmatrix'] = rMatrix	
		#SET THE newLineCode to the output of GRIDLABD								
		rdtJson['line_codes'].append(newLineCode)
	if debug==True:
		print "Created %s line_codes"%(str(len(rdtJson['line_codes'])))
		if debug==2:
			for elem in rdtJson['line_codes']: 
				print "   Line_Code:"
				for a,val in elem.iteritems():
					print "      %s: %s"%(str(a), str(val))

def makeBuses(rdtJson, jsonTree, debug):
	'''buses.
	Ziploads? house? regulator? Waterheater?
	'''
	objToFind = ['node', 'triplex_node', 'triplex_meter']
	for key, bus in jsonTree.iteritems():
		# if bus.get('object','') in objToFind and bus.get('bustype','').lower() != 'swing':
		if bus.get('object','').lower() in objToFind:
			newBus = createObj('bus')
			newBus['id'] = bus.get('name','')+'_bus'
			if bus.get('bustype','').lower() == 'swing':
				newBus['has_generator'] = True
			numPhases, newBus['has_phase'], max_real_phase, max_reactive_phase = getNodePhases(bus)
			# Remove entries I couldn't find, 10.
			# newBus.pop('y',None)
			# newBus.pop('x',None)
			rdtJson['buses'].append(newBus)
			# newBus.pop('ref_voltage', None)
			# newBus.pop('min_voltage', None)
			# newBus.pop('max_voltage', None)
	if debug: 
		print "Created %s buses"%(str(len(rdtJson['buses'])))
		if debug==2:
			for elem in rdtJson['buses']: 
				print "   Bus:"
				for a,val in elem.iteritems():
					print "      %s: %s"%(str(a), str(val))

def makeLoads(rdtJson, jsonTree, debug):
	'''loads.
	TODO*: How do I calculate real_phase and reactive_phase?
	'''
	objToFind = ['triplex_meter']
	for key, loads in jsonTree.iteritems():
		if loads.get('object','') in objToFind:
			newLoad = createObj('load')
			newLoad['id'] = loads.get('name','')+'_lod'
			for elem in rdtJson['buses']:
				if elem['id'][0:-4] == newLoad['id'][0:-4]:
					busID = elem['id']
					if debug==2: 
						print "      **Found load: %s bus as: %s**"%(newLoad['id'], busID)
			newLoad['node_id'] = busID
			numPhases, newLoad['has_phase'], newLoad['max_real_phase'], newLoad['max_reactive_phase'] = getNodePhases(loads, 10, 10)
			# newLoad.pop('is_critical',None)
			rdtJson['loads'].append(newLoad)
	if debug: 
		print "Created %s loads"%(str(len(rdtJson['loads'])))
		if debug==2:
			for elem in rdtJson['loads']: 
				print "   Load:"
				for a,val in elem.iteritems():
					print "      %s: %s"%(str(a), str(val))				

def makeGens(rdtJson, jsonTree, debug):
	'''generators.
	'''
	for key, gens in jsonTree.iteritems():
		if gens.get('bustype','').lower() == 'swing':
			newGen = createObj('gen')
			newGen['id'] = gens.get('name','')+'_gen'
			for elem in rdtJson['buses']:
				if elem['id'][0:-4] == newGen['id'][0:-4]:
					busID = elem['id']
					if debug: 
						print "   **Found Generator: %s\n With bus  %s**"%(newGen['id'], busID)
			newGen['node_id'] = busID	
			numPhases, newGen['has_phase'], newGen['max_real_phase'], newGen['max_reactive_phase'] = getNodePhases(gens)
			rdtJson['generators'].append(newGen)
	if debug: 
		print "Created %s generators"%(str(len(rdtJson['generators'])))
		if debug==2:
			for elem in rdtJson['generators']: 
				print "   Generator:"
				for a,val in elem.iteritems():
					print "      %s: %s"%(str(a), str(val))

def readXRMatrices(dataDir, rdtFile, length):
	'''Read XR Matrices from rdtFile. Add gridlabD csv file reading later.
	'''
	xMatrix, rMatrix = {1: [], 2: [], 3: []}, {1: [], 2: [], 3: []}
	with open(pJoin(dataDir,rdtFile), "r") as jsonIn:
		lineCodes = json.load(jsonIn)['line_codes']
	for i,code in enumerate(lineCodes):
		if i > length: break
		xMatrix[int(code['num_phases'])].append(code['xmatrix'])
		rMatrix[int(code['num_phases'])].append(code['rmatrix'])
	return xMatrix, rMatrix

def convertToRDT(inData, dataDir, feederName, debug=False):
	'''Read a omd.json feeder and convert it to fragility/RDT format.
	'''
	# Create RDT dict.
	if debug:
		print "Generating RDT input..."
		print "************************************"
	rdtJson = {
		'phase_variation' : inData.get('phase_variation', 0.15), 
		'chance_constraint' : inData.get('chance_constraint', 1.0),
		'critical_load_met' : inData.get('critical_load_met',0.98),
		'total_load_met' : inData.get('total_load_met',0.5),
		'scenarios' : [createObj('scenario')], # Made up fragility damage scenario.
		'line_codes' : [],
		'lines' : [],
		'buses' : [],
		'loads' : [],
		'generators' : []	
	}
	# Read and put omd.json into rdt.json.
	with open(pJoin(dataDir,feederName), "r") as jsonIn:
		jsonTree = json.load(jsonIn).get('tree','')
	#TODO: get GFM scenarios in to RDT
	lineCount = makeLines(rdtJson, jsonTree, debug)
	makeLineCodes(rdtJson, jsonTree, lineCount, dataDir, debug)
	makeBuses(rdtJson, jsonTree, debug)
	makeLoads(rdtJson, jsonTree, debug)
	makeGens(rdtJson, jsonTree, debug)
	# Write to file.
	rdtInFile = 'rdtIn'+feederName.strip('omd')+'json'
	with open(pJoin(dataDir,rdtInFile), "w") as outFile:
		json.dump(rdtJson, outFile, indent=4)
	if debug:		
		print "Done... RDT input saved to:            %s"%(pJoin(dataDir,rdtInFile))
		print "************************************\n\n"
	return rdtInFile

def diagramPrep(workDir, dataDir, feederName, debug):
	# ... Steps here.
	# Run gridlabd.
	if debug:
		print "Running gridlabD..."
		print "************************************"
	# 1. Run gridlabD on circuit.
	feederJson = json.load(open(pJoin(dataDir,feederName)))
	tree = feederJson.get("tree",{})
	attachments = feederJson.get("attachments",{})
	# 2. Read output.
	if debug:
		print "DID NOT RUN gridlabD. Results saved to:                 %s"%("N/A")
		print "************************************\n\n"
	return feederJson

def genDiagram(dataDir, feederJson, debug):
	if debug:
		print "Generating Feeder plot..."
		print "************************************"
	links = feederJson.get("links",{})
	tree = feederJson.get("tree", {})
	toRemove = []
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
							elif 'config' in leaf.get('object','') or 'climate' in leaf.get('object','') or 'conductor' in leaf.get('object','') or 'solver_method' in leaf or 'omftype' in leaf or 'clock' in leaf or 'module' in leaf:
								if x not in toRemove: toRemove.append(x)
	for rem in toRemove: tree.pop(rem)
	nxG = feeder.treeToNxGraph(tree)
	feeder.latLonNxGraph(nxG) # This function creates a .plt reference which can be saved here.
	plt.savefig(pJoin(dataDir,"feederChart.png"))
	if debug:
		print "Plot saved to:                 %s"%(pJoin(dataDir,"feederChart.png"))
		print "************************************\n\n"

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	startTime = dt.datetime.now()
	outData = {}
	with open(pJoin(modelDir,'allInputData.json')) as inputFile:    
	    allInputData = json.load(inputFile)
	    feederName = allInputData.get('feederName1','feeder')
	inputDict["feederName1"] = feederName
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(dt.datetime.now())
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	# Set up environment and paths
	# TODO: single work and dataDir for RDT.
	workDir = modelDir
	dataDir = modelDir
	rdtInData = {'phase_variation' : 0.15, 'chance_constraint' : 1.0, 'critical_load_met' : 0.98, 'total_load_met' : 0.5}
	feederName = allInputData['feederName1'] + '.omd'
	# TODO: investigate debug flag uses.
	debug = False
	with open(pJoin(modelDir,'xrMatrices.json'),'w') as xrMatrixFile:
		json.dump(json.loads(allInputData['xrMatrices']),xrMatrixFile, indent=4)
	rdtInFile = dataDir + '/' + convertToRDT(rdtInData, dataDir, feederName, debug)
	rdtInFile = dataDir + '/' + convertToRDT(rdtInData, dataDir, feederName, debug)
	rdtOutFile = dataDir + '/rdtOutput.json'
	# Generate the input file for GFM:
	fragIn = {}
	with open(pJoin(modelDir, 'allInputData.json'), 'r') as allInputData:
		allInputData = json.load(allInputData)
	fragInputBase = json.loads(allInputData['poleData'])
	baseAsset = fragInputBase['assets'][1]
	fragIn['assets'] = []
	fragIn['hazardFields'] = fragInputBase['hazardFields']
	fragIn['responseEstimators'] = fragInputBase['responseEstimators']
	with open(pJoin(modelDir,allInputData['weatherImpactsFileName']),'w') as hazardFile:
		hazardFile.write(allInputData['weatherImpacts'])
	if(platform.system() == "Windows"):  # HACK: do the world's worst URLENCODE:
		hazardAscPath = 'file:///' + pJoin(modelDir, allInputData['weatherImpactsFileName']).replace(' ','%20')
		hazardAscPath = hazardAscPath.replace('\\', '/')
	else: #for UNIX
		hazardAscPath = 'file://' + pJoin(modelDir, allInputData['weatherImpactsFileName']).replace(' ','%20')
	fragIn['hazardFields'][0]['rasterFieldData']['uri'] = hazardAscPath # HACK: just consider one hazard field.
	with open(pJoin(modelDir, allInputData['feederName1'] + '.omd'), "r") as jsonIn:
		feederModel = json.load(jsonIn)
	# Pull pole lat/lon data from OMD and add to pole system.
	for key in feederModel['tree'].keys():
		asset = copy.deepcopy(baseAsset)
		asset['id'] = key
		if "longitude" in feederModel['tree'][key] and 'latitude' in feederModel['tree'][key]:
			asset['assetGeometry']['coordinates'] = [feederModel['tree'][key]['longitude'], feederModel['tree'][key]['latitude']]
		fragIn['assets'].append(asset)
	with open(pJoin(modelDir, "gfmInput.json"), "w") as outFile:
		json.dump(fragIn, outFile, indent=4)
	# Run GFM.
	gfmBinaryPath = pJoin(__metaModel__._omfDir,'solvers','gfm', 'Fragility.jar')
	inputFilePath = pJoin(modelDir, 'gfmInput.json')
	gfmOutFileName = 'gfmOutput.json'
	outFilePath = pJoin(modelDir, gfmOutFileName)
	proc = subprocess.Popen(['java','-jar', gfmBinaryPath, inputFilePath, outFilePath])
	proc.wait()
	gfmRawOut = open(pJoin(modelDir,gfmOutFileName)).read()
	outData['gfmRawOut'] = gfmRawOut
	print 'Ran Fragility\n'
	# Run RDT.
	debug = False #TODO: remove.
	print "Running RDT..."
	print "************************************"
	rdtSolverFolder = pJoin(__metaModel__._omfDir,'solvers','rdt')
	rdtJarPath = pJoin(rdtSolverFolder,'micot-rdt.jar')
	proc = subprocess.Popen(['java', "-Djna.library.path=" + rdtSolverFolder, '-jar', rdtJarPath, '-c', rdtInFile, '-e', rdtOutFile])
	proc.wait()
	rdtRawOut = open(rdtOutFile).read()
	outData['rdtRawOut'] = rdtRawOut
	# Format output feeder.
	with open(pJoin(rdtOutFile), "r") as jsonIn:
		rdtOut = json.load(jsonIn)
	with open(pJoin(rdtOutFile),"w") as outFile:
		json.dump(rdtOut, outFile, indent = 4)
	print "\nOutput saved to:               %s"%(pJoin(dataDir, rdtOutFile))
	print "************************************\n\n"
	# Run GridLAB-D first time to generate xrMatrices. #TODO: integrate GLD990.
	feederJson = json.load(open(pJoin(modelDir,feederName)))
	tree = feederJson.get("tree",{})
	attachments = feederJson.get("attachments",{})
	climateFileName, latforpvwatts = zipCodeToClimateName(allInputData["simulationZipCode"])
	shutil.copy(pJoin(__metaModel__._omfDir, "data", "Climate", climateFileName + ".tmy2"), pJoin(modelDir, 'climate.tmy2'))
	gridlabdRawOut = gridlabd.runInFilesystem(tree, attachments=attachments, workDir=modelDir)
	outData['gridlabdRawOut'] = gridlabdRawOut
	# Draw the feeder.
	feederJson = diagramPrep(workDir, dataDir, feederName, debug)
	genDiagram(dataDir, feederJson, debug)
	with open(pJoin(modelDir,"feederChart.png"),"rb") as inFile:
		outData["oneLineDiagram"] = inFile.read().encode("base64")
	# Save the output to disk.
	with open(pJoin(modelDir,'allOutputData.json'),'w') as outFile:
		json.dump(outData, outFile, indent=4)
	
def cancel(modelDir):
	''' Voltage drop runs so fast it's pointless to cancel a run. '''
	pass

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "Simple Market System",
		"modelType": modelName,
		"runTime": "0:00:30",
		"layoutAlgorithm": "geospatial",
		"modelName": modelDir,
		"user": "admin",
		"created": "",
		"lineFixedCost": "0.0",
		"lineUnitCost": "0.0",
		"switchCost": "0.0",
		"dgFixedCost": "0.0",
		"dgUnitCost": "0.0",
		"hardeningFixedCost": "0.0",
		"hardeningUnitCost": "0.0",
		"maxDGPerGenerator": "0.0",
		"hardeningCandidates": "Line_id1, line_id2",
		"newLineCandidates": "(node1,node2),(node3,node4)",
		"generatorCandidates": "node1",
		"criticalLoadMet": "0.0",
		"nonCriticalLoadMet": "0.0",
		"chanceConstraint": "0.0",
		"phaseVariation": "0.0",
		"weatherImpacts": open(pJoin(__metaModel__._omfDir,"scratch","uploads","WindGrid_lpnorm_example.asc")).read(),
		"weatherImpactsFileName": "WindGrid_lpnorm_example.asc",
		"poleData": open(pJoin(__metaModel__._omfDir,"scratch","uploads","_fragility_input_example.json")).read(),
		"poleDataFileName": "_fragility_input_example.json",
		"xrMatrices":open(pJoin(__metaModel__._omfDir,"scratch","uploads","rdtInSimple_Market_System.json")).read(),
		"xrMatricesFileName":"rdtInSimple_Market_System.json",
		"simulationDate": "2012-01-01",
		"simulationZipCode": "64735"
	}
	#print defaultInputs
	creationCode = __metaModel__.new(modelDir, defaultInputs)
	try:
		# Copy the feeder from one place to another
		shutil.copyfile(pJoin(__metaModel__._omfDir, "scratch", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _runModel():
	# Location
	modelLoc = pJoin(__metaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
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
	run(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_runModel()
	
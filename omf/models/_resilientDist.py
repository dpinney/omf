''' Run micot-GFM, micot-RDT, and GridLAB-D to determine an optimal distribution resiliency investment. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback, copy, platform
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
import subprocess, random, webbrowser, multiprocessing
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
with open(pJoin(__neoMetaModel__._myDir,modelName+".html"),"r") as tempFile:
	template = Template(tempFile.read())

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
		'total_load_met' : gfmInputTemplate.get('total_load_met',0.5),
		'chance_constraint' : gfmInputTemplate.get('chance_constraint', 1.0),
		'phase_variation' : gfmInputTemplate.get('phase_variation', 0.15),
		'scenarios' : [] # Made up fragility damage scenario.
	}
	# Get necessary data from .omd.
	jsonTree = feederModel.get('tree',{})
	jsonNodes = feederModel.get('nodes',[])
	#Line Creation
	hardCands = gfmInputTemplate['hardeningCandidates'].strip().replace(' ', '').split(',')
	newLineCands = gfmInputTemplate["newLineCandidates"].strip().replace(' ', '').split(',')

	objToFind = ['transformer', 'regulator', 'underground_line', 'overhead_line']
	lineCount = 0
	for key, line in jsonTree.iteritems():
		if line.get('object','') in objToFind:
			newLine = dict({
				'id' : '', #*
				'node1_id' : '', #*
				'node2_id' : '', #*
				'line_code' : '', #*
				'length' : 1.0, #* Units match line code entries.
				# 'has_switch' : False,
				# 'construction_cost': 100,
				# 'harden_cost': 100000, # Russel: this exists unless its a trans.
				# 'switch_cost': 15, # taken from rdtInTrevor.json.
				'can_harden': False, # Not seen in rdtInTrevor.json.
				# 'can_add_switch': False, # Not seen in rdtInTrevor.json.
				# 'num_poles' : 2,
				# 'capacity' : 5780, # MVA capacity.
				'is_transformer' : False,
				'num_phases' : 3, #*
				# 'is_new' : False,
				'has_phase' : [True, True, True] #*
			})
			newLine['id'] = line.get('name','')
			newLine['node1_id'] = line.get('from','')+'_bus' 
			newLine['node2_id'] = line.get('to','')+'_bus'
			newLine['length'] = float(line.get('length',100))
			newLine['line_code'] = lineCount
			# Calculate harden_cost, 10.
			# newLine['capacity'] = 1000000000 # Set it arbitrarily high.
			if line.get('name','') in hardCands:
				newLine['can_harden'] = True
			if line.get('name','') in newLineCands:
				newLine["is_new"] = True
			if line.get('object','') in ['transformer','regulator']: 
				newLine['is_transformer'] = True
 			gfmJson['lines'].append(newLine)
			lineCount+=1
	# Line Code Creation
	xMatrices, rMatrices = {1: [], 2: [], 3: []}, {1: [], 2: [], 3: []}
	lineCodes = json.loads(gfmInputTemplate['xrMatrices'])['line_codes']
	for i,code in enumerate(lineCodes):
		if i > 100: break
		xMatrices[int(code['num_phases'])].append(code['xmatrix'])
		rMatrices[int(code['num_phases'])].append(code['rmatrix'])
	for lineCode in range(0,lineCount):
		newLineCode = dict({
			'line_code': '', #*
			'num_phases': '', #*
			'xmatrix': [[],[],[]], #* reactance terms: phaseA, phaseB, and phaseC.
			'rmatrix': [[],[],[]] #* resistance terms: phaseA/B/C.
		})
		newLineCode['line_code'] = lineCode
		# Get phases and which phase a/b/c exists.
		newLineCode['num_phases'] = gfmJson['lines'][lineCode]['num_phases']
		if int(newLineCode['num_phases']) < 3: 
			phasesExist = gfmJson['lines'][lineCode]['has_phase']
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
		gfmJson['line_codes'].append(newLineCode)
	# Bus creation:
	objToFind = ['node', 'load']
	for key, bus in jsonTree.iteritems():
		# if bus.get('object','') in objToFind and bus.get('bustype','').lower() != 'swing':
		if bus.get('object','').lower() in objToFind:
			newBus = dict({
				'id': '', #*
				# 'min_voltage': 0.8, # in p.u.
				# 'max_voltage': 1.2, # in p.u.
				'y': '', # not in schema.
				'x': '', # not in schema.
				# 'has_generator': False,
				# 'has_phase': [True, True, True],
				# 'ref_voltage': [1.0, 1.0, 1.0]
				# 'ref_voltage': 1.0 # From github.
			})
			newBus['id'] = bus.get('name','')+'_bus'
			numPhases, newBus['has_phase'], max_real_phase, max_reactive_phase = getNodePhases(bus, 0.0)
			gfmJson['buses'].append(newBus)
			for busNode in jsonNodes:
				# HACK: sometimes keys are strings. Sometimes not.
				if int(key) == busNode.get('treeIndex',0):
					# HACK: nice coords for GFM which wants lat/lon.
					newBus['y'] = busNode.get('y')/5000.0
					newBus['x'] = busNode.get('x')/5000.0
	# Load creation:
	objToFind = ['load']
	for key, loads in jsonTree.iteritems():
		if loads.get('object','') in objToFind:
			newLoad = dict({
				'id': '', #*
				'node_id': '', #*
				'is_critical': False, 
				'max_real_phase': [], #*
				'max_reactive_phase': [], #*
				'has_phase': [] #*
			})
			newLoad['id'] = loads.get('name','')+'_lod'
			for elem in gfmJson['buses']:
				if elem['id'][0:-4] == newLoad['id'][0:-4]:
					busID = elem['id']
			newLoad['node_id'] = busID
			numPhases, newLoad['has_phase'], newLoad['max_real_phase'], newLoad['max_reactive_phase'] = getNodePhases(loads, 10)
			# newLoad.pop('is_critical',None)
			gfmJson['loads'].append(newLoad)
	# Generator creation:
	for key, gens in jsonTree.iteritems():
		if gens.get('bustype','').lower() == 'swing':
			genID = gens.get('name','')+'_gen'
			for elem in gfmJson['buses']:
				if elem['id'][0:-4] == genID[0:-4]:
					busID = elem['id']
			numPhases, has_phase, max_real_phase, max_reactive_phase = getNodePhases(gens, gfmInputTemplate['maxDGPerGenerator'])
			genObj = dict({
	 			'id': gens.get('name','')+'_gen', #*
				'node_id': busID, #*
				# 'is_new': False, # Whether or not new generation can be built.
				# 'microgrid_cost': 1.5, # Per MW capacity of building DG.
				# 'max_microgrid': 0, # Max additional capacity for this gen.
				# 'microgrid_fixed_cost': 0, # One-time fixed cost for building DG.
				'has_phase': has_phase, #*
				'max_reactive_phase': max_reactive_phase, #*
				'max_real_phase': max_real_phase #*
			})
			# BUG: GENERATORS ADDED TO ALL SWING BUSES: gfmJson['generators'].append(genObj)
	# Return 
	return gfmJson

def genDiagram(outputDir, feederJson):
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
	nxG = feeder.treeToNxGraph(tree)
	feeder.latLonNxGraph(nxG) # This function creates a .plt reference which can be saved here.
	plt.savefig(pJoin(outputDir,"feederChart.png"))	

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	feederName = inputDict["feederName1"]
	with open(pJoin(modelDir,inputDict['weatherImpactsFileName']),'w') as hazardFile:
		hazardFile.write(inputDict['weatherImpacts'])
	with open(pJoin(modelDir, feederName + '.omd'), "r") as jsonIn:
		feederModel = json.load(jsonIn)
	# Create GFM input file.
	print "Running GFM ************************************"
	gfmInputTemplate = {
		'phase_variation' : float(inputDict['phaseVariation']),
		'chance_constraint' : float(inputDict['chanceConstraint']),
		'critical_load_met' : float(inputDict['criticalLoadMet']),
		'total_load_met' : (float(inputDict['criticalLoadMet']) + float(inputDict['nonCriticalLoadMet'])),
		'xrMatrices' : inputDict["xrMatrices"],
		'maxDGPerGenerator' : float(inputDict["maxDGPerGenerator"]),
		'newLineCandidates' : inputDict['newLineCandidates'],
		'hardeningCandidates' : inputDict['hardeningCandidates']
	}
	gfmJson = convertToGFM(gfmInputTemplate, feederModel)
	gfmInputFilename = 'gfmInput.json'
	with open(pJoin(modelDir, gfmInputFilename), "w") as outFile:
		json.dump(gfmJson, outFile, indent=4)
	# Run GFM
	gfmBinaryPath = pJoin(__neoMetaModel__._omfDir,'solvers','gfm', 'Fragility.jar')
	proc = subprocess.Popen(['java','-jar', gfmBinaryPath, '-r', gfmInputFilename, '-wf', inputDict['weatherImpactsFileName'],'-num','3'], cwd=modelDir)
	proc.wait()
	# HACK: rename the hardcoded gfm output
	rdtInputFilePath = pJoin(modelDir,'rdtInput.json')
	os.rename(pJoin(modelDir,'rdt_OUTPUT.json'),rdtInputFilePath)
	# Pull GFM input data on lines and generators for HTML presentation.
	with open(rdtInputFilePath, 'r') as rdtInputFile:
		# HACK: we use rdtInput as a string in the frontend.
		rdtJsonAsString = rdtInputFile.read()
		rdtJson = json.loads(rdtJsonAsString)
	# Calculate line costs.
	lineData = []
	for line in rdtJson["lines"]:
		lineData.append((line["id"], '{:,.2f}'.format(float(line["length"]) * float(inputDict["lineUnitCost"]))))
	outData["lineData"] = lineData
	outData["generatorData"] = '{:,.2f}'.format(float(inputDict["dgUnitCost"]) * float(inputDict["maxDGPerGenerator"]))
	outData['gfmRawOut'] = rdtJsonAsString
	# Run GridLAB-D first time to generate xrMatrices.
	if platform.system() == "Windoze":
		omdPath = pJoin(modelDir, feederName + ".omd")
		with open(omdPath, "r") as omd:
			omd = json.load(omd)
		#REMOVE NEWLINECANDIDATES
		'''deleteList = []
		newLines = inputDict["newLineCandidates"].strip().replace(' ', '').split(',')
		for newLine in newLines:
			for omdObj in omd["tree"]:
				if ("name" in omd["tree"][omdObj]):
					if (newLine == omd["tree"][omdObj]["name"]):
						deleteList.append(omdObj)
		for delItem in deleteList:
			print delItem
			del omd["tree"][delItem]
		'''
		#Load a blank glm file and use it to write to it
		feederPath = pJoin(modelDir, 'feeder.glm')
		with open(feederPath, 'w') as glmFile:
			toWrite =  omf.feeder.sortedWrite(omd['tree']) + "object jsondump {\n\tfilename_dump_reliability test_JSON_dump1.json;\n\twrite_reliability true;\n\tfilename_dump_line test_JSON_dump2.json;\n\twrite_line true; };\n"# + "object jsonreader {\n\tfilename " + insertRealRdtOutputNameHere + ";\n};"
			glmFile.write(toWrite)		
		#Write attachments from omd, if no file, one will be created
		for fileName in omd['attachments']:
			with open(os.path.join(modelDir, fileName),'w') as file:
				file.write(omd['attachments'][fileName])
		#Wire in the file the user specifies via zipcode.
		climateFileName, latforpvwatts = zipCodeToClimateName(inputDict["simulationZipCode"])
		shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", climateFileName + ".tmy2"), pJoin(modelDir, 'climate.tmy2'))
		proc = subprocess.Popen(['gridlabd', 'feeder.glm'], stdout=subprocess.PIPE, shell=True, cwd=modelDir)
		(out, err) = proc.communicate()
		accumulator = ""
		'''with open(pJoin(modelDir, "test_JSON_dump1.json"), "r") as gldOut:
			accumulator = json.load(gldOut)'''
		with open(pJoin(modelDir, "test_JSON_dump2.json"), "r") as gldOut:
			accumulator = json.load(gldOut)
		outData['gridlabdRawOut'] = accumulator
	else:
		tree = feederModel.get("tree",{})
		attachments = feederModel.get("attachments",{})
		climateFileName, latforpvwatts = zipCodeToClimateName(inputDict["simulationZipCode"])
		shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", climateFileName + ".tmy2"), pJoin(modelDir, 'climate.tmy2'))
		gridlabdRawOut = gridlabd.runInFilesystem(tree, attachments=attachments, workDir=modelDir)
		outData['gridlabdRawOut'] = gridlabdRawOut
	# Run RDT.
	print "Running RDT ************************************"
	rdtOutFile = modelDir + '/rdtOutput.json'
	rdtSolverFolder = pJoin(__neoMetaModel__._omfDir,'solvers','rdt')
	rdtJarPath = pJoin(rdtSolverFolder,'micot-rdt.jar')
	proc = subprocess.Popen(['java', "-Djna.library.path=" + rdtSolverFolder, '-jar', rdtJarPath, '-c', rdtInputFilePath, '-e', rdtOutFile])
	proc.wait()
	rdtRawOut = open(rdtOutFile).read()
	outData['rdtRawOut'] = rdtRawOut
	# Indent the RDT output nicely.
	with open(pJoin(rdtOutFile),"w") as outFile:
		rdtOut = json.loads(rdtRawOut)
		json.dump(rdtOut, outFile, indent = 4)
	# TODO: run GridLAB-D second time to validate RDT results with new control schemes.
	# Draw the feeder.
	genDiagram(modelDir, feederModel)
	with open(pJoin(modelDir,"feederChart.png"),"rb") as inFile:
		outData["oneLineDiagram"] = inFile.read().encode("base64")
	return outData

def cancel(modelDir):
	''' The model runs so fast it's pointless to cancel a run. '''
	pass

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "trip37",
		"modelType": modelName,
		"runTime": "0:00:30",
		"layoutAlgorithm": "geospatial",
		"modelName": modelDir,
		"user": "admin",
		"created": str(dt.datetime.now()),
		"lineUnitCost": "3000.0",
		"switchCost": "1000.0",
		"dgUnitCost": "200.0",
		"hardeningUnitCost": "1000.0",
		"maxDGPerGenerator": "5000.0",
		"hardeningCandidates": "A_node705-742,A_node705-712,A_node706-725",
		"newLineCandidates": "TIE_A_to_C,TIE_C_to_B,TIE_B_to_A",
		"generatorCandidates": "A_node706,A_node707,A_node708,B_node704,B_node705,B_node703",
		"criticalLoadMet": "0.98",
		"nonCriticalLoadMet": "0.0",
		"chanceConstraint": "1.0",
		"phaseVariation": "0.15",
		"weatherImpacts": open(pJoin(__neoMetaModel__._omfDir,"scratch","uploads","wf_clip.asc")).read(),
		"weatherImpactsFileName": "wf_clip.asc",
		"xrMatrices":open(pJoin(__neoMetaModel__._omfDir,"scratch","uploads","lineCodesTrip37.json")).read(),
		"xrMatricesFileName":"lineCodesTrip37.json",
		"simulationDate": "2012-01-01",
		"simulationZipCode": "64735"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		# Copy the feeder from one place to another
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "scratch", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
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
	runForeground(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_runModel()
	
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

class Line:
	lineCount = 0
	def __init__(self, id, node1, node2, length=1.0, lineCode=0, hardenCost=100000, numPhases=3, hasPhase=[True,True,True], isTransformer=None):
		self.id = id
		self.node1 = node1
		self.node2 = node2
		self.lineCode = Line.lineCount
		self.length = length
		self.hardenCost = hardenCost
		self.numPhases = numPhases
		self.hasPhase = hasPhase
		self.isTransformer = isTransformer
		self.is_new = False
		self.can_harden = False
		Line.lineCount += 1

	def checkNone(var):
		if var != None:
			return var

	def toOutput(line):
		lineOut = {}
		lineOut["id"] = line.id
		lineOut["node1_id"] = line.node1
		lineOut["node2_id"] = line.node2
		lineOut["line_code"] = line.lineCode
		lineOut["length"] = line.length
		lineOut["harden_cost"] = line.hardenCost
		lineOut["num_phases"] = line.numPhases
		lineOut["has_phase"] = line.hasPhase
		if line.isTransformer != None:
			lineOut["is_transformer"] = line.isTransformer
		lineOut["is_new"] = line.is_new
		lineOut["can_harden"] = line.can_harden
		return lineOut


class Gen:
	genCount = 0
	def __init__(self, id, node_id, has_phase=[True, True, True], max_reactive_phase=[1.7976931348623e+308, 1.7976931348623e+308, 1.7976931348623e+308], max_real_phase=[1.7976931348623e+308, 1.7976931348623e+308, 1.7976931348623e+308]):
		self.id = id
		self.node_id = node_id
		self.has_phase = has_phase
		self.max_reactive_phase = max_reactive_phase
		self.max_real_phase = max_real_phase
		Gen.genCount += 1

	def toOutput(gen):
		genOut = {}
		genOut["id"] = gen.id
		genOut["node_id"] = gen.node_id
		genOut["has_phase"] = gen.has_phase
		genOut["max_reactive_phase"] = gen.max_reactive_phase
		genOut["max_real_phase"] = gen.max_real_phase
		return genOut

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName+".html"),"r") as tempFile:
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
			'y': '', # not in schema.
			'x': '', # not in schema.
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

def getNodePhases(obj, maxRealPhase):
	'''read omd., 10json obj's phases and convert to rdt format.
	'''
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
	else:
		print "NO PHASES FOUND FOR OBJ:", obj	
	return numPhases, [hasphaseA, hasphaseB, hasphaseC], [maxRealPhaseA, maxRealPhaseB, maxRealPhaseC], [maxReactivePhaseA, maxReactivePhaseB, maxReactivePhaseC]

def makeLines(rdtJson, jsonTree, maxDG, newLines, hardCand, lineUnitCost, debug):
	''' lines.
	TODO: Put in accurate num_poles, ask if has_phase corresponds to a,b,c.
	TODO: Insert harden_cost calc.
	'''
	lineCosts = []
	hardCands = hardCand.strip().replace(' ', '').split(',')
	objToFind, lineCount = ['triplex_line','transformer', 'regulator', 'underground_line'], 0
	for key, line in jsonTree.iteritems():
		if line.get('object','') in objToFind:
			newLine = Line(line.get('name',''), line.get('from','')+'_bus', line.get('to','')+'_bus', float(line.get('length',100)))
			# Calculate harden_cost, 10.
			# newLine['capacity'] = 1000000000 # Set it arbitrarily high.
			if line.get('name','') in hardCands:
				newLine.can_harden = True
			if line.get('object','') == 'transformer': 
				#newLine['is_transformer'] = True
				newLine.isTransformer = True
				#newLine.pop('harden_cost',None)
 			rdtJson['lines'].append(newLine.toOutput())
			# print "Added newLine: %s (TOTAL: %s)\n"%(newLine, str(lineCount+1))
			lineCount+=1
			if newLine.can_harden == True:
				cost = 0
			else:
				cost = float(lineUnitCost)*float(line.get('length',100))
			lineCosts.append((line.get('name',''), cost))
	return lineCount, lineCosts

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

def makeBuses(rdtJson, jsonTree, jsonNodes, debug):
	'''buses.
	Ziploads? house? regulator? Waterheater?
	'''
	objToFind = ['node', 'triplex_node', 'triplex_meter', "load"]
	for key, bus in jsonTree.iteritems():
		# if bus.get('object','') in objToFind and bus.get('bustype','').lower() != 'swing':
		if bus.get('object','').lower() in objToFind:
			newBus = createObj('bus')
			newBus['id'] = bus.get('name','')+'_bus'
			if bus.get('bustype','').lower() == 'swing':
				newBus['has_generator'] = True
			numPhases, newBus['has_phase'], max_real_phase, max_reactive_phase = getNodePhases(bus, 0.0)
			rdtJson['buses'].append(newBus)
			for busNode in jsonNodes:
				if key == busNode.get('treeIndex'):
					newBus['y'] = busNode.get('y')#/1000.0
					newBus['x'] = busNode.get('x')#/1000.0

def makeLoads(rdtJson, jsonTree, debug):
	'''loads.
	TODO*: How do I calculate real_phase and reactive_phase?
	'''
	objToFind = ['triplex_meter', 'load']
	for key, loads in jsonTree.iteritems():
		if loads.get('object','') in objToFind:
			newLoad = createObj('load')
			newLoad['id'] = loads.get('name','')+'_lod'
			for elem in rdtJson['buses']:
				if elem['id'][0:-4] == newLoad['id'][0:-4]:
					busID = elem['id']
			newLoad['node_id'] = busID
			numPhases, newLoad['has_phase'], newLoad['max_real_phase'], newLoad['max_reactive_phase'] = getNodePhases(loads, 10)
			# newLoad.pop('is_critical',None)
			rdtJson['loads'].append(newLoad)		

def makeGens(rdtJson, jsonTree, maxRealPhase, newGens, debug):
	'''generators.
	'''
	for key, gens in jsonTree.iteritems():
		if gens.get('bustype','').lower() == 'swing':
			genID = gens.get('name','')+'_gen'
			for elem in rdtJson['buses']:
				if elem['id'][0:-4] == genID[0:-4]:
					busID = elem['id']
			numPhases, has_phase, max_real_phase, max_reactive_phase = getNodePhases(gens, maxRealPhase)
			newGen = Gen(gens.get('name','')+'_gen', busID, has_phase, max_reactive_phase, max_real_phase)
			rdtJson['generators'].append(newGen.toOutput())

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

def convertToRDT(inData, dataDir, feederName, maxDG, newLines, newGens, hardCand, lineUnitCost, debug=False):
	'''Read a omd.json feeder and convert it to fragility/RDT format.
	'''
	# Create RDT dict.
	if debug:
		print "Generating RDT input..."
		print "************************************"
	rdtJson = {
		'buses' : [],
		'loads' : [],
		'generators' : [],
		'line_codes' : [],
		'lines' : [],
		'critical_load_met' : inData.get('critical_load_met',0.98),
		'total_load_met' : inData.get('total_load_met',0.5),
		'chance_constraint' : inData.get('chance_constraint', 1.0),
		'phase_variation' : inData.get('phase_variation', 0.15),
		'scenarios' : [] # Made up fragility damage scenario.		
	}
	# Read and put omd.json into rdt.json.
	with open(pJoin(dataDir,feederName + '.omd'), "r") as jsonIn:
		jsonTree = json.load(jsonIn).get('tree','')
	with open(pJoin(dataDir,feederName + '.omd'), "r") as jsonIn:
		jsonNodes = json.load(jsonIn).get('nodes','')
	#TODO: get GFM scenarios in to RDT
	lineCount, lineCosts = makeLines(rdtJson, jsonTree, maxDG, newLines, hardCand, lineUnitCost, debug)
	makeLineCodes(rdtJson, jsonTree, lineCount, dataDir, debug)
	makeBuses(rdtJson, jsonTree, jsonNodes, debug)
	makeLoads(rdtJson, jsonTree, debug)
	makeGens(rdtJson, jsonTree, maxDG, newGens, debug)
	# Write to file.
	rdtInFile = 'gfmInput.json'
	with open(pJoin(dataDir,rdtInFile), "w") as outFile:
		json.dump(rdtJson, outFile, indent=4)
	if debug:		
		print "Done... RDT input saved to:            %s"%(pJoin(dataDir,rdtInFile))
		print "************************************\n\n"
	return rdtInFile, lineCosts

def genDiagram(dataDir, feederName, feederJson, debug):
	# Generate feeder diagram.
	feederJson = json.load(open(pJoin(dataDir,feederName + '.omd')))
	tree = feederJson.get("tree",{})
	if debug:
		print "Generating Feeder plot..."
		print "************************************"
	links = feederJson.get("links",{})
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

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	feederName = inputDict["feederName1"]
	with open(pJoin(modelDir,inputDict['weatherImpactsFileName']),'w') as hazardFile:
		hazardFile.write(inputDict['weatherImpacts'])
	with open(pJoin(modelDir, feederName + '.omd'), "r") as jsonIn:
		feederModel = json.load(jsonIn)
	# Run GFM.
	rdtInData = {'phase_variation' : float(inputDict['phaseVariation']), 'chance_constraint' : float(inputDict['chanceConstraint']), 'critical_load_met' : float(inputDict['criticalLoadMet']), 'total_load_met' : (float(inputDict['criticalLoadMet']) + float(inputDict['nonCriticalLoadMet']))}
	with open(pJoin(modelDir,'xrMatrices.json'),'w') as xrMatrixFile:
		json.dump(json.loads(inputDict['xrMatrices']),xrMatrixFile, indent=4)
	gfmInputFilename, lineCosts = convertToRDT(rdtInData, modelDir, feederName, inputDict["maxDGPerGenerator"], inputDict["newLineCandidates"], inputDict["generatorCandidates"], inputDict["hardeningCandidates"], inputDict["lineUnitCost"], debug=False)
	gfmBinaryPath = pJoin(__neoMetaModel__._omfDir,'solvers','gfm', 'Fragility.jar')
	# shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "solvers","gfm", 'rdt.json'), pJoin(modelDir, 'rdt.json'))
	# shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "solvers","gfm", 'wf_clip.asc'), pJoin(modelDir, 'wfclip.asc'))	
	proc = subprocess.Popen(['java','-jar', gfmBinaryPath, '-r', gfmInputFilename, '-wf', inputDict['weatherImpactsFileName'],'-num','3'], cwd=modelDir)
	# HACK: rename the hardcoded gfm output
	proc.wait()
	os.rename(pJoin(modelDir,'rdt_OUTPUT.json'),pJoin(modelDir,'rdtInput.json'))
	#test change
	#Denote new lines
	newLineCands = inputDict["newLineCandidates"].strip().replace(' ', '').split(',')
	'''with open(pJoin(modelDir,gfmOutFileName), "r") as gfmOut:
		gfmOut = json.load(gfmOut)
	for line in gfmOut['lines']:
		#set can_harden to false for transformers and regulators NO EXPLICIT IDENTIFIER FOR REGULATORS, ID ONLY
		if(line["is_transformer"] == True):
			line["can_harden"] = False
		for newLine in newLineCands:
			if(newLine == line['id']):
				line["is_new"] = True
	with open(pJoin(modelDir,gfmOutFileName),"w") as outFile:
		json.dump(gfmOut, outFile, indent = 4)
	'''
	gfmRawOut = open(pJoin(modelDir,gfmInputFilename)).read()		
	#extra step here, just set equal to gfmOut from above
	outData['gfmRawOut'] = gfmRawOut
	print 'Ran Fragility\n'
	# Run GridLAB-D first time to generate xrMatrices.
	if platform.system() == "Windoze":
		#GridlabD
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
		#Load an blank glm file and use it to write to it
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
		with open(pJoin(modelDir, "test_JSON_dump1.json"), "r") as gldOut:
			accumulator = json.load(gldOut)
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
	print "Running RDT..."
	print "************************************"
	rdtInFile = modelDir + '/' + 'rdtInput.json'
	rdtOutFile = modelDir + '/rdtOutput.json'
	rdtSolverFolder = pJoin(__neoMetaModel__._omfDir,'solvers','rdt')
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
	print "\nOutput saved to: %s"%(pJoin(modelDir, rdtOutFile))
	print "************************************\n\n"

	# TODO: run GridLAB-D second time to validate RDT results with new control schemes.
	#newFeederModel = copy.deepcopy(feederModel)

	#Deriving line names from RDT Input and line lengths from feeder omd file
	#Building hashmap of source and target nodes, used to represent lines.
	with open(rdtInFile, "r") as rdtInFileData:
		rdtInFileData = json.load(rdtInFileData)
	lineData = []

	for line in rdtInFileData["lines"]:
		lineData.append((line["id"], '{:,.2f}'.format(float(line["length"]) * float(inputDict["lineUnitCost"]))))
	outData["lineData"] = lineData
	outData["generatorData"] = '{:,.2f}'.format(float(inputDict["dgUnitCost"]) * float(inputDict["maxDGPerGenerator"]))

	# Draw the feeder.
	genDiagram(modelDir, feederName, feederModel, debug=False)
	with open(pJoin(modelDir,"feederChart.png"),"rb") as inFile:
		outData["oneLineDiagram"] = inFile.read().encode("base64")
	return outData

def cancel(modelDir):
	''' The model runs so fast it's pointless to cancel a run. '''
	pass

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "trip37_worksRdt",
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
		"weatherImpacts": open(pJoin(__neoMetaModel__._omfDir,"solvers","gfm","wf_clip.asc")).read(),
		"weatherImpactsFileName": "wf_clip.asc",
		"xrMatrices":open(pJoin(__neoMetaModel__._omfDir,"scratch","uploads","rdtInSimple_Market_System.json")).read(),
		"xrMatricesFileName":"rdtInSimple_Market_System.json",
		"simulationDate": "2012-01-01",
		"simulationZipCode": "64735"
	}
	#print defaultInputs
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
	
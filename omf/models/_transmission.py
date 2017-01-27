''' The transmission model pre-alpha release.
Requirements: GNU octave
Tested on Linux and macOS.
'''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, math
import multiprocessing
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *
import pprint as pprint

# OMF imports
sys.path.append(__metaModel__._omfDir) # for images in test.
import network

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "The transmission model imports, runs and visualizes MATPOWER transmission and generation simulations."

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,modelName + ".html"),"r") as tempFile:
	template = Template(tempFile.read())

# def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
# 	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	''' Render the model template to an HTML string.
	By default render a blank one for new input.
	If modelDir is valid, render results post-model-run.
	If absolutePaths, the HTML can be opened without a server. '''
	try:
		inJson = json.load(open(pJoin(modelDir,"allInputData.json")))
		modelPath, modelName = pSplit(modelDir)
		deepPath, user = pSplit(modelPath)
		inJson["modelName"] = modelName
		inJson["user"] = user
		allInputData = json.dumps(inJson)
	except IOError:
		allInputData = None
	try:
		allOutputData = open(pJoin(modelDir,"allOutputData.json")).read()
	except IOError:
		allOutputData = None
	if absolutePaths:
		# Parent of current folder.
		pathPrefix = __metaModel__._omfDir
	else:
		pathPrefix = ""
	return template.render(allInputData=allInputData,
		allOutputData=allOutputData, modelStatus=getStatus(modelDir), pathPrefix=pathPrefix, datastoreNames=datastoreNames, modelName=modelName)

def run(modelDir, inputDict):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
	except Exception, e:
		pass
	try:
		os.remove(pJoin(modelDir,inputDict.get("networkName1","network1")+".m"))
	except Exception, e:
		pass		
	try:
		os.remove(pJoin(modelDir,"matout.txt"))
	except Exception, e:
		pass
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(datetime.datetime.now())
	# Write input and send run to another process.
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	backProc = multiprocessing.Process(target = runForeground, args = (modelDir, inputDict,))
	backProc.start()
	print "SENT TO BACKGROUND", modelDir
	with open(pJoin(modelDir, "PPID.txt"),"w+") as pPidFile:
		pPidFile.write(str(backProc.pid))

def runForeground(modelDir, inputDict):
	''' Run the model in its directory.'''
	try:
		startTime = datetime.datetime.now()
		outData = {
			'tableData' : {'volts': [[],[]], 'powerReal' : [[],[]], 'powerReact' : [[],[]]},
			# 'charts' : {'volts' : '', 'powerReact' : '', 'powerReal' : ''},
			'voltsChart' : '', 'powerReactChart' : '', 'powerRealChart' : '',
			'stdout' : '', 'stderr' : ''
			}
		# Model operations go here.
		# Read feeder and convert to .mat.
		networkName = inputDict.get('networkName1','case9')
		networkJson = json.load(open(pJoin(modelDir,networkName+".omt")))
		matStr = network.netToMat(networkJson, networkName)
		with open(pJoin(modelDir,networkName+".m"),"w") as outMat:
			for row in matStr: outMat.write(row)		
		# Get MATPOWER directories for the Octave path.
		matDir =  pJoin(__metaModel__._omfDir,'solvers','matpower5.1')
		matPath = '"' + ":".join([matDir,pJoin(matDir,'t'),pJoin(matDir,'extras')]) + '"'
		# Configure and run MATPOWER.
		algorithm = inputDict.get("algorithm","NR")
		pfArg = "\'pf.alg\', \'"+algorithm+"\'"
		modelArg = "\'model\', \'"+inputDict.get("model","AC")+"\'"
		iterCode = "pf."+algorithm[:2].lower()+".max_it"
		pfItArg = "\'"+iterCode+"\', "+str(inputDict.get("iteration",10))
		pfTolArg = "\'pf.tol\', "+str(inputDict.get("tolerance",math.pow(10,-8)))
		pfEnflArg = "\'pf.enforce_q_lims\', "+str(inputDict.get("genLimits",0))
		mpoptArg = "mpopt = mpoption("+pfArg+", "+modelArg+", "+pfItArg+", "+pfTolArg+", "+pfEnflArg+"); "
		command = "octave -p" + matPath + "--no-gui --eval \""+mpoptArg+"runpf(\'"+pJoin(modelDir,networkName+'.m')+"\', mpopt)\" > \"" + pJoin(modelDir,"matout.txt") + "\""
		print "command:", command
		proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
		(out, err) = proc.communicate()
		# SKELETON code.
		imgSrc = pJoin(__metaModel__._omfDir,'scratch','transmission','inData')
		# Read matout.txt and parse into outData.
		gennums=[]
		todo = None
		with open(pJoin(modelDir,"matout.txt")) as f:
			for i,line in enumerate(f):
				# Determine what type of data is coming up.
				if "How many?" in line:
					todo = "count"
				elif "Generator Data" in line:
					todo = "gen"
					lineNo = i
				elif "Bus Data" in line:
					todo = "node"
					lineNo = i
				elif "Branch Data" in line:
					todo = "line"
					lineNo = i
				# Parse lines.
				line = line.split(' ')
				line = filter(lambda a: a!= '', line)
				if todo=="count":
					if "Buses" in line:
						busCount = int(line[1])
					elif "Generators" in line:
						genCount = int(line[1])
					elif "Loads" in line:
						loadCount = int(line[1])
					elif "Branches" in line:
						branchCount = int(line[1])
					elif "Transformers" in line:
						transfCount = int(line[1])
						todo = None
				elif todo=="gen":
					if i>(lineNo+4) and i<(lineNo+4+genCount+1):
						# gen bus numbers.
						gennums.append(line[1])
					elif i>(lineNo+4+genCount+1):
						todo = None
				elif todo=="node":
					if i>(lineNo+4) and i<(lineNo+4+busCount+1):
						# voltage
						if line[0] in gennums: comp="gen"
						else: comp="node"
						outData['tableData']['volts'][0].append(comp+str(line[0]))
						outData['tableData']['powerReal'][0].append(comp+str(line[0]))
						outData['tableData']['powerReact'][0].append(comp+str(line[0]))
						outData['tableData']['volts'][1].append(line[1])
						outData['tableData']['powerReal'][1].append(line[3])
						outData['tableData']['powerReact'][1].append(line[4])
					elif i>(lineNo+4+busCount+1):
						todo = None
				elif todo=="line":
					if i>(lineNo+4) and i<(lineNo+4+branchCount+1):
						# power
						outData['tableData']['powerReal'][0].append("line"+str(line[0]))
						outData['tableData']['powerReact'][0].append("line"+str(line[0]))
						outData['tableData']['powerReal'][1].append(line[3])
						outData['tableData']['powerReact'][1].append(line[4])
					elif i>(lineNo+4+branchCount+1):
						todo = None
		# Massage the data.
		for powerOrVolt in outData['tableData'].keys():
			for i in range(len(outData['tableData'][powerOrVolt][1])):
				if outData['tableData'][powerOrVolt][1][i]!='-':
					outData['tableData'][powerOrVolt][1][i]=float(outData['tableData'][powerOrVolt][1][i])
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
		# Remove ppid file or results won't render.
		try:
			os.remove(pJoin(modelDir, "PPID.txt"))
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
		try:
			os.remove(pJoin(modelDir, "PPID.txt"))
		except:
			pass

def genDiagram(modelDir, feederJson):
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
								if x not in toRemove: 
									toRemove.append(x)
	for rem in toRemove: 
		tree.pop(rem)
	nxG = feeder.treeToNxGraph(tree)
	feeder.latLonNxGraph(nxG) # This function creates a .plt reference which can be saved here.
	plt.savefig(pJoin(modelDir,"feederChart.png"))
	if debug:
		print "Plot saved to:                 %s"%(pJoin(modelDir,"feederChart.png"))
		print "************************************\n\n"

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"modelName": "Automated Testing of " + modelName,
		"networkName": "case9",
		"algorithm": "NR",
		"model": "AC",
		"tolerance": math.pow(10,-8),
		"iteration": 10,
		"genLimits": 0}
	creationCode = __metaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copy(pJoin(__metaModel__._omfDir,"static","SimpleNetwork.json"),pJoin(modelDir,"case9.omt"))
	except:
		return False
	return creationCode

def _simpleTest():
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
	renderAndShow(template, modelName)
	# Run the model.
	runForeground(modelLoc, inputDict=json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(template, modelName, modelDir=modelLoc)

if __name__ == '__main__':
	_simpleTest	()
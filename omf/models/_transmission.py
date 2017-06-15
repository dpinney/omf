''' The transmission model pre-alpha release.
Requirements: GNU octave
Tested on Linux and macOS.
'''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, math
import multiprocessing, platform
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *
import pprint as pprint
import matplotlib
import matplotlib.cm as cm
from matplotlib import pyplot as plt

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

def run(modelDir, inputDict):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
	except Exception, e:
		pass
	try:
		os.remove(pJoin(modelDir,inputDict.get("networkName1","default")+".m"))
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
		# Read feeder and convert to .mat.
		networkName = inputDict.get('networkName1','case9')
		networkJson = json.load(open(pJoin(modelDir,networkName+".omt")))
		matStr = network.netToMat(networkJson, networkName)
		with open(pJoin(modelDir,networkName+".m"),"w") as outMat:
			for row in matStr: outMat.write(row)		
		# Build the MATPOWER command.
		matDir =  pJoin(__metaModel__._omfDir,'solvers','matpower5.1')
		if platform.system() == "Windows":
			pathSep = ";"
		else:
			pathSep = ":"
		matPath = '"' + pathSep.join([matDir,pJoin(matDir,'t'),pJoin(matDir,'extras')]) + '"'
		algorithm = inputDict.get("algorithm","NR")
		pfArg = "'pf.alg', '" + algorithm + "'"
		modelArg = "'model', '" + inputDict.get("model","AC") + "'"
		iterCode = "pf." + algorithm[:2].lower() + ".max_it"
		pfItArg = "'" + iterCode + "', " + str(inputDict.get("iteration",10))
		pfTolArg = "'pf.tol', " + str(inputDict.get("tolerance",math.pow(10,-8)))
		pfEnflArg = "'pf.enforce_q_lims', " + str(inputDict.get("genLimits",0))
		if platform.system() == "Windows":
			# Find the location of octave-cli tool.
			envVars = os.environ["PATH"].split(';')
			octavePath = "C:\\Octave\\Octave-4.2.0"
			for pathVar in envVars:
				if "octave" in pathVar.lower():
					octavePath = pathVar
			# Run Windows-specific Octave command.
			mpoptArg = "mpoption(" + pfArg + ", " + modelArg + ", " + pfItArg + ", " + pfTolArg+", " + pfEnflArg + ") "
			cmd = "runpf('"+pJoin(modelDir,networkName+'.m')+"'," + mpoptArg +")"
			args = [octavePath + '\\bin\\octave-cli','-p',matPath, "--eval",  cmd]
			myOut = subprocess.check_output(args, shell=True)
			with open(pJoin(modelDir, "matout.txt"), "w") as matOut:
				matOut.write(myOut)
		else:
			# Run UNIX Octave command.
			mpoptArg = "mpopt = mpoption("+pfArg+", "+modelArg+", "+pfItArg+", "+pfTolArg+", "+pfEnflArg+"); "
			command = "octave -p " + matPath + "--no-gui --eval \""+mpoptArg+"runpf('"+pJoin(modelDir,networkName+'.m')+"', mpopt)\" > \"" + pJoin(modelDir,"matout.txt") + "\""
			proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
			(out, err) = proc.communicate()
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

		#Create chart
		with open(pJoin(modelDir,'case9.omt')) as inputFile:    
				case9 = json.load(inputFile)
		nodeVolts = outData["tableData"]["volts"][1]
		
		minNum = min(nodeVolts)
		maxNum = max(nodeVolts)
		norm = matplotlib.colors.Normalize(vmin=minNum, vmax=maxNum, clip=True)
		cmViridis = plt.get_cmap('viridis')
		mapper = cm.ScalarMappable(norm=norm, cmap=cmViridis)
		mapper._A = []
		plt.figure(figsize=(10,10))
		plt.colorbar(mapper)
		plt.axis('off')
		plt.tight_layout()
		plt.gca().invert_yaxis() # To make latitudes show up right.
		plt.gca().set_aspect('equal')
		busLocations = {}
		i = 0
		for bus in case9["bus"]:
			for busName, busInfo in bus.items():
				y = float(busInfo["latitude"])
				x = float(busInfo["longitude"])
				plt.plot([x], [y], marker='o', markersize=12.0, color=mapper.to_rgba(nodeVolts[i]), zorder=5)  
				busLocations[busName] = [x, y]
			i = i + 1
		for gen in case9["gen"]:
			for genName, genInfo in gen.items():
				x,y =  busLocations[genInfo["bus"]]
				plt.plot([x], [y], 's', color='gray', zorder=10)
		for branch in case9["branch"]:
			for branchName, branchInfo in branch.items():
				x1, y1 = busLocations[branchInfo["fbus"]]
				x2, y2 = busLocations[branchInfo["tbus"]]
				plt.plot([x1, x2], [y1,y2], color='black', marker = '', zorder=0)
		plt.savefig(modelDir + '/output.png')
		with open(pJoin(modelDir,"output.png"),"rb") as inFile:
			outData["chart"] = inFile.read().encode("base64")
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

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"networkName1": "case9",
		"algorithm": "NR",
		"model": "AC",
		"tolerance": math.pow(10,-8),
		"iteration": 10,
		"genLimits": 0,
		"modelType":modelName}
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
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc, inputDict=json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_simpleTest ()
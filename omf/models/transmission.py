''' The transmission model pre-alpha release.
Requirements: GNU octave
Tested on Linux and macOS.
'''

import json, os, shutil, subprocess, math, platform, base64
from os.path import join as pJoin

import matplotlib
if platform.system() == 'Darwin':
	matplotlib.use('TkAgg')
else:
	matplotlib.use('Agg')
from matplotlib import pyplot as plt
import matplotlib.cm as cm

from omf import network
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "The transmission model imports, runs and visualizes MATPOWER transmission and generation simulations."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	outData = {
		'tableData' : {'volts': [[],[]], 'powerReal' : [[],[]], 'powerReact' : [[],[]]},
		# 'charts' : {'volts' : '', 'powerReact' : '', 'powerReal' : ''},
		'voltsChart' : '', 'powerReactChart' : '', 'powerRealChart' : '',
		'stdout' : '', 'stderr' : ''
		}
	# Read feeder and convert to .mat.
	try:
		networkName = [x for x in os.listdir(modelDir) if x.endswith('.omt')][0][0:-4]
	except:
		networkName = 'case9'
	with open(pJoin(modelDir,networkName+".omt")) as f:
		networkJson = json.load(f)
	matName = 'matIn'
	matFileName = matName + '.m'
	matStr = network.netToMat(networkJson, matName)
	with open(pJoin(modelDir, matFileName),"w") as outMat:
		for row in matStr: outMat.write(row)		
	# Build the MATPOWER command.
	matDir =  pJoin(__neoMetaModel__._omfDir,'solvers','matpower5.1')
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
		cmd = "runpf('"+pJoin(modelDir,matFileName)+"'," + mpoptArg +")"
		args = [octavePath + '\\bin\\octave-cli','-p',matPath, "--eval",  cmd]
		myOut = subprocess.check_output(args, shell=True)
		with open(pJoin(modelDir, "matout.txt"), "w") as matOut:
			matOut.write(myOut)
	else:
		# Run UNIX Octave command.
		mpoptArg = "mpopt = mpoption("+pfArg+", "+modelArg+", "+pfItArg+", "+pfTolArg+", "+pfEnflArg+"); "
		command = "octave -p " + matPath + "--no-gui --eval \""+mpoptArg+"runpf('"+pJoin(modelDir,matFileName)+"', mpopt)\" > \"" + pJoin(modelDir,"matout.txt") + "\""
		proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		print(command)
		(out, err) = proc.communicate()
	imgSrc = pJoin(__neoMetaModel__._omfDir,'scratch','transmission','inData')
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
			line = [a for a in line if a != '']
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
	plt.gca().invert_yaxis() # HACK: to make latitudes show up right. TODO: y-flip the transEdit.html and remove this.
	plt.gca().set_aspect('equal')
	busLocations = {}
	i = 0
	for busName, busInfo in networkJson["bus"].items():
		y = float(busInfo["latitude"])
		x = float(busInfo["longitude"])
		plt.plot([x], [y], marker='o', markersize=12.0, color=mapper.to_rgba(nodeVolts[i]), zorder=5)  
		busLocations[busName] = [x, y]
		i = i + 1
	for genName, genInfo in networkJson["gen"].items():
		x,y =  busLocations[genInfo["bus"]]
		plt.plot([x], [y], 's', color='gray', zorder=10, markersize=6.0)
	for branchName, branchInfo in networkJson["branch"].items():
		x1, y1 = busLocations[branchInfo["fbus"]]
		x2, y2 = busLocations[branchInfo["tbus"]]
		plt.plot([x1, x2], [y1,y2], color='black', marker = '', zorder=0)
	plt.savefig(modelDir + '/output.png')
	with open(pJoin(modelDir,"output.png"),"rb") as inFile:
		outData["chart"] = base64.standard_b64encode(inFile.read()).decode('ascii')
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"networkName1": "case9",
		"algorithm": "NR",
		"model": "AC",
		"tolerance": "0.00000001",
		"iteration": 10,
		"genLimits": 0,
		"modelType":modelName}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copy(pJoin(__neoMetaModel__._omfDir,"static","SimpleNetwork.json"),pJoin(modelDir,"case9.omt"))
	except:
		return False
	return creationCode

@neoMetaModel_test_setup
def _tests():
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
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()

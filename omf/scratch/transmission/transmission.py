''' The transmission model. '''

'''
Reqs:
	octave (sudo apt-get install octave)
	matpower6.0b1 source (copy in scratch\transmission\inData)
	*ONLY TESTED ON LINUX

TODO:
	XXX Add MATPOWER functionality.
	XXX Add functionality to specify solvers, model, tolerance, iteration, genlimits.
	XXX Parse results to outputDict.
	XXX Render to transmission.html. Fix bug thats only rendering first two table rows.
	XXX Update test case. Add other .m tests.
	OOO Add cancel functionality. Did so by removing cancel from transmission.py. metamodel has a cancel.
	OOO Create network editor.
	OOO Link network editor to model.
	OOO Create MATPOWER wrapper. Remove CD function.
	OOO Explore docker/non-vm functionality to speed up test process.
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
import feeder
from solvers import nrelsam2013
from weather import zipCodeToClimateName

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"transmission.html"),"r") as tempFile:
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
		allOutputData=allOutputData, modelStatus=getStatus(modelDir), pathPrefix=pathPrefix, datastoreNames=datastoreNames)

def run(modelDir, inputDict):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
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
	''' Run the model in its directory.
	'''
	try:
		startTime = datetime.datetime.now()
		outData = {
			'tableData' : {'volts': [[],[]], 'powerReal' : [[],[]], 'powerReact' : [[],[]]},
			}		
		# Model operations goes here.
		# Configure and run MATPOWER.
		matDir =  pJoin(__metaModel__._omfDir,'scratch','transmission','inData', 'matpower6.0b1')
		networkName = inputDict.get('networkName','case9')
		with cd(matDir):
			shutil.copyfile(pJoin(networkName+'.m'),pJoin(modelDir,'network.m'))
			print "Copied network from: %s to: %s"%(pJoin(matDir, networkName+'.m'),pJoin(modelDir,'.network.m'))
		algorithm = inputDict.get("algorithm","NR")
		pfArg = "\'pf.alg\', \'"+algorithm+"\'"
		modelArg = "\'model\', \'"+inputDict.get("model","AC")+"\'"
		iterCode = "pf."+algorithm[:2].lower()+".max_it"
		pfItArg = "\'"+iterCode+"\', "+str(inputDict.get("iteration",10))
		pfTolArg = "\'pf.tol\', "+str(inputDict.get("tolerance",math.pow(10,-8)))
		pfEnflArg = "\'pf.enforce_q_lims\', "+str(inputDict.get("genLimits",0))
		mpoptArg = "mpopt = mpoption("+pfArg+", "+modelArg+", "+pfItArg+", "+pfTolArg+", "+pfEnflArg+"); "
		with cd(matDir):
			# results = octave --no-gui ...
			command = "octave --no-gui --eval \""+mpoptArg+"runpf(\'"+pJoin(modelDir,'network.m')+"\', mpopt)\" > "+"/home/dev/Desktop/matout.txt" # Can't save in scratch due to windows file sharing.
			print "command:", command
			proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
			(out, err) = proc.communicate()
		shutil.copy("/home/dev/Desktop/matout.txt", pJoin(modelDir,'matout.txt'))
		os.remove("/home/dev/Desktop/matout.txt")
		# SKELETON code.
		imgSrc = pJoin(__metaModel__._omfDir,'scratch','transmission','inData')	
		# shutil.copyfile(pJoin(imgSrc,'bg1.jpg'),pJoin(modelDir,'powerReal.jpg'))
		# shutil.copyfile(pJoin(imgSrc,'bg2.jpg'),pJoin(modelDir,'powerReact.jpg'))
		# shutil.copyfile(pJoin(imgSrc,'bg3.jpg'),pJoin(modelDir,'volts.jpg'))
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
		pprint.pprint(outData)
		with open(pJoin(imgSrc,'bg1.jpg'),"rb") as inFile:
			outData["powerReal"] = inFile.read().encode("base64")
		with open(pJoin(imgSrc,'bg2.jpg'),"rb") as inFile:
			outData["powerReact"] = inFile.read().encode("base64")
		with open(pJoin(imgSrc,'bg3.jpg'),"rb") as inFile:
			outData["volts"] = inFile.read().encode("base64")		
		# Model operations typically ends here.
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

# directory switching for matpower binaries.
class cd:
	"""Context manager for changing the current working directory"""
	def __init__(self, newPath):
		self.newPath = os.path.expanduser(newPath)

	def __enter__(self):
		self.savedPath = os.getcwd()
		os.chdir(self.newPath)

	def __exit__(self, etype, value, traceback):
		os.chdir(self.savedPath)


def _tests():
	for networkName in ['case5', 'case9', 'case30', 'case57', 'case300']:
		# Variables
		inData = {"user" : "admin", "modelName" : "Automated Transmission Model Testing",
			# "networkName" : "9-Bus System",
			"networkName" : networkName, # case file name copied from matpower folder.
			"algorithm" : "NR",
			"model" : "AC",
			"tolerance" : math.pow(10,-8),
			"iteration" : 10,
			"genLimits" : 0}
		workDir = pJoin(__metaModel__._omfDir,"data","Model")
		modelDir = pJoin(workDir, inData["user"], inData["modelName"])
		# Blow away old test results if necessary.
		try:
			shutil.rmtree(modelDir)
		except:
			# No previous test results.
			pass
		try:
			os.makedirs(modelDir)
		except: pass
		 # Run the model & show the output.
		runForeground(modelDir, inData)
		renderAndShow(template, modelDir = modelDir)

if __name__ == '__main__':
	_tests()
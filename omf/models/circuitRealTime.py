''' Display circuit simulator in real time. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *
# OMF imports
sys.path.append(__metaModel__._omfDir)

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = 'Write tooltip for circuitRealTime'

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,modelName + ".html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames, modelName=modelName)


def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	print os.getcwd()
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))	
	except Exception, e:
		pass
	# Check whether model exist or not
	try:
		if not os.path.isdir(modelDir):
			os.makedirs(modelDir)
			inputDict["created"] = str(datetime.datetime.now())
		startTime = datetime.datetime.now()
		# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
		# Update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
		print "\n   inputDict[runTime]", inputDict["runTime"]
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
		# Stdout/stderr.
		outData = {}		
		outData["stdout"] = "Success"
		outData["stderr"] = ""
		# Write the output.
		with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
			json.dump(outData, outFile, indent=4)
	except:
		#if input range wasn't valid delete output and pass
		try:
			os.remove(pJoin(modelDir,"allOutputData.json"))
		except Exception, e:
			pass

def cancel(modelDir):
	''' PV Watts runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	inData = {"modelType": modelName,"circuitFile" : "zenerreffollow.txt"}
	modelLoc = pJoin(workDir,"admin","Automated realTimeCircuit Testing")
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow(template)
	# Run the model.
	run(modelLoc, inData)
	# Show the output.
	renderAndShow(template, modelDir = modelLoc)

if __name__ == '__main__':
	_tests()
''' A model skeleton for future models: Calculates the sum of two integers. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import nrelsam2013
from weather import zipCodeToClimateName

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"_modelSkeleton.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def quickRender(template, modelDir="", absolutePaths=False, datastoreNames={}):
	''' Presence of this function indicates we can run the model quickly via a public interface. '''
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames, quickRender=True)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
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
		# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
		with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
			json.dump(inputDict, inputFile, indent = 4)			
		startTime = datetime.datetime.now()
		outData = {}		
		# Model operations goes here.
		inputOne = inputDict.get("input1", 123)
		inputTwo = inputDict.get("input2", 867)
		output = inputOne + inputTwo
		outData["output"] = output
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
	inData = {"user" : "admin", "modelName" : "Automated Model Skeleton Testing",
		"input1" : "abc1 Easy as...",
		"input2" : "123 Or Simple as..."}
	modelDir = pJoin(workDir, inData["user"], inData["modelName"])
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelDir)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow(template)
	# Run the model.
	run(modelDir, inData)
	# Show the output.
	renderAndShow(template, modelDir = modelDir)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelDir)

if __name__ == '__main__':
	_tests()			
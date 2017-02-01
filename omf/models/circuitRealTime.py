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
tooltip = 'Real time circuit simulator'

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,modelName + ".html"),"r") as tempFile:
	template = Template(tempFile.read())

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
		startTime = datetime.datetime.now()
		# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
		# Update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
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

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"circString":"$ 1 0.000005 10.20027730826997 50 5 43\nr 176 64 384 64 0 10\ns 384 64 448 64 0 1 false\nw 176 64 176 336 0\nc 384 336 176 336 0 0.000014999999999999999 2.2688085065409958\nl 384 64 384 336 0 1 0.035738623044691664\nv 448 336 448 64 0 0 40 5 0 0 0.5\nr 384 336 448 336 0 100\no 4 64 0 2083 20 0.05 0 -1 0",
		"user":"admin"
	}
	return __metaModel__.new(modelDir, defaultInputs)

def _tests():
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
	renderAndShow(template, modelName, modelDir=modelLoc)

if __name__ == '__main__':
	_tests()
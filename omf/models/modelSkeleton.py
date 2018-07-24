''' A model skeleton for future models: Calculates the sum of two integers. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback
from os.path import join as pJoin
from jinja2 import Template
import __neoMetaModel__
from __neoMetaModel__ import *

# OMF imports
sys.path.append(__neoMetaModel__._omfDir)
import feeder
from solvers import nrelsam2013
from weather import zipCodeToClimateName

# Model metadata:
modelName, template = metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
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
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user" : "admin",
		"modelType": modelName,
		"input1": "abc1 Easy as...",
		"input2": "123 Or Simple as...",
		"created":str(datetime.datetime.now())
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated pvWatts Testing")
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
	runForeground(modelLoc, inputDict=json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
''' Description TBD '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "Generate timeseries powerflow scenarios from a distribution feeder."

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName+".html"),"r") as tempFile:
	template = Template(tempFile.read())

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	# Get feeder name.
	feederName = [x for x in os.listdir(modelDir) if x.endswith(".omd")][0][:-4]
	inputDict["feederName1"] = feederName
	# Get the feeder data and write to .glm.
	with open(pJoin(modelDir,feederName + ".omd"),"r") as inFile:
		feederData = json.load(inFile)
	with open(pJoin(modelDir,"scenarioSeed.glm"), "w") as outFile:
		outFile.write(omf.feeder.sortedWrite(feederData["tree"]))
	# TODO: actually run the scenario generator.
	# Make an output.
	outData["test"] = 1
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	# TODO: add inputs needed based on spec.
	defaultInputs = {
		"feederName1": "Olin Barre Geo",
		"modelType": modelName,
		"runTime": "",
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+".omd"), pJoin(modelDir, defaultInputs["feederName1"]+".omd"))
	except:
		return False
	return creationCode

def _debugging():
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
	_debugging()
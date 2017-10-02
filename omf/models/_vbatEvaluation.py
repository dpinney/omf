''' VBAT Evaluation
Requirements: GNU octave
'''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, math
import multiprocessing, platform
from os.path import join as pJoin
from jinja2 import Template
import __neoMetaModel__
from __neoMetaModel__ import *
import random

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "Calculate the virtual battery capacity for a collection of thermostically controlled loads."

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName + ".html"),"r") as tempFile:
	template = Template(tempFile.read())

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	outData = {}
	# Run VBAT code.
	vbatPath = os.path.join(omf.omfDir,'solvers','vbat')
	command = 'octave --no-gui --eval "addpath(genpath(\'FULLPATH\'));VB_test"'\
	 	.replace('FULLPATH', vbatPath)\
	 	.replace('ARGS', '98158,1,0')
	# VB_func(out_temp,device_type, device_parameters)
	myOut = subprocess.check_output(command, shell=True)
	# Format results to go in chart.
	outData["minPowerSeries"] = [random.uniform(0.0,10.0) for x in xrange(8760)]
	outData["maxPowerSeries"] = [random.uniform(15.0,40.0) for x in xrange(8760)]
	outData["minEnergySeries"] = [random.uniform(0.0,2.0) for x in xrange(8760)]
	outData["maxEnergySeries"] = [random.uniform(3.0,20.0) for x in xrange(8760)]
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"algorithm": "NR",
		"model": "AC",
		"tolerance": "0.00000001",
		"iteration": 10,
		"genLimits": 0,
		"modelType":modelName}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

def _simpleTest():
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
	_simpleTest ()
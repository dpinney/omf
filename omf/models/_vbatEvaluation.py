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
	plat = platform.system()
	if plat == "Windows":
		octBin = 'c:\\Octave\\Octave-4.2.1\\bin\\octave-cli'
	elif plat == "Darwin":
		octBin = 'octave --no-window-system'
	else:
		octBin = 'octave --no-window-system'
	command = 'OCTBIN --eval "addpath(genpath(\'FULLPATH\'));VB_func(ARGS)"'\
	 	.replace('FULLPATH', vbatPath)\
	 	.replace('OCTBIN',octBin)\
		.replace('ARGS', inputDict['zipcode'] + ',' + inputDict['load_type'] +',[' + inputDict['capacitance'] + ','+ inputDict['resistance'] + 
			',' + inputDict['power'] + ',' + inputDict['cop'] + ',' + inputDict['deadband'] + ',' + inputDict['setpoint'] + ',' +
			inputDict['number_devices'] + ']')
	myOut = subprocess.check_output(command, shell=True, cwd=vbatPath)
	P_lower = myOut.partition("P_lower =\n\n")[2]
	P_lower = P_lower.partition("\n\nn")[0]
	P_lower = map(float,P_lower.split('\n'))
	P_upper = myOut.partition("P_upper =\n\n")[2]
	P_upper = P_upper.partition("\n\nn")[0]
	P_upper = map(float,P_upper.split('\n'))
	E_UL = myOut.partition("E_UL =\n\n")[2]
	E_UL = E_UL.partition("\n\n")[0]
	E_UL = map(float,E_UL.split('\n'))
	# Format results to go in chart.
	outData["minPowerSeries"] = [-1*x for x in P_lower]
	outData["maxPowerSeries"] = P_upper
	outData["minEnergySeries"] = [-1*x for x in E_UL]
	outData["maxEnergySeries"] = E_UL
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"load_type": "1",
		"zipcode": "94128",
		"number_devices": "50",
		"power": "5.6",
		"capacitance": "2",
		"resistance": "2",
		"cop": "2.5",
		"setpoint": "22.5",
		"deadband": "0.625",
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
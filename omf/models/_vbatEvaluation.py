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
#trying something
import ctypes  # An included library with Python install.   

	
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
	if inputDict['load_type'] == '4':
		numDevices = int(inputDict['number_devices'])
		if numDevices == 1:
			runTimeDuration = 2
		elif numDevices > 1 and numDevices < 10:
			runTimeDuration = 3.5
		elif numDevices >= 10 and numDevices < 50:
			runTimeDuration = 6
		else :
			runTimeDuration = (numDevices-numDevices%50)*.2
		inputDict['runTimeEstimate'] = 'This configuration will take an approximate run time of: ' + str(runTimeDuration) +' minutes.'
		#HACK: dump input immediately to show runtime estimate.
	else:
		inputDict['runTimeEstimate'] = 'This configuration will take an approximate run time of: 0.5 minutes.'
	with open(pJoin(modelDir,'allInputData.json'), 'w') as dictFile:
		json.dump(inputDict, dictFile, indent=4)
	if plat == 'Windows':
		octBin = 'c:\\Octave\\Octave-4.2.1\\bin\\octave-cli'
	elif plat == 'Darwin':
		octBin = 'octave --no-gui'
	else:
		octBin = 'octave --no-window-system'
	command = 'OCTBIN --eval "addpath(genpath(\'FULLPATH\'));VB_func(ARGS)"'\
	 	.replace('FULLPATH', vbatPath)\
	 	.replace('OCTBIN',octBin)\
		.replace('ARGS', inputDict['zipcode'] + ',' + inputDict['load_type'] +',[' + inputDict['capacitance'] + ','+ inputDict['resistance'] + 
			',' + inputDict['power'] + ',' + inputDict['cop'] + ',' + inputDict['deadband'] + ',' + inputDict['setpoint'] + ',' +
			inputDict['number_devices'] + ']')
	try:
		if plat == 'Windows':
			myOut = subprocess.check_output(command, shell=True, cwd=vbatPath)
		else:
			proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
			with open(pJoin(modelDir, "PID.txt"),"w") as pidFile:
				pidFile.write(str(proc.pid))
			(myOut, err) = proc.communicate()
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
		#inputDict["stderr"] = ""
	except:
		outData["stdout"] = "Failure"
		inputDict["stderr"] = myOut
		#outData["stderr"] = myOut
		#with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
		#	errorFile.write(myOut)
		#with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
		#	json.dump(inputDict, inFile, indent=4)
		'''inJson = json.load(open(pJoin(modelDir,"allInputData.json")))
			inJson["stderr"] = myOut
			allInputData = json.dumps(inJson)'''
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"load_type": "1",
		"zipcode": "'default'",
		"number_devices": "100",
		"power": "5.6",
		"capacitance": "2",
		"resistance": "2",
		"cop": "2.5",
		"setpoint": "22.5",
		"deadband": "0.625",
		"modelType":modelName}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

#def defaultValuesAC():
#	power = "1000",
#	capacitance = "2",
#	resistance = "2",
#	cop = "2.5",
#	setpoint = "22.5",
#	deadband = "0.625",
#	return power,capacitance,resistance,cop,setpoint,deadband


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
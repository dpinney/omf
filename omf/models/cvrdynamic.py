''' Calculate CVR impacts using a targetted set of dynamic loadflows. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess
import math, re, csv
import multiprocessing
from copy import deepcopy
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import __util__ as util
from datetime import datetime, date, time

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(_myDir)
print _omfDir
sys.path.append(_omfDir)

# OMF imports
sys.path.append(_omfDir)
import feeder
import calibrate
from solvers import gridlabd


def runModel(modelDir,localTree):
	'''This reads a glm file, changes the method of powerflow and reruns'''
	print "Testing GridlabD solver."
	startTime = datetime.now()
	binaryName = "gridlabd"
	for key in localTree:
		if "solver_method" in localTree[key].keys():
			solvmeth = localTree[key]["solver_method"]
			print "success", solvmeth 
			if solvmeth == 'NR':
				localTree[key]["solver_method"] = 'FBS'
			else:
				localTree[key]["solver_method"] = 'NR'
	#find the regulator attached to substation
	for key in localTree:
		if localTree[key].get('bustype','').lower() == 'swing':
			swingIndex = key
			swingName = localTree[key].get('name')
		if localTree[key].get('object','') == 'recorder' and localTree[key].get('file','') == 'outPower.csv':
			localTree[key]['file'] = 'Zregulator.csv'
	# Attach recorders relevant to CVR.
	recorders = [
			{'object': 'collector',
			'file': 'ZlossesTransformer.csv',
			'group': 'class=transformer',
			'limit': '0',
			'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
			{'object': 'collector',
			'file': 'ZlossesUnderground.csv',
			'group': 'class=underground_line',
			'limit': '0',
			'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
			{'object': 'collector',
			'file': 'ZlossesOverhead.csv',
			'group': 'class=overhead_line',
			'limit': '0',
			'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
			# {'object': 'recorder',
			# 'file': 'Zregulator.csv',
			# 'limit': '0',
			# 'parent': localTree[regIndex]['name'],
			# 'property': 'tap_A,tap_B,tap_C,power_in.real,power_in.imag'},
			{'object': 'collector',
			'file': 'ZvoltageJiggle.csv',
			'group': 'class=triplex_meter',
			'limit': '0',
			'property': 'min(voltage_12.mag),mean(voltage_12.mag),max(voltage_12.mag),std(voltage_12.mag)'},
			{'object': 'recorder',
			'file': 'ZsubstationTop.csv',
			'limit': '0',
			'parent': localTree[swingIndex]['name'],
			'property': 'voltage_A,voltage_B,voltage_C'}]
	biggest = 1 + max([int(k) for k in localTree.keys()])
	for index, rec in enumerate(recorders):
		localTree[biggest + index] = rec
	max_key = max([int(key) for key in localTree.keys()])
	print max_key
	# #find the regulator names and combine to form a string for volt-var control object
	regKeys = []
	accum = ""
	for key in localTree:
		if localTree[key].get("object","") == "regulator":
			accum += localTree[key].get("name","ERROR") + ","
			regKeys.append(key)
	regstr = accum[:-1]
	print regKeys
	#create volt-var control object
	# localTree[max_key+1] = {'object' : 'volt_var_control',
	# 'name' : 'volt_var_control',
	# 'control_method' : 'ACTIVE',
	# 'capacitor_delay' : '30.0',
	# 'regulator_delay' : '30.0',
	# 'desired_pf' : '0.99',
	# 'd_max' : '0.6',
	# 'd_min' : '0.1',
	# 'substation_link' : 'substation_transformer',
	# 'regulator_list' : regstr } 
	#running powerflow analysis via gridalab
	feeder.adjustTime(localTree, float(8760),"hours","2011-01-01")	
	output = gridlabd.runInFilesystem(localTree,keepFiles=True,workDir=modelDir)
	os.remove(pJoin(modelDir,"PID.txt"))
	p = output['Zregulator.csv']['power_in.real']
	#q = output['Zregulator.csv']['power_in.imag']
	#for debug
	plt.plot(range(len(p)),p)
	plt.show()
	print "DONE RUNNING", modelDir

if __name__ == '__main__':
	'''a compare solver functions which takes model directory as an input and compares two powerflow methods'''
	'''this model will first calibrate the feeder using SCADA data, from feederCalibrate.py'''
	#nameToSubcode = {'Coloma':471135, 'Friendship':470382}
	#creating a work directory
	inData = { "modelName": "Automated DynamicCVR Testing",
		"modelType": "cvrDynamic",
		"user": "admin"}
	workDir = pJoin(_omfDir,"data","Model")
	modelDir = pJoin(workDir, inData["user"], inData["modelName"])
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
	#calibrate and run cvrdynamic	
	feeder_path = pJoin(_omfDir,"data", "Feeder", "public","ABEC Frank LO.json")
	scadaPath = pJoin(_omfDir,"uploads","colScada.tsv")
	calibrate.omfCalibrate(modelDir,feeder_path,scadaPath)
	localTree = json.load(open(pJoin(modelDir,"calibrated feeder.json")))
	runModel(modelDir,localTree)

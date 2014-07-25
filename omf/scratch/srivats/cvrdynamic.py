''' Calculate CVR impacts using a targetted set of dynamic loadflows. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess
import math, re, csv
import multiprocessing
from copy import deepcopy
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
from datetime import datetime, date, time

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.getcwd())
_omfDir = os.path.dirname(_myDir)
print _omfDir
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
			print "current solver method", localTree[key]["solver_method"] 
			localTree[key]["solver_method"] = 'FBS'
	#find the swing bus and recorder attached to substation
	for key in localTree:
		if localTree[key].get('bustype','').lower() == 'swing':
			swingIndex = key
			swingName = localTree[key].get('name')
		if localTree[key].get('object','') == 'regulator' and localTree[key].get('from','') == swingName:
			regIndex = key
			regConfName = localTree[key]['configuration']
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
			{'object': 'recorder',
			'file': 'Zregulator.csv',
			'limit': '0',
			'parent': localTree[regIndex]['name'],
			'property': 'tap_A,tap_B,tap_C,power_in.real,power_in.imag'},
			{'object': 'collector',
			'file': 'ZvoltageJiggle.csv',
			'group': 'class=triplex_meter',
			'limit': '0',
			'property': 'min(voltage_12.mag),mean(voltage_12.mag),max(voltage_12.mag),std(voltage_12.mag)'},
			{'object': 'recorder',
			'file': 'ZsubstationTop.csv',
			'limit': '0',
			'parent': localTree[swingIndex]['name'],
			'property': 'voltage_A,voltage_B,voltage_C'},
			{'object': 'recorder',
			'file': 'ZsubstationBottom.csv',
			'limit': '0',
			'parent': localTree[regIndex]['to'],
			'property': 'voltage_A,voltage_B,voltage_C'}]
	biggest = 1 + max([int(k) for k in localTree.keys()])
	for index, rec in enumerate(recorders):
		localTree[biggest + index] = rec
	#run a reference load flow
	HOURS = float(100)
	feeder.adjustTime(localTree,HOURS,"hours","2011-01-01")	
	output = gridlabd.runInFilesystem(localTree,keepFiles=False,workDir=modelDir)
	os.remove(pJoin(modelDir,"PID.txt"))
	p = output['Zregulator.csv']['power_in.real']
	q = output['Zregulator.csv']['power_in.imag']
	#find the regulator and capacitor names and combine to form a string for volt-var control object
	regKeys = []
	accum_reg = ""
	for key in localTree:
		if localTree[key].get("object","") == "regulator":
			accum_reg += localTree[key].get("name","ERROR") + ","
			regKeys.append(key)
	regstr = accum_reg[:-1]
	print regKeys
	capKeys = []
	accum_cap = ""
	for key in localTree:
		if localTree[key].get("object","") == "capacitor":
			accum_cap += localTree[key].get("name","ERROR") + ","
			capKeys.append(key)
	capstr = accum_cap[:-1]
	print capKeys
	#time delays from configuration files
	time_delay_reg = '30.0'  
	time_delay_cap = '300.0'
	for key in localTree:
		if localTree[key].get('object','') == "regulator_configuration":
			time_delay_reg = localTree[key]['time_delay']
			print "time_delay_reg",time_delay_reg
		if localTree[key].get('object','') == "capacitor":
			time_delay_cap = localTree[key]['time_delay']
			print "time_delay_cap",time_delay_cap
	#create volt-var control object
	max_key = max([int(key) for key in localTree.keys()])
	print max_key
	localTree[max_key+1] = {'object' : 'volt_var_control',
	'name' : 'IVVC1',
	'control_method' : 'ACTIVE',
	'capacitor_delay' : str(time_delay_cap),
	'regulator_delay' : str(time_delay_reg),
	'desired_pf' : '0.99',
	'd_max' : '0.6',
	'd_min' : '0.1',
	'substation_link' : str(localTree[regIndex]['name']),
	'regulator_list' : regstr,
	'capacitor_list': capstr} 
	#running powerflow analysis via gridalab after attaching a regulator
	feeder.adjustTime(localTree,HOURS,"hours","2011-01-01")	
	output1 = gridlabd.runInFilesystem(localTree,keepFiles=True,workDir=modelDir)
	os.remove(pJoin(modelDir,"PID.txt"))
	pnew = output1['Zregulator.csv']['power_in.real']
	qnew = output1['Zregulator.csv']['power_in.imag']
	#total real and imaginary losses as a function of time
	realLoss = []
	imagLoss = []
	realLossnew = []
	imagLossnew = []
	subvolt = []
	lowVoltage = []
	highVoltage = []
	lowVoltagenew = []
	for element in range(int(HOURS)):
		r = 0.0
		i = 0.0
		rnew = 0.0
		inew = 0.0
		for device in ['ZlossesOverhead.csv','ZlossesTransformer.csv','ZlossesUnderground.csv']:
			for letter in ['A','B','C']:
				r += output[device]['sum(power_losses_' + letter + '.real)'][element]
				i += output[device]['sum(power_losses_' + letter + '.imag)'][element]
				rnew += output1[device]['sum(power_losses_' + letter + '.real)'][element]
				inew += output1[device]['sum(power_losses_' + letter + '.imag)'][element]
		realLoss.append(r)
		imagLoss.append(i)
		realLossnew.append(rnew)
		imagLossnew.append(inew)
		lowVoltage.append(float(output['ZvoltageJiggle.csv']['min(voltage_12.mag)'][element])/2.0)
		highVoltage.append(float(output['ZvoltageJiggle.csv']['max(voltage_12.mag)'][element])/2.0)
		lowVoltagenew.append(float(output1['ZvoltageJiggle.csv']['min(voltage_12.mag)'][element])/2.0)
	#tap positions
	tap = {'A':[],'B':[],'C':[]}
	tapnew = {'A':[],'B':[],'C':[]}
	for element in range(int(HOURS)):
		for letter in ['A','B','C']:
			tap[letter].append(output['Zregulator.csv']['tap_' + letter][element])
			tapnew[letter].append(output1['Zregulator.csv']['tap_' + letter][element])	
	#for debug
	plt.clf()
	plt.plot(p,label="substation real power without regulation")
	plt.plot(pnew,label="substation real power with regulation")
	plt.legend(loc=1)
	plt.figure("imaginary power")
	plt.plot(q,label="substation imag. power without regulation")
	plt.plot(qnew,label="substation imag. power with regulation")
	plt.legend(loc=1)
	plt.figure("real losses")
	plt.plot(realLoss,label="total losses real without regulation")
	plt.plot(realLossnew,label="total losses real with regulation")
	plt.legend(loc=1)
	plt.figure("imaginary losses")
	plt.plot(imagLoss,label="total losses imag. without regulation")
	plt.plot(imagLossnew,label="total losses imag. with regulation")
	plt.legend(loc=1)
	plt.figure("lowVoltage voltage as a function of time")
	plt.plot(lowVoltage,label="EOL voltage without regulation as a function of time")
	plt.plot(lowVoltagenew, label="EOL voltage with regulation as a function of time")
	plt.legend(loc=1)
	plt.show()
	plt.figure("TAP positions as a function of time")
	plt.plot(tap['C'],label="TAP C without regulation as a function of time")
	plt.plot(tapnew['C'], label="TAP C with regulation as a function of time")
	plt.legend(loc=3)
	plt.show()
	print "DONE RUNNING", modelDir

if __name__ == '__main__':
	'''a compare solver functions which takes model directory as an input and compares two powerflow methods'''
	'''this model will first calibrate the feeder using SCADA data, from feederCalibrate.py'''
	#creating a work directory
	inData = { "modelName": "Automated DynamicCVR Testing",
		"modelType": "cvrDynamic",
		"user": "admin"}
	workDir = pJoin(_omfDir,"data","Model")
	modelDir = pJoin(workDir, inData["user"], inData["modelName"])
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
	#calibrate and run cvrdynamic	
	feederPath = pJoin(_omfDir,"data", "Feeder", "public","ABEC Frank LO.json")
	scadaPath = pJoin(_omfDir,"uploads","FrankScada.tsv")
	calibrate.omfCalibrate(modelDir,feederPath,scadaPath)
	try:
		os.remove(pJoin(modelDir,"stderr.txt"))
		os.remove(pJoin(modelDir,"stdout.txt"))
	except:
		pass
	with open(pJoin(modelDir,"calibratedFeeder.json"), "r") as jsonIn:
		feederJson = json.load(jsonIn)
		localTree = feederJson.get("tree", {})
	runModel(modelDir,localTree)

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

def realPart(complexStr):
	''' real Part of a complex number.
	handles string if the string starts with a '+' or a '-'
	handles negative or positive, real and imaginary parts 
	example realPart(-20.5-6j) = -20.5'''
	if complexStr[0] == '+' or complexStr[0] == '-':
		complexStr1 = complexStr[1:len(complexStr)+1]
		sign = complexStr[0] + '1' 
	else:
		complexStr1 = complexStr
		sign = 1
	if complexStr1.find('+')>0:
		return float(complexStr1[0:complexStr1.find('+')])*float(sign)
	else:
		if complexStr1.find('-')>0:
			return float(complexStr1[0:complexStr1.find('-')])*float(sign)
		else:
			return float(complexStr1)*float(sign)

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
	#recorder object for capacitor switching - if capacitors exist
	if capKeys != []:
		for key in capKeys:
			recorders.append({'object': 'recorder',
			'file': 'ZcapSwitch' + str(key) + '.csv',
			'limit': '0',
			'parent': localTree[key]['name'],
			'property': 'switchA,switchB,switchC'})
	#attach recorder process
	biggest = 1 + max([int(k) for k in localTree.keys()])
	for index, rec in enumerate(recorders):
		localTree[biggest + index] = rec
	#run a reference load flow
	HOURS = float(500)
	feeder.adjustTime(localTree,HOURS,"hours","2011-01-01")	
	output = gridlabd.runInFilesystem(localTree,keepFiles=False,workDir=modelDir)
	os.remove(pJoin(modelDir,"PID.txt"))
	p = output['Zregulator.csv']['power_in.real']
	q = output['Zregulator.csv']['power_in.imag']
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
	#voltage calculations and tap calculations
	lowVoltage = []
	highVoltage = []
	lowVoltagenew = []
	tap = {'A':[],'B':[],'C':[]}
	tapnew = {'A':[],'B':[],'C':[]}
	volt = {'A':[],'B':[],'C':[]}
	voltnew = {'A':[],'B':[],'C':[]}
	switch = {'A':[],'B':[],'C':[]}
	switchnew = {'A':[],'B':[],'C':[]}
	for element in range(int(HOURS)):
		for letter in ['A','B','C']:
			tap[letter].append(output['Zregulator.csv']['tap_' + letter][element])
			tapnew[letter].append(output1['Zregulator.csv']['tap_' + letter][element])
			volt[letter].append(realPart(output['ZsubstationBottom.csv']['voltage_'+letter][element])/60)
			voltnew[letter].append(realPart(output1['ZsubstationBottom.csv']['voltage_'+letter][element])/60)
			switch[letter].append(output['ZcapSwitch' + str(int(capKeys[0])) + '.csv']['switch'+ letter][element])
			switchnew[letter].append(output1['ZcapSwitch' + str(int(capKeys[0])) + '.csv']['switch'+ letter][element])
		lowVoltage.append(float(output['ZvoltageJiggle.csv']['min(voltage_12.mag)'][element])/2.0)
		highVoltage.append(float(output['ZvoltageJiggle.csv']['max(voltage_12.mag)'][element])/2.0)
		lowVoltagenew.append(float(output1['ZvoltageJiggle.csv']['min(voltage_12.mag)'][element])/2.0)
	#for debug
	plt.clf()
	plt.plot(p,label="substation real power without IVVC")
	plt.plot(pnew,label="substation real power with IVVC")
	plt.legend(loc=1)
	plt.savefig(pJoin(modelDir,"real power.png"))
	plt.figure("imaginary power")
	plt.plot(q,label="substation imag. power without IVVC")
	plt.plot(qnew,label="substation imag. power with IVVC")
	plt.legend(loc=1)
	plt.savefig(pJoin(modelDir,"imaginary power.png"))
	plt.figure("real losses")
	plt.plot(realLoss,label="total losses real without IVVC")
	plt.plot(realLossnew,label="total losses real with IVVC")
	plt.legend(loc=1)
	plt.savefig(pJoin(modelDir,"real losses.png"))
	plt.figure("imaginary losses")
	plt.plot(imagLoss,label="total losses imag. without IVVC")
	plt.plot(imagLossnew,label="total losses imag. with IVVC")
	plt.legend(loc=1)
	plt.savefig(pJoin(modelDir,"imaginary losses.png"))
	plt.figure("lowVoltage voltage as a function of time")
	plt.plot(lowVoltage,label="EOL voltage without IVVC as a function of time")
	plt.plot(lowVoltagenew,label="EOL voltage with IVVC as a function of time")
	plt.legend(loc=1)
	plt.axis([0,HOURS,50.0,250.0])
	plt.savefig(pJoin(modelDir,"EOL voltage.png"))
	plt.figure("TAP positions as a function of time")
	plt.plot(tap['A'],label="TAP A without IVVC as a function of time")
	plt.plot(tapnew['A'], label="TAP A with IVVC as a function of time")
	plt.legend(loc=1)
	plt.axis([0,HOURS,-20.0,20.0])
	plt.savefig(pJoin(modelDir,"TAP A positions.png"))
	plt.figure("substation voltage as a function of time")
	plt.plot(volt['A'],label="sub. volt. A without IVVC as a function of time")
	plt.plot(voltnew['A'],label="sub. volt. A with IVVC as a function of time")
	plt.legend(loc=1)
	plt.axis([0,HOURS,50.0,250.0])
	plt.savefig(pJoin(modelDir,"substation volatage A.png"))
	plt.figure("capacitor switch state as a function of time")
	plt.plot(switch['A'],label="cap. switch A without IVVC as a function of time")
	plt.plot(switchnew['A'],label="cap. switch A with IVVC as a function of time")
	plt.legend(loc=1)
	plt.axis([0,HOURS,-2.0,2.0])
	plt.savefig(pJoin(modelDir,"capacitor switch A.png"))
	#plt.show()
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

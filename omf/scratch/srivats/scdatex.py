''' Extract SCADA data for feederCalibrate '''
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

scadadata = "ACECSCADA2.tsv"

def getTimeFormat(timestamp):
	'''This returns formatdate'''
	return datetime.strptime(str(timestamp),"%m/%d/%y %H:%M")

def getdatetime(timestamp):
	'''This function converts a timestamp to required date and time format in feederCalibrate.py'''
	date = ""
	time = ""
	
	formatdate = getTimeFormat(timestamp)
	date = formatdate.strftime('%Y-%m-%d')
	time = formatdate.strftime('%H')

	return date, float(time)


with open(pJoin(_omfDir,"scratch","old","staticCvrEvaluation","sourceData", scadadata),"r") as scadaFile:
	scadapython = csv.DictReader(scadaFile, delimiter='\t')
	allData = [row for row in scadapython if row['meterId']==str(471135)]

powerdata = []
timedata = []
pfdata = []	
for eachdict in allData:
	powerdata.append(float(eachdict['power']))
	timedata.append(str(eachdict['timestamp']))
	pfdata.append(float(eachdict['powerFactor']))

powerValue = 0.0

with open(pJoin(_omfDir,"uploads","colScada1.tsv"),"w") as writescada:
	writescada.write("meterid" + "	timestamp" + "	power"+ "	pf"+'\n')
	for stamp in timedata:
		powerValue = powerdata[timedata.index(stamp)]
		pfvalue = pfdata[timedata.index(stamp)]
		if powerValue == 0.0:
			powerValue = powerdata[timedata.index(stamp)-24]
			pfvalue = pfdata[timedata.index(stamp)-24]
		writescada.write("471135"+"	"+str(getTimeFormat(stamp).strftime('%m/%d/%Y %H:%M:%S'))+"	"+str(powerValue)+"	"+str(pfvalue)+'\n')		





# def comparesol(modelDir,localTree):
# 	'''This reads a glm file, changes the method of powerflow and reruns'''
# 	print "Testing GridlabD solver."

# 	startTime = datetime.now()

# 	binaryName = "gridlabd"

# 	for key in localTree:
# 		if "solver_method" in localTree[key].keys():
# 			solvmeth = localTree[key]["solver_method"]
# 			print "success", solvmeth 
# 			if solvmeth == 'NR':
# 				localTree[key]["solver_method"] = 'FBS'
# 			else:
# 				localTree[key]["solver_method"] = 'NR'

# 	# feeder.attachRecorders(localTree, "Regulator", "object", "regulator")
# 	# feeder.attachRecorders(localTree, "CollectorVoltage", None, None)	

# 	# last_key = len(localTree)

# 	# print last_key


# 	for key in localTree:
# 		if localTree[key].get('bustype','').lower() == 'swing':
# 			swingIndex = key
# 			swingName = localTree[key].get('name')

# 	print swingIndex, swingName

# 	for key in localTree:
# 		if localTree[key].get('object','') == 'regulator' and localTree[key].get('from','') == "COLOMA SUB":
# 			regIndex = key
# 			regConfName = localTree[key]['configuration']

# 	print regIndex


# 	# Attach recorders relevant to CVR.
# 	recorders = [
# 			{'object': 'collector',
# 			'file': 'ZlossesTransformer.csv',
# 			'group': 'class=transformer',
# 			'limit': '0',
# 			'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
# 			{'object': 'collector',
# 			'file': 'ZlossesUnderground.csv',
# 			'group': 'class=underground_line',
# 			'limit': '0',
# 			'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
# 			{'object': 'collector',
# 			'file': 'ZlossesOverhead.csv',
# 			'group': 'class=overhead_line',
# 			'limit': '0',
# 			'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'},
# 			{'object': 'recorder',
# 			'file': 'Zregulator.csv',
# 			'limit': '0',
# 			'parent': localTree[regIndex]['name'],
# 			'property': 'tap_A,tap_B,tap_C,power_in.real,power_in.imag'},
# 			{'object': 'collector',
# 			'file': 'ZvoltageJiggle.csv',
# 			'group': 'class=triplex_meter',
# 			'limit': '0',
# 			'property': 'min(voltage_12.mag),mean(voltage_12.mag),max(voltage_12.mag),std(voltage_12.mag)'},
# 			{'object': 'recorder',
# 			'file': 'ZsubstationTop.csv',
# 			'limit': '0',
# 			'parent': localTree[swingIndex]['name'],
# 			'property': 'voltage_A,voltage_B,voltage_C'},
# 			{'object': 'recorder',
# 			'file': 'ZsubstationBottom.csv',
# 			'limit': '0',
# 			'parent': localTree[regIndex]['to'],
# 			'property': 'voltage_A,voltage_B,voltage_C'} ]
	
# 	biggest = 1 + max([int(k) for k in localTree.keys()])
# 	for index, rec in enumerate(recorders):
# 		localTree[biggest + index] = rec


# 	max_key = max([int(key) for key in localTree.keys()])
# 	print max_key

# 	regKeys = []
# 	accum = ""

# 	for key in localTree:
# 		if localTree[key].get("object","") == "regulator":
# 			accum += localTree[key].get("name","ERROR") + ","
# 			regKeys.append(key)

# 	regstr = accum[:-1]

# 	print regKeys
# 	print regstr, type(regstr)

# 	# localTree[max_key+1] = {'object' : 'volt_var_control',
# 	# 'name' : 'volt_var_control',
# 	# 'control_method' : 'ACTIVE',
# 	# 'capacitor_delay' : '30.0',
# 	# 'regulator_delay' : '30.0',
# 	# 'desired_pf' : '0.99',
# 	# 'd_max' : '0.6',
# 	# 'd_min' : '0.1',
# 	# 'substation_link' : 'substation_transformer',
# 	# 'regulator_list' : regstr } 


# 	feeder.adjustTime(tree=localTree, simLength=float("100"),
# 			simLengthUnits="hours", simStartDate="2012-01-01")	

# 	output = gridlabd.runInFilesystem(localTree,keepFiles=True,workDir=modelDir)
# 	os.remove(pJoin(modelDir,"PID.txt"))
	

# 	p = output['Zregulator.csv']['power_in.real']
# 	q = output['Zregulator.csv']['power_in.imag']

# 	xtime = {}

# 	for key in output:
# 		if '# timestamp' in output[key]:
# 			xtime['timeStamps'] = output[key]['# timestamp']

# 	print type(xtime['timeStamps'][0])
# 	print len(p)

# 	xaxtick = str(xtime['timeStamps'])

# 	plt.plot(range(100),p)
# 	plt.show()

# 	print "p=" , p
# 	print "q=" , q
# 	print "DONE RUNNING", modelDir

# if __name__ == '__main__':
# 	'''a compare solver functions which takes model directory as an input and compares two powerflow methods'''
# 	'''this model will first calibrate the feeder using SCADA data, from feederCalibrate.py'''

# 	nameToSubcode = {'Coloma':471135, 'Friendship':470382}

# 	inData = { "modelName": "Automated DynamicCVR Testing",
# 		"modelType": "cvrDynamic",
# 		"user": "admin"}

# 	workDir = pJoin(_omfDir,"data","Model")
	
# 	modelDir = pJoin(workDir, inData["user"], inData["modelName"])

# 	if not os.path.isdir(modelDir):
# 		os.makedirs(modelDir)

# 	with open(pJoin(_omfDir,"data","Feeder","public","ABEC_Coloma_cal.json"),"r") as feederFile:
# 		feederJson = json.load(feederFile)

# 	localTree = deepcopy(feederJson)

# 	comparesol(modelDir,localTree)

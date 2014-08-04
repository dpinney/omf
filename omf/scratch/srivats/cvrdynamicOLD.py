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
import feederCalibrate
from solvers import gridlabd

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


def createLoadShape(modelDir,powerdata,timedata):
	'''This creates a loadshape player file'''

	powerValue = 0.0

	with open(pJoin(modelDir,"loadShapeScalar.player"),"w") as loadpPlayer:
		for stamp in timedata:
			powerValue = powerdata[timedata.index(stamp)]/float(max(powerdata))
			if powerValue == 0.0:
				powerValue = powerdata[timedata.index(stamp)-24]/float(max(powerdata))
			loadpPlayer.write(str(getTimeFormat(stamp).strftime('%Y-%m-%d %H:%M:%S'))+ " EST," + str(powerValue) + '\n')		

	return "loadShapeScalar.player"

def getScadaData(modelDir,scadadata,meterid):
	'''This extracts the scada data for a particular substation from ACEC SCADA file'''
	'''sample data required:
	'summerDay' : '2012-06-29'
	'winterDay' : '2012-01-19',
	'shoulderDay' : '2012-04-10',
	'summerPeakKW' : 5931.56,
	'summerTotalEnergy' : 107380.8,
	'summerPeakHour' : 17,
	'summerMinimumKW' : 2988,
	'summerMinimumHour' : 6,
	'winterPeakKW' : 3646.08,
	'winterTotalEnergy' : 75604.32,
	'winterPeakHour' : 21,
	'winterMinimumKW' : 2469.60,
	'winterMinimumHour' : 1,
	'shoulderPeakKW' : 2518.56 ,
	'shoulderTotalEnergy' : 52316.64,
	'shoulderPeakHour' : 21,
	'shoulderMinimumKW' : 1738.08,
	'shoulderMinimumHour' : 2'''

	with open(pJoin(_omfDir,"scratch","old","staticCvrEvaluation","sourceData", scadadata),"r") as scadaFile:
		scadapython = csv.DictReader(scadaFile, delimiter='\t')
		allData = [row for row in scadapython if row['meterId']==str(meterid)]

	powerdata = []
	timedata = []
	for eachdict in allData:
		powerdata.append(float(eachdict['power']))
		timedata.append(str(eachdict['timestamp']))



	#create a loadshape player file from SCADA data
	powerdata11 = powerdata[timedata.index('1/1/11 01:00'):timedata.index('12/31/11 23:00')+1] 
	timedata11 = timedata[timedata.index('1/1/11 01:00'):timedata.index('12/31/11 23:00')+1]

	for value in powerdata11:
		if value < 20.0:
			powerdata11[powerdata11.index(value)] = powerdata11[powerdata11.index(value)-24]

	with open(pJoin(modelDir,"powerdata.json"),"w") as outFile:
		json.dump(powerdata11, outFile, indent=4)

	filename = createLoadShape(modelDir,powerdata11,timedata11)


	#process summer data
	#create a dictionary of the required summer data

	summer = {'begindatetime': '6/1/11 00:00',
	'enddatetime': '8/31/11 23:00'}
    

    #subarray containing data specific to summer season
	summerpower = powerdata[timedata.index(summer['begindatetime']):timedata.index(summer['enddatetime'])+1]  
	summertime = timedata[timedata.index(summer['begindatetime']):timedata.index(summer['enddatetime'])+1]


	#max, min and indices
	summer['summerPeakKW'] = float(max(summerpower))     
	maxpowerind = summerpower.index(max(summerpower))
	maxtime = summertime[maxpowerind]
	ordate = maxtime[0:maxtime.index(" ")]

	summer['summerDay'], summer['summerPeakHour'] = getdatetime(maxtime)

	peakday = []
	peakdaykw = []

	for day in summertime:
		if day.startswith(ordate) == True:
			peakday.append(day)
			peakdaykw.append(summerpower[summertime.index(day)])


	summer['summerMinimumKW'] = float(min(peakdaykw))
	x, summer['summerMinimumHour'] = getdatetime(peakday[peakdaykw.index(min(peakdaykw))])

	#energy calculation
	energyTotal = 0

	yesdaykw = []
	yesday = summertime[maxpowerind-24]
	yesdate = yesday[0:yesday.index(" ")]
	

	for day in summertime:
		if day.startswith(yesdate) == True:
			yesdaykw.append(summerpower[summertime.index(day)])


	energyTotal = sum(peakdaykw) + sum(yesdaykw)

	summer['summerTotalEnergy'] = float(energyTotal)

	#print summer


	#process shoulder data
	#create a dictionary of the required shoulder data

	shoulder = {'begindatetime1': '3/1/11 00:00',
	'enddatetime1': '5/31/11 23:00',
	'begindatetime2':'9/1/11 00:00',
	'enddatetime2': '11/30/11 23:00'}

	#subarray containing data specific to shoulder season

	shoulderpower1 = powerdata[timedata.index(shoulder['begindatetime1']):timedata.index(shoulder['enddatetime1'])+1] 
	shoulderpower2 = powerdata[timedata.index(shoulder['begindatetime2']):timedata.index(shoulder['enddatetime2'])+1]
	shoulderpower = shoulderpower1 + shoulderpower2
	shouldertime1 = timedata[timedata.index(shoulder['begindatetime1']):timedata.index(shoulder['enddatetime1'])+1] 
	shouldertime2 = timedata[timedata.index(shoulder['begindatetime2']):timedata.index(shoulder['enddatetime2'])+1]
	shouldertime = shouldertime1 + shouldertime2

	#max, min and indices
	shoulder['shoulderPeakKW'] = float(max(shoulderpower))     
	maxpowerind1 = shoulderpower.index(max(shoulderpower))
	maxtime1 = shouldertime[maxpowerind1]

	ordate1 = maxtime1[0:maxtime1.index(" ")]

	shoulder['shoulderDay'], shoulder['shoulderPeakHour'] = getdatetime(maxtime1)

	peakday1 = []
	peakdaykw1 = []

	for day in shouldertime:
		if day.startswith(ordate1) == True:
			peakday1.append(day)
			peakdaykw1.append(shoulderpower[shouldertime.index(day)])


	shoulder['shoulderMinimumKW'] = float(min(peakdaykw1))
	x, shoulder['shoulderMinimumHour'] = getdatetime(peakday1[peakdaykw1.index(min(peakdaykw1))])


	#energy calculation
	energyTotal = 0

	yesdaykw1 = []
	yesday1 = shouldertime[maxpowerind1-24]
	yesdate1 = yesday1[0:yesday1.index(" ")]
	

	for day in shouldertime:
		if day.startswith(yesdate1) == True:
			yesdaykw1.append(shoulderpower[shouldertime.index(day)])


	energyTotal1 = sum(peakdaykw1) + sum(yesdaykw1)

	shoulder['shoulderTotalEnergy'] = float(energyTotal1)

	#print shoulder


	#process winter data
	#create a dictionary of the required winter data

	winter = {'begindatetime1': '1/1/11 01:00',
	'enddatetime1': '2/28/11 23:00',
	'begindatetime2':'12/1/11 00:00',
	'enddatetime2': '12/31/11 23:00'}

	#subarray containing data specific to winter season

	winterpower1 = powerdata[timedata.index(winter['begindatetime1']):timedata.index(winter['enddatetime1'])+1] 
	winterpower2 = powerdata[timedata.index(winter['begindatetime2']):timedata.index(winter['enddatetime2'])+1]
	winterpower = winterpower1 + winterpower2
	wintertime1 = timedata[timedata.index(winter['begindatetime1']):timedata.index(winter['enddatetime1'])+1] 
	wintertime2 = timedata[timedata.index(winter['begindatetime2']):timedata.index(winter['enddatetime2'])+1]
	wintertime = wintertime1 + wintertime2


	#max, min and indices
	winter['winterPeakKW'] = float(max(winterpower))     
	maxpowerind2 = winterpower.index(max(winterpower))
	maxtime2 = wintertime[maxpowerind2]


	ordate2 = maxtime2[0:maxtime2.index(" ")]

	winter['winterDay'], winter['winterPeakHour'] = getdatetime(maxtime2)

	peakday2 = []
	peakdaykw2 = []

	for day in wintertime:
		if day.startswith(ordate2) == True:
			peakday2.append(day)
			peakdaykw2.append(winterpower[wintertime.index(day)])


	winter['winterMinimumKW'] = float(min(peakdaykw2))
	x, winter['winterMinimumHour'] = getdatetime(peakday2[peakdaykw2.index(min(peakdaykw2))])

	#energy calculation
	energyTotal = 0

	yesdaykw2 = []
	yesday2 = wintertime[maxpowerind2-24]
	yesdate2 = yesday2[0:yesday2.index(" ")]
	

	for day in wintertime:
		if day.startswith(yesdate2) == True:
			yesdaykw2.append(winterpower[wintertime.index(day)])


	energyTotal2 = sum(peakdaykw2) + sum(yesdaykw2)

	winter['winterTotalEnergy'] = float(energyTotal2)

	#print winter


	return summer, shoulder, winter, filename 



def comparesol(modelDir,localTree):
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

	# feeder.attachRecorders(localTree, "Regulator", "object", "regulator")
	# feeder.attachRecorders(localTree, "CollectorVoltage", None, None)	

	# last_key = len(localTree)

	# print last_key



	for key in localTree:
		if localTree[key].get('bustype','').lower() == 'swing':
			swingIndex = key
			swingName = localTree[key].get('name')

	print swingIndex, swingName

	for key in localTree:
		if localTree[key].get('object','') == 'regulator' and localTree[key].get('from','') == swingName:
			regIndex = key
			regConfName = localTree[key]['configuration']

	print regIndex


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
			'property': 'voltage_A,voltage_B,voltage_C'} ]
	
	biggest = 1 + max([int(k) for k in localTree.keys()])
	for index, rec in enumerate(recorders):
		localTree[biggest + index] = rec


	max_key = max([int(key) for key in localTree.keys()])
	print max_key

	regKeys = []
	accum = ""

	for key in localTree:
		if localTree[key].get("object","") == "regulator":
			accum += localTree[key].get("name","ERROR") + ","
			regKeys.append(key)

	regstr = accum[:-1]

	print regKeys
	print regstr, type(regstr)

	localTree[max_key+1] = {'object' : 'volt_var_control',
	'name' : 'volt_var_control',
	'control_method' : 'ACTIVE',
	'capacitor_delay' : '30.0',
	'regulator_delay' : '30.0',
	'desired_pf' : '0.99',
	'd_max' : '0.6',
	'd_min' : '0.1',
	'substation_link' : 'substation_transformer',
	'regulator_list' : regstr } 


	feeder.adjustTime(tree=localTree, simLength=float("8760"),
			simLengthUnits="hours", simStartDate="2012-01-01")	

	output = gridlabd.runInFilesystem(localTree,keepFiles=True,workDir=modelDir)
	os.remove(pJoin(modelDir,"PID.txt"))
	

	p = output['Zregulator.csv']['power_in.real']
	q = output['Zregulator.csv']['power_in.imag']

	xtime = {}

	for key in output:
		if '# timestamp' in output[key]:
			xtime['timeStamps'] = output[key]['# timestamp']

	#print type(xtime['timeStamps'][0])
	#print len(p)

	#xaxtick = str(xtime['timeStamps'])

	# plt.plot(range(8760),p)
	# plt.show()

	# print "p=" , p
	# print "q=" , q
	print "DONE RUNNING", modelDir


if __name__ == '__main__':
	'''a compare solver functions which takes model directory as an input and compares two powerflow methods'''
	'''this model will first calibrate the feeder using SCADA data, from feederCalibrate.py'''

	nameToSubcode = {'Coloma':471135, 'Friendship':470382}

	inData = { "modelName": "Automated DynamicCVR Testing",
		"modelType": "cvrDynamic",
		"user": "admin"}

	workDir = pJoin(_omfDir,"data","Model")
	
	modelDir = pJoin(workDir, inData["user"], inData["modelName"])

	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)

	with open(pJoin(_omfDir,"data","Feeder","public","ABEC Columbia.json"),"r") as feederFile:
		feederJson = json.load(feederFile)

	localTree = deepcopy(feederJson["tree"])

	##scada data
	feedertype = 'Coloma'
	meterid = nameToSubcode[feedertype]
	scadadatafile = "ACECSCADA2.tsv"
	model_name = "calibrated_model_" + feedertype

	summer, shoulder, winter, filename = getScadaData(modelDir,scadadatafile,meterid)

	scada = {'summerDay' : summer['summerDay'],
		'winterDay' : winter['winterDay'],
		'shoulderDay' : shoulder['shoulderDay'],
		'summerPeakKW' : summer['summerPeakKW'],
		'summerTotalEnergy' : summer['summerTotalEnergy'],
		'summerPeakHour' : summer['summerPeakHour'],
		'summerMinimumKW' : summer['summerMinimumKW'],
		'summerMinimumHour' : summer['summerMinimumHour'],
		'winterPeakKW' : winter['winterPeakKW'],
		'winterTotalEnergy' : winter['winterTotalEnergy'],
		'winterPeakHour' : winter['winterPeakHour'],
		'winterMinimumKW' : winter['winterMinimumKW'],
		'winterMinimumHour' : winter['winterMinimumHour'],
		'shoulderPeakKW' : shoulder['shoulderPeakKW'],
		'shoulderTotalEnergy' : shoulder['shoulderTotalEnergy'],
		'shoulderPeakHour' : shoulder['shoulderPeakHour'],
		'shoulderMinimumKW' : shoulder['shoulderMinimumKW'],
		'shoulderMinimumHour' : shoulder['shoulderMinimumHour']} 


	print scada


	calibration_config = {'timezone' : 'PST+8PDT',
	'startdate' : '2011-01-01 01:00:00',   
	'stopdate' : '2011-12-31 23:00:00',    
	'region' : 6,
	'feeder_rating' : 7.5,
	'nom_volt' : 7200,
	#'voltage_players' : [os.path.abspath('./uploads/VA.player').replace('\\', '/'), os.path.abspath('./uploads/VB.player').replace('\\', '/'), os.path.abspath('./uploads/VC.player').replace('\\', '/')],
	'load_shape_scalar' : 1.0, 
	'load_shape_player_file' : pJoin(modelDir,filename)}

	calDir = pJoin(modelDir, "Calibration")

	if not os.path.isdir(calDir):
		os.makedirs(calDir)

	calibratedFeederTree, calibrationConfiguration = feederCalibrate.startCalibration(calDir, localTree, scada, model_name, calibration_config)

	print calibratedFeederTree
	
	with open(pJoin(modelDir,"ABEC_Coloma_cal.json"),"w") as outFile:
		json.dump(calibratedFeederTree, outFile, indent=4)


	# localTree1 = deepcopy(calibratedFeederTree)
	# comparesol(modelDir,localTree1)


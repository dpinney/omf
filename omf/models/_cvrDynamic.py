''' Calculate CVR impacts using a targetted set of dynamic loadflows. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess
import math, re, csv
import multiprocessing
from copy import deepcopy
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
from datetime import datetime, date, time, timedelta
import __metaModel__
from __metaModel__ import *

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
import calibrate
from solvers import gridlabd

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"_cvrDynamic.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def sepRealImag(complexStr):
	''' real and imaginary parts of a complex number.
	handles string if the string starts with a '+' or a '-'
	handles negative or positive, real and imaginary parts 
	example sepRealImag(-20.5-6j) = (-20.5, -6)'''
	if complexStr[0] == '+' or complexStr[0] == '-':
		complexStr1 = complexStr[1:len(complexStr)+1]
		sign = complexStr[0] + '1' 
	else:
		complexStr1 = complexStr
		sign = 1
	if complexStr1.find('+')>0:
		real = float(complexStr1[0:complexStr1.find('+')])*float(sign)
		imag = float(complexStr1[complexStr1.find('+')+1:-1])
	else:
		if complexStr1.find('-')>0:
			real = float(complexStr1[0:complexStr1.find('-')])*float(sign)
			imag = float(complexStr1[complexStr1.find('-')+1:-1])*-1
		else:
			if complexStr1.find('j')>0:
				real = 0.0
				imag = float(complexStr1[0:complexStr1.find('j')])*float(sign)
			else:
				real = float(complexStr1)*float(sign)
				imag = 0.0
	return real,imag

def run(modelDir,inData):
	'''This reads a glm file, changes the method of powerflow and reruns'''
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
	except:
		pass
	allOutput = {}
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inData["created"] = str(datetime.now())
	with open(pJoin(modelDir,"allInputData.json"),"w") as inputFile:
		json.dump(inData, inputFile, indent=4)
	binaryName = "gridlabd"
	startTime = datetime.now()
	with open(pJoin(modelDir,"calibratedFeeder.json"), "r") as jsonIn:
		feederJson = json.load(jsonIn)
		localTree = feederJson.get("tree", {})
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
			if localTree[key].get("control","").lower() == "manual":
				localTree[key]['control'] = "VOLT"
				print "changing capacitor control from manual to volt"
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
	HOURS = float(100)
	year_lp = False   #leap year
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
		# if localTree[key].get('object','') == "capacitor":
		# 	time_delay_cap = localTree[key]['time_delay']
		# 	print "time_delay_cap",time_delay_cap
	#change the recorder names
	for key in localTree:
		if localTree[key].get('object','') == "collector" or localTree[key].get('object','') == "recorder":
			if localTree[key].get('file','').startswith('Z'):
				localTree[key]['file'] = localTree[key].get('file','').replace('Z','NewZ')
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
	simStartDate = inData['simStart']
	feeder.adjustTime(localTree,HOURS,"hours",simStartDate)	
	output1 = gridlabd.runInFilesystem(localTree,keepFiles=True,workDir=modelDir)
	os.remove(pJoin(modelDir,"PID.txt"))
	pnew = output1['NewZregulator.csv']['power_in.real']
	qnew = output1['NewZregulator.csv']['power_in.imag']
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
				rnew += output1['New'+device]['sum(power_losses_' + letter + '.real)'][element]
				inew += output1['New'+device]['sum(power_losses_' + letter + '.imag)'][element]
		realLoss.append(r)
		imagLoss.append(i)
		realLossnew.append(rnew)
		imagLossnew.append(inew)
	#voltage calculations and tap calculations
	lowVoltage = []
	meanVoltage = []
	highVoltage = []
	lowVoltagenew = []
	meanVoltagenew = []
	highVoltagenew = []
	tap = {'A':[],'B':[],'C':[]}
	tapnew = {'A':[],'B':[],'C':[]}
	volt = {'A':[],'B':[],'C':[]}
	voltnew = {'A':[],'B':[],'C':[]}
	switch = {'A':[],'B':[],'C':[]}
	switchnew = {'A':[],'B':[],'C':[]}
	for element in range(int(HOURS)):
		for letter in ['A','B','C']:
			tap[letter].append(output['Zregulator.csv']['tap_' + letter][element])
			tapnew[letter].append(output1['NewZregulator.csv']['tap_' + letter][element])
			#voltage real, imag
			vr, vi = sepRealImag(output['ZsubstationBottom.csv']['voltage_'+letter][element])
			volt[letter].append(math.sqrt(vr**2+vi**2)/60)
			vrnew, vinew = sepRealImag(output1['NewZsubstationBottom.csv']['voltage_'+letter][element])
			voltnew[letter].append(math.sqrt(vrnew**2+vinew**2)/60)
			if capKeys != []:
				switch[letter].append(output['ZcapSwitch' + str(int(capKeys[0])) + '.csv']['switch'+ letter][element])
				switchnew[letter].append(output1['NewZcapSwitch' + str(int(capKeys[0])) + '.csv']['switch'+ letter][element])
		lowVoltage.append(float(output['ZvoltageJiggle.csv']['min(voltage_12.mag)'][element])/2.0)
		meanVoltage.append(float(output['ZvoltageJiggle.csv']['mean(voltage_12.mag)'][element])/2.0)
		highVoltage.append(float(output['ZvoltageJiggle.csv']['max(voltage_12.mag)'][element])/2.0)
		lowVoltagenew.append(float(output1['NewZvoltageJiggle.csv']['min(voltage_12.mag)'][element])/2.0)
		meanVoltagenew.append(float(output1['NewZvoltageJiggle.csv']['mean(voltage_12.mag)'][element])/2.0)
		highVoltagenew.append(float(output1['NewZvoltageJiggle.csv']['max(voltage_12.mag)'][element])/2.0)
	#energy calculations
	whEnergy = []
	whLosses = []
	whLoads = []
	whEnergy.append(sum(p)/10**6)
	whLosses.append(sum(realLoss)/10**6)
	whLoads.append((sum(p)-sum(realLoss))/10**6)
	whEnergy.append(sum(pnew)/10**6)
	whLosses.append(sum(realLossnew)/10**6)
	whLoads.append((sum(pnew)-sum(realLossnew))/10**6)
	indices = ['No IVVC', 'With IVVC']
	# energySalesRed = (whLoads[1]-whLoads[0])*(inData['wholesaleEnergyCostPerKwh'])*1000
	# lossSav = (whLosses[0]-whLosses[1])*inData['wholesaleEnergyCostPerKwh']*1000
	# print energySalesRed, lossSav
	#plots
	ticks = []
	plt.clf()
	plt.title("total energy")
	plt.ylabel("total load and losses (MWh)")
	for element in range(2):
		ticks.append(element)
		bar_loss = plt.bar(element, whLosses[element], 0.15, color= 'red')
		bar_load = plt.bar(element+0.15, whLoads[element], 0.15, color= 'orange')
	plt.legend([bar_load[0],bar_loss[0]],['total load', 'total losses'],bbox_to_anchor=(0., 0.915, 1., .102), loc=3,
		       ncol=2, mode="expand", borderaxespad=0.1)
	plt.xticks([t+0.15 for t in ticks],indices)
	plt.savefig(pJoin(modelDir,"totalEnergy.png"))
	with open(pJoin(modelDir,"totalEnergy.png"),"rb") as inFile:
		allOutput["totalEnergy"] = inFile.read().encode("base64")
	#real and imaginary power
	plt.figure("real power")
	plt.title("Real Power at substation")
	plt.ylabel("substation real power (MW)")
	pMW = [element/10**6 for element in p]
	pMWn = [element/10**6 for element in pnew]
	pw = plt.plot(pMW)
	npw = plt.plot(pMWn)
	plt.legend([pw[0], npw[0]], ['NO IVVC','WITH IVVC'],bbox_to_anchor=(0., 0.915, 1., .102), loc=3,
		ncol=2, mode="expand", borderaxespad=0.1)
	plt.savefig(pJoin(modelDir,"realPower.png"))
	with open(pJoin(modelDir,"realPower.png"),"rb") as inFile:
		allOutput["realPower"] = inFile.read().encode("base64")
	plt.figure("Reactive power")
	plt.title("Reactive Power at substation")
	plt.ylabel("substation reactive power (MVAR)")
	qMVAR = [element/10**6 for element in q]
	qMVARn = [element/10**6 for element in qnew]
	iw = plt.plot(qMVAR)
	niw = plt.plot(qMVARn)
	plt.legend([iw[0], niw[0]], ['NO IVVC','WITH IVVC'],bbox_to_anchor=(0., 0.915, 1., .102), loc=3,
		ncol=2, mode="expand", borderaxespad=0.1)
	plt.savefig(pJoin(modelDir,"imaginaryPower.png"))
	with open(pJoin(modelDir,"imaginaryPower.png"),"rb") as inFile:
		allOutput["imaginaryPower"] = inFile.read().encode("base64")
	#voltage plots
	plt.figure("voltages as a function of time")
	f,ax = plt.subplots(2,sharex=True)
	f.suptitle("Min and Max voltages on the feeder")
	lv = ax[0].plot(lowVoltage,color = 'cadetblue')
	mv = ax[0].plot(meanVoltage,color = 'blue')
	hv = ax[0].plot(highVoltage, color = 'cadetblue')
	ax[0].legend([lv[0], mv[0], hv[0]], ['low voltage','mean voltage','high voltage'],bbox_to_anchor=(0., 0.915, 1., .1), loc=3,
		ncol=3, mode="expand", borderaxespad=0.1)
	ax[0].set_ylabel('NO IVVC')
	nlv = ax[1].plot(lowVoltagenew,color = 'cadetblue')
	nmv = ax[1].plot(meanVoltagenew,color = 'blue')
	nhv = ax[1].plot(highVoltagenew, color = 'cadetblue')
	ax[1].set_ylabel('WITH IVVC')
	plt.savefig(pJoin(modelDir,"Voltages.png"))
	with open(pJoin(modelDir,"Voltages.png"),"rb") as inFile:
		allOutput["minMaxvolts"] = inFile.read().encode("base64")
	#tap positions
	plt.figure("TAP positions NO IVVC")
	f,ax = plt.subplots(6,sharex=True)
	f.set_size_inches(10,12.0)
	#f.suptitle("Regulator Tap positions")
	ax[0].plot(tap['A'])
	ax[0].set_title("Regulator Tap positions NO IVVC")
	ax[0].set_ylabel("TAP A")
	ax[1].plot(tap['B'])
	ax[1].set_ylabel("TAP B")
	ax[2].plot(tap['C'])
	ax[2].set_ylabel("TAP C")
	ax[3].plot(tapnew['A'])
	ax[3].set_title("WITH IVVC")
	ax[3].set_ylabel("TAP A")
	ax[4].plot(tapnew['B'])
	ax[4].set_ylabel("TAP B")
	ax[5].plot(tapnew['C'])
	ax[5].set_ylabel("TAP C")
	for subplot in range(6):
		ax[subplot].set_ylim(-20,20)
	f.tight_layout()
	plt.savefig(pJoin(modelDir,"RegulatorTAPpositions.png"))
	with open(pJoin(modelDir,"RegulatorTAPpositions.png"),"rb") as inFile:
		allOutput["regulatorTap"] = inFile.read().encode("base64")
	#substation voltages
	plt.figure("substation voltage as a function of time")
	f,ax = plt.subplots(6,sharex=True)
	f.set_size_inches(10,12.0)
	#f.suptitle("voltages at substation NO IVVC")
	ax[0].plot(volt['A'])
	ax[0].set_title('Substation voltages NO IVVC')
	ax[0].set_ylabel('voltage A')
	ax[1].plot(volt['B'])
	ax[1].set_ylabel('voltage B')
	ax[2].plot(volt['C'])
	ax[2].set_ylabel('voltage C')
	ax[3].plot(voltnew['A'])
	ax[3].set_title("WITH IVVC")
	ax[3].set_ylabel('voltage A')
	ax[4].plot(voltnew['B'])
	ax[4].set_ylabel('voltage B')
	ax[5].plot(voltnew['C'])
	ax[5].set_ylabel('voltage C')
	f.tight_layout()
	plt.savefig(pJoin(modelDir,"substationVoltages.png"))
	with open(pJoin(modelDir,"substationVoltages.png"),"rb") as inFile:
		allOutput["substationVoltages"] = inFile.read().encode("base64")
	#cap switches
	plt.figure("capacitor switch state as a function of time")
	f,ax = plt.subplots(6,sharex=True)
	f.set_size_inches(10,12.0)
	#f.suptitle("Capacitor switch state NO IVVC")
	ax[0].plot(switch['A'])
	ax[0].set_title("Capacitor switch state NO IVVC")
	ax[0].set_ylabel("switch A")
	ax[1].plot(switch['B'])
	ax[1].set_ylabel("switch B")
	ax[2].plot(switch['C'])
	ax[2].set_ylabel("switch C")
	ax[3].plot(switchnew['A'])
	ax[3].set_title("WITH IVVC")
	ax[3].set_ylabel("switch A")
	ax[4].plot(switchnew['B'])
	ax[4].set_ylabel("switch B")
	ax[5].plot(switchnew['C'])
	ax[5].set_ylabel("switch C")
	for subplot in range(6):
		ax[subplot].set_ylim(-2,2)
	f.tight_layout()
	plt.savefig(pJoin(modelDir,"capacitorSwitch.png"))
	with open(pJoin(modelDir,"capacitorSwitch.png"),"rb") as inFile:
		allOutput["capacitorSwitch"] = inFile.read().encode("base64")
	#plt.show()
	#monetization
	monthNames = ["January", "February", "March", "April", "May", "June", "July", "August",
		"September", "October", "November", "December"]
	monthToSeason = {'January':'Winter','February':'Winter','March':'Spring','April':'Spring',
		'May':'Spring','June':'Summer','July':'Summer','August':'Summer',
		'September':'Fall','October':'Fall','November':'Fall','December':'Winter'}
	if year_lp == True:
		febDays = 29
	else:
		febDays = 28
	monthHours = [int(31*24),int(febDays*24),int(31*24),int(30*24),int(31*24),int(30*24),int(31*24),int(31*24),int(30*24),int(31*24),int(30*24),int(31*24)]
	#find simulation months
	temp = 0
	cumulHours = []
	for x in range(12):
		temp += monthHours[x]
		cumulHours.append(temp)
	for i in range(12):
		if i == 0:
			lowval = 0
		else:
			lowval = cumulHours[i-1]
		if HOURS<=cumulHours[i] and HOURS>=lowval:
			hourMonth = monthNames[i]
			hourIndex = i
	#calculate peaks for the number of months in simulation
	previndex = 0
	monthPeak = {}
	monthPeakNew = {}
	peakSaveDollars = {}
	energyLostDollars = {}
	lossRedDollars = {}
	for month in range(hourIndex+1):
		index1 = int(previndex)
		index2 = int(min((index1 + int(monthHours[month])), HOURS))
		monthPeak[monthNames[month]] = max(p[index1:index2])/1000.0
		monthPeakNew[monthNames[month]] = max(pnew[index1:index2])/1000.0
		peakSaveDollars[monthNames[month]] = (monthPeak[monthNames[month]]-monthPeakNew[monthNames[month]])*float(inData['peakDemandCost'+str(monthToSeason[monthNames[month]])+'PerKw'])
		lossRedDollars[monthNames[month]] = (sum(realLoss[index1:index2])/1000.0 - sum(realLossnew[index1:index2])/1000.0)*(float(inData['wholesaleEnergyCostPerKwh']))
		energyLostDollars[monthNames[month]] = (sum(p[index1:index2])/1000.0  - sum(pnew[index1:index2])/1000.0  - sum(realLoss[index1:index2])/1000.0  
			+ sum(realLossnew[index1:index2])/1000.0 )*(float(inData['wholesaleEnergyCostPerKwh']) - float(inData['retailEnergyCostPerKwh']))
		previndex = index2
	#money charts
	simMonths = monthNames[:hourIndex+1]
	fig = plt.figure("cost benefit barchart",figsize=(10,8))
	ticks = range(len(simMonths))
	ticks1 = [element+0.15 for element in ticks]
	ticks2 = [element+0.30 for element in ticks]
	print ticks
	eld = [energyLostDollars[month] for month in simMonths]
	lrd = [lossRedDollars[month] for month in simMonths]
	psd = [peakSaveDollars[month] for month in simMonths]
	bar_eld = plt.bar(ticks,eld,0.15,color='red') 
	bar_psd = plt.bar(ticks1,psd,0.15,color='blue')
	bar_lrd = plt.bar(ticks2,lrd,0.15,color='green')
	plt.legend([bar_eld[0], bar_psd[0], bar_lrd[0]], ['energyLostDollars','peakReductionDollars','lossReductionDollars'],bbox_to_anchor=(0., 1.015, 1., .102), loc=3,
		ncol=2, mode="expand", borderaxespad=0.1)
	monShort = [element[0:3] for element in simMonths]
	plt.xticks([t+0.15 for t in ticks],monShort)
	plt.ylabel('Utility Savings ($)')
	plt.savefig(pJoin(modelDir,"spendChart.png"))
	with open(pJoin(modelDir,"spendChart.png"),"rb") as inFile:
		allOutput["spendChart"] = inFile.read().encode("base64")
	#cumulative savings graphs
	fig = plt.figure("cost benefit barchart",figsize=(10,5))
	annualSavings = sum(eld) + sum(lrd) + sum(psd)
	annualSave = lambda x:(annualSavings - float(inData['omCost'])) * x - float(inData['capitalCost'])
	simplePayback = float(inData['capitalCost'])/(annualSavings - float(inData['omCost']))
	plt.xlabel('Year After Installation')
	plt.xlim(0,30)
	plt.ylabel('Cumulative Savings ($)')
	plt.plot([0 for x in range(31)],c='gray')
	plt.axvline(x=simplePayback, ymin=0, ymax=1, c='gray', linestyle='--')
	plt.plot([annualSave(x) for x in range(31)], c='green')
	plt.savefig(pJoin(modelDir,"savingsChart.png"))
	with open(pJoin(modelDir,"savingsChart.png"),"rb") as inFile:
		allOutput["savingsChart"] = inFile.read().encode("base64")
	#data for highcharts
	simStartTimestamp = simStartDate + " 00:00:00"
	timestamps = []
	for y in range(int(HOURS)):
		formatDate = datetime.strptime(simStartTimestamp,"%Y-%m-%d %H:%M:%S") + timedelta(hours =y)
		timestamps.append(formatDate.strftime("%Y-%m-%d %H:%M:%S"))
	allOutput["timestamps"] = timestamps
	allOutput["noCVRPower"] = p
	allOutput["withCVRPower"] = pnew
	allOutput["noCVRLoad"] = whLoads[0]
	allOutput["withCVRLoad"] = whLoads[1]
	allOutput["noCVRLosses"] = whLosses[0]
	allOutput["withCVRLosses"] = whLosses[1]
	allOutput["noCVRTaps"] = tap
	allOutput["withCVRTaps"] = tapnew
	allOutput["noCVRSubVolts"] = volt
	allOutput["withCVRSubVolts"] = voltnew
	allOutput["noCVRCapSwitch"] = switch
	allOutput["withCVRCapSwitch"] = switchnew
	allOutput["noCVRHighVolt"] = highVoltage
	allOutput["withCVRHighVolt"] = highVoltagenew
	allOutput["noCVRLowVolt"] = lowVoltage
	allOutput["withCVRLowVolt"] = lowVoltagenew
	allOutput["noCVRMeanVolt"] = meanVoltage
	allOutput["withCVRMeanVolt"] = meanVoltagenew
	# Update the runTime in the input file.
	endTime = datetime.now()
	inData["runTime"] = str(timedelta(seconds=int((endTime - startTime).total_seconds())))
	with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
		json.dump(inData, inFile, indent=4)
	with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
		json.dump(allOutput, outFile, indent=4)
	print "DONE RUNNING", modelDir

def _tests():
	"runs local tests for dynamic CVR model"
	#creating a work directory and initializing data
	inData = { "modelName": "Automated DynamicCVR Testing",
		"modelType": "_cvrDynamic",
		"user": "admin",
		"runTime": "",
		"capitalCost": 30000,
		"omCost": 1000,
		"wholesaleEnergyCostPerKwh": 0.06,
		"retailEnergyCostPerKwh": 0.10,
		"peakDemandCostSpringPerKw": 5.0,
		"peakDemandCostSummerPerKw": 10.0,
		"peakDemandCostFallPerKw": 6.0,
		"peakDemandCostWinterPerKw": 8.0,
		"simStart": "2011-01-01"}
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	modelDir = pJoin(workDir, inData["user"], inData["modelName"])
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
	#calibrate and run cvrdynamic	
	feederPath = pJoin(__metaModel__._omfDir,"data", "Feeder", "admin","ABEC Frank new.json")
	scadaPath = pJoin(__metaModel__._omfDir,"uploads","FrankScada.tsv")
	calibrate.omfCalibrate(modelDir,feederPath,scadaPath)
	try:
		os.remove(pJoin(modelDir,"stderr.txt"))
		os.remove(pJoin(modelDir,"stdout.txt"))
	except:
		pass
	run(modelDir,inData)

if __name__ == '__main__':
	_tests()

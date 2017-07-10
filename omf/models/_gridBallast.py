''' Powerflow results for one Gridlab instance. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess, math, gc, networkx as nx,  numpy as np
from networkx.drawing.nx_agraph import graphviz_layout
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib
matplotlib.pyplot.switch_backend('Agg')
import multiprocessing
from os.path import join as pJoin
from os.path import split as pSplit
from jinja2 import Template
import traceback
from omf.models import __metaModel__
from __metaModel__ import *

# OMF imports
import omf.feeder as feeder
from omf.weather import zipCodeToClimateName
# System check - linux doesn't support newer GridLAB-D versions
if sys.platform == 'linux2':
	from omf.solvers import gridlabd
else:
	from omf.solvers import gridlabd_gridballast as gridlabd

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = 'gridBallast simulator'

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir, modelName + '.html'),'r') as tempFile:
	template = Template(tempFile.read())

def run(modelDir, inputDict):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(datetime.datetime.now())
	with open(pJoin(modelDir,'allInputData.json')) as inputFile:
		feederName = json.load(inputFile).get('feederName1','feeder1')
	inputDict["feederName1"] = feederName
	# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	# If we are re-running, remove output and old GLD run:
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
		shutil.rmtree(pJoin(modelDir,"gldContainer"))
	except:
		pass
	# Start background process.
	backProc = multiprocessing.Process(target = heavyProcessing, args = (modelDir, inputDict,))
	backProc.start()
	print "SENT TO BACKGROUND", modelDir
	with open(pJoin(modelDir, "PPID.txt"),"w+") as pPidFile:
		pPidFile.write(str(backProc.pid))

def runForeground(modelDir, inputDict):
	''' Run the model in the current process. WARNING: LONG RUN TIME. '''
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(datetime.datetime.now())
	# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	# If we are re-running, remove output and old GLD run:
	try: os.remove(pJoin(modelDir,"allOutputData.json"))
	except: pass
	try: shutil.rmtree(pJoin(modelDir,"gldContainer"))
	except: pass
	# Start process.
	with open(pJoin(modelDir, "PPID.txt"),"w+") as pPidFile:
		pPidFile.write('-999')
	heavyProcessing(modelDir, inputDict)

def heavyProcessing(modelDir, inputDict):
	''' Run the model in its directory. WARNING: GRIDLAB CAN TAKE HOURS TO COMPLETE. '''
	print "STARTING TO RUN", modelDir
	beginTime = datetime.datetime.now()
	# Get feeder name and data in.
	try: os.mkdir(pJoin(modelDir,'gldContainer'))
	except: pass
	try:	
		feederName = inputDict["feederName1"]
		inputDict["climateName"], latforpvwatts = zipCodeToClimateName(inputDict["zipCode"])
		shutil.copy(pJoin(__metaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"),
			pJoin(modelDir, "gldContainer", "climate.tmy2"))
		startTime = datetime.datetime.now()
		feederJson = json.load(open(pJoin(modelDir, feederName+'.omd')))
		tree = feederJson["tree"]
		#add a check to see if there is already a climate object in the omd file
		#if there is delete the climate from attachments and the climate object
		attachKeys = feederJson['attachments'].keys()
		for key in attachKeys:
			if key.endswith('.tmy2'):
				del feederJson['attachments'][key]	
		treeKeys = feederJson["tree"].keys()
		for key in treeKeys:
			if 'object' in feederJson['tree'][key]:
			 	if feederJson['tree'][key]['object'] == 'climate':
			 		del feederJson['tree'][key]
		oldMax = feeder.getMaxKey(tree)
		tree[oldMax + 1] = {'omftype':'module','argument':'climate'}
		tree[oldMax + 2] = {'object':'climate','name':'Climate','interpolate':'QUADRATIC','tmyfile':'climate.tmy2'}
		# tree[oldMax + 3] = {'object':'capacitor','control':'VOLT','phases':'ABCN','name':'CAPTEST','parent':'tm_1','capacitor_A':'0.10 MVAr','capacitor_B':'0.10 MVAr','capacitor_C':'0.10 MVAr','time_delay':'300.0','nominal_voltage':'2401.7771','voltage_set_high':'2350.0','voltage_set_low':'2340.0','switchA':'CLOSED','switchB':'CLOSED','switchC':'CLOSED','control_level':'INDIVIDUAL','phases_connected':'ABCN','dwell_time':'0.0','pt_phases':'ABCN'}
		# Set up GLM with correct time and recorders:
		feeder.attachRecorders(tree, "Regulator", "object", "regulator")
		feeder.attachRecorders(tree, "Capacitor", "object", "capacitor")
		feeder.attachRecorders(tree, "Inverter", "object", "inverter")
		feeder.attachRecorders(tree, "Windmill", "object", "windturb_dg")
		feeder.attachRecorders(tree, "CollectorVoltage", None, None)
		feeder.attachRecorders(tree, "Climate", "object", "climate")
		feeder.attachRecorders(tree, "OverheadLosses", None, None)
		feeder.attachRecorders(tree, "UndergroundLosses", None, None)
		feeder.attachRecorders(tree, "TriplexLosses", None, None)
		feeder.attachRecorders(tree, "TransformerLosses", None, None)
		feeder.groupSwingKids(tree)

		# System check - linux doesn't support newer GridLAB-D versions
		if sys.platform == 'linux2':
			pass
		else:
			# Set up GridBallast Controls
			totalWH = 0
			totalZIP = 0
			gbWH = 0
			gbZIP = 0
			# HACK: tree[10:19] is empty
			tree[10] = {'omftype':'#include', 'argument':'\"hot_water_demand.glm\"'}
			tree[11] = {'omftype':'#include', 'argument':'\"lock_mode_schedule.glm\"'}
			# Attach frequency player
			tree[12] = {'omftype':'class player', 'argument':'{double value;}'}
			stub = {'object':'player', 'file':'frequency.PLAYER', 'property':'value', 'name':'frequency'}
			copyStub = dict(stub)
			tree[feeder.getMaxKey(tree)+1] = copyStub
			# Waterheater Controller properties
			for key in tree.keys():
				if ('name' in tree[key]) and (tree[key].get('object') == 'waterheater'):
			 		totalWH += 1
		 			# Frequency control parameters
		 			tree[key]['enable_freq_control'] = 'true'
		 			tree[key]['measured_frequency'] = 'frequency.value'
		 			tree[key]['freq_lowlimit'] = 59.9
		 			tree[key]['freq_uplimit'] = 60.1
		 			tree[key]['heat_mode'] = 'ELECTRIC'
		 			# Voltage control parameters
		 			# tree[key]['enable_volt_control'] = 'true'
		 			# tree[key]['volt_lowlimit'] = 240.4
		 			# tree[key]['volt_uplimit'] = 241.4
		 			tree[key]['average_delay_time'] = 120
		 			# Lock Mode parameters
		 			# tree[key]['enable_lock'] = 'temp_lock_enable'
		 			# tree[key]['lock_STATUS'] = 'temp_lock_status'
		 			# tree[key]['controller_priority'] = 3214
		 			gbWH += 1
			 		# fix waterheater property demand to water_demand for newer GridLAB-D versions
			 		if 'demand' in tree[key]:
			 			# tree[key]['water_demand'] = tree[key]['demand']
			 			tree[key]['water_demand'] = 'weekday_hotwater*1'
			 			del tree[key]['demand']
			# ZIPload Controller properties
			for key in tree.keys():
				if ('name' in tree[key]) and (tree[key].get('object') == 'ZIPload'):
			 		totalZIP += 1
			 		# Frequency control parameters
		 			tree[key]['enable_freq_control'] = 'true'
		 			tree[key]['measured_frequency'] = 'frequency.value'
		 			tree[key]['freq_lowlimit'] = 59.9
		 			tree[key]['freq_uplimit'] = 60.1
		 			# Voltage control parameters
		 			# tree[key]['enable_volt_control'] = 'true'
		 			# tree[key]['volt_lowlimit'] = 240.4
		 			# tree[key]['volt_uplimit'] = 241.4
		 			tree[key]['average_delay_time'] = 120
		 			# Lock Mode parameters
		 			# tree[key]['enable_lock'] = 'temp_lock_enable'
		 			# tree[key]['lock_STATUS'] = 'temp_lock_status'
		 			# tree[key]['controller_priority'] = 3214
		 			tree[key]['groupid'] = 'fan'
		 			gbZIP += 1

		# Attach recorder for waterheaters on/off
		stub = {'object':'group_recorder', 'group':'"class=waterheater"', 'property':'is_waterheater_on', 'interval':3600, 'file':'allWaterheaterOn.csv'}
		copyStub = dict(stub)
		tree[feeder.getMaxKey(tree)+1] = copyStub
		# Attach recorder for waterheater tank temperatures
		stub = {'object':'group_recorder', 'group':'"class=waterheater"', 'property':'temperature', 'interval':3600, 'file':'allWaterheaterTemp.csv'}
		copyStub = dict(stub)
		tree[feeder.getMaxKey(tree)+1] = copyStub
		# Attach collector for total waterheater load
		stub = {'object':'collector', 'group':'"class=waterheater"', 'property':'sum(actual_load)', 'interval':3600, 'file':'allWaterheaterLoad.csv'}
		copyStub = dict(stub)
		tree[feeder.getMaxKey(tree)+1] = copyStub
		# Attach collector for total network load
		stub = {'object':'collector', 'group':'"class=triplex_meter"', 'property':'sum(measured_real_power)', 'interval':3600, 'file':'allMeterPower.csv'}
		copyStub = dict(stub)
		tree[feeder.getMaxKey(tree)+1] = copyStub

		# Attach collector for total overall ZIPload power/load
		stub = {'object':'collector', 'group':'"class=ZIPload"', 'property':'sum(base_power)', 'interval':3600, 'file':'allZIPloadPower.csv'}
		copyStub = dict(stub)
		tree[feeder.getMaxKey(tree)+1] = copyStub
		# Attach recorder for each ZIPload power/load
		stub = {'object':'group_recorder', 'group':'"class=ZIPload"', 'property':'base_power', 'interval':3600, 'file':'eachZIPloadPower.csv'}
		copyStub = dict(stub)
		tree[feeder.getMaxKey(tree)+1] = copyStub
		# Attach recorder for all ZIPloads demand_rate
		stub = {'object':'group_recorder', 'group':'"class=ZIPload"', 'property':'demand_rate', 'interval':3600, 'file':'allZIPloadDemand.csv'}
		copyStub = dict(stub)
		tree[feeder.getMaxKey(tree)+1] = copyStub
		# Attach recorder for all ZIPloads on
		stub = {'object':'group_recorder', 'group':'"class=ZIPload"', 'property':'number_of_devices_on', 'interval':3600, 'file':'allZIPloadOn.csv'}
		copyStub = dict(stub)
		tree[feeder.getMaxKey(tree)+1] = copyStub

		# Attach recorders for system voltage map:
		stub = {'object':'group_recorder', 'group':'"class=node"', 'interval':3600}
		for phase in ['A','B','C']:
			copyStub = dict(stub)
			copyStub['property'] = 'voltage_' + phase
			copyStub['file'] = phase.lower() + 'VoltDump.csv'
			tree[feeder.getMaxKey(tree) + 1] = copyStub
		# Attach recorders for system voltage map, triplex:
		stub = {'object':'group_recorder', 'group':'"class=triplex_node"', 'interval':3600}
		for phase in ['1','2']:
			copyStub = dict(stub)
			copyStub['property'] = 'voltage_' + phase
			copyStub['file'] = phase.lower() + 'nVoltDump.csv'
			tree[feeder.getMaxKey(tree) + 1] = copyStub
		# And get meters for system voltage map:
		stub = {'object':'group_recorder', 'group':'"class=triplex_meter"', 'interval':3600}
		for phase in ['1','2']:
			copyStub = dict(stub)
			copyStub['property'] = 'voltage_' + phase
			copyStub['file'] = phase.lower() + 'mVoltDump.csv'
			tree[feeder.getMaxKey(tree) + 1] = copyStub
		feeder.adjustTime(tree=tree, simLength=float(inputDict["simLength"]),
			simLengthUnits=inputDict["simLengthUnits"], simStartDate=inputDict["simStartDate"])
		# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
		rawOut = gridlabd.runInFilesystem(tree, attachments=feederJson["attachments"], 
			keepFiles=True, workDir=pJoin(modelDir,'gldContainer'))
		cleanOut = {}
		# Std Err and Std Out
		cleanOut['stderr'] = rawOut['stderr']
		cleanOut['stdout'] = rawOut['stdout']
		# Time Stamps
		for key in rawOut:
			print key
			if '# timestamp' in rawOut[key]:
				cleanOut['timeStamps'] = rawOut[key]['# timestamp']
				break
			elif '# property.. timestamp' in rawOut[key]:
				cleanOut['timeStamps'] = rawOut[key]['# property.. timestamp']
			else:
				cleanOut['timeStamps'] = []
		# Day/Month Aggregation Setup:
		stamps = cleanOut.get('timeStamps',[])
		level = inputDict.get('simLengthUnits','hours')
		# Climate
		for key in rawOut:
			if key.startswith('Climate_') and key.endswith('.csv'):
				cleanOut['climate'] = {}
				cleanOut['climate']['Rain Fall (in/h)'] = hdmAgg(rawOut[key].get('rainfall'), sum, level)
				cleanOut['climate']['Wind Speed (m/s)'] = hdmAgg(rawOut[key].get('wind_speed'), avg, level)
				cleanOut['climate']['Temperature (F)'] = hdmAgg(rawOut[key].get('temperature'), max, level)
				cleanOut['climate']['Snow Depth (in)'] = hdmAgg(rawOut[key].get('snowdepth'), max, level)
				cleanOut['climate']['Direct Normal (W/sf)'] = hdmAgg(rawOut[key].get('solar_direct'), sum, level)
				#cleanOut['climate']['Global Horizontal (W/sf)'] = hdmAgg(rawOut[key].get('solar_global'), sum, level)	
				climateWbySFList= hdmAgg(rawOut[key].get('solar_global'), sum, level)
				#converting W/sf to W/sm
				climateWbySMList= [x*10.76392 for x in climateWbySFList]
				cleanOut['climate']['Global Horizontal (W/sm)']=climateWbySMList			
		# Voltage Band
		if 'VoltageJiggle.csv' in rawOut:
			cleanOut['allMeterVoltages'] = {}
			cleanOut['allMeterVoltages']['Min'] = hdmAgg([float(i / 2) for i in rawOut['VoltageJiggle.csv']['min(voltage_12.mag)']], min, level)
			cleanOut['allMeterVoltages']['Mean'] = hdmAgg([float(i / 2) for i in rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)']], avg, level)
			cleanOut['allMeterVoltages']['StdDev'] = hdmAgg([float(i / 2) for i in rawOut['VoltageJiggle.csv']['std(voltage_12.mag)']], avg, level)
			cleanOut['allMeterVoltages']['Max'] = hdmAgg([float(i / 2) for i in rawOut['VoltageJiggle.csv']['max(voltage_12.mag)']], max, level)
		# Power Consumption
		cleanOut['Consumption'] = {}
		# Set default value to be 0, avoiding missing value when computing Loads
		cleanOut['Consumption']['Power'] = [0] * int(inputDict["simLength"])
		cleanOut['Consumption']['Losses'] = [0] * int(inputDict["simLength"])
		cleanOut['Consumption']['DG'] = [0] * int(inputDict["simLength"])
		for key in rawOut:
			if key.startswith('SwingKids_') and key.endswith('.csv'):
				oneSwingPower = hdmAgg(vecPyth(rawOut[key]['sum(power_in.real)'],rawOut[key]['sum(power_in.imag)']), avg, level)
				if 'Power' not in cleanOut['Consumption']:
					cleanOut['Consumption']['Power'] = oneSwingPower
				else:
					cleanOut['Consumption']['Power'] = vecSum(oneSwingPower,cleanOut['Consumption']['Power'])
			elif key.startswith('Inverter_') and key.endswith('.csv'): 	
				realA = rawOut[key]['power_A.real']
				realB = rawOut[key]['power_B.real']
				realC = rawOut[key]['power_C.real']
				imagA = rawOut[key]['power_A.imag']
				imagB = rawOut[key]['power_B.imag']
				imagC = rawOut[key]['power_C.imag']
				oneDgPower = hdmAgg(vecSum(vecPyth(realA,imagA),vecPyth(realB,imagB),vecPyth(realC,imagC)), avg, level)
				if 'DG' not in cleanOut['Consumption']:
					cleanOut['Consumption']['DG'] = oneDgPower
				else:
					cleanOut['Consumption']['DG'] = vecSum(oneDgPower,cleanOut['Consumption']['DG'])
			elif key.startswith('Windmill_') and key.endswith('.csv'):
				vrA = rawOut[key]['voltage_A.real']
				vrB = rawOut[key]['voltage_B.real']
				vrC = rawOut[key]['voltage_C.real']
				viA = rawOut[key]['voltage_A.imag']
				viB = rawOut[key]['voltage_B.imag']
				viC = rawOut[key]['voltage_C.imag']
				crB = rawOut[key]['current_B.real']
				crA = rawOut[key]['current_A.real']
				crC = rawOut[key]['current_C.real']
				ciA = rawOut[key]['current_A.imag']
				ciB = rawOut[key]['current_B.imag']
				ciC = rawOut[key]['current_C.imag']
				powerA = vecProd(vecPyth(vrA,viA),vecPyth(crA,ciA))
				powerB = vecProd(vecPyth(vrB,viB),vecPyth(crB,ciB))
				powerC = vecProd(vecPyth(vrC,viC),vecPyth(crC,ciC))
				oneDgPower = hdmAgg(vecSum(powerA,powerB,powerC), avg, level)
				if 'DG' not in cleanOut['Consumption']:
					cleanOut['Consumption']['DG'] = oneDgPower
				else:
					cleanOut['Consumption']['DG'] = vecSum(oneDgPower,cleanOut['Consumption']['DG'])
			elif key in ['OverheadLosses.csv', 'UndergroundLosses.csv', 'TriplexLosses.csv', 'TransformerLosses.csv']:
				realA = rawOut[key]['sum(power_losses_A.real)']
				imagA = rawOut[key]['sum(power_losses_A.imag)']
				realB = rawOut[key]['sum(power_losses_B.real)']
				imagB = rawOut[key]['sum(power_losses_B.imag)']
				realC = rawOut[key]['sum(power_losses_C.real)']
				imagC = rawOut[key]['sum(power_losses_C.imag)']
				oneLoss = hdmAgg(vecSum(vecPyth(realA,imagA),vecPyth(realB,imagB),vecPyth(realC,imagC)), avg, level)
				if 'Losses' not in cleanOut['Consumption']:
					cleanOut['Consumption']['Losses'] = oneLoss
				else:
					cleanOut['Consumption']['Losses'] = vecSum(oneLoss,cleanOut['Consumption']['Losses'])
			elif key.startswith('Regulator_') and key.endswith('.csv'):
				#split function to strip off .csv from filename and user rest of the file name as key. for example- Regulator_VR10.csv -> key would be Regulator_VR10
				regName=""
				regName = key
				newkey=regName.split(".")[0]
				cleanOut[newkey] ={}
				cleanOut[newkey]['RegTapA'] = [0] * int(inputDict["simLength"])
				cleanOut[newkey]['RegTapB'] = [0] * int(inputDict["simLength"])
				cleanOut[newkey]['RegTapC'] = [0] * int(inputDict["simLength"])
				cleanOut[newkey]['RegTapA'] = rawOut[key]['tap_A']
				cleanOut[newkey]['RegTapB'] = rawOut[key]['tap_B']
				cleanOut[newkey]['RegTapC'] = rawOut[key]['tap_C']
				cleanOut[newkey]['RegPhases'] = rawOut[key]['phases'][0]
			elif key.startswith('Capacitor_') and key.endswith('.csv'):
				capName=""
				capName = key
				newkey=capName.split(".")[0]
				cleanOut[newkey] ={}
				cleanOut[newkey]['Cap1A'] = [0] * int(inputDict["simLength"])
				cleanOut[newkey]['Cap1B'] = [0] * int(inputDict["simLength"])
				cleanOut[newkey]['Cap1C'] = [0] * int(inputDict["simLength"])
				cleanOut[newkey]['Cap1A'] = rawOut[key]['switchA']
				cleanOut[newkey]['Cap1B'] = rawOut[key]['switchB']
				cleanOut[newkey]['Cap1C'] = rawOut[key]['switchC']
				cleanOut[newkey]['CapPhases'] = rawOut[key]['phases'][0]

		# System check - linux doesn't support newer GridLAB-D versions
		if sys.platform == 'linux2':
			pass
		else:
			# Frequency Player
			inArray = feederJson['attachments']['frequency.PLAYER'].split('\n')
			tempArray = []
			for each in inArray:
				x = each.split(',')
				y = float(x[1])
				tempArray.append(y)
			cleanOut['frequencyPlayer'] = tempArray

		# Print gridBallast Outputs to allOutputData.json
		cleanOut['gridBallast'] = {}
		# System check - linux doesn't support newer GridLAB-D versions
		if sys.platform == 'linux2':
			pass
		else:
			cleanOut['gridBallast']['penetrationLevel'] = 100*(gbWH+gbZIP)/(totalWH+totalZIP)
		if 'allWaterheaterOn.csv' in rawOut:
			cleanOut['gridBallast']['waterheaterOn'] = {}
			for key in rawOut['allWaterheaterOn.csv']:
				if key.startswith('waterheater'):
					cleanOut['gridBallast']['waterheaterOn'][key] = rawOut.get('allWaterheaterOn.csv')[key]
		if 'allWaterheaterTemp.csv' in rawOut:
			cleanOut['gridBallast']['waterheaterTemp'] = {}
			for key in rawOut['allWaterheaterTemp.csv']:
				if key.startswith('waterheater'):
					cleanOut['gridBallast']['waterheaterTemp'][key] = rawOut.get('allWaterheaterTemp.csv')[key]
		if 'allMeterPower.csv' in rawOut:
			cleanOut['gridBallast']['totalNetworkLoad'] = rawOut.get('allMeterPower.csv')['sum(measured_real_power)']

		if ('allWaterheaterLoad.csv' in rawOut) and ('allZIPloadPower.csv' in rawOut):
			cleanOut['gridBallast']['availabilityMagnitude'] = [x + y for x, y in zip(rawOut.get('allWaterheaterLoad.csv')['sum(actual_load)'], rawOut.get('allZIPloadPower.csv')['sum(base_power)'])]
		if 'eachZIPloadPower.csv' in rawOut:
			cleanOut['gridBallast']['ZIPloadPower'] = {}
			for key in rawOut['eachZIPloadPower.csv']:
				if key.startswith('ZIPload'):
					cleanOut['gridBallast']['ZIPloadPower'][key] = rawOut.get('eachZIPloadPower.csv')[key]
		if 'allZIPloadDemand.csv' in rawOut:
			cleanOut['gridBallast']['ZIPloadDemand'] = {}
			for key in rawOut['allZIPloadDemand.csv']:
				if key.startswith('ZIPload'):
					cleanOut['gridBallast']['ZIPloadDemand'][key] = rawOut.get('allZIPloadDemand.csv')[key]
		if 'allZIPloadOn.csv' in rawOut:
			cleanOut['gridBallast']['ZIPloadOn'] = {}
			for key in rawOut['allZIPloadOn.csv']:
				if key.startswith('ZIPload'):
					cleanOut['gridBallast']['ZIPloadOn'][key] = rawOut.get('allZIPloadOn.csv')[key]

		# EventTime calculations
		eventTime = inputDict['eventTime']
		eventLength = inputDict['eventLength']
		eventLength = eventLength.split(':')
		eventDuration = datetime.timedelta(hours=int(eventLength[0]), minutes=int(eventLength[1]))
		eventStart = datetime.datetime.strptime(eventTime, '%Y-%m-%d %H:%M')
		eventEnd = eventStart + eventDuration
		cleanOut['gridBallast']['eventStart'] = str(eventStart)
		cleanOut['gridBallast']['eventEnd'] = str(eventEnd)
		# Drop timezone from timeStamp, Convert string to date
		timeStamps = [x[:19] for x in cleanOut['timeStamps']]
		dateTimeStamps = [datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in timeStamps]	
		eventEndIdx =  dateTimeStamps.index(eventEnd)
		# Recovery Time
		whOn = cleanOut['gridBallast']['waterheaterOn']
		whOnList = whOn.values()
		whOnZip = zip(*whOnList)
		whOnSum = [sum(x) for x in whOnZip]
		anyOn = [x > 0 for x in whOnSum] 
		tRecIdx = anyOn.index(True, eventEndIdx)
		tRec = dateTimeStamps[tRecIdx]
		recoveryTime = tRec - eventEnd
		cleanOut['gridBallast']['recoveryTime'] = str(recoveryTime)
		# Waterheaters Off-Duration
		offDuration = tRec - eventStart
		cleanOut['gridBallast']['offDuration'] = str(offDuration)
		# Reserve Magnitude Target (RMT)
		availMag = cleanOut['gridBallast']['availabilityMagnitude']
		totNetLoad = cleanOut['gridBallast']['totalNetworkLoad']
		# loadZip = zip(availMag,totNetLoad)
		# rmt = [x[0]/x[1] for x in loadZip]
		rmt = 100*1000*sum(availMag)/sum(totNetLoad)
		cleanOut['gridBallast']['rmt'] = rmt
		# Reserve Magnitude Variability Tolerance (RMVT)
		avgAvailMag = sum(availMag)/len(availMag)
		rmvtMax = max(availMag)/avgAvailMag
		rmvtMin = min(availMag)/avgAvailMag
		rmvt = rmvtMax - rmvtMin
		cleanOut['gridBallast']['rmvt'] = rmvt
		# Availability
		notAvail = float(availMag.count(0))/len(timeStamps)
		avail = (1-notAvail)*100
		cleanOut['gridBallast']['availability'] = avail
		# Waterheater Temperature Drop calculations
		whTemp = cleanOut['gridBallast']['waterheaterTemp']
		whTempList = whTemp.values()
		whTempZip = zip(*whTempList)
		whTempDrops = []
		LOWER_LIMIT_TEMP = 125 # Used for calculating quality of service.
		for time in whTempZip:
			tempDrop = sum([t < LOWER_LIMIT_TEMP for t in time])
			whTempDrops.append(tempDrop)
		cleanOut['gridBallast']['waterheaterTempDrops'] = whTempDrops

		# ZIPload calculations for Availability and QoS
		zPower = cleanOut['gridBallast']['ZIPloadPower']
		zPowerList = zPower.values()
		zPowerZip = zip(*zPowerList)
		zPowerSum = [sum(x) for x in zPowerZip]
		zDemand = cleanOut['gridBallast']['ZIPloadDemand']
		zDemandList  = zDemand.values()
		zDemandZip = zip(*zDemandList)
		zDrops = []
		for time in zDemandZip:
			for each in zPowerZip:
				zIdx = 0
				if each[zIdx] == 0:
					zIdx += 1
					zDrop = sum([t > 0 for t in time])
					zDrops.append(zDrop)
				else:
					zDrops.append(0)
		cleanOut['gridBallast']['qualityDrops'] = [x + y for x, y in zip(whTempDrops, zDrops)]

		# What percentage of our keys have lat lon data?
		latKeys = [tree[key]['latitude'] for key in tree if 'latitude' in tree[key]]
		latPerc = 1.0*len(latKeys)/len(tree)
		if latPerc < 0.25: doNeato = True
		else: doNeato = False
		# Generate the frames for the system voltage map time traveling chart.
		genTime = generateVoltChart(tree, rawOut, modelDir, neatoLayout=doNeato)
		cleanOut['genTime'] = genTime
		# Aggregate up the timestamps:
		if level=='days':
			cleanOut['timeStamps'] = aggSeries(stamps, stamps, lambda x:x[0][0:10], 'days')
		elif level=='months':
			cleanOut['timeStamps'] = aggSeries(stamps, stamps, lambda x:x[0][0:7], 'months')
		# Write the output.
		with open(pJoin(modelDir, "allOutputData.json"),"w") as outFile:
			json.dump(cleanOut, outFile, indent=4)
		# Update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
		with open(pJoin(modelDir, "allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
		# Clean up the PID file.
		os.remove(pJoin(modelDir, "gldContainer", "PID.txt"))
		print "DONE RUNNING", modelDir
	except Exception as e:
		# If input range wasn't valid delete output, write error to disk.
		cancel(modelDir)	
		thisErr = traceback.format_exc()
		print 'ERROR IN MODEL', modelDir, thisErr
		inputDict['stderr'] = thisErr
		with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
	finishTime = datetime.datetime.now()
	inputDict["runTime"] = str(datetime.timedelta(seconds = int((finishTime - beginTime).total_seconds())))
	with open(pJoin(modelDir, "allInputData.json"),"w") as inFile:
		json.dump(inputDict, inFile, indent = 4)
	try:
		os.remove(pJoin(modelDir,"PPID.txt"))
	except:
		pass

def generateVoltChart(tree, rawOut, modelDir, neatoLayout=True):
	''' Map the voltages on a feeder over time using a movie.'''
	# We need to timestamp frames with the system clock to make sure the browser caches them appropriately.
	genTime = str(datetime.datetime.now()).replace(':','.')
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	# Make a graph object.
	fGraph = feeder.treeToNxGraph(tree)
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		# was formerly : positions = nx.graphviz_layout(cleanG, prog='neato') but this threw an error
		positions = graphviz_layout(cleanG, prog='neato')
	else:
		rawPositions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
		# HACK: the import code reverses the y coords.
		def yFlip(pair):
			try: return (pair[0], -1.0*pair[1])
			except: return (0,0)
		positions = {k:yFlip(rawPositions[k]) for k in rawPositions}
	# Plot all time steps.
	nodeVolts = {}
	for step, stamp in enumerate(rawOut['aVoltDump.csv']['# timestamp']):
		# Build voltage map.
		nodeVolts[step] = {}
		for nodeName in [x for x in rawOut.get('aVoltDump.csv',{}).keys() + rawOut.get('1nVoltDump.csv',{}).keys() + rawOut.get('1mVoltDump.csv',{}).keys() if x != '# timestamp']:
			allVolts = []
			for phase in ['a','b','c','1n','2n','1m','2m']:
				try:
					voltStep = rawOut[phase + 'VoltDump.csv'][nodeName][step]
				except:
					continue # the nodeName doesn't have the phase we're looking for.
				# HACK: Gridlab complex number format sometimes uses i, sometimes j, sometimes d. WTF?
				if type(voltStep) is str: voltStep = voltStep.replace('i','j')
				v = complex(voltStep)
				phaseVolt = abs(v)
				if phaseVolt != 0.0:
					if _digits(phaseVolt)>3:
						# Normalize to 120 V standard
						phaseVolt = phaseVolt*(120/feedVoltage)
					allVolts.append(phaseVolt)
			# HACK: Take average of all phases to collapse dimensionality.
			nodeVolts[step][nodeName] = avg(allVolts)
	# Draw animation.
	voltChart = plt.figure(figsize=(15,15))
	plt.axes(frameon = 0)
	plt.axis('off')
	#set axes step equal
	voltChart.gca().set_aspect('equal')
	custom_cm = matplotlib.colors.LinearSegmentedColormap.from_list('custColMap',[(0.0,'blue'),(0.25,'darkgray'),(0.75,'darkgray'),(1.0,'yellow')])
	custom_cm.set_under(color='black')
	edgeIm = nx.draw_networkx_edges(fGraph, positions)
	nodeIm = nx.draw_networkx_nodes(fGraph,
		pos = positions,
		node_color = [nodeVolts[0].get(n,0) for n in fGraph.nodes()],
		linewidths = 0,
		node_size = 30,
		cmap = custom_cm)
	plt.sci(nodeIm)
	plt.clim(110,130)
	plt.colorbar()
	plt.title(rawOut['aVoltDump.csv']['# timestamp'][0])
	def update(step):
		nodeColors = np.array([nodeVolts[step].get(n,0) for n in fGraph.nodes()])
		plt.title(rawOut['aVoltDump.csv']['# timestamp'][step])
		nodeIm.set_array(nodeColors)
		return nodeColors,
	anim = FuncAnimation(voltChart, update, frames=len(rawOut['aVoltDump.csv']['# timestamp']), interval=200, blit=False)
	anim.save(pJoin(modelDir,'voltageChart.mp4'), codec='h264', extra_args=['-pix_fmt', 'yuv420p'])
	# Reclaim memory by closing, deleting and garbage collecting the last chart.
	voltChart.clf()
	plt.close()
	del voltChart
	gc.collect()
	return genTime

def avg(inList):
	''' Average a list. Really wish this was built-in. '''
	return sum(inList)/len(inList)

def hdmAgg(series, func, level):
	''' Simple hour/day/month aggregation for Gridlab. '''
	if level in ['days','months']:
		return aggSeries(stamps, series, func, level)
	else:
		return series

def aggSeries(timeStamps, timeSeries, func, level):
	''' Aggregate a list + timeStamps up to the required time level. '''
	# Different substring depending on what level we aggregate to:
	if level=='months': endPos = 7
	elif level=='days': endPos = 10
	combo = zip(timeStamps, timeSeries)
	# Group by level:
	groupedCombo = _groupBy(combo, lambda x1,x2: x1[0][0:endPos]==x2[0][0:endPos])
	# Get rid of the timestamps:
	groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
	return map(func, groupedRaw)

def _pyth(x,y):
	''' Compute the third side of a triangle--BUT KEEP SIGNS THE SAME FOR DG. '''
	sign = lambda z:(-1 if z<0 else 1)
	fullSign = sign(sign(x)*x*x + sign(y)*y*y)
	return fullSign*math.sqrt(x*x + y*y)

def _digits(x):
	''' Returns number of digits before the decimal in the float x. '''
	return math.ceil(math.log10(x+1))

def vecPyth(vx,vy):
	''' Pythagorean theorem for pairwise elements from two vectors. '''
	rows = zip(vx,vy)
	return map(lambda x:_pyth(*x), rows)

def vecSum(*args):
	''' Add n vectors. '''
	return map(sum,zip(*args))

def _prod(inList):
	''' Product of all values in a list. '''
	return reduce(lambda x,y:x*y, inList, 1)

def vecProd(*args):
	''' Multiply n vectors. '''
	return map(_prod, zip(*args))

def threePhasePowFac(ra,rb,rc,ia,ib,ic):
	''' Get power factor for a row of threephase volts and amps. Gridlab-specific. '''
	pfRow = lambda row:math.cos(math.atan((row[0]+row[1]+row[2])/(row[3]+row[4]+row[5])))
	rows = zip(ra,rb,rc,ia,ib,ic)
	return map(pfRow, rows)

def roundSeries(ser):
	''' Round everything in a vector to 4 sig figs. '''
	return map(lambda x:roundSig(x,4), ser)

def _groupBy(inL, func):
	''' Take a list and func, and group items in place comparing with func. Make sure the func is an equivalence relation, or your brain will hurt. '''
	if inL == []: return inL
	if len(inL) == 1: return [inL]
	newL = [[inL[0]]]
	for item in inL[1:]:
		if func(item, newL[-1][0]):
			newL[-1].append(item)
		else:
			newL.append([item])
	return newL

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"zipCode": "59001",
		"feederName1": "Olin Barre GH EOL Solar GridBallast",
		"simStartDate": "2012-01-01",
		"simLength": "72",
		"simLengthUnits": "hours", #minutes
		"eventType": "ramping", #unramping, overfrequency, underfrequency
		"eventTime": "2012-01-02 14:00",
		"eventLength": "03:00"
	}
	creationCode = __metaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__metaModel__._omfDir, "scratch", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _tests():
	# Location
	modelLoc = pJoin(__metaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	# renderAndShow(template, modelName)
	# Run the model.
	runForeground(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
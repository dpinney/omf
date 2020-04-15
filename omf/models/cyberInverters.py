''' Powerflow results for one Gridlab instance. '''

import json, os, csv, shutil, math
from os.path import join as pJoin
from functools import reduce

# OMF imports
from omf import feeder, weather
from omf.solvers import gridlabd
from omf.models import solarEngineering
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "The cyberInverters model shows the impacts of inverter hacks on a feeder including system voltages, regulator actions, and capacitor responses."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. WARNING: GRIDLAB CAN TAKE HOURS TO COMPLETE. '''
	# feederName = inputDict["feederName1"]
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	zipCode = "59001" #TODO get zip code from the PV and Load input file
	
	#Value check for attackVariable
	if inputDict.get("attackVariable", "None") == "None":
		attackAgentType = "None"
	else:
		attackAgentType = inputDict['attackVariable']
	#Open defense agent HDF5 file
	# with open(pJoin(modelDir,"defenseVariable.csv"),"w") as defenseVariableFile:
	# 	defenseVariableFile.write(inputDict['defenseVariable'])
	# try:
	# 	#TODO do whatever it is we need with defense agent values
	# 	with open(pJoin(modelDir,"defenseVariable.csv"), newline='') as inFile:
	# 		reader = csv.reader(inFile)
	# 		for row in reader:
	# 			#Do something!
	# 			if 3>4: raise Exception
	# 			pass
	# except:
	# 	#TODO change to an appropriate warning message
	# 	errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-demandResponse#walkthrough'>OMF Wiki demandResponse</a>"
	# 	raise Exception(errorMessage)
	#Value check for train
	if inputDict.get("trainAgent", "") == "False":
		trainAgentValue = False
	else:
		trainAgentValue = True
	#None check for simulation length
	if inputDict.get("simLength", "None") == "None":
		simLengthValue = None
	else:
		simLengthValue = int(inputDict["simLength"])
	#None check for simulation length
	if inputDict.get("simLengthUnits", "None") == "None":
		simLengthUnitsValue = None
	else:
		simLengthUnitsValue = inputDict["simLengthUnits"]
	#None check for simulation start date
	if inputDict.get("simStartDate", "None") == "None":
		simStartDateTimeValue = None
		simStartDateValue = None
		simStartTimeValue = None
	else:
		simStartDateTimeValue = inputDict["simStartDate"]
		simStartDateValue = simStartDateTimeValue.split('T')[0]
		simStartTimeValue = simStartDateTimeValue.split('T')[1]

	inputDict["climateName"] = weather.zipCodeToClimateName(zipCode)
	shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"),
		pJoin(modelDir, "climate.tmy2"))
	with open(pJoin(modelDir, feederName + '.omd')) as f:
		feederJson = json.load(f)
	tree = feederJson["tree"]
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
	# Attach current recorder for overhead_lines
	currentStub = {'object':'group_recorder', 'group':'"class=overhead_line"', 'interval':3600}
	for phase in ['A','B','C']:
		copyCurrentStub = dict(currentStub)
		copyCurrentStub['property'] = 'current_out_' + phase
		copyCurrentStub['file'] = 'OH_line_current_phase' + phase + '.csv'
		tree[feeder.getMaxKey(tree) + 1] = copyCurrentStub
	rating_stub = {'object':'group_recorder', 'group':'"class=overhead_line"', 'interval':3600}
	copyRatingStub = dict(rating_stub)
	copyRatingStub['property'] = 'continuous_rating'
	copyRatingStub['file'] = 'OH_line_cont_rating.csv'
	tree[feeder.getMaxKey(tree) + 1] = copyRatingStub
	flow_stub = {'object':'group_recorder', 'group':'"class=overhead_line"', 'interval':3600}
	copyFlowStub = dict(flow_stub)
	copyFlowStub['property'] = 'flow_direction'
	copyFlowStub['file'] = 'OH_line_flow_direc.csv'
	tree[feeder.getMaxKey(tree) + 1] = copyFlowStub
	# Attach current recorder for underground_lines
	currentStubOH = {'object':'group_recorder', 'group':'"class=underground_line"', 'interval':3600}
	for phase in ['A','B','C']:
		copyCurrentStubOH = dict(currentStubOH)
		copyCurrentStubOH['property'] = 'current_out_' + phase
		copyCurrentStubOH['file'] = 'UG_line_current_phase' + phase + '.csv'
		tree[feeder.getMaxKey(tree) + 1] = copyCurrentStubOH
	ug_rating_stub = {'object':'group_recorder', 'group':'"class=underground_line"', 'interval':3600}
	copyUGRatingStub = dict(ug_rating_stub)
	copyUGRatingStub['property'] = 'continuous_rating'
	copyUGRatingStub['file'] = 'UG_line_cont_rating.csv'
	tree[feeder.getMaxKey(tree) + 1] = copyUGRatingStub
	ug_flow_stub = {'object':'group_recorder', 'group':'"class=underground_line"', 'interval':3600}
	ugCopyFlowStub = dict(ug_flow_stub)
	ugCopyFlowStub['property'] = 'flow_direction'
	ugCopyFlowStub['file'] = 'UG_line_flow_direc.csv'
	tree[feeder.getMaxKey(tree) + 1] = ugCopyFlowStub
	# And get meters for system voltage map:
	stub = {'object':'group_recorder', 'group':'"class=triplex_meter"', 'interval':3600}
	for phase in ['1','2']:
		copyStub = dict(stub)
		copyStub['property'] = 'voltage_' + phase
		copyStub['file'] = phase.lower() + 'mVoltDump.csv'
		tree[feeder.getMaxKey(tree) + 1] = copyStub
	for key in tree:
		if 'bustype' in tree[key].keys():
			if tree[key]['bustype'] == 'SWING':
				tree[key]['object'] = 'meter'
				swingN = tree[key]['name']
	swingRecord = {'object':'recorder', 'property':'voltage_A,measured_real_power,measured_power','file':'subVoltsA.csv','parent':swingN, 'interval':60}
	tree[feeder.getMaxKey(tree) + 1] = swingRecord
	for key in tree:
		if 'omftype' in tree[key].keys() and tree[key]['argument']=='minimum_timestep=3600':
			tree[key]['argument'] = 'minimum_timestep=60'
	# If there is a varvolt object in the tree, add recorder to swingbus and node from voltage_measurements property
	# Find var_volt object
	downLineNode = 'None'
	for key in tree:
		if 'object' in tree[key].keys() and tree[key]['object']=='volt_var_control':
			downLineNode = tree[key]['voltage_measurements']
	if downLineNode != 'None':
		downNodeRecord = {'object':'recorder', 'property':'voltage_A','file':'firstDownlineVoltsA.csv','parent':downLineNode, 'interval':60}
		tree[feeder.getMaxKey(tree) + 1] = downNodeRecord
	
	feeder.adjustTime(tree=tree, simLength=float(inputDict["simLength"]),
		simLengthUnits=inputDict["simLengthUnits"], simStartDate=simStartDateValue)
	
	outData = {}
	# Std Err and Std Out
	outData['stderr'] = "This should be stderr"  #rawOut['stderr']
	outData['stdout'] = "This should be stdout"  #rawOut['stdout']
	# Time Stamps
	#TODO: Find a way to create a list of timestamps that would have been generated by gridlab-d outputs
	outData['timeStamps'] = []
	# For now, hard-coding timestamps for a 25 second simulation with one second intervals
	outData['timeStamps'] = [
		"2019-07-01 00:00:00 PDT",
        "2019-07-01 00:00:01 PDT",
        "2019-07-01 00:00:02 PDT",
        "2019-07-01 00:00:03 PDT",
        "2019-07-01 00:00:04 PDT",
        "2019-07-01 00:00:05 PDT",
        "2019-07-01 00:00:06 PDT",
        "2019-07-01 00:00:07 PDT",
        "2019-07-01 00:00:08 PDT",
        "2019-07-01 00:00:09 PDT",
        "2019-07-01 00:00:10 PDT",
        "2019-07-01 00:00:11 PDT",
        "2019-07-01 00:00:12 PDT",
        "2019-07-01 00:00:13 PDT",
        "2019-07-01 00:00:14 PDT",
        "2019-07-01 00:00:15 PDT",
        "2019-07-01 00:00:16 PDT",
        "2019-07-01 00:00:17 PDT",
        "2019-07-01 00:00:18 PDT",
        "2019-07-01 00:00:19 PDT",
        "2019-07-01 00:00:20 PDT",
        "2019-07-01 00:00:21 PDT",
        "2019-07-01 00:00:22 PDT",
        "2019-07-01 00:00:23 PDT",
        "2019-07-01 00:00:24 PDT"
        ]
	
	# Day/Month Aggregation Setup:
	stamps = outData.get('timeStamps',[])
	level = inputDict.get('simLengthUnits','seconds')
	# TODO: Create/populate Climate data without gridlab-d
	outData['climate'] = {}
	# for key in rawOut:
	# 	if key.startswith('Climate_') and key.endswith('.csv'):
	# 		outData['climate'] = {}
	# 		outData['climate']['Rain Fall (in/h)'] = hdmAgg(rawOut[key].get('rainfall'), sum, level)
	# 		outData['climate']['Wind Speed (m/s)'] = hdmAgg(rawOut[key].get('wind_speed'), avg, level)
	# 		outData['climate']['Temperature (F)'] = hdmAgg(rawOut[key].get('temperature'), max, level)
	# 		outData['climate']['Snow Depth (in)'] = hdmAgg(rawOut[key].get('snowdepth'), max, level)
	# 		outData['climate']['Direct Normal (W/sf)'] = hdmAgg(rawOut[key].get('solar_direct'), sum, level)
	# 		#outData['climate']['Global Horizontal (W/sf)'] = hdmAgg(rawOut[key].get('solar_global'), sum, level)	
	# 		climateWbySFList= hdmAgg(rawOut[key].get('solar_global'), sum, level)
	# 		#converting W/sf to W/sm
	# 		climateWbySMList= [x*10.76392 for x in climateWbySFList]
	# 		outData['climate']['Global Horizontal (W/sm)']=climateWbySMList			
	# Voltage Band
	outData['allMeterVoltages'] = {}
	outData['allMeterVoltages']['Min'] = [0] * int(inputDict["simLength"])
	outData['allMeterVoltages']['Mean'] = [0] * int(inputDict["simLength"])
	outData['allMeterVoltages']['StdDev'] = [0] * int(inputDict["simLength"])
	outData['allMeterVoltages']['Max'] = [0] * int(inputDict["simLength"])
	# Power Consumption
	outData['Consumption'] = {}
	# Set default value to be 0, avoiding missing value when computing Loads
	outData['Consumption']['Power'] = [0] * int(inputDict["simLength"])
	outData['Consumption']['Losses'] = [0] * int(inputDict["simLength"])
	outData['Consumption']['DG'] = [0] * int(inputDict["simLength"])
	
	outData['swingTimestamps'] = []
	outData['swingTimestamps'] = outData['timeStamps']

	latKeys = [tree[key]['latitude'] for key in tree if 'latitude' in tree[key]]
	latPerc = 1.0*len(latKeys)/len(tree)
	if latPerc < 0.25: doNeato = True
	else: doNeato = False
	# Generate the frames for the system voltage map time traveling chart.
	# TODO: fix voltChart in python3
	# genTime, mapTimestamp = solarEngineering.generateVoltChart(tree, rawOut, modelDir, neatoLayout=doNeato)
	# outData['genTime'] = genTime
	# outData['mapTimestamp'] = mapTimestamp
	# Aggregate up the timestamps:
	if level=='days':
		outData['timeStamps'] = aggSeries(stamps, stamps, lambda x:x[0][0:10], 'days')
	elif level=='months':
		outData['timeStamps'] = aggSeries(stamps, stamps, lambda x:x[0][0:7], 'months')

	def convertInputs():
		#create the PyCIGAR_inputs folder to store the input files to run PyCIGAR
		try:
			os.mkdir(pJoin(modelDir,"PyCIGAR_inputs"))
		except FileExistsError:
			print("PyCIGAR_inputs folder already exists!")
			pass
		except:
			print("Error occurred creating PyCIGAR_inputs folder")

		#create misc_inputs.csv file in folder
		# f1Name = "misc_inputs.csv"
		# with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", f1Name)) as f1:
		# 	misc_inputs = f1.read()
		misc_dict = {"Oscillation Penalty":2, 
		"Action Penalty":0.1, 
		"Deviation from Optimal Penalty":4, 
		"load file timestep":1, 
		"power factor":0.9, 
		"load scaling factor":1.5, 
		"solar scaling factor":3, 
		"measurement filter time constant mean":1.2, 
		"measurement filter time constant std":0.2, 
		"output filter time constant mean":0.115, 
		"output filter time constant std":0.025, 
		"bp1 default":0.98, 
		"bp2 default":1.01, 
		"bp3 default":1.01, 
		"bp4 default":1.04, 
		"bp5 default":1.07, 
		"max tap change default":16, 
		"forward band default":2, 
		"tap number default":16, 
		"tap delay default":2}
		with open(pJoin(modelDir,"PyCIGAR_inputs","misc_inputs.csv"),"w") as miscFile:
			#Populate misc_inputs.csv
			# miscFile.write(misc_inputs)
			for key in misc_dict.keys():
				miscFile.write("%s,%s\n"%(key,misc_dict[key]))

		#create ieee37.dss file in folder
		dss_filename = "ieee37.dss"
		with open(pJoin(modelDir, "PyCIGAR_inputs", dss_filename),"w") as dssFile:
			dssFile.write(inputDict['dssFile'])
		try:
			#TODO do whatever it is we need with load and pv values
			with open(pJoin(modelDir, "PyCIGAR_inputs", dss_filename), newline='') as inFile:
				reader = csv.reader(inFile)
				for row in reader:
					#Do something!
					if 3>4: raise Exception
					pass
		except:
			#TODO change to an appropriate warning message
			errorMessage = "OpenDSS file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-demandResponse#walkthrough'>OMF Wiki demandResponse</a>"
			raise Exception(errorMessage)

		#create load_solar_data.csv file in folder
		with open(pJoin(modelDir,"PyCIGAR_inputs","load_solar_data.csv"),"w") as loadPVFile:
			loadPVFile.write(inputDict['loadPV'])
			#Open load and PV input file
		try:
			#TODO do whatever it is we need with load and pv values
			with open(pJoin(modelDir,"PyCIGAR_inputs","load_solar_data.csv"), newline='') as inFile:
				reader = csv.reader(inFile)
				for row in reader:
					#Do something!
					if 3>4: raise Exception
					pass
		except:
			#TODO change to an appropriate warning message
			errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-demandResponse#walkthrough'>OMF Wiki demandResponse</a>"
			raise Exception(errorMessage)

		#create breakpoints.csv file in folder
		# f1Name = "breakpoints.csv"
		# with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", f1Name)) as f1:
		# 	breakpoints_inputs = f1.read()
		with open(pJoin(modelDir,"PyCIGAR_inputs","breakpoints.csv"),"w") as breakpointsFile:
			breakpointsFile.write(inputDict['breakpoints'])
		try:
			#TODO do whatever it is we need with load and pv values
			with open(pJoin(modelDir, "PyCIGAR_inputs", "breakpoints.csv"), newline='') as inFile:
				reader = csv.reader(inFile)
				for row in reader:
					#Do something!
					if 3>4: raise Exception
					pass
		except:
			#TODO change to an appropriate warning message
			errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-demandResponse#walkthrough'>OMF Wiki demandResponse</a>"
			raise Exception(errorMessage)
	def runPyCIGAR():
		#create the pycigarOutput folder to store the output file(s) generated by PyCIGAR
		try:
			os.mkdir(pJoin(modelDir,"pycigarOutput"))
		except FileExistsError:
			print("pycigarOutput folder already exists!")
			pass
		except:
			print("Error occurred creating pycigarOutput folder")

		#import and run pycigar
		import pycigar

		pycigar.main(
		    modelDir + "/PyCIGAR_inputs/misc_inputs.csv",
		    modelDir + "/PyCIGAR_inputs/ieee37.dss",
		    modelDir + "/PyCIGAR_inputs/load_solar_data.csv",
		    modelDir + "/PyCIGAR_inputs/breakpoints.csv",
		    2,
		    None,
		    modelDir + "/pycigarOutput/",
		)

	def convertOutputs():
		#set outData[] values to those from modelDir/pycigarOutput/pycigar_output_specs_.json
		#read in the pycigar-outputed json
		with open(pJoin(modelDir,"pycigarOutput","pycigar_output_specs.json"), 'r') as f:
			pycigarJson = json.load(f)
		
		#convert "allMeterVoltages"
		outData["allMeterVoltages"] = pycigarJson["allMeterVoltages"]
		
		#convert "Consumption"."Power"
		outData["Consumption"]["Power"] = pycigarJson["Consumption"]["Power Substation (W)"]

		#convert "Consumption"."Losses"
		outData["Consumption"]["Losses"] = pycigarJson["Consumption"]["Losses Total (W)"]

		#convert "Consumption"."DG"
		outData["Consumption"]["DG"] = pycigarJson["Consumption"]["DG Output (W)"]

		#convert "powerFactors"
		outData["powerFactors"] = pycigarJson["Substation Power Factor (%)"]	

		#convert "swingVoltage"
		outData["swingVoltage"] = pycigarJson["Substation Top Voltage(V)"]

		#convert "downlineNodeVolts"
		outData["downlineNodeVolts"] = pycigarJson["Substation Bottom Voltage(V)"]

		#convert "minVoltBand"
		outData["minVoltBand"] = pycigarJson["Substation Regulator Minimum Voltage(V)"]

		#convert "maxVoltBand"
		outData["maxVoltBand"] = pycigarJson["Substation Regulator Maximum Voltage(V)"]

		#create lists of circuit object names
		regNameList = []
		capNameList = []
		for key in pycigarJson:
			if key.startswith('Regulator_'):
				regNameList.append(key)
			elif key.startswith('Capacitor_'):
				capNameList.append(key)

		#convert regulator data
		for reg_name in regNameList:
			outData[reg_name] = {}
			regPhaseValue = pycigarJson[reg_name]["RegPhases"]
			if regPhaseValue.find('A') != -1:
				outData[reg_name]["RegTapA"] = pycigarJson[reg_name]["creg1a"]

			if regPhaseValue.find('B') != -1:
				outData[reg_name]["RegTapB"] = pycigarJson[reg_name]["creg1b"]

			if regPhaseValue.find('C') != -1:
				outData[reg_name]["RegTapC"] = pycigarJson[reg_name]["creg1c"]

			outData[reg_name]["RegPhases"] = regPhaseValue

		#convert inverter data
		inverter_output_dict = {} 
		for inv_dict in pycigarJson["Inverter Outputs"]:
			#create a new dictionary to represent the single inverter 
			new_inv_dict = {}
			#get values from pycigar output for given single inverter
			inv_name = inv_dict["Name"]
			inv_volt = inv_dict["Voltage (V)"]
			inv_pow_real = inv_dict["Power Output (W)"]
			inv_pow_imag = inv_dict["Reactive Power Output (VAR)"]
			#populate single inverter dict with pycigar values
			new_inv_dict["Voltage"] = inv_volt
			new_inv_dict["Power_Real"] = inv_pow_real
			new_inv_dict["Power_Imag"] = inv_pow_imag
			#add single inverter dict to dict of all the inverters using the inverter name as the key 
			inverter_output_dict[inv_name] = new_inv_dict
		outData["Inverter_Outputs"] = inverter_output_dict

		#convert capacitor data - Need one on test circuit first!
		for cap_name in capNameList:
			outData[cap_name] = {}
			capPhaseValue = pycigarJson[cap_name]["CapPhases"]
			if capPhaseValue.find('A') != -1:
				outData[cap_name]['Cap1A'] = [0] * int(inputDict["simLength"])
				outData[cap_name]['Cap1A'] = pycigarJson[cap_name]['switchA']

			if capPhaseValue.find('B') != -1:
				outData[cap_name]['Cap1B'] = [0] * int(inputDict["simLength"])
				outData[cap_name]['Cap1B'] = pycigarJson[cap_name]['switchB']

			if capPhaseValue.find('C') != -1:
				outData[cap_name]['Cap1C'] = [0] * int(inputDict["simLength"])
				outData[cap_name]['Cap1C'] = pycigarJson[cap_name]['switchC']
			
			outData[cap_name]["CapPhases"] = capPhaseValue

	convertInputs()
	runPyCIGAR()
	convertOutputs()
	return outData

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
	combo = list(zip(timeStamps, timeSeries))
	# Group by level:
	groupedCombo = _groupBy(combo, lambda x1,x2: x1[0][0:endPos]==x2[0][0:endPos])
	# Get rid of the timestamps:
	groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
	return list(map(func, groupedRaw))

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
	return [_pyth(*x) for x in rows]

def vecSum(*args):
	''' Add n vectors. '''
	return list(map(sum,zip(*args)))

def _prod(inList):
	''' Product of all values in a list. '''
	return reduce(lambda x,y:x*y, inList, 1)

def vecProd(*args):
	''' Multiply n vectors. '''
	return list(map(_prod, zip(*args)))

def threePhasePowFac(ra,rb,rc,ia,ib,ic):
	''' Get power factor for a row of threephase volts and amps. Gridlab-specific. '''
	pfRow = lambda row:math.cos(math.atan((row[0]+row[1]+row[2])/(row[3]+row[4]+row[5])))
	rows = zip(ra,rb,rc,ia,ib,ic)
	return list(map(pfRow, rows))

def roundSeries(ser):
	''' Round everything in a vector to 4 sig figs. '''
	return [roundSig(x, 4) for x in ser]

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

def stringToMag(s):
	if 'd' in s:
		return complex(s.replace('d','j')).real
	elif 'j' in s or 'i' in s:
		return abs(complex(s.replace('i','j')))


def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	f1Name = "load_solar_data.csv"
	with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", f1Name)) as f1:
		load_PV = f1.read()

	f2Name = "breakpoints.csv"
	with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", f2Name)) as f2:
		breakpoints_inputs = f2.read()

	f3Name = "ieee37.dss"
	with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", f3Name)) as f3:
		dssFile = f3.read()

	defaultInputs = {
		"simStartDate": "2019-07-01T00:00:00Z",
		"simLengthUnits": "seconds",
		# "feederName1": "ieee37fixed",
		"feederName1": "Olin Barre GH EOL Solar AVolts CapReg",
		"modelType": modelName,
		"zipCode": "59001",
		"simLength": "25",
		"loadPV": load_PV,
		"breakpoints": breakpoints_inputs,
		"dssFile": dssFile
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

@neoMetaModel_test_setup
def _tests():
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
	# __neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()

''' Powerflow results for one Gridlab instance. '''

import json, os, csv, shutil, math
from os.path import join as pJoin
from functools import reduce
from datetime import timedelta, datetime, tzinfo
from dateutil import parser as dt_parser

# OMF imports
from omf import feeder, weather
from omf.solvers import gridlabd
from omf.models import solarEngineering
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers.opendss import dssConvert
from shutil import copyfile, copytree

# Model metadata:

modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "The cyberInverters model shows the impacts of inverter hacks on a feeder including system voltages, regulator actions, and capacitor responses."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["omdFileName"] = feederName
	inputDict["dssFileName"] = feederName
	zipCode = "59001" #TODO get zip code from the PV and Load input file

	# Output a .dss file, which will be needed for ONM.
	with open(f'{modelDir}/{feederName}.omd', 'r') as omdFile:
		omd = json.load(omdFile)
	tree = omd['tree']
	niceDss = dssConvert.evilGldTreeToDssTree(tree)
	dssConvert.treeToDss(niceDss, f'{modelDir}/{inputDict["dssFileName"]}')
	# dssConvert.treeToDss(niceDss, f'{modelDir}/circuit.dss')

	# Confirm dss file name.
	dssName = [x for x in os.listdir(modelDir) if x.endswith('.dss')][0]
	inputDict["dssFileName"] = dssName

	#Value check for attackVariable
	if inputDict.get("attackVariable", "None") == "None":
		attackAgentType = "None"
	else:
		attackAgentType = inputDict["attackVariable"]

	# Value check for train
	if inputDict.get("trainAgent", "") == "True":
		trainAgentValue = True
	else:
		trainAgentValue = False

	# Value check for hackPercent and conversion to percentHackVal
	if inputDict.get("hackPercent", "None") == "None":
		hackPercentValue = None
	else:
		hackPercentValue = float(inputDict["hackPercent"])

	# create solarPVLengthValue to represent number of steps in simulation - will be manipulated by number of rows in load solar data csv file
	solarPVLengthValue = 0

	#create startStep to represent which step pyCigar should start on. Minimum = 100 steps
	#startStep = 100
	startStep = int(inputDict["simEntryStep"])
	
	#None check for simulation length
	if inputDict.get("simLength", "None") == "None":
		simLengthValue = None
	else:
		simLengthValue = int(inputDict["simLength"])

	#None check for simulation length units
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

	# None check for defenseVariable
	if inputDict.get("defenseVariable", "None") == "None":
		defenseAgentName = None
	else:
		defenseAgentName = inputDict['defenseVariable']
		#Check to make sure that defenseAgent selected by user exists, otherwise return a warning and set defenseAgentName to None
		if os.path.isdir(pJoin(modelDir, "pycigarOutput", defenseAgentName)) == False:
			errorMessage = "ERROR: Defense Agent named " + defenseAgentName + " could not be located."
			defenseAgentName = None
			raise Exception(errorMessage)

	inputDict["climateName"] = weather.zipCodeToClimateName(zipCode)
	shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"),
		pJoin(modelDir, "climate.tmy2"))
	
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
		with open(pJoin(modelDir,"PyCIGAR_inputs","misc_inputs.csv"),"w", newline='') as misc_stream:
			misc_stream.write(inputDict['miscFileContent'])

		#create dss file in folder
		copyfile(f'{modelDir}/{dssName}', f'{modelDir}/PyCIGAR_inputs/circuit.dss')

		#create load_solar_data.csv file in folder
		rowCount = 0
		with open(pJoin(modelDir,"PyCIGAR_inputs","load_solar_data.csv"),"w", newline='') as pv_stream:
			pv_stream.write(inputDict['loadPVFileContent'])
			#Open load and PV input file
		try:
			with open(pJoin(modelDir,"PyCIGAR_inputs","load_solar_data.csv"), newline='') as pv_stream2:
				reader = csv.reader(pv_stream2)
				for row in reader:
					rowCount = rowCount+1
			#Check to see if the simulation length matches the load and solar csv
			# if (rowCount-1)*misc_dict["load file timestep"] != simLengthValue:
			# 	errorMessage = "Load and PV Output File does not match simulation length specified by user"
			# 	raise Exception(errorMessage)
			solarPVLengthValue = rowCount-1
		except:
			#TODO change to an appropriate warning message
			errorMessage = "CSV file is incorrect format."
			raise Exception(errorMessage)

		#create breakpoints.csv file in folder
		with open(pJoin(modelDir,"PyCIGAR_inputs","breakpoints.csv"),"w", newline='') as bp_stream:
			bp_stream.write(inputDict['breakpointsFileContent'])

		#create storage_inputs.txt file in folder
		with open(pJoin(modelDir,"PyCIGAR_inputs","storage_inputs.txt"),"w", newline='') as batt_stream:
			batt_stream.writelines(inputDict['storageFileContent'])

		return solarPVLengthValue

	solarPVLengthValue = convertInputs()

	#create simLengthAdjusted to represent simLength accounting for start step offset
	simLengthAdjusted = 0

	if simLengthValue != None:
		if simLengthValue + startStep > solarPVLengthValue:
			#raise error message that simLengthValue is too large for given Load Solar csv and given timestep (set to 100)
			simLengthAdjusted = solarPVLengthValue - startStep
		else:
			#simLengthValue is equal to the value entered by the user
			simLengthAdjusted = simLengthValue
	else: 
		#simLengthAdjusted accounts for the offset by startStep
		simLengthAdjusted = solarPVLengthValue - startStep
	# #hard-coding simLengthAdjusted for testing purposes 
	# simLengthAdjusted = 750

	# create value to represent the timestep in which the hack starts and adjust it to make sure it is within the bounds of the simulation length
	hackStartVal = int(inputDict["hackStart"])
	hackEndVal = int(inputDict["hackEnd"])
	assert (hackStartVal <= simLengthAdjusted) or (hackEndVal <= simLengthAdjusted) or (hackEndVal-hackStartVal <= simLengthAdjusted), "Please ensure that the hack start and end times fall within the simulation length."

	# attackVars = dict of attack types and their corresponding parameter values
	# to add new attack: attackVars[attackAgentType_name] = {"hackStart": val, "hackEnd": val, "percentHack": val}
	# MAKE SURE to add attackVars entry when adding another Attack Agent option to the html dropdown list and the name must match the value passed back from the form (inputDict["attackVariable"])!
	attackVars = {}
	attackVars["None"] = {"hackStart": hackStartVal, "hackEnd": hackEndVal, "percentHack": 0.0}
	attackVars["VOLTAGE_OSCILLATION"] = {"hackStart": hackStartVal, "hackEnd": hackEndVal, "percentHack": 0.15}
	attackVars["VOLTAGE_IMBALANCE"] = {"hackStart": hackStartVal, "hackEnd": hackEndVal, "percentHack": 0.15} #percentHack must be between 0.1 and 0.4 for pre-trained VOLTAGE_IMBALANCE defense

	#check to make sure attackAgentType is in the attackVars dictionary, otherwise set it to None. This shouldn't ever be a problem since the user selects attackAgentType from a preset HTML dropdown.
	if attackAgentType not in attackVars:
		attackAgentType = "None"

	outData = {}
	# Std Err and Std Out
	outData['stderr'] = "This should be stderr"  #rawOut['stderr']
	outData['stdout'] = "This should be stdout"  #rawOut['stdout']
	
	# Create list of timestamps for simulation steps
	outData['timeStamps'] = []
	start_time = dt_parser.isoparse(simStartDateTimeValue)
	start_time = start_time + timedelta(seconds=startStep)
	for single_datetime in (start_time + timedelta(seconds=n) for n in range(simLengthAdjusted)):
		single_datetime_str = single_datetime.strftime("%Y-%m-%d %H:%M:%S%z") 
		outData['timeStamps'].append(single_datetime_str)

	# Day/Month Aggregation Setup:
	stamps = outData.get('timeStamps',[])
	level = inputDict.get('simLengthUnits','seconds')

	# TODO: Create/populate Climate data without gridlab-d
	outData['climate'] = {}
	outData['allMeterVoltages'] = {}
	outData['allMeterVoltages']['Min'] = [0] * int(simLengthAdjusted)
	outData['allMeterVoltages']['Mean'] = [0] * int(simLengthAdjusted)
	outData['allMeterVoltages']['StdDev'] = [0] * int(simLengthAdjusted)
	outData['allMeterVoltages']['Max'] = [0] * int(simLengthAdjusted)
	# Power Consumption
	outData['Consumption'] = {}
	# Set default value to be 0, avoiding missing value when computing Loads
	outData['Consumption']['Power'] = [0] * int(simLengthAdjusted)
	outData['Consumption']['Losses'] = [0] * int(simLengthAdjusted)
	outData['Consumption']['DG'] = [0] * int(simLengthAdjusted)
	
	outData['swingTimestamps'] = []
	outData['swingTimestamps'] = outData['timeStamps']

	# Aggregate up the timestamps:
	if level=='days':
		outData['timeStamps'] = aggSeries(stamps, stamps, lambda x:x[0][0:10], 'days')
	elif level=='months':
		outData['timeStamps'] = aggSeries(stamps, stamps, lambda x:x[0][0:7], 'months')
		
	#create the pycigarOutput folder to store the output file(s) generated by PyCIGAR
	try:
		os.mkdir(pJoin(modelDir,"pycigarOutput"))
	except FileExistsError:
		print("pycigarOutput folder already exists!")
		pass
	except:
		print("Error occurred creating pycigarOutput folder")

	def runPyCIGAR():
		#import and run pycigar
		import pycigar

		#Set up runType scenarios
		#runType of 2 implies the base scenario - not training a defense agent, nor is there a defense agent entered
		runType = "NO_DEFENSE"
		defenseAgentPath = None

		#set pycigar attack variables
		attackType = attackAgentType
		hackStartVal = attackVars[attackAgentType]["hackStart"]
		hackEndVal = attackVars[attackAgentType]["hackEnd"]
		percentHackVal = attackVars[attackAgentType]["percentHack"]
		if attackAgentType == "None":
			attackType = None

		#change percentHackVal to user input
		elif hackPercentValue != None:
			percentHackVal = hackPercentValue / 100.0

		includeBatt = False
		battPath = None
		if inputDict.get("includeBattery","None") == "True":
			includeBatt = True
			battPath = modelDir + "/PyCIGAR_inputs/storage_inputs.txt"

		# check to see if we are trying to train a defense agent
		if trainAgentValue:	
			#runType of 0 implies the training scenario - runs to train a defense agent and outputs a zip containing defense agent files
			# runType = 0 
			pycigar.main(
				misc_inputs_path = modelDir + "/PyCIGAR_inputs/misc_inputs.csv",
				dss_path = modelDir + "/PyCIGAR_inputs/circuit.dss",
				load_solar_path = modelDir + "/PyCIGAR_inputs/load_solar_data.csv",
				breakpoints_path = modelDir + "/PyCIGAR_inputs/breakpoints.csv",
				test = 'TRAIN',
				type_attack = attackType,
				policy = defenseAgentPath,
				output = modelDir + "/pycigarOutput/",
				start = startStep,
				duration = simLengthAdjusted,
				hack_start = hackStartVal,
				hack_end = hackEndVal,
				percentage_hack = percentHackVal,
				battery_path = battPath,
				battery_status = includeBatt
			)
			# Report out the agent paths.
			# TODO: test, this might break with allInputData file locking.
			defAgentFolders = os.listdir(pJoin(modelDir,"pycigarOutput"))
			inputDict['defenseAgentNames'] = ','.join([x for x in defAgentFolders if x.startswith('policy_')])
			print(inputDict['defenseAgentNames'])
			with open(pJoin(modelDir, "allInputData.json")) as inFileOb:
				json.dump(inputDict, inFileOb, indent=4)

		#check to see if user entered a defense agent file
		elif defenseAgentName != None:
			defenseAgentPath = pJoin(modelDir, "pycigarOutput", defenseAgentName)
			#runType of 1 implies the defense scenario - not training a defense agent, but a defense agent zip was uploaded
			runType = "DEFENSE" 

		# if there is no training selected and no attack variable, run without a defense agent
		pycigar.main(
			misc_inputs_path = modelDir + "/PyCIGAR_inputs/misc_inputs.csv",
			dss_path = modelDir + "/PyCIGAR_inputs/circuit.dss",
			load_solar_path = modelDir + "/PyCIGAR_inputs/load_solar_data.csv",
			breakpoints_path = modelDir + "/PyCIGAR_inputs/breakpoints.csv",
			test = runType,
			type_attack = attackType,
			policy = defenseAgentPath,
			output = modelDir + "/pycigarOutput/",
			start = startStep,
			#start = 3601,
			duration = simLengthAdjusted,
			hack_start = hackStartVal,
			hack_end = hackEndVal,
			percentage_hack = percentHackVal,
			battery_path = battPath,
			battery_status = includeBatt
		)

		#print("!!!!!!!!!!! Got through pyCigar !!!!!!!!!!!!")

	def convertOutputs():
		#set outData[] values to those from modelDir/pycigarOutput/pycigar_output_specs_.json
		#read in the pycigar-outputed json
		with open(pJoin(modelDir,"pycigarOutput","pycigar_output_specs.json"), 'r') as f:
			pycigarJson = json.load(f)
		
		#convert "allMeterVoltages"
		outData["allMeterVoltages"] = pycigarJson["allMeterVoltages"]
		
		#convert "Consumption"."Power"
		# HACK! Units are actually kW. Needs to be fixed in pyCigar.
		outData["Consumption"]["Power"] = pycigarJson["Consumption"]["Power Substation (W)"]

		#convert "Consumption"."Losses"
		outData["Consumption"]["Losses"] = pycigarJson["Consumption"]["Losses Total (W)"]

		#convert "Consumption"."DG"
		outData["Consumption"]["DG"] = [-1.0 * x for x in pycigarJson["Consumption"]["DG Output (W)"]]

		#convert "powerFactor"
		outData["powerFactor"] = pycigarJson["Substation Power Factor (%)"]	

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
		regDict = {}
		for reg_name in regNameList:
			short_reg_name = reg_name.replace("Regulator_","")
			newReg = {}
			newReg["phases"] = list(pycigarJson[reg_name]["RegPhases"])
			tapchanges = {}
			for phase in newReg["phases"]:
				phsup = phase.upper()
				tapchanges[phsup] = pycigarJson[reg_name][short_reg_name + phase.lower()]
			newReg["tapchanges"] = tapchanges
			regDict[reg_name.lower()] = newReg
		outData["Regulator_Outputs"] = regDict

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

		#convert capacitor data
		# TODO: Need to test with a capacitor in the circuit! No idea if this code works.
		capDict = {}
		for cap_name in capNameList:
			short_cap_name = cap_name.replace("Capacitor_","")
			newCap = {}
			newCap["phases"] = list(pycigarJson[cap_name]["CapPhases"])
			for phase in newCap["phases"]:
				newCap["switch" + phase.upper()] = pycigarJson[cap_name]["switch" + phase.lower()]
				newCap["timeseriesdata" + phase.upper()] = []
			capDict[cap_name] = newCap
		outData["Capacitor_Outputs"] = capDict
		
		#convert battery data
		battery_output_dict = {}
		transformatter = {"discharge":0,"standby":1,"charge":2}
		for bname,batt_dict in pycigarJson["Battery Outputs"].items():
			new_batt_dict = {}
			new_batt_dict["SOC"] = [x*100 for x in batt_dict["SOC"]]
			new_batt_dict["Charge_Status"] = [transformatter[x] for x in batt_dict["control_setting"]]
			#new_batt_dict["Power_Out"] = batt_dict["Power Output (W)"]
			#new_batt_dict["Power_In"] = batt_dict["Power Input (W)"]
			# create value for combined power in/output
			batt_power = batt_dict["Power Output (W)"]
			for i, val in enumerate(batt_dict["Power Input (W)"]):
				batt_power[i] = -(batt_power[i] + val)
			new_batt_dict["Power"] = batt_power
			if len(batt_dict["bat_cycle"]) == 0:
				new_batt_dict["Cycles"] = 0.0
			else:
				new_batt_dict["Cycles"] = batt_dict["bat_cycle"][-1]
			# add single battery dict to dict of all the batteries using the battery name as the key 
			battery_output_dict[batt_dict["Name"]] = new_batt_dict
		outData["Battery_Outputs"] = battery_output_dict

		# convert voltage imbalance data
		outData["voltageImbalances"] = {}
		for bus_name in pycigarJson["Voltage Imbalances"].keys():
			outData["voltageImbalances"][bus_name] = []
			outData["voltageImbalances"][bus_name] = pycigarJson["Voltage Imbalances"][bus_name]

		outData["stdout"] = pycigarJson["stdout"]

	runPyCIGAR()
	# Write outputs.
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
	# default model files:
	ckt_dir = "ieee37busdata"
	omd_fn = "ieee37_LBL"
	dss_fn = "ieee37_LBL.dss"
	pv_fn = "load_solar_data.csv"
	bp_fn = "breakpoints.csv"
	misc_fn = "misc_inputs.csv"
	batt_fn = "battery_inputs.txt"

	with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", ckt_dir, pv_fn)) as pv_stream:
		pv_ins = pv_stream.read()
	with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", ckt_dir, bp_fn)) as bp_stream:
		bp_ins = bp_stream.read()
	with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", ckt_dir, misc_fn)) as misc_stream:
		misc_ins = misc_stream.read()
	with open(pJoin(omf.omfDir, "static", "testFiles", "pyCIGAR", ckt_dir, batt_fn)) as batt_stream:
		batt_ins = batt_stream.read()

	defaultInputs = {
		"simStartDate": "2019-07-01T00:00:00Z",
		"simLength": "750",
		"simStepUnits": "seconds",
		"simEntryStep": "100",
		"feederName1": omd_fn,
		"circuitFileName1": dss_fn,
		"loadPVFileName": pv_fn,
		"loadPVFileContent": pv_ins,
		"breakpointsFileName":bp_fn,
		"breakpointsFileContent": bp_ins,
		"miscFileName": misc_fn,
		"miscFileContent": misc_ins,
		"storageFileName": batt_fn,
		"storageFileContent": batt_ins,
		"includeBattery": "False",
		"modelType": modelName,
		"zipCode": "59001",
		"trainAgent": "False",
		"attackVariable": "None",
		"defenseVariable": "None",
		"hackStart": "250",
		"hackEnd": "650",
		"hackPercent": "50",
		"defenseAgentNames": "policy_ieee37_oscillation_sample,policy_ieee37_unbalance_sample"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try: 
		# Grab pre-existing <feedername1>.omd from omf\static\publicfeeders
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
		# Move in default files and empty results folders.
		os.mkdir(pJoin(modelDir,"PyCIGAR_inputs"))
		os.mkdir(pJoin(modelDir,"pycigarOutput"))
		for name in defaultInputs['defenseAgentNames'].split(','):
			shutil.copytree(
				pJoin(__neoMetaModel__._omfDir, "static", "testFiles", "pyCIGAR", name),
				pJoin(modelDir, "pycigarOutput", name)
			)
		# Generate .dss file from .omd so we can open text editor right out of the gate.
		with open(f'{modelDir}/{defaultInputs["feederName1"]}.omd', 'r') as omdFile:
			omd = json.load(omdFile)
		tree = omd['tree']
		niceDss = dssConvert.evilGldTreeToDssTree(tree)
		dssConvert.treeToDss(niceDss, f'{modelDir}/{defaultInputs["circuitFileName1"]}')
	except:
		return False
	return creationCode

@neoMetaModel_test_setup
def _debugging():
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
	_debugging()

''' A model skeleton for future models: Calculates the sum of two integers. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import nrelsam2013
from weather import zipCodeToClimateName

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"_solarInterconnection.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))	
	except Exception, e:
		pass

	# Check whether model exist or not
	try:
		if not os.path.isdir(modelDir):
			os.makedirs(modelDir)
			inputDict["created"] = str(datetime.datetime.now())
		# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
		with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
			json.dump(inputDict, inputFile, indent = 4)			
		startTime = datetime.datetime.now()
		outData = {}

		# Model operations goes here.
		inputOne = inputDict.get("input1", 123)
		inputTwo = inputDict.get("input2", 867)
		output = inputOne + inputTwo
		outData["output"] = output
		# Model operations typically ends here.

		# Stdout/stderr.
		outData["stdout"] = "Success"
		outData["stderr"] = ""

		# Write the output.
		with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
			json.dump(outData, outFile, indent=4)

		# Update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)

	except:
		# If input range wasn't valid delete output, write error to disk.
		cancel(modelDir)				
		thisErr = traceback.format_exc()
		print 'ERROR IN MODEL', modelDir, thisErr
		inputDict['stderr'] = thisErr
		with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)

def _formatScadaData(workDir, scadaPath):
	# Takes scada csv and formats it to play nice with calibrate._processScadaData
	scadaFileName = scadaPath.split('/')[-1]
	with open(scadaPath,"r") as scadaFile:
		scadaReader = csv.DictReader(scadaFile, delimiter='\t')
		allData = [row for row in scadaReader]
	outScadaFile = pJoin(workDir,scadaFileName)
	scadaCSV = open(outScadaFile,'wb')
	wr = csv.writer(scadaCSV, delimiter='\t')
	wr.writerow(["timestamp", "power"])
	for hourlyIncrementor, row in enumerate(allData):
		if hourlyIncrementor%4==0: 
			time =  dt.datetime.strptime(str(row["Date/Time"]),"%m/%d/%y %I:%M %p")
			timestamp = time.strftime("%m/%d/%Y %H:%M:%S")
			powerInKw = float(row["MW"])*(10**3)
			wr.writerow([timestamp, powerInKw])
	return outScadaFile

def getInterval(simLengthUnits):
	if simLengthUnits == 'minutes': lengthInSeconds = 60
	elif simLengthUnits == 'hours': lengthInSeconds = 60*60
	elif simLengthUnits == 'days': lengthInSeconds = 60*60*24
	return lengthInSeconds

def feederMod(tree, simDir, timeZone):
	'''Does the following changes to a feeder:
		set timezone to CST, convert swing to meter, remove diesel generators, remove 0 power residential loads,
		remove schedule files, convert transformers to thermal models, hack regulator_configuration to indvidiaul and set a cap to open.
	'''
	try:
		# Set zone CST.
		if timeZone == 'CST': timeZone = 'CST+6CDT'
		elif timeZone == 'PST': timeZone = 'PST+6PDT'
		else: timeZone = 'PST+6PDT'
		for key in tree:
			if tree[key].get("timezone",""):
				tree[key]["timezone"] = timeZone
	except: print "Couldn't set timezone."
	try:
		# HACK: Make swing a meter to read power.
		for key in tree:
			if tree[key].get('bustype','').lower() == 'swing' and tree[key].get('object','') != 'meter':
				swingName = tree[key].get('name')
				regIndex = key
				tree[key]['object'] = 'meter'
	except: print "Couldn't set swing to meter."
	try:
		# Remove diesel generator.
		dieselKeys = []
		for key in tree:
			if tree[key].get('object','').lower() == 'diesel_dg':
				dieselKeys.append(key)
		for dieselkey in dieselKeys: tree.pop(str(dieselkey),None)
	except: print "Couldn't remove diesel from feeder."
	try:
		# Remove loads with 0 power across all 3 phases.
		loadKeys = []
		for key in tree:
			if tree[key].get('object','').lower() == 'load':
				powerA = float(tree[key].get('constant_power_A','').split("+")[0])
				powerB = float(tree[key].get('constant_power_B','').split("+")[0])
				powerC = float(tree[key].get('constant_power_C','').split("+")[0])
				if powerA == 0 and powerB == 0 and powerC == 0:
					loadKeys.append(key)
		for loadKey in loadKeys: tree.pop(str(loadKey),None)
	except: print "Couldn't remove loads."
	try:
		# Round up nominal_voltages.
		loadKeys = []
		for key in tree:
			if tree[key].get('object','').lower() == 'load':
				if float(tree[key].get('nominal_voltage',''))>7000 and float(tree[key].get('nominal_voltage',''))<7400:
					tree[key]['nominal_voltage'] = 7200.0
				elif float(tree[key].get('nominal_voltage',''))>14200 and float(tree[key].get('nominal_voltage',''))<14400:
					tree[key]['nominal_voltage'] = 14400.0
				elif float(tree[key].get('nominal_voltage',''))>100 and float(tree[key].get('nominal_voltage',''))<140:
					tree[key]['nominal_voltage'] = 120.0
		for loadKey in loadKeys: tree.pop(str(loadKey),None)
	except: print "Couldn't set nominal_voltages."
	try:
		# Remove schedules.
		for key in tree.keys():
			if tree[key].get('omftype','') == '#include':
				if 'schedules' in tree[key].get('argument',''):
					tree.pop(key,None)
	except: print "Couldn't remove schedules."
	try:
		# Hack caps.
		for key in tree:
			if tree[key].get('object','').lower() == 'capacitor' and tree[key].get('name','') == 'CP3035030769001':
				tree[key]['switchA'] = 'OPEN'
				tree[key]['switchB'] = 'OPEN'
	except: print "Couldnt hack cap CP3035030769001"
	# The following causes issues with calibration.
	# try:
	# 	# Hack caps.
	# 	for key in tree:
	# 		if tree[key].get('object','').lower() == 'capacitor':
	# 			tree[key]['switchA'] = 'CLOSED'
	# 			tree[key]['switchB'] = 'CLOSED'
	# 			if tree[key].get('name','') != 'CP3035030769001': tree[key]['switchC'] = 'CLOSED'
	# except: print "Couldnt hack caps"
	try:
		# Set regulator configuration to INDIVIDUAL.
		for key in tree:
			if tree[key].get('object','').lower() == 'regulator_configuration':
				tree[key]['control_level'] = "INDIVIDUAL"
	except: print "Couldn't hack regulator configuration."
	try:
		# Set secondary regulator band_voltage to 7199.
		for key in tree:
			if (tree[key].get('object','').lower() == 'regulator_configuration'):
				if str(tree[key].get('name','')).lower().strip('-config') in ['reg3035238265001', 'reg3028779653001', 'reg3035130559001']:
					tree[key]['band_center'] = '7199.99980927'
					tree[key]['band_width'] = '240.000462134'
				elif str(tree[key].get('name','')).lower().strip('-config') == 'reg3035844020001':
					tree[key]['band_width'] = '480.0008'
	except: print "Couldn't hack regulator band_center/width."
	try:
		maxKey = omf.feeder.getMaxKey(tree) + 1
		overheadLine = {"object": "overhead_line",
			"phases": "ACB",
			"from": "nodeCP3034700827001OH3034700827001",
			"name": "OH3034700863001",
			"to": "nodeOH3034700862001OH3034700863001",
			"length": "295.1642",
			"configuration": "OH3041074510001-LINECONFIG"}
		# Fix islanded nodes: Add a line to each capacitor.
		tree[maxKey] = overheadLine
		#2
		overheadLine = {"object": "overhead_line",
			"phases": "ACB",
			"from": "nodeCP3028904563001OH3028904563001",
			"name": "OH3028904501001",
			"to": "nodeOH3028903581001OH3028904501001",
			"length": "262.4106",
			"configuration": "OH3035236623001-LINECONFIG"}
		tree[maxKey+1] = overheadLine
		#3
		overheadLine = {"object": "overhead_line",
			"phases": "ACB",
			"from": "nodeCP3035761211001OH3035761211001",
			"name": "OH3035760179001",
			"to": "nodeOH3035760127001OH3035760179001",
			"length": "189.5655",
			"configuration": "OH3041074510001-LINECONFIG"}
		tree[maxKey+2] = overheadLine
		#4
		overheadLine = {"object": "overhead_line",
			"phases": "AB",
			"from": "nodeCP3035030769001OH3035030769001",
			"name": "OH3035030730001",
			"to": "nodeOH3029939851001OH3035030730001",
			"length": "215.891",
			"configuration": "OH3029748140001-LINECONFIG"}
		tree[maxKey+3] = overheadLine
	except Exception, e:
		raise e
	try:
		# Convert all load parents to meters to pass violation 3.
		loadParents = []
		for key in tree:
			if (tree[key].get('object','').lower() == 'load'):
				loadParents.append(str(tree[key].get('parent','')).lower())
		# Convert to meters.
		for key in tree:
			if tree[key].get('name','').lower() in loadParents:
				tree[key]['object'] = 'meter'
	except: print "Couldn't add a meter to a load."
	try:
		# Convert transformers to thermal models.
		systemSpecs = {}
		for key in tree:
			if tree[key].get('object','').lower() == 'transformer_configuration' and (float(tree[key].get('secondary_voltage','')) == 240 or float(tree[key].get('secondary_voltage','')) == 120):
				transConfig = tree[key].get('name')
				systemSpecs['primaryVolts'] = float(tree[key]['primary_voltage'])
				systemSpecs['secondaryVolts'] = float(tree[key]['secondary_voltage'])
		for key in tree:
			if tree[key].get('object','').lower() == 'transformer':
				try:
					if tree[key].get('configuration','') == transConfig:
						systemSpecs['transformer'] = (tree[key].get('name',''))
						systemSpecs['tranFromKey'] = (tree[key].get('from',''))
						transTo = tree[key].get('to','')
						systemSpecs['meter'] = transTo
				except: pass
		# Set to thermal equivalents.
		interval = getInterval('hours')
		transformers = []
		for key in tree:
			if tree[key].get('object','').lower() == 'transformer_configuration':
				tree[key]['full_load_loss'] = '0.006'
				tree[key]['no_load_loss'] = '0.003'
				tree[key]['reactance_resistance_ratio'] = '10'
				tree[key]['core_coil_weight'] = '50'
				tree[key]['tank_fittings_weight'] = '60'
				tree[key]['oil_volume'] = '5'
				tree[key]['rated_winding_hot_spot_rise'] = '80'
				tree[key]['rated_top_oil_rise'] = '30'
				tree[key]['rated_winding_time_constant'] = '0.5'
				tree[key]['installed_insulation_life'] = '175200'
				tree[key]['coolant_type'] = 'MINERAL_OIL'
				tree[key]['cooling_type'] = 'OA'
			elif tree[key].get('object','').lower() == 'transformer':
				tree[key]['use_thermal_model'] = "True"
				tree[key]['climate'] = "Climate"
				tree[key]['aging_granularity'] = interval
				tree[key]['percent_loss_of_life'] = "20"
				transformers.append(tree[key].get('name',''))
		systemSpecs["transformers"] = transformers
		with open(pJoin(simDir,"allOutputData.json"),"w") as outFile:
			json.dump(systemSpecs, outFile, indent=4)
		return systemSpecs
	except:
		print "Couldn't get primary or secondary volts, or convert transformers to thermal models."
		return {}


def feederModLoads(simDir):
	'''Adds a groupids attribute to classify loads by nominal voltage values. After calibrate because it disappears if added before. '''
	with open(pJoin(simDir,"calibratedFeeder.omd"), "r") as jsonIn:
		feederJson = json.load(jsonIn)
		tree = feederJson.get("tree", {})
	try:
		groupIDKeys = []
		for key in tree:
			if tree[key].get('object','').lower() == 'load':
				phases = ''.join(sorted(tree[key].get('phases','')))
				nominal_voltage = float(tree[key].get('nominal_voltage',''))
				if (nominal_voltage < 14600 and nominal_voltage > 14200): rating = '14k'
				elif (nominal_voltage < 7400 and nominal_voltage > 7000): rating = '7.2k'
				elif (nominal_voltage < 140 and nominal_voltage > 100): rating = '120'
				if phases!='': tree[key]['groupid'] = 'nominal'+rating+phases
				if tree[key]['groupid'] not in groupIDKeys: groupIDKeys.append(tree[key]['groupid'])
		# print "Load Combinations:",sorted(groupIDKeys)
	except: print "Couldn't set groupid for loads."
	# Write groupid recorder file names.
	with open(pJoin(simDir,"allOutputData.json"), "r") as jsonIn:
		systemSpecs = json.load(jsonIn)
	systemSpecs['loadKeys'] = groupIDKeys
	with open(pJoin(simDir,"allOutputData.json"),"w") as outFile:
		json.dump(systemSpecs, outFile, indent=4)
	# Write the modified tree.
	with open(pJoin(simDir,"calibratedFeeder.omd"),"w") as outJson:
		feederJson["tree"] = tree
		json.dump(feederJson, outJson, indent=4)


def getWeather(airport, simStartDate, simLength, tree):
	''' Downloads 2015 weather for a week in each season:
		Testing for only: 4-13, 7-13, 10-13, and 1-13. Other dates need to be tested.
	'''
	# Find and return weather data for specific sim start date.
	validWeatherDates = {'2015-04-13 05:00:00':'Spring','2015-07-13 05:00:00':'Summer','2015-10-13 05:00:00':'Fall','2015-01-13 05:00:00':'Winter', '2015-08-24 05:00:00' : 'Custom'}
	if str(simStartDate['Date']) not in validWeatherDates.keys():
		print "Pick a starting date from the following:", validWeatherDates.keys()
		return None
	else:
		try: os.mkdir(pJoin(os.getcwd(),'inFiles','weather'))
		except: pass
		weatherFile = "weather"+airport+".csv"
		simWeatherDir = pJoin(os.getcwd(),'inFiles','weather',validWeatherDates[str(simStartDate['Date'])],weatherFile)
		if not os.path.isfile(pJoin(simWeatherDir)):
			for seasonDate in validWeatherDates:
				# Download weather.
				print "Getting weather for:", seasonDate, "..."
				try: os.mkdir(pJoin(os.getcwd(),'inFiles','weather',validWeatherDates[str(seasonDate)]))
				except: pass
				firstDateTime = dt.datetime.strptime(str(seasonDate),"%Y-%m-%d %H:%M:%S")
				try:
					# Inputs.
					weatherFile = "weather"+airport+".csv"
					weatherStart = str(firstDateTime)[:10]
					daysToWeather = simLength/24+1
					weatherEnd = str(firstDateTime+dt.timedelta(days=daysToWeather))[:10]
					# Function.
					assert None==omf.weather.makeClimateCsv(weatherStart, weatherEnd, airport, pJoin(os.getcwd(),'inFiles','weather',validWeatherDates[str(seasonDate)],weatherFile), cleanup=True)
				except:
					print "... WEATHER FAILED TO DOWNLOAD FOR:", firstDateTime
		# Set in tree.
		try:
			# Set in tree.
			maxKey = omf.feeder.getMaxKey(tree) + 1
			for key in tree:
				if tree[key].get('object','').lower() == 'climate':
					tree[key]['tmyfile'] = str("\"weather"+airport+".csv\"")
					tree[key]['reader'] = "weatherReader"
					tree[key].pop('quadratic',None)
			tree[maxKey] = {"object": "csv_reader",
				"name":"\"weatherReader\"",
				"filename": str("\"weather"+airport+".csv\"")
			}
		except: print "Couldn't set new weather in tree."
		return simWeatherDir

def gridlabImport(workDir, feederName, glmString):
	''' Function to convert a glm to json. '''
	newFeeder = dict(**omf.feeder.newFeederWireframe)
	newFeeder["tree"] = omf.feeder.parse(glmString, False)
	newFeeder["layoutVars"]["xScale"] = 0
	newFeeder["layoutVars"]["yScale"] = 0
	newFeeder["attachments"] = {}
	with open(pJoin(workDir,feederName+".omd"), "w") as outFile:
		json.dump(newFeeder, outFile, indent=4)

def setPlayerScada(playerFile,tree, workDir):
	'''Sets the player for scada data in the feeder to a given player file. Interpolates to minute level too.'''
	powerVals, timestamps, newLines = [], [], []
	with open(playerFile, "r") as playerIn:
		allData = playerIn.readlines()
	for data in allData:
		powerVals.append(data.split('CST,')[1].strip())
		timestamps.append(data.split('CST,')[0].strip())
	with open(pJoin(workDir, "gridlabD","subScada.player"),"w") as playFile:
		for i,powerval in enumerate(powerVals):
			if i==len(powerVals)-1:
					line = timestamps[i] + " CST," + str(float(powerval)) + "\n"
					playFile.write(line)
			else:
				for j in range(60):
					power = float(powerval)+j*(float(powerVals[i+1])-float(powerval))/60
					timestamp = dt.datetime.strptime(timestamps[i], "%Y-%m-%d %H:%M:%S")
					timestamp = timestamp+dt.timedelta(minutes=j)
					line = timestamp.strftime("%Y-%m-%d %H:%M:%S") + " CST," + str(power) + "\n"
					playFile.write(line)
					newLines.append(line)
	# Overwrite tree reference to previous player.
	for key in tree:
		if tree[key].get('name','') == 'scadaLoads': tree[key]['file'] = 'subScada.player'
	return newLines

def analysis(simDir, simStartDate, simLength, simLengthUnits, scadaPath, skipSolar=False, solarNode='gen'):
	'''Yields nonagon analysis results, done after calibration.'''
	gridlabdDir = pJoin(simDir,"gridlabD")
	with open(pJoin(simDir,"calibratedFeeder.omd"), "r") as jsonIn:
		feederJson = json.load(jsonIn)
		tree = feederJson.get("tree", {})
	# Get swing recorder key.
	for key in tree:
		if tree[key].get('bustype','').lower() == 'swing':
			swingName = tree[key].get('name','')
	for key in tree:
		if tree[key].get('object','').lower() == 'recorder' and tree[key].get('parent','') == swingName:
			outputRecorderKey = key
	scadaSubPower = calibrate._processScadaData(gridlabdDir, scadaPath, simStartDate, simLengthUnits) #TODO: Check if this still works for minute simulation.
	# parse data for a minute resolution.
	if '08/24' in simStartDate['Date'].strftime("%m/%d"):
		newLines = setPlayerScada(pJoin("inFiles","huwaii_minute.player"),tree, simDir)
		feederJson.pop('attachments')
		feederJson = {'attachments' : {'subScada.player' : newLines}}
		print "Simulation data is 8/24 so converted hourly player to a minute player."
	firstDateTime = dt.datetime.strptime(str(simStartDate["Date"]),"%Y-%m-%d %H:%M:%S")
	timeZone = simStartDate["timeZone"]
	with open(pJoin(simDir,"allOutputData.json"), "r") as jsonIn:
		systemSpecs = json.load(jsonIn)
	# Add solar & inverter (10MW as 1 panel/inverter).
	maxKey = omf.feeder.getMaxKey(tree) + 1
	if skipSolar: print "*Skipping solar."
	else:
		# Attach inverter to solarNode specified, 'gen' if it's not found.
		print "SolarNode=", solarNode
		try:
			for key in tree:
				 # If 'gen' is in name, this is the solar location as set by UCS.
				if tree[key].get('object','').lower() == 'node' and solarNode in tree[key].get('name','').lower():
					inverterParent = str(tree[key].get('name','')).strip()
					tree[key]['object'] = 'meter'
			inverterParent
		except:
			solarNode = 'gen'
			for key in tree:
				 # If 'gen' is in name, this is the solar location as set by UCS.
				if tree[key].get('object','').lower() == 'node' and solarNode in tree[key].get('name','').lower():
					inverterParent = str(tree[key].get('name','')).strip()
					tree[key]['object'] = 'meter'
		# Gridlab new solar + inverter.
		tree[maxKey] = 	{"object": "inverter",
			"name": "DHHL_8_inv",
			"phases": "CS",
			"parent": inverterParent,
			"latitude": "995.577352925",
			"longitude": "724.281583249",
			"generator_mode": "CONSTANT_PF",
			"generator_status": "ONLINE",
			"inverter_type": "PWM",
			"power_factor": "1.0",
			"rated_power": "1424.93 kVA",
			"V_In": "1000.0",
			"I_In": "4110",
			"use_multipoint_efficiency": "FALSE",
			"inverter_manufacturer":"SMA"}
		tree[maxKey+1] = {"object": "solar",
			"name": "DHHL_8_PV",
			"phases": "CS",
			"parent": "DHHL_8_inv",
			"latitude": "995.577352925",
			"longitude": "723.281583249",
			"weather": "Climate",
			"generator_mode": "SUPPLY_DRIVEN",
			"generator_status": "ONLINE",
			"panel_type": "MULTI_CRYSTAL_SILICON",
			"NOCT": "111.2",
			"Tambient": "68",
			"V_Max": "34.1",
			"Voc": "42.3",
			"efficiency": "0.16",
			"area": "86268.75 m^2"}
	# Add recorders.
	def addRecorders(tree, maxKey):
		'''Adds recorders to meter, caps, regs, secondary system, and thermal components,a volt dump, and violation recorder.'''
		# Triplex_meters.
		tripMeterObj = {"object": "collector",
			'group': 'class=triplex_meter',
			'property': 'min(voltage_12.mag),mean(voltage_12.mag),max(voltage_12.mag),std(voltage_12.mag)',
			'file': 'ZvoltageJiggle.csv',
			'limit': '0'}
		tripMeterRecKey = maxKey +1
		tree[tripMeterRecKey] = tripMeterObj
		tree[tripMeterRecKey]["file"] = "ZvoltageJiggle.csv"
		# Residential meters.
		maxKey, i = tripMeterRecKey, 1
		for i,loadKey in enumerate(systemSpecs["loadKeys"]):
			resMeterObj = {"object": "collector",
				'group': 'class=load AND groupid='+str(loadKey),
				'property': 'min(voltage_A.real),mean(voltage_A.real),max(voltage_A.real),min(voltage_B.real),mean(voltage_B.real),max(voltage_B.real),min(voltage_C.real),mean(voltage_C.real),max(voltage_C.real)',
				'file': 'L'+str(loadKey)+'voltageJiggle.csv',
				'limit': '0'}
			tree[maxKey+i+1] = resMeterObj
			tree[maxKey+i+1]["file"] = 'L'+str(loadKey)+'voltageJiggle.csv'
		# Get reg/cap info, write recorders.
		maxKey = omf.feeder.getMaxKey(tree)+1
		regKeys = []
		accum_reg = []
		capKeys = []
		accum_cap = []
		interval = getInterval(simLengthUnits)
		interval = 30
		for key in tree:
			if tree[key].get("object","") == "regulator":
				accum_reg.append(tree[key].get("name","ERROR"))
				regKeys.append(key)
			elif tree[key].get("object","") == "capacitor":
				accum_cap.append(tree[key].get("name","ERROR"))
				capKeys.append(key)
		for i in range(1, len(accum_reg)+1):
			regName = accum_reg[i-1]
			recOb = {"object": "recorder",
				"parent": str(regName),
				"property": "tap_A,tap_B,tap_C,phases",
				"file": str("Regulator_"+regName+".csv"),
				"interval": interval}
			tree[maxKey+i] = recOb
			tree[maxKey+i]["file"] = str("Regulator_"+regName+".csv")
		maxKey = maxKey + i
		for i in range(1, len(accum_cap)+1):
			capName = accum_cap[i-1]
			recOb = {"object": "recorder",
				"parent": str(capName),
				"property": "switchA,switchB,switchC,phases",
				"file": str("Capacitor_"+capName+".csv"),
				"interval": interval}
			tree[maxKey+i] = recOb
			tree[maxKey+i]["file"] = str("Capacitor_"+capName+".csv")
		# Write recorders to secondary system. multirecorder was bugging so uses individual recorders.
		maxKey = maxKey + i
		i = 1
		for key, val in systemSpecs.iteritems():
			if key == 'meter':
				objName = systemSpecs[key]
				recOb = {"object": "recorder",
					"parent": str(objName),
					"property": "voltage_1.real",
					"file": str("SecondarySys_"+objName+".csv"),
					"interval": interval}
				tree[maxKey+i] = recOb
				i+=1
			elif key == 'tranFromKey':
				objName = systemSpecs[key]
				recOb = {"object": "recorder",
					"parent": str(objName),
					"property": "voltage_A.real,voltage_B.real,voltage_C.real,voltage_A.imag,voltage_B.imag,voltage_C.imag",
					"file": str("SecondarySys_"+objName+".csv"),
					"interval": interval}
				tree[maxKey+i] = recOb
				i+=1
		for transformer in systemSpecs["transformers"]:
			recOb = {"object": "recorder",
				"parent": str(transformer),
				"property": "top_oil_hot_spot_temperature,winding_hot_spot_temperature",
				"file": str("Thermal_"+transformer+".csv"),
				"interval": interval}
			tree[maxKey+i] = recOb
			i+=1
		# Violation recorder: the new kid on the block.
		maxKey = maxKey + i
		violrecOb = {"object": "violation_recorder",
			"node_continuous_voltage_limit_lower":"0.95",
			"file": "Violation_Log.csv",
			"secondary_dist_voltage_rise_lower_limit": "-0.042",
			"substation_pf_lower_limit": "0.85",
			"substation_breaker_C_limit": "300",
			"secondary_dist_voltage_rise_upper_limit": "0.025",
			"substation_breaker_B_limit": "300",
			"violation_flag": "ALLVIOLATIONS",
			"node_instantaneous_voltage_limit_upper": "1.1",
			"//violation_delay": "3300",
			"inverter_v_chng_per_interval_lower_bound": "-0.050",
			"virtual_substation": "substation_transformer",
			"substation_breaker_A_limit": "300",
			"xfrmr_thermal_limit_lower": "0",
			"node_continuous_voltage_interval": "300",
			"strict": "false",
			"node_instantaneous_voltage_limit_lower": "0",
			"line_thermal_limit_upper": "1",
			"echo": "false",
			"node_continuous_voltage_limit_upper": "1.05",
			"interval": interval,
			"line_thermal_limit_lower": "0",
			"summary": "Violation_Summary.csv",
			"inverter_v_chng_interval": "60",
			"xfrmr_thermal_limit_upper": "2",
			"inverter_v_chng_per_interval_upper_bound": "0.050"}
		tree[maxKey+1] = violrecOb
		tree[maxKey+1]["file"] = "Violation_Log.csv"
		# Losses.
		omf.feeder.attachRecorders(tree, "OverheadLosses", None, None)
		omf.feeder.attachRecorders(tree, "UndergroundLosses", None, None)
		omf.feeder.attachRecorders(tree, "TriplexLosses", None, None)
		omf.feeder.attachRecorders(tree, "TransformerLosses", None, None)
		# Others.
		omf.feeder.attachRecorders(tree, "Climate", "object", "climate")
		if not skipSolar: omf.feeder.attachRecorders(tree, "Inverter", "object", "inverter")
		omf.feeder.attachRecorders(tree, "CollectorVoltage", None, None)
		# Group swing fun.
		omf.feeder.groupSwingKids(tree)
		# Volt dump used for system voltage map charts.
		stub = {'object':'group_recorder', 'group':'"class=node"', 'property':'voltage_A', 'interval':interval, 'file':'aVoltDump.csv'}
		for phase in ['A','B','C']:
			copyStub = dict(stub)
			copyStub['property'] = 'voltage_' + phase
			copyStub['file'] = phase.lower() + 'VoltDump.csv'
			tree[omf.feeder.getMaxKey(tree) + 1] = copyStub
		# print "Wrote recorders for analysis."
	addRecorders(tree, maxKey+1)
	omf.feeder.adjustTime(tree, simLength+1, simLengthUnits, firstDateTime.strftime("%Y-%m-%d %H:%M:%S"))
	if skipSolar: print "Running final powerflow without solar added."
	tree[outputRecorderKey]["file"] = "caliSubCheck.csv"
	nextOutput = gridlabd.runInFilesystem(tree, keepFiles=True, workDir=gridlabdDir)
	outRealPow2nd = nextOutput["caliSubCheck.csv"]["measured_real_power"]
	outImagPower2nd = nextOutput["caliSubCheck.csv"]["measured_reactive_power"]
	nextAppKw = [(x[0]**2 + x[1]**2)**0.5/1000
		for x in zip(outRealPow2nd, outImagPower2nd)]
	# Parse and plot output, calculate power, DG, more.
	print "Computing losses, DG, Source/Dist Energy, Reg Tag Positions, and Cap Switch Positions."
	cleanOut = {}
	cleanOut['Power'] = [float(element)/1000 for element in outRealPow2nd[1:simLength+1]]
	level = simLengthUnits
	accum_capNew, accum_regNew, secondSys, thermalKeys = [], [], [], []
	mean14400, max14400, min14400 = {}, {}, {}
	mean7200, max7200, min7200 = {}, {}, {}
	mean120, max120, min120 = {}, {}, {}
	for key in nextOutput:
		'''Parses gridlabd output via reading keys to calculate outputs.'''
		# Losses.
		if key in ['OverheadLosses.csv', 'UndergroundLosses.csv', 'TriplexLosses.csv', 'TransformerLosses.csv']:
			realA = nextOutput[key]['sum(power_losses_A.real)']
			realB = nextOutput[key]['sum(power_losses_B.real)']
			realC = nextOutput[key]['sum(power_losses_C.real)']
			imagA = nextOutput[key]['sum(power_losses_A.imag)']
			imagB = nextOutput[key]['sum(power_losses_B.imag)']
			imagC = nextOutput[key]['sum(power_losses_C.imag)']
			oneLoss = hdmAgg(vecSum(realA,realB,realC), avg, level)
			oneLosskW = [float(element)/1000 for element in oneLoss]
			if 'Losses' not in cleanOut:
				cleanOut['Losses'] = oneLosskW
			else:
				cleanOut['Losses'] = vecSum(oneLosskW,cleanOut['Losses'])
		# DG Power.
		elif key.startswith('Inverter_') and key.endswith('.csv'):
			realA = nextOutput[key]['power_A.real']
			realB = nextOutput[key]['power_B.real']
			realC = nextOutput[key]['power_C.real']
			imagA = nextOutput[key]['power_A.imag']
			imagB = nextOutput[key]['power_B.imag']
			imagC = nextOutput[key]['power_C.imag']
			oneDgPower = hdmAgg(vecSum(realA,realB,realC), avg, level)
			oneDgPowerkW = [float(value)/1000 for value in oneDgPower]
			if 'DG' not in cleanOut:
				cleanOut['DG'] = oneDgPowerkW
			else:
				cleanOut['DG'] = vecSum(oneDgPowerkW,cleanOut['DG'])
		# Regulator.
		elif key.startswith('Regulator_') and key.endswith('.csv'):
			regName=""
			regName = key
			newkey=regName.strip(".csv")
			cleanOut[newkey] ={}
			cleanOut[newkey]['RegTapA'] = nextOutput[key].get('tap_A',0)
			cleanOut[newkey]['RegTapB'] = nextOutput[key].get('tap_B',0)
			cleanOut[newkey]['RegTapC'] = nextOutput[key].get('tap_C',0)
			cleanOut[newkey]['RegPhases'] = nextOutput[key].get('phases',0)
			accum_regNew.append(newkey)
		# Capacitor.
		elif key.startswith('Capacitor') and key.endswith('.csv'):
			capName=""
			capName = key
			newkey=capName.strip(".csv")
			cleanOut[newkey] ={}
			switchA = nextOutput[key].get('switchA',0)
			switchB = nextOutput[key].get('switchB',0)
			switchC = nextOutput[key].get('switchC',0)
			# It doesn't record vector of cap switch data, only a single float, so manually set it.
			cleanOut[newkey]['CapSwitchA'] = switchA
			cleanOut[newkey]['CapSwitchB'] = switchB
			cleanOut[newkey]['CapSwitchC'] = switchC
			accum_capNew.append(newkey)
		# Triplex meter voltages.
		elif key.startswith('ZvoltageJiggle') and key.endswith('.csv'):
			cleanOut['triplexVolt'] = {}
			cleanOut['triplexVolt']['High']	= map(divby2,nextOutput['ZvoltageJiggle.csv']['max(voltage_12.mag)'])
			cleanOut['triplexVolt']['Mean']	= map(divby2,nextOutput['ZvoltageJiggle.csv']['mean(voltage_12.mag)'])
			cleanOut['triplexVolt']['Low'] = map(divby2,nextOutput['ZvoltageJiggle.csv']['min(voltage_12.mag)'])
		# Residential loads.
		elif key.startswith('Lnominal') and key.endswith('.csv'):
			loadVoltMeanA  = nextOutput[key]['mean(voltage_A.real)']
			loadVoltMeanB  = nextOutput[key]['mean(voltage_B.real)']
			loadVoltMeanC  = nextOutput[key]['mean(voltage_C.real)']
			loadVoltMaxA = nextOutput[key]['max(voltage_A.real)']
			loadVoltMaxB = nextOutput[key]['max(voltage_B.real)']
			loadVoltMaxC = nextOutput[key]['max(voltage_C.real)']
			loadVoltMinA = nextOutput[key]['min(voltage_A.real)']
			loadVoltMinB = nextOutput[key]['min(voltage_B.real)']
			loadVoltMinC = nextOutput[key]['min(voltage_C.real)']
			# meanVals = map(divby3,vecSum(loadVoltMeanA,loadVoltMeanB,loadVoltMeanC))
			if sum(loadVoltMeanA) > sum(loadVoltMeanB) and sum(loadVoltMeanA) > sum(loadVoltMeanC): meanVals = loadVoltMeanA
			elif sum(loadVoltMeanB) > sum(loadVoltMeanA) and sum(loadVoltMeanB) > sum(loadVoltMeanC): meanVals = loadVoltMeanB
			else: meanVals = loadVoltMeanC
			if sum(loadVoltMaxA) > sum(loadVoltMaxB) and sum(loadVoltMaxA) > sum(loadVoltMaxC): maxVals = loadVoltMaxA
			elif sum(loadVoltMaxB) > sum(loadVoltMaxA) and sum(loadVoltMaxB) > sum(loadVoltMaxC): maxVals = loadVoltMaxB
			else: maxVals = loadVoltMaxC
			if sum(loadVoltMinA) > sum(loadVoltMinB) and sum(loadVoltMinA) > sum(loadVoltMinC): minVals = loadVoltMinA
			elif sum(loadVoltMinB) > sum(loadVoltMinA) and sum(loadVoltMinB) > sum(loadVoltMinC): minVals = loadVoltMinB
			else: minVals = loadVoltMinC
			if '14k' in key: nominal_voltage = 14400
			elif '7.2k' in key: nominal_voltage = 7200
			elif '120' in key: nominal_voltage = 14400
			meanArr=([systemSpecs['secondaryVolts']*(float(value)/nominal_voltage) for value in meanVals if value<(nominal_voltage*1.15) and value>(nominal_voltage*0.85)])
			maxArr=([systemSpecs['secondaryVolts']*(float(value)/nominal_voltage) for value in maxVals if value<(nominal_voltage*1.15) and value>(nominal_voltage*0.85)])
			minArr=([systemSpecs['secondaryVolts']*(float(value)/nominal_voltage) for value in minVals if value<(nominal_voltage*1.15) and value>(nominal_voltage*0.85)])
			# Filter out bad values:
			for item in list(meanArr):
				if item > 120*1.25 or item < 120*0.75: meanArr.remove(item)
			for item in list(maxArr):
				if item > 120*1.25 or item < 120*0.75: maxArr.remove(item)
			for item in list(minArr):
				if item > 120*1.25 or item < 120*0.75: minArr.remove(item)
			# Store in dict.			
			if '14k' in key:
				if meanArr != []: mean14400[key] = meanArr
				if maxArr != []: max14400[key] = maxArr
				if minArr != []: min14400[key] = minArr
			elif '7.2k' in key:
				if meanArr != []: mean7200[key] = meanArr
				if maxArr != []: max7200[key] = maxArr
				if minArr != []: min7200[key] = minArr
			elif '120' in key:
				if meanArr != []: mean120[key] = meanArr
				if maxArr != []: max120[key] = maxArr
				if minArr != []: min120[key] = minArr
		# Secondary system: Convert primary to per unit quantity * 120V.
		elif key.startswith('SecondarySys_') and key.endswith('.csv'):
			if "SecondarySys_"+str(systemSpecs['tranFromKey']) == str(key.strip().strip(".csv")):
				objName = key
				newkey=objName.strip(".csv")
				riseDropValA = nextOutput[key].get('voltage_A.real',0)
				riseDropValB = nextOutput[key].get('voltage_B.real',0)
				riseDropValC = nextOutput[key].get('voltage_C.real',0)
				riseDropValAImag = nextOutput[key].get('voltage_A.imag',0)
				riseDropValBImag = nextOutput[key].get('voltage_B.imag',0)
				riseDropValCImag = nextOutput[key].get('voltage_C.imag',0)
				riseDropVals = vecSum(riseDropValA,riseDropValB,riseDropValC)
				cleanOut[newkey] = {}
				cleanOut[newkey] = [float(systemSpecs['secondaryVolts'])*(float(systemSpecs['primaryVolts'])/float(value)) for value in riseDropVals][1:simLength+1]
				secondSys.append(newkey)
			else:
				objName = key
				newkey=objName.strip(".csv")
				riseDropVals = nextOutput[key].get('voltage_1.real',0)
				cleanOut[newkey] = {}
				cleanOut[newkey] = [value for value in riseDropVals][1:simLength+1]
				secondSys.append(newkey)
		elif key.startswith('Thermal_') and key.endswith('.csv'):
			objName = key
			newkey=objName.strip(".csv")
			temperatures = nextOutput[key].get('top_oil_hot_spot_temperature',0)
			cleanOut[newkey] = {}
			cleanOut[newkey] = temperatures
			thermalKeys.append(newkey)
		elif key.startswith('Climate_') and key.endswith('.csv'):
			cleanOut['climate'] = {}
			cleanOut['climate']["Precipitation (in/h)"] = hdmAgg(nextOutput[key].get('rainfall'), sum, level)
			cleanOut['climate']["Direct Insolation (W/m^2)"] = hdmAgg(nextOutput[key].get('solar_direct'), sum, level)
			cleanOut['climate']['Temperature (F)'] = hdmAgg(nextOutput[key].get('temperature'), max, level)
	# Process loads further.
	cleanOut['loadVolt'] = {'nominal14400':{},'nominal7200':{},'nominal120':{}}
	# 14400 nominal voltage loads.
	meanSS14400 = [mean14400[key] for key in mean14400.keys()]
	minSS14400 = [min14400[key] for key in min14400.keys()]
	maxSS14400 = [max14400[key] for key in max14400.keys()]
	cleanOut['loadVolt']['nominal14400'] = {'Mean':[x/len(mean14400) for x in np.sum(meanSS14400,axis=0)],'Low':[x/len(min14400) for x in np.sum(minSS14400,axis=0)],'High': [x/len(max14400) for x in np.sum(maxSS14400,axis=0)]}
	# 7200 nominal_voltage loads.
	meanSS7200 = [mean7200[key] for key in mean7200.keys()]
	minSS7200 = [min7200[key] for key in min7200.keys()]
	maxSS7200 = [max7200[key] for key in max7200.keys()]
	cleanOut['loadVolt']['nominal7200'] = {'Mean':[x/len(mean7200) for x in np.sum(meanSS7200,axis=0)],'Low':[x/len(min7200) for x in np.sum(minSS7200,axis=0)],'High':[x/len(max7200) for x in np.sum(maxSS7200,axis=0)]}
	# 120 nominal voltage loads.
	if len(min120) == 0: min120 = mean120
	if len(mean120) == 0: 
		min120, mean120 = max120, max120
	meanSS120 = [mean120[key] for key in mean120.keys()]
	minSS120 = [min120[key] for key in min120.keys()]
	maxSS120 = [max120[key] for key in max120.keys()]
	print "minSS120", len(minSS120), "meanSS120", len(meanSS120), "maxSS120", len(maxSS120)
	print "minSS7200", len(minSS7200), "meanSS7200", len(meanSS7200), "maxSS7200", len(maxSS7200)
	print "minSS14400", len(minSS14400), "meanSS14400", len(meanSS14400), "maxSS14400", len(maxSS14400)		
	cleanOut['loadVolt']['nominal120'] = {'Mean':[x/len(mean120) for x in np.sum(meanSS120,axis=0)],'Low':[x/len(min120) for x in np.sum(minSS120,axis=0)],'High':[x/len(max120) for x in np.sum(maxSS120,axis=0)]}
	# Plot our outputs.
	def plotAll(plotDir):
		# Substation powerflow and scada curve.
		secondDateTime = firstDateTime+dt.timedelta(hours=1)
		plotThings.plotLine(plotDir, cleanOut['Power'], {"Title":"Substation Powerflow", "fileName":"subPowerFlow","labels":"Substation", "timeZone":timeZone}, secondDateTime, simLengthUnits)
		plotThings.plotLine(plotDir, scadaSubPower[1:simLength+1], {"Title":"Scada Substation Curve", "fileName":"scadaSub","labels":"Scada Readings", "timeZone":timeZone}, secondDateTime, simLengthUnits)
		# Power consumption across transmission system.
		if skipSolar: cleanOut['DG'] = [0 for i in range(simLength+1)]
		transPowVectors = [cleanOut['Power'], cleanOut['DG'][1:simLength+1], cleanOut['Losses'][1:simLength+1]]
		labels = ["Substation Powerflow", "DG", "Technical Losses"]
		colors = ['blue','green','red']
		chartData = {"Title":"Power Consumption from Transmission System", "fileName":"powerTransSystem", "colors":colors,"labels":labels, "timeZone":timeZone}
		plotThings.plotLine(plotDir, transPowVectors, chartData, secondDateTime, simLengthUnits)
		# Just losses and DG.
		plotThings.plotLine(plotDir, cleanOut['Losses'], {"Title":"Technical Losses", "fileName":"techLosses","labels":"Substation", "timeZone":timeZone}, secondDateTime, simLengthUnits)
		plotThings.plotLine(plotDir, cleanOut['DG'], {"Title":"DG", "fileName":"distGen","labels":"Solar", "timeZone":timeZone}, secondDateTime, simLengthUnits)
		# Meter and load voltages.
		loadVolts14400 = [cleanOut['loadVolt']['nominal14400']['High'][2:simLength+1],cleanOut['loadVolt']['nominal14400']['Mean'][2:simLength+1],cleanOut['loadVolt']['nominal14400']['Low'][2:simLength+1]]
		loadVolts7200 = [cleanOut['loadVolt']['nominal7200']['High'][2:simLength+1],cleanOut['loadVolt']['nominal7200']['Mean'][2:simLength+1],cleanOut['loadVolt']['nominal7200']['Low'][2:simLength+1]]
		loadVolts120 = [cleanOut['loadVolt']['nominal120']['High'][2:simLength+1],cleanOut['loadVolt']['nominal120']['Mean'][2:simLength+1],cleanOut['loadVolt']['nominal120']['Low'][2:simLength+1]]
		triplexMetVolts = [cleanOut['triplexVolt']['High'][2:simLength+1],cleanOut['triplexVolt']['Mean'][2:simLength+1],cleanOut['triplexVolt']['Low'][2:simLength+1]]
		labels = ["14400 Load Max","14400 Load Mean","14400 Load Min","7200 Load Max","7200 Load Mean","7200 Load Min","120 Load Max", "120 Load Mean", "120 Load Min", "Triplex Meter Max","Triplex Meter Mean","Triplex Meter Min"]
		colors = ['lightblue','blue','darkblue','lightgreen','green','darkgreen','lightgray','gray','darkgray','lightpink','hotpink','deeppink']
		chartData = {"Title":"Meter Voltages", "fileName":"meterVoltages", "yAxis":"Meter Voltage (V)","colors":colors,"labels":labels, "timeZone":timeZone, "boundaries":[float(systemSpecs['secondaryVolts'])*1.05, float(systemSpecs['secondaryVolts'])*0.95]}
		plotThings.plotLine(plotDir, loadVolts14400+loadVolts7200+loadVolts120+triplexMetVolts, chartData, secondDateTime, simLengthUnits)
		# 14400
		chartData = {"Title":"Load Voltages", 
			"fileName":"loadVoltages14400", 
			"yAxis":"Load Voltage (V)",
			"colors":['lightblue','blue','darkblue'],
			"labels":["14400 Load Max","14400 Load Mean","14400 Load Min"], 
			"timeZone":timeZone, 
			"boundaries":[float(systemSpecs['secondaryVolts'])*1.05, float(systemSpecs['secondaryVolts'])*0.95]}
		plotThings.plotLine(plotDir, loadVolts14400, chartData, secondDateTime, simLengthUnits)
		# 7200
		chartData = {"Title":"Load Voltages", 
			"fileName":"loadVoltages7200", 
			"yAxis":"Load Voltage (V)",
			"colors":['lightblue','blue','darkblue'],
			"labels":["7200 Load Max","7200 Load Mean","7200 Load Min"], 
			"timeZone":timeZone, 
			"boundaries":[float(systemSpecs['secondaryVolts'])*1.05, float(systemSpecs['secondaryVolts'])*0.95]}
		plotThings.plotLine(plotDir, loadVolts7200, chartData, secondDateTime, simLengthUnits)
		# 120
		chartData = {"Title":"Load Voltages", 
			"fileName":"loadVoltages120", 
			"yAxis":"Load Voltage (V)",
			"colors":['lightblue','blue','darkblue'],
			"labels":["120 Load Max","120 Load Mean","120 Load Min"], 
			"timeZone":timeZone, 
			"boundaries":[float(systemSpecs['secondaryVolts'])*1.05, float(systemSpecs['secondaryVolts'])*0.95]}
		plotThings.plotLine(plotDir, loadVolts120, chartData, secondDateTime, simLengthUnits)		
		# Voltage drops/rises.
		secSystemVolts = [float(x)-float(y) for x,y in zip(cleanOut[secondSys[0]],cleanOut[secondSys[1]])][1:]
		labels = "Triplex Meter"
		chartData = {"Title":"Secondary System Rise/Drops (V)", "fileName":"secondRiseDrop", "yAxis":"Voltage Change (V)","labels":labels, "timeZone":timeZone, "boundaries":[-3, 5]}
		plotThings.plotLine(plotDir, secSystemVolts, chartData, secondDateTime, simLengthUnits)
		# Reg/cap positions.
		for i in range(0, len(accum_regNew)):
			labels = ["Tap_Pos_A", "Tap_Pos_B", "Tap_Pos_C"]
			colors = ["green","red","yellow"]
			regNameKey, regName = accum_regNew[i], str(accum_regNew[i]).split("Regulator_")[1]
			tapA = [float(element) for element in cleanOut[regNameKey]['RegTapA']][1:simLength+1]
			tapB = [float(element) for element in cleanOut[regNameKey]['RegTapB']][1:simLength+1]
			tapC = [float(element) for element in cleanOut[regNameKey]['RegTapC']][1:simLength+1]
			chartData = {"Title": "Regulator Tap Positions for "+regName, "yAxis":"Tap Position", "fileName":"RegTapPos_"+regName,"colors":colors,"labels":labels, "timeZone":timeZone}
			plotThings.plotLine(plotDir, [tapA, tapB, tapC], chartData, secondDateTime, simLengthUnits)
		for i in range(0, len(accum_capNew)):
			labels = ["Switch_Pos_A", "Switch_Pos_B", "Switch_Pos_C"]
			colors = ["green","red","yellow"]
			capNameKey, capName = accum_capNew[i], str(accum_capNew[i]).split("Capacitor_")[1]
			posA = [float(element) for element in cleanOut[capNameKey]['CapSwitchA']][1:simLength+1]
			posB = [float(element) for element in cleanOut[capNameKey]['CapSwitchB']][1:simLength+1]
			posC = [float(element) for element in cleanOut[capNameKey]['CapSwitchC']][1:simLength+1]
			chartData = {"Title": "Capacitor Tap Positions for "+capName, "yAxis":"Switch Position", "fileName":"CapSwitchPos_"+capName,"colors":colors,"labels":labels, "timeZone":timeZone}
			plotThings.plotLine(plotDir, [posA, posB, posC], chartData, secondDateTime, simLengthUnits)
		# Plot thermal limits.
		for i in range(0, len(thermalKeys)):
			compKey, compName = thermalKeys[i], str(thermalKeys[i]).split("Thermal_")[1]
			compValues = [float(element) for element in cleanOut[compKey]][1:simLength+1]
			chartData = {"Title": "Temperatures for "+compName, "yAxis":"Temperature ("+u'\N{DEGREE SIGN}'+"C)", "fileName":"Thermal_"+compName,"labels":"Transformer", "timeZone":timeZone}
			plotThings.plotLine(plotDir, compValues, chartData, secondDateTime, simLengthUnits)
		# Plot weather.
		weatherVectors = [cleanOut['climate']["Direct Insolation (W/m^2)"][1:simLength+1], cleanOut['climate']["Temperature (F)"][1:simLength+1], cleanOut['climate']["Precipitation (in/h)"][1:simLength+1]]
		labels = ["Insolation", "Temperature", "Rainfall"]
		colors = ['lightgray','red', 'lightblue']
		chartData = {"Title":"Weather",  "yAxis":"Climate Units", "fileName":"weather", "colors":colors,"labels":labels, "timeZone":timeZone}
		plotThings.plotLine(plotDir, weatherVectors, chartData, firstDateTime+dt.timedelta(hours=1), simLengthUnits)
		# Format and plot stacked bar.
		tPower = np.sum(cleanOut['Power'])
		tLosses = np.sum(cleanOut['Losses'])
		tDG = np.sum(cleanOut['DG'])
		tLoads = tPower + tDG - tLosses
		print "Energy bar chart: losses/loads difference: ", (tLoads-tLosses), "(%)", (tLoads/tLoads)
		dgExported = []
		fromGrid = []
		for i in range(0,len(cleanOut['Power'])):
			curVal = cleanOut['Power'][i]
			if curVal < 0: dgExported.append(curVal)
			else: fromGrid.append(curVal)
		tDGExported = np.sum(dgExported)
		print 'tdgexported:', tDGExported
		print "-tdgExported", -1.0*tDGExported
		tFromGrid = np.sum(fromGrid)
		tDGDirect = tLoads + tLosses - tFromGrid
		botBars = [tDGDirect, tFromGrid, -1.0*tDGExported]
		topBars = [tLoads, tLosses]
		plotThings.plotBar(plotDir, botBars, topBars, {"Title":"Energy Balance", "yLabelTop":"Consumption","yLabelBot":"Generation","fileName":"energyBal"})
	plotAll(simDir)
	# Rewrite violations csv file for Results Page.html iFrame.
	def parseViolationsFriendly(violationsFile):
		'''Parses Violation_Log.csv from gridlabD. Reads a row at a time, keeping: times, violation, observation, limits, abd objects.'''
		r = re.compile('.*-.*-.*')
		try:
			csvFile = violationsFile
			with open(csvFile, 'rb') as f:
				reader = csv.reader(f)
				violationsLog = list(reader)
			violationData = {}
			for row in violationsLog:
				if r.match(str(row[0])) is not None:
					if violationData.get(row[0],'') == '':
						violationData[row[0].strip()] = {row[5].strip():{"Violation":row[1].strip(),"Observation":row[2].strip(),"LimitH":row[3].strip(),"LimitL":row[4].strip(),"Message":row[8].strip()}}
					else:
						violationData[row[0].strip()][row[5].strip()] = {"Violation":row[1].strip(),"Observation":row[2].strip(),"LimitH":row[3].strip(),"LimitL":row[4].strip(),"Message":row[8].strip()}
		except:
			print "VIOLATION PARSER CRASHED"
			return {}
		return violationData
	violationsFile = pJoin(gridlabdDir, "Violation_Log.csv")
	nextOutput['ViolationsData'] = parseViolationsFriendly(violationsFile)
	if len(nextOutput['ViolationsData']) == 0: print "*No violations found."
	# Formatting for the HTML page.
	with open(violationsFile, 'rb') as f:
		reader = csv.reader(f)
		violationsLog = list(reader)
	violationCSV = open(pJoin(simDir,'violationLogClean.csv'),'wb')
	wr = csv.writer(violationCSV, dialect='excel')
	for i in range(len(violationsLog)):
		if i>5: wr.writerow(violationsLog[i])
	# Write the output.
	with open(pJoin(simDir,"nonagonAnalysisFeeder.omd"),"w") as outJson:
		feederJson["values"] = {"ViolationsData" : nextOutput["ViolationsData"]}
		feederJson["values"]["voltDumps"] = {'aVoltDump.csv':nextOutput['aVoltDump.csv'],'bVoltDump.csv':nextOutput['bVoltDump.csv'],'cVoltDump.csv':nextOutput['cVoltDump.csv']}
		feederJson["tree"] = tree
		json.dump(feederJson, outJson, indent=4)
	return pJoin(simDir,"nonagonAnalysisFeeder.omd")
	# return tree, nextOutput


# Run Model
def _tests(stdInFile, seqInFile, clearSimDir=False, convert=False, doCalibrate=False, doAnalysis=True, skipSolar=False, voltageChart=False):
	'''Runs the UCS Model in this flow: Convert from std/seq to glm. Then glm to json. Then clean up json. Then calibrate and run analysis.'''
	# Inputs. 
	# Note: Sim date must start on 4/13, 7/13, 10/13, or 1/13 at specific times to use wunderground weather. 8/24 is only for minute res.
	# Weekly res.
	simDate = dt.datetime.strptime("4/13/2015 05:00:00", "%m/%d/%Y %H:%M:%S")
	caliberror, trim = (0.05,5), 3
	simStartDate = {"Date":simDate,"timeZone":"CST"}
	simLength = 24*7
	simLengthUnits = 'hours'
	#  Minute res.
	# simDate = dt.datetime.strptime("8/24/2015 05:00:00", "%m/%d/%Y %H:%M:%S")
	# simStartDate = {"Date":simDate,"timeZone":"CST"}
	# simLength = 60*12
	# simLengthUnits = 'minutes'		
	solarLoc = 'gen'
	solver = 'NR'
	# Set directories.
	workDir = pJoin(os.getcwd(), "outFiles")
	simDir = pJoin(workDir, "SpringWeek")
	try: os.mkdir(pJoin(workDir))
	except: pass
	try:
		if clearSimDir: shutil.rmtree(pJoin(simDir))
	except: pass
	try: os.mkdir(pJoin(simDir))
	except: pass
	try: os.mkdir(pJoin(simDir, "gridlabD"))
	except: pass
	print "Running simulation at: %s" %(simDir.split("/")[-2]+"/"+simDir.split("/")[-1])
	print "For %s %s on date: %s\n"%(str(simLength),simLengthUnits,simStartDate['Date'])
	def circuitConversion():
		# Circuit Conversion.
		if convert or not os.path.isfile(pJoin(workDir,'OMF_Norfork1.glm')):
			try:
				# Convert .std and .seq to a .glm if needed.
				print "Converting .STD/SEQ to .GLM:"
				def runMilConvert(stdInFile, seqInFile):
					import matplotlib
					from matplotlib import pyplot as plt
					with open(pJoin(os.getcwd(),"inFiles", stdInFile),'r') as inFile:
						stdString = inFile.read()
					with open(pJoin(os.getcwd(),"inFiles", seqInFile),'r') as inFile2:
						seqString = inFile2.read()
					myFeed, xScale, yScale = omf.milToGridlab.convert(stdString,seqString)
					with open(pJoin(workDir,stdInFile.replace('.std','.glm')),'w') as outFile:
						outFile.write(omf.feeder.sortedWrite(myFeed))
					myGraph = omf.feeder.treeToNxGraph(myFeed)
					omf.feeder.latLonNxGraph(myGraph, neatoLayout=False)
					plt.savefig(pJoin(workDir,stdInFile.replace('.std','.png')))
				runMilConvert(stdInFile, seqInFile)
				print "... Done.\n"
			except: print "...Error in conversion.\n"
		else: print ".STD/SEQ exist... Skipping conversion."
		if convert or not os.path.isfile(pJoin(workDir,'OMF_Norfork1.omd')):
			try:
				# Convert .glm to .json.
				print "Converting GLM to JSON .OMD:"
				with open(pJoin(workDir, 'OMF_Norfork1.glm'),'r') as glmFile:
					outGlm = glmFile.read()
				gridlabImport(workDir, 'OMF_Norfork1', outGlm)
				print "... Done.\n"
			except: print "... GLM to JSON conversion failed.\n"
		else: print ".JSON .omd exists... skipping conversion."
	circuitConversion()
	def calibration():
		# Calibration.
		if doCalibrate or not os.path.isfile(pJoin(simDir, 'calibratedFeeder.omd')):
			with open(pJoin(workDir,"OMF_Norfork1.omd"), "r") as jsonIn:
				feederJson = json.load(jsonIn)
				tree = feederJson.get("tree", {})
			# Get weather & cleanup feeder.
			simWeatherDir = getWeather("SEP", simStartDate, simLength, tree)
			if os.path.isfile(simWeatherDir): shutil.copy(simWeatherDir, pJoin(simDir,"gridlabD"))
			else:
				print "=========\n ENCOUNTERED UNKNOWN ERROR WITH WEATHER... \nLoaded the following .TMY2 instead: %s"%(pJoin(os.getcwd(),"inFiles","climate.tmy2"))
				shutil.copy(pJoin(os.getcwd(),"inFiles","climate.tmy2"), pJoin(simDir,"gridlabD"))
			feederMod(tree, simDir, "CST") # Clean up feeder.
			cleanFeederPath = pJoin(workDir,"OMF_Norfork1_Cleaned.omd")
			with open(cleanFeederPath,"w") as outJson:
				feederJson["tree"] = tree
				json.dump(feederJson, outJson, indent=4)
			# Calibrate.
			print "\nCalibrating feeder with %s solver..."%(solver)
			scadaPath = _formatScadaData(workDir, pJoin(os.getcwd(),"inFiles","NorforkScada.csv"))
			startTime = time.time()
			calibrate.omfCalibrate(simDir, cleanFeederPath, scadaPath, simStartDate, simLength, simLengthUnits, solver, caliberror, trim)
			calibTime = time.time() - startTime
		else: calibTime = 0.0
		print ('...Calibration Done! Took {0} minutes.\n'.format(calibTime/60))
		return calibTime
	calibTime  = calibration()
	def nonagon():
		# The Nonagon-Analysis.
		if doAnalysis or not os.path.isfile(pJoin(simDir,'nonagonAnalysisFeeder.omd')):
			print "\nBeginning analysis..."
			feederModLoads(simDir) # Clean up feeder.
			startTime2 = time.time()
			scadaPath = pJoin(workDir, "NorforkScada.csv")
			# solarLoc = 'node3035169780001OH3035169780001' # A loc at the end of the feeder.
			analysis(simDir, simStartDate, simLength, simLengthUnits, scadaPath, skipSolar)
			nonagonTime = time.time() - startTime2
		else: nonagonTime = 0.0
		print ('...Analysis done! Took {0} minutes.\n'.format(nonagonTime/60))
		return nonagonTime
	nonagonTime = nonagon()
	def voltagechart():
		# Voltage chart creation.
		if voltageChart or not os.path.isfile(pJoin(simDir,'voltChart.mp4')):
			print "\nStarting .mp4 voltage line chart generation..."
			startTime = time.time()
			genTime = plotThings.generateVoltChart(simDir, simLength)
			voltTime = time.time()-startTime
		else:
			voltTime = 0.0
		print "... .mp4 generated! It took {0} seconds.\n\n".format(voltTime)
		return voltTime
	voltTime = voltagechart()
	print "ALL GOOD FOR A TOTAL OF {0} MINUTES".format((calibTime+nonagonTime+voltTime)/60)


if __name__ == '__main__':
	stdInFile = 'OMF_Norfork1.std'
	seqInFile = 'OMF_Norfork1.seq'	
	_tests(stdInFile, seqInFile)			
''' Graph the voltage drop on a feeder. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
from random import randint, uniform
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
plt.switch_backend('Agg')
plt.style.use('seaborn')
import csv

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *

from omf.solvers.REopt import run as runREopt

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Injects faults in to circuits and measures fault currents, voltages, and protective device response."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	# feederName = inputDict["feederName1"]
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	# Create voltage drop plot.
	# print "*DEBUG: feederName:", feederName
	omd = json.load(open(pJoin(modelDir,feederName + '.omd')))
	if inputDict.get("layoutAlgorithm", "geospatial") == "geospatial":
		neato = False
	else:
		neato = True
	# None check for batterySize
	if inputDict.get("batterySize", "None") == "None":
		batterySizeValue = None
	else:
		batterySizeValue = float(inputDict["batterySize"])
	# None check for chargeRate
	if inputDict.get("chargeRate", "None") == "None":
		chargeRateValue = None
	else:
		chargeRateValue = float(inputDict["chargeRate"])
	# None check for efficiency
	if inputDict.get("efficiency", "None") == "None":
		efficiencyValue = None
	else:
		efficiencyValue = float(inputDict["efficiency"])
	# None check for gasEfficiency
	if inputDict.get("gasEfficiency", "None") == "None":
		gasEfficiencyValue = None
	else:
		gasEfficiencyValue = float(inputDict["gasEfficiency"])
	# None check for numVehicles
	if inputDict.get("numVehicles", "None") == "None":
		numVehiclesValue = None
	else:
		numVehiclesValue = int(inputDict["numVehicles"])
	# None check for energyCost
	if inputDict.get("energyCost", "None") == "None":
		energyCostValue = None
	else:
		energyCostValue = float(inputDict["energyCost"])
	# None check for demandCost
	if inputDict.get("demandCost", "None") == "None":
		demandCostValue = None
	else:
		demandCostValue = float(inputDict["demandCost"])
	# None check for startHour
	if inputDict.get("startHour", "None") == "None":
		startHourValue = None
	else:
		startHourValue = int(inputDict["startHour"])
	# None check for endHour
	if inputDict.get("endHour", "None") == "None":
		endHourValue = None
	else:
		endHourValue = int(inputDict["endHour"])
	# None check for chargeLimit
	if inputDict.get("chargeLimit", "None") == "None":
		chargeLimitValue = None
	else:
		chargeLimitValue = float(inputDict["chargeLimit"])
	# None check for minCharge
	if inputDict.get("minCharge", "None") == "None":
		minChargeValue = None
	else:
		minChargeValue = float(inputDict["minCharge"])/100
	# None check for maxCharge
	if inputDict.get("maxCharge", "None") == "None":
		maxChargeValue = None
	else:
		maxChargeValue = float(inputDict["maxCharge"])/100
	# None check for gasCost
	if inputDict.get("gasCost", "None") == "None":
		gasCostValue = None
	else:
		gasCostValue = float(inputDict["gasCost"])
	# None check for workload
	if inputDict.get("workload", "None") == "None":
		workloadValue = None
	else:
		workloadValue = float(inputDict["workload"])
	# None check for loadName
	if inputDict.get("loadName", "None") == "None":
		loadNameValue = None
	else:
		loadNameValue = inputDict["loadName"]
	# None check for latitude
	if inputDict.get("latitude", "None") == "None":
		latitudeValue = None
	else:
		latitudeValue = float(inputDict["latitude"])
	# None check for longitude
	if inputDict.get("longitude", "None") == "None":
		longitudeValue = None
	else:
		longitudeValue = float(inputDict["longitude"])
	# None check for year
	if inputDict.get("year", "None") == "None":
		yearValue = None
	else:
		yearValue = int(inputDict["year"])

	# Setting up the loadShape file.
	with open(pJoin(modelDir,"loadShape.csv"),"w") as loadShapeFile:
		loadShapeFile.write(inputDict['loadShape'])
	try:
		loadShapeList = []
		with open(pJoin(modelDir,"loadShape.csv")) as inFile:
			reader = csv.reader(inFile)
			for row in reader:
				loadShapeList.append(row) 
			if len(loadShapeList)!=8760: raise Exception
	except:
		errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-demandResponse#walkthrough'>OMF Wiki demandResponse</a>"
		raise Exception(errorMessage)

	loadShapeValue = [float(x[0]) for x in loadShapeList]

	# print loadShapeValue
	
	#calculate and display EV Charging Demand image, carpet plot image of 8760 load shapes
	maxLoadValue, demandImg, carpetPlotImg, hourlyConValue, combinedLoadShapeValue = plotEVShape(
		numVehicles = numVehiclesValue,
		chargeRate = chargeRateValue, 
		batterySize = batterySizeValue, 
		startHour = startHourValue, 
		endHour = endHourValue, 
		chargeLimit = chargeLimitValue, 
		minCharge = minChargeValue, 
		maxCharge = maxChargeValue, 
		loadShape = loadShapeValue)
	demandImg.savefig(pJoin(modelDir, "evChargingDemand.png"))
	with open(pJoin(modelDir, "evChargingDemand.png"),"rb") as evFile:
		outData["evChargingDemand"] = evFile.read().encode("base64")
	carpetPlotImg.savefig(pJoin(modelDir, "carpetPlot.png"))
	with open(pJoin(modelDir, "carpetPlot.png"),"rb") as cpFile:
		outData["carpetPlot"] = cpFile.read().encode("base64")
	
	#run and display fuel cost calculation
	fuelCostHtml = fuelCostCalc(
		numVehicles = numVehiclesValue,
		batterySize = batterySizeValue,
		efficiency = efficiencyValue,
		energyCost = energyCostValue,
		gasEfficiency = gasEfficiencyValue,
		gasCost = gasCostValue,
		workload = workloadValue)
	with open(pJoin(modelDir, "fuelCostCalc.html"), "w") as fuelFile:
		fuelFile.write(fuelCostHtml)
	outData["fuelCostCalcHtml"] = fuelCostHtml

	#run and display voltage drop image and protective device status table
	voltPlotChart, protDevTable = drawPlotFault(
		pJoin(modelDir,feederName + ".omd"),
		neatoLayout = neato,
		edgeCol = "PercentOfRating",
		nodeCol = "perUnitVoltage",
		nodeLabs = None,
		edgeLabs = None,
		customColormap = False,
		scaleMin = .9,
		scaleMax = 1.1,
		faultLoc = None,
		faultType = None,
		rezSqIn = 225,
		simTime = "2000-01-01 0:00:00",
		workDir = modelDir)
	voltPlotChart.savefig(pJoin(modelDir, "output.png"))
	with open(pJoin(modelDir, "statusTable.html"), "w") as tabFile:
		tabFile.write(protDevTable)
	outData['protDevTableHtml'] = protDevTable
	with open(pJoin(modelDir, "output.png"),"rb") as inFile:
		outData["voltageDrop"] = inFile.read().encode("base64")

	def voltplot_protdev(max_value=None, load_name=None):
		warnings.filterwarnings("ignore")
		omd = json.load(open(pJoin(modelDir,feederName + ".omd")))
		tree = omd.get('tree', {})
		attachments = omd.get('attachments',[])

		#check to see that maximum load value is passed in
		maxValue = max_value
		loadName = load_name
		# maxValue = maxLoadValue
		# loadName = loadNameValue
		if maxValue != None:
			maxValue = float(maxValue)
			maxValueWatts = maxValue * 1000
			# print "maxValue = " + str(maxValue)
			# print "maxValueWatts = " + str(maxValueWatts)
			#check to see that loadName is specified
			if loadName != None:
				# Map to speed up name lookups.
				nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}
				#check if the specified load name is in the tree
				if loadName in nameToIndex:
					key = nameToIndex[loadName]
					obtype = tree[key].get("object","")
					if obtype in ['triplex_node', 'triplex_load']:
						tree[key]['power_12_real'] = maxValueWatts
						#tree[key]['power_12'] = maxValueWatts
					elif obtype in ['load', 'pqload']:
						#tree[key]['constant_power_A_real'] = maxValueWatts
						tree[key]['constant_power_A_real'] = maxValueWatts/3
						tree[key]['constant_power_B_real'] = maxValueWatts/3
						tree[key]['constant_power_C_real'] = maxValueWatts/3
					else:
						raise Exception('Specified load name does not correspond to a load object. Make sure the object is of the following types: load, pqload, triplex_node, triplex_meter.')
					#run gridlab-d simulation with specified load set to max value
					omd['tree'] = tree
					feederName2 = "Olin Barre Fault - evInterconnection.omd"
					with open(modelDir + '/' + feederName2, "w+") as write_file:
						json.dump(omd, write_file)

					tempVoltPlotChart, tempProtDevTable = drawPlotFault(
						pJoin(modelDir,feederName2),
						neatoLayout = neato,
						edgeCol = "PercentOfRating",
						nodeCol = "perUnitVoltage",
						nodeLabs = "Load",
						edgeLabs = None,
						customColormap = False,
						scaleMin = .9,
						scaleMax = 1.1,
						faultLoc = None,
						faultType = None,
						rezSqIn = 225,
						simTime = "2000-01-01 0:00:00",
						workDir = modelDir,
						loadLoc = loadName)
					# loadVoltPlotChart.savefig(pJoin(modelDir, "loadVoltPlot.png"))
					# with open(pJoin(modelDir, "loadStatusTable.html"), "w") as tabFile:
					# 	tabFile.write(loadProtDevTable)
					# outData['loadProtDevTableHtml'] = loadProtDevTable
					# with open(pJoin(modelDir, "loadVoltPlot.png"),"rb") as inFile:
					# 	outData["loadVoltageDrop"] = inFile.read().encode("base64")
					return tempVoltPlotChart, tempProtDevTable
				else:
					print "Didn't find the gridlab object named " + loadName
					#raise an exception if loadName isn't in the tree
					raise Exception('Specified load name does not correspond to an object in the tree.')
			else:
				print "loadName is None"
				#raise an exception if loadName isn't specified
				raise Exception('Invalid request. Load Name must be specified.')
		else:
			print "maxValue is None"
			#raise an exception if maximum load value is not being passed in
			raise Exception('Error retrieving maximum load value from load shape.')

	#run and display voltage drop image and protective device status table with updated glm where the node with the specified load name is changed to the max value
	loadVoltPlotChart, loadProtDevTable = voltplot_protdev(max_value=maxLoadValue, load_name=loadNameValue)
	loadVoltPlotChart.savefig(pJoin(modelDir, "loadVoltPlot.png"))
	with open(pJoin(modelDir, "loadStatusTable.html"), "w") as tabFile:
		tabFile.write(loadProtDevTable)
	outData['loadProtDevTableHtml'] = loadProtDevTable
	with open(pJoin(modelDir, "loadVoltPlot.png"),"rb") as inFile:
		outData["loadVoltageDrop"] = inFile.read().encode("base64")

	# Create the input JSON file for REopt
	scenario = {
		"Scenario": {
			"Site": {
				"latitude": latitudeValue,
				"longitude": longitudeValue,
				"LoadProfile": {
					"loads_kw": combinedLoadShapeValue,		#8760 value list
					"year": yearValue 						#MUST BE THE CORRECT YEAR CORRELATING TO loads_kw!!
				},
				"ElectricTariff": {
					"urdb_rate_name": "custom",
					"blended_annual_rates_us_dollars_per_kwh": energyCostValue,
					"blended_annual_demand_charges_us_dollars_per_kw": demandCostValue
				},
				"Wind": {
					"max_kw": 0,
					"max_kwh": 0
				}
			}
		}
	}
	with open(pJoin(modelDir, "Scenario_test_POST.json"), "w") as jsonFile:
		json.dump(scenario, jsonFile)
	# Run REopt API script
	runREopt(pJoin(modelDir, 'Scenario_test_POST.json'), pJoin(modelDir, 'results.json'))

	#read results from json generated from REopt
	with open(pJoin(modelDir, "results.json"), "r") as REoptFile:
		REopt_output = json.load(REoptFile)
		#print REopt_output
	#find the values for energy cost with and without microgrid
	REopt_ev_energy_cost = REopt_output["outputs"]["Scenario"]["Site"]["ElectricTariff"]["year_one_bill_bau_us_dollars"]
	REopt_opt_energy_cost =	REopt_output["outputs"]["Scenario"]["Site"]["ElectricTariff"]["year_one_bill_us_dollars"]
	# REopt_ev_energy_cost = 100000
	# REopt_opt_energy_cost =	90000

	#Create the building energy cost table
	energyCostHtml = energyCostCalc(
		max_bau_load_shape = max(loadShapeValue),
		sum_bau_load_shape = sum(loadShapeValue),
		demand_charge = demandCostValue,
		energy_charge = energyCostValue,
		REopt_EV_output = REopt_ev_energy_cost,
		REopt_opt_output = REopt_opt_energy_cost)
	with open(pJoin(modelDir, "energyCostCalc.html"), "w") as energyFile:
		energyFile.write(energyCostHtml)
	outData["energyCostCalcHtml"] = energyCostHtml

	#get REopt's optimized load shape value list
	REoptLoadShape = REopt_output["outputs"]["Scenario"]["Site"]["LoadProfile"]["year_one_electric_load_series_kw"]

	#Create the maxLoadShape image
	maxLoadShapeImg = plotMaxLoadShape(
		loadShape = loadShapeValue,
		combined_load = combinedLoadShapeValue,
		hourly_con = hourlyConValue,
		REopt_load = REoptLoadShape)
	maxLoadShapeImg.savefig(pJoin(modelDir, "maxLoadShape.png"))
	with open(pJoin(modelDir, "maxLoadShape.png"),"rb") as evFile:
		outData["maxLoadShape"] = evFile.read().encode("base64")

	#Create 3rd powerflow run with maximum load from new ReOpt output load shape
	REoptVoltPlotChart, REoptProtDevTable = voltplot_protdev(max_value=max(REoptLoadShape), load_name=loadNameValue)
	REoptVoltPlotChart.savefig(pJoin(modelDir, "REoptVoltPlot.png"))
	with open(pJoin(modelDir, "REoptStatusTable.html"), "w") as tabFile:
		tabFile.write(REoptProtDevTable)
	outData['REoptProtDevTableHtml'] = REoptProtDevTable
	with open(pJoin(modelDir, "REoptVoltPlot.png"),"rb") as inFile:
		outData["REoptVoltageDrop"] = inFile.read().encode("base64")
	return outData

def drawPlotFault(path, workDir=None, neatoLayout=False, edgeLabs=None, nodeLabs=None, edgeCol=None, nodeCol=None, faultLoc=None, faultType=None, customColormap=False, scaleMin=None, scaleMax=None, rezSqIn=400, simTime='2000-01-01 0:00:00', loadLoc=None):
	''' Draw a color-coded map of the voltage drop on a feeder.
	path is the full path to the GridLAB-D .glm file or OMF .omd file.
	workDir is where GridLAB-D will run, if it's None then a temp dir is used.
	neatoLayout=True means the circuit is displayed using a force-layout approach.
	edgeCol property must be either 'Current', 'Power', 'Rating', 'PercentOfRating', or None
	nodeCol property must be either 'Voltage', 'VoltageImbalance', 'perUnitVoltage', 'perUnit120Voltage', or None
	edgeLabs and nodeLabs properties must be either 'Name', 'Value', or None
	edgeCol and nodeCol can be set to false to avoid coloring edges or nodes
	customColormap=True means use a one that is nicely scaled to perunit values highlighting extremes.
	faultType and faultLoc are the type of fault and the name of the line that it occurs on.
	Returns a matplotlib object.'''
	# Be quiet matplotlib:
	warnings.filterwarnings("ignore")
	if path.endswith('.glm'):
		tree = omf.feeder.parse(path)
		attachments = []
	elif path.endswith('.omd'):
		omd = json.load(open(path))
		tree = omd.get('tree', {})
		attachments = omd.get('attachments',[])
	else:
		raise Exception('Invalid input file type. We require a .glm or .omd.')
	#print path
	# add fault object to tree
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	# Add Reliability module
	tree[str(biggestKey*10)] = {"module":"reliability","maximum_event_length":"18000","report_event_log":"true"}
	CLOCK_START = simTime
	dt_start = parser.parse(CLOCK_START)
	dt_end = dt_start + relativedelta(seconds=+20)
	CLOCK_END = str(dt_end)
	CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END
	if faultType != None:
		# Add eventgen object (the fault)
		tree[str(biggestKey*10 + 1)] = {"object":"eventgen","name":"ManualEventGen","parent":"RelMetrics", "fault_type":faultType, "manual_outages":faultLoc + ',' + CLOCK_RANGE} # TODO: change CLOCK_RANGE to read the actual start and stop time, not just hard-coded
		# Add fault_check object
		tree[str(biggestKey*10 + 2)] = {"object":"fault_check","name":"test_fault","check_mode":"ONCHANGE", "eventgen_object":"ManualEventGen", "output_filename":"Fault_check_out.txt"}
		# Add reliabilty metrics object
		tree[str(biggestKey*10 + 3)] = {"object":"metrics", "name":"RelMetrics", "report_file":"Metrics_Output.csv", "module_metrics_object":"PwrMetrics", "metrics_of_interest":'"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"', "customer_group":'"groupid=METERTEST"', "metric_interval":"5 h", "report_interval":"5 h"}
		# Add power_metrics object
		tree[str(biggestKey*10 + 4)] = {"object":"power_metrics","name":"PwrMetrics","base_time_value":"1 h"}
		
		# HACK: set groupid for all meters so outage stats are collected.
		noMeters = True
		for key in tree:
			if tree[key].get('object','') in ['meter', 'triplex_meter']:
				tree[key]['groupid'] = "METERTEST"
				noMeters = False
		if noMeters:
			raise Exception("No meters detected on the circuit. Please add at least one meter to allow for collection of outage statistics.")
	for key in tree:
		if 'clock' in tree[key]:
			tree[key]['starttime'] = "'" + CLOCK_START + "'"
			tree[key]['stoptime'] = "'" + CLOCK_END + "'"
	
	# dictionary to hold info on lines present in glm
	edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator', 'fuse', 'switch'], False)
	# Map to speed up name lookups.
	nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}
	# Get rid of schedules and climate and check for all edge types:
	for key in tree.keys():
		obtype = tree[key].get("object","")
		if obtype == 'underground_line':
			edge_bools['underground_line'] = True
		elif obtype == 'overhead_line':
			edge_bools['overhead_line'] = True
		elif obtype == 'triplex_line':
			edge_bools['triplex_line'] = True
		elif obtype == 'transformer':
			edge_bools['transformer'] = True
		elif obtype == 'regulator':
			edge_bools['regulator'] = True
		elif obtype == 'fuse':
			edge_bools['fuse'] = True
		elif obtype == 'switch':
			edge_bools['switch'] = True
		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
			del tree[key]
	# Make sure we have a voltage dump and current dump:
	tree[str(biggestKey*10 + 5)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + 6)] = {"object":"currdump","filename":"currDump.csv"}
	# Line rating dumps
	tree[omf.feeder.getMaxKey(tree) + 1] = {
		'module': 'tape'
	}
	for key in edge_bools.keys():
		if edge_bools[key]:
			tree[omf.feeder.getMaxKey(tree) + 1] = {
				'object':'group_recorder', 
				'group':'"class='+key+'"',
				'property':'continuous_rating',
				'file':key+'_cont_rating.csv'
			}
	#Record initial status readout of each fuse/recloser/switch/sectionalizer before running
	# Reminder: fuse objects have 'phase_X_status' instead of 'phase_X_state'
	protDevices = dict.fromkeys(['fuse', 'recloser', 'switch', 'sectionalizer'], False)
	#dictionary of protective device initial states for each phase
	protDevInitStatus = {}
	#dictionary of protective devices final states for each phase after running Gridlab-D
	protDevFinalStatus = {}
	#dictionary of protective device types to help the testing and debugging process
	protDevTypes = {}
	protDevOpModes = {}
	for key in tree:
		obj = tree[key]
		obType = obj.get('object')
		if obType in protDevices.keys():
			obName = obj.get('name', '')
			protDevTypes[obName] = obType
			if obType != 'fuse':
				protDevOpModes[obName] = obj.get('operating_mode', 'INDIVIDUAL')
			protDevices[obType] = True
			protDevInitStatus[obName] = {}
			protDevFinalStatus[obName] = {}
			for phase in ['A', 'B', 'C']:
				if obType != 'fuse':
					phaseState = obj.get('phase_' + phase + '_state','CLOSED')
				else:
					phaseState = obj.get('phase_' + phase + '_status','GOOD')
				if phase in obj.get('phases', ''):
					protDevInitStatus[obName][phase] = phaseState
	#print protDevInitStatus

	#Create a recorder for protective device states
	for key in protDevices.keys():
		if protDevices[key]:
			for phase in ['A', 'B', 'C']:
				if key != 'fuse':
					tree[omf.feeder.getMaxKey(tree) + 1] = {
						'object':'group_recorder', 
						'group':'"class='+key+'"',
						'property':'phase_' + phase + '_state',
						'file':key + '_phase_' + phase + '_state.csv'
					}
				else:
					tree[omf.feeder.getMaxKey(tree) + 1] = {
						'object':'group_recorder', 
						'group':'"class='+key+'"',
						'property':'phase_' + phase + '_status',
						'file':key + '_phase_' + phase + '_state.csv'
					}

	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)
	
	#Record final status readout of each fuse/recloser/switch/sectionalizer after running
	for key in protDevices.keys():
		if protDevices[key]:
			for phase in ['A', 'B', 'C']:
				with open(pJoin(workDir,key+'_phase_'+phase+'_state.csv'),'r') as statusFile:
					reader = csv.reader(statusFile)
					# loop past the header, 
					keys = []
					vals = []
					for row in reader:
						if '# timestamp' in row:
							keys = row
							i = keys.index('# timestamp')
							keys.pop(i)
							vals = reader.next()
							vals.pop(i)
					for pos,key2 in enumerate(keys):
						protDevFinalStatus[key2][phase] = vals[pos]
	#print protDevFinalStatus

	#compare initial and final states of protective devices
	#quick compare to see if they are equal
	#print cmp(protDevInitStatus, protDevFinalStatus)
	#find which values changed
	changedStates = {}


	#read voltDump values into a dictionary.
	try:
		dumpFile = open(pJoin(workDir,'voltDump.csv'),'r')
	except:
		raise Exception('GridLAB-D failed to run with the following errors:\n' + gridlabOut['stderr'])
	reader = csv.reader(dumpFile)
	reader.next() # Burn the header.
	keys = reader.next()
	
	

	voltTable = []
	for row in reader:
		rowDict = {}
		for pos,key in enumerate(keys):
			rowDict[key] = row[pos]
		voltTable.append(rowDict)
	# read currDump values into a dictionary
	with open(pJoin(workDir,'currDump.csv'),'r') as currDumpFile:
		reader = csv.reader(currDumpFile)
		reader.next() # Burn the header.
		keys = reader.next()
		currTable = []
		for row in reader:
			rowDict = {}
			for pos,key in enumerate(keys):
				rowDict[key] = row[pos]
			currTable.append(rowDict)
	# read line rating values into a single dictionary
	lineRatings = {}
	rating_in_VA = []
	for key1 in edge_bools.keys():
		if edge_bools[key1]:		
			with open(pJoin(workDir,key1+'_cont_rating.csv'),'r') as ratingFile:
				reader = csv.reader(ratingFile)
				# loop past the header, 
				keys = []
				vals = []
				for row in reader:
					if '# timestamp' in row:
						keys = row
						i = keys.index('# timestamp')
						keys.pop(i)
						vals = reader.next()
						vals.pop(i)
				for pos,key2 in enumerate(keys):
					lineRatings[key2] = abs(float(vals[pos]))
	#edgeTupleRatings = lineRatings copy with to-from tuple as keys for labeling
	edgeTupleRatings = {}
	for edge in lineRatings:
		for obj in tree.values():
			if obj.get('name','').replace('"','') == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				ratingVal = lineRatings.get(edge)
				edgeTupleRatings[coord] = ratingVal
	# Calculate average node voltage deviation. First, helper functions.
	def digits(x):
		''' Returns number of digits before the decimal in the float x. '''
		return math.ceil(math.log10(x+1))
	def avg(l):
		''' Average of a list of ints or floats. '''
		# HACK: add a small value to the denominator to avoid divide by zero for out of service locations (i.e. zero voltage).
		return sum(l)/(len(l) + 0.00000000000000001)
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	# Tot it all up.
	nodeVolts = {}
	nodeVoltsPU = {}
	nodeVoltsPU120 = {}
	voltImbalances = {}
	for row in voltTable:
		allVolts = []
		allVoltsPU = []
		allDiffs = []
		nodeName = row.get('node_name','')
		for phase in ['A','B','C']:
			realVolt = abs(float(row['volt'+phase+'_real']))
			imagVolt = abs(float(row['volt'+phase+'_imag']))
			phaseVolt = math.sqrt((realVolt ** 2) + (imagVolt ** 2))
			if phaseVolt != 0.0:
				treeKey = nameToIndex.get(nodeName, 0)
				nodeObj = tree.get(treeKey, {})
				try:
					nominal_voltage = float(nodeObj['nominal_voltage'])
				except:
					nominal_voltage = feedVoltage
				allVolts.append(phaseVolt)
				normVolt = (phaseVolt/nominal_voltage)
				allVoltsPU.append(normVolt)
		avgVolts = avg(allVolts)
		avgVoltsPU = avg(allVoltsPU)
		avgVoltsPU120 = 120 * avgVoltsPU
		nodeVolts[nodeName] = float("{0:.2f}".format(avgVolts))
		nodeVoltsPU[nodeName] = float("{0:.2f}".format(avgVoltsPU))
		nodeVoltsPU120[nodeName] = float("{0:.2f}".format(avgVoltsPU120))
		if len(allVolts) == 3:
			voltA = allVolts.pop()
			voltB = allVolts.pop()
			voltC = allVolts.pop()
			allDiffs.append(abs(float(voltA-voltB)))
			allDiffs.append(abs(float(voltA-voltC)))
			allDiffs.append(abs(float(voltB-voltC)))
			maxDiff = max(allDiffs)
			voltImbal = maxDiff/avgVolts
			voltImbalances[nodeName] = float("{0:.2f}".format(voltImbal))
		# Use float("{0:.2f}".format(avg(allVolts))) if displaying the node labels
	nodeLoadNames = {}
	nodeNames = {}
	for key in nodeVolts.keys():
		nodeNames[key] = key
		if key == loadLoc:
			nodeLoadNames[key] = "LOAD: " + key
	# find edge currents by parsing currdump
	edgeCurrentSum = {}
	edgeCurrentMax = {}
	for row in currTable:
		allCurr = []
		for phase in ['A','B','C']:
			realCurr = abs(float(row['curr'+phase+'_real']))
			imagCurr = abs(float(row['curr'+phase+'_imag']))
			phaseCurr = math.sqrt((realCurr ** 2) + (imagCurr ** 2))
			allCurr.append(phaseCurr)
		edgeCurrentSum[row.get('link_name','')] = sum(allCurr)
		edgeCurrentMax[row.get('link_name','')] = max(allCurr)
	# When just showing current as labels, use sum of the three lines' current values, when showing the per unit values (current/rating), use the max of the three
	#edgeTupleCurrents = edgeCurrents copy with to-from tuple as keys for labeling
	edgeTupleCurrents = {}
	#edgeValsPU = values normalized per unit by line ratings
	edgeValsPU = {}
	#edgeTupleValsPU = edgeValsPU copy with to-from tuple as keys for labeling
	edgeTupleValsPU = {}
	#edgeTuplePower = dict with to-from tuples as keys and sim power as values for debugging
	edgeTuplePower = {}
	#edgeTupleNames = dict with to-from tuples as keys and names as values for debugging
	edgeTupleNames = {}
	#edgeTupleFaultNames = dict with to-from tuples as keys and the name of the Fault as the only value
	edgeTupleFaultNames = {}
	#edgeTupleProtDevs = dict with to-from tuples as keys and the initial of the type of protective device as the value
	edgeTupleProtDevs = {}
	#linePhases = dictionary containing the number of phases on each line for line-width purposes
	linePhases = {}
	edgePower = {}
	for edge in edgeCurrentSum:
		for obj in tree.values():
			obname = obj.get('name','').replace('"','')
			if obname == edge:
				objType = obj.get('object')
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				currVal = edgeCurrentSum.get(edge)
				voltVal = avg([nodeVolts.get(nodeFrom), nodeVolts.get(nodeTo)])
				power = (currVal * voltVal)/1000
				lineRating = lineRatings.get(edge, 10.0**9)
				edgePerUnitVal = (edgeCurrentMax.get(edge))/lineRating
				edgeTupleCurrents[coord] = "{0:.2f}".format(currVal)
				edgeTuplePower[coord] = "{0:.2f}".format(power)
				edgePower[edge] = power
				edgeValsPU[edge] = edgePerUnitVal
				edgeTupleValsPU[coord] = "{0:.2f}".format(edgePerUnitVal)
				edgeTupleNames[coord] = edge
				if faultLoc == edge:
					edgeTupleFaultNames[coord] = "FAULT: " + edge
				phaseStr = obj.get('phases','').replace('"','').replace('N','').replace('S','')
				numPhases = len(phaseStr)
				if (numPhases < 1) or (numPhases > 3):
					numPhases = 1
				linePhases[edge] = numPhases
				if objType == 'fuse':
					edgeTupleProtDevs[coord] = 'F'
				elif objType == 'switch':
					edgeTupleProtDevs[coord] = 'S'
				elif objType == 'recloser':
					edgeTupleProtDevs[coord] = 'R'
				elif objType == 'sectionalizer':
					edgeTupleProtDevs[coord] = 'X'
	#define which dict will be used for edge line color
	edgeColors = edgeValsPU
	#define which dict will be used for edge label
	edgeLabels = edgeTupleValsPU
	# Build the graph.
	fGraph = omf.feeder.treeToNxGraph(tree)
	# TODO: consider whether we can set figsize dynamically.
	wlVal = int(math.sqrt(float(rezSqIn)))
	voltChart = plt.figure(figsize=(wlVal, wlVal))
	plt.axes(frameon = 0)
	plt.axis('off')
	voltChart.gca().set_aspect('equal')
	plt.tight_layout()
	# Need to get edge names from pairs of connected node names.
	edgeNames = []
	for e in fGraph.edges():
		edgeNames.append((fGraph.edge[e[0]][e[1]].get('name','BLANK')).replace('"',''))
	#set axes step equal
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
	#create custom colormap
	if customColormap:
		if scaleMin != None and scaleMax != None:
			scaleDif = scaleMax - scaleMin
			custom_cm = matplotlib.colors.LinearSegmentedColormap.from_list('custColMap',[(scaleMin,'blue'),(scaleMin+(0.12*scaleDif),'darkgray'),(scaleMin+(0.56*scaleDif),'darkgray'),(scaleMin+(0.8*scaleDif),'red')])
			vmin = scaleMin
			vmax = scaleMax
		else:
			custom_cm = matplotlib.colors.LinearSegmentedColormap.from_list('custColMap',[(0.0,'blue'),(0.15,'darkgray'),(0.7,'darkgray'),(1.0,'red')])
			vmin = 0
			vmax = 1.25
		custom_cm.set_under(color='black')
	else:
		custom_cm = plt.cm.get_cmap('viridis')
		if scaleMin != None and scaleMax != None:
			vmin = scaleMin
			vmax = scaleMax
		else:
			vmin = None
			vmax = None
	drawColorbar = False
	emptyColors = {}
	#draw edges with or without colors
	if edgeCol != None:
		drawColorbar = True
		if edgeCol == "Current":
			edgeList = [edgeCurrentSum.get(n,1) for n in edgeNames]
			drawColorbar = True
		elif edgeCol == "Power":
			edgeList = [edgePower.get(n,1) for n in edgeNames]
			drawColorbar = True
		elif edgeCol == "Rating":
			edgeList = [lineRatings.get(n, 10.0**9) for n in edgeNames]
			drawColorbar = True
		elif edgeCol == "PercentOfRating":
			edgeList = [edgeValsPU.get(n,.5) for n in edgeNames]
			drawColorbar = True
		else:
			edgeList = [emptyColors.get(n,.6) for n in edgeNames]
			print "WARNING: edgeCol property must be 'Current', 'Power', 'Rating', 'PercentOfRating', or None"
	else:
		edgeList = [emptyColors.get(n,.6) for n in edgeNames]
	edgeIm = nx.draw_networkx_edges(fGraph,
		pos = positions,
		edge_color = edgeList,
		width = [linePhases.get(n,1) for n in edgeNames],
		edge_cmap = custom_cm)
	#draw edge labels
	if edgeLabs != None:
		if edgeLabs == "Name":
			edgeLabels = edgeTupleNames
		elif edgeLabs == "Fault":
			edgeLabels = edgeTupleFaultNames
		elif edgeLabs == "Value":
			if edgeCol == "Current":
				edgeLabels = edgeTupleCurrents
			elif edgeCol == "Power":
				edgeLabels = edgeTuplePower
			elif edgeCol == "Rating":
				edgeLabels = edgeTupleRatings
			elif edgeCol == "PercentOfRating":
				edgeLabels = edgeTupleValsPU
			else:
				edgeLabels = None
				print "WARNING: edgeCol property cannot be set to None when edgeLabs property is set to 'Value'"
		elif edgeLabs == "ProtDevs":
			edgeLabels = edgeTupleProtDevs
		else:
			edgeLabs = None
			print "WARNING: edgeLabs property must be either 'Name', 'Value', or None"
	if edgeLabs != None:
		edgeLabelsIm = nx.draw_networkx_edge_labels(fGraph,
			pos = positions,
			edge_labels = edgeLabels,
			font_size = 8)
	# draw nodes with or without color
	if nodeCol != None:
		if nodeCol == "Voltage":
			nodeList = [nodeVolts.get(n,1) for n in fGraph.nodes()]
			drawColorbar = True
		elif nodeCol == "VoltageImbalance":
			nodeList = [voltImbalances.get(n,1) for n in fGraph.nodes()]
			drawColorbar = True
		elif nodeCol == "perUnitVoltage":
			nodeList = [nodeVoltsPU.get(n,.5) for n in fGraph.nodes()]
			drawColorbar = True
		elif nodeCol == "perUnit120Voltage":
			nodeList = [nodeVoltsPU120.get(n,60) for n in fGraph.nodes()]
			drawColorbar = True
		else:
			nodeList = [emptyColors.get(n,1) for n in fGraph.nodes()]
			print "WARNING: nodeCol property must be 'Voltage', 'VoltageImbalance', 'perUnitVoltage', 'perUnit120Voltage', or None"
	else:
		nodeList = [emptyColors.get(n,.6) for n in fGraph.nodes()]

	nodeIm = nx.draw_networkx_nodes(fGraph,
		pos = positions,
		node_color = nodeList,
		linewidths = 0,
		node_size = 30,
		vmin = vmin,
		vmax = vmax,
		cmap = custom_cm)
	#draw node labels
	nodeLabels = {}
	if nodeLabs != None:
		if nodeLabs == "Name":
			nodeLabels = nodeNames
		elif nodeLabs == "Value":
			if nodeCol == "Voltage":
				nodeLabels = nodeVolts
			elif nodeCol == "VoltageImbalance":
				nodeLabels = voltImbalances
			elif nodeCol == "perUnitVoltage":
				nodeLabels = nodeVoltsPU
			elif nodeCol == "perUnit120Voltage":
				nodeLabels = nodeVoltsPU120
			else:
				nodeLabels = None
				print "WARNING: nodeCol property cannot be set to None when nodeLabs property is set to 'Value'"
		#HACK: add hidden node label option for displaying specified load name
		elif nodeLabs == "Load":
			nodeLabels = nodeLoadNames
		else:
			nodeLabs = None
			print "WARNING: nodeLabs property must be either 'Name', 'Value', or None"
	if nodeLabs != None:
		nodeLabelsIm = nx.draw_networkx_labels(fGraph,
			pos = positions,
			labels = nodeLabels,
			font_size = 8)
	plt.sci(nodeIm)
	# plt.clim(110,130)
	if drawColorbar:
		plt.colorbar()
	# Also draw a table.
	#TODO: factor this out and in to work().
	table = drawTable(initialStates=protDevInitStatus, finalStates=protDevFinalStatus, deviceTypes=protDevTypes)
	return voltChart, table

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	fName = "input - 200 Employee Office, Springfield Illinois, 2001.csv"
	defaultInputs = {
		"feederName1": "Olin Barre Fault",
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "geospatial",
		"batterySize" : "50",
		"chargeRate" : "40",
		"efficiency" : "0.5",
		"gasEfficiency" : "8",
		"numVehicles" : "50",
		"energyCost" : "0.12",
		"startHour" : "8",
		"endHour" : "10",
		"chargeLimit" : "150",
		"minCharge" : "10",
		"maxCharge" : "50",
		"gasCost" : "2.70",
		"workload" : "40",
		"loadShape" : open(pJoin(omf.omfDir, "static", "testFiles", fName)).read(),
		"fileName" : fName,
		"loadName" : "62474211556",
		"rezSqIn" : "400",
		"simTime" : '2000-01-01 0:00:00',
		"latitude" : '39.7817',
		"longitude" : '-89.6501',
		"year" : '2001',
		"demandCost" : '0.1'
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _testingPlot():
	PREFIX = omf.omfDir + '/scratch/CIGAR/'
	# FNAME = 'test_base_R4-25.00-1.glm_CLEAN.glm'
	# FNAME = 'test_Exercise_4_2_1.glm'
	# FNAME = 'test_ieee37node.glm'
	FNAME = 'test_ieee37nodeFaultTester.glm'
	# FNAME = 'test_ieee123nodeBetter.glm'
	# FNAME = 'test_large-R5-35.00-1.glm_CLEAN.glm'
	# FNAME = 'test_medium-R4-12.47-1.glm_CLEAN.glm'
	# FNAME = 'test_smsSingle.glm'
	# Hack: Agg backend doesn't work for interactivity. Switch to something we can use:
	# plt.switch_backend('MacOSX')
	chart = drawPlotFault(PREFIX + FNAME, neatoLayout=True, edgeCol="Current", nodeCol=None, nodeLabs="Name", edgeLabs=None, faultLoc="node713-704", faultType="TLG", customColormap=False, scaleMin=None, scaleMax=None, rezSqIn=225, simTime='2000-01-01 0:00:00')
	chart.savefig(PREFIX + "YO_WHATS_GOING_ON.png")
	# plt.show()

def drawTable(initialStates=None, finalStates=None, deviceTypes=None):
	#return self.log
	html_str = """
		<table cellpadding="0" cellspacing="0">
			<thead>
				<tr>
					<th>Protective Device Name</th>
					<th>Device Type</th>
					<th>Initial States</th>
					<th>Final States</th>
					<th>Changes</th>
				</tr>
			</thead>
			<tbody>"""
	for device in initialStates.keys():
		row_str = "<tr><td>"+device+"</td><td>"
		devType = deviceTypes[device]
		if devType == 'fuse':
			row_str += "Fuse (F)</td><td>"
		elif devType == 'switch':
			row_str += "Switch (S)</td><td>"
		elif devType == 'recloser':
			row_str += "Recloser (R)</td><td>"
		elif devType == 'sectionalizer':
			row_str += "Sectionalizer (X)</td><td>"
		else:
			row_str += "Unknown</td><td>"
		for phase in initialStates[device].keys():
			row_str += "Phase " + phase + " = " + initialStates[device][phase] + "</br>"
		row_str += "</td><td>"
		for phase in finalStates[device].keys():
			row_str += "Phase " + phase + " = " + finalStates[device][phase] + "</br>"
		row_str += "</td>"
		noChange = True
		change_str = ""
		for phase in finalStates[device].keys():
			try:
				if initialStates[device][phase] != finalStates[device][phase]:
					change_str += "Phase " + phase + " : " + initialStates[device][phase] + " -> " + finalStates[device][phase] + "</br>"
					noChange = False
			except:
				pass #key error...
		if noChange:
			row_str += "<td>No Change"
		else:
			row_str += "<td style=\"color: red;\">"
			row_str += change_str
		row_str += "</td></tr>"
		html_str += row_str
	html_str += """</tbody></table>"""
	return html_str

def plotMaxLoadShape(loadShape=None, combined_load=None, hourly_con=None, REopt_load=None):
	base_shape = loadShape
	base_shape_REopt = REopt_load

	#find the maximum combined load value
	max_val = max(combined_load)
	#find that value's index
	max_index = combined_load.index(max_val)

	#find the day that the max load value occurs
	max_day_val = (max_index)/24
	max_hour_val = (max_index)%24
	day_shape = base_shape[max_day_val*24:max_day_val*24+24]

	#find the maximum REopt load value
	max_val_REopt = max(base_shape_REopt)
	#find that value's index
	max_index_REopt = base_shape_REopt.index(max_val_REopt)

	#find the day that the max REopt load value occurs
	max_day_val_REopt = (max_index_REopt)/24
	max_hour_val_REopt = (max_index_REopt)%24
	day_shape_REopt = base_shape_REopt[max_day_val_REopt*24:max_day_val_REopt*24+24]

	print "max_val: " + str(max_val)
	print "max_val_REopt: " + str(max_val_REopt)

	def maxLoadShape(load_vec, daily_vec, REopt_vec):
		maxLoadShapeImg = plt.figure()
		plt.style.use('seaborn')
		plt.ylim(0.0, 1.15*max_val)
		if len(load_vec) != 0:
			plt.stackplot(range(len(load_vec)), load_vec, daily_vec)
		if len(REopt_vec) != 0:
			plt.plot(day_shape_REopt, color='black', linestyle='dotted', label='with REopt Optimization')
		plt.title('Maximum Daily Load Shape')
		plt.ylabel('Demand (KW)')
		plt.xlabel('Time of Day (Hour)')
		plt.legend()
		plt.close()
		return maxLoadShapeImg

	return maxLoadShape(day_shape, hourly_con, day_shape_REopt)


def plotEVShape(numVehicles=None, chargeRate=None, batterySize=None, startHour=None, endHour=None, chargeLimit=None, minCharge=None, maxCharge=None, loadShape=None, rezSqIn=None):
	shapes = []
	for i in range(numVehicles):
		# Random arrival
		charge_start = randint(startHour * 60, endHour * 60)
		# Random charge needed
		charge_needed = (1 - uniform(minCharge, maxCharge)) * batterySize
		# Make an array of charging powers and set them.
		shape = np.zeros(30*60)	# minute resolution, day + 6 hours.
		charging_minutes = int(60 * charge_needed/chargeRate)
		shape[charge_start: charge_start + charging_minutes] = 1.0 * chargeRate
		shapes.append(shape)
	def first_free_minute(shape, start_minute):
		'Find the earliest minute a load is not charging.'
		for m in range(start_minute, len(shape)):
			if shape[m] == 0:
				return m
		# If it's never free:
		return -1

	# Peak limit a collection of load shapes.
	shapes2 = np.copy(shapes)
	max_minutes = len(shapes2[0])
	for minute in range(max_minutes):	
		tot_load = sum([x[minute] for x in shapes2])
		if tot_load > chargeLimit:
			reduce_perc = chargeLimit / tot_load
			for shape in shapes2:
				# Stick the additional charging needed at the first free time.
				free_min = first_free_minute(shape, minute)
				shape[free_min] = (1 - reduce_perc) * shape[minute]
				# Reduce current load in proportion to how high the total is.
				shape[minute] = reduce_perc * shape[minute]
	# Plot the EV shape.
	evShape = plt.figure()
	plt.title('EV Charging Demand')
	plt.stackplot(range(max_minutes), shapes2)
	plt.ylabel('Demand (KW)')
	plt.xlabel('Time of Day (Hour)')
	plt.plot(sum(shapes), color='black', label='Total (Uncontrolled)')
	plt.plot(sum(shapes2), color='black', linestyle='dotted', label='Total (Controlled)')
	plt.xticks([x*60 for x in range(max_minutes/60)], range(max_minutes/60))
	plt.legend()
	plt.close()
	#plt.show()

	# Make a charging shape.
	con_charge = sum(shapes2)
	hourly_con = range(24)
	for i in range(24):
		hourly_con[i] = float(sum(con_charge[i * 60:i * 60 + 60])/60.0)

	# Make an annual building load base shape.
	#ann_shape = open(loadShape).readlines()
	#base_shape = [float(x) for x in ann_shape]
	base_shape = loadShape

	# Make an output csv.
	combined = []
	for i in range(8760):
		com_load = base_shape[i] + hourly_con[i % 24]
		combined.append(com_load)
	with open('output - evInterconnection combined load shapes.csv', 'w') as outFile:
		for row in combined:
			outFile.write(str(row) + '\n')

	def carpet_plot(load_vec, daily_vec):
		'Plot an 8760 load shape plus a daily augmentation in a nice grid.'
		carpetPlotImg = plt.figure()
		plt.style.use('seaborn')
		for i in range(1,371):
			# x = np.random.rand(24)
			x = list(load_vec[i*24:i*24 + 24])
			plt.subplot(31, 12, i)
			plt.axis('off')
			plt.ylim(0.0, max(combined))
			if len(x) != 0:
				plt.stackplot(range(len(x)), x, daily_vec)
			if i <= 12:
				plt.title(i)
			if i % 12 == 1:
				plt.text(-5.0, 0.1, str(1 + i / 12), horizontalalignment='left',verticalalignment='center')
		#plt.show()
		plt.close()
		return carpetPlotImg

	#find the maximum combined load value
	max_val = max(combined)
	# #find that value's index
	# max_index = combined.index(max_val)

	# #find the day that the max load value occurs
	# max_day_val = (max_index)/24
	# max_hour_val = (max_index)%24
	# day_shape = base_shape[max_day_val*24:max_day_val*24+24]

	# def maxLoadShape(load_vec, daily_vec):
	# 	maxLoadShapeImg = plt.figure()
	# 	plt.style.use('seaborn')
	# 	plt.ylim(0.0, 1.15*max_val)
	# 	if len(load_vec) != 0:
	# 		plt.stackplot(range(len(load_vec)), load_vec, daily_vec)
	# 	plt.title('Maximum Daily Load Shape')
	# 	plt.ylabel('Demand (KW)')
	# 	plt.xlabel('Time of Day (Hour)')
	# 	plt.close()
	# 	return maxLoadShapeImg
		
	#return max_val, evShape, carpet_plot(base_shape, hourly_con), maxLoadShape(day_shape, hourly_con), combined
	return max_val, evShape, carpet_plot(base_shape, hourly_con), hourly_con, combined

def fuelCostCalc(numVehicles=None, batterySize=None, efficiency=None, energyCost=None, gasEfficiency=None, gasCost=None, workload=None):
	dailyGasAmount = workload/gasEfficiency #amount(gal) of gas used per vehicle, daily
	dailyGasCost = dailyGasAmount*gasCost #amount($) spent on gas per vehicle, daily
	totalGasCost = numVehicles*dailyGasCost #amount($) spent on gas daily for all vehicles
	dailyEnergyAmount = workload/efficiency #amount(KWh) of energy used per vehicle, daily
	dailyEnergyCost = dailyEnergyAmount*energyCost #amount($) spent on energy per vehicle, daily
	totalEnergyCost = numVehicles*dailyEnergyCost #amount($) spent on energy daily for all vehicles
	dailySavings = dailyGasCost-dailyEnergyCost #amount($) saved per vehicle, daily
	totalSavings = totalGasCost-totalEnergyCost #amount($) saved daily
	html_str = """
		<div style="text-align:center">
			<p style="padding-top:10px; padding-bottom:10px;">Driving <b>""" + str(numVehicles) +"""</b> vehicles <b>"""+ str(workload) +""" miles</b> daily, at <b>"""+ str(gasEfficiency) +""" mpg</b> and <b>$""" + str(gasCost) + """/gal</b>:</p>
			<p>Total gas used daily:<span style="padding-left:2em">"""+str(dailyGasAmount)+""" gal</span></p>
			<p>Daily Cost per vehicle:<span style="padding-left:2em">$"""+str(dailyGasCost)+"""</span></p>
			<p>Total daily cost:<span style="padding-left:2em">$"""+str(totalGasCost)+"""</span></p>
			<p style="padding-top:10px; padding-bottom:10px;">Driving <b>""" + str(numVehicles) +"""</b> vehicles <b>"""+ str(workload) +""" miles</b> daily, at <b>"""+ str(efficiency) +""" mpkwh</b> and <b>$""" + str(energyCost) + """/kwh:</b></p>
			<p>Total energy used daily:<span style="padding-left:2em">"""+str(dailyEnergyAmount)+""" kwh</span></p>
			<p>Daily cost per vehicle:<span style="padding-left:2em">$"""+str(dailyEnergyCost)+"""</span></p>
			<p>Total daily cost:<span style="padding-left:2em">$"""+str(totalEnergyCost)+"""</span></p>
			<p style="padding-top:10px; padding-bottom:10px;">Daily savings per vehicle:<span style="padding-left:1em">$"""+str(dailySavings)+"""</span><span style="padding-left:4em">Total daily savings:<span style="padding-left:1em">$"""+str(totalSavings)+"""</span></span></p>
		</div>"""
	return html_str

def energyCostCalc(max_bau_load_shape = None, sum_bau_load_shape = None, demand_charge = None, energy_charge = None, REopt_EV_output=None, REopt_opt_output=None):
	bau_energy_cost = max_bau_load_shape*demand_charge + sum_bau_load_shape*energy_charge
	ev_energy_cost = REopt_EV_output
	opt_energy_cost = REopt_opt_output
	html_str = """
		<div style="text-align:center">
			<p style="padding-top:30px; padding-bottom:15px;">Yearly Energy Costs:</p>
			<p style="padding-top:10px; padding-bottom:10px;">Business as usual (no EVs): <b>$""" + '{:20,.2f}'.format(bau_energy_cost) +"""</b> </p>
			<p style="padding-top:10px; padding-bottom:10px;">with EVs: <b>$""" + '{:20,.2f}'.format(ev_energy_cost) +"""</b> </p>
			<p style="padding-top:10px; padding-bottom:30px;">with EVs and microgrid: <b>$""" + '{:20,.2f}'.format(opt_energy_cost) +"""</b> </p>
		</div>"""
	return html_str

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
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()
	# _testingPlot()
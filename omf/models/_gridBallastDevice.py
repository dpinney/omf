''' Simulate a GridBallast device at a single service point. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import networkx as nx
from omf.models import __metaModel__
from __metaModel__ import *

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "Simulate a GridBallast device at a single service point."

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,modelName+".html"),"r") as tempFile:
	template = Template(tempFile.read())

# We just hardcode the GridLAB-D model here since it is the same for every model instance:
circuitModel = {
	"tree": {
		"24": {
			"phases": "BS", 
			"object": "triplex_meter", 
			"nominal_voltage": "120", 
			"name": "tn_2"
		}, 
		"25": {
			"phases": "AS", 
			"from": "tn_1", 
			"name": "tl_1", 
			"object": "triplex_line", 
			"to": "tm_1", 
			"length": "100", 
			"configuration": "trip_line_config"
		}, 
		"27": {
			"phases": "AS", 
			"object": "triplex_meter", 
			"nominal_voltage": "120", 
			"name": "tm_1"
		}, 
		"20": {
			"name": "tconf", 
			"primary_voltage": "2401.777", 
			"install_type": "POLETOP", 
			"object": "transformer_configuration", 
			"secondary_voltage": "120", 
			"connect_type": "SINGLE_PHASE_CENTER_TAPPED", 
			"shunt_impedance": "10000+10000j", 
			"impedance": "0.00033+0.0022j", 
			"powerA_rating": "110 kVA"
		}, 
		"21": {
			"name": "tconf2", 
			"primary_voltage": "2401.777", 
			"install_type": "POLETOP", 
			"object": "transformer_configuration", 
			"secondary_voltage": "120", 
			"connect_type": "SINGLE_PHASE_CENTER_TAPPED", 
			"shunt_impedance": "10000+10000j", 
			"impedance": "0.00033+0.0022j", 
			"powerB_rating": "110 kVA"
		}, 
		"22": {
			"phases": "BS", 
			"from": "n630", 
			"name": "T2", 
			"object": "transformer", 
			"to": "tn_2", 
			"configuration": "tconf2", 
			"groupid": "Distribution_Trans"
		}, 
		"23": {
			"phases": "AS", 
			"object": "triplex_node", 
			"nominal_voltage": "120", 
			"name": "tn_1"
		}, 
		"29": {
			"schedule_skew": "-810", 
			"auxiliary_system_type": "ELECTRIC", 
			"name": "house1", 
			"parent": "tm_1", 
			"floor_area": "1838", 
			"cooling_COP": "3.2", 
			"object": "house", 
			"cooling_system_type": "ELECTRIC", 
			"aux_heat_temperature_lockout": "2.270706e+001", 
			"heating_setpoint": "heating1*1", 
			"motor_model": "BASIC", 
			"auxiliary_strategy": "LOCKOUT", 
			"air_temperature": "70", 
			"thermal_integrity_level": "5", 
			"heating_COP": "3.1", 
			"cooling_setpoint": "cooling7*1", 
			"mass_temperature": "70", 
			"motor_efficiency": "GOOD", 
			"heating_system_type": "HEAT_PUMP"
		}, 
		"1": {
			"omftype": "#include", 
			"argument": "\"schedules.glm\""
		}, 
		"0": {
			"timezone": "PST+8PDT", 
			"stoptime": "'2000-01-10 00:00:00'", 
			"starttime": "'2000-01-01 00:00:00'", 
			"clock": "clock"
		}, 
		"3": {
			"omftype": "#set", 
			"argument": "profiler=1"
		}, 
		"2": {
			"omftype": "#set", 
			"argument": "minimum_timestep=60"
		}, 
		"5": {
			"omftype": "module", 
			"argument": "generators"
		}, 
		"4": {
			"omftype": "#set", 
			"argument": "relax_naming_rules=1"
		}, 
		"7": {
			"omftype": "module", 
			"argument": "climate"
		}, 
		"6": {
			"omftype": "module", 
			"argument": "tape"
		}, 
		"9": {
			"solver_method": "NR", 
			"NR_iteration_limit": "50", 
			"module": "powerflow"
		}, 
		"8": {
			"module": "residential", 
			"implicit_enduses": "NONE"
		}, 
		"11": {
			"Control": "MANUAL", 
			"raise_taps": "16", 
			"PT_phase": "ABC", 
			"name": "regulator_configuration_6506321", 
			"band_center": "2401", 
			"tap_pos_A": "1", 
			"tap_pos_B": "1", 
			"object": "regulator_configuration", 
			"time_delay": "30.0", 
			"connect_type": "1", 
			"regulation": "0.10", 
			"CT_phase": "ABC", 
			"band_width": "50", 
			"tap_pos_C": "1", 
			"Type": "A", 
			"lower_taps": "16"
		}, 
		"10": {
			"object": "climate", 
			"name": "\"climate\"", 
			"interpolate": "QUADRATIC", 
			"tmyfile": "\"climate.tmy2\""
		}, 
		"13": {
			"object": "triplex_line_conductor", 
			"resistance": "0.97", 
			"name": "tlc", 
			"geometric_mean_radius": "0.01111"
		}, 
		"12": {
			"diameter": "0.368", 
			"name": "trip_line_config", 
			"object": "triplex_line_configuration", 
			"conductor_1": "tlc", 
			"conductor_2": "tlc", 
			"conductor_N": "tlc", 
			"insulation_thickness": "0.08"
		}, 
		"17": {
			"phases": "ABC", 
			"from": "n650", 
			"name": "Reg1", 
			"object": "regulator", 
			"to": "n630", 
			"configuration": "regulator_configuration_6506321"
		}, 
		"16": {
			"phases": "ABCN", 
			"name": "n650", 
			"object": "node", 
			"bustype": "SWING", 
			"voltage_B": "-1200.8886-2080.000j", 
			"voltage_C": "-1200.8886+2080.000j", 
			"voltage_A": "2401.7771", 
			"nominal_voltage": "2401.7771"
		}, 
		"19": {
			"phases": "AS", 
			"from": "n630", 
			"name": "T1", 
			"object": "transformer", 
			"to": "tn_1", 
			"configuration": "tconf", 
			"groupid": "Distribution_Trans"
		}, 
		"18": {
			"phases": "ABCN", 
			"name": "n630", 
			"object": "node", 
			"voltage_B": "-1200.8886-2080.000j", 
			"voltage_C": "-1200.8886+2080.000j", 
			"voltage_A": "2401.7771", 
			"nominal_voltage": "2401.7771"
		}, 
		"31": {
			"parent": "house1", 
			"name": "convenienceLoads1", 
			"power_fraction": "0.100000", 
			"object": "ZIPload", 
			"current_fraction": "0.100000", 
			"base_power": "plug1*2.477490", 
			"groupid": "plugload", 
			"current_pf": "0.950000", 
			"power_pf": "0.950000", 
			"impedance_fraction": "0.800000", 
			"impedance_pf": "0.950000"
		}, 
		"30": {
			"schedule_skew": "-810", 
			"tank_volume": "50", 
			"name": "waterheater1", 
			"parent": "house1", 
			"object": "waterheater", 
			"heating_element_capacity": "4.8 kW", 
			"thermostat_deadband": "2.9", 
			"location": "INSIDE", 
			"demand": "water14*1", 
			"tank_setpoint": "136.8", 
			"tank_UA": "2.4", 
			"temperature": "135"
		}, 
		"34": {
			"parent": "house1", 
			"name": "fan1", 
			"power_fraction": "0.013500", 
			"object": "ZIPload", 
			"current_fraction": "0.253400", 
			"base_power": "fan1*0.106899", 
			"groupid": "fan", 
			"current_pf": "0.950000", 
			"power_pf": "-1.000000", 
			"impedance_fraction": "0.733200", 
			"impedance_pf": "0.970000"
		}, 
		"33": {
			"parent": "house1", 
			"name": "television1", 
			"power_fraction": "0.998700", 
			"object": "ZIPload", 
			"current_fraction": "0.039600", 
			"base_power": "television5*0.200598", 
			"groupid": "TV", 
			"current_pf": "-0.540000", 
			"power_pf": "-1.000000", 
			"impedance_fraction": "-0.038300", 
			"impedance_pf": "0.610000"
		}, 
		"32": {
			"parent": "house1", 
			"name": "lights1", 
			"power_fraction": "0.003200", 
			"object": "ZIPload", 
			"current_fraction": "0.425700", 
			"base_power": "lights1*1.616013", 
			"groupid": "lights", 
			"current_pf": "-1.000000", 
			"power_pf": "1.000000", 
			"impedance_fraction": "0.571100", 
			"impedance_pf": "1.000000"
		}
	},
	"attachments": {
		"climate.tmy2":open(__metaModel__._omfDir + "/data/Climate/KY-LEXINGTON.tmy2").read(),
		"schedules.glm":open(__metaModel__._omfDir + "/schedules.glm").read()
	}
}

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	try:
		# Set up GLM with correct time and recorders:
		omd = json.load(open(pJoin(modelDir,'feeder.omd')))
		tree = omd.get('tree',{})
		feeder.attachRecorders(tree, "CollectorVoltage", None, None)
		feeder.attachRecorders(tree, "Climate", "object", "climate")
		feeder.attachRecorders(tree, "OverheadLosses", None, None)
		feeder.attachRecorders(tree, "UndergroundLosses", None, None)
		feeder.attachRecorders(tree, "TriplexLosses", None, None)
		feeder.attachRecorders(tree, "TransformerLosses", None, None)
		feeder.groupSwingKids(tree)
		feeder.adjustTime(tree, 120, 'hours', '2011-01-01')
		# Run GridLAB-D
		startTime = dt.datetime.now()
		rawOut = gridlabd.runInFilesystem(tree, attachments=omd.get('attachments',{}), workDir=modelDir)
		# Clean the output.
		cleanOut = {}
		# Std Err and Std Out
		cleanOut['stderr'] = rawOut['stderr']
		cleanOut['stdout'] = rawOut['stdout']
		# Time Stamps
		for key in rawOut:
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
				cleanOut['climate']['Rain Fall (in/h)'] = rawOut[key].get('rainfall')
				cleanOut['climate']['Wind Speed (m/s)'] = rawOut[key].get('wind_speed')
				cleanOut['climate']['Temperature (F)'] = rawOut[key].get('temperature')
				cleanOut['climate']['Snow Depth (in)'] = rawOut[key].get('snowdepth')
				cleanOut['climate']['Direct Normal (W/sf)'] = rawOut[key].get('solar_direct')
				climateWbySFList= rawOut[key].get('solar_global')
				#converting W/sf to W/sm
				climateWbySMList= [x*10.76392 for x in climateWbySFList]
				cleanOut['climate']['Global Horizontal (W/sm)']=climateWbySMList			
		# Voltage Band
		if 'VoltageJiggle.csv' in rawOut:
			cleanOut['allMeterVoltages'] = {}
			cleanOut['allMeterVoltages']['Min'] = [float(i / 2) for i in rawOut['VoltageJiggle.csv']['min(voltage_12.mag)']]
			cleanOut['allMeterVoltages']['Mean'] = [float(i / 2) for i in rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)']]
			cleanOut['allMeterVoltages']['StdDev'] = [float(i / 2) for i in rawOut['VoltageJiggle.csv']['std(voltage_12.mag)']]
			cleanOut['allMeterVoltages']['Max'] = [float(i / 2) for i in rawOut['VoltageJiggle.csv']['max(voltage_12.mag)']]
		# Dump the results.
		endTime = dt.datetime.now()
		inputDict["runTime"] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
		with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
			json.dump(cleanOut, outFile, indent=4)
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

def cancel(modelDir):
	''' Voltage drop runs so fast it's pointless to cancel a run. '''
	pass

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"user": "admin",
		"layoutAlgorithm": "geospatial",
		"simLength":120,
		"simLengthUnits":"hours"
	}
	creationCode = __metaModel__.new(modelDir, defaultInputs)
	try:
		with open(modelDir + "/feeder.omd","w") as feederFile:
			json.dump(circuitModel, feederFile, indent=4)
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
	renderAndShow(template, modelName)
	# Run the model.
	run(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(template, modelName, modelDir=modelLoc)
 	# # Delete the model.
 	# time.sleep(2)
 	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
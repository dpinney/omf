''' A model skeleton for future models: Calculates the sum of two integers. '''

import warnings
# warnings.filterwarnings("ignore")
import csv
import shutil, datetime
from pathlib import Path
import plotly
import plotly.graph_objs as go

# OMF imports
#from omf import feeder
#from omf.models.voltageDrop import drawPlot
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

#import omf.solvers.reopt_jl as reopt
import omf.solvers.der_cam as dercam
import omf.solvers.PowerModelsONM as pmonm
import omf.solvers.protsetopt as pso

import omf.models.microgridDesign as microgridDesign


# Model metadata
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	run_reopt = inputDict.get("run_reopt")
	run_dercam = inputDict.get("run_dercam")
	run_pmonm = inputDict.get("run_pmonm")
	run_pso = inputDict.get("run_pso")
	outData["run_reopt"] = run_reopt
	outData["run_dercam"] = run_dercam
	outData["run_pmonm"] = run_pmonm
	outData["run_pso"] = run_pso

	### reopt_jl
	if run_reopt:
		reoptInputs = inputDict.get("reopt_jl")
		reoptOutData = microgridDesign.work(modelDir,reoptInputs)
		outData["reoptOutData"] = reoptOutData 
	
	### der_cam	
	if run_dercam:
		dercamInputs = inputDict.get("dercam")
		apiKey = dercamInputs["api_key"]
		hasModelFile = dercamInputs["hasModelFile"]
		if hasModelFile:
			modelFile = dercamInputs["modelFile"]
			dercam.run(modelDir, modelFile=modelFile, apiKey=apiKey)
		else:
			dercam.run(modelDir, reoptFile="Scenario_Test_POST.json", apiKey=apiKey)
		dercamOutData = {}
		currentHeader = ""
		currentDict = {}
		with open(pJoin(modelDir,"results.csv")) as f:
			dercam_csv = csv.reader(f)
			for row in dercam_csv:
				# checks for header rows 
				if len(row) >= 1 and len(row[0]) > 1 and '+' in row[0]:
					if currentHeader != "" and currentDict != {}:
						dercamOutData[currentHeader] = currentDict
					currentHeader = row[0]
					remove_chars = '+ '
					for char in remove_chars:
						currentHeader = currentHeader.replace(char, '')
					currentDict = {}
				# adds key-value pair to currentDict otherwise
				elif len(row) > 1:
					val = row[0]
					val = val.replace(" ","")
					if len(row) == 2 or (len(row) == 3 and (row[2] == "NA" or row[1] == row[2])):
						currentDict[val] = row[1]
					else:
						currentDict[val] = row[1:]

		outData["dercamOutData"] = dercamOutData
		#plots/graphs to make:

	#to figure out: what data from reopt/dercam goes into pmonm?

	### PowerModelsONM
	if run_pmonm:
		pmonmInputs = inputDict.get("pmonm")
		if not pmonm.check_instantiated():
			pmonm.install_onm()
		pmonmCircuit = pmonmInputs.get("circuitFile")
		pmonmSettings = pmonmInputs.get("settingsFile")
		pmonmEvents = pmonmInputs.get("eventsFile")
		if pmonmSettings == "":
			settingsInputs = pmonmInputs.get("settingsInputs")
			settingsPath = pJoin(modelDir,"pmonm_settings.json")
			settingsInputs["settingsPath"] = settingsPath
			settingsInputs["circuitPath"] = pmonmCircuit
			pmonm.build_settings_file(**settingsInputs)
		else:
			settingsPath = pmonmSettings
		if pmonmEvents == "":
			eventsInputs = pmonmInputs.get("eventsInputs")
			eventsPath = pJoin(modelDir,"pmonm_events.json")
			eventsInputs["eventsPath"] = eventsPath
			eventsInputs["circuitPath"] = pmonmCircuit
			pmonm.build_events_file(**eventsInputs)
		else:
			eventsPath = pmonmEvents
		pmonmOut = pJoin(modelDir,"pmonm_output.json")
		pmonm.run_onm(circuitPath=pmonmCircuit, settingsPath=settingsPath, eventsPath=eventsPath, outputPath=pmonmOut)
		with open(pmonmOut) as j:
			pmonmOutData = json.load(j)
		outData["pmonmOutData"] = pmonmOutData
		#plots/graphs to make
		#

	#to figure out: how to parse pmonm "Protection Settings" output into pso 
	# => convert to dss file somehow? not needed?
	
	### ProtectionSettingsOptimizer
	if run_pso:
		psoInputs = inputDict.get("pso")
		del psoInputs["circuitFile"]
		psoInputs["testPath"] = psoInputs["circuitPath"]
		psoInputs["testFile"] = psoInputs["circuitFileName"]
		del psoInputs["circuitPath"]
		del psoInputs["circuitFileName"]
		pso.run(**psoInputs)
		with open(pJoin(psoInputs["testPath"],"settings_rso_out.json")) as j:
			psoSettings = json.load(j)
		with open(pJoin(psoInputs["testPath"],"old_info_rso_out.json")) as j:
			psoOldInfo = json.load(j)
		outData["psoSettings"] = psoSettings
		outData["psoOldInfo"] = psoOldInfo

	#to figure out : which solvers can run in different threads/subprocesses?

	#making PowerModelsONM output graphs :
	#todo: outData["Protection settings"]["settings"] should contain key output (not showing anything with current test files)
	def makeGridLine(x,y,color,name):
			plotLine = go.Scatter(
				x = x, 
				y = y,
				line = dict( color=(color)),
				name = name,
				hoverlabel = dict(namelength = -1),
				showlegend=True
			)
			return plotLine
	
	plotlyLayout = go.Layout(
			width=1000,
			height=375,
			legend=dict(
				x=0,
				y=1.25,
				orientation="h")
			)
	
	x = outData['pmonmOutData']['Simulation time steps']
	plotData = []
	pmonm_voltages = outData["pmonmOutData"]["Voltages"]
	min_voltage = makeGridLine(x, pmonm_voltages["Min voltage (p.u.)"],'blue','Min. Voltage')
	plotData.append(min_voltage)
	max_voltage = makeGridLine(x, pmonm_voltages["Max voltage (p.u.)"],'red','Max. Voltage')
	plotData.append(max_voltage)
	mean_voltage = makeGridLine(x, pmonm_voltages["Mean voltage (p.u.)"],'green','Mean Voltage')
	plotData.append(mean_voltage)
	plotlyLayout['yaxis'].update(title='Voltage (p.u.)')
	plotlyLayout['xaxis'].update(title='Simulation Time Steps')
	outData["pmonmVoltageData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["pmonmVoltageLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

	plotData = []
	storage_soc = makeGridLine(x, outData['pmonmOutData']['Storage SOC (%)'],'red','Storage SOC')
	plotData.append(storage_soc)
	plotlyLayout['yaxis'].update(title='SOC (%)')
	plotlyLayout['xaxis'].update(title='Simulation Time Steps')
	outData["pmonmStorageSOCData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["pmonmStorageSOCLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

	pmonm_load_served = outData['pmonmOutData']['Load served']
	plotData = []
	microgridCustomers = makeGridLine(x,pmonm_load_served['Microgrid customers (%)'],'blue','Microgrid customers')
	plotData.append(microgridCustomers)
	totalLoad = makeGridLine(x,pmonm_load_served['Total load (%)'],'purple','Total load')
	plotData.append(totalLoad)
	bonusLoadViaMicrogrid = makeGridLine(x,pmonm_load_served['Bonus load via microgrid (%)'],'brown','Bonus load via microgrid')
	plotData.append(bonusLoadViaMicrogrid)
	feederCustomers = makeGridLine(x,pmonm_load_served['Feeder customers (%)'],'yellow','Feeder customers')
	plotData.append(feederCustomers)
	feederLoad = makeGridLine(x,pmonm_load_served['Feeder load (%)'],'red','Feeder load')
	plotData.append(feederLoad)
	totalCustomers = makeGridLine(x,pmonm_load_served['Total customers (%)'],'green','Total customers')
	plotData.append(totalCustomers)
	microgridLoad = makeGridLine(x,pmonm_load_served['Microgrid load (%)'],'gray','Microgrid load')
	plotData.append(microgridLoad)
	bonusCustomersViaMicrogrid = makeGridLine(x,pmonm_load_served['Bonus customers via microgrid (%)'],'orange','Bonus customers via microgrid (%)')
	plotData.append(bonusCustomersViaMicrogrid)
	plotlyLayout['yaxis'].update(title='Load Served (%)')
	plotlyLayout['xaxis'].update(title='Simulation Time Steps')
	outData["pmonmLoadServedData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["pmonmLoadServedLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

	pmonm_generator_profiles = outData['pmonmOutData']["Generator profiles"]
	plotData = []
	diesel_dg = makeGridLine(x,pmonm_generator_profiles['Diesel DG (kW)'],'red','Diesel DG')
	plotData.append(diesel_dg)
	energy_storage = makeGridLine(x,pmonm_generator_profiles['Energy storage (kW)'],'green','Energy storage')
	plotData.append(energy_storage)
	solar_dg = makeGridLine(x,pmonm_generator_profiles['Solar DG (kW)'],'orange','Solar DG')
	plotData.append(solar_dg)
	grid_mix = makeGridLine(x,pmonm_generator_profiles['Grid mix (kW)'],'blue','Grid mix')
	plotData.append(grid_mix)
	plotlyLayout['yaxis'].update(title='(kW)')
	plotlyLayout['xaxis'].update(title='Simulation Time Steps')
	outData["pmonmGeneratorProfilesData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["pmonmGeneratorProfilesLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

	#to potentially add: "Device action timeline"

	#outData["output"] = 
	# Model operations typically ends here.
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user" : "admin",
		"modelType": modelName,
		"created":str(datetime.datetime.now()),
		#"use_cache": True,
		"run_reopt": True,
		"run_dercam": True,
		"run_pmonm": True,
		"run_pso": True
	}

	#saving solvers' default inputs to sub-dictionaries in defaultInputs (todo: test)
 
	##### reopt_jl
	fName = "input - 200 Employee Office, Springfield Illinois, 2001.csv"
	with open(pJoin(omf.omfDir, "static", "testFiles", fName)) as f:
		load_shape = f.read()
	cfName = "critical_load_test.csv"
	with open(pJoin(omf.omfDir, "static", "testFiles", cfName)) as f:
		crit_load_shape = f.read()
	reoptDefaultInputs = {
		"loadShape" : load_shape,
		"criticalLoadShape" : crit_load_shape,
		"solar" : "on",
		"wind" : "off",
		"battery" : "on",
		"fileName" : fName,
		"criticalFileName" : cfName,
		"latitude" : '39.7817',
		"longitude" : '-89.6501',
		"year" : '2017',
		"analysisYears" : '25',
		"discountRate" : '0.083', 
        "solverTolerance": "0.05", 
		"maxRuntimeSeconds": "240",
		"energyCost" : "0.1",
		"demandCost" : '20',
		"urdbLabelSwitch": "off",
		"urdbLabel" : '5b75cfe95457a3454faf0aea',
		"wholesaleCost" : "0.034",
		"omCostEscalator" : "0.025",
		"solarMacrsOptionYears": "5",
		"windMacrsOptionYears": "5",
		"batteryMacrsOptionYears": "7",
		"dieselMacrsOptionYears": 0,
		"solarItcPercent": "0.26",
		"windItcPercent": "0.26",
		"batteryItcPercent": 0,
		"solarCost" : "1600",
		"windCost" : "4898",
		"batteryPowerCost" : "840",
		"batteryCapacityCost" : "420",
		"batteryPowerCostReplace" : "410",
		"batteryCapacityCostReplace" : "200",
		"batteryPowerReplaceYear": '10',
		"batteryCapacityReplaceYear": '10',
		"dieselGenCost": "500",
		"solarMin": 0,
		"windMin": 0,
		"batteryPowerMin": 0,
		"batteryCapacityMin": 0,
		"dieselMin": 0,
		"solarMax": "10000000",
		"windMax": "10000000",
		"batteryPowerMax": "1000000",
		"batteryCapacityMax": "1000000",
		"dieselMax": "100000",
		"solarExisting": 0,
		"outage_start_hour": "500",
		"outageDuration": "24",
		"fuelAvailable": "20000",
		"genExisting": 0,
		"minGenLoading": "0.3",
		"dieselFuelCostGal": "3", 
		"dieselCO2Factor": 22.4, 
		"dieselOMCostKw": 10, 
		"dieselOMCostKwh": 0, 
		"value_of_lost_load": "100",
		"solarCanCurtail": True,
		"solarCanExport": True,
		"dieselOnlyRunsDuringOutage": True
	} #get from microgridDesign.new(modelDir) instead if possible? 
	#alternative idea: set defaults to lehigh4mgs reopt_mg3
	defaultInputs["reopt_jl"] = reoptDefaultInputs
	
	### DER-CAM
	dercamInputs = { 
		"api_key": "",
		"hasModelFile": True, #False,
		"modelFile": pJoin(__neoMetaModel__._omfDir, "solvers","der_cam","testFiles","test.xlsx"), #"",
		"modelFileName": "test.xlsx" #""
	}
	defaultInputs["dercam"] = dercamInputs
 
 	### PowerModelsONM
	circuitFileName = "circuit_plus_mgAll.clean.dss"
	circuitFile = pJoin(__neoMetaModel__._omfDir, "static", "testFiles", "lehigh4mgs", circuitFileName)
	settingsInputs = {
			"loadPrioritiesFile": "",
			"microgridTaggingFile": "",
			"max_switch_actions": 1,
			"vm_lb_pu": 0.9,
			"vm_ub_pu": 1.1,
			"sbase_default": 1000.0,
			"line_limit_mult":'Inf',
			"vad_deg":5.0, 
	}
	eventsInputs = {
			"custom_events_file":'',
			"default_switch_state": 'PMD.OPEN',
			"default_switch_dispatchable": 'PMD.NO',
			"default_switch_status": 'PMD.ENABLED'
	}
	#temporary test files
	#defaultPath = pJoin(__neoMetaModel__._omfDir, "static", "testFiles","lehigh4mgs")
	defaultPath = pJoin(__neoMetaModel__._omfDir, "static", "testFiles")
	defaultCircuitFile = "iowa240_dwp_22.dss" #"circuit_plus_mgAll_relays.dss"
	defaultSettingsFile = "iowa240_dwp_22.settings.json" #"circuit_plus_mgAll_relays.settings.json"
	defaultEventsFile = "iowa240_dwp_22.events.json" #"circuit_plus_mgAll_relays.events_prev.json"
	pmonmDefaultInputs = {
		"circuitFile": pJoin(defaultPath,defaultCircuitFile), #circuitFile,
		"circuitFileName": defaultCircuitFile, #circuitFileName
		#add other function inputs (for events & settings) as 'Advanced Options'?
		"buildSettingsFile": False, #True, #on switch (T/F) display settingsFile option (False) or settings file parameters (True)
		"buildEventsFile": False, #True,
		"settingsFile": pJoin(defaultPath, defaultSettingsFile), #"",
		"settingsFileName": defaultSettingsFile, #"",
		"eventsFile": pJoin(defaultPath,defaultEventsFile),
		"eventsFileName": defaultEventsFile,
		#for building settings file:
		"loadPrioritiesFileName": "",
		"microgridTaggingFileName": "",
		#settings file advanced options
		"settingsInputs": settingsInputs,
		#for building events file
		"custom_events_file_name": "",
		"eventsInputs": eventsInputs
	}
	defaultInputs["pmonm"] = pmonmDefaultInputs 

	### ProtectionSettingsOptimizer
	psoPath = pJoin(__neoMetaModel__._omfDir,"solvers","protsetopt","testFiles")
	psoDefaultInputs = { 
		"circuitPath": psoPath,
		"circuitFile": pJoin(psoPath,"IEEE34Test.dss"),
		"circuitFileName": "IEEE34Test.dss",
		"Fres": ['0.001','1'], #fault resistances to test
		"Fts": ['3ph','SLG','LL'], #supported fault types
		"Force_NOIBR": 1, 
		"enableIT": 0,
		"CTI": 0.25,
        "OTmax": 10,
		"type_select": False,
		"Fault_Res": ['R0_001','R1'],
		"Min_Ip": [0.1,0.1],
		"Substation_bus": 'sourcebus'
	} 
	defaultInputs["pso"] = psoDefaultInputs 

	return __neoMetaModel__.new(modelDir, defaultInputs)

def display_prev_results():
	modelLoc = Path(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	__neoMetaModel__.renderAndShow(modelLoc)

@neoMetaModel_test_setup
def _debugging():
	# Location
	modelLoc = Path(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()
	#display_prev_results()

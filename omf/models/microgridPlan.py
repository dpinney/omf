''' A model skeleton for future models: Calculates the sum of two integers. '''

import warnings
# warnings.filterwarnings("ignore")
import csv
import shutil, datetime
from pathlib import Path

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
		print("testing (remove): running reopt_jl")
		reoptInputs = inputDict.get("reopt_jl")
		reoptOutData = microgridDesign.work(modelDir,reoptInputs)
		outData["reoptOutData"] = reoptOutData 
	
	### der_cam	
	if run_dercam:
		print("testing (remove): running der_cam")
		dercamInputs = inputDict.get("dercam")
		apiKey = dercamInputs["api_key"]
		hasModelFile = dercamInputs["hasModelFile"]
		if hasModelFile:
			modelFile = dercamInputs["modelFile"]
			dercam.run(modelDir, modelFile=modelFile, apiKey=apiKey)
		else:
			dercam.run(modelDir, reoptFile="Scenario_Test_POST.json", apiKey=apiKey)
		dercamOutData = dict()
		with open(pJoin(modelDir,"results.csv")) as f:
			dercam_csv = csv.reader(f)
			for row in dercam_csv:
				if len(row) > 1: #row[0][0] != "+" and
					val = row[0].replace(" ","_")
					dercamOutData[val] = row[1]

		outData["dercamOutData"] = dercamOutData

	### PowerModelsONM
	if run_pmonm:
		print("testing (remove): running pmONM")
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
	
	
	### ProtectionSettingsOptimizer
	if run_pso:
		print("testing (remove): running pso")
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

	#todo: generate output tables / graphs for der-cam, pmonm, pso 

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
		"run_reopt": False,
		"run_dercam": False,
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
	defaultPath = pJoin(__neoMetaModel__._omfDir, "static", "testFiles")
	defaultCircuitFile = "iowa240_dwp_22.dss"
	defaultSettingsFile = "iowa240_dwp_22.settings.json"
	defaultEventsFile = "iowa240_dwp_22.events.json"
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

@neoMetaModel_test_setup
def _debugging(): #_test():
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
	#_test()

''' Performs a cost-benefit analysis for a utility or cooperative member interested in 
controlling behind-the-meter distributed energy resources (DERs).'''

import warnings
# warnings.filterwarnings("ignore")

import shutil, datetime, csv, json
from os.path import join as pJoin
import numpy as np
import pandas as pd

# OMF imports
from omf import feeder
from omf.models.voltageDrop import drawPlot
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.models import vbatDispatch as vb
from omf.solvers import reopt_jl

# Model metadata:
tooltip = ('The derUtilityCost model evaluates the financial costs of controlling behind-the-meter '
	'distributed energy resources (DERs) using the NREL renewable energy optimization tool (REopt) and '
	'the OMF virtual battery dispatch module (vbatDispatch).')
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def create_REopt_jl_jsonFile(modelDir, inputDict):

	## Site parameters
	latitude = float(inputDict['latitude'])
	longitude = float(inputDict['longitude'])
	urdbLabel = str(inputDict['urdbLabel'])
	year = int(inputDict['year'])

	## Energy technologies
	solar = inputDict['solar'] 
	generator = inputDict['generator']
	battery = inputDict['battery']

	## Load demand file and make it JSON ready
	with open(pJoin(modelDir, "demand.csv")) as loadFile:
		load = pd.read_csv(loadFile, header=None)
		load = load[0].values.tolist()
		

	"""
	## Financial and Load parameters
	energyCost = float(inputDict['energyCost'])
	demandCost = float(inputDict['demandCost'])
	wholesaleCost = float(inputDict['wholesaleCost'])
	lostLoadValue = float(inputDict['value_of_lost_load'])
	analysisYears = int(inputDict['analysisYears'])
	omCostEscalator = float(inputDict['omCostEscalator'])
	discountRate = float(inputDict['discountRate'])
	criticalLoadFactor = float(inputDict['criticalLoadFactor'])
	userCriticalLoadShape = True if inputDict['userCriticalLoadShape'] == "True" else False

	## Solar parameters
	solarCost = float(inputDict['solarCost'])
	solarMin = float(inputDict['solarMin'])
	if solar == 'off':
		solarMax = 0
	elif solar == 'on':
		solarMax = float(inputDict['solarMax'])
		solarExisting = float(inputDict['solarExisting'])

	solarCanExport = True if inputDict['solarCanExport'] == "True" else False
	solarCanCurtail = True if inputDict['solarCanCurtail'] == "True" else False
	solarMacrsOptionYears = int(inputDict['solarMacrsOptionYears'])
	solarItcpercent = float(inputDict['solarItcPercent'])

	## BESS parameters
	batteryPowerCost = float(inputDict['batteryPowerCost'])
	batteryCapacityCost = float(inputDict['batteryCapacityCost'])
	batteryPowerCostReplace = float(inputDict['batteryPowerCostReplace'])
	batteryCapacityCostReplace = float(inputDict['batteryCapacityCostReplace'])
	batteryPowerReplaceYear = float(inputDict['batteryPowerReplaceYear'])
	batteryCapacityReplaceYear = float(inputDict['batteryCapacityReplaceYear'])
	batteryPowerMin = float(inputDict['batteryPowerMin'])
	batteryCapacityMin = float(inputDict['batteryCapacityMin'])
	batteryMacrsOptionYears = int(inputDict['batteryMacrsOptionYears'])
	batteryItcPercent = float(inputDict['batteryItcPercent'])

	## Diesel Generator paramters
	dieselGenCost = float(inputDict['dieselGenCost'])
	dieselMacrsOptionYears = int(inputDict['dieselMacrsOptionYears'])
	dieselMax = float(inputDict['dieselMax'])
	dieselMin = float(inputDict['dieselMin'])
	dieselFuelCostGal = float(inputDict['dieselFuelCostGal'])
	dieselCO2Factor = float(inputDict['dieselCO2Factor'])
	dieselOMCostKw = float(inputDict['dieselOMCostKw'])
	dieselOMCostKwh = float(inputDict['dieselOMCostKwh'])
	dieselOnlyRunsDuringOutage = True if inputDict['dieselOnlyRunsDuringOutage'] == "True" else False

	## Outage/resilience paramters
	outage_start_hour = int(inputDict['outage_start_hour'])
	outage_duration = int(inputDict['outageDuration'])
	outage_end_hour = outage_start_hour + outage_duration

	scenario = {
		"Site": {
			"latitude": latitude,
			"longitude": longitude
		},
		"ElectricTariff": {
			"wholesale_rate": wholesaleCost
		},
		"ElectricLoad": {
			"loads_kw": jsonifiableLoad,
			"year": year
		},
		"Financial": {
			"value_of_lost_load_per_kwh": value_of_lost_load,
			"analysis_years": analysisYears,
			"om_cost_escalation_rate_fraction": omCostEscalator,
			"offtaker_discount_rate_fraction": discountRate
		},
		"PV": {
			"installed_cost_per_kw": solarCost,
			"min_kw": solarMin,
			"max_kw": solarMax,
			"can_export_beyond_nem_limit": solarCanExport,
			"can_curtail": solarCanCurtail,
			"macrs_option_years": solarMacrsOptionYears,
			"federal_itc_fraction": solarItcPercent
		},
		"ElectricStorage": {
			"installed_cost_per_kwh": batteryPowerCost,
			"installed_cost_per_kwh": batteryCapacityCost,
			"replace_cost_per_kw": batteryPowerCostReplace,
			"replace_cost_per_kwh": batteryCapacityCostReplace,
			"inverter_replacement_year": batteryPowerReplaceYear,
			"battery_replacement_year": batteryCapacityReplaceYear,
			"min_kw": batteryPowerMin,
			"min_kwh": batteryCapacityMin,
			"macrs_option_years": batteryMacrsOptionYears,
			"total_itc_fraction": batteryItcPercent
		},
		"Generator": {
			"installed_cost_per_kw": dieselGenCost,
			"only_runs_during_grid_outage": dieselOnlyRunsDuringOutage,
			"macrs_option_years": dieselMacrsOptionYears
		}
	}
	"""

	scenario = {
		"Site": {
			"latitude": latitude,
			"longitude": longitude
		},
		"ElectricTariff": {
			"urdb_label": urdbLabel
		},
		"ElectricLoad": {
			"loads_kw": load,
			"year": year
		},
		"PV": {
		},
	}

	with open(pJoin(modelDir, "Scenario_test.json"), "w") as jsonFile:
		json.dump(scenario, jsonFile)

	return scenario

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	# Delete output file every run if it exists
	out = {}

	## Setting up the demand file (hourly kWh) and temperature file
	with open(pJoin(modelDir, 'demand.csv'), 'w') as f:
		f.write(inputDict['demandCurve'].replace('\r', ''))
	with open(pJoin(modelDir, 'demand.csv'), newline='') as f:
		demand = [float(r[0]) for r in csv.reader(f)]
		assert len(demand) == 8760

	with open(pJoin(modelDir, 'temp.csv'), 'w') as f:
		lines = inputDict['tempCurve'].split('\n')
		out["tempData"] = [float(x) if x != '999.0' else float(inputDict['setpoint']) for x in lines if x != '']
		correctData = [x+'\n' if x != '999.0' else inputDict['setpoint']+'\n' for x in lines if x != '']
		f.write(''.join(correctData))
	assert len(correctData) == 8760
	
	outage = True if inputDict["outage"] == "on" else False

	## Create REopt input file
	create_REopt_jl_jsonFile(modelDir, inputDict)

	## Run REopt.jl
	reopt_jl.run_reopt_jl(modelDir, "Scenario_test.json")
	with open(pJoin(modelDir, 'results.json')) as jsonFile:
		results = json.load(jsonFile)
		
	## Output data
	out['solar'] = inputDict['solar']
	out['generator'] = inputDict['generator'] ## TODO: make generator switch on only during outage?
	out['battery'] = inputDict['battery']
	out['year'] = inputDict['year']
	out['urdbLabel'] = inputDict['urdbLabel']
	out['demandCost'] = results['ElectricTariff']['lifecycle_demand_cost_after_tax']
	out['powerPVToGrid'] = results['PV']['electric_to_grid_series_kw']#['year_one_to_grid_series_kw']


	## Run REopt and gather outputs for vbatDispath
	## TODO: Create a function that will gather the urdb label from a user provided location (city,state)
	#RE.run_reopt_jl(modelDir,inputFile,outages)

	#RE.run_reopt_jl(path="/Users/astronobri/Documents/CIDER/reopt/inputs/", inputFile="UP_PV_outage_1hr.json", outages=outage) # UP coop PV 
	#RE.run_reopt_jl(path="/Users/astronobri/Documents/CIDER/reopt/inputs/", inputFile="residential_input.json", outages=True) # UP coop PV 

	#with open(pJoin(modelDir, 'results.json')) as jsonFile:
		#results = json.load(jsonFile)

	#getting REoptInputs to access default input values more easily 
	#with open(pJoin(modelDir, 'REoptInputs.json')) as jsonFile:
		#reopt_inputs = json.load(jsonFile)

	if (outage):
		with open(pJoin(modelDir, 'resultsResilience.json')) as jsonFile:
			resultsResilience = json.load(jsonFile)
	
	## Run vbatDispatch with outputs from REopt
	#VB.new(modelDir)
	#modelDir = "/Users/astronobri/Documents/CIDER/omf/omf/data/Model/admin/meowtest"

	test = vb.work(modelDir,inputDict)
	with open('/Users/astronobri/Documents/CIDER/jsontestfile.json', "w") as fp:
		json.dump(test, fp) 

	#outData['stdout'] = test
	#print(modDirvbatt)
	#vbattWork_out = vb.work(modelDir,vbattNew_out[1])

	# Model operations typically ends here.
	# Stdout/stderr.
	out["stdout"] = "Success"
	out["stderr"] = ""
	return out

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_1yr_Load.csv")) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_1yr_Temp.csv")) as f:
		temp_curve = f.read()

	defaultInputs = {
		"user" : "admin",
		"modelType": modelName,
		"latitude" : '39.7392358', 
		"longitude" : '-104.990251',
		#"latitude" :  '39.532165', ## Rivesville, WV
		#"longitude" : '-80.120618',
		"year" : '2018',
		"analysis_years" : 25, 
		#"urdbLabel" : '612ff9c15457a3ec18a5f7d3', ## Brighton, CO - United Power 
		"urdbLabel" : '643476222faee2f0f800d8b1', ## Rivesville, WV - Monongahela Power
		"demandCurve": demand_curve,
		"tempCurve": temp_curve,
		"outage": False,
		"solar" : "on",
		"battery" : "on",
		"generator" : "off",
		"created":str(datetime.datetime.now()),
		"load_type": "2",
		"number_devices": "1",
		"power": "5.6",
		"capacitance": "2",
		"resistance": "2",
		"cop": "2.5",
		"setpoint": "19.5",
		"deadband": "0.625",
		"demandChargeCost":"25",
		"electricityCost":"0.16",
		"projectionLength":"25",
		"discountRate":"2",
		"unitDeviceCost":"150",
		"unitUpkeepCost":"5",
		#"fileName": "Texas_1yr_Load.csv",
		#"tempFileName": "Texas_1yr_Temp.csv",
		#"fileName": "/Users/astronobri/Documents/CIDER/reopt/inputs/residential_PV_load.csv", 
		"fileName": "/Users/astronobri/Documents/CIDER/UP-slide18/3reopt-web-residential-load-profile.csv",
		"tempFileName": "/Users/astronobri/Desktop/extended_temperature_data.csv",
		"modelType": modelName
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def _tests():
	## Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated_Testing_of_" + modelName)
	## Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		## No previous test results.
		pass
	## Create New.
	new(modelLoc)
	## Pre-run.
	#__neoMetaModel__.renderAndShow(modelLoc)
	## Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	## Show the output.
	#__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
	#pass


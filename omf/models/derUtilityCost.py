''' Performs a cost-benefit analysis for a utility or cooperative member interested in 
controlling behind-the-meter distributed energy resources (DERs).'''

## TODO: check out gridlabMulti.py, cvrDynamic.py, demandResponse.py, 
## vbatDispatch.py, solarEngineering.py for potential display and plot feautures 

import warnings
# warnings.filterwarnings("ignore")

import shutil, datetime, csv, json
from os.path import join as pJoin
import numpy as np
import pandas as pd

# OMF imports
from omf.models.voltageDrop import drawPlot
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.models import vbatDispatch as vb
from omf.models import derConsumer
from omf.solvers import reopt_jl

# Model metadata:
tooltip = ('The derUtilityCost model evaluates the financial costs of controlling behind-the-meter '
	'distributed energy resources (DERs) using the NREL renewable energy optimization tool (REopt) and '
	'the OMF virtual battery dispatch module (vbatDispatch).')
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False


def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	# Delete output file every run if it exists
	outData = {}

	## Create REopt input file
	reopt_input_scenario = derConsumer.create_REopt_jl_jsonFile(modelDir, inputDict)

	## NOTE: This code will be used once reopt_jl is working
	## Run REopt.jl 
	#outage_flag = inputDict['outage'] #TODO: Add outage option to HTML
	#reopt_jl.run_reopt_jl(modelDir, reopt_input_scenario, outages=outage_flag)

	## NOTE: This code is temporary
	## Read in a static REopt test file
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","utility_reopt_results.json")) as f:
		reoptResults = pd.json_normalize(json.load(f))
		print('Successfully read in REopt test file. \n')

	## Create timestamp array from REopt input information
	year = reoptResults['inputs.ElectricLoad.year'][0]
	arr_size = np.size(reoptResults['outputs.ElectricUtility.electric_to_load_series_kw'][0])
	timestamps = derConsumer.create_timestamps(start_time=f'{year}-01-01', end_time=f'{year}-12-31 23:00:00', arr_size=arr_size)

	## Convert temperature data from str to float
	temperatures = [float(value) for value in inputDict['tempCurve'].split('\n') if value.strip()]
	demand = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()])

	## Run vbatDispatch
	vbatResults = vb.work(modelDir,inputDict)
	with open(pJoin(modelDir, 'vbatResults.json'), 'w') as jsonFile:
		json.dump(vbatResults, jsonFile)
	outData.update(vbatResults) ## Update output file with vbat results


	## Output data
	#outData['solar'] = inputDict['solar']
	#outData['generator'] = inputDict['generator'] ## TODO: make generator switch on only during outage?
	#outData['battery'] = inputDict['battery']
	#outData['year'] = inputDict['year']
	#outData['urdbLabel'] = inputDict['urdbLabel']
	#out['demandCost'] = results['ElectricTariff']['lifecycle_demand_cost_after_tax']
	#out['powerPVToGrid'] = results['PV']['electric_to_grid_series_kw']#['year_one_to_grid_series_kw']

	## Run REopt and gather outputs for vbatDispath
	## TODO: Create a function that will gather the urdb label from a user provided location (city,state)
	#RE.run_reopt_jl(modelDir,inputFile,outages)

	#reopt_jl.run_reopt_jl(path="/Users/astronobri/Documents/CIDER/reopt/inputs/", inputFile="UP_PV_outage_1hr.json", outages=outage) # UP coop PV 
	#reopt_jl.run_reopt_jl(path="/Users/astronobri/Documents/CIDER/reopt/inputs/", inputFile=pJoin(__neoMetaModel__._omfDir,"static","testFiles","residential_input.json"), outages=True) # residential PV 

	
	inputDict['outage'] = False ##NOTE: Temporary line to disable the following outage resilience code
	if (inputDict['outage']):
		try:
			with open(pJoin(modelDir, 'resultsResilience.json')) as jsonFile:
				resultsResilience = json.load(jsonFile)
				outData.update(resultsResilience) ## Update out file with resilience results
		except FileNotFoundError:
			results_file = pJoin(modelDir, 'resultsResilience.json')
			print(f"File '{results_file}' not found.")
			raise
	
	


	# Model operations typically ends here.
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","utility_2018_kW_load.csv")) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","utility_CO_2018_temperatures.csv")) as f:
		temp_curve = f.read()

	defaultInputs = {
		## OMF inputs:
		"user" : "admin",
		"modelType": modelName,
		"created":str(datetime.datetime.now()),

		## REopt inputs:
		"latitude" : '39.7392358', 
		"longitude" : '-104.990251',
		"year" : '2018',
		"analysis_years" : '25', 
		"urdbLabel" : '612ff9c15457a3ec18a5f7d3', ## Brighton, CO - United Power 
		"fileName": "utility_2018_kW_load.csv",
		"tempFileName": "utility_CO_2018_temperatures.csv",
		"demandCurve": demand_curve,
		"tempCurve": temp_curve,
		"outage": True,
		"outage_start_hour": '2100',
		"outage_duration": '3',
		"solar" : "on",
		"battery" : "on",
		"generator" : "off",

		## vbatDispatch inputs:
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
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def _debugging():
	## Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	## Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		## No previous test results.
		pass
	## Create New.
	new(modelLoc)
	## Pre-run.
	__neoMetaModel__.renderAndShow(modelLoc)
	## Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	## Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()
	pass


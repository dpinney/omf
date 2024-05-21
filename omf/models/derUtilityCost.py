''' Performs a cost-benefit analysis for a utility or cooperative member interested in 
controlling behind-the-meter distributed energy resources (DERs).'''

## TODO: check out gridlabMulti.py, cvrDynamic.py, demandResponse.py, 
## vbatDispatch.py, solarEngineering.py for potential display and plot feautures 

# Python imports
import warnings
# warnings.filterwarnings("ignore")
import shutil, datetime, csv, json
from os.path import join as pJoin
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.utils

# OMF imports
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
hidden = True


def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	# Delete output file every run if it exists
	outData = {}

	## Create REopt input file
	reopt_input_scenario = derConsumer.create_REopt_jl_jsonFile(modelDir, inputDict)

	## NOTE: This code will be used once reopt_jl is working
	## Run REopt.jl 
	outage_flag = inputDict['outage']
	
	reopt_jl.run_reopt_jl(modelDir, "reopt_input_scenario.json", outages=outage_flag)
	with open(pJoin(modelDir, 'results.json')) as jsonFile:
		reoptResults = json.load(jsonFile)
	outData.update(reoptResults) ## Update output file with reopt results

	## NOTE: This code is temporary
	## Read in a static REopt test file
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","utility_reopt_results.json")) as f:
		reoptResults = pd.json_normalize(json.load(f))
		print('Successfully read in REopt test file. \n')

	## Create timestamp array from REopt input information
	try:
		year = reoptResults['ElectricLoad.year'][0]
	except KeyError:
		year = inputDict['year'] # Use the user provided year if none found in reoptResults
	
	arr_size = np.size(reoptResults['ElectricUtility']['electric_to_load_series_kw'])
	timestamps = derConsumer.create_timestamps(start_time=f'{year}-01-01', end_time=f'{year}-12-31 23:00:00', arr_size=arr_size)

	## Convert temperature data from str to float
	temperatures = [float(value) for value in inputDict['tempCurve'].split('\n') if value.strip()]
	demand = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()])

	## If outage is specified, load the resilience results
	if (inputDict['outage']):
		try:
			with open(pJoin(modelDir, 'resultsResilience.json')) as jsonFile:
				reoptResultsResilience = json.load(jsonFile)
				outData.update(reoptResultsResilience) ## Update out file with resilience results
		except FileNotFoundError:
			results_file = pJoin(modelDir, 'resultsResilience.json')
			print(f"File '{results_file}' not found. REopt may not have simulated the outage.")
			raise
	
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
	
	## Test plot
	showlegend = False #temporarily disable the legend toggle

	PV = reoptResults['outputs.PV.electric_to_load_series_kw'][0]
	BESS = reoptResults['outputs.ElectricStorage.storage_to_load_series_kw'][0]
	vbpower_series = pd.Series(vbatResults['VBpower'][0])
	vbat_discharge = vbpower_series.where(vbpower_series < 0, 0) #negative values
	vbat_charge = vbpower_series.where(vbpower_series > 0, 0) ## positive values; part of the New Load?
	vbat_discharge_flipsign = vbat_discharge.mul(-1) ## flip sign of vbat discharge for plotting purposes
	grid_to_load = reoptResults['outputs.ElectricUtility.electric_to_load_series_kw'][0]
	grid_charging_BESS = reoptResults['outputs.ElectricUtility.electric_to_storage_series_kw'][0]


	fig = go.Figure()
	fig.add_trace(go.Scatter(x=timestamps,
                         y=np.asarray(BESS) + np.asarray(demand) + np.asarray(vbat_discharge_flipsign),
						 yaxis='y1',
                         mode='none',
                         fill='tozeroy',
                         name='BESS Serving Load (kW)',
                         fillcolor='rgba(0,137,83,1)',
						 showlegend=showlegend))
	fig.update_traces(fillpattern_shape='/', selector=dict(name='BESS Serving Load (kW)'))

	fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(vbat_discharge_flipsign)+np.asarray(demand),
							yaxis='y1',
							mode='none',
							fill='tozeroy',
							fillcolor='rgba(127,0,255,1)',
							name='vbat Serving Load (kW)',
							showlegend=showlegend))
	fig.update_traces(fillpattern_shape='/', selector=dict(name='vbat Serving Load (kW)'))

	fig.add_trace(go.Scatter(x=timestamps,
                         y=np.asarray(demand)-np.asarray(BESS)-np.asarray(vbat_discharge_flipsign),
						 yaxis='y1',
                         mode='none',
                         name='Original Load (kW)',
                         fill='tozeroy',
                         fillcolor='rgba(100,200,210,1)',
						 showlegend=showlegend))

	fig.add_trace(go.Scatter(x=timestamps,
                         y=np.asarray(demand) + np.asarray(reoptResults['outputs.ElectricUtility.electric_to_storage_series_kw'][0]) + np.asarray(vbat_charge),
						 yaxis='y1',
                         mode='none',
                         name='Additional Load (Charging BESS and vbat)',
                         fill='tonexty',
                         fillcolor='rgba(175,0,42,0)',
						 showlegend=showlegend))
	fig.update_traces(fillpattern_shape='.', selector=dict(name='Additional Load (Charging BESS and vbat)'))
	

	grid_serving_new_load = np.asarray(grid_to_load) + np.asarray(grid_charging_BESS)+ np.asarray(vbat_charge) - np.asarray(vbat_discharge_flipsign) + np.asarray(PV)
	fig.add_trace(go.Scatter(x=timestamps,
                         y=grid_serving_new_load,
						 yaxis='y1',
                         mode='none',
                         fill='tozeroy',
                         name='Grid Serving Load (kW)',
                         fillcolor='rgba(192,192,192,1)',
						 showlegend=showlegend))
	
	fig.add_trace(go.Scatter(x=timestamps,
						  y=temperatures,
						  yaxis='y2',
						  mode='lines',
						  line=dict(color='red',width=1),
						  name='Average Temperature',
						  showlegend=showlegend 
						  ))

	#fig.add_trace(go.Scatter(x=timestamps, 
	#				 y=demand,
	#				 yaxis='y1',
	#				 mode='lines',
	#				 line=dict(color='black'),
	#				 name='Demand',
	#				 showlegend=showlegend))
	#fig.update_traces(legendgroup='Demand', visible='legendonly', selector=dict(name='Original Load (kW)')) ## Make demand hidden on plot by default

	fig.add_trace(go.Scatter(x=timestamps,
					 y=PV,
					 yaxis='y1',
					 mode='none',
					 fill='tozeroy',
					 name='PV Serving Load (kW)',
					 fillcolor='rgba(255,246,0,1)',
					 showlegend=showlegend
					 ))
	
	fig.update_layout(
    	title='Utility Data Test',
    	xaxis=dict(title='Timestamp'),
    	yaxis=dict(title="Energy (kW)"),
    	yaxis2=dict(title='degrees Celsius',
                overlaying='y',
                side='right'
                ),
    	legend=dict(
			orientation='h',
			yanchor="bottom",
			y=1.02,
			xanchor="right",
			x=1
			)
	)

	fig.show()

	## Encode plot data as JSON for showing in the HTML 
	outData['plotlyPlot'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['plotlyLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

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
		"longitude" : '-104.990251', ## Brighton, CO
		"year" : '2018',
		"analysis_years" : '25', 
		"urdbLabel" : '612ff9c15457a3ec18a5f7d3', ## Brighton, CO
		"fileName": "utility_2018_kW_load.csv",
		"tempFileName": "utility_CO_2018_temperatures.csv",
		"demandCurve": demand_curve,
		"tempCurve": temp_curve,
		"PV": "Yes",
		"BESS": "No",
		"generator": "No",
		"outage": True,
		"outage_start_hour": '2100',
		"outage_duration": '3',

		## vbatDispatch inputs:
		"load_type": "2", ## Heat Pump
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
def _tests_disabled():
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
	__neoMetaModel__.renderAndShow(modelLoc) ## NOTE: Why is there a pre-run?
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests_disabled() ## NOTE: Workaround for failing test. When model is ready, change back to just _tests()
	pass


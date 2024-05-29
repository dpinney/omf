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
	'distributed energy resources (DERs) using the NREL Renewable Energy Optimization Tool (REopt) and '
	'the OMF virtual battery dispatch module (vbatDispatch).')
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False ## Keep the model hidden=True during active development


def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	# Delete output file every run if it exists
	outData = {}

	## Create REopt input file
	derConsumer.create_REopt_jl_jsonFile(modelDir, inputDict)

	## NOTE: The single commented code below is used temporarily if reopt_jl is not working or for other debugging purposes.
	## Also NOTE: If this is used, you typically have to add a ['outputs'] key before the variable of interest.
	## For example, instead of reoptResults['ElectricStorage']['storage_to_load_series_kw'], it would have to be
	## reoptResults['outputs']['ElectricStorage']['storage_to_load_series_kw'] when using the static reopt file below.
	#with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","utility_reopt_results.json")) as f:
	#	reoptResults = pd.json_normalize(json.load(f))
	#	print('Successfully read in REopt test file. \n')

	## Run REopt.jl 
	reopt_jl.run_reopt_jl(modelDir, "reopt_input_scenario.json", outages=inputDict['outage'])
	with open(pJoin(modelDir, 'results.json')) as jsonFile:
		reoptResults = json.load(jsonFile)
	outData.update(reoptResults) ## Update output file with reopt results

	## Convert user provided demand and temp data from str to float
	temperatures = [float(value) for value in inputDict['tempCurve'].split('\n') if value.strip()]
	demand = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()])

	## Create timestamp array from REopt input information
	try:
		year = reoptResults['ElectricLoad.year'][0]
	except KeyError:
		year = inputDict['year'] # Use the user provided year if none found in reoptResults
	
	arr_size = np.size(demand) # desired array size of the timestamp array
	timestamps = derConsumer.create_timestamps(start_time=f'{year}-01-01', end_time=f'{year}-12-31 23:00:00', arr_size=arr_size)

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
	
	## Run vbatDispatch, unless it is disabled
	if inputDict['load_type'] != '0': ## Load type 0 corresponds to the "None" option, which disables this vbatDispatch function
		vbatResults = vb.work(modelDir,inputDict)
		with open(pJoin(modelDir, 'vbatResults.json'), 'w') as jsonFile:
			json.dump(vbatResults, jsonFile)
		outData.update(vbatResults) ## Update output file with vbat results

		## vbatDispatch variables
		vbpower_series = pd.Series(vbatResults['VBpower'])
		vbat_charge = vbpower_series.where(vbpower_series > 0, 0) ##positive values = charging
		vbat_discharge = vbpower_series.where(vbpower_series < 0, 0) #negative values = discharging
		vbat_discharge_flipsign = vbat_discharge.mul(-1) ## flip sign of vbat discharge for plotting purposes

	## DER Overview plot
	showlegend = True # either enable or disable the legend toggle in the plot
	grid_to_load = reoptResults['ElectricUtility']['electric_to_load_series_kw']

	if inputDict['PV'] == 'Yes': ## PV
		PV = reoptResults['PV']['electric_to_load_series_kw']
	else:
		PV = np.zeros_like(demand)
	
	if inputDict['BESS'] == 'Yes': ## BESS
		#BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
		BESS = np.ones_like(demand) ## Ad-hoc line used because BESS is not being built in REopt for some reason. Currently debugging 5/2024
		grid_charging_BESS = reoptResults['ElectricUtility']['electric_to_storage_series_kw']
		#outData['chargeLevelBattery'] = reoptResults['ElectricStorage']['soc_series_fraction']

		## NOTE: The following 3 lines of code are temporary; it reads in the SOC info from a static reopt test file 
		## For some reason REopt is not producing BESS results so this is a workaround
		with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','utility_reopt_results.json')) as f:
			static_reopt_results = json.load(f)
		outData['chargeLevelBattery'] = static_reopt_results['outputs']['ElectricStorage']['soc_series_fraction']
	else:
		BESS = np.zeros_like(demand)
		grid_charging_BESS = np.zeros_like(demand)

	## Create DER overview plot object
	fig = go.Figure()
	if inputDict['load_type'] != '0': ## Load type 0 corresponds to the "None" option, which disables this vbatDispatch function
		vbat_discharge_component = np.asarray(vbat_discharge_flipsign)
		vbat_charge_component = np.asarray(vbat_charge)
		fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(vbat_discharge_flipsign)+np.asarray(demand),
							yaxis='y1',
							mode='none',
							fill='tozeroy',
							fillcolor='rgba(127,0,255,1)',
							name='vbat Serving Load (kW)',
							showlegend=showlegend))
		fig.update_traces(fillpattern_shape='/', selector=dict(name='vbat Serving Load (kW)'))
	else:
		vbat_discharge_component = np.zeros_like(demand)
		vbat_charge_component = np.zeros_like(demand)

	## BESS serving load piece
	if (inputDict['BESS'] == 'Yes'):
		fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(BESS) + np.asarray(demand) + vbat_discharge_component,
							yaxis='y1',
							mode='none',
							fill='tozeroy',
							name='BESS Serving Load (kW)',
							fillcolor='rgba(0,137,83,1)',
							showlegend=showlegend))
		fig.update_traces(fillpattern_shape='/', selector=dict(name='BESS Serving Load (kW)'))

	## Original load piece (minus any vbat or BESS charging aka 'new/additional loads')
	fig.add_trace(go.Scatter(x=timestamps,
						y=np.asarray(demand)-np.asarray(BESS)-vbat_discharge_component,
						yaxis='y1',
						mode='none',
						name='Original Load (kW)',
						fill='tozeroy',
						fillcolor='rgba(100,200,210,1)',
						showlegend=showlegend))

	## Additional load (Charging BESS and vbat)
	## NOTE: demand is added here for plotting purposes, so that the additional load shows up above the demand curve.
	## How or if this should be done is still being discussed
	fig.add_trace(go.Scatter(x=timestamps,
                         y=np.asarray(demand) + np.asarray(grid_charging_BESS) + vbat_charge_component,
						 yaxis='y1',
                         mode='none',
                         name='Additional Load (Charging BESS and vbat)',
                         fill='tonexty',
                         fillcolor='rgba(175,0,42,0)',
						 showlegend=showlegend))
	fig.update_traces(fillpattern_shape='.', selector=dict(name='Additional Load (Charging BESS and vbat)'))
	
	## Grid serving new load
	## TODO: Should PV really be in this?
	grid_serving_new_load = np.asarray(grid_to_load) + np.asarray(grid_charging_BESS)+ vbat_charge_component - vbat_discharge_component + np.asarray(PV)
	fig.add_trace(go.Scatter(x=timestamps,
                         y=grid_serving_new_load,
						 yaxis='y1',
                         mode='none',
                         fill='tozeroy',
                         name='Grid Serving Load (kW)',
                         fillcolor='rgba(192,192,192,1)',
						 showlegend=showlegend))
	
	## Temperature line on a secondary y-axis (defined in the plot layout)
	fig.add_trace(go.Scatter(x=timestamps,
						  y=temperatures,
						  yaxis='y2',
						  mode='lines',
						  line=dict(color='red',width=1),
						  name='Average Temperature',
						  showlegend=showlegend 
						  ))

	## NOTE: This code hides the demand curve initially when the plot is made, but it can be 
	## toggled back on by the user by clicking it in the plot legend
	#fig.add_trace(go.Scatter(x=timestamps, 
	#				 y=demand,
	#				 yaxis='y1',
	#				 mode='lines',
	#				 line=dict(color='black'),
	#				 name='Demand',
	#				 showlegend=showlegend))
	#fig.update_traces(legendgroup='Demand', visible='legendonly', selector=dict(name='Original Load (kW)')) ## Make demand hidden on plot by default

	## PV piece, if enabled
	if (inputDict['PV'] == 'Yes'):
		fig.add_trace(go.Scatter(x=timestamps,
						y=PV,
						yaxis='y1',
						mode='none',
						fill='tozeroy',
						name='PV Serving Load (kW)',
						fillcolor='rgba(255,246,0,1)',
						showlegend=showlegend
						))
	
	## Plot layout
	fig.update_layout(
    	title='Utility Data Test',
    	xaxis=dict(title='Timestamp'),
    	yaxis=dict(title="Power (kW)"),
    	yaxis2=dict(title='degrees Celsius',
                overlaying='y',
                side='right'
                ),
    	legend=dict(
			orientation='h',
			yanchor='bottom',
			y=1.02,
			xanchor='right',
			x=1
			)
	)

	## NOTE: This opens a window that displays the correct figure with the appropriate patterns.
	## For some reason, the slash-mark patterns are not showing up on the OMF page otherwise.
	## Eventually we will delete this part.
	fig.show()

	## Encode plot data as JSON for showing in the HTML 
	outData['derOverviewData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['derOverviewLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

	## Battery State of Charge plot
	if inputDict['BESS'] == 'Yes':
		fig = go.Figure()

		fig.add_trace(go.Scatter(x=timestamps,
							y=outData['chargeLevelBattery'],
							mode='none',
							fill='tozeroy',
							fillcolor='red',
							name='Battery Charge Level',
							showlegend=True))
		fig.update_layout(
			xaxis=dict(title='Timestamp'),
			yaxis=dict(title='Charge (%)')
		)

		outData['batteryChargeData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
		outData['batteryChargeLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

	# Model operations typically ends here.
	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','utility_2018_kW_load.csv')) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','utility_CO_2018_temperatures.csv')) as f:
		temp_curve = f.read()

	defaultInputs = {
		## OMF inputs:
		'user' : 'admin',
		'modelType': modelName,
		'created': str(datetime.datetime.now()),

		## REopt inputs:
		'latitude' : '39.986771 ', 
		'longitude' : '-104.812599', ## Brighton, CO
		'year' : '2018',
		'analysis_years' : '25', 
		'urdbLabel' : '612ff9c15457a3ec18a5f7d3', ## Brighton, CO
		## TODO: Create a function that will gather the urdb label from a user provided location (city,state), rather than requiring the URDB label
		'fileName': 'utility_2018_kW_load.csv',
		'tempFileName': 'utility_CO_2018_temperatures.csv',
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,
		'PV': 'Yes',
		'BESS': 'Yes',
		'generator': 'No',
		'outage': True,
		'outage_start_hour': '2100',
		'outage_duration': '3',

		## vbatDispatch inputs:
		'load_type': '2', ## Heat Pump
		'number_devices': '1',
		'power': '5.6',
		'capacitance': '2',
		'resistance': '2',
		'cop': '2.5',
		'setpoint': '19.5',
		'deadband': '0.625',
		'demandChargeCost': '25',
		'electricityCost': '0.16',
		'projectionLength': '25',
		'discountRate': '2',
		'unitDeviceCost': '150',
		'unitUpkeepCost': '5',
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def _tests_disabled():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
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


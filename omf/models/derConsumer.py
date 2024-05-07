''' Performs cost-benefit analysis for a member-consumer with distributed 
energy resource (DER) technologies. '''

import warnings
# warnings.filterwarnings("ignore")

# Python imports
import shutil, datetime
from os.path import join as pJoin
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
import matplotlib.pyplot as plt

# OMF imports
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.models import vbatDispatch as vb
from omf.solvers import reopt_jl

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

def castAddInputs(val1,val2):
	''' Casts string inputs to appropriate type and returns their sum. 
		If inputs are cast to floats, rounds their sum to avoid float subtraction errors.'''
	try:
		cast1 = int(val1)
		cast2 = int(val2)
		return cast1+cast2
	except ValueError:
		try:
			cast1 = float(val1)
			cast2 = float(val2)
            #Find longest decimal place of the numbers and round their sum to that place to avoid float arithmetic errors
			decPl1 = val1.strip()[::-1].find('.')
			decPl2 = val2.strip()[::-1].find('.')  
            #valX.strip() used instead of str(castX) because str(castX) may return scientific notation
			roundedSum = round(cast1+cast2,max(decPl1,decPl2,1))     
			return roundedSum
		except ValueError:
			return val1+val2

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	outData = {}	

	## Read in a static REopt test file
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","residential_REopt_results.json")) as f:
		reoptResults = pd.json_normalize(json.load(f))
		print('Successfully loaded REopt test file. \n')

	# Model operations goes here.

	## Create timestamp array from REopt input information
	year = reoptResults['inputs.ElectricLoad.year'][0]
	arr_size = np.size(reoptResults['outputs.ElectricUtility.electric_to_load_series_kw'][0])
	timestamps = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:00:00', periods=arr_size)

	## Convert temperature data from str to float
	temperatures = [float(value) for value in inputDict['tempCurve'].split('\n') if value.strip()]
	demand = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()])


	## Run vbatDispatch
	vbatResults = vb.work(modelDir,inputDict)
	
	with open(pJoin(modelDir, 'vbatResults.json'), 'w') as jsonFile:
		json.dump(vbatResults, jsonFile)
	outData.update(vbatResults) ## Update output file with vbat results
	

	## Test plot
	plotData = []
	
	showlegend = False

	layout = go.Layout(
    	title='Residential Data',
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
							mode='none',
							fill='tozeroy',
							fillcolor='rgba(127,0,255,1)',
							name='vbat Serving Load (kW)',
							showlegend=showlegend))
	fig.update_traces(fillpattern_shape='/', selector=dict(name='vbat Serving Load (kW)'))

	fig.add_trace(go.Scatter(x=timestamps,
                         y=np.asarray(demand)-np.asarray(BESS)-np.asarray(vbat_discharge_flipsign),
                         mode='none',
                         name='Original Load (kW)',
                         fill='tozeroy',
                         fillcolor='rgba(100,200,210,1)',
						 showlegend=showlegend))

	fig.add_trace(go.Scatter(x=timestamps,
					 y=PV,
					 yaxis='y1',
					 mode='none',
					 fill='tozeroy',
					 name='PV Serving Load (kW)',
					 fillcolor='rgba(255,246,0,1)',
					 showlegend=showlegend
					 ))
	
	fig.add_trace(go.Scatter(x=timestamps,
                         y=np.asarray(demand) + np.asarray(reoptResults['outputs.ElectricUtility.electric_to_storage_series_kw'][0]) + np.asarray(vbat_charge),
                         mode='none',
                         name='Additional Load (Charging BESS and vbat)',
                         fill='tonexty',
                         fillcolor='rgba(175,0,42,0)',
						 showlegend=showlegend))
	fig.update_traces(fillpattern_shape='.', selector=dict(name='Additional Load (Charging BESS and vbat)'))


	grid_serving_new_load = np.asarray(grid_to_load) + np.asarray(grid_charging_BESS)+ np.asarray(vbat_charge) - np.asarray(vbat_discharge_flipsign) + np.asarray(PV)
	fig.add_trace(go.Scatter(x=timestamps,
                         y=grid_serving_new_load,
                         mode='none',
                         fill='tozeroy',
                         name='Grid Serving Load (kW)',
                         fillcolor='rgba(192,192,192,0.5)',
						 showlegend=showlegend))
	
	fig.add_trace(go.Scatter(x=timestamps, 
					   y=temperatures,
					   yaxis='y2',
					   mode='lines',
					   line=dict(color='red',width=1),
					   name='Average Temperature',
					   showlegend=showlegend #temporarily disable the legend toggle
	))

	fig.add_trace(go.Scatter(x=timestamps, 
					 y=demand,
					 yaxis='y1',
					 mode='lines',
					 line=dict(color='black'),
					 name='Demand',
					 showlegend=showlegend
					))
	fig.update_traces(legendgroup='Demand', visible='legendonly', selector=dict(name='Original Load (kW)')) ## Make demand hidden on plot by default


	## Encode plot data as JSON for showing in the HTML side
	outData['plotlyPlot'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['plotlyLayout'] = json.dumps(layout, cls=plotly.utils.PlotlyJSONEncoder)

	# Model operations typically ends here.
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""

	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","residential_PV_load.csv")) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","residential_extended_temperature_data.csv")) as f:
		temp_curve = f.read()
	
	defaultInputs = {
		## OMF inputs:
		"user": "admin",
		"modelType": modelName,
		"created": str(datetime.datetime.now()),
		"user": "admin",
		"modelType": modelName,

		## REopt inputs:
		"latitude":  '39.532165', ## Rivesville, WV
		"longitude": '-80.120618', ## TODO: Should these be strings or floats? Update - strings.
		"year": '2018',
		"analysisYears": '25', 
		"urdbLabel": '643476222faee2f0f800d8b1', ## Rivesville, WV - Monongahela Power
		"fileName": "residential_PV_load.csv",
		"tempFileName": "residential_extended_temperature_data.csv",
		"demandCurve": demand_curve,
		"tempCurve": temp_curve,
		"outage": False,
		"PV": "Yes",
		"BESS": "No",
		"generator": "No",

		## vbatDispatch inputs:
		"load_type": '2', ## Heat Pump
		"number_devices": '1',
		"power": '5.6',
		"capacitance": '2',
		"resistance": '2',
		"cop": '2.5',
		"setpoint": '19.5',
		"deadband": '0.625',
		"demandChargeCost": '25',
		"electricityCost": '0.16',
		"projectionLength": '25',
		"discountRate": '2',
		"unitDeviceCost": '150',
		"unitUpkeepCost": '5',
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def _tests():
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
	__neoMetaModel__.renderAndShow(modelLoc) ## Why is there a pre-run?
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

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
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	#_tests()
	_debugging() ## This is only used to bypass the runAllTests errors due to this model's incompletion. It is just a copy of _tests() function.
	pass
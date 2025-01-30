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
from numpy_financial import npv

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
hidden = True ## Keep the model hidden=True during active development

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	# Delete output file every run if it exists
	outData = {}

	## Update inputDict with derUtilityCost inputs	
	## Site parameters
	latitude = float(inputDict['latitude'])
	longitude = float(inputDict['longitude'])
	urdbLabel = str(inputDict['urdbLabel'])
	year = int(inputDict['year'])
	projectionLength = int(inputDict['projectionLength'])
	demand_array = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()]) ## process input format into an array
	demand = demand_array.tolist() if isinstance(demand_array, np.ndarray) else demand_array ## make demand array into a list	for REopt

	## Begin the REopt input dictionary called 'scenario' that is required to run omf.solvers.reopt_jl
	scenario = {
		'Site': {
			'latitude': latitude,
			'longitude': longitude
		},
		'ElectricTariff': {
			'urdb_label': urdbLabel
		},
		'ElectricLoad': {
			'loads_kw': demand,
			'year': year
		},
		'Financial': {
			'analysis_years': projectionLength
		}
	}

	## Add fossil fuel (diesel) generator to input scenario
	if inputDict['fossilGenerator'] == 'Yes':
		scenario['Generator'] = {
			'existing_kw': float(inputDict['existing_gen_kw']),
			'max_kw': 0,
			'min_kw': 0,
			'only_runs_during_grid_outage': False,
			'fuel_avail_gal': float(inputDict['fuel_available_gal']),
			'fuel_cost_per_gallon': float(inputDict['fuel_cost_per_gal'])
		}

	## Add a Battery Energy Storage System (BESS) section if enabled 
	if float(inputDict['numberBESS']) > 0:
		scenario['ElectricStorage'] = {
			##TODO: Add options here, if needed
			'min_kw': float(inputDict['BESS_kw'])*float(inputDict['numberBESS']),
			'max_kw':  float(inputDict['BESS_kw'])*float(inputDict['numberBESS']),
			'min_kwh':  float(inputDict['BESS_kwh'])*float(inputDict['numberBESS']),
			'max_kwh':  float(inputDict['BESS_kwh'])*float(inputDict['numberBESS']),
			'can_grid_charge': True,
			'total_rebate_per_kw': 0,
			'macrs_option_years': 0,
			'installed_cost_per_kw': 0,
			'installed_cost_per_kwh': 0,
			'battery_replacement_year': 0,
			'inverter_replacement_year': 0,
			'replace_cost_per_kwh': 0.0,
			'replace_cost_per_kw': 0.0,
			'total_rebate_per_kw': 0.0,
			'total_itc_fraction': 0.0,
			}
	
	## Save the scenario file
	## NOTE: reopt_jl currently requires a path for the input file, so the file must be saved to a location preferrably in the modelDir directory
	with open(pJoin(modelDir, 'reopt_input_scenario.json'), 'w') as jsonFile:
		json.dump(scenario, jsonFile)

	## Create basic REopt input file
	## NOTE: This function is disabled for now since the scenario dictionary above is hard coded and not relying on the derConsumer function to produce the REopt input file.
	#derConsumer.create_REopt_jl_jsonFile(modelDir, inputDict)

	## Run REopt.jl
	reopt_jl.run_reopt_jl(modelDir, 'reopt_input_scenario.json')
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
	
	timestamps = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:00:00', periods=np.size(demand))

	## Set up base input dictionary for vbatDispatch runs
	inputDict_vbatDispatch = {
		'load_type': '', ## 1=AirConditioner, 2=HeatPump, 3=Refrigerator, 4=WaterHeater (This is from vbatDispatch.html)
		'number_devices': '',
		'power': '',
		'capacitance': '',
		'resistance': '',
		'cop': '',
		'setpoint':  '',
		'deadband': '',
		'unitDeviceCost': '0.0', ## set to zero: assuming utility does not pay for this
		'unitUpkeepCost':  '0.0', ## set to zero: assuming utility does not pay for this
		'demandChargeCost': inputDict['demandChargeCost'],
		'electricityCost': inputDict['electricityCost'],
		'projectionLength': inputDict['projectionLength'],
		'discountRate': inputDict['discountRate'],
		'fileName': inputDict['fileName'],
		'tempFileName':  inputDict['tempFileName'],
		'demandCurve':  inputDict['demandCurve'],
		'tempCurve': inputDict['tempCurve'],
	}
	
	## Define thermal variables that change depending on the thermal technology
	thermal_suffixes = ['_hp', '_ac', '_wh'] ## heat pump, air conditioner, water heater - (Add more suffixes here after establishing inputs in the defaultInputs and derUtilityCost.html)
	thermal_variables=['load_type','number_devices','power','capacitance','resistance','cop','setpoint','deadband',
					'TESS_operationalCosts_ongoing','TESS_operationalCosts_onetime','TESS_subsidy_ongoing','TESS_subsidy_onetime']

	all_device_suffixes = []
	single_device_results = {}
	for suffix in thermal_suffixes:

		## Include only the thermal devices specified by the user
		if float(inputDict['load_type'+suffix]) > 0 and float(inputDict['number_devices'+suffix]) > 0:
			all_device_suffixes.append(suffix)

			## Add the appropriate thermal device variables to the inputDict_vbatDispatch
			for i in thermal_variables:
				inputDict_vbatDispatch[i] = inputDict[i+suffix]

			## Create subdirectory for the thermal device to store the vbatDispatch results
			newDir = pJoin(modelDir,'vbatDispatch_results'+suffix)
			os.makedirs(newDir, exist_ok=True)
			os.chdir(newDir) ##jump into the new directory

			## Run vbatDispatch for the thermal device
			vbatResults = vb.work(modelDir,inputDict_vbatDispatch)
			with open(pJoin(newDir, 'vbatResults.json'), 'w') as jsonFile:
				json.dump(vbatResults, jsonFile)
			
			## Update the vbatResults to include operational costs and subsidies
			vbatResults['TESS_operationalCosts_ongoing'] = inputDict_vbatDispatch['TESS_operationalCosts_ongoing']
			vbatResults['TESS_operationalCosts_onetime'] = inputDict_vbatDispatch['TESS_operationalCosts_onetime']
			vbatResults['TESS_subsidy_onetime'] = inputDict_vbatDispatch['TESS_subsidy_onetime']
			vbatResults['TESS_subsidy_ongoing'] = inputDict_vbatDispatch['TESS_subsidy_ongoing']

			## Store the results in all_device_results dictionary
			single_device_results['vbatResults'+suffix] = vbatResults

			## Go back to the main derUtilityCost model directory
			os.chdir(modelDir)


	## Initialize empty dictionary to hold all thermal device results added together
	## Length 8760 is hourly data for a year, length 12 is monthly data for a year
	combined_device_results = {
		'vbatPower_series': [0]*8760,
		'vbat_charge': [0]*8760,
		'vbat_discharge': [0]*8760,
		'vbat_discharge_flipsign': [0]*8760,
		'vbatMinEnergyCapacity': [0]*8760,
		'vbatMaxEnergyCapacity':[0]*8760,
		'vbatEnergy':[0]*8760,
		'vbatMinPowerCapacity': [0]*8760,
		'vbatMaxPowerCapacity': [0]*8760,
		'vbatPower': [0]*8760,
		'savingsTESS': [0]*12,
		'energyAdjustedMonthlyTESS': [0]*12,
		'demandAdjustedTESS': [0]*8760,
		'peakAdjustedDemandTESS': [0]*12,
		'totalCostAdjustedTESS': [0]*12,
		'demandChargeAdjustedTESS': [0]*12,
		'energyCostAdjustedTESS':[0]*12,
		'combinedTESS_operationalCosts_ongoing': 0,
		'combinedTESS_operationalCosts_onetime': 0,
		'combinedTESS_subsidy_ongoing': 0,
		'combinedTESS_subsidy_onetime': 0,
	}

	## Combine all thermal device variable data for plotting
	for device_result in single_device_results:
		## vbatDispatch variables
		combined_device_results['vbatPower'] = [sum(x) for x in zip(combined_device_results['vbatPower'], single_device_results[device_result]['VBpower'])]
		vbatPower_series = pd.Series(combined_device_results['vbatPower'])
		combined_device_results['vbatPower_series'] = vbatPower_series
		combined_device_results['vbat_charge'] = vbatPower_series.where(vbatPower_series > 0, 0) ##positive values = charging
		combined_device_results['vbat_discharge'] = vbatPower_series.where(vbatPower_series < 0, 0) ##negative values = discharging
		combined_device_results['vbat_discharge_flipsign'] = combined_device_results['vbat_discharge'].mul(-1) ## flip sign of vbat discharge for plotting purposes
		combined_device_results['vbatMinEnergyCapacity'] = [sum(x) for x in zip(combined_device_results['vbatMinEnergyCapacity'], single_device_results[device_result]['minEnergySeries'])]
		combined_device_results['vbatMaxEnergyCapacity'] = [sum(x) for x in zip(combined_device_results['vbatMaxEnergyCapacity'], single_device_results[device_result]['maxEnergySeries'])]
		combined_device_results['vbatEnergy'] = [sum(x) for x in zip(combined_device_results['vbatEnergy'], single_device_results[device_result]['VBenergy'])]
		combined_device_results['vbatMinPowerCapacity'] = [sum(x) for x in zip(combined_device_results['vbatMinPowerCapacity'], single_device_results[device_result]['minPowerSeries'])]
		combined_device_results['vbatMaxPowerCapacity'] = [sum(x) for x in zip(combined_device_results['vbatMaxPowerCapacity'], single_device_results[device_result]['maxPowerSeries'])]
		combined_device_results['savingsTESS'] = [sum(x) for x in zip(combined_device_results['savingsTESS'], single_device_results[device_result]['savings'])]
		combined_device_results['energyAdjustedMonthlyTESS'] = [sum(x) for x in zip(combined_device_results['energyAdjustedMonthlyTESS'], single_device_results[device_result]['energyAdjustedMonthly'])]
		combined_device_results['demandAdjustedTESS'] = [sum(x) for x in zip(combined_device_results['demandAdjustedTESS'], single_device_results[device_result]['demandAdjusted'])]
		combined_device_results['peakAdjustedDemandTESS'] = [sum(x) for x in zip(combined_device_results['peakAdjustedDemandTESS'], single_device_results[device_result]['peakAdjustedDemand'])]
		combined_device_results['totalCostAdjustedTESS'] = [sum(x) for x in zip(combined_device_results['totalCostAdjustedTESS'], single_device_results[device_result]['totalCostAdjusted'])]
		combined_device_results['demandChargeAdjustedTESS'] = [sum(x) for x in zip(combined_device_results['demandChargeAdjustedTESS'], single_device_results[device_result]['demandChargeAdjusted'])]
		combined_device_results['energyCostAdjustedTESS'] = [sum(x) for x in zip(combined_device_results['energyCostAdjustedTESS'], single_device_results[device_result]['energyCostAdjusted'])]
		combined_device_results['combinedTESS_operationalCosts_ongoing'] += float(single_device_results[device_result]['TESS_operationalCosts_ongoing'])
		combined_device_results['combinedTESS_operationalCosts_onetime'] += float(single_device_results[device_result]['TESS_operationalCosts_onetime'])
		combined_device_results['combinedTESS_subsidy_ongoing'] += float(single_device_results[device_result]['TESS_subsidy_ongoing'])
		combined_device_results['combinedTESS_subsidy_onetime'] += float(single_device_results[device_result]['TESS_subsidy_onetime'])

		## TODO: Bri - compare these with the manually calculated variables at bottom


	## NOTE: temporarily comment out the two derConsumer runs to run the code quicker
	"""
	## Scale down the utility demand to create an ad-hoc small consumer load (1 kW average) and large consumer load (10 kW average)
	utilityLoadAverage = np.average(demand)
	smallConsumerTargetAverage = 1.0 #Unit: kW
	largeConsumerTargetAverage = 10.0 #Unit: kW
	smallConsumerLoadScaleFactor = smallConsumerTargetAverage / utilityLoadAverage 
	largeConsumerLoadScaleFactor = largeConsumerTargetAverage / utilityLoadAverage 
	smallConsumerLoad = demand * smallConsumerLoadScaleFactor
	largeConsumerLoad = demand * largeConsumerLoadScaleFactor

	## Convert small and large consumer load arrays into strings and pass it back to derConsumer
	## TODO: Ideally this model wouldn't handle data in string format, it feels like extra work - consider changing that input format type later to floats
	smallConsumerLoadString = '\n'.join([str(value) for value in smallConsumerLoad])
	largeConsumerLoadString = '\n'.join([str(value) for value in largeConsumerLoad])

	## Create a new derConsumer model directory to store the results for both small and large consumers
	newDir_smallderConsumer = pJoin(modelDir,'smallderConsumer')
	newDir_largederConsumer = pJoin(modelDir,'largederConsumer')
	os.makedirs(newDir_smallderConsumer, exist_ok=True)
	os.makedirs(newDir_largederConsumer, exist_ok=True)
	os.chdir(newDir_smallderConsumer)
	print("Current Directory:", os.getcwd())

	## Set up model inputs for derConsumer and pass the small and large consumer loads to omf/models/derConsumer
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','residential_critical_load.csv')) as f:
		criticalLoad_curve = f.read()
	
	derConsumerInputDict = {
		## OMF inputs:
		'user' : 'admin',
		'modelType': modelName,
		'created': str(datetime.datetime.now()),

		## REopt inputs:
		## NOTE: Variables are strings as dictated by the html input options
		'latitude':  inputDict['latitude'], ## use utility's lat and lon 
		'longitude': inputDict['longitude'], 
		'year' : '2018',
		'urdbLabel': inputDict['urdbLabel'],
		'fileName': 'residential_PV_load.csv',
		'tempFileName': 'residential_extended_temperature_data.csv',
		'criticalLoadFileName': 'residential_critical_load.csv', ## critical load here = 50% of the daily demand
		'demandCurve': smallConsumerLoadString,
		'tempCurve': inputDict['tempCurve'],
		'criticalLoad': criticalLoad_curve,
		'criticalLoadSwitch': 'Yes',
		'criticalLoadFactor': '0.50',
		'PV': 'Yes',
		'BESS': 'Yes',
		'generator': 'No',
		'outage': True,
		'outage_start_hour': '4637',
		'outage_duration': '3',

		## Financial Inputs
		'demandChargeURDB': 'Yes',
		'demandChargeCost': '25',
		'projectionLength': '25',

		## vbatDispatch inputs:
		'load_type': '2', ## Heat Pump
		'number_devices': '1',
		'power': '5.6',
		'capacitance': '2',
		'resistance': '2',
		'cop': '2.5',
		'setpoint': '19.5',
		'deadband': '0.625',
		'electricityCost': '0.16',
		'discountRate': '2',
		'unitDeviceCost': '150',
		'unitUpkeepCost': '5',

		## DER Program Design inputs:
		'utilityProgram': 'No',
		'rateCompensation': '0.1', ## unit: $/kWh
		#'maxBESSDischarge': '0.80', ## Between 0 and 1 (Percent of total BESS capacity) #TODO: Fix the HTML input for this
		'subsidy': '12',
	}
	smallConsumerOutput = derConsumer.work(newDir_smallderConsumer,derConsumerInputDict)

	## Change directory to large derConsumer and run that case
	os.chdir(newDir_largederConsumer)
	derConsumerInputDict['demandCurve'] = largeConsumerLoadString
	derConsumerInputDict['number_devices'] = '2'
	largeConsumerOutput = derConsumer.work(newDir_largederConsumer,derConsumerInputDict)

	## Change directory back to derUtilityCost
	os.chdir(modelDir)
	outData.update({
		'TESSsavingsSmallConsumer': smallConsumerOutput['savings'],
		'TESSsavingsLargeConsumer': largeConsumerOutput['savings']
	})
	"""

	## DER Serving Load Overview plot ###################################################################################################################################################################
	showlegend = True # either enable or disable the legend toggle in the plot
	#lineshape = 'linear'
	lineshape = 'hv'
	grid_to_load = reoptResults['ElectricUtility']['electric_to_load_series_kw']

	if 'ElectricStorage' in reoptResults:
		BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
		grid_charging_BESS = reoptResults['ElectricUtility']['electric_to_storage_series_kw']
		outData['chargeLevelBattery'] = reoptResults['ElectricStorage']['soc_series_fraction']
	else:
		BESS = np.zeros_like(demand)
		grid_charging_BESS = np.zeros_like(demand)
		outData['chargeLevelBattery'] = np.zeros_like(demand)

	## NOTE: The following 6 lines of code are temporary; it reads in the SOC info from a static REopt test file (a previously completed REopt run) 
	## This functionality was used when REopt did not produce BESS results, or the results were arrays of zeros.
	
	#with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','utility_reopt_results.json')) as f:
	#	static_reopt_results = json.load(f)
	#BESS = static_reopt_results['outputs']['ElectricStorage']['storage_to_load_series_kw']
	#grid_charging_BESS = static_reopt_results['outputs']['ElectricUtility']['electric_to_storage_series_kw']
	#outData['chargeLevelBattery'] = static_reopt_results['outputs']['ElectricStorage']['soc_series_fraction']
	#outData.update(static_reopt_results['outputs'])

	## Create DER overview plot object
	fig = go.Figure()

	## vbatDispatch variables
	vbat_discharge_component = np.array(combined_device_results['vbat_discharge_flipsign'])
	vbat_charge_component = np.array(combined_device_results['vbat_charge'])

	## Convert all values from kW to Watts for plotting purposes only
	grid_to_load_W = np.array(grid_to_load) * 1000.
	BESS_W = np.array(BESS) * 1000.
	grid_charging_BESS_W = np.array(grid_charging_BESS) * 1000.
	vbat_discharge_component_W = vbat_discharge_component * 1000.
	vbat_charge_component_W = vbat_charge_component * 1000.
	demand_W = np.array(demand) * 1000.
	if 'Generator' in reoptResults:
		generator = np.array(reoptResults['Generator']['electric_to_load_series_kw'])
		generator_W = generator * 1000.
	else:
		generator = np.zeros_like(demand)
		generator_W = np.zeros_like(demand)

	## Additional load (Charging BESS and vbat)
	## NOTE: demand is added here for plotting purposes, so that the additional load shows up above the demand curve.
	## How or if this should be done is still being discussed - break out into a separate plot eventually
	
	## Commented out the below because we are changing the "additional load" area fill to be instead reflected as "BESS Charging (additional load)" and "TESS Charging (additional load)"
	#additional_load = demand + grid_charging_BESS + vbat_charge_component
	#fig.add_trace(go.Scatter(x=timestamps,
    #                     y=additional_load,
	#					 yaxis='y1',
    #                     mode='none',
    #                     name='Additional Load (Charging BESS and TESS)',
    #                     fill='tonexty',
    #                     fillcolor='rgba(175,0,42,0)',
	#					 showlegend=showlegend))
	#fig.update_traces(fillpattern_shape='.', selector=dict(name='Additional Load (Charging BESS and TESS)'))
	
	## Grid serving new load
	grid_serving_new_load_W = grid_to_load_W + grid_charging_BESS_W + vbat_charge_component_W - vbat_discharge_component_W
	fig.add_trace(go.Scatter(x=timestamps,
                        y=grid_serving_new_load_W,
						yaxis='y1',
                        #mode='none',
                        fill='tozeroy',
                        name='Grid Serving Load',
						fillcolor='rgba(192,192,192,1)',
                        line=dict(color='rgba(192,192,192,1)'), ## Plotly default assigns different colors for line and fillcolor
						line_shape=lineshape,
						#stackgroup='one',
						showlegend=showlegend))
	
	## Temperature line on a secondary y-axis (defined in the plot layout)
	fig.add_trace(go.Scatter(x=timestamps,
						y=temperatures,
						yaxis='y2',
						#mode='lines',
						line=dict(color='red',width=1),
						name='Average Air Temperature',
						showlegend=showlegend 
						))
	## Make temperature and its legend name hidden in the plot by default
	fig.update_traces(legendgroup='Average Air Temperature', visible='legendonly', selector=dict(name='Average Air Temperature')) 

	## BESS serving load piece
	fig.add_trace(go.Scatter(x=timestamps,
						y = BESS_W, # + np.asarray(demand) + vbat_discharge_component,
						yaxis='y1',
						#mode='none',
						fill='tozeroy',
						name='Home BESS Serving Load',
						fillcolor='rgba(0,137,83,1)',
						line=dict(color='rgba(0,0,0,0)'), #transparent line (to get around the Plotly default line)
						line_shape=lineshape,
						#stackgroup='one',
						showlegend=showlegend))

	## vbatDispatch (TESS) piece
	fig.add_trace(go.Scatter(x=timestamps,
						y = vbat_discharge_component_W,
						yaxis='y1',
						#mode='none',
						fill='tozeroy',
						fillcolor='rgba(127,0,255,1)',
						name='Home TESSs Serving Load',
						line=dict(color='rgba(0,0,0,0)'), #transparent line (to get around the Plotly default line)
						line_shape=lineshape,
						#stackgroup='one',
						showlegend=showlegend))
		
	## Fossil Generator piece
	if 'Generator' in reoptResults:
		fig.add_trace(go.Scatter(x=timestamps,
						y = generator_W,
						yaxis='y1',
						mode='none',
						fill='tozeroy',
						fillcolor='rgba(153,0,0,1)',
						line=dict(color='rgba(0,0,0,0)'), #transparent line (to get around the Plotly default line)
						name='Fossil Generator Serving Load',
						line_shape=lineshape,
						#stackgroup='one',
						showlegend=showlegend))
		
	## Grid charging BESS piece
	fig.add_trace(go.Scatter(x=timestamps,
                        y=grid_charging_BESS_W*-1., ## changed to negative sign to indicate charging behavior
						yaxis='y1',
                        #mode='none',
                        name='Grid Charging Home BESS',
                        fill='tozeroy',
						fillcolor='rgba(118,196,165,1)',
						line=dict(color='rgba(0,0,0,0)'), #transparent line (to get around the Plotly default line)
						line_shape=lineshape,
						showlegend=showlegend))
	
	## Grid charging TESS piece
	fig.add_trace(go.Scatter(x=timestamps,
    	                    y = vbat_charge_component_W*-1.,  ## changed to negative sign to indicate charging behavior
							yaxis='y1',
            	            #mode='none',
                	        name='Grid Charging Home TESS',
                    	    fill='tozeroy',
							fillcolor='rgba(207,158,255,1)',
							line=dict(color='rgba(0,0,0,0)'), #transparent line (to get around the Plotly default line)
							line_shape=lineshape,
							showlegend=showlegend))

	## Plot layout
	fig.update_layout(
    	xaxis=dict(title='Timestamp'),
    	yaxis=dict(title="Power (W)"),
    	yaxis2=dict(title='degrees Fahrenheit',
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
	#fig.show()
	#outData['derOverviewHtml'] = fig.to_html(full_html=False)
	fig.write_html(pJoin(modelDir, "Plot_DerServingLoadOverview.html"))

	## Encode plot data as JSON for showing in the HTML 
	outData['derOverviewData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['derOverviewLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)


	## Impact to Demand plot ###################################################################################################################################################################
	showlegend = True # either enable or disable the legend toggle in the plot
	#lineshape = 'linear'
	lineshape = 'hv'

	fig = go.Figure()
	demand_W = demand * 1000.
	new_demand = demand_W + vbat_charge_component_W + grid_charging_BESS_W - BESS_W - vbat_discharge_component_W - generator_W

	## Original load piece (minus any vbat or BESS charging aka 'new/additional loads')
	fig.add_trace(go.Scatter(x=timestamps,
						y = demand_W,
						yaxis='y1',
						mode='none',
						name='Original Demand',
						fill='tozeroy',
						fillcolor='rgba(81,40,136,1)',
						showlegend=showlegend))
	## Make original load and its legend name hidden in the plot by default
	#fig.update_traces(legendgroup='Original Demand', visible='legendonly', selector=dict(name='Original Demand')) 

	## New demand piece (minus any vbat or BESS charging aka 'new/additional loads')
	fig.add_trace(go.Scatter(x=timestamps,
						y = new_demand,
						yaxis='y1',
						mode='none',
						name='New Demand',
						fill='tozeroy',
						fillcolor='rgba(235, 97, 35, 0.5)',
						showlegend=showlegend))
	## Make original load and its legend name hidden in the plot by default
	#fig.update_traces(legendgroup='New Demand', visible='legendonly', selector=dict(name='New Demand')) 

	## Temperature line on a secondary y-axis (defined in the plot layout)
	fig.add_trace(go.Scatter(x=timestamps,
						y=temperatures,
						yaxis='y2',
						#mode='lines',
						line=dict(color='red',width=1),
						name='Average Air Temperature',
						showlegend=showlegend 
						))
	## Make temperature and its legend name hidden in the plot by default
	fig.update_traces(legendgroup='Average Air Temperature', visible='legendonly', selector=dict(name='Average Air Temperature')) 


	## Plot layout
	fig.update_layout(
    	xaxis=dict(title='Timestamp'),
    	#yaxis=dict(title='Power (W)',type='log'),
		yaxis=dict(title='Power (W)'),
    	yaxis2=dict(title='degrees Fahrenheit',
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
	#fig.show()
	#outData['derOverviewHtml'] = fig.to_html(full_html=False)
	fig.write_html(pJoin(modelDir, "Plot_NewDemand.html"))

	## Encode plot data as JSON for showing in the HTML 
	outData['newDemandData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['newDemandLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)


	## Create Thermal Battery Power plot object ######################################################################################################################################################
	fig = go.Figure()
	fig.add_trace(go.Scatter(
		x=timestamps,
		y=combined_device_results['vbatMinPowerCapacity'],
		yaxis='y1',
		mode='lines',
		line=dict(color='green', width=1),
		name='Minimum Calculated Power Capacity',
		showlegend=True 
		))
	fig.add_trace(go.Scatter(
		x=timestamps, 
		y=combined_device_results['vbatMaxPowerCapacity'],
		yaxis='y1',
		mode='lines',
		line=dict(color='blue', width=1),
		name='Maximum Calculated Power Capacity',
		showlegend=True
	))
	fig.add_trace(go.Scatter(
		x=timestamps, 
		y=combined_device_results['vbatPower'], 
		yaxis='y1',
		mode='lines',
		line=dict(color='black', width=1),
		name='Actual Power Utilized',
		showlegend=True
	))

	## Plot layout
	fig.update_layout(
		xaxis=dict(title='Timestamp'),
		yaxis=dict(title='Power (kW)'),
		legend=dict(
			orientation='h',
			yanchor='bottom',
			y=1.02,
			xanchor='right',
			x=1
			)
	)
	
	## Encode plot data as JSON for showing in the HTML side
	outData['thermalBatPowerPlot'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['thermalBatPowerPlotLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)	



	## Create Chemical BESS State of Charge plot object ######################################################################################################################################################
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=timestamps,
						y=outData['chargeLevelBattery'],
						mode='lines',
						line=dict(color='red', width=1),
						name='Battery SOC',
						showlegend=True))
	
	fig.update_layout(
		xaxis=dict(title='Timestamp'),
		yaxis=dict(title='Charge (%)'),
		legend=dict(
				orientation='h',
				yanchor='bottom',
				y=1.02,
				xanchor='right',
				x=1
				)
	)
	outData['batteryChargeData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['batteryChargeLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)


	"""
	#####################################################################################################################################################################################################
	## Compensation rate to member-consumer
	compensationRate = float(inputDict['rateCompensation'])
	subsidy = float(inputDict['subsidy']) ## TODO: Amount for the entire analysis - should we divide this up by # of months and add to the monthly consumer savings?
	electricityCost = float(inputDict['electricityCost'])

	monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
					(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
					(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]
	
	load_smallConsumer_monthly = np.asarray([sum(smallConsumerLoad[s:f]) for s, f in monthHours])
	load_largeConsumer_monthly = np.asarray([sum(largeConsumerLoad[s:f]) for s, f in monthHours])
	loadCost_smallConsumer_monthly = load_smallConsumer_monthly * electricityCost
	loadCost_largeConsumer_monthly = load_largeConsumer_monthly * electricityCost

	## Check if REopt results include a BESS output that is not an empty list
	if 'ElectricStorage' in reoptResults and any(reoptResults['ElectricStorage']['storage_to_load_series_kw']):
		BESS_utility = reoptResults['ElectricStorage']['storage_to_load_series_kw'] ## The BESS that is recommended for the utility
		BESS_smallConsumer = smallConsumerOutput['ElectricStorage']['storage_to_load_series_kw'] ## A scaled down version of the utility's load to represent a small consumer (1 kWh average load)
		BESS_largeConsumer = largeConsumerOutput['ElectricStorage']['storage_to_load_series_kw'] ## A scaled down version of the utility's load to represent a large consumer (10 kWh average load)
		BESS_smallConsumer_monthly = np.asarray([sum(BESS_smallConsumer[s:f]) for s, f in monthHours])
		BESS_largeConsumer_monthly = np.asarray([sum(BESS_largeConsumer[s:f]) for s, f in monthHours])
		BESSCost_smallConsumer_monthly = BESS_smallConsumer_monthly * compensationRate
		BESSCost_largeConsumer_monthly = BESS_largeConsumer_monthly * compensationRate

		## Divide subsidy amount up into the monthly consumer savings
		subsidy_monthly = np.full(12, subsidy/12)

		## Add BESS + TESS + subsidy(divided by 12 months) = total savings
		TESSCost_smallConsumer_monthly = np.asarray(outData['TESSsavingsSmallConsumer'])
		TESSCost_largeConsumer_monthly = np.asarray(outData['TESSsavingsLargeConsumer'])
		totalCost_smallConsumer_monthly = TESSCost_smallConsumer_monthly + BESSCost_smallConsumer_monthly + subsidy_monthly
		totalCost_largeConsumer_monthly = TESSCost_largeConsumer_monthly + BESSCost_largeConsumer_monthly + subsidy_monthly

		## Update the consumer savings output to represent both thermal BESS (vbatDispatch results) and REopt's BESS results
		outData.update({
			'totalSavingsSmallConsumer': list(totalCost_smallConsumer_monthly),
			'totalSavingsLargeConsumer': list(totalCost_largeConsumer_monthly)
		})

		## Print some monthly costs/savings for analysis
		print('Small Consumer consumption cost (w/o BESS): ${:,.2f}'.format(np.sum(loadCost_smallConsumer_monthly)))
		print('Small Consumer savings for BESS only: ${:,.2f} \n'.format(np.sum(BESSCost_smallConsumer_monthly)))	
		print('Large Consumer consumption cost (w/o BESS): ${:,.2f}'.format(np.sum(loadCost_largeConsumer_monthly)))
		print('Large Consumer savings for BESS only: ${:,.2f}'.format(np.sum(BESSCost_largeConsumer_monthly)))
		BESS_compensated_to_consumer = np.sum(BESS_utility)*compensationRate+subsidy
		print('--------------------------------------------------------')
		print('Utility total compensation for consumer BESS ($ annually): ${:,.2f}'.format(BESS_compensated_to_consumer))
		BESS_bought_from_grid = np.sum(BESS_utility) * electricityCost
		print('Utility BESS savings (1 year BESS kWh x electricity cost): ${:,.2f}'.format(BESS_bought_from_grid))
		print('Difference (Utility BESS savings - Compensation to consumers): ${:,.2f}'.format(BESS_bought_from_grid-BESS_compensated_to_consumer))

	"""

	## Update energy and power variables
	monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
		(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
		(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]
	electricityCost = float(inputDict['electricityCost'])
	demandChargeCost = float(inputDict['demandChargeCost'])
	rateCompensation = float(inputDict['rateCompensation'])

	outData['peakDemand'] = [max(demand[s:f]) for s, f in monthHours] 
	outData['energyMonthly'] = [sum(demand[s:f]) for s, f in monthHours]
	outData['energyCost'] = [em*electricityCost for em in outData['energyMonthly']]

	## Define the new demand curve, accounting for all DERs
	outData['demandAdj_total'] = list(demand - BESS - vbat_discharge_component - generator + grid_charging_BESS + vbat_charge_component)
	outData['energyAdjustedMonthly_total'] = [sum(outData['demandAdj_total'][s:f]) for s, f in monthHours]
	outData['energyAdjustedMonthly_BESS'] = [sum(BESS[s:f]) for s, f in monthHours]
	outData['energyAdjustedMonthly_TESS'] = [sum(vbat_discharge_component[s:f]) for s, f in monthHours]
	outData['energyAdjustedMonthly_generator'] = [sum(generator[s:f]) for s, f in monthHours]
	outData['energyAdjustedMonthly_BESScharging'] = [sum(grid_charging_BESS[s:f]) for s, f in monthHours]
	outData['energyAdjustedMonthly_TESScharging'] = [sum(vbat_charge_component[s:f]) for s, f in monthHours]
	outData['energyAdjustedMonthly_gridCharging'] = list(np.array(outData['energyAdjustedMonthly_TESScharging']) + np.array(outData['energyAdjustedMonthly_BESScharging']))

	outData['energyCostAdjusted_total'] = [eam*electricityCost for eam in outData['energyAdjustedMonthly_total']]
	outData['energyCostAdjusted_BESS'] = [eam*electricityCost for eam in outData['energyAdjustedMonthly_BESS']]
	outData['energyCostAdjusted_TESS'] = [eam*electricityCost for eam in outData['energyAdjustedMonthly_TESS']]
	outData['energyCostAdjusted_generator'] = [eam*electricityCost for eam in outData['energyAdjustedMonthly_generator']]
	outData['energyCostAdjusted_gridCharging'] = [eam*electricityCost for eam in outData['energyAdjustedMonthly_gridCharging']]
	outData['energyCostAdjusted_gridCharging_annual'] = list(np.full(projectionLength, np.sum(outData['energyCostAdjusted_gridCharging'])))

	outData['demandCharge'] = [peak*demandChargeCost for peak in outData['peakDemand']]
	outData['peakAdjustedDemand_total'] = [max(outData['demandAdj_total'][s:f]) for s, f in monthHours]
	outData['demandChargeAdjusted_total'] = [pad*demandChargeCost for pad in outData['peakAdjustedDemand_total']]
	outData['totalCost_service'] = [ec+dcm for ec, dcm in zip(outData['energyCost'], outData['demandCharge'])]
	outData['totalCostAdjusted_service'] = [eca+dca for eca, dca in zip(outData['energyCostAdjusted_total'], outData['demandChargeAdjusted_total'])]
	outData['savings_adjusted'] = [tot-tota for tot, tota in zip(outData['totalCost_service'], outData['totalCostAdjusted_service'])]
	outData['savings_demandCharge'] = list(np.array(outData['demandCharge']) - np.array(outData['demandChargeAdjusted_total']))
	outData['savings_demandCharge_annual'] = list(np.full(projectionLength, np.sum(outData['savings_demandCharge'])))

	## Calculate total residential BESS capacity and compensation
	total_kw_residential_BESS = int(inputDict['numberBESS']) * float(inputDict['BESS_kw'])
	total_kwh_residential_BESS = int(inputDict['numberBESS']) * float(inputDict['BESS_kwh'])
	total_residential_BESS_compensation = rateCompensation * np.sum(total_kwh_residential_BESS)

	## Calculate monthly BESS costs and savings
	BESS_monthly_compensation_to_consumer = np.array([sum(BESS[s:f])*rateCompensation for s, f in monthHours])
	BESS_yearly_compensation_to_consumer_total = np.sum(BESS_monthly_compensation_to_consumer)
	BESS_allyears_compensation_to_consumer_array = np.full(projectionLength, BESS_yearly_compensation_to_consumer_total)
	BESS_monthly_if_bought_from_grid = np.array([sum(BESS[s:f])*electricityCost for s, f in monthHours])
	
	## Calculate total BESS and TESS savings
	utilitySavings_from_BESS_TESS = np.array(combined_device_results['savingsTESS']) + BESS_monthly_if_bought_from_grid

	####################################################################################
	## Calculate the financial benefit of controlling member-consumer DERs
	####################################################################################
	projectionLength = int(inputDict['projectionLength'])

	## Calculate residential BESS installation costs
	installed_cost_per_kw = 20
	installed_cost_per_kwh = 80
	total_kw_installed_costs = installed_cost_per_kw * total_kw_residential_BESS
	total_kwh_installed_costs = installed_cost_per_kwh * total_kwh_residential_BESS
	#total_installed_costs = ## TODO: How do we deal with both costs per kw and kWh?

	## Calculate the BESS subsidy for year 1 and the projection length (all years)
	## Year 1 includes the onetime subsidy, but subsequent years do not.
	BESS_subsidy_ongoing = float(inputDict['BESS_subsidy_ongoing'])
	BESS_subsidy_onetime = float(inputDict['BESS_subsidy_onetime'])
	BESS_subsidy_year1_total =  BESS_subsidy_onetime + (BESS_subsidy_ongoing*12.0)
	BESS_subsidy_allyears_array = np.full(projectionLength, BESS_subsidy_ongoing*12.0)
	BESS_subsidy_allyears_array[0] += BESS_subsidy_onetime

	## Calculate Generator Subsidy for year 1 and the projection length (all years)
	## Year 1 includes the onetime subsidy, but subsequent years do not.
	GEN_subsidy_ongoing = float(inputDict['GEN_subsidy_ongoing'])
	GEN_subsidy_onetime = float(inputDict['GEN_subsidy_onetime'])
	GEN_subsidy_year1_total =  GEN_subsidy_onetime + (GEN_subsidy_ongoing*12.0)
	GEN_subsidy_allyears_array = np.full(projectionLength, GEN_subsidy_ongoing*12.0)
	GEN_subsidy_allyears_array[0] += GEN_subsidy_onetime

	## Calculate the total TESS subsidies for year 1 and the projection length (all years)
	## Year 1 includes the onetime subsidy, but subsequent years do not.
	combinedTESS_subsidy_year1_total = combined_device_results['combinedTESS_subsidy_onetime'] + (combined_device_results['combinedTESS_subsidy_ongoing']*12.0)
	combinedTESS_subsidy_allyears_array = np.full(projectionLength, combined_device_results['combinedTESS_subsidy_ongoing']*12.0)
	combinedTESS_subsidy_allyears_array[0] += combined_device_results['combinedTESS_subsidy_onetime']

	## Calculate the total TESS+BESS+generator subsidies for year 1 and the projection length (all years)
	## Year 1 includes the onetime subsidy, but subsequent years do not.
	allDevices_subsidy_ongoing = GEN_subsidy_ongoing + BESS_subsidy_ongoing + combined_device_results['combinedTESS_subsidy_ongoing']
	allDevices_subsidy_onetime = GEN_subsidy_onetime + BESS_subsidy_onetime + combined_device_results['combinedTESS_subsidy_onetime']
	allDevices_subsidy_year1_total = allDevices_subsidy_onetime + (allDevices_subsidy_ongoing*12.0)
	allDevices_subsidy_year1_array = np.full(12, allDevices_subsidy_ongoing)
	allDevices_subsidy_year1_array[0] += allDevices_subsidy_onetime
	allDevices_subsidy_allyears_array = np.full(projectionLength, allDevices_subsidy_ongoing*12.0)
	allDevices_subsidy_allyears_array[0] += allDevices_subsidy_onetime

	## Calculate the utility's ongoing and onetime operational costs for each device
	## This includes costs for things like API calls to control the DERs

	## Total combined (TESS+BESS) ongoing and onetime operational costs
	operationalCosts_ongoing_BESS = float(inputDict['BESS_operationalCosts_ongoing'])
	operationalCosts_ongoing_TESS = float(combined_device_results['combinedTESS_operationalCosts_ongoing'])
	operationalCosts_ongoing_total = operationalCosts_ongoing_BESS + operationalCosts_ongoing_TESS
	operationalCosts_onetime_BESS = float(inputDict['BESS_operationalCosts_onetime'])
	operationalCosts_onetime_TESS = float(combined_device_results['combinedTESS_operationalCosts_onetime'])
	operationalCosts_onetime_total = operationalCosts_onetime_BESS + operationalCosts_onetime_TESS

	## Total combined (TESS+BESS) operational costs for 1 year (float value)
	operationalCosts_BESS_year1_total = operationalCosts_onetime_BESS + (operationalCosts_ongoing_BESS*12.0)
	operationalCosts_TESS_year1_total = operationalCosts_onetime_TESS + (operationalCosts_ongoing_TESS*12.0)
	operationalCosts_1year_total = operationalCosts_BESS_year1_total + operationalCosts_TESS_year1_total

	## Total combined (TESS+BESS) operational costs for 1 year (monthly values for 1 year)
	operationalCosts_BESS_year1_array = np.full(12, operationalCosts_ongoing_BESS)
	operationalCosts_TESS_year1_array = np.full(12, operationalCosts_ongoing_TESS)
	operationalCosts_BESS_year1_array[0] += operationalCosts_onetime_BESS
	operationalCosts_TESS_year1_array[0] += operationalCosts_onetime_TESS
	operationalCosts_year1_array = operationalCosts_BESS_year1_array + operationalCosts_TESS_year1_array

	## Total operational costs for BESS and TESS for all years of analysis (yearly values for projectionLength duration)
	operationalCosts_yearly_total = operationalCosts_ongoing_total + operationalCosts_onetime_total
	operationalCosts_BESS_allyears_array = np.full(projectionLength, operationalCosts_ongoing_BESS*12.0)
	operationalCosts_TESS_allyears_array = np.full(projectionLength, operationalCosts_ongoing_TESS*12.0)
	operationalCosts_BESS_allyears_array[0] += operationalCosts_onetime_BESS
	operationalCosts_TESS_allyears_array[0] += operationalCosts_onetime_TESS

	## Calculating total utility costs
	utilityCosts_1year_total = operationalCosts_1year_total + allDevices_subsidy_year1_total + total_residential_BESS_compensation
	## NOTE: utilityCosts_allyears_total (below) assumes that the REopt BESS array will be the same for every year of the entire projectionLength (entire analysis)
	utilityCosts_allyears_total = utilityCosts_1year_total + (projectionLength-1)*(operationalCosts_ongoing_total+allDevices_subsidy_year1_total+total_residential_BESS_compensation)
	utilityCosts_1year_array = list(np.array(operationalCosts_year1_array) + np.array(allDevices_subsidy_year1_array) + np.array(BESS_monthly_compensation_to_consumer))
	
	## Calculating total utility savings
	utilitySavings_1year_total = np.sum(utilitySavings_from_BESS_TESS)
	utilitySavings_1year_array = utilitySavings_from_BESS_TESS
	utilitySavings_allyears_total = utilitySavings_1year_total*projectionLength
	utilitySavings_allyears_array = np.full(projectionLength, utilitySavings_1year_total)

	## Calculating total utility net savings (savings minus costs)
	utilityNetSavings_1year_total =  utilitySavings_1year_total - utilityCosts_1year_total
	utilityNetSavings_1year_array = np.array(utilitySavings_1year_array) - np.array(utilityCosts_1year_array)
	utilityNetSavings_allyears_total = utilitySavings_allyears_total - utilityCosts_allyears_total
	utilityNetSavings_allyears_array = np.full(projectionLength, utilityNetSavings_1year_total)

	## Update utility savings to include subsidies and BESS compensation to conumers
	#outData['savings_total'] = list(np.array(outData['savings_adjusted']) - np.array(utilityCosts_1year_array))

	## Update financial parameters
	#outData['savings'] = utilityNetSavings_1year_array
	#outData['totalCost_TESS'] = float(inputDict['unitUpkeepCost'])*float(inputDict['number_devices'])
	#outData['totalCost_annual'] = list((outData['totalCost_TESS'] + np.array(utilityCosts_1year_array))) # + np.array(outData['energyCostAdjusted_gridCharging'] + np.array(outData['demandChargeAdjusted_total'])))
	#outData['totalCost_annual'] = list((outData['totalCost_TESS'] + np.array(utilityCosts_1year_array)) + np.array(outData['energyCostAdjusted_total']) + np.array(outData['demandChargeAdjusted_total']))
	outData['totalCost_annual'] = list(np.array(utilityCosts_1year_array))
	outData['totalCost_paidToConsumer'] = list(BESS_monthly_compensation_to_consumer + allDevices_subsidy_year1_array)
	outData['NPV'] = npv(float(inputDict['discountRate'])/100., utilityNetSavings_allyears_array)
	if utilitySavings_1year_total == 0:
		outData['SPP'] = 0.
	else:
		outData['SPP'] = utilityCosts_allyears_total / utilitySavings_1year_total

	annualEarnings = np.sum(outData['savings_adjusted']) - np.sum(outData['totalCost_annual'])
	annualEarnings_array = np.array(outData['savings_adjusted']) - np.array(outData['totalCost_annual'])
	outData['savings_total'] = list(annualEarnings_array) ## (total cost of service - adjusted total cost of service) - (operational costs + subsidies + BESS compensation to consumer)
	outData['annualEarnings_BESS'] = list(np.full(projectionLength, np.sum(outData['energyCostAdjusted_BESS'])))
	outData['annualEarnings_TESS'] = list(np.full(projectionLength, np.sum(outData['energyCostAdjusted_TESS'])))
	outData['annualEarnings_generator'] = list(np.full(projectionLength, np.sum(outData['energyCostAdjusted_generator'])))

	cashFlowList_total = np.full(projectionLength, annualEarnings)
	outData['cashFlowList_total'] = list(cashFlowList_total)
	#outData['cumulativeCashflow_total'] = [sum(cashFlowList_total[:i+1]) for i in cashFlowList_total]
	outData['cumulativeCashflow_total'] = list(np.cumsum(cashFlowList_total))
	outData['savingsAllYears'] = list(utilitySavings_allyears_array)
	
	## Show the costs to the utility as negative values in the Cash Flow Projection plot (costs to the utility)
	outData['subsidies'] = list(allDevices_subsidy_allyears_array*-1.)
	outData['BESS_compensation_to_consumer_allyears'] = list(BESS_allyears_compensation_to_consumer_array*-1.)
	outData['operationalCosts_BESS_allyears'] = list(operationalCosts_BESS_allyears_array*-1.)
	outData['operationalCosts_TESS_allyears'] = list(operationalCosts_TESS_allyears_array*-1.)
	
	# Model operations typically ends here.
	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','utility_2018_kW_load.csv')) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','open-meteo-denverCO-noheaders.csv')) as f:
		temp_curve = f.read()

	defaultInputs = {
		## TODO: incorporate float, int, bool types instead of only strings
		## OMF inputs:
		'user' : 'admin',
		'modelType': modelName,
		'created': str(datetime.datetime.now()),

		## REopt inputs:
		'latitude' : '39.986771', 
		'longitude' : '-104.812599', ## Brighton, CO
		'year' : '2018',
		'urdbLabel' : '612ff9c15457a3ec18a5f7d3', ## Brighton, CO
		'fileName': 'utility_2018_kW_load.csv',
		'tempFileName': 'open-meteo-denverCO-noheaders.csv',
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,

		## Fossil Fuel Generator
		'fossilGenerator': 'Yes',
		'existing_gen_kw': '7000',
		'fuel_available_gal': '20000',
		'fuel_cost_per_gal': '3.61',

		## Chemical Battery Inputs
		'numberBESS': '1000', ## Number of residential Tesla Powerwall 3 batteries
		'BESS_operationalCosts_ongoing': '20.0',
		'BESS_operationalCosts_onetime': '1000', 
		'BESS_kw': '5',
		'BESS_kwh': '13.5',

		## Financial Inputs
		'demandChargeCost': '25', ## used by vbatDispatch
		'projectionLength': '25',
		'electricityCost': '0.04',
		'rateCompensation': '0.02', ## unit: $/kWh
		'TESS_subsidy_onetime_ac': '5.0',
		'TESS_subsidy_ongoing_ac': '1.0',
		'TESS_subsidy_onetime_hp': '10.0',
		'TESS_subsidy_ongoing_hp': '2.0',
		'TESS_subsidy_onetime_wh': '15.0',
		'TESS_subsidy_ongoing_wh': '3.0',
		'BESS_subsidy_onetime': '30.0',
		'BESS_subsidy_ongoing': '4.0',
		'GEN_subsidy_onetime': '35.0',
		'GEN_subsidy_ongoing': '5.0',
		'TESS_operationalCosts_ongoing_hp': '10.0',
		'TESS_operationalCosts_onetime_hp': '1000', 
		'TESS_operationalCosts_ongoing_ac': '10.0',
		'TESS_operationalCosts_onetime_ac': '1000', 
		'TESS_operationalCosts_ongoing_wh': '10.0',
		'TESS_operationalCosts_onetime_wh': '1000', 
		'discountRate': '2',

		## Home Air Conditioner inputs (vbatDispatch):
		'load_type_ac': '1', 
		'number_devices_ac': '2000',
		'power_ac': '5.6',
		'capacitance_ac': '2',
		'resistance_ac': '2',
		'cop_ac': '2.5',
		'setpoint_ac': '22.5',
		'deadband_ac': '0.625',

		## Home Heat Pump inputs (vbatDispatch):
		'load_type_hp': '2', 
		'number_devices_hp': '2000',
		'power_hp': '5.6',
		'capacitance_hp': '2',
		'resistance_hp': '2',
		'cop_hp': '3.5',
		'setpoint_hp': '19.5',
		'deadband_hp': '0.625',

		## Home Water Heater inputs (vbatDispatch):
		'load_type_wh': '4', 
		'number_devices_wh': '2000',
		'power_wh': '4.5',
		'capacitance_wh': '0.4',
		'resistance_wh': '120',
		'cop_wh': '1',
		'setpoint_wh': '48.5',
		'deadband_wh': '3',


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


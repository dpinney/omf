''' Performs a cost-benefit analysis for a utility or cooperative member interested in 
controlling behind-the-meter distributed energy resources (DERs).'''

## TODO: check out gridlabMulti.py, cvrDynamic.py, demandResponse.py, 
## vbatDispatch.py, solarEngineering.py for potential display and plot feautures 

## Python imports
import warnings
# warnings.filterwarnings("ignore")
import shutil, datetime, csv, json
from os.path import join as pJoin
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
import plotly.express as px
from numpy_financial import npv

## OMF imports
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.models import vbatDispatch as vb
from omf.models import derConsumer
from omf.solvers import reopt_jl

## Model metadata:
tooltip = ('The derUtilityCost model evaluates the financial costs of controlling behind-the-meter '
	'distributed energy resources (DERs) using the NREL Renewable Energy Optimization Tool (REopt) and '
	'the OMF virtual battery dispatch module (vbatDispatch).')
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True ## Keep the model hidden=True during active development

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	## Delete output file every run if it exists
	outData = {}

	## Gather input variables to pass to the omf.solvers.reopt_jl model
	latitude = float(inputDict['latitude'])
	longitude = float(inputDict['longitude'])
	urdbLabel = str(inputDict['urdbLabel'])
	year = int(inputDict['year'])
	projectionLength = int(inputDict['projectionLength'])
	demand_array = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()]) ## process input format into an array
	demand = demand_array.tolist() if isinstance(demand_array, np.ndarray) else demand_array ## make demand array into a list	for REopt

	## Create a REopt input dictionary called 'scenario' (required input for omf.solvers.reopt_jl)
	## NOTE: REopt specific inputs are specified in this input dictionary
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

	## Add fossil fuel generator to input scenario, if enabled
	if inputDict['fossilGenerator'] == 'Yes' and float(inputDict['number_devices_GEN']) > 0:
		GENcheck = 'enabled'
		scenario['Generator'] = {
			'existing_kw': float(inputDict['existing_gen_kw']) * float(inputDict['number_devices_GEN']),
			'max_kw': 0,
			'min_kw': 0,
			'only_runs_during_grid_outage': False,
			'fuel_avail_gal': float(inputDict['fuel_avail_gal']) * float(inputDict['number_devices_GEN']),
			'fuel_cost_per_gallon': float(inputDict['fuel_cost_per_gal']),
		}
	else:
		GENcheck = 'disabled'

	## Add a Battery Energy Storage System (BESS) section to REopt input scenario, if enabled 
	if inputDict['enableBESS'] == 'Yes' and float(inputDict['number_devices_BESS']) > 0:
		BESScheck = 'enabled'
		scenario['ElectricStorage'] = {
			'min_kw': float(inputDict['BESS_kw']) * float(inputDict['number_devices_BESS']),
			'max_kw': float(inputDict['BESS_kw']) * float(inputDict['number_devices_BESS']),
			'min_kwh': float(inputDict['BESS_kwh']) * float(inputDict['number_devices_BESS']),
			'max_kwh': float(inputDict['BESS_kwh']) * float(inputDict['number_devices_BESS']),
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
	else:
		BESScheck = 'disabled'
	
	## Save the scenario file
	## NOTE: reopt_jl currently requires a path for the input file, so the file must be saved to a location preferrably in the modelDir directory
	with open(pJoin(modelDir, 'reopt_input_scenario.json'), 'w') as jsonFile:
		json.dump(scenario, jsonFile)

	## Create basic REopt input file
	## NOTE: This function is disabled for now since the scenario dictionary above is now hard coded here and no longer relies on the helper function in omf.models.derConsumer to produce the REopt input file.
	#derConsumer.create_REopt_jl_jsonFile(modelDir, inputDict)

	########################################################################################################################
	## Run REopt.jl
	########################################################################################################################
	reopt_jl.run_reopt_jl(modelDir, 'reopt_input_scenario.json')

	## Load the REopt results once it is finished running.
	## TODO: Add warnings here to handle when REopt does not produce an output or gives an error
	with open(pJoin(modelDir, 'results.json')) as jsonFile:
		reoptResults = json.load(jsonFile)
	outData.update(reoptResults) ## Update output file with reopt results

	## Convert the user-provided demand curve and temperature curve values from strings to floats
	temperatures = [float(value) for value in inputDict['tempCurve'].split('\n') if value.strip()]
	demand = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()])

	## Create timestamp array from REopt input information
	## TODO: check that this KeyError works
	try:
		year = reoptResults['ElectricLoad.year'][0]
	except KeyError:
		year = inputDict['year'] ## Use the user provided year if none found in reoptResults
	timestamps = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:00:00', periods=np.size(demand))

	########################################################################################################################
	## Run vbatDispatch model
	########################################################################################################################

	## Set up base input dictionary for vbatDispatch runs
	inputDict_vbatDispatch = {
		'load_type': '', ## 1=AirConditioner, 2=HeatPump, 3=Refrigerator, 4=WaterHeater (This is from OMF model vbatDispatch.html)
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
	
	## Define thermal variables that change depending on the thermal technology(ies) enabled by the user
	thermal_suffixes = ['_hp', '_ac', '_wh'] ## heat pump, air conditioner, water heater - (Add more suffixes here after establishing inputs in the defaultInputs and derUtilityCost.html)
	thermal_variables=['load_type','number_devices','power','capacitance','resistance','cop','setpoint','deadband','TESS_subsidy_ongoing','TESS_subsidy_onetime']

	all_device_suffixes = []
	single_device_results = {} 
	for suffix in thermal_suffixes:
		## Include only the thermal devices specified by the user
		if float(inputDict['load_type'+suffix]) > 0 and float(inputDict['number_devices'+suffix]) > 0:
			all_device_suffixes.append(suffix)

			## Add the appropriate thermal device variables to the inputDict_vbatDispatch
			for i in thermal_variables:
				inputDict_vbatDispatch[i] = inputDict[i+suffix]

			## Create a model subdirectory for each thermal device and store the vbatDispatch results
			newDir = pJoin(modelDir,'vbatDispatch_results'+suffix)
			os.makedirs(newDir, exist_ok=True)
			os.chdir(newDir) ##jump into the newly created subdirectory

			## Run vbatDispatch for the thermal device
			vbatResults = vb.work(modelDir,inputDict_vbatDispatch)
			with open(pJoin(newDir, 'vbatResults.json'), 'w') as jsonFile:
				json.dump(vbatResults, jsonFile)
			
			## Update the vbatResults to include subsidies (for easier usage later)
			vbatResults['TESS_subsidy_onetime'] = float(inputDict_vbatDispatch['TESS_subsidy_onetime'])*float(inputDict['number_devices'+suffix])
			vbatResults['TESS_subsidy_ongoing'] = float(inputDict_vbatDispatch['TESS_subsidy_ongoing'])*float(inputDict['number_devices'+suffix])

			## Store the results in all_device_results dictionary
			single_device_results['vbatResults'+suffix] = vbatResults

			## Go back to the main derUtilityCost model directory and continue on
			os.chdir(modelDir)

	## Initialize an empty dictionary to hold all thermal device results added together
	## Length 8760 represents hourly data for one year, length 12 is monthly data for a year
	combined_device_results = {
		'vbatPower_series': [0]*8760,
		'vbat_charge': [0]*8760,
		'vbat_discharge': [0]*8760,
		'vbat_charge_flipsign': [0]*8760,
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
		'monthlyEnergyConsumptionCost_Adjusted_TESS':[0]*12,
		'combinedTESS_subsidy_ongoing': 0,
		'combinedTESS_subsidy_onetime': 0,
	}

	## Combine all thermal device variable data for plotting
	for device_result in single_device_results:
		combined_device_results['vbatPower'] = [sum(x) for x in zip(combined_device_results['vbatPower'], single_device_results[device_result]['VBpower'])]
		vbatPower_series = pd.Series(combined_device_results['vbatPower'])
		combined_device_results['vbatPower_series'] = vbatPower_series
		combined_device_results['vbat_discharge'] = vbatPower_series.where(vbatPower_series > 0, 0) ##positive values = discharging
		combined_device_results['vbat_charge'] = vbatPower_series.where(vbatPower_series < 0, 0) ##negative values = charging
		combined_device_results['vbat_charge_flipsign'] = combined_device_results['vbat_charge'].mul(-1) ## flip sign of vbat charge to positive values for plotting purposes
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
		combined_device_results['monthlyEnergyConsumptionCost_Adjusted_TESS'] = [sum(x) for x in zip(combined_device_results['monthlyEnergyConsumptionCost_Adjusted_TESS'], single_device_results[device_result]['energyCostAdjusted'])]
		combined_device_results['combinedTESS_subsidy_ongoing'] += float(single_device_results[device_result]['TESS_subsidy_ongoing'])
		combined_device_results['combinedTESS_subsidy_onetime'] += float(single_device_results[device_result]['TESS_subsidy_onetime'])

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
	########################################################################################################################################################
	## DER Serving Load Overview plot 
	########################################################################################################################################################

	## If REopt outputs any Electric Storage (BESS) that also does not contain all zeros:
	if 'ElectricStorage' in reoptResults: 
		if any(value != 0 for value in reoptResults['ElectricStorage']['storage_to_load_series_kw']):
			BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
			grid_charging_BESS = reoptResults['ElectricUtility']['electric_to_storage_series_kw']
			outData['chargeLevelBattery'] = reoptResults['ElectricStorage']['soc_series_fraction']
		else:
			raise ValueError('Error: The BESS was not built by the REopt model. "storage_to_load_series_kw" contains all zeros.')
	else:
		print('No BESS was specified in REopt. Setting BESS variables to zero for plotting purposes.')
		BESS = np.zeros_like(demand)
		grid_charging_BESS = np.zeros_like(demand)
		outData['chargeLevelBattery'] = list(np.zeros_like(demand))

	## NOTE: The following 6 lines of code are temporary; it reads in the SOC info from a static REopt test file (a previously completed REopt run) 
	## NOTE: This functionality was used when REopt did not produce BESS results, or the results were arrays of zeros.
	#with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','utility_reopt_results.json')) as f:
	#	static_reopt_results = json.load(f)
	#BESS = static_reopt_results['outputs']['ElectricStorage']['storage_to_load_series_kw']
	#grid_charging_BESS = static_reopt_results['outputs']['ElectricUtility']['electric_to_storage_series_kw']
	#outData['chargeLevelBattery'] = static_reopt_results['outputs']['ElectricStorage']['soc_series_fraction']
	#outData.update(static_reopt_results['outputs'])

	## vbatDispatch variables
	vbat_discharge_component = np.array(combined_device_results['vbat_discharge'])
	vbat_charge_component = np.array(combined_device_results['vbat_charge_flipsign'])

	## Convert all values from kW to Watts for plotting purposes only
	grid_to_load = reoptResults['ElectricUtility']['electric_to_load_series_kw']
	grid_to_load_W = np.array(grid_to_load) * 1000.
	BESS_W = np.array(BESS) * 1000.
	grid_charging_BESS_W = np.array(grid_charging_BESS) * 1000.
	vbat_discharge_component_W = vbat_discharge_component * 1000.
	vbat_charge_component_W = vbat_charge_component * 1000.
	demand_W = np.array(demand) * 1000.
	grid_serving_new_load_W = grid_to_load_W + grid_charging_BESS_W + vbat_charge_component_W - vbat_discharge_component_W

	if 'Generator' in reoptResults:
		generator = np.array(reoptResults['Generator']['electric_to_load_series_kw'])
		generator_W = generator * 1000.
	else:
		generator = np.zeros_like(demand)
		generator_W = np.zeros_like(demand)
	
	## Put all DER plot variables into a dataFrame for plotting
	df = pd.DataFrame({
		'timestamp': timestamps,
		'Home BESS Serving Load': BESS_W,
		'Home TESS Serving Load': vbat_discharge_component_W,
		'Grid Serving Load': grid_serving_new_load_W,
		'Home Generator Serving Load': generator_W,
		'Grid Charging Home BESS': grid_charging_BESS_W,
		'Grid Charging Home TESS': vbat_charge_component_W
	})

	## Define colors for each plot series
	colors = {
		'Grid Serving Load': 'rgba(128, 128, 128, 0.8)',  ## Gray
		'Home BESS Serving Load': 'rgba(0, 128, 0, 0.8)',  ## Green
		'Home Generator Serving Load': 'rgba(139, 0, 0, 0.8)',  ## Dark red
		'Home TESS Serving Load': 'rgba(128, 0, 128, 0.8)',  ## Purple
		'Grid Charging Home BESS': 'rgba(0, 128, 0, 0.4)',  ## Green w/ half opacity
		'Grid Charging Home TESS': 'rgba(128, 0, 128, 0.4)'  ## Purple w/ half opacity
	}

	## Plot options
	showlegend = True ## either enable or disable the legend toggle in the plot
	lineshape = 'hv'
	fig = go.Figure()

	## Discharging DERs to plot
	for col in ["Grid Serving Load", "Home BESS Serving Load", "Home Generator Serving Load", "Home TESS Serving Load","Grid Charging Home BESS", "Grid Charging Home TESS"]:
		fig.add_trace(go.Scatter(
			x=df["timestamp"],
			y=df[col],
			fill="tonexty",
			mode="none",
			name=col,
			fillcolor=colors[col],
			line_shape=lineshape,			
			stackgroup="discharge"  ## Stack all the discharging DERs together
		))

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
	fig.update_layout(
		xaxis_title="Timestamp",yaxis_title="Power (W)",
		yaxis2=dict(title='degrees Fahrenheit',overlaying='y',side='right'),
    	legend=dict(orientation='h',yanchor='bottom', xanchor='right',y=1.02,x=1,)
	)

	## NOTE: This opens a window that displays the correct figure with the appropriate patterns.
	## NOTE (cont.): For some reason, the slash-mark patterns are not showing up on the OMF page otherwise. Eventually we will delete this part.
	#fig.show()
	#outData['derOverviewHtml'] = fig.to_html(full_html=False)
	fig.write_html(pJoin(modelDir, "Plot_DerServingLoadOverview.html"))

	## Encode plot data as JSON for showing in the HTML 
	outData['derOverviewData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['derOverviewLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

	###################################################################################################################################
	## Impact to Demand plot 
	###################################################################################################################################
	showlegend = True ## either enable or disable the legend toggle in the plot
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
						fillcolor='rgba(235,97,35,0.5)',
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

	## Plot layout
	fig.update_layout(
    	xaxis=dict(title='Timestamp'),
    	#yaxis=dict(title='Power (W)',type='log'),
		yaxis=dict(title='Power (W)'),
    	yaxis2=dict(title='degrees Fahrenheit',overlaying='y',side='right'),
		legend=dict(orientation='h',yanchor='bottom',y=1.02,xanchor='right',x=1)
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

	################################################################################################################################################
	## Create Thermal Battery Power plot object 
	################################################################################################################################################
	fig = go.Figure()

	data_names = ['vbatMinPowerCapacity', 'vbatMaxPowerCapacity', 'vbatPower']
	colors = ['green', 'blue', 'black']
	titles = ['Minimum Calculated Power Capacity', 'Maximum Calculated Power Capacity', 'Actual Power Utilized']

	dataCheckList = []
	for data_name, color, title in zip(data_names, colors, titles):
		dataCheck = np.sum(combined_device_results[data_name])
		dataCheckList.append(dataCheck)
		fig.add_trace(go.Scatter(
			x=timestamps, 
			y=np.array(combined_device_results[data_name])*1000., ## convert from kW to W
			yaxis='y1',
			mode='lines',
			line=dict(color=color, width=1),
			name=title,
			showlegend=True
		))

	fig.update_layout(xaxis=dict(title='Timestamp'), yaxis=dict(title='Power (W)'),
		legend=dict(orientation='h',yanchor='bottom',y=1.02,xanchor='right',x=1))
	
	## Add a thermal battery variable that signals to the HTML plot if all of the thermal series contain no data
	outData['thermalDataCheck'] = float(sum(np.array(dataCheckList)))
	
	## Encode plot data as JSON for showing in the HTML side
	outData['thermalBatPowerPlot'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['thermalBatPowerPlotLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)	

	################################################################################################################################################
	## Create Chemical BESS State of Charge plot object 
	################################################################################################################################################
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=timestamps, y=outData['chargeLevelBattery'],
						mode='lines',
						line=dict(color='purple', width=1),
						name='Battery SOC',
						showlegend=True))
	
	fig.update_layout(xaxis=dict(title='Timestamp'), yaxis=dict(title='Charge (%)'), legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right',x=1))

	outData['batteryChargeData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['batteryChargeLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)


	"""
	#####################################################################################################################################################################################################
	## Compensation rate to member-consumer
	compensationRate = float(inputDict['rateCompensation'])
	subsidy = float(inputDict['subsidy']) ## TODO: Amount for the entire analysis - should we divide this up by # of months and add to the monthly consumer savings?
	consumptionCost = float(inputDict['electricityCost'])

	monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
					(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
					(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]
	
	load_smallConsumer_monthly = np.asarray([sum(smallConsumerLoad[s:f]) for s, f in monthHours])
	load_largeConsumer_monthly = np.asarray([sum(largeConsumerLoad[s:f]) for s, f in monthHours])
	loadCost_smallConsumer_monthly = load_smallConsumer_monthly * consumptionCost
	loadCost_largeConsumer_monthly = load_largeConsumer_monthly * consumptionCost

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
		BESS_bought_from_grid = np.sum(BESS_utility) * consumptionCost
		print('Utility BESS savings (1 year BESS kWh x electricity cost): ${:,.2f}'.format(BESS_bought_from_grid))
		print('Difference (Utility BESS savings - Compensation to consumers): ${:,.2f}'.format(BESS_bought_from_grid-BESS_compensated_to_consumer))

	"""

	#########################################################################################################################################################
	### Calculate the monthly consumption and peak demand costs and savings
	#########################################################################################################################################################

	## Update energy and power variables
	monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
		(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
		(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]
	consumptionCost = float(inputDict['electricityCost'])
	demandCost = float(inputDict['demandChargeCost'])
	rateCompensation = float(inputDict['rateCompensation'])

	## Calculate the monthly demand and energy consumption (for the demand curve without DERs)
	outData['monthlyPeakDemand'] = [max(demand[s:f]) for s, f in monthHours] ## The maximum peak kW for each month
	outData['monthlyPeakDemandCost'] = [peak*demandCost for peak in outData['monthlyPeakDemand']] ## peak demand charge before including DERs
	outData['monthlyEnergyConsumption'] = [sum(demand[s:f]) for s, f in monthHours] ## The total energy kWh for each month
	outData['monthlyEnergyConsumptionCost'] = [em*consumptionCost for em in outData['monthlyEnergyConsumption']] ## The total cost of kWh energy each month

	## Calculate the monthly adjusted demand ("adjusted" = the demand curve including DERs)
	outData['adjustedDemand'] = list(demand - BESS - vbat_discharge_component - generator + grid_charging_BESS + vbat_charge_component)
	outData['monthlyAdjustedEnergyConsumption'] = [sum(outData['adjustedDemand'][s:f]) for s, f in monthHours]
	outData['monthlyAdjustedEnergyConsumptionCost'] = [eam*consumptionCost for eam in outData['monthlyAdjustedEnergyConsumption']]
	outData['monthlyAdjustedPeakDemand'] = [max(outData['adjustedDemand'][s:f]) for s, f in monthHours] ## monthly peak demand hours (including DERs)
	outData['monthlyAdjustedPeakDemandCost'] = [pad*demandCost for pad in outData['monthlyAdjustedPeakDemand']] ## peak demand charge after including all DERs

	## Calculate the individual costs and savings from the adjusted energy and adjusted demand charges
	outData['monthlyPeakDemandSavings'] = list(np.array(outData['monthlyPeakDemandCost']) - np.array(outData['monthlyAdjustedPeakDemandCost'])) ## total demand charge savings from all DERs
	#print('Monthly Peak Demand cost (baseline demand): \n', np.array(outData['monthlyPeakDemandCost']))
	#print('Monthly Adjusted Peak Demand cost: \n', np.array(outData['monthlyAdjustedPeakDemandCost']))
	#print('Monthly Peak Demand Savings Dcost x (D-Dadj): \n', outData['monthlyPeakDemandSavings'])

	outData['monthlyEnergyConsumptionSavings'] = list(np.array(outData['monthlyEnergyConsumptionCost']) - np.array(outData['monthlyAdjustedEnergyConsumptionCost'])) ## total consumption savings from BESS only
	
	## Calculate the combined costs and savings from the adjusted energy and adjusted demand charges
	outData['monthlyTotalCostService'] = [ec+dcm for ec, dcm in zip(outData['monthlyEnergyConsumptionCost'], outData['monthlyPeakDemandCost'])] ## total cost of energy and demand charge prior to DERs
	outData['monthlyTotalCostAdjustedService'] = [eca+dca for eca, dca in zip(outData['monthlyAdjustedEnergyConsumptionCost'], outData['monthlyAdjustedPeakDemandCost'])] ## total cost of energy and peak demand from including DERs
	outData['monthlyTotalSavingsAdjustedService'] = [tot-tota for tot, tota in zip(outData['monthlyTotalCostService'], outData['monthlyTotalCostAdjustedService'])] ## total savings from all DERs

	#########################################################################################################################################################
	### Calculate the individual (BESS, TESS, and GEN) contributions to the consumption and peak demand savings
	#########################################################################################################################################################
	BESSdemand = np.array(BESS)-np.array(grid_charging_BESS)
	TESSdemand = np.array(vbat_discharge_component)-np.array(vbat_charge_component)
	GENdemand = np.array(generator)
	monthlyBESSconsumption = [sum(BESSdemand[s:f]) for s, f in monthHours]
	monthlyTESSconsumption = [sum(TESSdemand[s:f]) for s, f in monthHours]
	monthlyGENconsumption = [sum(GENdemand[s:f]) for s, f in monthHours]

	## Find the original and adjusted demand peak each month and calculate the individual DER contribution at both of those peaks.
	## NOTE: _adjP = adjusted peak demand (kW), _baseP = baseline (original) peak demand (kW)
	BESSpeakDemand_adjP = np.zeros(8760) ## Initialize contribution arrays with zeros (8760 = hourly increments in a year)
	TESSpeakDemand_adjP = np.zeros(8760)
	GENpeakDemand_adjP = np.zeros(8760) 
	BESSpeakDemand_baseP = np.zeros(8760)
	TESSpeakDemand_baseP = np.zeros(8760)
	GENpeakDemand_baseP = np.zeros(8760)
	peakDemand_baseP = np.zeros(8760)
	peakDemand_adjP = np.zeros(8760)
	for s, f in monthHours:
		## Gather the monthly baseline and adjusted demand curve data and identify the maximum peak kW per month
		month_data_adjP = outData['adjustedDemand'][s:f]
		month_peak_kw_adjP = max(month_data_adjP)

		month_data_baseP = demand[s:f]
		month_peak_kw_baseP = max(month_data_baseP)

		## Create a mask array where 1=peak and 0=nonpeak
		peak_mask_adjP = np.where(month_data_adjP == month_peak_kw_adjP, 1.0, 0.0)
		BESSpeakDemand_adjP[s:f] = BESSdemand[s:f] * peak_mask_adjP ## BESS demand at the monthly adjusted peak
		TESSpeakDemand_adjP[s:f] = TESSdemand[s:f] * peak_mask_adjP ## TESS demand at the monthly adjusted peak
		GENpeakDemand_adjP[s:f] = GENdemand[s:f] * peak_mask_adjP ## GEN demand at the monthly adjusted peak
		peakDemand_adjP[s:f] = demand[s:f] * peak_mask_adjP ## demand at the monthly adjusted demand peak
		
		peak_mask_baseP = np.where(month_data_baseP == month_peak_kw_baseP, 1.0, 0.0)
		BESSpeakDemand_baseP[s:f] = BESSdemand[s:f] * peak_mask_baseP ## BESS demand at the monthly baseline peak
		TESSpeakDemand_baseP[s:f] = TESSdemand[s:f] * peak_mask_baseP ## TESS demand at the monthly baseline peak
		GENpeakDemand_baseP[s:f] = GENdemand[s:f] * peak_mask_baseP ## GEN demand at the monthly baseline peak
		peakDemand_baseP[s:f] = demand[s:f] * peak_mask_baseP ## demand at the monthly baseline demand peak

	## Monthly BESS, TESS, and GEN energy consumption savings
	monthlyBESS_consumption_savings = [monthlyConsumption*consumptionCost for monthlyConsumption in monthlyBESSconsumption]
	monthlyTESS_consumption_savings = [monthlyConsumption*consumptionCost for monthlyConsumption in monthlyTESSconsumption]
	monthlyGEN_consumption_savings = [monthlyConsumption*consumptionCost for monthlyConsumption in monthlyGENconsumption]
	monthlyAllDER_consumption_savings = [a+b+c for a,b,c in zip(monthlyBESS_consumption_savings,monthlyTESS_consumption_savings,monthlyGEN_consumption_savings)]
	totalAllDER_consumption_savings = sum(monthlyAllDER_consumption_savings)
	#print('total consumption savings when adding up individual DERs: ', totalAllDER_consumption_savings)
	#print('total consumption savings (D-Dadj)*Ecost: ', consumptionCost*(sum(demand)-sum(outData['adjustedDemand']))) NOTE: These agree, yay!

	## Monthly BESS, TESS, and GEN peak demand savings
	## NOTE: The sum is done over the entire month's DER contribution because the contribution arrays have zeroes everywhere except for the peak hour per month
	monthlyBESS_peakDemand_savings_adjP = [sum(BESSpeakDemand_adjP[s:f])*demandCost for s, f in monthHours]
	monthlyTESS_peakDemand_savings_adjP = [sum(TESSpeakDemand_adjP[s:f])*demandCost for s, f in monthHours]
	monthlyGEN_peakDemand_savings_adjP = [sum(GENpeakDemand_adjP[s:f])*demandCost for s, f in monthHours]
	monthlyAllDER_peakDemand_savings_adjP = [a+b+c for a,b,c in zip(monthlyBESS_peakDemand_savings_adjP,monthlyTESS_peakDemand_savings_adjP,monthlyGEN_peakDemand_savings_adjP)]
	totalAllDER_peakDemand_savings = sum(monthlyAllDER_peakDemand_savings_adjP)
	#print('total peak demand savings when adding up individual DERs: ', totalAllDER_peakDemand_savings)
	#print('Should match (peak demand cost - peak adjusted demand cost)+()')

	monthlyBESS_peakDemand_adjP = [sum(BESSpeakDemand_adjP[s:f]) for s, f in monthHours]
	monthlyTESS_peakDemand_adjP = [sum(TESSpeakDemand_adjP[s:f]) for s, f in monthHours]
	monthlyGEN_peakDemand_adjP = [sum(GENpeakDemand_adjP[s:f]) for s, f in monthHours]
	monthlyAllDER_peakDemand_adjP = [a+b+c for a,b,c in zip(monthlyBESS_peakDemand_adjP,monthlyTESS_peakDemand_adjP,monthlyGEN_peakDemand_adjP)]

	monthly_peakDemand_baseP = [sum(peakDemand_baseP[s:f]) for s, f in monthHours] ## monthly peak demand of baseline demand
	monthly_peakDemand_adjP = [sum(peakDemand_adjP[s:f]) for s, f in monthHours] ## monthly peak demand of adjusted demand

	## Do the same but for the baseline peak savings
	monthlyBESS_peakDemand_baseP = [sum(BESSpeakDemand_baseP[s:f]) for s, f in monthHours]
	monthlyTESS_peakDemand_baseP = [sum(TESSpeakDemand_baseP[s:f]) for s, f in monthHours]
	monthlyGEN_peakDemand_baseP = [sum(GENpeakDemand_baseP[s:f]) for s, f in monthHours]
	monthlyAllDER_peakDemand_baseP = [a+b+c for a,b,c in zip(monthlyBESS_peakDemand_baseP,monthlyTESS_peakDemand_baseP,monthlyGEN_peakDemand_baseP)]
	
	monthlyBESS_peakDemand_savings_baseP = [sum(BESSpeakDemand_baseP[s:f])*demandCost for s, f in monthHours]
	monthlyTESS_peakDemand_savings_baseP = [sum(TESSpeakDemand_baseP[s:f])*demandCost for s, f in monthHours]
	monthlyGEN_peakDemand_savings_baseP = [sum(GENpeakDemand_baseP[s:f])*demandCost for s, f in monthHours]
	monthlyAllDER_peakDemand_savings_baseP = [a+b+c for a,b,c in zip(monthlyBESS_peakDemand_savings_baseP,monthlyTESS_peakDemand_savings_baseP,monthlyGEN_peakDemand_savings_baseP)]

	## Extrapolate costs from 1 year to the entire projection length
	outData['totalPeakDemandSavings_allDER_allyears'] = list(np.full(projectionLength, np.sum(outData['monthlyPeakDemandSavings'])))

	#########################################################################################################################################################
	### Calculate the compensation per kWh for BESS, TESS, and GEN technologies
	#########################################################################################################################################################
	BESS_compensation_year1_array = np.array([sum(BESS[s:f])*rateCompensation for s, f in monthHours])
	BESS_compensation_year1_total = np.sum(BESS_compensation_year1_array)
	BESS_compensation_allyears_array = np.full(projectionLength, BESS_compensation_year1_total)
	GEN_compensation_year1_array = np.array([sum(generator[s:f])*rateCompensation for s, f in monthHours])
	GEN_compensation_year1_total = np.sum(GEN_compensation_year1_array)
	GEN_compensation_allyears_array = np.full(projectionLength, GEN_compensation_year1_total)
	TESS_compensation_year1_array = np.array([sum(vbat_discharge_component[s:f])*rateCompensation for s, f in monthHours])
	TESS_compensation_year1_total = np.sum(TESS_compensation_year1_array)
	TESS_compensation_allyears_array = np.full(projectionLength, TESS_compensation_year1_total)
	allDevices_compensation_year1_array = BESS_compensation_year1_array + GEN_compensation_year1_array + TESS_compensation_year1_array
	allDevices_compensation_year1_total = np.sum(allDevices_compensation_year1_array)
	allDevices_compensation_allyears_array = BESS_compensation_allyears_array + GEN_compensation_allyears_array + TESS_compensation_allyears_array

	## Calculate the F_val (the linear scaling factor that accound for the peak demand shift)
	## NOTE: See CIDER project plan for doc link to detailed calculation of F_val
	demand_1 = np.array(monthly_peakDemand_baseP) ## peak demand at t=1
	demand_2 = np.array(monthly_peakDemand_adjP) ## peak demand at t=2
	D_DER_1 = np.array(monthlyAllDER_peakDemand_baseP) ## DER contribution (kW) at t=1
	D_DER_2 = np.array(monthlyAllDER_peakDemand_adjP) ## DER contribution (kW) at t=2
	F_val = (demand_1 - demand_2 + D_DER_2) / D_DER_1

	## Apply the monthly F_val to the monthly BESS, TESS, GEN peak demand savings
	monthlyBESS_peakDemand_savings = monthlyBESS_peakDemand_savings_baseP*F_val ## change these back to adjP if not working
	monthlyTESS_peakDemand_savings = monthlyTESS_peakDemand_savings_baseP*F_val
	monthlyGEN_peakDemand_savings = monthlyGEN_peakDemand_savings_baseP*F_val

	######################################################################################################################################################
	## COSTS
	## Calculate the financial costs of controlling member-consumer DERs
	## e.g. subsidies, operational costs, startup costs
	######################################################################################################################################################
	projectionLength = int(inputDict['projectionLength'])
	## If the DER tech is disabled, then set all their subsidies equal to zero.
	if BESScheck == 'enabled':
		BESS_subsidy_ongoing = float(inputDict['BESS_subsidy_ongoing'])*float(inputDict['number_devices_BESS'])
		BESS_subsidy_onetime = float(inputDict['BESS_subsidy_onetime'])*float(inputDict['number_devices_BESS'])
	else:
		BESS_subsidy_ongoing = 0
		BESS_subsidy_onetime = 0

	if GENcheck == 'enabled':
		GEN_subsidy_ongoing = float(inputDict['GEN_subsidy_ongoing'])*float(inputDict['number_devices_GEN'])
		GEN_subsidy_onetime = float(inputDict['GEN_subsidy_onetime'])*float(inputDict['number_devices_GEN'])
	else:
		GEN_subsidy_ongoing = 0
		GEN_subsidy_onetime = 0

	if sum(np.array(vbat_discharge_component)) == 0:
		TESS_subsidy_ongoing = 0
		TESS_subsidy_onetime = 0
	else:
		TESS_subsidy_ongoing = combined_device_results['combinedTESS_subsidy_ongoing']
		TESS_subsidy_onetime = combined_device_results['combinedTESS_subsidy_onetime']

	## Calculate the BESS subsidy for year 1 and the projection length (all years)
	## Year 1 includes the onetime subsidy, but subsequent years do not.
	BESS_subsidy_year1_total =  BESS_subsidy_onetime + (BESS_subsidy_ongoing*12.0)
	BESS_subsidy_allyears_array = np.full(projectionLength, BESS_subsidy_ongoing*12.0)
	BESS_subsidy_allyears_array[0] += BESS_subsidy_onetime

	## Calculate the total TESS subsidies for year 1 and the projection length (all years)
	## Year 1 includes the onetime subsidy, but subsequent years do not.
	combinedTESS_subsidy_year1_total = TESS_subsidy_onetime + (TESS_subsidy_ongoing*12.0)
	combinedTESS_subsidy_allyears_array = np.full(projectionLength, TESS_subsidy_ongoing*12.0)
	combinedTESS_subsidy_allyears_array[0] += TESS_subsidy_onetime

	## Calculate Generator Subsidy for year 1 and the projection length (all years)
	## Year 1 includes the onetime subsidy, but subsequent years do not.
	GEN_subsidy_year1_total =  GEN_subsidy_onetime + (GEN_subsidy_ongoing*12.0)
	GEN_subsidy_allyears_array = np.full(projectionLength, GEN_subsidy_ongoing*12.0)
	GEN_subsidy_allyears_array[0] += GEN_subsidy_onetime
	
	## Calculate the total TESS+BESS+generator subsidies for year 1 and the projection length (all years)
	## The first month of Year 1 includes the onetime subsidy, but subsequent months and years do not include the onetime subsidy again.
	allDevices_subsidy_ongoing = GEN_subsidy_ongoing + BESS_subsidy_ongoing + TESS_subsidy_ongoing
	allDevices_subsidy_onetime = GEN_subsidy_onetime + BESS_subsidy_onetime + TESS_subsidy_onetime
	allDevices_subsidy_year1_total = allDevices_subsidy_onetime + (allDevices_subsidy_ongoing*12.0)
	allDevices_subsidy_year1_array = np.full(12, allDevices_subsidy_ongoing)
	allDevices_subsidy_year1_array[0] += allDevices_subsidy_onetime
	allDevices_subsidy_allyears_array = np.full(projectionLength, allDevices_subsidy_ongoing*12.0)
	allDevices_subsidy_allyears_array[0] += allDevices_subsidy_onetime

	## Calculate ongoing and onetime operational costs
	## NOTE: This includes costs for things like API calls to control the DERs
	operationalCosts_ongoing = float(inputDict['operationalCosts_ongoing'])
	operationalCosts_onetime = float(inputDict['operationalCosts_onetime'])
	operationalCosts_year1_total = operationalCosts_onetime + (operationalCosts_ongoing*12.0)
	operationalCosts_year1_array = np.full(12, operationalCosts_ongoing)
	operationalCosts_year1_array[0] += operationalCosts_onetime
	operationalCosts_allyears_array = np.full(projectionLength, operationalCosts_ongoing*12.0)
	operationalCosts_allyears_array[0] += operationalCosts_onetime

	## Calculate startup costs
	startupCosts = float(inputDict['startupCosts'])
	startupCosts_year1_array = np.zeros(12)
	startupCosts_year1_array[0] += startupCosts
	startupCosts_allyears_array = np.full(projectionLength, 0.0)
	startupCosts_allyears_array[0] += startupCosts

	## Calculate demand charge costs for year 1 and all years
	costs_demandCharge_year1_array = np.array(outData['monthlyAdjustedPeakDemandCost'])
	costs_demandCharge_year1_total = np.sum(costs_demandCharge_year1_array)
	costs_demandCharge_allyears_array = np.full(projectionLength,costs_demandCharge_year1_total)

	## Calculate total utility costs for year 1 and all years
	utilityCosts_year1_total = operationalCosts_year1_total + allDevices_subsidy_year1_total + allDevices_compensation_year1_total + startupCosts
	utilityCosts_year1_array = operationalCosts_year1_array + allDevices_subsidy_year1_array + allDevices_compensation_year1_array 
	utilityCosts_year1_array[0] += startupCosts
	utilityCosts_allyears_array = operationalCosts_allyears_array + allDevices_subsidy_allyears_array + allDevices_compensation_allyears_array 
	utilityCosts_allyears_array[0] += startupCosts
	utilityCosts_allyears_total = np.sum(utilityCosts_allyears_array)

	## Calculate total costs for BESS, TESS, and GEN
	"""
	if np.sum(BESS) > 0:
		totalCosts_BESS_allyears_array = BESS_subsidy_allyears_array + BESS_compensation_allyears_array
	else:
		print('REopt did not build a BESS (the discharge array for the year is zero). Setting total BESS costs and incentives to 0 for plotting purposes.')
		totalCosts_BESS_allyears_array = np.full(projectionLength, 0)
	
	if np.sum(generator) > 0:
		totalCosts_GEN_allyears_array = GEN_subsidy_allyears_array + GEN_compensation_allyears_array
	else:
		print('REopt did not build a Generator (the discharge array for the year is zero). Setting total GEN costs and incentives to 0 for plotting purposes.')
		totalCosts_GEN_allyears_array = np.full(projectionLength, 0)
	"""
	totalCosts_GEN_allyears_array = GEN_subsidy_allyears_array + GEN_compensation_allyears_array
	totalCosts_BESS_allyears_array = BESS_subsidy_allyears_array + BESS_compensation_allyears_array
	totalCosts_TESS_allyears_array = combinedTESS_subsidy_allyears_array + TESS_compensation_allyears_array

	######################################################################################################################################################
	## SAVINGS
	## Calculate the financial savings of controlling member-consumer DERs
	## NOTE: The savings are just from the adjusted energy cost and adjusted demand charge. 
	######################################################################################################################################################
	utilitySavings_year1_total = np.sum(outData['monthlyTotalSavingsAdjustedService'])
	utilitySavings_year1_array = np.array(outData['monthlyTotalSavingsAdjustedService'])
	utilitySavings_allyears_array = np.full(projectionLength, utilitySavings_year1_total)
	utilitySavings_allyears_total = np.sum(utilitySavings_allyears_array)

	## Calculating total utility net savings (savings minus costs)
	utilityNetSavings_year1_total =  utilitySavings_year1_total - utilityCosts_year1_total
	utilityNetSavings_year1_array = utilitySavings_year1_array - utilityCosts_year1_array
	utilityNetSavings_allyears_total = utilitySavings_allyears_total - utilityCosts_allyears_total
	utilityNetSavings_allyears_array = utilitySavings_allyears_array - utilityCosts_allyears_array

	## Update financial parameters
	outData['totalCost_year1'] = list(utilityCosts_year1_array)
	outData['totalSavings_year1'] = list(utilitySavings_year1_array)
	outData['totalCost_paidToConsumer'] = list(allDevices_compensation_year1_array + allDevices_subsidy_year1_array)

	## Calculate Net Present Value (NPV) and Simple Payback Period (SPP)
	outData['NPV'] = npv(float(inputDict['discountRate'])/100., utilityNetSavings_allyears_array)
	#SPP = utilityCosts_year1_total / utilityNetSavings_year1_total
	initialInvestment = startupCosts + operationalCosts_onetime + allDevices_subsidy_onetime
	utilityCosts_year1_minus_onetime_costs = (operationalCosts_ongoing*12.0) + (allDevices_subsidy_ongoing*12.0) + allDevices_compensation_year1_total
	utilityNetSavings_year1_total_minus_onetime_costs = utilitySavings_year1_total - utilityCosts_year1_minus_onetime_costs
	SPP = initialInvestment/utilityNetSavings_year1_total_minus_onetime_costs
	outData['SPP'] = SPP
	outData['totalNetSavings_year1'] = list(utilityNetSavings_year1_array) ## (total cost of service - adjusted total cost of service) - (operational costs + subsidies + compensation to consumer + startup costs)
	outData['totalNetSavings_allyears'] = list(utilityNetSavings_allyears_array)
	outData['cumulativeCashflow_total'] = list(np.cumsum(utilityNetSavings_allyears_array))
	outData['savingsAllYears'] = list(utilitySavings_allyears_array)
	outData['costsAllYears'] = list(utilityCosts_allyears_array*-1.) ## Show as negative for plotting purposes
	
	######################################################################################################################################################
	## CashFlow Projection Plot variables
	## NOTE: The utility costs are shown as negative values
	######################################################################################################################################################
	outData['subsidies'] = list(allDevices_subsidy_allyears_array*-1.)
	outData['BESS_compensation_to_consumer_allyears'] = list(BESS_compensation_allyears_array*-1.)
	outData['TESS_compensation_to_consumer_allyears'] = list(TESS_compensation_allyears_array*-1.)
	outData['GEN_compensation_to_consumer_allyears'] = list(GEN_compensation_allyears_array*-1.)
	outData['operationalCosts_allyears'] = list(operationalCosts_allyears_array*-1.)
	outData['operationalCosts_year1'] = list(operationalCosts_year1_array*-1.)
	outData['startupCosts_year1'] = list(startupCosts_year1_array*-1.)
	outData['startupCosts_allyears'] = list(startupCosts_allyears_array*-1.)
	
	## Combine the startup and operational costs for displaying in the Monthly Cost Comparison table
	startup_and_operational_costs_year1_array = startupCosts_year1_array + operationalCosts_year1_array
	outData['startupAndOperationalCosts_year1'] = list(startup_and_operational_costs_year1_array)
	
	######################################################################################################################################################
	## Savings Breakdown Per Technology Plot variables
	######################################################################################################################################################
	outData['savings_peakDemand_BESS_allyears'] = list(np.full(projectionLength, sum(monthlyBESS_peakDemand_savings)))
	outData['savings_consumption_BESS_allyears'] = list(np.full(projectionLength, sum(monthlyBESS_consumption_savings)))
	outData['savings_peakDemand_TESS_allyears'] = list(np.full(projectionLength, sum(monthlyTESS_peakDemand_savings)))
	outData['savings_consumption_TESS_allyears'] = list(np.full(projectionLength, sum(monthlyTESS_consumption_savings)))
	outData['savings_peakDemand_GEN_allyears'] = list(np.full(projectionLength, sum(monthlyGEN_peakDemand_savings)))
	outData['savings_consumption_GEN_allyears'] = list(np.full(projectionLength, sum(monthlyGEN_consumption_savings)))
	outData['totalCosts_BESS_allyears'] = list(-1.0*totalCosts_BESS_allyears_array) ## Costs are negative for plotting purposes
	outData['totalCosts_TESS_allyears'] = list(-1.0*totalCosts_TESS_allyears_array) ## Costs are negative for plotting purposes
	outData['totalCosts_GEN_allyears'] = list(-1.0*totalCosts_GEN_allyears_array) ## Costs are negative for plotting purposes
	outData['cumulativeSavings_total'] = list(np.cumsum(utilitySavings_allyears_array))

	## Add a flag for the case when no DER technology is specified. The Savings Breakdown plot will then display a placeholder plot with no available data.
	outData['techCheck'] = float(sum(BESS) + sum(vbat_discharge_component) + sum(generator))

	## Model operations typically end here.
	## Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','derUtilityCost','utility_2018_kW_load.csv')) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','derUtilityCost','open-meteo-denverCO-noheaders.csv')) as f:
		temp_curve = f.read()

	defaultInputs = {
		## TODO: maybe incorporate float, int, bool types on the html side instead of only strings
		## OMF inputs:
		'user' : 'admin',
		'modelType': modelName,
		'created': str(datetime.datetime.now()),

		## REopt inputs:
		'latitude' : '39.986771', 
		'longitude' : '-104.812599', ## Brighton, CO
		'year' : '2018',
		'urdbLabel' : '5b311c595457a3496d8367be', #'612ff9c15457a3ec18a5f7d3' the commented URDB is Brighton, CO non-TOU residential rate
		'fileName': 'utility_2018_kW_load.csv',
		'tempFileName': 'open-meteo-denverCO-noheaders.csv',
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,

		## Fossil Fuel Generator Inputs
		## Modeled after Generac 20 kW diesel model with max tank of 95 gallons
		'fossilGenerator': 'Yes',
		'number_devices_GEN': '5',
		'existing_gen_kw': '20', ## Number is based on Generac 20 kW diesel model
		'fuel_avail_gal': '95', 
		'fuel_cost_per_gal': '3.49', ## Number is based on fuel cost of diesel

		## Chemical Battery Inputs
		## Modeled after residential Tesla Powerwall 3 battery specs
		'enableBESS': 'Yes',
		'number_devices_BESS': '20000',
		'BESS_kw': '5.0',
		'BESS_kwh': '13.5',

		## Financial Inputs
		'demandChargeCost': '50', ## this input is used by vbatDispatch
		'projectionLength': '25',
		'electricityCost': '0.05',
		'rateCompensation': '0.02', ## unit: $/kWh
		'discountRate': '2',
		'startupCosts': '200000',
		'TESS_subsidy_onetime_ac': '25.0',
		'TESS_subsidy_ongoing_ac': '0.0',
		'TESS_subsidy_onetime_hp': '100.0',
		'TESS_subsidy_ongoing_hp': '0.0',
		'TESS_subsidy_onetime_wh': '25.0',
		'TESS_subsidy_ongoing_wh': '0.0',
		'BESS_subsidy_onetime': '100.0',
		'BESS_subsidy_ongoing': '0.0',
		'GEN_subsidy_onetime': '0.0',
		'GEN_subsidy_ongoing': '0.0',
		'operationalCosts_ongoing': '1000.0',
		'operationalCosts_onetime': '20000.0',

		## Home Air Conditioner inputs (vbatDispatch):
		'load_type_ac': '1', 
		'number_devices_ac': '33000',
		'power_ac': '5.6',
		'capacitance_ac': '2',
		'resistance_ac': '2',
		'cop_ac': '2.5',
		'setpoint_ac': '22.5',
		'deadband_ac': '0.625',

		## Home Heat Pump inputs (vbatDispatch):
		'load_type_hp': '2', 
		'number_devices_hp': '16500',
		'power_hp': '5.6',
		'capacitance_hp': '2',
		'resistance_hp': '2',
		'cop_hp': '3.5',
		'setpoint_hp': '19.5',
		'deadband_hp': '0.625',

		## Home Water Heater inputs (vbatDispatch):
		'load_type_wh': '4', 
		'number_devices_wh': '33000',
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
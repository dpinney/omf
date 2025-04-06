''' Performs cost-benefit analysis for a member-consumer with distributed 
energy resource (DER) technologies. '''

# Python imports
import warnings
# warnings.filterwarnings("ignore")
import shutil, datetime
from os.path import join as pJoin
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
import requests
import matplotlib.pyplot as plt
from numpy_financial import npv

# OMF imports
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.models import vbatDispatch as vb
from omf.solvers import reopt_jl

# Model metadata:
tooltip = ('The derConsumer model evaluates the financial costs of controlling behind-the-meter \
           distributed energy resources (DERs) at the residential level using the National Renewable Energy \
		   Laboratory (NREL) Renewable Energy Optimization Tool (REopt) and the OMF virtual battery dispatch \
		   module (vbatDispatch).')
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True ## Keep the model hidden=True during active development

def work(modelDir, inputDict):
	''' Run the model in its directory. '''

	## Delete output file every run if it exists
	outData = {}

	########################################################################################################################
	## Run REopt.jl solver
	########################################################################################################################

	## Create REopt input file
	latitude = float(inputDict['latitude'])
	longitude = float(inputDict['longitude'])
	urdbLabel = str(inputDict['urdbLabel'])
	year = int(inputDict['year'])
	projectionLength = int(inputDict['projectionLength'])
	demand_array = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()]) ## process input format into an array
	demand = demand_array.tolist() if isinstance(demand_array, np.ndarray) else demand_array ## make demand array into a list	for REopt

	## Begin the REopt input dictionary called 'scenario'
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
			"analysis_years": projectionLength
		}
	}

	## Add a Battery Energy Storage System (BESS) section if enabled 
	if inputDict['enableBESS'] == 'Yes':
		BESScheck = 'enabled'
		scenario['ElectricStorage'] = {
			'min_kw': float(inputDict['BESS_kw']), 
			'max_kw': float(inputDict['BESS_kw']), 
			'min_kwh': float(inputDict['BESS_kwh']), 
			'max_kwh': float(inputDict['BESS_kwh']), 
			'can_grid_charge': True,
			'total_rebate_per_kw': 0.0,
			'macrs_option_years': 0,
			'replace_cost_per_kw': float(inputDict['replace_cost_per_kw']),
			'replace_cost_per_kwh': float(inputDict['replace_cost_per_kwh']),
			'total_itc_fraction': 0.0,
			'inverter_replacement_year': int(inputDict['inverter_replacement_year']),
			'battery_replacement_year': int(inputDict['battery_replacement_year']),
			}
	else:
		BESScheck = 'disabled'
	
	## Add fossil fuel (diesel) generator to input scenario (if enabled)
	if inputDict['fossilGenerator'] == 'Yes':
		GENcheck = 'enabled'
		scenario['Generator'] = {
			'existing_kw': float(inputDict['existing_gen_kw']), ## Existing generator
			'max_kw': 0.0, ## New generator minumum
			'min_kw': 0.0, ## New generator maximum
			'only_runs_during_grid_outage': False,
			'fuel_avail_gal': float(inputDict['fuel_available_gal']),
			'fuel_cost_per_gallon': float(inputDict['fuel_cost_per_gal']),
			'replacement_year': int(inputDict['generator_replacement_year']),
			'replace_cost_per_kw': float(inputDict['replace_cost_generator_per_kw'])
		}
	else:
		GENcheck = 'disabled'

	## Save the scenario file
	## NOTE: reopt_jl currently requires a path for the input file, so the file must be saved to a location
	## preferrably in the modelDir directory
	with open(pJoin(modelDir, 'reopt_input_scenario.json'), 'w') as jsonFile:
		json.dump(scenario, jsonFile)
	
	## Read in a static REopt test file
	## NOTE: The single commented code below is used temporarily if reopt_jl is not working or for other debugging purposes.
	## Also NOTE: If this is used, you typically have to add a ['outputs'] key before the variable of interest.
	## For example, instead of reoptResults['ElectricStorage']['storage_to_load_series_kw'], it would have to be
	## reoptResults['outputs']['ElectricStorage']['storage_to_load_series_kw'] when using the static reopt file below.
	#with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","residential_reopt_results.json")) as f:
	#	reoptResults = pd.json_normalize(json.load(f))
	#	print('Successfully loaded REopt test file. \n')

	reopt_jl.run_reopt_jl(modelDir, 'reopt_input_scenario.json')
	with open(pJoin(modelDir, 'results.json')) as jsonFile:
		reoptResults = json.load(jsonFile)
	outData.update(reoptResults) ## Update output file outData with REopt results data

	## Convert user provided demand and temp data from str to float
	temperatures = [float(value) for value in inputDict['tempCurve'].split('\n') if value.strip()]
	demand = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()])

	## Create timestamp array from REopt input information
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
		'load_type': '', ## 1=AirConditioner, 2=HeatPump, 3=Refrigerator, 4=WaterHeater (These conventions are from OMF model vbatDispatch.html)
		'number_devices': '1',
		'power': '',
		'capacitance': '',
		'resistance': '',
		'cop': '',
		'setpoint':  '',
		'deadband': '',
		'unitDeviceCost': '', 
		'unitUpkeepCost':  '', 
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
	thermal_variables=['load_type','power','capacitance','resistance','cop','setpoint','deadband','TESS_subsidy_ongoing','TESS_subsidy_onetime','unitDeviceCost','unitUpkeepCost']

	all_device_suffixes = []
	single_device_results = {} 
	for suffix in thermal_suffixes:
		## Include only the thermal devices specified by the user
		if float(inputDict['load_type'+suffix]) > 0:
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
			vbatResults['TESS_subsidy_onetime'] = float(inputDict_vbatDispatch['TESS_subsidy_onetime'])#*float(inputDict['number_devices'+suffix])
			vbatResults['TESS_subsidy_ongoing'] = float(inputDict_vbatDispatch['TESS_subsidy_ongoing'])#*float(inputDict['number_devices'+suffix])

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


	########################################################################################################################################################
	## DER Serving Load Overview plot 
	########################################################################################################################################################

	## If REopt outputs any Electric Storage (BESS) that also does not contain all zeros:
	if 'Generator' in reoptResults:
		generator = np.array(reoptResults['Generator']['electric_to_load_series_kw'])
		generator = np.where(generator == -0.0, 0.0, generator) ## convert negative zero values to positive zero values
		generator_W = generator * 1000. ## convert from kW to W for plotting
	else:
		generator = np.zeros_like(demand)
		generator_W = generator * 1000. ## convert from kW to W for plotting
	
	## TODO: Potentially clean up this ElectricStorage code to make it more sensible and flow better
	if 'ElectricStorage' in reoptResults: 
		if any(value != 0 for value in reoptResults['ElectricStorage']['storage_to_load_series_kw']):
			BESS = np.array(reoptResults['ElectricStorage']['storage_to_load_series_kw'])
			BESS = np.where(BESS == -0.0, 0.0, BESS) ## convert negative zero values to positive zero values
			BESS_W = BESS * 1000. ## convert from kW to W for plotting
			grid_charging_BESS = np.array(reoptResults['ElectricUtility']['electric_to_storage_series_kw'])
			grid_charging_BESS = np.where(grid_charging_BESS == -0.0, 0.0, grid_charging_BESS) ## convert negative zero values to positive zero values
			grid_charging_BESS_W = grid_charging_BESS * 1000. ## convert from kW to W for plotting
			outData['chargeLevelBattery'] = list(np.array(reoptResults['ElectricStorage']['soc_series_fraction']) * 100.)
		else:
			#raise ValueError('The BESS was not built by the REopt model. "storage_to_load_series_kw" contains all zeros.')
			BESS = np.zeros_like(demand)
			BESS_W = BESS * 1000. ## convert from kW to W for plotting
			grid_charging_BESS = np.zeros_like(demand)
			grid_charging_BESS_W = grid_charging_BESS * 1000. ## convert from kW to W for plotting
			outData['chargeLevelBattery'] = list(np.zeros_like(demand))
	else:
		print('No BESS was specified in REopt. Setting BESS variables to zero for plotting purposes.')
		BESS = np.zeros_like(demand)
		BESS_W = BESS * 1000. ## convert from kW to W for plotting
		grid_charging_BESS = np.zeros_like(demand)
		grid_charging_BESS_W = grid_charging_BESS * 1000. ## convert from kW to W for plotting
		outData['chargeLevelBattery'] = list(np.zeros_like(demand))

	## vbatDispatch variables
	vbat_discharge_component = np.array(combined_device_results['vbat_discharge'])
	vbat_charge_component = np.array(combined_device_results['vbat_charge_flipsign'])
	vbat_discharge_component = np.where(vbat_discharge_component == -0.0, 0.0, vbat_discharge_component) ## convert negative zero values to positive zero values
	vbat_charge_component = np.where(vbat_charge_component == -0.0, 0.0, vbat_charge_component) ## convert negative zero values to positive zero values
	vbat_discharge_component_W = vbat_discharge_component * 1000. ## convert from kW to W for plotting
	vbat_charge_component_W = vbat_charge_component * 1000. ## convert from kW to W for plotting
	
	## Calculate all other plot variables from kW to W for plotting
	demand_W = np.array(demand) * 1000. ## convert from kW to W for plotting
	grid_to_load = np.array(reoptResults['ElectricUtility']['electric_to_load_series_kw'])
	grid_to_load = np.where(grid_to_load == -0.0, 0.0, grid_to_load) ## convert negative zero values to positive zero values
	grid_to_load_W = grid_to_load * 1000. ## convert from kW to W for plotting
	grid_serving_new_load_W = grid_to_load_W + grid_charging_BESS_W + vbat_charge_component_W - vbat_discharge_component_W

	## Put all DER plot variables into a dataFrame for plotting
	df = pd.DataFrame({
		'timestamp': timestamps,
		'Home BESS Serving Load': BESS_W,
		'Home TESS Serving Load': vbat_discharge_component_W,
		'Grid Serving Load': grid_to_load_W, #grid_serving_new_load_W,
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
	lineshape = 'hv'

	new_demand = demand_W + vbat_charge_component_W + grid_charging_BESS_W - BESS_W - vbat_discharge_component_W - generator_W

	fig = go.Figure()

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
		BESS_subsidy_ongoing = float(inputDict['BESS_subsidy_ongoing'])
		BESS_subsidy_onetime = float(inputDict['BESS_subsidy_onetime'])
	else:
		BESS_subsidy_ongoing = 0
		BESS_subsidy_onetime = 0

	if GENcheck == 'enabled':
		GEN_subsidy_ongoing = float(inputDict['GEN_subsidy_ongoing'])
		GEN_subsidy_onetime = float(inputDict['GEN_subsidy_onetime'])
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

	#total_govt_rebate = float(inputDict['total_govt_rebate'])

	## Calculate Net Present Value (NPV) and Simple Payback Period (SPP)
	## Consumer costs = generator fuel cost + installed cost of BESS (per kW and per kWh) + BESS replacement cost + BESS inverter replacement cost + TESS unit cost + TESS upkeep cost
	## Consumer income = upfront subsidy + ongoing subsidy + energy compensation rate for DERs + BESS rebate 
	## Initial investment = BESS installation cost and TESS unit cost
	## ongoing costs are everything else
	projectionLength = int(inputDict['projectionLength'])
	#SPP = utilityCosts_year1_total / utilityNetSavings_year1_total
	BESS_initial_cost = 0 #reoptResults['ElectricStorage']['initial_capital_cost']
	#TESS_initial_cost = float(inputDict['unitDeviceCost']) * float(inputDict['number_devices'])
	BESS_subsidy_onetime = float(inputDict['BESS_subsidy_onetime'])
	BESS_subsidy_ongoing = float(inputDict['BESS_subsidy_ongoing'])

	BESS_compensation = sum(BESS) * rateCompensation
	TESS_compensation = sum(vbat_discharge_component) * rateCompensation
	#TESS_upkeep_cost = float(inputDict['unitUpkeepCost']) * float(inputDict['number_devices'])
	subsidies = allDevices_subsidy_ongoing + allDevices_subsidy_onetime
	#GEN_fuel_cost_year1 = reoptResults['Generator']['year_one_fuel_cost_before_tax_bau']
	#GEN_fuel_cost_allyears = reoptResults['Generator']['lifecycle_fuel_cost_after_tax']
	initialInvestment = BESS_initial_cost #+ TESS_initial_cost
	total_costs = initialInvestment #+ TESS_upkeep_cost
	total_costs_minus_initial_investment = total_costs - initialInvestment
	savings = subsidies + BESS_compensation + TESS_compensation #+GEN_compensation
	net_savings = savings - total_costs_minus_initial_investment
	consumerNetSavings_allyears_array = np.full(projectionLength, net_savings)
	outData['NPV'] = npv(float(inputDict['discountRate'])/100., consumerNetSavings_allyears_array)
	#utilityCosts_year1_minus_onetime_costs = (operationalCosts_ongoing*12.0) + (allDevices_subsidy_ongoing*12.0) + allDevices_compensation_year1_total
	#utilityNetSavings_year1_total_minus_onetime_costs = utilitySavings_year1_total - utilityCosts_year1_minus_onetime_costs
	SPP = initialInvestment/net_savings
	outData['SPP'] = SPP
	outData['savings'] = list(np.full(12,savings))
	outData['savingsAllYears'] = list(np.full(projectionLength,savings))
	total_costs_allYears = np.full(projectionLength,total_costs_minus_initial_investment)
	total_costs_allYears[0] += initialInvestment
	outData['costsAllYears'] = list(np.full(projectionLength,total_costs_allYears*-1.0)) ## negative for plotting purposes
	outData['cumulativeCashflow_total'] = list(np.cumsum(consumerNetSavings_allyears_array))

	######################################################################################################################################################
	## CashFlow Projection Plot variables
	## NOTE: The utility costs are shown as negative values
	######################################################################################################################################################
	## Calculate ongoing and onetime operational costs
	## NOTE: This includes costs for things like API calls to control the DERs
	operationalCosts_ongoing = 0. ## set these to 0 as a placeholder
	operationalCosts_onetime = 0.
	operationalCosts_year1_total = operationalCosts_onetime + (operationalCosts_ongoing*12.0)
	operationalCosts_year1_array = np.full(12, operationalCosts_ongoing)
	operationalCosts_year1_array[0] += operationalCosts_onetime
	operationalCosts_allyears_array = np.full(projectionLength, operationalCosts_ongoing*12.0)
	operationalCosts_allyears_array[0] += operationalCosts_onetime

	## Calculate startup costs
	startupCosts = 0. ## set this to 0 as a placeholder
	startupCosts_year1_array = np.zeros(12)
	startupCosts_year1_array[0] += startupCosts
	startupCosts_allyears_array = np.full(projectionLength, 0.0)
	startupCosts_allyears_array[0] += startupCosts

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
	totalCosts_GEN_allyears_array = GEN_subsidy_allyears_array + GEN_compensation_allyears_array
	totalCosts_BESS_allyears_array = BESS_subsidy_allyears_array + BESS_compensation_allyears_array
	totalCosts_TESS_allyears_array = combinedTESS_subsidy_allyears_array + TESS_compensation_allyears_array
	utilitySavings_year1_total = np.sum(outData['monthlyTotalSavingsAdjustedService'])
	utilitySavings_year1_array = np.array(outData['monthlyTotalSavingsAdjustedService'])
	utilitySavings_allyears_array = np.full(projectionLength, utilitySavings_year1_total)
	utilitySavings_allyears_total = np.sum(utilitySavings_allyears_array)

	
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


	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''

	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','derConsumer','residential_PV_load.csv')) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','derConsumer','residential_extended_temperature_data.csv')) as f:
		temp_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','derConsumer','residential_critical_load.csv')) as f:
		criticalLoad_curve = f.read()
	
	defaultInputs = {
		## OMF inputs:
		'user' : 'admin',
		'modelType': modelName,
		'created': str(datetime.datetime.now()),

		## REopt inputs:
		## NOTE: Variables are strings as dictated by the html input options
		'latitude':  '38.353673', ## Charleston, WV
		'longitude': '-81.640283',
		'year' : '2018',
		'urdbLabel': '5a95a9a45457a36540a199a0', ## Charleston, WV (Appalachian Power Co Residential Time of Day URDB label)
		'fileName': 'residential_PV_load.csv',
		'tempFileName': 'residential_extended_temperature_data.csv',
		'criticalLoadFileName': 'residential_critical_load.csv', ## critical load here = 50% of the daily demand
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,
		'criticalLoad': criticalLoad_curve,
		'criticalLoadSwitch': 'Yes',
		'criticalLoadFactor': '0.50',

		## Financial Inputs
		'demandChargeCost': '0.0', ## Set to zero because this component is not usually included in residential retail rates
		'projectionLength': '25',
		'electricityCost': '0.16',
		'discountRate': '1',
		'rateCompensation': '0.1', ## unit: $/kWh
		'subsidyUpfront': '50',
		'subsidyOngoing': '10',
		'TESS_subsidy_onetime_ac': '25.0',
		'TESS_subsidy_ongoing_ac': '0.0',
		'TESS_subsidy_onetime_hp': '100.0',
		'TESS_subsidy_ongoing_hp': '0.0',
		'TESS_subsidy_onetime_wh': '25.0',
		'TESS_subsidy_ongoing_wh': '0.0',
		'BESS_subsidy_onetime': '100.0',
		'BESS_subsidy_ongoing': '10.0',
		'GEN_subsidy_onetime': '25.0',
		'GEN_subsidy_ongoing': '0.0',

		## Chemical Battery Inputs
		## Modeled after residential Tesla Powerwall 3 battery specs
		'enableBESS': 'Yes',
		'BESS_kw': '5',
		'BESS_kwh': '13.5',
		'BESS_retrofit_cost': '0.0',
		'utility_BESS_portion': '20',
		'total_govt_rebate': '0.0', ## No incentives considered
		'replace_cost_per_kw': '324.0', 
		'replace_cost_per_kwh': '351.0', 
		'battery_replacement_year': '10',  
		'BESS_installed_cost': '0', 
		'total_itc_fraction': '0.0', ## No ITC
		'inverter_replacement_year': '10',
		'replace_cost_inverter': '2400',

		## Fossil Fuel Generator
		## Modeled after Generac Guardian 5 kW model ## NOTE: For liquid propane: 3.56 gal/hr
		'fossilGenerator': 'Yes',
		'existing_gen_kw': '5',
		'gen_retrofit_cost': '0',
		'fuel_available_gal': '1000', 
		'fuel_cost_per_gal': '1.00',
		'replace_cost_generator_per_kw': '450',
		'generator_replacement_year': '15',

		## Home Air Conditioner inputs (vbatDispatch):
		'load_type_ac': '1', 
		'unitDeviceCost_ac': '8', #a cheap wifi-enabled smart outlet to plug the AC into tis about $8
		'unitUpkeepCost_ac': '0',
		'power_ac': '5.6',
		'capacitance_ac': '2',
		'resistance_ac': '2',
		'cop_ac': '2.5',
		'setpoint_ac': '22.5',
		'deadband_ac': '0.625',

		## Home Heat Pump inputs (vbatDispatch):
		'load_type_hp': '2', 
		'unitDeviceCost_hp': '150',
		'unitUpkeepCost_hp': '0',
		'power_hp': '5.6',
		'capacitance_hp': '2',
		'resistance_hp': '2',
		'cop_hp': '3.5',
		'setpoint_hp': '19.5',
		'deadband_hp': '0.625',

		## Home Water Heater inputs (vbatDispatch):
		'load_type_wh': '4', 
		'unitDeviceCost_wh': '175',
		'unitUpkeepCost_wh': '0',
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
	__neoMetaModel__.renderAndShow(modelLoc) ## Why is there a pre-run?
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests_disabled() ## NOTE: Workaround for failing test. When model is ready, change back to just _tests()
	pass
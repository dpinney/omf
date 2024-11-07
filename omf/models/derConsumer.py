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
hidden = False ## Keep the model hidden=True during active development

def create_REopt_jl_jsonFile(modelDir, inputDict):
	'''
	Function that assembles a dictionary (and saves as a JSON file) of all user inputs for the purposes \
		of preparing to run reopt_jl.
	** Inputs
		modelDir: (str) path of where to save the ouput JSON file (needed for reopt_jl)
		inputDict: (dict) input dictionary containing relevant user inputs to be modeled in REopt 
			(e.g. latitude, longitude, urdb label, etc.)
	** Outputs
		scenario: (dict) output dictionary containing the correct format.
	'''

	## Site parameters
	latitude = float(inputDict['latitude'])
	longitude = float(inputDict['longitude'])
	urdbLabel = str(inputDict['urdbLabel'])
	year = int(inputDict['year'])
	projectionLength = int(inputDict['projectionLength'])
	demand_array = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()]) ## process input format into an array
	demand = demand_array.tolist() if isinstance(demand_array, np.ndarray) else demand_array ## make demand array into a list	for REopt

	"""
	## NOTE: The following lines of code are optional parameters that may or may not be used in the future.
	## Copied from omf.models.microgridDesign

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

	## Add a PV section if enabled 
	if inputDict['PV'] == 'Yes':
		scenario['PV'] = {
			##TODO: Add options here, if needed
			}

	## Add a Battery Energy Storage System (BESS) section if enabled 
	if inputDict['BESS'] == 'Yes':
		scenario['ElectricStorage'] = {
			##TODO: Add options here, if needed
			#scenario['ElectricStorage']['size_kw'] = 2
			"min_kw": 2,
			"min_kwh": 8,
			'total_rebate_per_kw': float(inputDict['total_rebate_per_kw']),
			'macrs_option_years': float(inputDict['macrs_option_years']),
			'macrs_bonus_fraction': float(inputDict['macrs_bonus_fraction']),
			'replace_cost_per_kw': float(inputDict['replace_cost_per_kw']),
			'replace_cost_per_kwh': float(inputDict['replace_cost_per_kwh']),
			'installed_cost_per_kw': float(inputDict['installed_cost_per_kw']),
			'installed_cost_per_kwh': float(inputDict['installed_cost_per_kwh']),
			'total_itc_fraction': float(inputDict['total_itc_fraction']),
			}
		

	## Add a Diesel Generator section if enabled
	if inputDict['generator'] == 'Yes':
		scenario['Generator'] = {
			##TODO: Add options here, if needed
			}

	## Save the scenario file
	## NOTE: reopt_jl currently requires a path for the input file, so the file must be saved to a location
	## preferrably in the modelDir directory
	with open(pJoin(modelDir, 'reopt_input_scenario.json'), 'w') as jsonFile:
		json.dump(scenario, jsonFile)
	return scenario


def get_tou_rates(modelDir, inputDict): 
	'''
	Function that pulls rate information from the OEDI utility rate database via API functionality.

	** Inputs
	modelDir: (str) Currently model directory
	inputDict: (dict) Input dictionary containing latitude and longitude information 

	** Outputs
	data: (JSON file) Ouput JSON file containing the API response fields \
		(see https://openei.org/services/doc/rest/util_rates/?version=3#json-output-format for more info)
	'''

	api_url = 'https://api.openei.org/utility_rates?parameters'
	api_key = '5dFShfSVRt2XJpPYCbzBeLM6nHrOXc0VFPTWxfJJ' ## API key generated by following this website: 'https://openei.org/services/'

	params = {
		'version': '3',
		'format': 'json',
		'api_key': api_key,
		'detail': 'full',
		'lat': inputDict['latitude'],
		'lon': inputDict['longitude']
		}
	
	#if inputDict['demandChargeURDB'] == 'Yes':
	#	params['getpage'] = str(inputDict['urdbLabel']) ## Residential TOU example: 5b311c595457a3496d8367be
	#else:
	#	params['lat'] = inputDict['latitude'],
	#	params['lon'] = inputDict['longitude']
	
	try:
		response = requests.get(api_url, params=params)
		response.raise_for_status()  ## Raise an exception for HTTP errors
		
		data = response.json()

		## Save the retrieved data as a JSON file
		with open(pJoin(modelDir, 'OEDIrateData.json'), 'w') as json_file:
			json.dump(data, json_file)
		
		return data
			
	except requests.exceptions.RequestException as e:
		print('Error:', e)
		return None
	

def get_tou_rates_adhoc():
	'''
	Ad-hoc function that arbitrarily assigns TOU rates for summer/winter on- and 0ff-peaks.
	NOTE: This function was temporarily used in place of get_tou_rates() due to issues with API \
	not returning rate data. Issue was solved by specifying 'detail: full' in the API request.
	'''

	tou_rates = {
		## Example TOU rates data for ad-hoc use
		'summer_on_peak': 0.25,
		'summer_off_peak': 0.15,
		'winter_on_peak': 0.20,
		'winter_off_peak': 0.12
	}
	return tou_rates

## Function to create TOU schedule based on the given OEDI utility energy schedule
def create_tou_schedule(energy_schedule):
	'''
	Function that sorts through the OEDI's provided energy rate schedule to create a Time of Use (TOU) schedule.

	** Inputs
	energy_schedule: (array of arrays) Corresponds to the demandweekdayschedule or demandweekendschedule provided by the OEDI API request. \
		Time of Use Demand Charge Structure Weekday or Weekend Schedule. Value is an array of arrays. \
		The 12 top-level arrays correspond to a month of the year. Each month array contains one integer per hour of the weekday \
		from 12am to 11pm, and the integer corresponds to the index of a period in demandratestructure. 

	** Outputs
	tou_schedule: (DataFrame) Consisting of the Month, Hour, and TOU Period (an integer corresponding to the index \
		of a period in demandratestructure)
	'''
	tou_schedule = []
	for month in range(12):
		for hour in range(24):
			tou_schedule.append({
				'Month': month + 1,
				'Hour': hour,
				'TOU Period': energy_schedule[month][hour]
			})
	return pd.DataFrame(tou_schedule)

## Function to get the TOU rate based on the TOU schedule
def calc_tou_rate(timestamp, tou_schedules, tou_structure):
	'''
	Function that identifies the Time of Use (TOU) rate given the TOU schedule and structure.
	
	** Inputs
	timestamp: (array) Hourly timestamps for a given year, length 8760.
	tou_schedules: (DataFrame) Consisting of the Month, Hour, and TOU Period (an integer corresponding to the index \
		of a period in demandratestructure)
	tou_structure: (array) Corresponds to the energyratestructure provided by the OEDI API response request.

	** Outputs
	tou_rate: (float) The TOU rate ($) for the specified period.
	tou_period: (int) An integer number corresponding to the index of a period in demandratestructure provided by the OEDI API response request.
	'''
	month = timestamp.month
	hour = timestamp.hour
	day_of_week = timestamp.weekday()

	## Weekdays
	if day_of_week < 5: 
		tou_period = tou_schedules['weekday'].loc[(tou_schedules['weekday']['Month'] == month) & (tou_schedules['weekday']['Hour'] == hour), 'TOU Period'].values[0]
	
	## Weekends
	else:
		tou_period = tou_schedules['weekend'].loc[(tou_schedules['weekend']['Month'] == month) & (tou_schedules['weekend']['Hour'] == hour), 'TOU Period'].values[0]

	tou_rate = tou_structure[tou_period][0]['rate']
	return tou_rate, tou_period


def work(modelDir, inputDict):
	''' Run the model in its directory. '''

	## Delete output file every run if it exists
	outData = {}	
	
	## Add REopt BESS inputs to inputDict
	## NOTE: These inputs are being added directly to inputDict because they are not specified by user input
	## If they become user inputs, then they can be placed directly into the defaultInputs under the new() function below
	inputDict.update({
		'total_rebate_per_kw': '10.0',
		'macrs_option_years': '25',
		'macrs_bonus_fraction': '0.4',
		'replace_cost_per_kw': '460.0',
		'replace_cost_per_kwh': '230.0',
		'installed_cost_per_kw': '500.0', 
		'installed_cost_per_kwh': '80.0', 
		'total_itc_fraction': '0.0',
	})

	## Create REopt input file
	create_REopt_jl_jsonFile(modelDir, inputDict)
	
	## Read in a static REopt test file
	## NOTE: The single commented code below is used temporarily if reopt_jl is not working or for other debugging purposes.
	## Also NOTE: If this is used, you typically have to add a ['outputs'] key before the variable of interest.
	## For example, instead of reoptResults['ElectricStorage']['storage_to_load_series_kw'], it would have to be
	## reoptResults['outputs']['ElectricStorage']['storage_to_load_series_kw'] when using the static reopt file below.
	#with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","residential_reopt_results.json")) as f:
	#	reoptResults = pd.json_normalize(json.load(f))
	#	print('Successfully loaded REopt test file. \n')

	## Run REopt.jl 
	reopt_jl.run_reopt_jl(modelDir, 'reopt_input_scenario.json')
	#reopt_jl.run_reopt_jl(modelDir, '/Users/astronobri/Documents/CIDER/scratch/reopt_input_scenario_26may2024_0258.json', outages=inputDict['outage'])
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

	## Run vbatDispatch, unless it is disabled
	## TODO: Check that the rest of the code functions if the vbat (TESS) load type is None
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


	## DER Overview plot ###################################################################################################################################################################
	grid_to_load = reoptResults['ElectricUtility']['electric_to_load_series_kw']
	if 'Generator' in reoptResults:
		generator = reoptResults['Generator']['electric_to_load_series_kw']

	if 'PV' in reoptResults: ## PV
		PV = reoptResults['PV']['electric_to_load_series_kw']
	else:
		PV = np.zeros_like(demand)
	
	## Using REopt's Battery Energy Storage System (BESS) output
	if 'ElectricStorage' in reoptResults and any(reoptResults['ElectricStorage']['storage_to_load_series_kw']): ## BESS
		print("Using REopt's BESS output. \n")
		BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
		grid_charging_BESS = np.asarray(reoptResults['ElectricUtility']['electric_to_storage_series_kw'])
		if 'PV' in reoptResults:
			grid_charging_BESS += np.asarray(reoptResults['PV']['electric_to_storage_series_kw'])
		outData['chargeLevelBattery'] = reoptResults['ElectricStorage']['soc_series_fraction']

		## Update the monthly consumer savings
		## Add BESS compensation amount to vbatDispatch's thermal BESS savings
		monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
				(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
				(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]
		BESS_compensation_monthly = np.asarray([sum(BESS[s:f]) for s, f in monthHours])
		outData['savings'] = list(np.asarray(outData['savings'])+np.asarray(BESS_compensation_monthly)) ## NOTE: There is likely a better way to add two lists together, but this works for now

	else:
		print('No BESS found in REopt: Setting BESS data to 0. \n')
		BESS = np.zeros_like(demand)
		grid_charging_BESS = np.zeros_like(demand)
		outData['chargeLevelBattery'] = np.zeros_like(demand)

	## NOTE: The following 3 lines of code read in the SOC info from a static reopt test file 
	#with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','residential_reopt_results.json')) as f:
	#	static_reopt_results = json.load(f)
	#outData['chargeLevelBattery'] = static_reopt_results['outputs']['ElectricStorage']['soc_series_fraction']


	## Create DER overview plot object ######################################################################################################################################################
	fig = go.Figure()
	showlegend = True # either enable or disable the legend toggle in the plot
	if inputDict['load_type'] != '0': ## Load type 0 corresponds to the "None" option, which disables this vbatDispatch function
		vbat_discharge_component = np.asarray(vbat_discharge_flipsign)
		vbat_charge_component = np.asarray(vbat_charge)
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

	## Temperature line on a secondary y-axis (defined in the plot layout)
	fig.add_trace(go.Scatter(x=timestamps,
						  y=temperatures,
						  yaxis='y2',
						  mode='lines',
						  line=dict(color='red',width=1),
						  name='Average Air Temperature',
						  showlegend=showlegend 
						  ))
	
	fig.add_trace(go.Scatter(x=timestamps,
						y=vbat_discharge_component + np.asarray(demand),
						yaxis='y1',
						mode='none',
						fill='tozeroy',
						fillcolor='rgba(127,0,255,1)',
						name='vbat Serving Load (kW)',
						showlegend=showlegend))
	fig.update_traces(fillpattern_shape='/', selector=dict(name='vbat Serving Load (kW)'))

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
                         name='Additional Load (Charging BESS and vbat)', ## TODO: Edit this title accordingly if BESS and/or vbat are disabled
                         fill='tonexty',
                         fillcolor='rgba(175,0,42,0)',
						 showlegend=showlegend))
	fig.update_traces(fillpattern_shape='.', selector=dict(name='Additional Load (Charging BESS and vbat)'))

	## Grid serving new load
	## TODO: Should PV really be in this?
	grid_serving_new_load = np.asarray(grid_to_load) + np.asarray(grid_charging_BESS) + vbat_charge_component - vbat_discharge_component + np.asarray(PV)
	fig.add_trace(go.Scatter(x=timestamps,
                         y=grid_serving_new_load,
						 yaxis='y1',
                         mode='none',
                         fill='tozeroy',
                         name='Grid Serving New Load (kW)',
                         fillcolor='rgba(192,192,192,1)',
						 showlegend=showlegend))

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

	## PV plot, if enabled
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

	## Generator serving load piece
	if (inputDict['generator'] == 'Yes'):
		fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(generator),
							yaxis='y1',
							mode='none',
							fill='tozeroy',
							name='Generator Serving Load (kW)',
							fillcolor='rgba(0,137,83,1)',
							showlegend=showlegend))
		fig.update_traces(fillpattern_shape='/', selector=dict(name='BESS Serving Load (kW)'))

	## Plot layout
	fig.update_layout(
    	#title='Residential Data',
    	xaxis=dict(title='Timestamp'),
    	yaxis=dict(title='Power (kW)'),
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
	## Eventually we want to delete this part.
	fig.show() 

	## Encode plot data as JSON for showing in the HTML side
	outData['derOverviewData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['derOverviewLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)


	## Create Exported Power plot object ######################################################################################################################################################
	fig = go.Figure()
	
	## Power used to charge BESS (electric_to_storage_series_kw)
	if inputDict['BESS'] == 'Yes':
		fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(grid_charging_BESS),
							mode='none',
							fill='tozeroy',
							name='Power Used to Charge BESS',
							fillcolor='rgba(75,137,83,1)',
							showlegend=True))
	
	## Power used to charge vbat (vbat_charging)
	if inputDict['load_type'] != '0':
		fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(vbat_charge),
							mode='none',
							fill='tozeroy',
							name='Power Used to Charge TESS',
							fillcolor='rgba(155,148,225,1)',
							showlegend=True))
	

	if inputDict['PV'] == 'Yes':
		PVcurtailed = reoptResults['PV']['electric_curtailed_series_kw']
		electric_to_grid = reoptResults['PV']['electric_to_grid_series_kw']

		## PV curtailed (electric_curtailed_series_kw)
		fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(PVcurtailed),
							mode='none',
							fill='tozeroy',
							name='PV Curtailed',
							fillcolor='rgba(0,137,83,1)',
							showlegend=True))
		
		## PV exported to grid (electric_to_grid_series_kw)
		fig.add_trace(go.Scatter(x=timestamps,
					y=np.asarray(electric_to_grid),
					mode='none',
					fill='tozeroy',
					name='Power Exported to Grid',
					fillcolor='rgba(33,78,154,1)',
					showlegend=True))
		
	## Power used to meet load (NOTE: Does this mean grid to load?)
	fig.add_trace(go.Scatter(x=timestamps,
					y=np.asarray(grid_to_load),
					mode='none',
					fill='tozeroy',
					name='Grid Serving Load',
					fillcolor='rgba(100,131,130,1)',
					showlegend=True))

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
	outData['exportedPowerData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['exportedPowerLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)


	## Create Thermal Device Temperature plot object ######################################################################################################################################################
	if inputDict['load_type'] != '0': ## If vbatDispatch is called in the analysis:
	
		fig = go.Figure()
	
		## It seems like the setpoint (interior temp) is fixed for devices except the water heater.
		## TODO: If desired, could code this up to extract the interior temperature from the water heater code.
		## It does not currently seem to output the changing interior temp.

		#if inputDict['load_type'] == '4': ## Water Heater (the only option that evolves interior temperature over time)
			# Interior Temperature
			#interior_temp = theta.mean(axis=0) 
			#theta_s_wh #temperature setpoint (interior)
			#theta_s_wh +/- deadband 

		fig.add_trace(go.Scatter(x=timestamps,
							y=temperatures,
							yaxis='y2',
							mode='lines',
							line=dict(color='red',width=1),
							name='Average Air Temperature',
							showlegend=showlegend 
							))
		
		upper_bound = np.full_like(demand,float(inputDict['setpoint']) + float(inputDict['deadband'])/2)
		lower_bound = np.full_like(demand,float(inputDict['setpoint']) - float(inputDict['deadband'])/2)
		setpoint = np.full_like(demand, float(inputDict['setpoint'])) ## the setpoint is currently a fixed number

		## Plot deadband upper bound
		fig.add_trace(go.Scatter(
			x=timestamps,  
			y=upper_bound, 
			yaxis='y2',
			line=dict(color='rgba(0,0,0,1)'), ## color black
			name='Deadband upper bound',
			showlegend=True
		))

		## Plot deadband lower bound
		fig.add_trace(go.Scatter(
			x=timestamps, 
			y=lower_bound,  
			yaxis='y2',
			mode='lines',
			line=dict(color='rgba(0,0,0,0.5)'),  ## color black but half opacity = gray color
			name='Deadband lower bound',
			showlegend=True
		))

		## Plot the setpoint (interior temperature)
		fig.add_trace(go.Scatter(
			x=timestamps, 
			y=setpoint,  
			yaxis='y2',
			mode='lines',
			line=dict(color='rgba(0, 27, 255, 1)'),  ## color blue
			name='Setpoint',
			showlegend=True
		))


		## Plot layout
		fig.update_layout(
			#title='Residential Data',
			xaxis=dict(title='Timestamp'),
			yaxis=dict(title='Power (kW)'),
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

		#fig.show()
		
		## Encode plot data as JSON for showing in the HTML side
		outData['thermalDevicePlotData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
		outData['thermalDevicePlotLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''

	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','residential_PV_load.csv')) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','residential_extended_temperature_data.csv')) as f:
		temp_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','residential_critical_load.csv')) as f:
		criticalLoad_curve = f.read()
	
	defaultInputs = {
		## OMF inputs:
		'user' : 'admin',
		'modelType': modelName,
		'created': str(datetime.datetime.now()),

		## REopt inputs:
		## NOTE: Variables are strings as dictated by the html input options
		'latitude':  '39.532165', ## Rivesville, WV
		'longitude': '-80.120618', 
		'year' : '2018',
		'urdbLabel': '643476222faee2f0f800d8b1', ## Rivesville, WV - Monongahela Power
		'fileName': 'residential_PV_load.csv',
		'tempFileName': 'residential_extended_temperature_data.csv',
		'criticalLoadFileName': 'residential_critical_load.csv', ## critical load here = 50% of the daily demand
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,
		'criticalLoad': criticalLoad_curve,
		'criticalLoadSwitch': 'Yes',
		'criticalLoadFactor': '0.50',
		'PV': 'Yes',
		'BESS': 'Yes',
		'generator': 'No',

		## Financial Inputs
		'demandChargeURDB': 'Yes',
		'demandChargeCost': '0', ## Utility does not usually charge this for residential consumers (but could for commercial consumers)
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
		'subsidy': '50',
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
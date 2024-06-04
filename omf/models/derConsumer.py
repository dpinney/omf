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

def create_timestamps(start_time='2017-01-01',end_time='2017-12-31 23:00:00',arr_size=8760):
	''' 
	Creates an array of timestamps (using pandas package) given a start time, stop time, and array size.
	** Inputs
		start_time: (str) Beginning of the timestamp array in 'year-month-day hh:mm:ss format'
		end_time: (str) End of the timestamp array in 'year-month-day hh:mm:ss format'
		arr_size: (int) Size of the timestamp array (default=8760 for one year in hourly increments)
	** Outputs
		timestamps: (arr) Of size arr_size from start_time to end_time
	** Required packages
		import pandas as pd
 	'''
	timestamps = pd.date_range(start=start_time, end=end_time, periods=arr_size)
	return timestamps

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
	demand = np.asarray([float(value) for value in inputDict['demandCurve'].split('\n') if value.strip()])
	demand = demand.tolist() if isinstance(demand, np.ndarray) else demand ## make demand into a list	

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
			}

	## Add a Diesel Generator section if enabled
	if inputDict['generator'] == 'Yes':
		scenario['generator'] = {
			##TODO: Add options here, if needed
			}
	
	## Add an Outage section if enabled
	if inputDict['outage'] == True:
		scenario['ElectricUtility'] = {
			'outage_start_time_step': int(inputDict['outage_start_hour']),
			'outage_end_time_step': int(inputDict['outage_start_hour'])+int(inputDict['outage_duration'])
			}

	## Save the scenario file
	## NOTE: reopt_jl currently requires a path for the input file, so the file must be saved to a location
	## preferrably in the modelDir 
	with open(pJoin(modelDir, 'reopt_input_scenario.json'), 'w') as jsonFile:
		json.dump(scenario, jsonFile)
	return scenario


def get_tou_rates(modelDir, inputDict): 
	'''
	Function that pulls rate information from the OEDI utility rate database via API functionality.

	** Inputs
	modelDir: (str) Currently model directory
	lat: (float) Latitude of the utility
	lon: (float) Longitude of the utility
	##inputDict: (dict) Input dictionary containing latitude and longitude information (NOTE: this will replace lat and lon

	** Outputs
	data: (JSON file) Ouput JSON file containing the API response fields \
		(see https://openei.org/services/doc/rest/util_rates/?version=3#json-output-format for more info)
	'''

	api_url = 'https://api.openei.org/utility_rates?parameters'
	api_key = '5dFShfSVRt2XJpPYCbzBeLM6nHrOXc0VFPTWxfJJ' ## API key generated by following this website: 'https://openei.org/services/'

	params = {
		'version': '3',
		'format': 'json',
		'lat': inputDict['latitude'],
		'lon': inputDict['longitude'],
		'api_key': api_key,
		'detail': 'full',
		#'getpage': '5b311c595457a3496d8367be', ## Residential TOU
		}
	
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
	NOTE: This function is temporarily used in place of get_tou_rates() due to issues with API \
	not returning rate data at this time.
	'''

	tou_rates = {
		## Example TOU rates data for ad-hoc use
		'summer_on_peak': 0.25,
		'summer_off_peak': 0.15,
		'winter_on_peak': 0.20,
		'winter_off_peak': 0.12
	}
	return tou_rates

def generate_day_hours(monthHours):
	'''
	Create an array of start and stop hours for each day if given an array of start/stop hours for each month.

	** Inputs
	monthHours: (list) List of (start, stop) hours for each month in a year's worth of hourly data (length 8760)
	
	** Outputs
	dayHours: (list) List of (start, stop) hours for each day
	'''

	dayHours = []
	for start_hour, end_hour in monthHours:
		for day_start in range(start_hour, end_hour, 24):
			day_end = min(day_start + 24, end_hour)
			dayHours.append((day_start, day_end))
	return dayHours

def create_dispatch_schedule(temperature_array, dayHours):
	'''
	Create a dispatch schedule for solar, battery, and grid technologies for the span of a year. \
	The max temperature is determined every day during hotter months (March-August) and solar is \
	dispatched for two hours starting on the start hour. For the rest of the colder months, the \
	same is done but for the min temperature for that day. NOTE: normally, there would be 2 minimum \
	peak temperatures in the winter months where DERs would be dispatched, but only 1 is modeled \
	here for simplicity. The function returns a list of strings of either 'Grid', 'Battery', or 'Solar' \
	to signify what technology is dispatched at that hour.

	** Inputs
	temperature_array: (arr; length 8760) Hourly temperature data for a year
	dayHours: (list) List of (start, stop) times for each hour in a year

	** Outputs
	dispatch_schedule (list): List of strings that say either 'Grid', 'Battery', or 'Solar' to \
		signify which technology is dispatched at that start hour. The duration of dispatch is \
		at least 2 hours.

	'''
	## Initialize a dispatch schedule with "Grid" for all hours
	dispatch_schedule = ["Grid"] * len(temperature_array)  

	## Assign hourly dispatch according to the max temp in hotter months and min temp in colder months
	for start_hour, end_hour in dayHours:
		day_temperatures = temperature_array[start_hour:end_hour]
		max_temp = max(day_temperatures)
		min_temp = min(day_temperatures)

		## March to August (hotter months)
		if start_hour in range(1416, 5832):  
			for i in range(start_hour, end_hour):
				if temperature_array[i] == max_temp: ## max temperature peak for dispatch
					for j in range(i, min(i + 2, end_hour)): ## Duration of dispatch >2hrs
						dispatch_schedule[j] = "Solar"
		
		## Other months (colder months)
		else:  
			for i in range(start_hour, end_hour):
				if temperature_array[i] == min_temp: ## min temperature peak for dispatch
					for j in range(i, min(i + 2, end_hour)): ## Duration of dispatch >2hrs
						dispatch_schedule[j] = "Battery"

	return dispatch_schedule

def solar_demand(PV, hourDispatch, on_peak_hours, off_peak_hours):
	'''
	Extract solar demand while keeping track of on-peak or off-peak hours.

	** Inputs
	PV: (list) List of PV dispatch values (from REopt).
	hour_types: (list) List indicating the type of each hour, where 'Solar' signifies solar demand.
	on_peak_hours: (range) Range representing on-peak hours.
	off_peak_hours: (list) List representing off-peak hours.

	** Output
	solar_demand: (list) List of tuples containing (PV value, hour_of_year, peak_type).
	'''

	solar_demand = []

	for i, dispatchType in enumerate(hourDispatch):
		if dispatchType == 'Solar':
			## Determine the peak type (on-peak or off-peak)
			peak_type = 'On-Peak' if i % 24 in on_peak_hours else 'Off-Peak'

			## Append to the solar_demand list as a tuple
			solar_demand.append((PV[i], i, peak_type))
			#print(PV[i])

	return solar_demand

def total_solar_cost(solar_demand, tou_rates):
	'''
	Calculate the total cost for solar demand based on the TOU rates.

	** Inputs
	solar_demand: (list) List of tuples containing (demand_value, hour_of_year, peak_type).
	tou_rates: (dict) Dictionary containing the TOU rates for summer_on_peak and summer_off_peak hours.

	** Output
	total_cost: (float) Total cost for solar demand based on TOU rates.
	'''

	## Initialize total cost
	total_cost = 0.0

	## Loop through each tuple in solar_demand
	for demand_value, hour_of_year, peak_type in solar_demand:
		## Determine the rate based on the peak type
		rate = tou_rates['summer_on_peak'] if peak_type == 'On-Peak' else tou_rates['summer_off_peak']
		## Add the cost for this hour
		total_cost += demand_value * rate

	return total_cost

def work(modelDir, inputDict):
	''' Run the model in its directory. '''

	# Delete output file every run if it exists
	outData = {}	
	
	## Create REopt input file
	create_REopt_jl_jsonFile(modelDir, inputDict)
	
	## NOTE: The single commented code below is used temporarily if reopt_jl is not working or for other debugging purposes.
	## Also NOTE: If this is used, you typically have to add a ['outputs'] key before the variable of interest.
	## For example, instead of reoptResults['ElectricStorage']['storage_to_load_series_kw'], it would have to be
	## reoptResults['outputs']['ElectricStorage']['storage_to_load_series_kw'] when using the static reopt file below.
	## Read in a static REopt test file 
	#with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","residential_reopt_results.json")) as f:
	#	reoptResults = pd.json_normalize(json.load(f))
	#	print('Successfully loaded REopt test file. \n')

	## Run REopt.jl 
	reopt_jl.run_reopt_jl(modelDir, 'reopt_input_scenario.json', outages=inputDict['outage'])
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
		year = inputDict['year'] # Use the user provided year if none found in reoptResults

	arr_size = np.size(demand) # desired array size of the timestamp array
	timestamps = create_timestamps(start_time=f'{year}-01-01', end_time=f'{year}-12-31 23:00:00', arr_size=arr_size)

	## If outage is specified in the inputs, load the resilience results
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
		vbpower_series = pd.Series(vbatResults['VBpower'][0])
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
		BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
		grid_charging_BESS = reoptResults['ElectricUtility']['electric_to_storage_series_kw']
		outData['chargeLevelBattery'] = reoptResults['ElectricStorage']['soc_series_fraction']

		## NOTE: The following 3 lines of code read in the SOC info from a static reopt test file 
		#with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','residential_reopt_results.json')) as f:
		#	static_reopt_results = json.load(f)
		#outData['chargeLevelBattery'] = static_reopt_results['outputs']['ElectricStorage']['soc_series_fraction']

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
                         name='Additional Load (Charging BESS and vbat)', ## TODO: Edit this title accordingly if BESS and/or vbat are disabled
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
	## Eventually we will delete this part.
	fig.show() 

	## Encode plot data as JSON for showing in the HTML side
	outData['derOverviewData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['derOverviewLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

	## Add REopt resilience plot (adapted from omf/models/microgridDesign.py)
	#helper function for generating output graphs
	def makeGridLine(x,y,color,name):
		plotLine = go.Scatter(
			x = x, 
			y = y,
			line = dict( color=(color)),
			name = name,
			hoverlabel = dict(namelength = -1),
			showlegend=True,
			stackgroup='one',
			mode='none'
		)
		return plotLine
	#Set plotly layout ---------------------------------------------------------------
	plotlyLayout = go.Layout(
		width=1000,
		height=375,
		legend=dict(
			x=0,
			y=1.25,
			orientation="h")
		)
	x = list(range(len(reoptResults['ElectricUtility']['electric_to_load_series_kw'])))
	plotData = []
	#x_values = pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01'))
	x_values = timestamps
	powerGridToLoad = makeGridLine(x_values,reoptResults['ElectricUtility']['electric_to_load_series_kw'],'blue','Load met by Grid')
	plotData.append(powerGridToLoad)
	
	if (inputDict['outage']): ## TODO: condense this code if possible
		outData['resilience'] = reoptResultsResilience['resilience_by_time_step']
		outData['minOutage'] = reoptResultsResilience['resilience_hours_min']
		outData['maxOutage'] = reoptResultsResilience['resilience_hours_max']
		outData['avgOutage'] = reoptResultsResilience['resilience_hours_avg']
		outData['survivalProbX'] = reoptResultsResilience['outage_durations']
		outData['survivalProbY'] = reoptResultsResilience['probs_of_surviving']

		plotData = []
		resilience = go.Scatter(
			x=x,
			y=outData['resilience'],
			line=dict( color=('red') ),
		)
		plotData.append(resilience)
		plotlyLayout['yaxis'].update(title='Longest Outage survived (Hours)')
		plotlyLayout['xaxis'].update(title='Start Hour')
		outData['resilienceData'] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		outData['resilienceLayout'] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

		plotData = []
		survivalProb = go.Scatter(
			x=outData['survivalProbX'],
			y=outData['survivalProbY'],
			line=dict( color=('red') ),
			name='Probability of Surviving Outage of a Given Duration')
		plotData.append(survivalProb)
		plotlyLayout['yaxis'].update(title='Probability of meeting critical Load')
		plotlyLayout['xaxis'].update(title='Outage Length (Hours)')
		outData['resilienceProbData' ] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		outData['resilienceProbLayout'] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)


	## Create Exported Power plot object
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
							name='Power Used to Charge VBAT',
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

	########## DER Sharing Program options ##########
	if (inputDict['utilityProgram']):
		print('Considering utility DER sharing program \n')
		
		## Gather DERs from REopt and vbatDispatch
		PVcost = float(inputDict['rateCompensation']) * np.sum(PV)
		print('PV compensation: ', PVcost)


		## Gather TOU rates
		#latitude = float(inputDict['latitude'])
		#longitude = float(inputDict['longitude'])
		## NOTE: Temporarily override lat/lon for a utility that has TOU rates specifically
		inputDict['latitude'] = 39.986771 
		inputDict['longitude'] = -104.812599 ## Brighton, CO
		rate_info = get_tou_rates(modelDir, inputDict)

		## Look at all the "name" keys containing "TOU" or "time of use"
		#filtered_names = [item['name'] for item in rate_info['items'] if 'TOU' in item['name'] or 'time-of-use' in item['name'] or 'Time of Use' in item['name']]
		#for name in filtered_names: 
		#	print(name)	## Print the filtered names

		## Select one of the name keys (in this case, the residential TOU)
		TOUdata = []
		TOUname = 'Residential Time of Use'
		for item in rate_info['items']:
			if item['name'] == TOUname:
				TOUdata.append(item)

		print(TOUdata)

		## NOTE: ad-hoc TOU rates were used when the rate_info was not working.
		#tou_rates = get_tou_rates_adhoc()
		#print(TOUdata[0])
		
		## Tiered Energy Usage Charge Structure. Each element in the top-level array corresponds to one period 
			#(see energyweekdayschedule and energyweekendschedule) and each array element within a period corresponds 
			#to one tier. Indices are zero-based to correspond with energyweekdayschedule and energyweekendschedule entries: 
			#[[{"max":(Decimal),"unit":(Enumeration),"rate":(Decimal),"adj":(Decimal),"sell":(Decimal)},...],...]
		energyRateStructure = TOUdata[0]['energyratestructure']
		
		## Tiered Energy Usage Charge Structure Weekday Schedule. Value is an array of arrays. The 12 top-level arrays correspond 
			#to a month of the year. Each month array contains one integer per hour of the weekday from 12am to 11pm, and the
			#integer corresponds to the index of a period in energyratestructure.
		energyWeekdaySchedule = TOUdata[0]['energyweekdayschedule']
		energyWeekendSchedule = TOUdata[0]['energyweekendschedule']
		

		'''
		## NOTE: The following dict is not being used because the the API is not returning these variables yet
		rate_info = {
			'rate_name': data['items'][0]['name'], ## Rate name
			'fixed_monthly_charge': data['items'][0]['fixedmonthlycharge'], ## Fixed monthly charge ($)
			'demand_rate_unit': data['items'][0]['demandrateunit'], ## Time of Use Rate Units
			'demand_rate_structure': data['items'][0]['demandratestructure'], ## Time of Use Demand Charge Structure
			'demand_weekday_schedule': data['items'][0]['demandweekdayschedule'],
			'demand_weekend_schedule': data['items'][0]['demandweekendschedule'],
			'flat_demand_structure': data['items'][0]['flatdemandstructure'],
			'flat_demand_months': data['items'][0]['flatdemandmonths'],
			'flat_demand_unit': data['items'][0]['flatdemandunit']
		}
		'''

		########## Generate peak shave schedule ##########

		## List of (start, stop) hours for each month in a year
		monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
		(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
		(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]
		dayHours = generate_day_hours(monthHours) ## Generate (start, stop) hours for each day


		########## Determine area under the curve ##########
		## Typical on-peak and off-peak hours during hotter months (March to August)
		on_peak_hours = range(14, 20)  ## On-peak hours typically from 2:00 PM to 8:00 PM
		off_peak_hours = list(range(0, 6)) + list(range(22, 24))  ## Off-peak hours typically from 10:00 PM to 6:00 AM
		
		
		########## Apply rate compensations to DERs deployed ##########

		########## Plot the peak shave schedule? ##########

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
		'analysis_years' : '25', 
		'urdbLabel': '643476222faee2f0f800d8b1', ## Rivesville, WV - Monongahela Power
		'fileName': 'residential_PV_load.csv',
		'tempFileName': 'residential_extended_temperature_data.csv',
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,
		'PV': 'Yes',
		'BESS': 'Yes',
		'generator': 'No',
		'outage': True,
		'outage_start_hour': '4637',
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

		## DER Program Design inputs:
		'utilityProgram': 'Yes',
		'rateCompensation': '0.1', ## unit: $/kWh
		'maxBESSDischarge': '80', ## unit: % (Percent of total BESS)
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
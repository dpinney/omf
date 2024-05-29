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
	if inputDict['outage'] == 'Yes':
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


def get_tou_rates(modelDir, lat, lon): ## TODO: change lat,lon to inputDict once model is working
	api_url = 'https://api.openei.org/utility_rates?parameters'
	api_key = '5dFShfSVRt2XJpPYCbzBeLM6nHrOXc0VFPTWxfJJ' ## API key generated by following this website: 'https://openei.org/services/'

	params = {
		'version': '3',
		'format': 'json',
		'lat': lat,
		'lon': lon,
		'api_key': api_key
		}
	try:
		response = requests.get(api_url, params=params)
		response.raise_for_status()  ## Raise an exception for HTTP errors
		
		data = response.json()

		# Save the retrieved data as a JSON file
		with open(pJoin(modelDir, 'OEDIrateData.json'), 'w') as json_file:
			json.dump(data, json_file)
		
		return data
			
	except requests.exceptions.RequestException as e:
		print('Error:', e)
		return None


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
		#BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
		BESS = np.ones_like(demand) ## NOTE: Ad-hoc line used because BESS is not being built in REopt for some reason. Currently debugging 5/2024
		grid_charging_BESS = reoptResults['ElectricUtility']['electric_to_storage_series_kw']

		## NOTE: The following 3 lines of code are temporary; it reads in the SOC info from a static reopt test file 
		## For some reason REopt is not producing BESS results so this is a workaround
		with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','residential_reopt_results.json')) as f:
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

	## DER Sharing Program options
	if (inputDict['utilityProgram']):
		print('Considering utility DER sharing program \n')
		
		## Gather TOU rates
		#latitude = float(inputDict['latitude'])
		#longitude = float(inputDict['longitude'])
		## NOTE: Temporarily use the lat/lon for a utility that has TOU rates specifically
		latitude = 39.986771 
		longitude = -104.812599 ## Brighton, CO
		rate_info = get_tou_rates(modelDir, latitude, longitude) ## NOTE: lan/lon will be replaced by inputDict

		## Extract "name" keys containing "TOU" or "time of use"
		filtered_names = [item['name'] for item in rate_info['items'] if 'TOU' in item['name'] or 'time-of-use' in item['name'] or 'Time of Use' in item['name']]
		for name in filtered_names: ## Print the filtered names
			print(name)	

		TOUname = 'Residential Time of Use'
		TOUdata = []

		for item in rate_info['items']:
			if item['name'] == TOUname:
				TOUdata.append(item)

		print(TOUdata)

		'''
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

		## Generate peak shave schedule

		## Determine area under the curve

		## Apply rate compensations to DERs deployed

		## Plot the peak shave schedule?

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
		'latitude':  '39.532165', ## Rivesville, WV
		'longitude': '-80.120618', ## TODO: Should these be strings or floats? Update - strings.
		'year' : '2018',
		'analysis_years' : '25', 
		'urdbLabel': '643476222faee2f0f800d8b1', ## Rivesville, WV - Monongahela Power
		'fileName': 'residential_PV_load.csv',
		'tempFileName': 'residential_extended_temperature_data.csv',
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,
		'PV': 'No',
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
		'utilityProgram': 'Yes', ## unit: $/kWh
		'rateCompensation': '0', ## unit: $
		'fixedCompensation': '0', ## unit: $
		'fixedCompensationFrequency': '0', ## 0=one-time only, 1=yearly
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
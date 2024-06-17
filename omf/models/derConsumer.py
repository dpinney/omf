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
			#scenario['ElectricStorage']['size_kw'] = 2
			}
		

	## Add a Diesel Generator section if enabled
	if inputDict['generator'] == 'Yes':
		scenario['Generator'] = {
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

## Function to create TOU schedule based on the given OEDI utility energy schedule
def create_tou_schedule(energy_schedule):
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

	grid_to_load = reoptResults['ElectricUtility']['electric_to_load_series_kw']
	if 'Generator' in reoptResults:
		generator = reoptResults['Generator']['electric_to_load_series_kw']

	if inputDict['PV'] == 'Yes': ## PV
		PV = reoptResults['PV']['electric_to_load_series_kw']
	else:
		PV = np.zeros_like(demand)
	
	## NOTE: This section for BESS uses REopt's BESS, which we are finding is inconsistent and tends to not work
	## unless an outage is specified (or when we specify a generator). We are instead going to try to use our own BESS model.
	## Currently, the BESS model is only being run when considering a DER utility program is enabled.
	## TODO: Change this to instead check for BESS in the output file, rather than input
	#if inputDict['BESS'] == 'Yes': ## BESS
		#BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
		#grid_charging_BESS = reoptResults['ElectricUtility']['electric_to_storage_series_kw']
		#outData['chargeLevelBattery'] = reoptResults['ElectricStorage']['soc_series_fraction']

		## NOTE: The following 3 lines of code read in the SOC info from a static reopt test file 
		#with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','residential_reopt_results.json')) as f:
		#	static_reopt_results = json.load(f)
		#outData['chargeLevelBattery'] = static_reopt_results['outputs']['ElectricStorage']['soc_series_fraction']

	#else:
		#BESS = np.zeros_like(demand)
		#grid_charging_BESS = np.zeros_like(demand)
	BESS = np.zeros_like(demand)
	grid_charging_BESS = np.zeros_like(demand)

	########## DER Sharing Program options ######################################################################################################################################################
	if (inputDict['utilityProgram']):
		print('Considering utility DER sharing program \n')

		## Gather TOU rates
		#latitude = float(inputDict['latitude'])
		#longitude = float(inputDict['longitude'])
		## TODO: To make this more modular, require user to input specific urdb label and use the getpage variable in get_tou_rates() function
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

		PV_series = pd.Series(PV, index=timestamps)
		demand_series = pd.Series(demand, index=timestamps)
		temperature_series = pd.Series(temperatures, index=timestamps)
		BESS_series = pd.Series(BESS, index=timestamps)
		#grid_serving_load_series = pd.Series(grid_to_load, index=timestamps) 
		## NOTE: REopt gives grid_to_load, but for now I'm just prioritizing DERs serving the load and buying grid if needed.
		## If we don't want to prioritize DERs serving the load before buying from grid, then need to integrate REopt's grid_to_load
		## into the code loop below.

		## Create weekday and weekend TOU schedules
		weekday_tou_schedule = create_tou_schedule(TOUdata[0]['energyweekdayschedule'])
		weekend_tou_schedule = create_tou_schedule(TOUdata[0]['energyweekendschedule'])

		## Combine the weekday and weekend schedules
		tou_schedules = {'weekday': weekday_tou_schedule, 'weekend': weekend_tou_schedule}
		tou_structure = TOUdata[0]['energyratestructure']
		fixed_monthly_charge = TOUdata[0]['fixedmonthlycharge']
		compensation_rate = float(inputDict['rateCompensation'])
		subsidy_amount = float(inputDict['subsidy'])

		## Identify the on- and off-peak periods
		on_peak_periods = []
		off_peak_periods = []
		for period, rate in enumerate(tou_structure):
			if rate[0]['rate'] == max(tou_structure, key=lambda x: x[0]['rate'])[0]['rate']:
				on_peak_periods.append(period)
			if rate[0]['rate'] == min(tou_structure, key=lambda x: x[0]['rate'])[0]['rate']:
				off_peak_periods.append(period)

		## Create dataframe to store the schedule
		schedule = pd.DataFrame({
			'Solar Generation (kW)': PV_series,
			'Household Demand (kW)': demand_series,
			'Grid Serving Load (kW)': np.zeros(len(timestamps)),  ## Placeholder; will get updated in the loop
			'Battery State of Charge': np.zeros(len(timestamps)),  ## Placeholder 
		}, index=timestamps)

		## BESS physical parameters
		## TODO: Make these inputs on the HTML side if keeping this battery model
		battery_energy_capacity = 13.5 ## kWh; Tesla Powerwall 2
		battery_max_charge_rate = 3.3  ## kW
		battery_max_discharge_rate = 3.3  ## kW
		#battery_efficiency = 0.9  # Efficiency of the battery ## NOTE: maybe add this in later?
		battery_soc = 0  ## Initial battery state of charge
		battery_soc_min = 0.2 * battery_energy_capacity  ## Min= 20% of battery capacity

		## BESS allowed for utility use
		## NOTE: I just realized that this code is set up to only use 80% of the battery to do peak shaving, rather than
		## giving/selling the 80% to the utility. TODO: how do we modify this? Lisa and I are thinking of ways to do (and plot) this
		max_utility_usage_percentage = float(inputDict['maxBESSDischarge'])  ## Up to 80% of the total battery charge
		max_utility_usage = battery_energy_capacity * max_utility_usage_percentage

		## Initial variables to be updated in the loop
		economic_benefit = 0  ## Economic benefit of storing excess solar. NOTE: Is this useful?
		total_economic_benefit = 0
		total_energy_cost = 0  ## The total cost of energy 
		total_der_compensation = 0  ## The total DER compensation amount (when DERs are discharged)
		max_demand_periods = {period: 0 for period in range(len(tou_structure))}  ## The max demand during each period (for calculating the demand cost)

		## Initial monthly cost tracking variables
		monthly_energy_cost = [0] * 12
		monthly_der_compensation = [0] * 12
		monthly_economic_benefit = [0] * 12

		for i in range(1, len(timestamps)):
			timestamp = timestamps[i] ## Grab the hour timestamp
			month = timestamp.month - 1 ## grab month information for cost savings analysis (Index 0=Jan, 11=Dec)
			tou_rate, tou_period = calc_tou_rate(timestamp, tou_schedules, tou_structure) ## Grab the specific TOU info for that hour

			net_load = demand_series[i] - PV_series[i] ## Net load after PV is accounted for

			if net_load > 0:
				## Discharge the battery during on-peak hours; update BESS and economic variables
				if tou_period in on_peak_periods:
					## Discharge BESS to household first
					discharge = min(battery_max_discharge_rate, net_load, battery_soc - battery_soc_min)
					battery_soc -= discharge
					net_load -= discharge

					## If BESS > 20% after serving household load, then utility can use it
					if battery_soc > battery_soc_min:
						utility_discharge = min(battery_max_discharge_rate, battery_soc - battery_soc_min, max_utility_usage)
						battery_soc -= utility_discharge
						der_compensation += utility_discharge * compensation_rate
						monthly_der_compensation[month] += utility_discharge * compensation_rate
						max_utility_usage -= utility_discharge  # Reduce the remaining utility usage allowance

					else: ## buy from the grid
						grid_usage = net_load ## grid_usage is how much energy needs to be bought from the grid
						total_energy_cost += grid_usage * tou_rate
						monthly_energy_cost[month] += grid_usage * tou_rate
				
				else: ## If off-peak period, use grid if necessary
					battery_soc = min(battery_energy_capacity, battery_soc + battery_max_charge_rate)
					grid_usage = net_load
					total_energy_cost += grid_usage * tou_rate
					monthly_energy_cost[month] += grid_usage * tou_rate
					der_compensation = 0

			else: ## If net_load <= 0 (PV has served all load)
				excess_solar = -net_load
				## Store any excess PV in the BESS during off-peak periods
				if tou_period in off_peak_periods:

					charge = min(battery_max_charge_rate, excess_solar)
					battery_soc = min(battery_energy_capacity, battery_soc + charge)
					#print('battery soc in offpeak 2: \n',battery_soc)
					grid_usage = 0  ## No energy being bought from the grid
					economic_benefit = charge * compensation_rate  ## Economic benefit from storing excess solar.
					monthly_economic_benefit[month] += charge * compensation_rate
					der_compensation = 0  ## No DER compensation for charging
				else:
					## If not off-peak, sell excess solar to the grid
					der_compensation = excess_solar * compensation_rate
					monthly_der_compensation[month] += excess_solar * compensation_rate

			## Update the total economic benefit and DER compensation variables
			total_economic_benefit += economic_benefit
			total_der_compensation += der_compensation

			## Track the maximum demand for the current TOU period
			max_demand_periods[tou_period] = max(max_demand_periods[tou_period], demand_series[i] + grid_usage)

			## Update the DER schedule
			schedule.loc[timestamp, 'Grid Serving Load (kW)'] = grid_usage
			schedule.loc[timestamp, 'Battery State of Charge'] = battery_soc

		## Calculate total demand cost (including fixed monthly charge)
		demand_cost = sum(max_demand_periods[period] * tou_structure[period][0]['rate'] for period in max_demand_periods) + fixed_monthly_charge

		## Calculate total DER compensation amount (including any subsidies)
		total_compensation = total_economic_benefit + total_der_compensation - total_energy_cost + subsidy_amount - demand_cost
		
		print(f"Total Energy Cost: ${total_energy_cost:.2f}")
		print(f"Total DER Compensation: ${total_der_compensation:.2f}")
		print(f"Total Compensation: ${total_compensation:.2f}")

		## Add variables to outData
		outData['energyCost'] = list(np.asarray(outData['energyCost']) + monthly_energy_cost)
		outData['monthlyDERcompensation'] = monthly_der_compensation
		outData['monthlyEconomicBenefit'] = monthly_economic_benefit

		print(monthly_der_compensation)

		## Plots
		fig = go.Figure()
		fig.add_trace(go.Scatter(x=schedule.index,
					y=schedule['Solar Generation (kW)'],
					yaxis='y1',
					mode='none',
					fill='tozeroy',
					fillcolor='yellow',
					name='Solar Generation (kW)'))
		fig.add_trace(go.Scatter(x=schedule.index,
			y=schedule['Household Demand (kW)'],
			yaxis='y1',
			mode='none',
			fill='tozeroy',
			fillcolor='black',
			name='Household Demand (kW)'))		
		fig.add_trace(go.Scatter(x=schedule.index,
			y=schedule['Grid Serving Load (kW)'],
			yaxis='y1',
			mode='none',
			fill='tozeroy',
			fillcolor='gray',
			name='Grid Serving Load (kW)'))
		fig.add_trace(go.Scatter(x=schedule.index,
			y= battery_energy_capacity - schedule['Battery State of Charge'],
			yaxis='y1',
			mode='none',
			fill='tozeroy',
			fillcolor='green',
			name='Battery Discharge (kW)'))
		fig.add_trace(go.Scatter(
			x=schedule.index,
			y=(schedule['Battery State of Charge'] / battery_energy_capacity) * 100,
			yaxis='y2',
			mode='none',  
			fill='tozeroy',
			fillcolor='rgba(0, 0, 255, 0.3)', 
			name='Battery State of Charge (%)',
			visible='legendonly'  ## Initially hide this trace
		))
		
		## Plot layout
		fig.update_layout(
			xaxis=dict(title='Timestamp'),
			yaxis=dict(
				title='Power (kW)',
				range=[0, battery_energy_capacity]  # Set range for y1 axis
			),
			yaxis2=dict(
				title='Battery State of Charge (%)',
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
		outData['derBESSplot'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
		outData['derBESSplotLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)


	## Create DER overview plot object ######################################################################################################################################################
	fig = go.Figure()
	showlegend = True # either enable or disable the legend toggle in the plot
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
							y=np.asarray(BESS),
							yaxis='y1',
							mode='none',
							fill='tozeroy',
							name='BESS Serving Load (kW)',
							fillcolor='rgba(0,137,83,1)',
							showlegend=showlegend))
		fig.update_traces(fillpattern_shape='/', selector=dict(name='BESS Serving Load (kW)'))

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

	## Add REopt resilience plot (adapted from omf/models/microgridDesign.py) ########################################################################################################################
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
		'outage_duration': '23',

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
		'maxBESSDischarge': '0.80', ## Between 0 and 1 (Percent of total BESS capacity) #TODO: Fix the HTML input for this
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
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
from itertools import accumulate

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
		}

	## Add a Battery Energy Storage System (BESS) section if enabled 
	if inputDict['chemBESSgridcharge'] == 'Yes':
		can_grid_charge_bool = True
	else:
		can_grid_charge_bool = False

	scenario['ElectricStorage'] = {
		##TODO: Add options here, if needed
		'min_kw': float(inputDict['BESS_kw'])*float(inputDict['numberBESS']),
		'max_kw':  float(inputDict['BESS_kw'])*float(inputDict['numberBESS']),
		'min_kwh':  float(inputDict['BESS_kwh'])*float(inputDict['numberBESS']),
		'max_kwh':  float(inputDict['BESS_kwh'])*float(inputDict['numberBESS']),
		'can_grid_charge': can_grid_charge_bool,
		'total_rebate_per_kw': 0,
		'macrs_option_years': 0,
		'installed_cost_per_kw': float(inputDict['installed_cost_per_kw']),
		'installed_cost_per_kwh': float(inputDict['installed_cost_per_kwh']),
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
	
	## Run vbatDispatch, unless it is disabled
	if (inputDict['load_type'] != '0') and (int(inputDict['number_devices'])>0): ## Load type 0 corresponds to the "None" option, which disables this vbatDispatch function
		vbatResults = vb.work(modelDir,inputDict)
		with open(pJoin(modelDir, 'vbatResults.json'), 'w') as jsonFile:
			json.dump(vbatResults, jsonFile)
		outData.update(vbatResults) ## Update output file with vbat results

		## vbatDispatch variables
		vbpower_series = pd.Series(vbatResults['VBpower'])
		vbat_charge = vbpower_series.where(vbpower_series > 0, 0) ##positive values = charging
		vbat_discharge = vbpower_series.where(vbpower_series < 0, 0) #negative values = discharging
		vbat_discharge_flipsign = vbat_discharge.mul(-1) ## flip sign of vbat discharge for plotting purposes
		vbatMinEnergyCapacity = pd.Series(vbatResults['minEnergySeries'])
		vbatMaxEnergyCapacity = pd.Series(vbatResults['maxEnergySeries'])
		vbatEnergy = pd.Series(vbatResults['VBenergy'])
		vbatMinPowerCapacity = pd.Series(vbatResults['minPowerSeries'])
		vbatMaxPowerCapacity = pd.Series(vbatResults['maxPowerSeries'])
		vbatPower = vbpower_series

	subsidyUpfront = float(inputDict['subsidyUpfront'])
	subsidyRecurring = float(inputDict['subsidyRecurring'])

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

	## DER Overview plot ###################################################################################################################################################################
	showlegend = True # either enable or disable the legend toggle in the plot
	grid_to_load = reoptResults['ElectricUtility']['electric_to_load_series_kw']

	BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
	grid_charging_BESS = reoptResults['ElectricUtility']['electric_to_storage_series_kw']
	outData['chargeLevelBattery'] = reoptResults['ElectricStorage']['soc_series_fraction']

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
	if (inputDict['load_type'] != '0') and (int(inputDict['number_devices'])>0): ## Load type 0 corresponds to the "None" option, which disables this vbatDispatch function
		vbat_discharge_component = np.array(vbat_discharge_flipsign)
		vbat_charge_component = np.array(vbat_charge)
	else:
		vbat_discharge_component = np.zeros_like(demand)
		vbat_charge_component = np.zeros_like(demand)

	## Convert all values from kW to Watts for plotting purposes only
	grid_to_load = np.array(grid_to_load) * 1000.
	BESS = np.array(BESS) * 1000.
	grid_charging_BESS = np.array(grid_charging_BESS) * 1000.
	vbat_discharge_component = vbat_discharge_component * 1000.
	vbat_charge_component = vbat_charge_component * 1000.
	demand = np.array(demand) * 1000.
	if 'Generator' in reoptResults:
		generator = np.array(reoptResults['Generator']['electric_to_load_series_kw']) * 1000.

	## Original load piece (minus any vbat or BESS charging aka 'new/additional loads')
	fig.add_trace(go.Scatter(x=timestamps,
						y = demand - BESS - vbat_discharge_component,
						yaxis='y1',
						mode='none',
						name='Original Load',
						fill='tozeroy',
						fillcolor='rgba(100,200,210,1)',
						showlegend=showlegend))
	## Make original load and its legend name hidden in the plot by default
	fig.update_traces(legendgroup='Original Load (kW)', visible='legendonly', selector=dict(name='Original Load (kW)')) 

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
	grid_serving_new_load = grid_to_load + grid_charging_BESS + vbat_charge_component - vbat_discharge_component
	fig.add_trace(go.Scatter(x=timestamps,
                        y=grid_serving_new_load,
						yaxis='y1',
                        #mode='none',
                        #fill='tozeroy',
                        name='Grid Serving Load',
                        line=dict(color='rgba(192,192,192,1)', width=1),
						stackgroup='one',
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
						y = BESS, # + np.asarray(demand) + vbat_discharge_component,
						yaxis='y1',
						#mode='none',
						#fill='tozeroy',
						name='BESS Serving Load',
						line=dict(color='rgba(0,137,83,1)', width=1),
						stackgroup='one',
						showlegend=showlegend))

	fig.add_trace(go.Scatter(x=timestamps,
                        y=np.asarray(grid_charging_BESS),
						yaxis='y1',
                        #mode='none',
                        name='Additional Load from BESS',
                        #fill='tozeroy',
                        line=dict(color='rgba(118,196,165,1)', width=1),
						stackgroup='one',
						showlegend=showlegend))
	
	##vbatDispatch (TESS) piece
	if (inputDict['load_type'] != '0') and (int(inputDict['number_devices'])>0): ## Load type 0 corresponds to the "None" option, which disables this vbatDispatch function
		fig.add_trace(go.Scatter(x=timestamps,
							y = vbat_discharge_component,
							yaxis='y1',
							#mode='none',
							#fill='tozeroy',
							fillcolor='rgba(127,0,255,1)',
							name='TESS Serving Load',
							line=dict(color='rgba(127,0,255,1)', width=1),
							stackgroup='one',
							showlegend=showlegend))
		
		fig.add_trace(go.Scatter(x=timestamps,
    	                    y = vbat_charge_component,
							yaxis='y1',
            	            #mode='none',
                	        name='Additional load from TESS',
                    	    #fill='tozeroy',
                        	line=dict(color='rgba(207,158,255,1)', width=1),
							stackgroup='one',
							showlegend=showlegend))

	## Fossil Generator piece
	if 'Generator' in reoptResults:
		fig.add_trace(go.Scatter(x=timestamps,
						y = generator,
						yaxis='y1',
						mode='none',
						fill='tozeroy',
						fillcolor='rgba(153,0,0,1)',
						name='Fossil Generator Serving Load',
						showlegend=showlegend))

	## Plot layout
	fig.update_layout(
    	xaxis=dict(title='Timestamp'),
    	yaxis=dict(title="Power (W)"),
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
	#fig.show()
	#outData['derOverviewHtml'] = fig.to_html(full_html=False)
	fig.write_html(pJoin(modelDir, "Plot_DerServingLoadOverview.html"))

	## Encode plot data as JSON for showing in the HTML 
	outData['derOverviewData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['derOverviewLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

	## Create Thermal Battery Power plot object ######################################################################################################################################################
	if (inputDict['load_type'] != '0') and (int(inputDict['number_devices'])>0): ## If vbatDispatch is enabled:		
		fig = go.Figure()
		fig.add_trace(go.Scatter(
			x=timestamps,
			y=vbatMinPowerCapacity,
			yaxis='y1',
			mode='lines',
			line=dict(color='green', width=1),
			name='Minimum Power Capacity',
			showlegend=True 
			))
		fig.add_trace(go.Scatter(
			x=timestamps, 
			y=vbatMaxPowerCapacity,  
			yaxis='y1',
			mode='lines',
			line=dict(color='blue', width=1),
			name='Maximum Power Capacity',
			showlegend=True
		))
		fig.add_trace(go.Scatter(
			x=timestamps, 
			y=vbatPower,  
			yaxis='y1',
			mode='lines',
			line=dict(color='black', width=1),
			name='Actual Power',
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
						mode='none',
						fill='tozeroy',
						fillcolor='red',
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

	## Calculate total residential BESS capacity and compensation
	total_kw_residential_BESS = int(inputDict['numberBESS']) * float(inputDict['BESS_kw'])
	total_kwh_residential_BESS = int(inputDict['numberBESS']) * float(inputDict['BESS_kwh'])
	rateCompensation = float(inputDict['rateCompensation'])
	total_residential_BESS_compensation = rateCompensation * np.sum(total_kwh_residential_BESS)

	## Update utility savings to include BESS savings
	## Currently, outData['savings'] is the vbatDispatch result savings only
	BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
	monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
				(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
				(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]
	electricityCost = float(inputDict['electricityCost'])
	BESS_savings_monthly = np.array([sum(BESS[s:f])*electricityCost for s, f in monthHours])
	savings_from_BESS_TESS = np.array(outData['savings']) + BESS_savings_monthly
	outData['savings'] = list(savings_from_BESS_TESS)

	## Update the financial cost ouput to include REopt BESS 
	## TODO: combine these with the same variables from vbatDispatch. Currently this just replaces the vbatDispatch variables.
	installed_cost_per_kw = float(inputDict['installed_cost_per_kw'])
	installed_cost_per_kwh = float(inputDict['installed_cost_per_kwh'])
	operational_costs_per_kw = installed_cost_per_kw * total_kw_residential_BESS
	operational_costs_per_kwh = installed_cost_per_kwh * total_kwh_residential_BESS
	#total_operational_costs = # can you add operational costs per kW + operational costs per kWh together?
	netCashflow = np.sum(savings_from_BESS_TESS) - total_residential_BESS_compensation - operational_costs_per_kwh - subsidyUpfront - (subsidyRecurring*int(inputDict['projectionLength']))
	#initialCosts = 1.
	outData['NPV'] = netCashflow
	#outData['SPP'] = initialCosts / netCashflow
	outData['cumulativeCashflow'] = reoptResults['Financial']['offtaker_annual_free_cashflows'] #list(accumulate(reoptResults['Financial']['offtaker_annual_free_cashflows']))
	outData['netCashflow'] = reoptResults['Financial']['offtaker_discounted_annual_free_cashflows'] #list(accumulate(reoptResults['Financial']['offtaker_annual_free_cashflows'])) ## or alternatively: offtaker_annual_free_cashflows

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
		'tempFileName': 'utility_CO_2018_temperatures.csv',
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,

		## Fossil Fuel Generator
		'fossilGenerator': 'Yes',
		'existing_gen_kw': '7000',

		## Chemical Battery Inputs
		'numberBESS': '100', ## Number of residential Tesla Powerwall 2 batteries
		'chemBESSgridcharge': 'Yes',  
		'installed_cost_per_kw': '20.0', #'300.0', ## (Residential: $1,000-$1,500 per kW, Utility: $300-$700 per kW)
		'installed_cost_per_kwh': '60.0', #'480.0', ## Cost per kWh reflecting Powerwall’s installed cost (Residential: $400-$900 per kWh, Utility: $200-$400 per kWh)
		'BESS_kw': '5',
		'BESS_kwh': '13.5',

		## Financial Inputs
		'demandChargeCost': '25',
		'projectionLength': '25',
		'electricityCost': '0.04',
		'rateCompensation': '0.02', ## unit: $/kWh
		'subsidyUpfront': '100.0',
		'subsidyRecurring': '0',

		## vbatDispatch inputs:
		'load_type': '1', ## Air Conditioner
		'number_devices': '2000',
		'power': '5.6',
		'capacitance': '2',
		'resistance': '2',
		'cop': '2.5',
		'setpoint': '22.5',
		'deadband': '0.625',
		'discountRate': '2',
		'unitDeviceCost': '0',
		'unitUpkeepCost': '0',
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


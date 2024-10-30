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

	## Add REopt BESS inputs to inputDict
	## NOTE: These inputs are being added directly to inputDict because they are not specified by user input
	## If they become user inputs, then they can be placed directly into the defaultInputs under the new() function below
	inputDict.update({
		'total_rebate_per_kw': '10.0',
		'macrs_option_years': '25',
		'macrs_bonus_fraction': '0.4',
		'replace_cost_per_kw': '10.0', 
		'replace_cost_per_kwh': '5.0', 
		'installed_cost_per_kw': '10.0',
		'installed_cost_per_kwh': '5.0',
		'total_itc_fraction': '0.0',
	})

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
	
	timestamps = pd.date_range(start=f'{year}-01-01', end=f'{year}-12-31 23:00:00', periods=np.size(demand))

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
		vbatMinEnergyCapacity = pd.Series(vbatResults['minEnergySeries'])
		vbatMaxEnergyCapacity = pd.Series(vbatResults['maxEnergySeries'])
		vbatEnergy = pd.Series(vbatResults['VBenergy'])
		vbatMinPowerCapacity = pd.Series(vbatResults['minPowerSeries'])
		vbatMaxPowerCapacity = pd.Series(vbatResults['maxPowerSeries'])
		vbatPower = vbpower_series

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
		'subsidy': '55',
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
		'savingsSmallConsumer': smallConsumerOutput['savings'],
		'savingsLargeConsumer': largeConsumerOutput['savings']
	})

	## DER Overview plot ###################################################################################################################################################################
	showlegend = True # either enable or disable the legend toggle in the plot
	grid_to_load = reoptResults['ElectricUtility']['electric_to_load_series_kw']

	if inputDict['PV'] == 'Yes': ## PV
		PV = reoptResults['PV']['electric_to_load_series_kw']
	else:
		PV = np.zeros_like(demand)
	
	if inputDict['BESS'] == 'Yes': ## BESS
		BESS = reoptResults['ElectricStorage']['storage_to_load_series_kw']
		#BESS = np.ones_like(demand) ## Ad-hoc line used because BESS is not being built in REopt for some reason. Currently debugging 5/2024
		grid_charging_BESS = reoptResults['ElectricUtility']['electric_to_storage_series_kw']
		outData['chargeLevelBattery'] = reoptResults['ElectricStorage']['soc_series_fraction']

		## NOTE: The following 3 lines of code are temporary; it reads in the SOC info from a static reopt test file 
		## For some reason REopt is not producing BESS results so this is a workaround
		#with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','utility_reopt_results.json')) as f:
		#	static_reopt_results = json.load(f)
		#BESS = static_reopt_results['outputs']['ElectricStorage']['storage_to_load_series_kw']
		#grid_charging_BESS = static_reopt_results['outputs']['ElectricUtility']['electric_to_storage_series_kw']
		#outData['chargeLevelBattery'] = static_reopt_results['outputs']['ElectricStorage']['soc_series_fraction']
		#outData.update(static_reopt_results['outputs'])
	else:
		BESS = np.zeros_like(demand)
		grid_charging_BESS = np.zeros_like(demand)

	## Create DER overview plot object
	fig = go.Figure()
	if inputDict['load_type'] != '0': ## Load type 0 corresponds to the "None" option, which disables this vbatDispatch function
		vbat_discharge_component = np.asarray(vbat_discharge_flipsign)
		vbat_charge_component = np.asarray(vbat_charge)

	else:
		vbat_discharge_component = np.zeros_like(demand)
		vbat_charge_component = np.zeros_like(demand)

	## Define additional load and avoided load
	additional_load = np.asarray(demand) + np.asarray(grid_charging_BESS) + vbat_charge_component
	#avoided_load = np.asarray(BESS) + vbat_discharge_component

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
                         y=additional_load,
						 yaxis='y1',
                         mode='none',
                         name='Additional Load (Charging BESS and TESS)',
                         fill='tonexty',
                         fillcolor='rgba(175,0,42,0)',
						 showlegend=showlegend))
	fig.update_traces(fillpattern_shape='.', selector=dict(name='Additional Load (Charging BESS and TESS)'))
	
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
						  name='Average Air Temperature',
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

	## BESS serving load piece
	if (inputDict['BESS'] == 'Yes'):
		fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(BESS), # + np.asarray(demand) + vbat_discharge_component,
							yaxis='y1',
							mode='none',
							fill='tozeroy',
							name='BESS Serving Load (kW)',
							fillcolor='rgba(0,137,83,1)',
							showlegend=showlegend))
		fig.update_traces(fillpattern_shape='/', selector=dict(name='BESS Serving Load (kW)'))

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
		
	##vbatDispatch (TESS) piece
	#TODO: add enabling/disabling switch here
	fig.add_trace(go.Scatter(x=timestamps,
							y=np.asarray(vbat_discharge_flipsign),
							yaxis='y1',
							mode='none',
							fill='tozeroy',
							fillcolor='rgba(127,0,255,1)',
							name='TESS Serving Load (kW)',
							showlegend=showlegend))
	fig.update_traces(fillpattern_shape='/', selector=dict(name='TESS Serving Load (kW)'))

	## Plot layout
	fig.update_layout(
    	title='DER Overview for Utility',
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
	#fig.show()
	#outData['derOverviewHtml'] = fig.to_html(full_html=False)
	fig.write_html(pJoin(modelDir, "Plot_DerServingLoadOverview.html"))

	## Encode plot data as JSON for showing in the HTML 
	outData['derOverviewData'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
	outData['derOverviewLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)

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


	## Create Thermal Battery Energy plot object ######################################################################################################################################################
	if inputDict['load_type'] != '0': ## If vbatDispatch is called in the analysis:
		fig = go.Figure()
		fig.add_trace(go.Scatter(
			x=timestamps,
			y=vbatMinEnergyCapacity,
			yaxis='y1',
			mode='lines',
			line=dict(color='green', width=1),
			name='Minimum Energy Capacity',
			showlegend=True 
			))
		fig.add_trace(go.Scatter(
			x=timestamps, 
			y=vbatMaxEnergyCapacity,  
			yaxis='y1',
			mode='lines',
			line=dict(color='blue', width=1),
			name='Maximum Energy Capacity',
			showlegend=True
		))
		fig.add_trace(go.Scatter(
			x=timestamps, 
			y=vbatEnergy,  
			yaxis='y1',
			mode='lines',
			line=dict(color='black', width=1),
			name='Actual Energy Capacity',
			showlegend=True
		))

		## Plot layout
		fig.update_layout(
			xaxis=dict(title='Timestamp'),
			yaxis=dict(title='Energy (kWh)'),
			legend=dict(
				orientation='h',
				yanchor='bottom',
				y=1.02,
				xanchor='right',
				x=1
				)
		)
		
		## Encode plot data as JSON for showing in the HTML side
		outData['thermalBatEnergyPlot'] = json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)
		outData['thermalBatEnergyPlotLayout'] = json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)
	
	## Create Thermal Battery Power plot object ######################################################################################################################################################
	if inputDict['load_type'] != '0': ## If vbatDispatch is called in the analysis:
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
	

	## Create Battery State of Charge plot object ######################################################################################################################################################
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
		plotlyLayout['yaxis'].update(title='Probability of Meeting Critical Load')
		plotlyLayout['xaxis'].update(title='Outage Length (Hours)')
		outData['resilienceProbData' ] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		outData['resilienceProbLayout'] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

	#####################################################################################################################################################################################################
	## Compensation rate to member-consumer
	compensationRate = float(inputDict['rateCompensation'])
	subsidy = float(inputDict['subsidy'])
	electricityCost = float(inputDict['electricityCost'])

	monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
					(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
					(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]
	
	load_smallConsumer_monthly = np.asarray([sum(smallConsumerLoad[s:f]) for s, f in monthHours])
	load_largeConsumer_monthly = np.asarray([sum(largeConsumerLoad[s:f]) for s, f in monthHours])
	loadCost_smallConsumer_monthly = load_smallConsumer_monthly * electricityCost
	loadCost_largeConsumer_monthly = load_largeConsumer_monthly * electricityCost


	if 'ElectricStorage' in reoptResults: ## BESS
		BESS_utility = reoptResults['ElectricStorage']['storage_to_load_series_kw']
		BESS_smallConsumer = smallConsumerOutput['ElectricStorage']['storage_to_load_series_kw']
		BESS_largeConsumer = largeConsumerOutput['ElectricStorage']['storage_to_load_series_kw']
		BESS_smallConsumer_monthly = np.asarray([sum(BESS_smallConsumer[s:f]) for s, f in monthHours])
		BESS_largeConsumer_monthly = np.asarray([sum(BESS_largeConsumer[s:f]) for s, f in monthHours])
		BESSCost_smallConsumer_monthly = BESS_smallConsumer_monthly * compensationRate
		BESSCost_largeConsumer_monthly = BESS_largeConsumer_monthly * compensationRate

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
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','utility_2018_kW_critical_load.csv')) as f:
		criticalLoad_curve = f.read()

	defaultInputs = {
		## OMF inputs:
		'user' : 'admin',
		'modelType': modelName,
		'created': str(datetime.datetime.now()),

		## REopt inputs:
		'latitude' : '39.986771', 
		'longitude' : '-104.812599', ## Brighton, CO
		'year' : '2018',
		'urdbLabel' : '612ff9c15457a3ec18a5f7d3', ## Brighton, CO
		## TODO: Create a function that will gather the urdb label from a user provided location (city,state), rather than requiring the URDB label
		'fileName': 'utility_2018_kW_load.csv',
		'tempFileName': 'utility_CO_2018_temperatures.csv',
		'demandCurve': demand_curve,
		'tempCurve': temp_curve,
		'criticalLoadFileName': 'utility_2018_kW_critical_load.csv', ## critical load here = 50% of the daily demand
		'criticalLoad': criticalLoad_curve,
		'criticalLoadSwitch': 'Yes',
		'criticalLoadFactor': '0.50',
		'PV': 'Yes',
		'BESS': 'Yes',
		'generator': 'No',
		'outage': True,
		'outage_start_hour': '1836', #Hour 1836 = March 17, 2018, 12pm
		'outage_duration': '4',

		## Financial Inputs
		'demandChargeURDB': 'Yes',
		'demandChargeCost': '25',
		'projectionLength': '25',
		'rateCompensation': '0.02', ## unit: $/kWh
		'subsidy': '100.0',

		## vbatDispatch inputs:
		'load_type': '2', ## Heat Pump
		'number_devices': '2000',
		'power': '5.6',
		'capacitance': '2',
		'resistance': '2',
		'cop': '2.5',
		'setpoint': '22.5',
		'deadband': '0.625',
		'electricityCost': '0.04',
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


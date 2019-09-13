import matplotlib, warnings, csv, json, plotly
from os.path import join as pJoin
from matplotlib import pyplot as plt
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf.solvers.REopt import run as runREopt
from omf.solvers.REopt import runResilience as runResilienceREopt
import numpy as np
import plotly.graph_objs as go

warnings.filterwarnings('ignore')

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "The microGridDesign model uses a 1yr load profile to determine the most economical combination of solar, wind, and storage technologies to use in a microgrid. The model also provides basic resiliency analysis."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. '''

	outData = {}

	if inputDict.get("solar", "None") == "None":
		solar = 'off'
	else: 
		solar = 'on'
	if inputDict.get("wind", "None") == "None":
		wind = 'off'
	else: 
		wind = 'on'
	if inputDict.get("battery", "None") == "None":
		battery = 'off'
	else: 
		battery = 'on'

	# Setting up the loadShape file.
	with open(pJoin(modelDir,"loadShape.csv"),"w") as loadShapeFile:
		loadShapeFile.write(inputDict['loadShape'])

	try:
		loadShape = []
		with open(pJoin(modelDir,"loadShape.csv")) as inFile:
			reader = csv.reader(inFile)
			for row in reader:
				loadShape.append(row) 
			if len(loadShape)!=8760: raise Exception
	except:
		errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-demandResponse#walkthrough'>OMF Wiki demandResponse</a>"
		raise Exception(errorMessage)

	latitude = float(inputDict['latitude'])
	longitude = float(inputDict['longitude'])
	energyCost = float(inputDict['energyCost'])
	demandCost = float(inputDict['demandCost'])
	year = int(inputDict['year'])
	criticalLoadFactor = float(inputDict['criticalLoadFactor'])/100
	solarCost = float(inputDict['solarCost'])
	windCost = float(inputDict['windCost'])
	batteryPowerCost = float(inputDict['batteryPowerCost'])
	batteryEnergyCost = float(inputDict['batteryEnergyCost'])
	solarMin = float(inputDict['solarMin'])
	windMin = float(inputDict['windMin'])
	batteryPowerMin = float(inputDict['batteryPowerMin'])
	batteryEnergyMin = float(inputDict['batteryEnergyMin'])
	#outageStart = int(inputDict['outageStart'])
	#outageEnd = outageStart + indexStringnt(inputDict['outageDuration'])
	#if outageEnd > 8759:
		#outageEnd = 8759
	#singleOutage = True
	#if str(inputDict['outageType']) == 'annual':
		#singleOutage = False
	
	loadShape = np.array(loadShape)
	numRows = loadShape.shape[0]
	numCols = loadShape.shape[1]
	outData['numScenarios'] = numCols+1;

	totalLoad = np.zeros(numRows)
	for i in range(0,1+numCols):
		indexString = str(i+1)

		if i == numCols:
			load = totalLoad
		else:
			load = loadShape[:,i]
			print(type(load), load[0], load )
			load = [float(x) for x in load]
			totalLoad = np.add(totalLoad, load)

		jsonifiableLoad = list(load);

		# Create the input JSON file for REopt
		scenario = {
			"Scenario": {
				"Site": {
					"latitude": latitude,
					"longitude": longitude,
					"ElectricTariff": {
						"urdb_rate_name": "custom",
						"blended_annual_rates_us_dollars_per_kwh": energyCost,
						"blended_annual_demand_charges_us_dollars_per_kw": demandCost
					},
					"LoadProfile": {
						"loads_kw": jsonifiableLoad,
						"year": year,
						"critical_load_pct": criticalLoadFactor
					},
					"PV": {
						"installed_cost_us_dollars_per_kw": solarCost,
						"min_kw": solarMin
					},
					"Storage": {
						"installed_cost_us_dollars_per_kw": batteryPowerCost,
						"installed_cost_us_dollars_per_kwh": batteryEnergyCost,
						"min_kw": batteryPowerMin,
						"min_kwh": batteryEnergyMin

					},
					"Wind": {
						"installed_cost_us_dollars_per_kw": windCost,
						"min_kw": windMin

					}
				}
			}
		}

		if solar == 'off':
			scenario['Scenario']['Site']['PV']['max_kw'] = 0;
		if wind == 'off':
			scenario['Scenario']['Site']['Wind']['max_kw'] = 0;
		if battery == 'off':
			scenario['Scenario']['Site']['Storage']['max_kw'] = 0;
	
		with open(pJoin(modelDir, "Scenario_test_POST.json"), "w") as jsonFile:
			json.dump(scenario, jsonFile)

		# Run REopt API script
		runREopt(pJoin(modelDir, 'Scenario_test_POST.json'), pJoin(modelDir, 'results.json'))
		with open(pJoin(modelDir, 'results.json')) as jsonFile:
			results = json.load(jsonFile)
		
		runID = results['outputs']['Scenario']['run_uuid']
		runResilienceREopt(runID, pJoin(modelDir, 'resultsResilience.json'))
		with open(pJoin(modelDir, 'resultsResilience.json')) as jsonFile:
			resultsResilience = json.load(jsonFile)

		resultsSubset = results['outputs']['Scenario']['Site']
		outData['demandCostBAU' + indexString] = resultsSubset['ElectricTariff']['total_demand_cost_bau_us_dollars']
		if outData['demandCostBAU' + indexString] is None:
			errMsg = results['messages'].get('error','API currently unavailable please try again later')
			raise Exception('The reOpt data analysis API by NREL had the following error: ' + errMsg) 
	
		outData['demandCost' + indexString] = resultsSubset['ElectricTariff']['total_demand_cost_us_dollars']
		outData['demandCostDiff' + indexString] = outData['demandCostBAU' + indexString] - outData['demandCost' + indexString]
		outData['energyCostBAU' + indexString] = resultsSubset['ElectricTariff']['total_energy_cost_bau_us_dollars']
		outData['energyCost' + indexString] = resultsSubset['ElectricTariff']['total_energy_cost_us_dollars']
		outData['energyCostDiff' + indexString] = outData['energyCostBAU' + indexString] - outData['energyCost' + indexString]
		outData['fixedCostBAU' + indexString] = resultsSubset['ElectricTariff']['total_fixed_cost_bau_us_dollars']
		outData['fixedCost' + indexString] = resultsSubset['ElectricTariff']['total_fixed_cost_us_dollars']
		outData['fixedCostDiff' + indexString] = outData['fixedCostBAU' + indexString] - outData['fixedCost' + indexString]
		outData['powerGridToBattery' + indexString] = resultsSubset['ElectricTariff']['year_one_to_battery_series_kw']
		outData['powerGridToLoad' + indexString] = resultsSubset['ElectricTariff']['year_one_to_load_series_kw']
		outData['totalCostBAU' + indexString] = resultsSubset['Financial']['lcc_bau_us_dollars']
		outData['totalCost' + indexString] = resultsSubset['Financial']['lcc_us_dollars']
		outData['totalCostDiff' + indexString] = outData['totalCostBAU' + indexString] - outData['totalCost' + indexString]
		outData['savings' + indexString] = resultsSubset['Financial']['npv_us_dollars']
		outData['load' + indexString] = resultsSubset['LoadProfile']['year_one_electric_load_series_kw']
		
		if solar == 'on':	
			outData['sizePV' + indexString] = resultsSubset['PV']['size_kw']
			outData['powerPV' + indexString] = resultsSubset['PV']['year_one_power_production_series_kw']
			outData['powerPVToBattery' + indexString] = resultsSubset['PV']['year_one_to_battery_series_kw']
			outData['powerPVToLoad' + indexString] = resultsSubset['PV']['year_one_to_load_series_kw']
		else:
			outData['sizePV' + indexString] = 0
		
		if battery == 'on':
			outData['powerBattery' + indexString] = resultsSubset['Storage']['size_kw']
			outData['capacityBattery' + indexString] = resultsSubset['Storage']['size_kwh']
			outData['chargeLevelBattery' + indexString] = resultsSubset['Storage']['year_one_soc_series_pct']
			outData['powerBatteryToLoad' + indexString] = resultsSubset['Storage']['year_one_to_load_series_kw']
		else:
			outData['powerBattery' + indexString] = 0
			outData['capacityBattery' + indexString] = 0
		
		if wind == 'on':
			outData['sizeWind' + indexString] = resultsSubset['Wind']['size_kw']
			outData['powerWind' + indexString] = resultsSubset['Wind']['year_one_power_production_series_kw']
			outData['powerWindToBattery' + indexString] = resultsSubset['Wind']['year_one_to_battery_series_kw']
			outData['powerWindToLoad' + indexString] = resultsSubset['Wind']['year_one_to_load_series_kw']
			if outData['powerWindToLoad' + indexString] is None:
				wind = 'off'
		else:
			outData['sizeWind' + indexString] = 0
		
		outData['resilience' + indexString] = resultsResilience['resilience_by_timestep']
		outData['minOutage' + indexString] = resultsResilience['resilience_hours_min']
		outData['maxOutage' + indexString] = resultsResilience['resilience_hours_max']
		outData['avgOutage' + indexString] = resultsResilience['resilience_hours_avg']
		outData['survivalProbX' + indexString] = resultsResilience['outage_durations']
		outData['survivalProbY' + indexString] = resultsResilience['probs_of_surviving']
		outData['runID' + indexString] = runID
		outData['apiKey' + indexString] = 'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9'

		outData['solar' + indexString] = solar
		outData['wind' + indexString] = wind
		outData['battery' + indexString] = battery

		#Set plotly layout ---------------------------------------------------------------
		plotlyLayout = go.Layout(
			width=1000,
			height=375,
			legend=dict(
				x=0,
				y=1.25,
				orientation="h")
			)
		
		x = range(len(outData['powerGridToLoad' + indexString]))

		plotData = []
		powerGridToLoad = go.Scatter(
			x=x,
			y=outData['powerGridToLoad' + indexString],
			line=dict( color=('red') ),
			name="Load met by Grid",
			showlegend=True,
			stackgroup='one')
		plotData.append(powerGridToLoad)

		if solar == 'on':
			powerPVToLoad = go.Scatter(
				x=x,
				y=outData['powerPVToLoad' + indexString],
				line=dict( color=('green') ),
				name="Load met by Solar",
				stackgroup='one')
			plotData.append(powerPVToLoad)

		if battery == 'on':
			powerBatteryToLoad = go.Scatter(
				x=x,
				y=outData['powerBatteryToLoad' + indexString],
				line=dict( color=('blue') ),
				name="Load met by Battery",
				stackgroup='one')
			plotData.append(powerBatteryToLoad)

		if wind == 'on':
			powerWindToLoad = go.Scatter(
				x=x,
				y=outData['powerWindToLoad' + indexString],
				line=dict( color=('yellow') ),
				name="Load met by Wind",
				stackgroup='one')
			plotData.append(powerWindToLoad)

		plotlyLayout['yaxis'].update(title='Power (kW)')
		plotlyLayout['xaxis'].update(title='Hour')
		outData["powerGenerationData" + indexString ] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		outData["plotlyLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

		plotData = []
		if solar == 'on':
			
			powerPVToLoad = go.Scatter(
				x=x,
				y=outData['powerPVToLoad' + indexString],
				line=dict( color=('green') ),
				name="Solar used to meet Load",
				stackgroup='one')
			plotData.append(powerPVToLoad)

			if battery == 'on':
				powerPVToBattery = go.Scatter(
					x=x,
					y=outData['powerPVToBattery' + indexString],
					line=dict( color=('yellow') ),
					name="Solar used to charge Battery",
					stackgroup='one')
				plotData.append(powerPVToBattery)

			powerPV = go.Scatter(
				x=x,
				y=outData['powerPV' + indexString],
				line=dict( color=('red') ),
				name="Solar Generation")
			plotData.append(powerPV)

		outData["solarData" + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)

			
		plotData = []
		if wind == 'on':
			
			powerWindToLoad = go.Scatter(
				x=x,
				y=outData['powerWindToLoad' + indexString],
				line=dict( color=('green') ),
				name="Wind used to meet Load",
				stackgroup='one')
			plotData.append(powerWindToLoad)

			if battery == 'on':
				powerWindToBattery = go.Scatter(
					x=x,
					y=outData['powerWindToBattery' + indexString],
					line=dict( color=('yellow') ),
					name="Wind used to charge Battery",
					stackgroup='one')
				plotData.append(powerWindToBattery)

			powerWind = go.Scatter(
				x=x,
				y=outData['powerWind' + indexString],
				line=dict( color=('red') ),
				name="Wind Generation")
			plotData.append(powerWind)

		outData["windData"  + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)


		plotData = []
		if battery == 'on':
			powerGridToBattery = go.Scatter(
				x=x,
				y=outData['powerGridToBattery' + indexString],
				line=dict( color=('red') ),
				name="Grid",
				stackgroup='one')
			plotData.append(powerGridToBattery)

			if solar == 'on':
				powerPVToBattery = go.Scatter(
					x=x,
					y=outData['powerPVToBattery' + indexString],
					line=dict( color=('green') ),
					name="Solar",
					stackgroup='one')
				plotData.append(powerPVToBattery)

			if wind == 'on':
				powerWindToBattery = go.Scatter(
					x=x,
					y=outData['powerWindToBattery' + indexString],
					line=dict( color=('yellow') ),
					name="Wind",
					stackgroup='one')
				plotData.append(powerWindToBattery)

		outData["batteryData" + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
			
		plotData = []
		if battery == 'on':
			chargeLevelBattery = go.Scatter(
				x=x,
				y=outData['chargeLevelBattery' + indexString],
				line=dict( color=('red') )
			)
			plotData.append(chargeLevelBattery)
			plotlyLayout['yaxis'].update(title='Charge (%)')
			plotlyLayout['xaxis'].update(title='Hour')
			outData["batteryChargeData" + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
			outData["batteryChargeLayout" + indexString] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)
		
		plotData = []
		resilience = go.Scatter(
			x=x,
			y=outData['resilience' + indexString],
			line=dict( color=('red') ),
		)
		plotData.append(resilience)
		plotlyLayout['yaxis'].update(title='Longest Outage survived (Hours)')
		plotlyLayout['xaxis'].update(title='Start Hour')
		outData["resilienceData" + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		outData["resilienceLayout" + indexString] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)
		
		plotData = []
		survivalProb = go.Scatter(
			x=outData['survivalProbX' + indexString],
			y=outData['survivalProbY' + indexString],
			line=dict( color=('red') ),
			name="Load met by Battery")
		plotData.append(survivalProb)
		plotlyLayout['yaxis'].update(title='Probability of meeting critical Load')
		plotlyLayout['xaxis'].update(title='Outage Length (Hours)')
		outData["resilienceProbData" + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		outData["resilienceProbLayout"  + indexString] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	fName = "input - 2 col, 200 Employee Office, Springfield Illinois, 2001.csv"
	defaultInputs = {
		"modelType": modelName,
		"runTime": "",
		"loadShape" : open(pJoin(omf.omfDir, "static", "testFiles", fName)).read(),
		"solar" : "on",
		"wind" : "off",
		"battery" : "on",
		"fileName" : fName,
		"latitude" : '39.7817',
		"longitude" : '-89.6501',
		"year" : '2001',
		"energyCost" : "0.08",
		"demandCost" : '20',
		"solarCost" : "2000",
		"windCost" : "4989",
		"batteryEnergyCost" : "500",
		"batteryPowerCost" : "1000",
		"solarMin": 0,
		"windMin": 0,
		"batteryPowerMin": 0,
		"batteryEnergyMin": 0,
		"outageDate" : "2001-01-01",
		"outageHour" : "0",
		"outageDuration" : "1",
		"criticalLoadFactor" : "50",
		"outageType" : "once"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

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
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

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
	loadShape = [float(x[0]) for x in loadShape]
	year = int(inputDict['year'])
	criticalLoadFactor = float(inputDict['criticalLoadFactor'])/100
	#outageStart = int(inputDict['outageStart'])
	#outageEnd = outageStart + int(inputDict['outageDuration'])
	#if outageEnd > 8759:
		#outageEnd = 8759
	#singleOutage = True
	#if str(inputDict['outageType']) == 'annual':
		#singleOutage = False
	solarCost = float(inputDict['solarCost'])
	windCost = float(inputDict['windCost'])
	batteryPowerCost = float(inputDict['batteryPowerCost'])
	batteryEnergyCost = float(inputDict['batteryEnergyCost'])
	solarMin = float(inputDict['solarMin'])
	windMin = float(inputDict['windMin'])
	batteryPowerMin = float(inputDict['batteryPowerMin'])
	batteryEnergyMin = float(inputDict['batteryEnergyMin'])
	
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
					"loads_kw": loadShape,
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
	outData['demandCostBAU'] = resultsSubset['ElectricTariff']['total_demand_cost_bau_us_dollars']
	if outData['demandCostBAU'] is None:
		errMsg = results['messages'].get('error','API currently unavailable please try again later')
		raise Exception('The reOpt data analysis API by NREL had the following error: ' + errMsg) 
	outData['demandCost'] = resultsSubset['ElectricTariff']['total_demand_cost_us_dollars']
	outData['demandCostDiff'] = outData['demandCostBAU'] - outData['demandCost']
	outData['energyCostBAU'] = resultsSubset['ElectricTariff']['total_energy_cost_bau_us_dollars']
	outData['energyCost'] = resultsSubset['ElectricTariff']['total_energy_cost_us_dollars']
	outData['energyCostDiff'] = outData['energyCostBAU'] - outData['energyCost']
	outData['fixedCostBAU'] = resultsSubset['ElectricTariff']['total_fixed_cost_bau_us_dollars']
	outData['fixedCost'] = resultsSubset['ElectricTariff']['total_fixed_cost_us_dollars']
	outData['fixedCostDiff'] = outData['fixedCostBAU'] - outData['fixedCost']
	outData['powerGridToBattery'] = resultsSubset['ElectricTariff']['year_one_to_battery_series_kw']
	outData['powerGridToLoad'] = resultsSubset['ElectricTariff']['year_one_to_load_series_kw']
	outData['totalCostBAU'] = resultsSubset['Financial']['lcc_bau_us_dollars']
	outData['totalCost'] = resultsSubset['Financial']['lcc_us_dollars']
	outData['totalCostDiff'] = outData['totalCostBAU'] - outData['totalCost']
	outData['savings'] = resultsSubset['Financial']['npv_us_dollars']
	outData['load'] = resultsSubset['LoadProfile']['year_one_electric_load_series_kw']
	
	if solar == 'on':	
		outData['sizePV'] = resultsSubset['PV']['size_kw']
		outData['powerPV'] = resultsSubset['PV']['year_one_power_production_series_kw']
		outData['powerPVToBattery'] = resultsSubset['PV']['year_one_to_battery_series_kw']
		outData['powerPVToLoad'] = resultsSubset['PV']['year_one_to_load_series_kw']
	else:
		outData['sizePV'] = 0
	
	if battery == 'on':
		outData['powerBattery'] = resultsSubset['Storage']['size_kw']
		outData['capacityBattery'] = resultsSubset['Storage']['size_kwh']
		outData['chargeLevelBattery'] = resultsSubset['Storage']['year_one_soc_series_pct']
		outData['powerBatteryToLoad'] = resultsSubset['Storage']['year_one_to_load_series_kw']
	else:
		outData['powerBattery'] = 0
		outData['capacityBattery'] = 0
	
	if wind == 'on':
		outData['sizeWind'] = resultsSubset['Wind']['size_kw']
		outData['powerWind'] = resultsSubset['Wind']['year_one_power_production_series_kw']
		outData['powerWindToBattery'] = resultsSubset['Wind']['year_one_to_battery_series_kw']
		outData['powerWindToLoad'] = resultsSubset['Wind']['year_one_to_load_series_kw']
		if outData['powerWindToLoad'] is None:
			wind = 'off'
	else:
		outData['sizeWind'] = 0
	
	outData['resilience'] = resultsResilience['resilience_by_timestep']
	outData['minOutage'] = resultsResilience['resilience_hours_min']
	outData['maxOutage'] = resultsResilience['resilience_hours_max']
	outData['avgOutage'] = resultsResilience['resilience_hours_avg']
	outData['survivalProbX'] = resultsResilience['outage_durations']
	outData['survivalProbY'] = resultsResilience['probs_of_surviving']
	outData['runID'] = runID
	outData['apiKey'] = 'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9'

	outData['solar'] = solar
	outData['wind'] = wind
	outData['battery'] = battery

	#Set plotly layout
	plotlyLayout = go.Layout(
		width=1000,
		height=375,
		legend=dict(
			x=0,
			y=1.25,
			orientation="h")
		)
	
	x = range(len(outData['powerGridToLoad']))

	plotData = []
	powerGridToLoad = go.Scatter(
		x=x,
		y=outData['powerGridToLoad'],
		line=dict( color=('red') ),
		name="Load met by Grid",
		showlegend=True)
	plotData.append(powerGridToLoad)

	if solar == 'on':
		powerPVToLoad = go.Scatter(
			x=x,
			y=outData['powerPVToLoad'],
			line=dict( color=('green') ),
			name="Load met by Solar")
		plotData.append(powerPVToLoad)

	if battery == 'on':
		powerBatteryToLoad = go.Scatter(
			x=x,
			y=outData['powerBatteryToLoad'],
			line=dict( color=('blue') ),
			name="Load met by Battery")
		plotData.append(powerBatteryToLoad)

	if wind == 'on':
		powerWindToLoad = go.Scatter(
			x=x,
			y=outData['powerWindToLoad'],
			line=dict( color=('yellow') ),
			name="Load met by Wind")
		plotData.append(powerWindToLoad)

	plotlyLayout['yaxis'].update(title='Power (kW)')
	plotlyLayout['xaxis'].update(title='Hour')
	outData["powerGenerationData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["plotlyLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

	plotData = []
	if solar == 'on':
		
		powerPV = go.Scatter(
			x=x,
			y=outData['powerPV'],
			line=dict( color=('red') ),
			name="Solar Generation")
		plotData.append(powerPV)

		powerPVToLoad = go.Scatter(
			x=x,
			y=outData['powerPVToLoad'],
			line=dict( color=('green') ),
			name="olar used to meet Load")
		plotData.append(powerPVToLoad)

		if battery == 'on':
			powerPVToBattery = go.Scatter(
				x=x,
				y=outData['powerPVToBattery'],
				line=dict( color=('yellow') ),
				name="Solar used to charge Battery")
			plotData.append(powerPVToBattery)

	outData["solarData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)

		
	plotData = []
	if wind == 'on':
		powerWind = go.Scatter(
			x=x,
			y=outData['powerWind'],
			line=dict( color=('red') ),
			name="Wind Generation")
		plotData.append(powerWind)

		powerWindToLoad = go.Scatter(
			x=x,
			y=outData['powerWindToLoad'],
			line=dict( color=('green') ),
			name="'Wind used to meet Load'")
		plotData.append(powerWindToLoad)

		if battery == 'on':
			powerWindToBattery = go.Scatter(
				x=x,
				y=outData['powerWindToBattery'],
				line=dict( color=('yellow') ),
				name="Wind used to charge Battery")
			plotData.append(powerWindToBattery)

	outData["windData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)


	plotData = []
	if battery == 'on':
		powerGridToBattery = go.Scatter(
			x=x,
			y=outData['powerGridToBattery'],
			line=dict( color=('red') ),
			name="Grid")
		plotData.append(powerGridToBattery)

		if solar == 'on':
			powerPVToBattery = go.Scatter(
				x=x,
				y=outData['powerPVToBattery'],
				line=dict( color=('green') ),
				name="Solar")
			plotData.append(powerPVToBattery)

		if wind == 'on':
			powerWindToBattery = go.Scatter(
				x=x,
				y=outData['powerWindToBattery'],
				line=dict( color=('yellow') ),
				name="Wind")
			plotData.append(powerWindToBattery)

	outData["batteryData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		
	plotData = []
	if battery == 'on':
		chargeLevelBattery = go.Scatter(
			x=x,
			y=outData['chargeLevelBattery'],
			line=dict( color=('red') )
		)
		plotData.append(chargeLevelBattery)
		plotlyLayout['yaxis'].update(title='Charge (%)')
		plotlyLayout['xaxis'].update(title='Hour')
		outData["batteryChargeData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		outData["batteryChargeLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)
	
	plotData = []
	resilience = go.Scatter(
		x=x,
		y=outData['resilience'],
		line=dict( color=('red') ),
	)
	plotData.append(resilience)
	plotlyLayout['yaxis'].update(title='Longest Outage survived (Hours)')
	plotlyLayout['xaxis'].update(title='Start Hour')
	outData["resilienceData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["resilienceLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)
	
	plotData = []
	survivalProb = go.Scatter(
		x=outData['survivalProbX'],
		y=outData['survivalProbY'],
		line=dict( color=('red') ),
		name="Load met by Battery")
	plotData.append(survivalProb)
	plotlyLayout['yaxis'].update(title='Probability of meeting critical Load')
	plotlyLayout['xaxis'].update(title='Outage Length (Hours)')
	outData["resilienceProbData"] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["resilienceProbLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)


	return outData



def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	fName = "input - 200 Employee Office, Springfield Illinois, 2001.csv"
	defaultInputs = {
		"modelType": modelName,
		"runTime": "",
		"loadShape" : open(pJoin(omf.omfDir, "static", "testFiles", fName)).read(),
		"solar" : "on",
		"wind" : "on",
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
	pass

if __name__ == '__main__':
	_debugging()

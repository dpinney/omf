import matplotlib, warnings, csv, json
from os.path import join as pJoin
from matplotlib import pyplot as plt
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf.solvers.REopt import run as runREopt
from omf.solvers.REopt import runResilience as runResilienceREopt
import numpy as np

warnings.filterwarnings('ignore')

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "The microGridDesign model ..."
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

	if outData['powerWindToLoad'] is None:
		wind = 'off'

	outData['solar'] = solar
	outData['wind'] = wind
	outData['battery'] = battery

	plt.clf()
	plotLabels = []
	#plt.plot(outData['load'])
	#plotLabels.append('Total Load')

	x = range(len(outData['powerGridToLoad']))

	plt.bar(x, outData['powerGridToLoad'], width=1)
	bottom = np.array(outData['powerGridToLoad'])
	plotLabels.append('Load met by Grid')
	if solar == 'on':
		plt.bar(x, outData['powerPVToLoad'],bottom=bottom, width=1)
		bottom += np.array(outData['powerPVToLoad'])
		plotLabels.append('Load met by Solar')
	if battery == 'on':
		plt.bar(x, outData['powerBatteryToLoad'],bottom=bottom, width=1)
		bottom += np.array(outData['powerBatteryToLoad'])
		plotLabels.append('Load met by Battery')
	if wind == 'on':
		plt.bar(x, outData['powerWindToLoad'],bottom=bottom, width=1)
		bottom += np.array(outData['powerWindToLoad'])
		plotLabels.append('Load met by Wind')
	plt.ylabel('Power (kW)')
	plt.xlabel('Hour')
	lgd = plt.legend(labels=plotLabels, bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", 
	mode="expand", borderaxespad=0, ncol=3)
	plt.savefig(modelDir + '/loadPlot.png', dpi=600)

	plt.clf()
	plotLabels = []
	bottom = 0*np.array(x,dtype='float64')
	if solar == 'on':
		plt.bar(x, outData['powerPV'],width=1)
		bottom += np.array(outData['powerPV'])
		plotLabels.append('Solar Generation')
		plt.bar(x, outData['powerPVToLoad'],bottom=bottom, width=1)
		bottom += np.array(outData['powerPVToLoad'])
		plotLabels.append('Solar used to meet Load')
		if battery == 'on':
			plt.bar(x, outData['powerPVToBattery'],bottom=bottom, width=1)
			bottom += np.array(outData['powerPVToBattery'])
			plotLabels.append('Solar used to charge Battery')
		plt.ylabel('Power (kW)')
		plt.xlabel('Hour')
		lgd = plt.legend(labels=plotLabels, bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", 
		mode="expand", borderaxespad=0, ncol=3)
	plt.savefig(modelDir + '/solarPlot.png', dpi=600)

	plt.clf()
	plotLabels = []
	bottom = 0*np.array(x,dtype='float64')
	if wind == 'on':
		plt.bar(x, outData['powerWind'],width=1)
		bottom += np.array(outData['powerWind'])
		plotLabels.append('Wind Generation')
		plt.bar(x, outData['powerWindToLoad'],bottom=bottom, width=1)
		bottom += np.array(outData['powerWindToLoad'])
		plotLabels.append('Wind used to meet Load')
		if battery == 'on':
			plt.bar(x, outData['powerWindToBattery'],bottom=bottom, width=1)
			bottom += np.array(outData['powerWindToBattery'])
			plotLabels.append('Wind used to charge Battery')
		plt.ylabel('Power (kW)')
		plt.xlabel('Hour')
		lgd = plt.legend(labels=plotLabels, bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", 
		mode="expand", borderaxespad=0, ncol=3)
	plt.savefig(modelDir + '/windPlot.png', dpi=600)
	
	plt.clf()
	plotLabels = []
	bottom = 0*np.array(x,dtype='float64')
	if battery == 'on':
		plt.bar(x, outData['powerGridToBattery'], width=1)
		bottom += np.array(outData['powerGridToBattery'])
		plotLabels.append('Grid')
		if solar == 'on':
			plt.bar(x, outData['powerPVToBattery'],bottom=bottom, width=1)
			bottom += np.array(outData['powerPVToBattery'])
			plotLabels.append('Solar')
		if wind == 'on':
			plt.bar(x, outData['powerWindToBattery'],bottom=bottom, width=1)
			bottom += np.array(outData['powerWindToBattery'])
			plotLabels.append('Wind')
		plt.ylabel('Power (kW)')
		plt.xlabel('Hour')
		lgd = plt.legend(labels=plotLabels, bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", 
		mode="expand", borderaxespad=0, ncol=3)
	plt.savefig(modelDir + '/batteryPlot.png', dpi=600)

	plt.clf()
	if battery == 'on':
		plt.bar(x, outData['chargeLevelBattery'], width=1)
		plt.ylabel('Charge (%)')
		plt.xlabel('Hour')
	plt.savefig(modelDir + '/batteryChargePlot.png', dpi=600)

	plt.clf()
	plt.bar(x, outData['resilience'], width=1)
	plt.ylabel('Longest Outage survived')
	plt.xlabel('Start Hour')
	plt.savefig(modelDir + '/resiliencePlot.png', dpi=600)

	plt.clf()
	plt.bar(outData['survivalProbX'],outData['survivalProbY'], width=1)
	plt.ylabel('Probability of meeting critical Load')
	plt.xlabel('Outage Length')
	plt.savefig(modelDir + '/resilienceProbPlot.png', dpi=600)
	plt.clf()

	with open(pJoin(modelDir,"loadPlot.png"),"rb") as inFile:
		outData["loadPlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"solarPlot.png"),"rb") as inFile:
		outData["solarPlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"windPlot.png"),"rb") as inFile:
		outData["windPlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"batteryPlot.png"),"rb") as inFile:
		outData["batteryPlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"batteryChargePlot.png"),"rb") as inFile:
		outData["batteryChargePlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"resiliencePlot.png"),"rb") as inFile:
		outData["resiliencePlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"resilienceProbPlot.png"),"rb") as inFile:
		outData["resilienceProbPlot"] = inFile.read().encode("base64")

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
		"criticalLoadFactor" : "100",
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

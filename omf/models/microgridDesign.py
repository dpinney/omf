''' Design microgrid with optimal generation mix for economics and/or reliability. '''
import warnings, csv, json
from os.path import join as pJoin
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objs as go
import omf
import omf.solvers.REopt as REopt
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# warnings.filterwarnings('ignore')

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "The microGridDesign model uses a 1yr load profile to determine the most economical combination of solar, wind, and storage technologies to use in a microgrid. The model also provides basic resiliency analysis."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	solar = inputDict['solar'] 
	wind = inputDict['wind']
	battery = inputDict['battery']
	urdbLabelSwitch = inputDict['urdbLabelSwitch']
	outData['solar'] = inputDict['solar']
	outData['wind'] = inputDict['wind']
	outData['battery'] = inputDict['battery']
	outData['year'] = inputDict['year']
	outData['urdbLabelSwitch'] = inputDict['urdbLabelSwitch']

	# Setting up the loadShape file.
	with open(pJoin(modelDir,"loadShape.csv"),"w") as loadShapeFile:
		loadShapeFile.write(inputDict['loadShape'])

	try:
		loadShape = []
		with open(pJoin(modelDir,"loadShape.csv"), newline='') as inFile:
			reader = csv.reader(inFile)
			for row in reader:
				loadShape.append(row) 
			if len(loadShape)!=8760: raise Exception
	except:
		errorMessage = "Loadshape CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-demandResponse#walkthrough'>OMF Wiki demandResponse</a>"
		raise Exception(errorMessage)

	# Setting up the criticalLoadShape file.
	# ToDo: make a condition to make criticalLoadShape file optional, and not needed in default
	# make a switch for "User supplying critical loadshape?"
	# if "User supplying critical loadshape?" = True:
	with open(pJoin(modelDir,"criticalLoadShape.csv"),"w") as criticalLoadShapeFile:
		criticalLoadShapeFile.write(inputDict['criticalLoadShape'])

	try:
		criticalLoadShape = []
		with open(pJoin(modelDir,"criticalLoadShape.csv"), newline='') as inFile:
			reader = csv.reader(inFile)
			for row in reader:
				criticalLoadShape.append(row) 
			if len(criticalLoadShape)!=8760: raise Exception
	except:
		errorMessage = "Critical Loadshape CSV file is incorrect format. Please see valid format definition at <a target='_blank' href='https://github.com/dpinney/omf/wiki/Models-~-demandResponse#walkthrough'>OMF Wiki demandResponse</a>"
		raise Exception(errorMessage)

	latitude = float(inputDict['latitude'])
	longitude = float(inputDict['longitude'])
	energyCost = float(inputDict['energyCost'])
	demandCost = float(inputDict['demandCost'])
	if urdbLabelSwitch == 'on':
		urdbLabel = str(inputDict['urdbLabel'])
	# TODO: Enable all instances of 'annualCostSwitch', 'energyCostMonthly', 'demandCostMonthly' in mgDesign.py once a suitable way to enter a list of 12 monthly rates is found for mgDesign.html
	# annualCostSwitch = inputDict['annualCostSwitch']
	# energyCostMonthly = inputDict['energyCostMonthly']
	# demandCostMonthly = inputDict['demandCostMonthly']
	wholesaleCost = float(inputDict['wholesaleCost'])
	omCostEscalator = float(inputDict['omCostEscalator'])
	year = int(inputDict['year'])
	analysisYears = int(inputDict['analysisYears'])
	discountRate = float(inputDict['discountRate'])
	criticalLoadFactor = float(inputDict['criticalLoadFactor'])
	solarMacrsOptionYears = float(inputDict['solarMacrsOptionYears'])
	windMacrsOptionYears = float(inputDict['windMacrsOptionYears'])
	batteryMacrsOptionYears = float(inputDict['batteryMacrsOptionYears'])
	dieselMacrsOptionYears = float(inputDict['dieselMacrsOptionYears'])
	solarItcPercent = float(inputDict['solarItcPercent'])
	windItcPercent = float(inputDict['windItcPercent'])
	batteryItcPercent = float(inputDict['batteryItcPercent'])
	solarCost = float(inputDict['solarCost'])
	windCost = float(inputDict['windCost'])
	batteryPowerCost = float(inputDict['batteryPowerCost'])
	batteryCapacityCost = float(inputDict['batteryCapacityCost'])
	batteryPowerCostReplace = float(inputDict['batteryPowerCostReplace'])
	batteryCapacityCostReplace = float(inputDict['batteryCapacityCostReplace'])
	batteryPowerReplaceYear = float(inputDict['batteryPowerReplaceYear'])
	batteryCapacityReplaceYear = float(inputDict['batteryCapacityReplaceYear'])
	dieselGenCost = float(inputDict['dieselGenCost'])
	solarMin = float(inputDict['solarMin'])
	windMin = float(inputDict['windMin'])
	batteryPowerMin = float(inputDict['batteryPowerMin'])
	batteryCapacityMin = float(inputDict['batteryCapacityMin'])
	solarMax = float(inputDict['solarMax'])
	windMax = float(inputDict['windMax'])
	batteryPowerMax = float(inputDict['batteryPowerMax'])
	batteryCapacityMax = float(inputDict['batteryCapacityMax'])
	solarExisting = float(inputDict['solarExisting'])
	fuelAvailable = float(inputDict['fuelAvailable'])
	genExisting = float(inputDict['genExisting'])
	minGenLoading = float(inputDict['minGenLoading'])
	outage_start_hour = float(inputDict['outage_start_hour'])
	outage_end_hour = outage_start_hour + float(inputDict['outageDuration'])
	if outage_end_hour > 8759:
		outage_end_hour = 8760
	value_of_lost_load = float(inputDict['value_of_lost_load'])
	solarCanExport = bool(inputDict['solarCanExport'])
	solarCanCurtail = bool(inputDict['solarCanCurtail'])
	# explicitly convert string inputs from microgridDesign.html into usable boolean for REopt Scenario
	if inputDict['solarCanExport'] == "true":
		solarCanExport = True
	elif inputDict['solarCanExport'] == "false":
		solarCanExport = False
	if inputDict['solarCanCurtail'] == "true":
		solarCanCurtail = True
	elif inputDict['solarCanCurtail'] == "false":
		solarCanCurtail = False
	userCriticalLoadShape = bool(inputDict['userCriticalLoadShape'])
	if inputDict['userCriticalLoadShape'] == "true":
		userCriticalLoadShape = True
	elif inputDict['userCriticalLoadShape'] == "false":
		userCriticalLoadShape = False
	dieselMax = float(inputDict['dieselMax'])
	dieselMin = float(inputDict['dieselMin'])
	dieselFuelCostGal = float(inputDict['dieselFuelCostGal'])
	dieselCO2Factor = float(inputDict['dieselCO2Factor'])
	dieselOMCostKw = float(inputDict['dieselOMCostKw'])
	dieselOMCostKwh = float(inputDict['dieselOMCostKwh'])
	dieselOnlyRunsDuringOutage = bool(inputDict['dieselOnlyRunsDuringOutage'])
	if inputDict['dieselOnlyRunsDuringOutage'] == "true":
		dieselOnlyRunsDuringOutage = True
	elif inputDict['dieselOnlyRunsDuringOutage'] == "false":
		dieselOnlyRunsDuringOutage = False

	#outageStart = int(inputDict['outageStart'])
	#outageEnd = outageStart + indexStringnt(inputDict['outageDuration'])
	#if outageEnd > 8759:
		#outageEnd = 8759
	#singleOutage = True
	#if str(inputDict['outageType']) == 'annual':
		#singleOutage = False
	
	loadShape = np.array(loadShape)
	criticalLoadShape = np.array(criticalLoadShape)
	numRows = loadShape.shape[0]
	numCols = loadShape.shape[1]
	outData['numScenarios'] = numCols+1;

	totalLoad = np.zeros(numRows)
	totalCriticalLoad = np.zeros(numRows)
	for i in range(0,1+numCols):
		indexString = str(i+1)

		if i == numCols:
			load = totalLoad
			criticalLoad = totalCriticalLoad
		else:
			load = loadShape[:,i]
			print(type(load), load[0], load )
			load = [float(x) for x in load]
			totalLoad = np.add(totalLoad, load)

			criticalLoad = criticalLoadShape[:,i]
			# print(type(load), load[0], load )
			criticalLoad = [float(x) for x in criticalLoad]
			totalCriticalLoad = np.add(totalCriticalLoad, criticalLoad)

		jsonifiableLoad = list(load)
		jsonifiableCriticalLoad = list(criticalLoad);

		# Create the input JSON file for REopt
		# TODO: To use energyCostMonthly, comment out demandCost and energyCost lines in the Scenario JSON
		scenario = {
			"Scenario": {
				"Site": {
					"latitude": latitude,
					"longitude": longitude,
					"ElectricTariff": {
						"wholesale_rate_us_dollars_per_kwh": wholesaleCost,
						"wholesale_rate_above_site_load_us_dollars_per_kwh": wholesaleCost
					},
					"LoadProfile": {
						"loads_kw": jsonifiableLoad,
						"year": year
					},
					"Financial": {
						"value_of_lost_load_us_dollars_per_kwh": value_of_lost_load,
						"analysis_years": analysisYears,
						"om_cost_escalation_pct": omCostEscalator,
						"offtaker_discount_pct": discountRate
					},
					"PV": {
						"installed_cost_us_dollars_per_kw": solarCost,
						"min_kw": solarMin,
						"can_export_beyond_site_load": solarCanExport,
						"can_curtail": solarCanCurtail,
						"macrs_option_years": solarMacrsOptionYears,
						"federal_itc_pct": solarItcPercent
					},
					"Storage": {
						"installed_cost_us_dollars_per_kw": batteryPowerCost,
						"installed_cost_us_dollars_per_kwh": batteryCapacityCost,
						"replace_cost_us_dollars_per_kw": batteryPowerCostReplace,
						"replace_cost_us_dollars_per_kwh": batteryCapacityCostReplace,
						"inverter_replacement_year": batteryPowerReplaceYear,
						"battery_replacement_year": batteryCapacityReplaceYear,
						"min_kw": batteryPowerMin,
						"min_kwh": batteryCapacityMin,
						"macrs_option_years": batteryMacrsOptionYears,
						"total_itc_percent": batteryItcPercent
					},
					"Wind": {
						"installed_cost_us_dollars_per_kw": windCost,
						"min_kw": windMin,
						"macrs_option_years": windMacrsOptionYears,
						"federal_itc_pct": windItcPercent
					},
					"Generator": {
						"installed_cost_us_dollars_per_kw": dieselGenCost,
						"generator_only_runs_during_grid_outage": dieselOnlyRunsDuringOutage,
						"macrs_option_years": dieselMacrsOptionYears
					}
				}
			}
		}

		# TODO: Enable all instances of 'annualCostSwitch', 'energyCostMonthly', 'demandCostMonthly' in mgDesign.py once a suitable way to enter a list of 12 monthly rates is found for mgDesign.html
		# pick whether to use annual or monthly rates
		# if annualCostSwitch == 'on':
		# 	scenario['Scenario']['Site']['ElectricTariff']['blended_annual_rates_us_dollars_per_kwh'] = energyCost
		# 	scenario['Scenario']['Site']['ElectricTariff']['blended_annual_demand_charges_us_dollars_per_kw'] = demandCost
		# elif annualCostSwitch == 'off':
		# 	scenario['Scenario']['Site']['ElectricTariff']['blended_monthly_rates_us_dollars_per_kwh'] = energyCostMonthly
		# 	scenario['Scenario']['Site']['ElectricTariff']['blended_monthly_demand_charges_us_dollars_per_kw'] = demandCostMonthly
		# solar and battery have default 'max_kw' == 1000000000; Wind has default 'max_kw' == 0 and thus must be set explicitly; Check https://developer.nrel.gov/docs/energy-optimization/reopt-v1 for updates
		if solar == 'off':
			scenario['Scenario']['Site']['PV']['max_kw'] = 0
		elif solar == 'on':
			scenario['Scenario']['Site']['PV']['max_kw'] = solarMax
			scenario['Scenario']['Site']['PV']['existing_kw'] = solarExisting
			scenario['Scenario']['Site']['LoadProfile']['loads_kw_is_net'] = False
			# To turn off energy export/net-metering, set wholesaleCost to "0" and excess PV gen will be curtailed
			if solarCanExport == False:
				scenario['Scenario']['Site']['ElectricTariff']["wholesale_rate_above_site_load_us_dollars_per_kwh"] = 0
				scenario['Scenario']['Site']['ElectricTariff']["wholesale_rate_us_dollars_per_kwh"] = 0;
		if wind == 'off':
			scenario['Scenario']['Site']['Wind']['max_kw'] = 0
		elif wind == 'on':
			scenario['Scenario']['Site']['Wind']['max_kw'] = windMax;
		if battery == 'off':
			scenario['Scenario']['Site']['Storage']['max_kw'] = 0
			scenario['Scenario']['Site']['Storage']['max_kwh'] = 0 #May not be a needed constraint, even though it is stated as such in the NREL docs
		elif battery == 'on':
			scenario['Scenario']['Site']['Storage']['max_kw'] = batteryPowerMax
			scenario['Scenario']['Site']['Storage']['max_kwh'] = batteryCapacityMax;
		# if outage_start_hour is > 0, a resiliency optimization that includes diesel is triggered
		if outage_start_hour != 0:
			scenario['Scenario']['Site']['LoadProfile']['outage_is_major_event'] = True
			scenario['Scenario']['Site']['LoadProfile']['critical_load_pct'] = criticalLoadFactor
			scenario['Scenario']['Site']['LoadProfile']['outage_start_time_step'] = outage_start_hour
			scenario['Scenario']['Site']['LoadProfile']['outage_end_time_step'] = outage_end_hour
			scenario['Scenario']['Site']['Generator']['fuel_avail_gal'] = fuelAvailable
			scenario['Scenario']['Site']['Generator']['min_turn_down_pct'] = minGenLoading
			scenario['Scenario']['Site']['Generator']['existing_kw'] = genExisting
			scenario['Scenario']['Site']['Generator']['diesel_fuel_cost_us_dollars_per_gallon'] = dieselFuelCostGal
			scenario['Scenario']['Site']['Generator']['emissions_factor_lb_CO2_per_gal'] = dieselCO2Factor
			scenario['Scenario']['Site']['Generator']['om_cost_us_dollars_per_kw'] = dieselOMCostKw
			scenario['Scenario']['Site']['Generator']['om_cost_us_dollars_per_kwh'] = dieselOMCostKwh


			# use userCriticalLoadShape only if True, else model defaults to criticalLoadFactor
			if userCriticalLoadShape == True:
				scenario['Scenario']['Site']['LoadProfile']['critical_loads_kw'] = jsonifiableCriticalLoad
			# diesel has a quirk in how it gets inputted to REopt such that when strictly specified, allOutputData["sizeDiesel1"] = allInputData['dieselMax'] + allInputData['genExisting']
			if dieselMax - genExisting > 0:
				scenario['Scenario']['Site']['Generator']['max_kw'] = dieselMax - genExisting
			else:
				scenario['Scenario']['Site']['Generator']['max_kw'] = 0
			if dieselMin - genExisting > 0:
				scenario['Scenario']['Site']['Generator']['min_kw'] = dieselMin - genExisting
			else:
				scenario['Scenario']['Site']['Generator']['min_kw'] = 0

		# set rates
		if urdbLabelSwitch == 'off':
			scenario['Scenario']['Site']['ElectricTariff']['blended_annual_rates_us_dollars_per_kwh'] = energyCost
			scenario['Scenario']['Site']['ElectricTariff']['blended_annual_demand_charges_us_dollars_per_kw'] = demandCost
		elif urdbLabelSwitch == 'on':
			scenario['Scenario']['Site']['ElectricTariff']['urdb_label'] = urdbLabel


		with open(pJoin(modelDir, "Scenario_test_POST.json"), "w") as jsonFile:
			json.dump(scenario, jsonFile)

		# Run REopt API script
		REopt.run(pJoin(modelDir, 'Scenario_test_POST.json'), pJoin(modelDir, 'results.json'))
		with open(pJoin(modelDir, 'results.json')) as jsonFile:
			results = json.load(jsonFile)
		
		runID = results['outputs']['Scenario']['run_uuid']
		REopt.runResilience(runID, pJoin(modelDir, 'resultsResilience.json'))
		with open(pJoin(modelDir, 'resultsResilience.json')) as jsonFile:
			resultsResilience = json.load(jsonFile)

		resultsSubset = results['outputs']['Scenario']['Site']
		outData['demandCostBAU' + indexString] = resultsSubset['ElectricTariff']['total_demand_cost_bau_us_dollars']
		if outData['demandCostBAU' + indexString] is None:
			errMsg = results['messages'].get('error','API currently unavailable please try again later')
			raise Exception('The REopt data analysis API by NREL had the following error: ' + errMsg) 
	
		outData['demandCost' + indexString] = resultsSubset['ElectricTariff']['total_demand_cost_us_dollars']
		outData['demandCostDiff' + indexString] = round(outData['demandCostBAU' + indexString] - outData['demandCost' + indexString],2)
		outData['energyCostBAU' + indexString] = resultsSubset['ElectricTariff']['total_energy_cost_bau_us_dollars']
		outData['energyCost' + indexString] = resultsSubset['ElectricTariff']['total_energy_cost_us_dollars']
		outData['energyCostDiff' + indexString] = round(outData['energyCostBAU' + indexString] - outData['energyCost' + indexString],2)
		outData['fixedCostBAU' + indexString] = resultsSubset['ElectricTariff']['total_fixed_cost_bau_us_dollars']
		outData['fixedCost' + indexString] = resultsSubset['ElectricTariff']['total_fixed_cost_us_dollars']
		outData['fixedCostDiff' + indexString] = outData['fixedCostBAU' + indexString] - outData['fixedCost' + indexString]
		outData['powerGridToBattery' + indexString] = resultsSubset['ElectricTariff']['year_one_to_battery_series_kw']
		outData['powerGridToLoad' + indexString] = resultsSubset['ElectricTariff']['year_one_to_load_series_kw']
		outData['totalCostBAU' + indexString] = resultsSubset['Financial']['lcc_bau_us_dollars']
		outData['totalCost' + indexString] = resultsSubset['Financial']['lcc_us_dollars']
		outData['totalCostDiff' + indexString] = round(outData['totalCostBAU' + indexString] - outData['totalCost' + indexString],2)
		outData['savings' + indexString] = resultsSubset['Financial']['npv_us_dollars']
		outData['initial_capital_costs' + indexString] = resultsSubset['Financial']['initial_capital_costs']
		outData['initial_capital_costs_after_incentives' + indexString] = resultsSubset['Financial']['initial_capital_costs_after_incentives']
		outData['load' + indexString] = resultsSubset['LoadProfile']['year_one_electric_load_series_kw']
		outData['avgLoad' + indexString] = round(sum(resultsSubset['LoadProfile']['year_one_electric_load_series_kw'])/len(resultsSubset['LoadProfile']['year_one_electric_load_series_kw']),1)
		
		# carry over analysisYears as this is not an REopt output
		outData['analysisYears' + indexString] = analysisYears
		outData['discountRate' + indexString] = discountRate

		# outputs to be used in microgridup.py
		# outData['yearOneEmissionsLbsBau' + indexString] = resultsSubset['year_one_emissions_bau_lb_C02']
		# outData['yearOneEmissionsLbs' + indexString] = resultsSubset['year_one_emissions_lb_C02']
		# outData['yearOneEmissionsTons' + indexString] = round((outData['yearOneEmissionsLbs' + indexString])/2205,0)
		# outData['yearOneEmissionsReducedTons' + indexString] = round((resultsSubset['year_one_emissions_bau_lb_C02'] - resultsSubset['year_one_emissions_lb_C02'])/2205,0)
		# outData['yearOneEmissionsReducedPercent' + indexString] = round((resultsSubset['year_one_emissions_bau_lb_C02'] - resultsSubset['year_one_emissions_lb_C02'])/resultsSubset['year_one_emissions_bau_lb_C02']*100,0)		
		# outData['yearOnePercentRenewable' + indexString] = round(resultsSubset['renewable_electricity_energy_pct']*100,0)
		
		outData['yearOneEmissionsTons' + indexString] = round(resultsSubset['year_one_emissions_tCO2'])
		outData['yearOneEmissionsReducedTons' + indexString] = round(resultsSubset['year_one_emissions_tCO2_bau'] - resultsSubset['year_one_emissions_tCO2'])
		outData['yearOneEmissionsReducedPercent' + indexString] = round((resultsSubset['year_one_emissions_tCO2_bau'] - resultsSubset['year_one_emissions_tCO2'])/resultsSubset['year_one_emissions_tCO2_bau']*100,0)
		outData['yearOnePercentRenewable' + indexString] = round(resultsSubset['annual_renewable_electricity_pct']*100,0)
		outData['yearOneOMCostsBeforeTax' + indexString] = round(resultsSubset['Financial']['year_one_om_costs_before_tax_us_dollars'],0)
		

		if solar == 'on':
			outData['sizePV' + indexString] = resultsSubset['PV']['size_kw']
			outData['sizePVRounded' + indexString] = round(resultsSubset['PV']['size_kw'],1)
			outData['powerPV' + indexString] = resultsSubset['PV']['year_one_power_production_series_kw']
			outData['powerPVToBattery' + indexString] = resultsSubset['PV']['year_one_to_battery_series_kw']
			outData['powerPVToLoad' + indexString] = resultsSubset['PV']['year_one_to_load_series_kw']
			outData['powerPVCurtailed' + indexString] = resultsSubset['PV']['year_one_curtailed_production_series_kw']
			outData['powerPVToGrid' + indexString] = resultsSubset['PV']['year_one_to_grid_series_kw']
			outData['sizePVExisting' + indexString] = results['inputs']['Scenario']['Site']['PV']['existing_kw']
			outData['solarCost' + indexString] = float(inputDict['solarCost'])

		else:
			outData['sizePV' + indexString] = 0
			outData['sizePVRounded' + indexString] = 0
		
		if battery == 'on':
			outData['powerBattery' + indexString] = resultsSubset['Storage']['size_kw']
			outData['powerBatteryRounded' + indexString] = round(resultsSubset['Storage']['size_kw'],1)
			outData['capacityBattery' + indexString] = resultsSubset['Storage']['size_kwh']
			outData['capacityBatteryRounded' + indexString] = round(resultsSubset['Storage']['size_kwh'],1)
			outData['chargeLevelBattery' + indexString] = resultsSubset['Storage']['year_one_soc_series_pct']
			outData['powerBatteryToLoad' + indexString] = resultsSubset['Storage']['year_one_to_load_series_kw']
			outData['batteryPowerCost' + indexString] = float(inputDict['batteryPowerCost'])
			outData['batteryCapacityCost' + indexString] = float(inputDict['batteryCapacityCost'])
			# batteryPowerReplaceYear, batteryCapacityReplaceYear, 'batteryPowerCostReplace', 'batteryCapacityCostReplace', batteryKwExisting and batteryKwhExisting are pass through variables used in microgridUp project
			if 'batteryPowerCostReplace' in inputDict.keys():
				outData['batteryPowerCostReplace' + indexString] = float(inputDict['batteryPowerCostReplace'])
			if 'batteryCapacityCostReplace' in inputDict.keys():
				outData['batteryCapacityCostReplace' + indexString] = float(inputDict['batteryCapacityCostReplace'])
			if 'batteryPowerReplaceYear' in inputDict.keys():
				outData['batteryPowerReplaceYear' + indexString] = float(inputDict['batteryPowerReplaceYear'])
			if 'batteryCapacityReplaceYear' in inputDict.keys():
				outData['batteryCapacityReplaceYear' + indexString] = float(inputDict['batteryCapacityReplaceYear'])
			if 'batteryKwExisting' in inputDict.keys():
				outData['batteryKwExisting' + indexString] = float(inputDict['batteryKwExisting'])
			if 'batteryKwhExisting' in inputDict.keys():
				outData['batteryKwhExisting' + indexString] = float(inputDict['batteryKwhExisting'])

		else:
			outData['powerBattery' + indexString] = 0
			outData['capacityBattery' + indexString] = 0
			outData['powerBatteryRounded' + indexString] = 0
			outData['capacityBatteryRounded' + indexString] = 0
		
		if wind == 'on':
			outData['sizeWind' + indexString] = resultsSubset['Wind']['size_kw']
			outData['sizeWindRounded' + indexString] = round(resultsSubset['Wind']['size_kw'],1)
			outData['powerWind' + indexString] = resultsSubset['Wind']['year_one_power_production_series_kw']
			outData['powerWindToBattery' + indexString] = resultsSubset['Wind']['year_one_to_battery_series_kw']
			outData['powerWindToLoad' + indexString] = resultsSubset['Wind']['year_one_to_load_series_kw']
			outData['windCost' + indexString] = float(inputDict['windCost'])
			# windExisting is a pass through variables used in microgridUp project
			if 'windExisting' in inputDict.keys():
				outData['windExisting' + indexString] = float(inputDict['windExisting'])
		else:
			outData['sizeWind' + indexString] = 0
			outData['sizeWindRounded' + indexString] = 0

		# diesel generator does not follow on/off convention, as it is not turned on by user, but rather is automatically turned on when an outage is specified
		outData['sizeDiesel' + indexString] = resultsSubset['Generator']['size_kw']
		outData['sizeDieselRounded' + indexString] = round(resultsSubset['Generator']['size_kw'],1)
		outData['dieselGenCost' + indexString] = float(inputDict['dieselGenCost'])
		outData['dieselOnlyRunsDuringOutage' + indexString] = bool(inputDict['dieselOnlyRunsDuringOutage'])
		outData['dieselOMCostKw' + indexString] = float(inputDict['dieselOMCostKw'])
		outData['dieselOMCostKwh' + indexString] = float(inputDict['dieselOMCostKwh'])
		if resultsSubset['Generator']['size_kw'] == 0:
			outData['sizeDieselRounded' + indexString] = 0
		outData['fuelUsedDiesel' + indexString] = resultsSubset['Generator']['fuel_used_gal']
		outData['fuelUsedDieselRounded' + indexString] = round(resultsSubset['Generator']['fuel_used_gal'],0)
		outData['sizeDieselExisting' + indexString] = results['inputs']['Scenario']['Site']['Generator']['existing_kw']
		outData['powerDiesel' + indexString] = resultsSubset['Generator']['year_one_power_production_series_kw']
		outData['powerDieselToBattery' + indexString] = resultsSubset['Generator']['year_one_to_battery_series_kw']
		outData['powerDieselToLoad' + indexString] = resultsSubset['Generator']['year_one_to_load_series_kw']

		# output resilience stats if resilienceRun was successful
		if 'resilience_by_timestep' in resultsResilience:
			outData['resilience' + indexString] = resultsResilience['resilience_by_timestep']
			outData['minOutage' + indexString] = resultsResilience['resilience_hours_min']
			outData['maxOutage' + indexString] = resultsResilience['resilience_hours_max']
			outData['avgOutage' + indexString] = resultsResilience['resilience_hours_avg']
			outData['survivalProbX' + indexString] = resultsResilience['outage_durations']
			outData['survivalProbY' + indexString] = resultsResilience['probs_of_surviving']
			outData['avoidedOutageCosts' + indexString] = resultsResilience['avoided_outage_costs_us_dollars']

		outData['runID' + indexString] = runID
		outData['apiKey' + indexString] = 'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9'



		#Set plotly layout ---------------------------------------------------------------
		plotlyLayout = go.Layout(
			width=1000,
			height=375,
			legend=dict(
				x=0,
				y=1.25,
				orientation="h")
			)
		
		x = list(range(len(outData['powerGridToLoad' + indexString])))

		plotData = []
		powerGridToLoad = go.Scatter(
			x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
			y=outData['powerGridToLoad' + indexString],
			line=dict( color=('blue') ),
			name="Load met by Grid",
			hoverlabel = dict(namelength = -1),
			showlegend=True,
			stackgroup='one',
			mode='none')
		plotData.append(powerGridToLoad)

		if solar == 'on':
			powerPVToLoad = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerPVToLoad' + indexString],
				line=dict( color=('yellow') ),
				name="Load met by Solar",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerPVToLoad)

		if battery == 'on':
			powerBatteryToLoad = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerBatteryToLoad' + indexString],
				line=dict( color=('gray') ),
				name="Load met by Battery",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerBatteryToLoad)

		if wind == 'on':
			powerWindToLoad = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerWindToLoad' + indexString],
				line=dict( color=('purple') ),
				name="Load met by Wind",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerWindToLoad)

		if resultsSubset['Generator']['size_kw'] > 0:
			powerDieselToLoad = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerDieselToLoad' + indexString],
				line=dict( color=('brown') ),
				name="Load met by Fossil Gen",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerDieselToLoad)			

		plotlyLayout['yaxis'].update(title='Power (kW)')
		plotlyLayout['xaxis'].update(title='Time')
		outData["powerGenerationData" + indexString ] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
		outData["plotlyLayout"] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)

		plotData = []
		if solar == 'on':
			
			powerPVToLoad = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerPVToLoad' + indexString],
				line=dict( color=('yellow') ),
				name="Solar used to meet Load",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerPVToLoad)

			powerPVToGrid = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerPVToGrid' + indexString],
				line=dict( color=('blue') ),
				name="Solar exported to Grid",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerPVToGrid)

			powerPVCurtailed = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerPVCurtailed' + indexString],
				line=dict( color=('red') ),
				name="Solar power curtailed",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerPVCurtailed)

			if battery == 'on':
				powerPVToBattery = go.Scatter(
					x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
					y=outData['powerPVToBattery' + indexString],
					line=dict( color=('gray') ),
					name="Solar used to charge Battery",
					hoverlabel = dict(namelength = -1),
					stackgroup='one',
					mode='none')
				plotData.append(powerPVToBattery)

			# powerPV = go.Scatter(
			# 	x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
			# 	y=outData['powerPV' + indexString],
			# 	line=dict( color=('red') ),
			# 	name="Solar Generation")
			# plotData.append(powerPV)

		outData["solarData" + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)

			
		plotData = []
		if wind == 'on':
			
			powerWindToLoad = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerWindToLoad' + indexString],
				line=dict( color=('purple') ),
				name="Wind used to meet Load",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerWindToLoad)

			if battery == 'on':
				powerWindToBattery = go.Scatter(
					x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
					y=outData['powerWindToBattery' + indexString],
					line=dict( color=('gray') ),
					name="Wind used to charge Battery",
					hoverlabel = dict(namelength = -1),
					stackgroup='one',
					mode='none')
				plotData.append(powerWindToBattery)

			# powerWind = go.Scatter(
			# 	x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
			# 	y=outData['powerWind' + indexString],
			# 	line=dict( color=('red') ),
			# 	name="Wind Generation")
			# plotData.append(powerWind)

		outData["windData"  + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)

		plotData = []
		if resultsSubset['Generator']['size_kw'] > 0:
			
			powerDieselToLoad = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerDieselToLoad' + indexString],
				line=dict( color=('brown') ),
				name="Fossil Gen used to meet Load",
				hoverlabel = dict(namelength = -1),
				stackgroup='one',
				mode='none')
			plotData.append(powerDieselToLoad)

			if battery == 'on':
				powerDieselToBattery = go.Scatter(
					x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
					y=outData['powerDieselToBattery' + indexString],
					line=dict( color=('gray') ),
					name="Fossil Gen used to charge Battery",
					hoverlabel = dict(namelength = -1),
					stackgroup='one',
					mode='none')
				plotData.append(powerDieselToBattery)

			# powerDiesel = go.Scatter(
			# 	x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
			# 	y=outData['powerDiesel' + indexString],
			# 	line=dict( color=('red') ),
			# 	name="Fossil Generation")
			# plotData.append(powerDiesel)

		outData["dieselData"  + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)

		plotData = []
		if battery == 'on':
			powerGridToBattery = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['powerGridToBattery' + indexString],
				line=dict( color=('blue') ),
				name="Grid",
				stackgroup='one',
				mode='none')
			plotData.append(powerGridToBattery)

			if solar == 'on':
				powerPVToBattery = go.Scatter(
					x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
					y=outData['powerPVToBattery' + indexString],
					line=dict( color=('yellow') ),
					name="Solar",
					stackgroup='one',
					mode='none')
				plotData.append(powerPVToBattery)

			if wind == 'on':
				powerWindToBattery = go.Scatter(
					x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
					y=outData['powerWindToBattery' + indexString],
					line=dict( color=('purple') ),
					name="Wind",
					stackgroup='one',
					mode='none')
				plotData.append(powerWindToBattery)

			if resultsSubset['Generator']['size_kw'] > 0:
				powerDieselToBattery = go.Scatter(
					x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
					y=outData['powerDieselToBattery' + indexString],
					line=dict( color=('brown') ),
					name="Fossil Gen",
					stackgroup='one',
					mode='none')
				plotData.append(powerDieselToBattery)


		outData["batteryData" + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
			
		plotData = []
		if battery == 'on':
			chargeLevelBattery = go.Scatter(
				x=pd.to_datetime(x, unit = 'h', origin = pd.Timestamp(f'{year}-01-01')),
				y=outData['chargeLevelBattery' + indexString],
				line=dict( color=('red') )
			)
			plotData.append(chargeLevelBattery)
			plotlyLayout['yaxis'].update(title='Charge (%)')
			plotlyLayout['xaxis'].update(title='Time')
			outData["batteryChargeData" + indexString] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
			outData["batteryChargeLayout" + indexString] = json.dumps(plotlyLayout, cls=plotly.utils.PlotlyJSONEncoder)
		

		# plot resilience stats if resilienceRun was successful
		if 'resilience_by_timestep' in resultsResilience:
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

		if numCols == 1:
			break # if we only have a single load, don't run an additional combined load shape run.
	#print("Wind kw from resultsSubset:", resultsSubset['Wind']['size_kw'])

	return outData

def runtimeEstimate(modelDir):
	''' Estimated runtime of model in minutes. '''
	return 2.0

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	# fName = "input - col 1 commercial 120 kW per day, col 2 residential  30 kWh per day.csv"
	fName = "input - 200 Employee Office, Springfield Illinois, 2001.csv"
	with open(pJoin(omf.omfDir, "static", "testFiles", fName)) as f:
		load_shape = f.read()

	cfName = "critical_load_test.csv"
	with open(pJoin(omf.omfDir, "static", "testFiles", cfName)) as f:
		crit_load_shape = f.read()
	defaultInputs = {
		"modelType": modelName,
		"runTime": "",
		"loadShape" : load_shape,
		"criticalLoadShape" : crit_load_shape,
		"solar" : "on",
		"wind" : "off",
		"battery" : "on",
		"fileName" : fName,
		"criticalFileName" : cfName,
		"latitude" : '39.7817',
		"longitude" : '-89.6501',
		"year" : '2017',
		"analysisYears" : '25',
		"discountRate" : '0.083', # Nominal energy offtaker discount rate. In single ownership model the offtaker is also the generation owner
		"energyCost" : "0.1",
		"demandCost" : '20',
		"urdbLabelSwitch": "off",
		"urdbLabel" : '5b75cfe95457a3454faf0aea',
		# TODO: Enable all instances of 'annualCostSwitch', 'energyCostMonthly', 'demandCostMonthly' in mgDesign.py once a suitable way to enter a list of 12 monthly rates is found for mgDesign.html
		# "annualCostSwitch": "off",
		# "energyCostMonthly" : [0.0531, 0.0531, 0.0531, 0.0531, 0.0531, 0.0531, 0.0531, 0.0531, 0.0531, 0.0531, 0.0531, 0.0531],
		# "demandCostMonthly" : [8.6879, 8.6879, 8.6879, 8.6879, 8.6879, 8.6879, 8.6879, 8.6879, 8.6879, 8.6879, 8.6879, 8.6879],
		"wholesaleCost" : "0.034",
		"omCostEscalator" : "0.025", # annual O+M cost escalation rate for all generation types
		"solarMacrsOptionYears": "5", # Set to zero to disable MACRS accelerated depreciation
		"windMacrsOptionYears": "5", # Set to zero to disable MACRS accelerated depreciation
		"batteryMacrsOptionYears": "7", # Set to zero to disable MACRS accelerated depreciation
		"dieselMacrsOptionYears": 0, # Set to zero to disable MACRS accelerated depreciation
		"solarItcPercent": "0.26",
		"windItcPercent": "0.26",
		"batteryItcPercent": 0,
		"solarCost" : "1600",
		"windCost" : "4898",
		"batteryPowerCost" : "840",
		"batteryCapacityCost" : "420",
		"batteryPowerCostReplace" : "410",
		"batteryCapacityCostReplace" : "200",
		"batteryPowerReplaceYear": '10', # year at which batteryPowerCostReplace (the inverter) is reinstalled, one time
		"batteryCapacityReplaceYear": '10', # year at which batteryCapacityCostReplace (the battery cells) is reinstalled, one time
		"dieselGenCost": "500",
		"solarMin": 0,
		"windMin": 0,
		"batteryPowerMin": 0,
		"batteryCapacityMin": 0,
		"dieselMin": 0,
		"solarMax": "10000000",
		"windMax": "10000000",
		"batteryPowerMax": "1000000",
		"batteryCapacityMax": "1000000",
		"dieselMax": "100000",
		"solarExisting": 0,
		"userCriticalLoadShape": False,
		"criticalLoadFactor": ".5",
		"outage_start_hour": "500",
		"outageDuration": "24",
		"fuelAvailable": "20000",
		"genExisting": 0,
		"minGenLoading": "0.3",
		"dieselFuelCostGal": "3", # default value for diesel
		"dieselCO2Factor": 22.4, # default value for diesel
		"dieselOMCostKw": 10, # default value for diesel
		"dieselOMCostKwh": 0, # default value for diesel
		#"windExisting": "20",
		#"batteryKwExisting": 0,
		#"batteryKwhExisting": 0,
		"value_of_lost_load": "100",
		"solarCanCurtail": True,
		"solarCanExport": True,
		"dieselOnlyRunsDuringOutage": True
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
	renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

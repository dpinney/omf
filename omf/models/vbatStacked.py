''' Evaluate demand response energy and economic savings available using PNNL VirtualBatteries (VBAT) model. '''

import shutil, csv, os, math
from os.path import join as pJoin
import pandas as pd
import numpy as np
from datetime import datetime as dt
from numpy import npv

import __neoMetaModel__
from __neoMetaModel__ import *
from solvers import VB

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Calculate the energy storage capacity for a collection of thermostatically controlled loads."
hidden = True

def n(num):
	return "${:,.2f}".format(num)

def pyVbat(tempCurve, modelDir, i):
	vbType = i['load_type']
	# with open(pJoin(modelDir, 'temp.csv')) as f:
	# 	ambient = np.array([float(r[0]) for r in csv.reader(f)])
	ambient = np.array(tempCurve)
	variables = [i['capacitance'], i['resistance'], i['power'], i['cop'], 
		i['deadband'], float(i['setpoint']), i['number_devices']]
	variables = [float(v) for v in variables]
	variables.insert(0, ambient)

	if vbType == '1':
		return VB.AC(*variables).generate() # air conditioning
	elif vbType == '2':
		return VB.HP(*variables).generate() # heat pump
	elif vbType == '3':
		return VB.RG(*variables).generate() # refrigerator
	elif vbType == '4':
		ambient = np.array([[i]*60 for i in list(variables[0])]).reshape(365*24*60, 1)
		variables[0] = ambient
		variables.append(ambient)
		file = pJoin(__neoMetaModel__._omfDir,'static','testFiles',"Flow_raw_1minute_BPA.csv")
		water = np.genfromtxt(file, delimiter=',')
		variables.append(water)
		return VB.WH(*variables).generate() # water heater

def work(modelDir, ind):
	out = {}
	
	try:
		tempCurve = [float(x) for x in ind["tempCurve"].split('\n')]
		gt_demand = [float(x) for x in ind["gt_demandCurve"].split('\n')] if ind["payment_structure"] == "gt" else []
		with open(pJoin(modelDir, 'inputCsv.csv'), 'w') as f:
			f.write(ind["inputCsv"].replace('\r', ''))
	except:
		raise Exception("CSV file is incorrect format. Please see valid format "
			"definition at <a target='_blank' href = 'https://github.com/dpinney/"
			"omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>\nOMF Wiki "
			"storagePeakShave - Demand File CSV Format</a>")

	input_df = pd.read_csv(pJoin(modelDir, 'inputCsv.csv'), index_col=['Hour'])
	P_lower, P_upper, E_UL = pyVbat(tempCurve, modelDir, ind)

	input_df['VB Power upper (kW)'] = P_upper
	input_df['VB Power lower (kW)'] = [-x for x in P_lower]
	input_df['VB Energy upper (kWh)'] = E_UL
	input_df['VB Energy lower (kWh)'] = [-x for x in E_UL]
	
	if ind["payment_structure"] == "gt":
		output_df = VB.run_fhec(ind, gt_demand, input_df)

	else:
		output_df = VB.run_okec(ind, input_df)
		
	out["show_gt"] = "none" if len(gt_demand) == 0 else "";
		
	# ------------------------------- CASH FLOW --------------------------- #
	number_devices = float(ind["number_devices"])
	upkeep_cost = float(ind["unitUpkeepCost"])
	device_cost = float(ind["unitDeviceCost"])
	projYears = int(ind["projectionLength"])

	if ind["payment_structure"] == "gt":
		np_gt_demand = gt_demand #np.array(gt_demand)
		threshold = np.percentile(np_gt_demand, float(ind["peakPercentile"])*100)
		indexes = [i for i, l in enumerate(gt_demand) if l >= threshold]
		
		mult = float(ind["peakMultiplier"])
		rate = float(ind["electricityCost"])
		
		price_structure_before = sum([l*rate*mult if i in indexes else l*rate for i, l in enumerate(output_df["Load (kW)"])])
		price_structure_after = sum([l*rate*mult if i in indexes else l*rate for i, l in enumerate(output_df["Net load (kW)"])])
	if ind["payment_structure"] == "ppm":
		price_structure_before = (output_df['Load (kW)'].max()*float(ind["annual_peak_charge"]) + 
			output_df['Load (kW)'].mean()*float(ind["avg_demand_charge"]))
		price_structure_after = (output_df['Net load (kW)'].max()*float(ind["annual_peak_charge"]) + 
			output_df['Net load (kW)'].mean()*float(ind["avg_demand_charge"]))
	
	if ind["use_regulation"] == "on":
		regulation_after = (output_df['Regulation (kW)']*input_df['Reg-up Price ($/MW)']/1000).sum()
	else:
		regulation_after = 0

	total_upkeep_costs = upkeep_cost*number_devices
	cost_before = price_structure_before
	cost_after = price_structure_after - regulation_after
	
	gross_savings = cost_before - cost_after
	money_saved = gross_savings - total_upkeep_costs

	styling = "style='border-bottom: 3px solid black;'"

	out['cost_table'] = (
			"<tr><td style='font-weight: bold;'>Price Structure</td><td>{0}</td><td>{1}</td><td>{2}</td></tr>"
			# "<tr><td style='font-weight: bold;'>Deferral</td><td>$0.00</td><td>$0.00</td><td>$0.00</td></tr>"
			"<tr {6}><td style='font-weight: bold; border-bottom: 3px solid black;'>Regulation</td><td {6}>{3}</td><td {6}>{4}</td><td {6}>{5}</td></tr>"
		).format(n(price_structure_before), n(price_structure_after), n(price_structure_before - price_structure_after),
				n(0), n(regulation_after), n(regulation_after), 
				styling) + (
				"<tr><td colspan='2'>&nbsp;</td><td style='font-weight: bold;'>Gross Savings</td><td>{0}</td></tr>"
			"<tr><td colspan='2'>&nbsp;</td><td style='font-weight: bold;'>Upkeep Cost</td><td>-{1}</td></tr>"
			"<tr><td colspan='2'>&nbsp;</td><td style='font-weight: bold;'>Total Savings</td><td>{2}</td></tr>"
		).format(n(gross_savings), n(total_upkeep_costs), n(money_saved))

	cashFlowCurve = [money_saved for year in range(projYears)]
	cashFlowCurve.insert(0, -1 * number_devices * device_cost)  # insert initial investment
	out['SPP'] = (number_devices*device_cost)/(money_saved)
	out['netCashflow'] = cashFlowCurve
	out['cumulativeCashflow'] = [sum(cashFlowCurve[:i+1]) for i, d in enumerate(cashFlowCurve)]
	out['NPV'] = npv(float(ind["discountRate"])/100, cashFlowCurve)

	out["gt_demand"] = gt_demand
	out["demand"] = output_df['Load (kW)'].tolist()
	out["VBpower"] = output_df['VB power (kW)'].tolist()
	out["VBenergy"] = [-x for x in output_df['VB energy (kWh)'].tolist()]
	out["demandAdjusted"] = output_df['Net load (kW)'].tolist()
	out["regulation"] = output_df['Regulation (kW)'].tolist() if 'Regulation (kW)' in output_df else 0
	# [0]*output_df.shape[0]

	out['vbpu'] = input_df['VB Power upper (kW)'].tolist()
	out['vbpl'] = input_df['VB Power lower (kW)'].tolist()
	out['vbeu'] = input_df['VB Energy upper (kWh)'].tolist()
	out['vbel'] = input_df['VB Energy lower (kWh)'].tolist()

	out["stdout"] = "Success"
	return out


def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		# options for dispatch
		"use_deferral": "off",
		"use_arbitrage": "on",
		"use_regulation": "on",
		"userHourLimit": "8760",
		"energyReserve": "1",
		# VB inputs
		"number_devices": "2000",
		"load_type": "2",
		"power": "5.6",
		"capacitance": "2",
		"resistance": "2",
		"cop": "2.5",
		"setpoint": "22.5",
		"deadband": "0.625",
		"projectionLength":"15",
		"discountRate":"2",
		"unitDeviceCost":"20",
		"unitUpkeepCost":"2",
		# By dispatch
		"payment_structure": "gt", # "ppm"
		# ppm
		"annual_peak_charge": "100",
		"avg_demand_charge": "120",
		"fuel_charge": "0.002",
		# gt
		"electricityCost":"0.041",
		"peakMultiplier": "5",
		"peakPercentile": "0.99",
		"gt_demandCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","fhec_2017_gt.csv")).read(),
		"gt_demandCurveFileName": "fhec_2017_gt.csv",
		
		"tempCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_1yr_Temp.csv")).read(),
		"tempCurveFileName": "Texas_1yr_Temp.csv",
		"inputCsv": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","fhec_knievel_demand_reduction_input.csv")).read(),
		"inputCsvFileName": "fhec_knievel_demand_reduction_input.csv",
		"modelType": modelName,
		## FORECAST ##
		# 'histFileName': 'd_Texas_17yr_TempAndLoad.csv',
		# 'dispatch_type': 'prediction', # 'optimal'
		# 'epochs': '100',
		# 'confidence': '90',
		# "histCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","d_Texas_17yr_TempAndLoad.csv"), 'rU').read(),
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _simpleTest():
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	if os.path.isdir(modelLoc):
		shutil.rmtree(modelLoc)
	new(modelLoc) # Create New.
	renderAndShow(modelLoc) # Pre-run.
	runForeground(modelLoc) # Run the model.
	renderAndShow(modelLoc) # Show the output.

if __name__ == '__main__':
	_simpleTest()

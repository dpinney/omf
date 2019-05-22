
''' Evaluate demand response energy and economic savings available using PNNL VirtualBatteries (VBAT) model. '''

import shutil, csv, pulp, os, math
from os.path import join as pJoin
import pandas as pd
import numpy as np
from datetime import datetime as dt

import __neoMetaModel__
from __neoMetaModel__ import *
from solvers import VB

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Calculate the energy storage capacity for a collection of thermostatically controlled loads."
hidden = True

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


def run_fhec(ind, gt_demand, Input):
	fhec_kwh_rate = float(ind["electricityCost"]) # $/kW
	fhec_peak_mult = float(ind["peakMultiplier"])

	s = sorted(gt_demand)

	# peak hours calculation
	perc = float(ind["peakPercentile"])
	fhec_gt98 = s[int(perc*len(s))]

	fhec_peak_hours = []
	for idx, val in enumerate(gt_demand):
		if  val > fhec_gt98:
			fhec_peak_hours.extend([idx+1])
			
	fhec_off_peak_hours = []
	for i in range(len(gt_demand)):
		if  i not in fhec_peak_hours:
			fhec_off_peak_hours.extend([i+1])

	# read the input data, including load profile, VB profile, and regulation price
	# Input = pd.read_csv(input_csv, index_col=['Hour'])

	# VB model parameters
	C = float(ind["capacitance"]) # thermal capacitance
	R = float(ind["resistance"]) # thermal resistance
	deltaT = 1
	alpha = math.exp(-deltaT/(C*R)) # hourly self discharge rate

	E_0 = 0 # VB initial energy state

	###############################################################################

	# start demand charge reduction LP problem
	model = pulp.LpProblem("Demand charge minimization problem FHEC-Knievel", pulp.LpMinimize)

	# decision variable of VB charging power; dim: 8760 by 1
	VBpower = pulp.LpVariable.dicts("ChargingPower", ((hour) for hour in Input.index))
	# set bound
	for hour in Input.index:
		VBpower[hour].lowBound = Input.loc[hour, "VB Power lower (kW)"]
		VBpower[hour].upBound  = Input.loc[hour, "VB Power upper (kW)"]

	# decision variable of VB energy state; dim: 8760 by 1
	VBenergy = pulp.LpVariable.dicts("EnergyState",((hour) for hour in Input.index))
	# set bound
	for hour in Input.index:
		VBenergy[hour].lowBound = Input.loc[hour, "VB Energy lower (kWh)"]
		VBenergy[hour].upBound  = Input.loc[hour, "VB Energy upper (kWh)"]

	# decision variable of annual peak demand
	PeakDemand = peak = pulp.LpVariable("annual peak demand", lowBound=0)

	# decision variable: hourly regulation up capacity; dim: 8760 by 1
	reg_up = pulp.LpVariable.dicts("hour reg up", ((hour) for hour in Input.index), lowBound=0)
	# decision variable: hourly regulation dn capacity; dim: 8760 by 1
	reg_dn = pulp.LpVariable.dicts("hour reg dn", ((hour) for hour in Input.index), lowBound=0)

	# objective function: sum of monthly demand charge
	model += pulp.lpSum([fhec_peak_mult*fhec_kwh_rate*(Input.loc[hour, "Load (kW)"]+VBpower[hour]) for hour in fhec_peak_hours]
						+ [fhec_kwh_rate*(Input.loc[hour, "Load (kW)"]+VBpower[hour]) for hour in fhec_off_peak_hours]
						+ [Input.loc[hour, "Reg-up Price ($/kWh)"]*reg_up[hour] for hour in Input.index]
						+ [Input.loc[hour, "Reg-dn Price ($/kWh)"]*reg_dn[hour] for hour in Input.index])

	# VB energy state as a function of VB power
	for hour in Input.index:
		if hour==1:
			model += VBenergy[hour] == alpha*E_0 + VBpower[hour]*deltaT
		else:
			model += VBenergy[hour] == alpha*VBenergy[hour-1] + VBpower[hour]*deltaT

	# hourly regulation constraints
	for hour in Input.index:
		model += reg_up[hour] == reg_dn[hour] # regulation balance
		model += VBenergy[hour] - reg_up[hour]*deltaT >= VBenergy[hour].lowBound
		model += VBenergy[hour] + reg_dn[hour]*deltaT <= VBenergy[hour].upBound

	model.solve()

	###############################################################################

	output = []
	for hour in VBpower:
		var_output = {
			'Date/Time': Input.loc[hour, "Date/Time"],
			'Hour': hour,
			'VB energy (kWh)': int(100*VBenergy[hour].varValue)/100,
			'VB power (kW)': int(100*VBpower[hour].varValue)/100,
			'Load (kW)': int(100*Input.loc[hour, "Load (kW)"])/100,
			'Net load (kW)': int(100*(VBpower[hour].varValue+Input.loc[hour, "Load (kW)"]))/100,
			'Regulation (kW)': int(100*reg_up[hour].varValue)/100
		}
		output.append(var_output)
	output_df = pd.DataFrame.from_records(output)
	return output_df

def run_okec(ind, Input):
	okec_peak_charge = float(ind["annual_peak_charge"]) # annual peak demand charge $100/kW
	okec_avg_demand_charge = float(ind["avg_demand_charge"]) # $120/kW
	okec_fuel_charge = float(ind["fuel_charge"]) # total energy $/kWh

	# VB model parameters
	C = float(ind["capacitance"]) # thermal capacitance
	R = float(ind["resistance"]) # thermal resistance
	deltaT = 1
	alpha = math.exp(-deltaT/(C*R)) # hourly self discharge rate

	E_0 = 0 # VB initial energy state

###############################################################################

	# start demand charge reduction LP problem
	model = pulp.LpProblem("Demand charge minimization problem OKEC-Buffett", pulp.LpMinimize)

	# decision variable of VB charging power; dim: 8760 by 1
	VBpower = pulp.LpVariable.dicts("ChargingPower", ((hour) for hour in Input.index))
	# set bound
	for hour in Input.index:
		 VBpower[hour].lowBound = Input.loc[hour, "VB Power lower (kW)"]
		 VBpower[hour].upBound  = Input.loc[hour, "VB Power upper (kW)"]

	# decision variable of VB energy state; dim: 8760 by 1
	VBenergy = pulp.LpVariable.dicts("EnergyState",((hour) for hour in Input.index))
	# set bound
	for hour in Input.index:
		VBenergy[hour].lowBound = Input.loc[hour, "VB Energy lower (kWh)"]
		VBenergy[hour].upBound  = Input.loc[hour, "VB Energy upper (kWh)"]

	# decision variable of annual peak demand
	PeakDemand = peak = pulp.LpVariable("annual peak demand", lowBound=0)

	# decision variable: hourly regulation up capacity; dim: 8760 by 1
	reg_up = pulp.LpVariable.dicts("hour reg up", ((hour) for hour in Input.index), lowBound=0)
	# decision variable: hourly regulation dn capacity; dim: 8760 by 1
	reg_dn = pulp.LpVariable.dicts("hour reg dn", ((hour) for hour in Input.index), lowBound=0)

	# objective function: sum of monthly demand charge
	model += pulp.lpSum(okec_peak_charge*PeakDemand
			+ [okec_avg_demand_charge*(Input.loc[hour, "Load (kW)"]+VBpower[hour])/len(Input.index) for hour in Input.index]
			+ [okec_fuel_charge*(Input.loc[hour, "Load (kW)"]+VBpower[hour])*deltaT for hour in Input.index]
			+ [Input.loc[hour, "Reg-up Price ($/kWh)"]*reg_up[hour] for hour in Input.index]
			+ [Input.loc[hour, "Reg-dn Price ($/kWh)"]*reg_dn[hour] for hour in Input.index])

	# VB energy state as a function of VB power
	for hour in Input.index:
		if hour==1:
			model += VBenergy[hour] == alpha*E_0 + VBpower[hour]*deltaT
		else:
			model += VBenergy[hour] == alpha*VBenergy[hour-1] + VBpower[hour]*deltaT
		
	# hourly regulation constraints
	for hour in Input.index:
		model += PeakDemand >= Input.loc[hour, "Load (kW)"] + VBpower[hour]
		model += reg_up[hour] == reg_dn[hour] # regulation balance
		model += VBenergy[hour] - reg_up[hour]*deltaT >= VBenergy[hour].lowBound
		model += VBenergy[hour] + reg_dn[hour]*deltaT <= VBenergy[hour].upBound

	model.solve()
	
	###############################################################################

	output = []
	for hour in VBpower:
		var_output = {
			'Date/Time': Input.loc[hour, "Date/Time"],
			'Hour': hour,
			'VB energy (kWh)': int(100*VBenergy[hour].varValue)/100,
			'VB power (kW)': int(100*VBpower[hour].varValue)/100,
			'Load (kW)': int(100*Input.loc[hour, "Load (kW)"])/100,
			'Net load (kW)': int(100*(VBpower[hour].varValue+Input.loc[hour, "Load (kW)"]))/100,
			'Regulation (kW)': int(100*reg_up[hour].varValue)/100
		}
		output.append(var_output)
	output_df = pd.DataFrame.from_records(output)
	
	return output_df

def work(modelDir, ind):
	out = {}
	
	try:
		tempCurve = [float(x) for x in ind["tempCurve"].split('\n')]
		gt_demand = [float(x) for x in ind["gt_demandCurve"].split('\n')] if ind["payment_structure"] == "fhec" else []
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
	
	if ind["payment_structure"] == "fhec":
		output_df = run_fhec(ind, gt_demand, input_df)
	else:
		output_df = run_okec(ind, input_df)

	out["show_gt"] = "none" if len(gt_demand) == 0 else "";

	out["gt_demand"] = gt_demand
	out["demand"] = output_df['Load (kW)'].tolist()
	out["VBpower"] = output_df['VB power (kW)'].tolist()
	out["VBenergy"] = output_df['VB energy (kWh)'].tolist()
	out["demandAdjusted"] = output_df['Net load (kW)'].tolist()
	out["stdout"] = "Success"
	return out


def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		# VB inputs
		"number_devices": "2000",
		"load_type": "1",
		"power": "5.6",
		"capacitance": "2",
		"resistance": "2",
		"cop": "2.5",
		"setpoint": "22.5",
		"deadband": "0.625",
		"electricityCost":"0.041",
		"projectionLength":"15",
		"discountRate":"2",
		"unitDeviceCost":"150",
		"unitUpkeepCost":"5",
		# By dispatch
		"payment_structure": "fhec",
		# okec
		"annual_peak_charge": "100",
		"avg_demand_charge": "120",
		"fuel_charge": "0.002",
		# fhec
		"peakMultiplier": "2.5",
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
	_simpleTest ()

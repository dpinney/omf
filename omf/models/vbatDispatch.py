''' Evaluate demand response energy and economic savings available using PNNL VirtualBatteries (VBAT) model. '''

import json, shutil, subprocess, platform, csv, pulp
import os
from os.path import join as pJoin
from sklearn import linear_model
import pandas as pd
import datetime as dt
import numpy as np
from numpy import array, npv, arctan as atan
import __neoMetaModel__
from __neoMetaModel__ import *
from solvers import VB
from omf import loadForecast as fc

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Calculate the energy storage capacity for a collection of thermostatically controlled loads."

def pyVbat(modelDir, i):
	vbType = i['load_type']
	with open(pJoin(modelDir, 'temp.csv')) as f:
		ambient = np.array([float(r[0]) for r in csv.reader(f)])
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

def pulpFunc(inputDict, demand, P_lower, P_upper, E_UL, monthHours):
	### Di's Modified dispatch code	
	alpha = 1-(1/(float(inputDict["capacitance"])*float(inputDict["resistance"])))  #1-(deltaT/(C*R)) hourly self discharge rate
	# LP Variables
	model = pulp.LpProblem("Demand charge minimization problem", pulp.LpMinimize)
	VBpower = pulp.LpVariable.dicts("ChargingPower", range(8760)) # decision variable of VB charging power; dim: 8760 by 1
	VBenergy = pulp.LpVariable.dicts("EnergyState", range(8760)) # decision variable of VB energy state; dim: 8760 by 1
	VBdispatch = pulp.LpVariable.dicts("NumberTimesDispatched", range(8760), lowBound=0) #upBound=1.5)

	for i in range(8760):
		VBpower[i].lowBound = -1*P_lower[i]
		VBpower[i].upBound = P_upper[i]
		VBenergy[i].lowBound = -1*E_UL[i]
		VBenergy[i].upBound = E_UL[i]
	pDemand = pulp.LpVariable.dicts("MonthlyDemand", range(12), lowBound=0)
	
	# Objective function: Minimize sum of peak demands
	model += pulp.lpSum(pDemand) 

	# VB energy state as a function of VB power
	model += VBenergy[0] == VBpower[0]
	for i in range(1, 8760):
		model += VBenergy[i] == alpha * VBenergy[i-1] + VBpower[i]

	for month, (s, f) in zip(range(12), monthHours):
		for i in range(s, f):
			model += pDemand[month] >= demand[i] + VBpower[i]

	model.solve()

	return [VBpower[i].varValue for i in range(8760)], [VBenergy[i].varValue for i in range(8760)]

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	if inputDict['dispatch_type'] == 'prediction':
		return workForecast(modelDir, inputDict)

	out = {}
	try:
		with open(pJoin(modelDir, 'demand.csv'), 'w') as f:
			f.write(inputDict['demandCurve'].replace('\r', ''))
		with open(pJoin(modelDir, 'demand.csv')) as f:
			demand = [float(r[0]) for r in csv.reader(f)]
	 		assert len(demand) == 8760	
		
		with open(pJoin(modelDir, 'temp.csv'), 'w') as f:
			lines = inputDict['tempCurve'].split('\n')
			out["tempData"] = [float(x) if x != '999.0' else float(inputDict['setpoint']) for x in lines[:-1]]
			correctData = [x+'\n' if x != '999.0' else inputDict['setpoint']+'\n' for x in lines][:-1]
			f.write(''.join(correctData))
			assert len(correctData) == 8760
	except:
		raise Exception("CSV file is incorrect format. Please see valid format "
			"definition at <a target='_blank' href = 'https://github.com/dpinney/"
			"omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>\nOMF Wiki "
			"storagePeakShave - Demand File CSV Format</a>")
	
	# # created using calendar = {'1': 31, '2': 28, ..., '12': 31}
	# m = [calendar[key]*24 for key in calendar]
	# monthHours = [(sum(m[:i]), sum(m[:i+1])) for i, _ in enumerate(m)]
	monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
					(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
					(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]

	P_lower, P_upper, E_UL = pyVbat(modelDir, inputDict)
	P_lower, P_upper, E_UL = list(P_lower), list(P_upper), list(E_UL)

	out["minPowerSeries"] = [-1*x for x in P_lower]
	out["maxPowerSeries"] = P_upper
	out["minEnergySeries"] = [-1*x for x in E_UL]
	out["maxEnergySeries"] = E_UL
	
	VBpower, out["VBenergy"] = pulpFunc(inputDict, demand, P_lower, P_upper, E_UL, monthHours)
	out["VBpower"] = VBpower
	out["dispatch_number"] = [len([p for p in VBpower[s:f] if p != 0]) for (s, f) in monthHours]

	peakDemand = [max(demand[s:f]) for s, f in monthHours] 
	energyMonthly = [sum(demand[s:f]) for s, f in monthHours]
	demandAdj = [d+p for d, p in zip(demand, out["VBpower"])]
	peakAdjustedDemand = [max(demandAdj[s:f]) for s, f in monthHours]
	energyAdjustedMonthly = [sum(demandAdj[s:f]) for s, f in monthHours]

	rms = all([x == 0 for x in P_lower]) and all([x == 0 for x in P_upper])
	out["dataCheck"] = 'VBAT returns no values for your inputs' if rms else ''
	out["demand"] = demand
	out["peakDemand"] = peakDemand
	out["energyMonthly"] = energyMonthly
	out["demandAdjusted"] = demandAdj
	out["peakAdjustedDemand"] = peakAdjustedDemand
	out["energyAdjustedMonthly"] = energyAdjustedMonthly
	
	cellCost = float(inputDict["unitDeviceCost"])*float(inputDict["number_devices"])
	eCost = float(inputDict["electricityCost"])
	dCharge = float(inputDict["demandChargeCost"])

	out["VBdispatch"] = [dal-d for dal, d in zip(demandAdj, demand)]
	out["energyCost"] = [em*eCost for em in energyMonthly]
	out["energyCostAdjusted"] = [eam*eCost for eam in energyAdjustedMonthly]
	out["demandCharge"] = [peak*dCharge for peak in peakDemand]
	out["demandChargeAdjusted"] = [pad*dCharge for pad in out["peakAdjustedDemand"]]
	out["totalCost"] = [ec+dcm for ec, dcm in zip(out["energyCost"], out["demandCharge"])]
	out["totalCostAdjusted"] = [eca+dca for eca, dca in zip(out["energyCostAdjusted"], out["demandChargeAdjusted"])]
	out["savings"] = [tot-tota for tot, tota in zip(out["totalCost"], out["totalCostAdjusted"])]

	annualEarnings = sum(out["savings"]) - float(inputDict["unitUpkeepCost"])*float(inputDict["number_devices"])
	cashFlowList = [annualEarnings] * int(inputDict["projectionLength"])
	cashFlowList.insert(0, -1*cellCost)

	out["NPV"] = npv(float(inputDict["discountRate"])/100, cashFlowList)
	out["SPP"] = cellCost / annualEarnings
	out["netCashflow"] = cashFlowList
	out["cumulativeCashflow"] = [sum(cashFlowList[:i+1]) for i, d in enumerate(cashFlowList)]

	out["stdout"] = "Success"
	return out

def vbat24hr(ind, temp):
	vbType = ind['load_type']
	variables = [ind['capacitance'], ind['resistance'], ind['power'], ind['cop'], 
		ind['deadband'], float(ind['setpoint']), ind['number_devices']]
	variables = [float(v) for v in variables]
	variables.insert(0, temp)

	if vbType == '1':
		return [list(i) for i in VB.AC(*variables).generate()] # air conditioning
	elif vbType == '2':
		return [list(i) for i in VB.HP(*variables).generate()] # heat pump
	elif vbType == '3':
		return [list(i) for i in VB.RG(*variables).generate()] # refrigerator
	elif vbType == '4':
		temp = np.array([[i]*60 for i in list(variables[0])]).reshape(365*24*60, 1)
		variables[0] = temp
		variables.append(temp)
		file = pJoin(__neoMetaModel__._omfDir,'static','testFiles',"Flow_raw_1minute_BPA.csv")
		water = np.genfromtxt(file, delimiter=',')
		variables.append(water)
		return [list(i) for i in VB.WH(*variables).generate()] # water heater

def workForecast(modelDir, ind):
	''' Run the model in its directory.'''
	o = {}

	# Grab data from CSV, 
	try:
		with open(pJoin(modelDir, 'hist.csv'), 'w') as f:
			f.write(ind['histCurve'].replace('\r', ''))
		df = pd.read_csv(pJoin(modelDir, 'hist.csv'), parse_dates=['dates'])
		df['month'] = df['dates'].dt.month
		df['dayOfYear'] = df['dates'].dt.dayofyear
		assert df.shape[0] >= 26280 # must be longer than 3 years
		assert df.shape[1] == 5
	except:
		raise Exception("CSV file is incorrect format.")

	# train model on previous data
	all_X = fc.makeUsefulDf(df)
	all_y = df['load']
	X_train, y_train = all_X[:-8760], all_y[:-8760]
	# clf = linear_model.SGDRegressor(max_iter=10000, tol=1e-4)
	# clf.fit(X_train, y_train)

	# ---------------------- MAKE PREDICTIONS ------------------------------- #
	X_test, y_test = all_X[-8760:], all_y[-8760:]
	predictions = fc.neural_net_predictions(all_X, all_y)
	dailyLoadPredictions = [predictions[i:i+24] for i in range(0, len(predictions), 24)]
	
	P_lower, P_upper, E_UL = vbat24hr(ind, df['tempc'][-8760:])
	dailyPl = [P_lower[i:i+24] for i in range(0, len(P_lower), 24)]
	dailyPu = [P_upper[i:i+24] for i in range(0, len(P_upper), 24)]
	dailyEu = [E_UL[i:i+24] for i in range(0, len(E_UL), 24)]
	
	vbp, vbe = [], []
	dispatched_d = [False]*365
	# Decide what days to dispatch
	zipped = zip(dailyLoadPredictions, df['month'][-8760:], dailyPl, dailyPu, dailyEu)
	for i, (load, m, pl, pu, eu) in enumerate(zipped):
		peak = max(load)
		if fc.shouldDispatchPS(peak, m, df, float(ind['confidence'])/100):
			dispatched_d[i] = True
			p, e = fc.pulp24hrVbat(ind, load, pl, pu, eu)
			vbp.extend(p)
			vbe.extend(e)
		else:
			vbp.extend([0]*24)
			vbe.extend([0]*24)

	### TESTING FOR ACCURACY ###
	assert len(dailyPl) == 365
	assert all([len(i) == 24 for i in dailyPl])

	VB_power, VB_energy = vbp, vbe

	# -------------------- MODEL ACCURACY ANALYSIS -------------------------- #

	o['predictedLoad'] = fc.neural_net_predictions(all_X, all_y)
	o['trainAccuracy'] = 0 #round(clf.score(X_train, y_train) * 100, 2)
	o['testAccuracy'] = 0 #round(clf.score(X_test, y_test) * 100, 2)

	# PRECISION AND RECALL
	maxDays = []
	for month in range(1, 13):
		test = df[df['month'] == month]
		maxDays.append(test.loc[test['load'].idxmax()]['dayOfYear'])
	
	shouldHaveDispatched = [False]*365
	for day in maxDays:
		shouldHaveDispatched[day] = True

	truePositive = len([b for b in [i and j for (i, j) in zip(dispatched_d, shouldHaveDispatched)] if b])
	falsePositive = len([b for b in [i and (not j) for (i, j) in zip(dispatched_d, shouldHaveDispatched)] if b])
	falseNegative = len([b for b in [(not i) and j for (i, j) in zip(dispatched_d, shouldHaveDispatched)] if b])
	o['confidence'] = ind['confidence']
	o['precision'] = round(truePositive / float(truePositive + falsePositive) * 100, 2)
	o['recall'] = round(truePositive / float(truePositive + falseNegative) * 100, 2)
	o['number_of_dispatches'] = len([i for i in dispatched_d if i])
	o['MAE'] = round(sum([abs(l-m)/m*100 for l, m in zip(predictions, list(y_test))])/8760., 2)

	# ---------------------- FINANCIAL ANALYSIS ----------------------------- #

	o['VBpower'], o['VBenergy'] = list(VB_power), list(VB_energy)

	# Calculate monthHours
	year = df[-8760:].copy()
	year.reset_index(inplace=True)
	year['hour'] = list(year.index)
	start = list(year.groupby('month').first()['hour'])
	finish = list(year.groupby('month').last()['hour'])
	monthHours = [(s, f+1) for (s, f) in zip(start, finish)]

	demand = list(y_test)
	peakDemand = [max(demand[s:f]) for s, f in monthHours] 
	energyMonthly = [sum(demand[s:f]) for s, f in monthHours]
	demandAdj = [d+p for d, p in zip(demand, o['VBpower'])]
	peakAdjustedDemand = [max(demandAdj[s:f]) for s, f in monthHours]
	energyAdjustedMonthly = [sum(demandAdj[s:f]) for s, f in monthHours]

	o['demand'] = demand
	o['peakDemand'] = peakDemand
	o['energyMonthly'] = energyMonthly
	o['demandAdjusted'] = demandAdj
	o['peakAdjustedDemand'] = peakAdjustedDemand
	o['energyAdjustedMonthly'] = energyAdjustedMonthly
	
	cellCost = float(ind['unitDeviceCost'])*float(ind['number_devices'])
	eCost = float(ind['electricityCost'])
	dCharge = float(ind['demandChargeCost'])

	o['VBdispatch'] = [dal-d for dal, d in zip(demandAdj, demand)]
	o['energyCost'] = [em*eCost for em in energyMonthly]
	o['energyCostAdjusted'] = [eam*eCost for eam in energyAdjustedMonthly]
	o['demandCharge'] = [peak*dCharge for peak in peakDemand]
	o['demandChargeAdjusted'] = [pad*dCharge for pad in o['peakAdjustedDemand']]
	o['totalCost'] = [ec+dcm for ec, dcm in zip(o['energyCost'], o['demandCharge'])]
	o['totalCostAdjusted'] = [eca+dca for eca, dca in zip(o['energyCostAdjusted'], o['demandChargeAdjusted'])]
	o['savings'] = [tot-tota for tot, tota in zip(o['totalCost'], o['totalCostAdjusted'])]

	annualEarnings = sum(o['savings']) - float(ind['unitUpkeepCost'])*float(ind['number_devices'])
	cashFlowList = [annualEarnings] * int(ind['projectionLength'])
	cashFlowList.insert(0, -1*cellCost)

	o['NPV'] = np.npv(float(ind['discountRate'])/100, cashFlowList)
	o['SPP'] = cellCost / annualEarnings
	o['netCashflow'] = cashFlowList
	o['cumulativeCashflow'] = [sum(cashFlowList[:i+1]) for i, d in enumerate(cashFlowList)]
	
	o['stdout'] = 'Success'
	return o

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"load_type": "1",
		"number_devices": "2000",
		"power": "5.6",
		"capacitance": "2",
		"resistance": "2",
		"cop": "2.5",
		"setpoint": "22.5",
		"deadband": "0.625",
		"demandChargeCost":"25",
		"electricityCost":"0.06",
		"projectionLength":"15",
		"discountRate":"2",
		"unitDeviceCost":"150",
		"unitUpkeepCost":"5",
		"demandCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","FrankScadaValidVBAT.csv")).read(),
		"tempCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","weatherNoaaTemp.csv")).read(),
		"fileName": "FrankScadaValidVBAT.csv",
		"tempFileName": "weatherNoaaTemp.csv",
		'histFileName': 'Texas_17yr_TempAndLoad.csv',
		"modelType": modelName,
		## FORECAST ##
		'dispatch_type': 'prediction', # 'optimal'
		'confidence': '90',
		"histCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_17yr_TempAndLoad.csv"), 'rU').read(),
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

"""
def runOctave(modelDir, inputDict):
	plat = platform.system()
	octBin = ('c:\\Octave\\Octave-4.2.1\\bin\\octave-cli' if plat == 'Windows'
				else ('octave --no-gui' if plat == 'Darwin' else 'octave --no-window-system'))
	vbatPath = pJoin(omf.omfDir, 'solvers', 'vbat')
	ARGS = "'{}/temp.csv',{},[{},{},{},{},{},{},{}]".format(
		modelDir, inputDict['load_type'], inputDict['capacitance'], 
		inputDict['resistance'], inputDict['power'], inputDict['cop'],
		inputDict['deadband'], inputDict['setpoint'], inputDict['number_devices'])

	command = '{} --eval "addpath(genpath(\'{}\'));VB_func({})"'.format(octBin, vbatPath, ARGS)
	if plat != 'Windows':
		command = [command]
	mo, _ = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).communicate()

	def parse(key, mo):
		'''some pretty ugly string wrestling'''
		return [float(m) for m in mo.partition(key+' =\n\n')[2].partition('\n\n')[0].split('\n')]
	try:
		return parse('P_lower', mo), parse('P_upper', mo), parse('E_UL', mo)
	except:
		raise Exception('Parsing error, check power data')

def octaveEquivalent(modelDir, inputDict):
	ltype = int(inputDict['load_type'])
	if ltype == 4:
		return runOctave(modelDir, inputDict)

	C = float(inputDict['capacitance'])
	R = float(inputDict['resistance']) 
	P = float(inputDict['power'])
	eta = float(inputDict['cop'])
	delta = float(inputDict['deadband'])
	theta_s = float(inputDict['setpoint'])
	N = float(inputDict['number_devices'])

	with open(pJoin(modelDir, 'temp.csv')) as f:
		theta_a = [float(r[0]) for r in csv.reader(f)]

	theta_a = array(theta_a)

	if ltype in (1, 2, 3):
		# radians or degrees default numpy v octave
		if ltype == 1:
			participation = (atan(theta_a-27) - atan(20-27))/((atan(45-27) - atan(20-27)));
		elif ltype == 2:
			participation = 1-(atan(theta_a-10) - atan(0-10))/((atan(25-10) - atan(0-10)))
		elif ltype == 3:
			participation = [1]*8760

		# converts participation to regular list as well
		participation = [0 if p < 0 else p for p in participation]
		participation = [1 if p > 1 else p for p in participation]

		if ltype in (1, 3):
			P_value = (theta_a - theta_s)/R/eta
		elif ltype == 2:
			P_value = (theta_s - theta_a)/R/eta

		# P_value now also just a regular list
		P_value = [0 if p < 0 else p for p in P_value]

		P_lower = [N*part*d for part, d in zip(participation, P_value)]
		P_upper = [N*part*(P - d) for part, d in zip(participation, P_value)]
		P_upper = [0 if p < 0 else p for p in P_upper]
		E_UL = [N*part*C*delta/2/eta for part in participation]


	#temperature_a = read(csv) sans header
	# if device_type == 3:
	# temperature_a = 20*ones(8760, 1)

	# if case 4 transpose the variables

	return P_lower, P_upper, E_UL

def carpetPlot(tempData):
	#tempData is a 8760 list that contains the temperature data to be displayed in a carpet plot
	#takes about one minute to run
	calendar = collections.OrderedDict()
	calendar['0'] = 31
	calendar['1'] = 28
	calendar['2'] = 31
	calendar['3'] = 30
	calendar['4'] = 31
	calendar['5'] = 30
	calendar['6'] = 31
	calendar['7'] = 31
	calendar['8'] = 30
	calendar['9'] = 31
	calendar['10'] = 30
	calendar['11'] = 31
	f, axarr = plt.subplots(12, 31, sharex=True, sharey=True)
	f.suptitle('Carpet Plot of VBAT energy potential')
	f.text(0.5, 0.05, 'Days', ha='center', va='center')
	f.text(0.04, 0.5, 'Months', ha='center', va='center', rotation='vertical')
	f.text(0.095,0.86, 'Jan', ha='center', va='center')
	f.text(0.095,0.79, 'Feb', ha='center', va='center')
	f.text(0.095,0.72, 'Mar', ha='center', va='center')
	f.text(0.095,0.66, 'Apr', ha='center', va='center')
	f.text(0.095,0.59, 'May', ha='center', va='center')
	f.text(0.095,0.525, 'Jun', ha='center', va='center')
	f.text(0.095,0.47, 'Jul', ha='center', va='center')
	f.text(0.095,0.40, 'Aug', ha='center', va='center')
	f.text(0.095,0.335, 'Sep', ha='center', va='center')
	f.text(0.095,0.265, 'Oct', ha='center', va='center')
	f.text(0.095,0.195, 'Nov', ha='center', va='center')
	f.text(0.095,0.135, 'Dec', ha='center', va='center')
	dayNum = -24
	for month in calendar:
		for day in range(calendar[month]):
			dayNum += 24
			dayValues = []
			for z in range(24):
				dayValues.append(tempData[dayNum + z])
			axarr[int(month),day].plot(dayValues)
			axarr[int(month),day].axis('off')
	axarr[1,28].plot(0,0)
	axarr[1,29].plot(0,0)
	axarr[1,30].plot(0,0)
	axarr[3,30].plot(0,0)
	axarr[5,30].plot(0,0)
	axarr[8,30].plot(0,0)
	axarr[10,30].plot(0,0)
	axarr[1,28].axis('off')
	axarr[1,29].axis('off')
	axarr[1,30].axis('off')
	axarr[3,30].axis('off')
	axarr[5,30].axis('off')
	axarr[8,30].axis('off')
	axarr[10,30].axis('off')
	plt.savefig('vbatDispatchCarpetPlot.png')
"""
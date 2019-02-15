''' Apply PNNL VirtualBatteries (VBAT) load model to day ahead forecast.'''
import pandas as pd
import numpy as np
from sklearn import linear_model
import pulp
from os.path import isdir, join as pJoin
import __neoMetaModel__
from __neoMetaModel__ import *
from omf import loadForecast as fc

# Model metadata:
modelName, template = metadata(__file__)
tooltip = ('Calculate the virtual battery capacity for a collection of '
	'thermostically controlled loads with day-ahead forecasting.')
hidden = True

def shouldDispatch(peak, month, df, conf, goal, deferral):
	if goal != 'deferral':
		return peak > df[:-8760].groupby('month')['load'].quantile(conf)[month]
	else:
		return peak > deferral*conf

def pulp24hr(demand, power, energy, battEff):
	# LP Variables
	model = pulp.LpProblem('Daily demand charge minimization problem', pulp.LpMinimize)
	VBpower = pulp.LpVariable.dicts('ChargingPower', range(24)) # decision variable of VB charging power; dim: 8760 by 1
	VBenergy = pulp.LpVariable.dicts('EnergyState', range(24)) # decision variable of VB energy state; dim: 8760 by 1
	
	for i in range(24):
		VBpower[i].lowBound = -power
		VBpower[i].upBound = power
		VBenergy[i].lowBound = 0
		VBenergy[i].upBound = energy
	pDemand = pulp.LpVariable('Peak Demand', lowBound=0)
	
	# Objective function: Minimize peak demand
	model += pDemand

	# VB energy state as a function of VB power
	model += VBenergy[0] == 0
	for i in range(1, 24):
		model += VBenergy[i] == battEff * VBenergy[i-1] + VBpower[i]
	for i in range(24):
		model += pDemand >= demand[i] + VBpower[i]
	model.solve()
	return [VBpower[i].varValue for i in range(24)], [VBenergy[i].varValue for i in range(24)]

def work(modelDir, ind):
	#print(ind)
	''' Run the model in its directory.'''
	# drop inverter efficiency
	# drop DoD
	(cellCapacity, dischargeRate, chargeRate, cellQuantity, cellCost) = \
		[float(ind[x]) for x in ('cellCapacity', 'dischargeRate', 'chargeRate', 'cellQuantity', 'cellCost')]
	battEff	= float(ind.get("batteryEfficiency")) / 100.0
	dodFactor = float(ind.get('dodFactor')) / 100.0
	projYears = int(ind.get('projectionLength'))
	batteryCycleLife = int(ind.get('batteryCycleLife'))

	o = {}

	try:
		with open(pJoin(modelDir, 'hist.csv'), 'w') as f:
			f.write(ind['historicalData'])#.replace('\r', ''))
		df = pd.read_csv(pJoin(modelDir, 'hist.csv'), parse_dates=['dates'])
		df['month'] = df['dates'].dt.month
		df['dayOfYear'] = df['dates'].dt.dayofyear
		assert df.shape[0] >= 26280 # must be longer than 3 years
		assert df.shape[1] == 5
	except ZeroDivisionError:
		raise Exception("CSV file is incorrect format.")

	# retrieve goal
	goal = ind['goal']
	threshold = float(ind['transformerThreshold'])*1000
	confidence = float(ind['confidence'])/100

	# train model on previous data
	all_X = fc.makeUsefulDf(df)
	all_y = df['load']
	X_train, y_train = all_X[:-8760], all_y[:-8760]
	clf = linear_model.SGDRegressor(max_iter=10000, tol=1e-4)
	clf.fit(X_train, y_train)

	# ---------------------- MAKE PREDICTIONS ------------------------------- #
	X_test, y_test = all_X[-8760:], all_y[-8760:]

	# Collect data necessary for dispatch calculations
	predictions = clf.predict(X_test)
	dailyLoadPredictions = [predictions[i:i+24] for i in range(0, len(predictions), 24)]	
	weather = df['tempc'][-8760:]
	dailyWeatherPredictions = [weather[i:i+24] for i in range(0, len(weather), 24)]
	month = df['month'][-8760:]

	dispatched = [False]*365
	# decide to implement VBAT every day for a year
	VB_power, VB_energy = [], []
	for i, (load24, temp24, m) in enumerate(zip(dailyLoadPredictions, dailyWeatherPredictions, month)):
		peak = max(load24)
		if fc.shouldDispatchDeferral(peak, df, confidence, threshold):
			dispatched[i] = True
			vbp, vbe = fc.pulp24hrBattery(load24, dischargeRate*cellQuantity, 
				cellCapacity*cellQuantity, battEff)
			VB_power.extend(vbp)
			VB_energy.extend(vbe)
		else:
			VB_power.extend([0]*24)
			VB_energy.extend([0]*24)

	# -------------------- MODEL ACCURACY ANALYSIS -------------------------- #

	o['predictedLoad'] = list(clf.predict(X_test))
	o['trainAccuracy'] = round(clf.score(X_train, y_train) * 100, 2)
	o['testAccuracy'] = round(clf.score(X_test, y_test) * 100, 2)

	# PRECISION AND RECALL
	maxDays = []
	for month in range(1, 13):
		test = df[df['month'] == month]
		maxDays.append(test.loc[test['load'].idxmax()]['dayOfYear'])
	
	shouldHaveDispatched = [False]*365
	for day in maxDays:
		shouldHaveDispatched[day] = True

	truePositive = len([b for b in [i and j for (i, j) in zip(dispatched, shouldHaveDispatched)] if b])
	falsePositive = len([b for b in [i and (not j) for (i, j) in zip(dispatched, shouldHaveDispatched)] if b])
	falseNegative = len([b for b in [(not i) and j for (i, j) in zip(dispatched, shouldHaveDispatched)] if b])
	o['precision'] = round(truePositive / float(truePositive + falsePositive) * 100, 2)
	o['recall'] = round(truePositive / float(truePositive + falseNegative) * 100, 2)
	o['number_of_dispatches'] = len([i for i in dispatched if i])
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
	
	initInvestment = cellCost*cellQuantity
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

	annualEarnings = sum(o['savings']) # - something!
	cashFlowList = [annualEarnings] * int(ind['projectionLength'])
	cashFlowList.insert(0, -1*initInvestment)

	o['NPV'] = np.npv(float(ind['discountRate'])/100, cashFlowList)
	o['SPP'] = initInvestment / annualEarnings
	o['netCashflow'] = cashFlowList
	o['cumulativeCashflow'] = [sum(cashFlowList[:i+1]) for i, d in enumerate(cashFlowList)]

	o['dataCheck'] = 'Threshold exceeded' if any([threshold > i for i in demandAdj]) and goal == 'deferral' else ''
	o['transformerThreshold'] = threshold if goal == 'deferral' else None

	o['stdout'] = 'Success'
	return o

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"user": "admin",
		"goal": "deferral",
		"confidence": "80",
		"demandChargeCost":"25",
		"electricityCost":"0.06",
		"projectionLength":"15",
		"discountRate":"2",
		"historicalData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_17yr_TempAndLoad.csv"), 'rU').read(),
		"filename": "Texas_17yr_TempAndLoad.csv",
		"transformerThreshold": "20",
		"batteryEfficiency": "92",
		"inverterEfficiency": "97.5",
		"cellCapacity": "7",
		"dischargeRate": "5",
		"chargeRate": "5",
		"cellCost": "7140",
		"cellQuantity": "25",
		"projYears": "15",
		"chargePriceThreshold": "0.07",
		"dischargePriceThreshold":"0.15",
		"dodFactor":"100",
		"batteryCycleLife": "5000"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

def _tests():
	modelLoc = pJoin(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
	if isdir(modelLoc):
		shutil.rmtree(modelLoc)
	new(modelLoc) # Create New.
	renderAndShow(modelLoc) # Pre-run.
	runForeground(modelLoc) # Run the model.	
	renderAndShow(modelLoc) # Show the output.

if __name__ == '__main__':
	_tests()

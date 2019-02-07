''' Apply PNNL VirtualBatteries (VBAT) load model to day ahead forecast.'''
import pandas as pd
import numpy as np
from sklearn import linear_model
import pulp
from os.path import isdir, join as pJoin
import __neoMetaModel__
from __neoMetaModel__ import *
from solvers import VB 
import forecast as fc

# Model metadata:
modelName, template = metadata(__file__)
tooltip = ('Calculate the virtual battery capacity for a collection of '
	'thermostically controlled loads with day-ahead forecasting.')
hidden = True

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

def work(modelDir, ind):
	''' Run the model in its directory.'''
	o = {}

	# Grab data from CSV, 
	try:
		with open(pJoin(modelDir, 'hist.csv'), 'w') as f:
			f.write(ind['historicalData'].replace('\r', ''))
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
	clf = linear_model.SGDRegressor(max_iter=10000, tol=1e-4)
	clf.fit(X_train, y_train)

	# ---------------------- MAKE PREDICTIONS ------------------------------- #
	X_test, y_test = all_X[-8760:], all_y[-8760:]
	predictions = clf.predict(X_test)
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
		"confidence": "95",
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
		"historicalData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_17yr_TempAndLoad.csv")).read(),
		"filename": "Texas_17yr_TempAndLoad.csv",
		"modelType": modelName
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

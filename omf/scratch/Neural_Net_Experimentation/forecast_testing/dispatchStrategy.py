''' Apply PNNL VirtualBatteries (VBAT) load model to day ahead forecast.'''
import pandas as pd
import numpy as np
from sklearn import linear_model
import pulp
from os.path import isdir, join as pJoin
import __neoMetaModel__
from __neoMetaModel__ import *
from solvers import VB
import VB

# Model metadata:
modelName, template = metadata(__file__)
tooltip = ('Calculate the virtual battery capacity for a collection of '
	'thermostically controlled loads with day-ahead forecasting.')
hidden = True

def makeUsefulDf(df):
	def _normalizeCol(l):
		s = l.max() - l.min()
		return l if s == 0 else (l - l.mean()) / s

	def _chunks(l, n):
		return [l[i:i+n] for i in range(0, len(l), n)]

	r_df = pd.DataFrame()
	r_df['load_n'] = _normalizeCol(df['load'])
	r_df['years_n'] = _normalizeCol(df['dates'].dt.year - 2000)
	
	# fix outliers
	m = df['tempc'].replace([-9999], np.nan)
	m.ffill(inplace=True)
	r_df['temp_n'] = _normalizeCol(m)

	# add the value of the load 24hrs before
	r_df['load_prev_n'] = r_df['load_n'].shift(24)
	r_df['load_prev_n'].bfill(inplace=True)

	# create day of week vector
	r_df['day'] = df['dates'].dt.dayofweek # 0 is Monday.
	w = ['S', 'M', 'T', 'W', 'R', 'F', 'A']
	for i, d in enumerate(w):
		r_df[d] = (r_df['day'] == i).astype(int)
	
	# create hour of day vector
	r_df['hour'] = df['dates'].dt.hour
	d = [('h' + str(i)) for i in range(24)]
	for i, h in enumerate(d):
		r_df[h] = (r_df['hour'] == i).astype(int)
	
	# create month vector
	r_df['month'] = df['dates'].dt.month
	y = [('m' + str(i)) for i in range(12)]
	for i, m in enumerate(y):
	    r_df[m] = (r_df['month'] == i).astype(int)

	# create 'load day before' vector
	n = np.array([val for val in _chunks(list(r_df['load_n']), 24) for _ in range(24)])
	l = ['l' + str(i) for i in range(24)]
	for i, s in enumerate(l):
	    r_df[s] = n[:, i]

	m = r_df.drop(['month', 'hour', 'day', 'load_n'], axis=1)
	return m

def vbat24hr(ind, temp24):
	vbType = ind['load_type']
	variables = [ind['capacitance'], ind['resistance'], ind['power'], ind['cop'], 
		ind['deadband'], float(ind['setpoint']), ind['number_devices']]
	variables = [float(v) for v in variables]

	ambient = temp24
	variables.insert(0, ambient)

	if vbType == '1':
		return [list(i) for i in VB.AC(*variables).generate()] # air conditioning
	elif vbType == '2':
		return [list(i) for i in VB.HP(*variables).generate()] # heat pump
	elif vbType == '3':
		return [list(i) for i in VB.RG(*variables).generate()] # refrigerator

def shouldDispatch(peak, month, df, alpha=.99):
	return peak > df.groupby('month')['load'].quantile(alpha)[month]

def pulp24hr(ind, demand, P_lower, P_upper, E_UL):
	### Di's Modified dispatch code	
	alpha = 1-(1/(float(ind['capacitance'])*float(ind['resistance'])))  #1-(deltaT/(C*R)) hourly self discharge rate
	# LP Variables
	model = pulp.LpProblem('Daily demand charge minimization problem', pulp.LpMinimize)
	VBpower = pulp.LpVariable.dicts('ChargingPower', range(24)) # decision variable of VB charging power; dim: 8760 by 1
	VBenergy = pulp.LpVariable.dicts('EnergyState', range(24)) # decision variable of VB energy state; dim: 8760 by 1
	VBdispatch = pulp.LpVariable.dicts('NumberTimesDispatched', range(24), lowBound=0) #upBound=1.5)

	for i in range(24):
		VBpower[i].lowBound = -1*P_lower[i]
		VBpower[i].upBound = P_upper[i]
		VBenergy[i].lowBound = -1*E_UL[i]
		VBenergy[i].upBound = E_UL[i]
	pDemand = pulp.LpVariable('Peak Demand', lowBound=0)
	
	# Objective function: Minimize sum of peak demands
	model += pDemand

	# VB energy state as a function of VB power
	model += VBenergy[0] == VBpower[0]
	for i in range(1, 24):
		model += VBenergy[i] == alpha * VBenergy[i-1] + VBpower[i]

	for i in range(24):
		model += pDemand >= demand[i] + VBpower[i]

	model.solve()

	return [VBpower[i].varValue for i in range(24)], [VBenergy[i].varValue for i in range(24)]

def work(modelDir, ind):
	''' Run the model in its directory.'''
	o = {}

	# collect data, put into useful format, split into test
	b_df = pd.read_csv('sampleInput.csv', parse_dates=['dates'])
	b_df['month'] = b_df['dates'].dt.month
	df = makeUsefulDf(b_df)

	# train model on previous data
	all_X = df
	all_y = b_df['load']
	X_train, y_train = all_X[:-8760], all_y[:-8760]
	clf = linear_model.SGDRegressor(max_iter=10000, tol=1e-4)
	clf.fit(X_train, y_train)

	# ---------------------- MAKE PREDICTIONS ------------------------------- #
	monthHours = [(0, 744), (744, 1416), (1416, 2160), (2160, 2880), 
				(2880, 3624), (3624, 4344), (4344, 5088), (5088, 5832), 
				(5832, 6552), (6552, 7296), (7296, 8016), (8016, 8760)]

	l = [[i+1]*((f-s)/24) for i, (s, f) in enumerate(monthHours)]
	month = [i for s in l for i in s]

	X_test, y_test = all_X[-8760:], all_y[-8760:]
	weather = b_df['tempc'][-8760:] 
	predictions = clf.predict(X_test)

	VB_power, VB_energy = [], []

	dailyLoadPredictions = [predictions[i:i+24] for i in range(0, len(predictions), 24)]
	dailyWeatherPredictions = [weather[i:i+24] for i in range(0, len(weather), 24)]

	for i, (load24, temp24, m) in enumerate(zip(dailyLoadPredictions, dailyWeatherPredictions, month)):
		peak = max(load24)
		if shouldDispatch(peak, m, b_df):
			P_lower, P_upper, E_UL = vbat24hr(ind, temp24)
			vbp, vbe = pulp24hr(ind, load24, P_lower, P_upper, E_UL)
			VB_power.extend(vbp)
			VB_energy.extend(vbe)
		else:
			VB_power.extend([0]*24)
			VB_energy.extend([0]*24)

	print len(VB_power), len(VB_energy)
	o['predicted_load'] = clf.predict(X_test)
	o['train accuracy'] = clf.score(X_train, y_train)
	o['test accuracy'] = clf.score(X_test, y_test)

	# ---------------------- FINANCIAL ANALYSIS ----------------------------- #

	o['VBpower'], o['VBenergy'] = VB_power, VB_energy

	demand = y_test
	peakDemand = [max(demand[s:f]) for s, f in monthHours] 
	energyMonthly = [sum(demand[s:f]) for s, f in monthHours]
	demandAdj = [d+p for d, p in zip(demand, o['VBpower'])]
	peakAdjustedDemand = [max(demandAdj[s:f]) for s, f in monthHours]
	energyAdjustedMonthly = [sum(demandAdj[s:f]) for s, f in monthHours]

	rms = all([x == 0 for x in P_lower]) and all([x == 0 for x in P_upper])
	o['dataCheck'] = 'VBAT returns no values for your inputs' if rms else ''
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
	ind = {
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
		#"demandCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","FrankScadaValidVBAT.csv")).read(),
		#"tempCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","weatherNoaaTemp.csv")).read(),
		#"fileName": "FrankScadaValidVBAT.csv",
		#"tempFileName": "weatherNoaaTemp.csv",
		#"modelType": modelName
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

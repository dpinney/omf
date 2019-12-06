''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import os, sys, shutil, csv
from datetime import datetime as dt, timedelta
import pulp
from os.path import isdir, join as pJoin
from numpy import npv
import pandas as pd

from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf import forecast as fc

# Model metadata:
modelName, template = metadata(__file__)
tooltip = ("The storagePeakShave model calculates the value of a distribution utility " 
	"deploying energy storage based on three possible battery dispatch strategies.")

def heat(l, alpha=.10):
	r = []
	for i, x in enumerate(l):
		if i == 0:
			diff = (0 - l[i]) - (l[i] - l[i+1])
			r.append(l[i] + alpha*diff)
		elif i == len(l) - 1:
			diff = (l[i-1] - l[i]) - (l[i] - 0)
			r.append(l[i] + alpha*diff)
		else:
			diff = (l[i-1] - l[i]) - (l[i] - l[i+1])
			r.append(l[i] + alpha*diff)
	
	sum_r = sum(r)
	sum_l = sum(l)
	if sum_l != sum_r:
		p = []
		prop = sum_l / sum_r
		return [round(prop*x, 4) for x in r]
	else:
		return r

def pulp24hrBattery(day_load, RATING, CAPACITY, battEff):
	model = pulp.LpProblem("Daily demand charge minimization problem", pulp.LpMinimize)
	power = pulp.LpVariable.dicts("ChargingPower", range(24))
	energy = pulp.LpVariable.dicts("EnergyState", range(24))

	for i in range(24):
		power[i].lowBound = -RATING
		power[i].upBound = 0
		energy[i].lowBound = 0
		energy[i].upBound = CAPACITY
	pDemand = pulp.LpVariable("Peak Demand", lowBound=0)

	# Objective function: Minimize peak demand
	model += pDemand

	# VB energy state as a function of VB power
	model += energy[0] == CAPACITY
	for i in range(1, 24):
		model += energy[i] == energy[i - 1] + power[i]
	for i in range(24):
		model += pDemand >= day_load[i] + power[i]
	model.solve()

	return (
		# heat([power[i].varValue for i in range(24)]),
		[power[i].varValue for i in range(24)],
		[energy[i].varValue for i in range(24)]
	)

def work(modelDir, inputDict):
	''' Model processing done here. '''
	dispatchStrategy = str(inputDict.get('dispatchStrategy'))
	if dispatchStrategy == 'prediction':
		return forecastWork(modelDir, inputDict)

	out = {}  # See bottom of file for out's structure
	cellCapacity, dischargeRate, chargeRate, cellQuantity, demandCharge, cellCost, retailCost = \
		[float(inputDict[x]) for x in ('cellCapacity', 'dischargeRate', 'chargeRate',
			'cellQuantity', 'demandCharge', 'cellCost', 'retailCost')]

	projYears, batteryCycleLife = [int(inputDict[x]) for x in ('projYears', 'batteryCycleLife')]
	
	discountRate = float(inputDict.get('discountRate')) / 100.0
	dodFactor = float(inputDict.get('dodFactor')) / 100.0

	# Efficiency calculation temporarily removed
	inverterEfficiency = float(inputDict.get('inverterEfficiency')) / 100.0
	# Note: inverterEfficiency is squared to get round trip efficiency.
	battEff = float(inputDict.get('batteryEfficiency')) / 100.0 * (inverterEfficiency ** 2)

	with open(pJoin(modelDir, 'demand.csv'), 'w') as f:
		f.write(inputDict['demandCurve'])
	if dispatchStrategy == 'customDispatch':
		with open(pJoin(modelDir, 'dispatchStrategy.csv'), 'w') as f:
			f.write(inputDict['customDispatchStrategy'])

	dc = [] # main data table
	try:
		dates = [(dt(2011, 1, 1) + timedelta(hours=1)*x) for x in range(8760)]
		with open(pJoin(modelDir, 'demand.csv')) as f:
			reader = csv.reader(f)
			for row, date in zip(reader, dates):
				dc.append({	'power': float(row[0]), # row is a list of length 1
							'month': date.month - 1,
							'hour': date.hour })
		assert len(dc) == 8760
	except:
		if str(sys.exc_info()[0]) != "<type 'exceptions.SystemExit'>":
			raise Exception("CSV file is incorrect format. Please see valid "
				"format definition at <a target='_blank' href = 'https://github.com/"
				"dpinney/omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>"
				"\nOMF Wiki storagePeakShave - Demand File CSV Format</a>")

	# list of 12 lists of monthly demands
	demandByMonth = [[t['power'] for t in dc if t['month']==x] for x in range(12)]
	monthlyPeakDemand = [max(lDemands) for lDemands in demandByMonth]
	battCapacity = cellQuantity * cellCapacity * dodFactor
	battDischarge = cellQuantity * dischargeRate
	battCharge = cellQuantity * chargeRate

	SoC = battCapacity 
	if dispatchStrategy == 'optimal':
		ps = [battDischarge] * 12
		# keep shrinking peak shave (ps) until every month doesn't fully expend the battery
		while True:
			SoC = battCapacity
			incorrect_shave = [False] * 12
			for row in dc:
				month = row['month']
				if not incorrect_shave[month]:
					powerUnderPeak = monthlyPeakDemand[month] - row['power'] - ps[month]
					charge = (min(powerUnderPeak, battCharge, battCapacity - SoC) if powerUnderPeak > 0
						else -1 * min(abs(powerUnderPeak), battDischarge, SoC))
					if charge == -1 * SoC:
						incorrect_shave[month] = True
					SoC += charge
					row['netpower'] = row['power'] + charge
					row['battSoC'] = SoC
			ps = [s-1 if incorrect else s for s, incorrect in zip(ps, incorrect_shave)]
			if not any(incorrect_shave):
				break
	elif dispatchStrategy == 'daily':
		start = int(inputDict.get('startPeakHour'))
		end = int(inputDict.get('endPeakHour'))
		for r in dc:
			# Discharge if hour is within peak hours otherwise charge
			charge = (-1*min(battDischarge, SoC) if start <= r['hour'] <= end 
				else min(battCharge, battCapacity - SoC))
			r['netpower'] = r['power'] + charge
			SoC += charge
			r['battSoC'] = SoC
	elif dispatchStrategy == 'customDispatch':
		try:
			with open(pJoin(modelDir,'dispatchStrategy.csv')) as f:
				reader = csv.reader(f)
				for d, r in zip(dc, reader):
					d['dispatch'] = int(r[0])
				assert all(['dispatch' in r for r in dc])  # ensure each row is filled
		except:
			if str(sys.exc_info()[0]) != "<type 'exceptions.SystemExit'>":
				raise Exception("Dispatch Strategy file is in an incorrect " 
					"format. Please see valid format definition at <a target "
					"= '_blank' href = 'https://github.com/dpinney/omf/wiki/"
					"Models-~-storagePeakShave#custom-dispatch-strategy-file-"
					"csv-format'>\nOMF Wiki storagePeakShave - Custom "
					"Dispatch Strategy File Format</a>")
		for r in dc:
			# Discharge if there is a 1 in the dispatch strategy csv, otherwise charge the battery.
			charge = (-1*min(battDischarge, SoC) if r['dispatch'] == 1 
				else min(battCharge, battCapacity-SoC))
			r['netpower'] = r['power'] + charge
			SoC += charge
			r['battSoC'] = SoC

	# ------------------------- CALCULATIONS ------------------------- #
	netByMonth = [[t['netpower'] for t in dc if t['month']==x] for x in range(12)]
	monthlyPeakNet = [max(net) for net in netByMonth]
	ps = [h-s for h, s in zip(monthlyPeakDemand, monthlyPeakNet)]
	dischargeByMonth = [[i-j for i, j in zip(k, l) if i-j < 0] for k, l in zip(netByMonth, demandByMonth)]

	# Monthly Cost Comparison Table
	out['monthlyDemand'] = [sum(lDemand)/1000 for lDemand in demandByMonth]
	out['monthlyDemandRed'] = [t-p for t, p in zip(out['monthlyDemand'], ps)]
	out['ps'] = ps
	out['benefitMonthly'] = [x*demandCharge for x in ps]
	
	# Demand Before and After Storage Graph
	out['demand'] = [t['power']*1000.0 for t in dc] # kW -> W
	out['demandAfterBattery'] = [t['netpower']*1000.0 for t in dc] # kW -> W
	out['batteryDischargekW'] = [d-b for d, b in zip(out['demand'], out['demandAfterBattery'])]
	out['batteryDischargekWMax'] = max(out['batteryDischargekW'])

	with open(pJoin(modelDir, 'batteryDispatch.txt'), 'w') as f:
		f.write('\n'.join([str(x) for x in out['batteryDischargekW']]) + '\n')

	# Battery State of Charge Graph
	out['batterySoc'] = SoC = [t['battSoC']/battCapacity*100*dodFactor + (100-100*dodFactor) for t in dc]
	# Estimate number of cyles the battery went through. Sums the percent of SoC.
	cycleEquivalents = sum([SoC[i]-SoC[i+1] for i, x in enumerate(SoC[:-1]) if SoC[i+1] < SoC[i]]) / 100.0
	out['cycleEquivalents'] = cycleEquivalents
	out['batteryLife'] = batteryCycleLife / cycleEquivalents

	# Cash Flow Graph
	cashFlowCurve = [sum(ps)*demandCharge for year in range(projYears)]
	cashFlowCurve.insert(0, -1 * cellCost * cellQuantity)  # insert initial investment
	# simplePayback is also affected by the cost to recharge the battery every day of the year
	out['SPP'] = (cellCost*cellQuantity)/(sum(ps)*demandCharge)
	out['netCashflow'] = cashFlowCurve
	out['cumulativeCashflow'] = [sum(cashFlowCurve[:i+1]) for i, d in enumerate(cashFlowCurve)]
	out['NPV'] = npv(discountRate, cashFlowCurve)

	battCostPerCycle = cellQuantity * cellCost / batteryCycleLife
	lcoeTotCost = cycleEquivalents*retailCost + battCostPerCycle*cycleEquivalents
	out['LCOE'] = lcoeTotCost / (cycleEquivalents*battCapacity)

	# Other
	out['startDate'] = '2011-01-01'  # dc[0]['datetime'].isoformat()
	out['stderr'] = ''
	# Seemingly unimportant. Ask permission to delete.
	out['stdout'] = 'Success' 
	out['months'] = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

	return out

def forecastWork(modelDir, ind):
	import tensorflow as tf

	''' Run the model in its directory.'''
	(cellCapacity, dischargeRate, chargeRate, cellQuantity, cellCost) = \
		[float(ind[x]) for x in ('cellCapacity', 'dischargeRate', 'chargeRate', 'cellQuantity', 'cellCost')]
	demandCharge = float(ind['demandCharge'])
	retailCost = float(ind['retailCost'])

	battEff	= float(ind.get("batteryEfficiency")) / 100.0
	dodFactor = float(ind.get('dodFactor')) / 100.0
	projYears = int(ind.get('projYears'))
	batteryCycleLife = int(ind.get('batteryCycleLife'))
	battCapacity = cellQuantity * float(ind['cellCapacity']) * dodFactor

	o = {}

	try:
		with open(pJoin(modelDir, 'hist.csv'), 'w') as f:
			f.write(ind['histCurve'].replace('\r', ''))
		df = pd.read_csv(pJoin(modelDir, 'hist.csv'))
		assert df.shape[0] >= 26280 # must be longer than 3 years
		if df.shape[1] == 6:
			df['dates'] = df.apply(
				lambda x: dt(
					int(x['year']), 
					int(x['month']), 
					int(x['day']), 
					int(x['hour'])), 
				axis=1
			)
		else:
			df = pd.read_csv(pJoin(modelDir, 'hist.csv'), parse_dates=['dates'])
			df['month'] = df.dates.dt.month
		df['dayOfYear'] = df['dates'].dt.dayofyear
	except:
		raise Exception("CSV file is incorrect format.")

	# ---------------------- MAKE PREDICTIONS ------------------------------- #
	# train model on previous data
	all_X = fc.makeUsefulDf(df)
	all_y = df['load']
	if ind['newModel'] == 'True':
		model = None 
	else:
		with open(pJoin(modelDir, 'neural_net.h5'), 'wb') as f:
			f.write(ind['model'].decode('base64'))
		model = tf.keras.models.load_model(pJoin(modelDir, 'neural_net.h5'))
		# model = tf.keras.models.load_model(ind['model'])
	predictions, accuracy = fc.neural_net_predictions(all_X, all_y, epochs=int(ind['epochs']), model=model, 
		save_file=pJoin(modelDir, 'neural_net_model.h5'))

	dailyLoadPredictions = [predictions[i:i+24] for i in range(0, len(predictions), 24)]	
	weather = df['tempc'][-8760:]
	dailyWeatherPredictions = [weather[i:i+24] for i in range(0, len(weather), 24)]

	# decide to implement VBAT every day for a year
	VB_power, VB_energy = [], []
	for i, (load24, temp24) in enumerate(zip(dailyLoadPredictions, dailyWeatherPredictions)):
		vbp, vbe = pulp24hrBattery(load24, dischargeRate*cellQuantity, 
			cellCapacity*cellQuantity, battEff)
		VB_power.extend(vbp)
		VB_energy.extend(vbe)
	
	# -------------------- MODEL ACCURACY ANALYSIS -------------------------- #
	o['predictedLoad'] = predictions
	o['trainAccuracy'] = 100 - round(accuracy['train'], 1)
	o['testAccuracy'] = 100 - round(accuracy['test'], 1)
	# ---------------------- FINANCIAL ANALYSIS ----------------------------- #

	# Calculate monthHours
	year = df[-8760:].copy()
	year.reset_index(inplace=True)
	year['hour'] = list(year.index)
	start = list(year.groupby('month').first()['hour'])
	finish = list(year.groupby('month').last()['hour'])
	monthHours = [(s, f+1) for (s, f) in zip(start, finish)]

	demand = list(df['load'][-8760:])
	peakDemand = [max(demand[s:f]) for s, f in monthHours] 
	demandAdj = [d+p for d, p in zip(demand, VB_power)]
	peakDemandAdj = [max(demandAdj[s:f]) for s, f in monthHours]

	# Monthly Cost Comparison Table
	o['monthlyDemand'] = peakDemand
	o['monthlyDemandRed'] = peakDemandAdj
	o['ps'] = [p-s for p, s in zip(peakDemand, peakDemandAdj)]
	o['benefitMonthly'] = [x*demandCharge for x in o['ps']]
	
	# Demand Before and After Storage Graph
	o['demand'] = demand
	o['demandAfterBattery'] = demandAdj
	o['batteryDischargekW'] = VB_power
	o['batteryDischargekWMax'] = max(VB_power)

	with open(pJoin(modelDir, 'batteryDispatch.txt'), 'w') as f:
		f.write('\n'.join([str(x) for x in o['batteryDischargekW']]) + '\n')

	batteryCycleLife = float(ind['batteryCycleLife'])
	o['batterySoc'] = SoC = [100 - (e / battCapacity * 100) for e in VB_energy]
	cycleEquivalents = sum([SoC[i]-SoC[i+1] for i, x in enumerate(SoC[:-1]) if SoC[i+1] < SoC[i]]) / 100.0
	o['cycleEquivalents'] = cycleEquivalents
	o['batteryLife'] = batteryCycleLife / (cycleEquivalents+10)

	# Cash Flow Graph
	cashFlowCurve = [sum(o['ps'])*demandCharge for year in range(projYears)]
	cashFlowCurve.insert(0, -1 * cellCost * cellQuantity)  # insert initial investment
	o['SPP'] = (cellCost*cellQuantity)/(sum(o['ps'])*demandCharge)
	o['netCashflow'] = cashFlowCurve
	o['cumulativeCashflow'] = [sum(cashFlowCurve[:i+1]) for i, d in enumerate(cashFlowCurve)]
	o['NPV'] = npv(float(ind['discountRate']), cashFlowCurve)

	battCostPerCycle = cellQuantity * cellCost / batteryCycleLife
	lcoeTotCost = cycleEquivalents*retailCost + battCostPerCycle*cycleEquivalents
	o['LCOE'] = lcoeTotCost / (cycleEquivalents*battCapacity+10)

	# Other
	o['startDate'] = '2011-01-01'
	o['stderr'] = ''
	o['stdout'] = 'Success' 
	
	return o

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		'batteryEfficiency': '100',
		'inverterEfficiency': '100',
		'cellCapacity': '7',
		'discountRate': '2.5',
		'created': '2015-06-12 17:20:39.308239',
		'dischargeRate': '5',
		'modelType': modelName,
		'chargeRate': '5',
		'demandCurve': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','Texas_1yr_Load.csv')).read(),
		'fileName': 'FrankScadaValidCSV_Copy.csv',
		# 'dispatchStrategy': 'prediction', 
		'dispatchStrategy': 'optimal', 
		'cellCost': '7140',
		'cellQuantity': '100',
		'runTime': '0:00:03',
		'projYears': '15',
		'demandCharge': '20',
		'dodFactor':'100',
		'retailCost': '0.06',
		'startPeakHour': '18',
		'endPeakHour': '22',
		'batteryCycleLife': '5000',
		# required if dispatch strategy is custom
		'customDispatchStrategy': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','dispatchStrategy.csv')).read(),
		# forecast
		'epochs': '1',
		'newModel': "False",
		'model': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','NCENT.h5')).read().encode("base64"),
		'modelFileName': 'NCENT.h5',
		'histFileName': 'd_Texas_17yr_TempAndLoad.csv',
		"histCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_17yr_TempAndLoad.csv"), 'rU').read(),
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	modelLoc = pJoin(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
	# Blow away old test results if necessary.
	if isdir(modelLoc):
		shutil.rmtree(modelLoc)	
	new(modelLoc)  # Create New.
	renderAndShow(modelLoc)  # Pre-run.
	runForeground(modelLoc)  # Run the model.
	renderAndShow(modelLoc)  # Show the output.

if __name__ == '__main__':
	_tests()
''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import os, sys, shutil, csv, datetime as dt
from os.path import isdir, join as pJoin
from numpy import npv
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# Model metadata:
modelName, template = metadata(__file__)
tooltip = ("The storagePeakShave model calculates the value of a distribution utility " 
	"deploying energy storage based on three possible battery dispatch strategies.")

def _cycleCount(SoC):
	count, inloop = 0, False
	for c in SoC:
		if c < 75.0 and not inloop:
			count += 1
			inloop = True
		if c == 100.0 and inloop:
			inloop = False
	return count

def work(modelDir, inputDict):
	''' Model processing done here. '''
	outData = {}  # See bottom of file for outData's structure

	# Trusted variables
	(cellCapacity, dischargeRate, chargeRate, cellQuantity, demandCharge, cellCost) = \
		[float(inputDict[x]) for x in ('cellCapacity', 'dischargeRate', 'chargeRate', 
			'cellQuantity', 'demandCharge', 'cellCost')]

	# Untrusted variables
	retailCost = float(inputDict.get('retailCost', 0.07))
	projYears = int(inputDict.get('projYears', 10))
	startPeakHour = int(inputDict.get('startPeakHour', 18))
	endPeakHour = int(inputDict.get('endPeakHour', 24))
	dispatchStrategy = str(inputDict.get('dispatchStrategy'))
	batteryCycleLife = int(inputDict.get('batteryCycleLife', 5000))
	
	# Percents -> Decimals, untrusted
	discountRate = float(inputDict.get('discountRate', 2.5)) / 100.0
	dodFactor = float(inputDict.get('dodFactor', 85)) / 100.0

	# Temporarily removed from equations.
	# inverterEfficiency = float(inputDict.get('inverterEfficiency', 92)) / 100.0
	# Note: inverterEfficiency is squared to get round trip efficiency.
	# battEff = float(inputDict.get('batteryEfficiency', 92)) / 100.0 * (inverterEfficiency ** 2)

	# Put demand data in to a file for safe keeping.
	with open(pJoin(modelDir, 'demand.csv'), 'w') as demandFile:
		demandFile.write(inputDict['demandCurve'])
	
	# If dispatch is custom, write the strategy to a file in the model directory
	if dispatchStrategy == 'customDispatch':
		with open(pJoin(modelDir, 'dispatchStrategy.csv'), 'w') as customDispatchFile:
			customDispatchFile.write(inputDict['customDispatchStrategy'])
	
	# Start running battery simulation.
	battCapacity = cellQuantity * cellCapacity * dodFactor
	battDischarge = cellQuantity * dischargeRate
	battCharge = cellQuantity * chargeRate
	
	dates = [(dt.datetime(2011,1,1) + dt.timedelta(hours=1) * x) for x in range(8760)]
	
	# Most of our data goes inside the dc "table"
	dc = []
	try:
		with open(pJoin(modelDir, 'demand.csv')) as inFile:
			reader = csv.reader(inFile)
			for row, date in zip(reader, dates):
				dc.append({ 
						'datetime': date, 
						'power': float(row[0]), # row is a list of length 1
						'month': date.month - 1,
						'hour': date.hour
					})
		assert len(dc) == 8760
	except:
		if str(sys.exc_info()[0]) != "<type 'exceptions.SystemExit'>":		
			raise Exception("CSV file is incorrect format. Please see valid "
				"format definition at <a target='_blank' href = 'https://github.com/"
				"dpinney/omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>"
				"\nOMF Wiki storagePeakShave - Demand File CSV Format</a>")

	# list of 12 lists of monthly demands
	dcGroupByMonth = [[t['power'] for t in dc if t['month']==x] for x in range(12)]

	if dispatchStrategy == 'optimal':	
		ps = [battDischarge] * 12	
		monthlyPeakDemand = [max(lDemands) for lDemands in dcGroupByMonth]
		battSoC = battCapacity  # Battery state of charge; begins full.
		battDoD = [battCapacity] * 12  # Depth-of-discharge every month, depends on dodFactor.
		for row in dc:
			month = row['month']
			powerUnderPeak = monthlyPeakDemand[month] - row['power'] - ps[month]
			isCharging = powerUnderPeak > 0
			isDischarging = powerUnderPeak <= 0
			charge = isCharging * min(
				powerUnderPeak, # new monthly peak - row['power']
				battCharge, # battery maximum charging rate.
				battCapacity - battSoC) # capacity remaining in battery. 
			discharge = isDischarging * min(
				abs(powerUnderPeak), # new monthly peak - row['power']
				abs(battDischarge), # battery maximum charging rate.
				abs(battSoC)) # capacity remaining in battery.
			battSoC += charge
			battSoC -= discharge
			# Update minimum state-of-charge for this month.
			battDoD[month] = min(battSoC, battDoD[month])
			row['netpower'] = row['power'] + charge - discharge
			row['battSoC'] = battSoC
		ps = [ps[month]-(battDoD[month] < 0) for month in range(12)]
		peakShaveSum = sum(ps)
	elif dispatchStrategy == 'daily':
		battSoC = battCapacity
		for row in dc:
			month = int(row['month'])
			discharge = min(battDischarge, battSoC)
			charge = min(battCharge, battCapacity-battSoC)
			#If hour is within peak hours and the battery has charge
			if startPeakHour <= row['hour'] <= endPeakHour and battSoC >= 0:
				row['netpower'] = row['power'] - discharge
				battSoC -= discharge
			else:
			#If hour is outside peak hours and the battery isnt fully charged, charge it
				row['netpower'] = row['power'] + charge
				battSoC += charge
			row['battSoC'] = battSoC

		simpleDCGroupByMonth = [[t for t in dc if t['month']==x] for x in range(12)]
		#Finding rows with max power
		monthlyPeakDemandHist =  [max(dVals, key=lambda x: x['power']) for dVals in simpleDCGroupByMonth]
		monthlyPeakDemandShav = [max(dVals, key=lambda x: x['netpower']) for dVals in simpleDCGroupByMonth]
		ps = [h['power']-s['netpower'] for h, s in zip(monthlyPeakDemandHist, monthlyPeakDemandShav)]
		peakShaveSum = sum(ps)
	else: # Custom dispatch.
		try:
			with open(pJoin(modelDir,'dispatchStrategy.csv')) as strategyFile:
				reader = csv.DictReader(strategyFile)
				for d, row in zip(dc, reader):
					d['dispatch'] = int(row['dispatch'])
				assert all(['dispatch' in r for r in dc])  # ensure each row is filled
		except:
			if str(sys.exc_info()[0]) != "<type 'exceptions.SystemExit'>":
				raise Exception("Dispatch Strategy file is in an incorrect " 
					"format. Please see valid format definition at <a target "
					"= '_blank' href = 'https://github.com/dpinney/omf/wiki/"
					"Models-~-storagePeakShave#custom-dispatch-strategy-file-"
					"csv-format'>\nOMF Wiki storagePeakShave - Custom "
					"Dispatch Strategy File Format</a>")
		battSoC = battCapacity
		for row in dc:
			discharge = min(battDischarge, battSoC)
			charge = min(battCharge, battCapacity - battSoC)
			# If there is a 1 in the dispatch strategy csv, the battery discharges
			if row['dispatch'] == 1:
				row['netpower'] = row['power'] - discharge
				battSoC -= discharge
			else:
				# Otherwise charge the battery.
				if battSoC < battCapacity:
					battSoC += charge
					row['netpower'] = row['power'] + charge
				else:
					row['netpower'] = row['power']
			row['battSoC'] = battSoC
		
		# Calculating how much the battery discharges each month
		dischargeGroupByMonth = [[t['netpower']-t['power'] for t in dc if t['month']==x] for x in range(12)]
		simpleDCGroupByMonth = [[t for t in dc if t['month']==x] for x in range(12)]
		monthlyPeakDemandHist =  [max(dVals, key=lambda x: x['power']) for dVals in simpleDCGroupByMonth]
		monthlyPeakDemandShav = [max(dVals, key=lambda x: x['netpower']) for dVals in simpleDCGroupByMonth]
		ps = [h['power']-s['netpower'] for h, s in zip(monthlyPeakDemandHist, monthlyPeakDemandShav)]
		peakShaveSum = sum(ps)
		# Calculate how much the battery charges per year for cashFlowCurve, SPP calculation, kWhToRecharge
		chargePerMonth = [sum(month) for month in dischargeGroupByMonth]
		totalYearlyCharge = sum(chargePerMonth)
	
	# ------------------------- CALCULATIONS ------------------------- #
	# peakShave of 0 means no benefits, so make it -1 to avoid divide by zero error
	if peakShaveSum == 0:
		peakShaveSum = -1
	
	# dispatch-specific output
	if dispatchStrategy == 'optimal':
		cashFlowCurve = [peakShaveSum * demandCharge for year in range(projYears)]
		outData['SPP'] = (cellCost*cellQuantity)/(peakShaveSum*demandCharge)
		outData['kWhtoRecharge'] = ps
	elif dispatchStrategy == 'daily':
		#cashFlowCurve is $ in from peak shaving minus the cost to recharge the battery every day of the year
		cashFlowCurve = [(peakShaveSum * demandCharge)-(battCapacity*365*retailCost) for year in range(projYears)]
		#simplePayback is also affected by the cost to recharge the battery every day of the year
		outData['SPP'] = (cellCost*cellQuantity)/((peakShaveSum*demandCharge)-(battCapacity*365*retailCost))
		#Battery is dispatched and charged every day, ~30 days per month
		outData['kWhtoRecharge'] = [battCapacity * 30] * 12
	else:
		cashFlowCurve = [(peakShaveSum * demandCharge)-(totalYearlyCharge*retailCost) for year in range(projYears)]
		outData['SPP'] = (cellCost*cellQuantity)/((peakShaveSum*demandCharge)-(totalYearlyCharge*retailCost))
		outData['kWhtoRecharge'] = chargePerMonth
	cashFlowCurve.insert(0, -1 * cellCost * cellQuantity)  # insert initial investment
	

	# Monthly Cost Comparison Table
	outData['monthlyDemand'] = [sum(lDemand)/1000 for lDemand in dcGroupByMonth]
	outData['monthlyDemandRed'] = [t - p for t, p in zip(outData['monthlyDemand'], ps)]
	outData['ps'] = ps
	# outData['kWhtoRecharge'] see above
	outData['benefitMonthly'] = [x * demandCharge for x in ps]
	outData['costtoRecharge'] = [retailCost * x for x in outData['kWhtoRecharge']]
	outData['benefitNet'] = [b - c for b, c in zip(outData['benefitMonthly'], outData['costtoRecharge'])]

	# Demand Before and After Storage Graph
	outData['demand'] = [t['power']*1000.0 for t in dc]
	outData['demandAfterBattery'] = [t['netpower']*1000.0 for t in dc]
	outData['batteryDischargekW'] = [d - dab for d, dab in zip(outData['demand'], outData['demandAfterBattery'])]
	outData['batteryDischargekWMax'] = max(outData['batteryDischargekW'])


	# Battery State of Charge Graph
	# Turn dc's SoC into a percentage, with dodFactor considered.
	outData['batterySoc'] = [t['battSoC']/battCapacity*100.0*dodFactor + (100-100*dodFactor) for t in dc]
	# Estimate number of cyles the battery went through.
	outData['cycleEquivalents'] = cycleEquivalents = _cycleCount(outData['batterySoc'])
	outData['batteryLife'] = batteryCycleLife/cycleEquivalents

	# Cash Flow Graph
	outData['netCashflow'] = cashFlowCurve
	outData['cumulativeCashflow'] = [sum(cashFlowCurve[:i+1]) for i, d in enumerate(cashFlowCurve)]
	outData['NPV'] = npv(discountRate, cashFlowCurve)
	
	battCostPerCycle = cellQuantity * cellCapacity * cellCost / batteryCycleLife
	lcoeTotEnergy = cycleEquivalents * cellQuantity * cellCapacity
	lcoeTotCost = cycleEquivalents*retailCost + battCostPerCycle*cycleEquivalents
	LCOE = lcoeTotCost / lcoeTotEnergy
	outData['LCOE'] = LCOE

	# Other
	outData['startDate'] = '2011-01-01'  # dc[0]['datetime'].isoformat()
	outData['stderr'] = ''
	# Seemingly unimportant. Ask permission to delete.
	outData['stdout'] = 'Success' 
	outData['months'] = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
	

	# ------------------------ DEBUGGING TOOLS ----------------------- #
	# import matplotlib.pyplot as plt 
	# dcThroughTheMonth = [[t for t in iter(dc) if t['month']<=x] for x in range(12)]
	# hoursThroughTheMonth = [len(dcThroughTheMonth[month]) for month in range(12)]
	# # Output some matplotlib results as well.
	# plt.plot([t['power'] for t in dc])
	# plt.plot([t['netpower'] for t in dc])
	# plt.plot([t['battSoC'] for t in dc])
	# for month in range(12):
	#   plt.axvline(hoursThroughTheMonth[month])
	# plt.savefig(pJoin(modelDir,"plot.png"))

	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		# used by __neoMetaModel__.py
		'modelType': modelName,
		'created': '2015-06-12 17:20:39.308239',
		'runTime': '0:00:03',
		# used for this program
		'batteryEfficiency': '92',
		'inverterEfficiency': '97.5',
		'cellCapacity': '7',
		'discountRate': '2.5',
		'dischargeRate': '5',
		'chargeRate': '5',
		'demandCurve': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','FrankScadaValidCSV_Copy.csv')).read(),
		'fileName': 'FrankScadaValidCSV_Copy.csv',
		'dispatchStrategy': 'optimal',
		'cellCost': '7140',
		'cellQuantity': '10',
		'projYears': '15',
		'demandCharge': '20',
		'dodFactor': '97',
		'retailCost': '0.06',
		'startPeakHour': '18',
		'endPeakHour': '22',
		'batteryCycleLife': '5000',
		# required if dispatch strategy is custom
		'customDispatchStrategy': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','dispatchStrategy.csv')).read(),
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

'''
outDic {
	startdate: str
	stdout: "Success"
	batteryDischargekWMax: float
	batteryDischargekw: [8760] float
	monthlyDemandRed: [12] float
	ps: [12] float
	demandAfterBattery: [8760] float
	SPP: float
	kwhtoRecharge [12] float
	LCOE: float
	batteryLife: float
	cumulativeCashflow: [12] float
	batterySoc: [8760] float
	demand: [8760] float
	benefitMonthly: [12] float
	netCashflow: [12] float
	costtoRecharge: [12] float
	months: [12] (strings)
	monthlyDemand: [12] float
	cycleEquivalents: float
	stderr: ""
	NPV: float
	benefitNet: 12
}
'''

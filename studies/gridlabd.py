#!/usr/bin/env python

if __name__ == '__main__':
	# Setup for tests.
	import os, sys
	os.chdir('./..')
	sys.path.append(os.getcwd())

import os
import feeder
import __util__ as util
import solvers
with open('./studies/gridlabd.html','r') as configFile: configHtmlTemplate = configFile.read()

class Gridlabd:
	def __init__(self, jsonDict, new=False):
		self.analysisName = jsonDict.get('analysisName','')
		self.name = jsonDict.get('name','')
		self.simLength = jsonDict.get('simLength',0)
		self.simLengthUnits = jsonDict.get('simLengthUnits','')
		self.simStartDate = jsonDict.get('simStartDate','')
		self.climate = jsonDict.get('climate','')
		self.sourceFeeder = jsonDict.get('sourceFeeder','')
		self.inputJson = jsonDict.get('inputJson', {})
		self.outputJson = jsonDict.get('outputJson', {})
		self.studyType = 'gridlabd'
		# If we're creating a new one:
		if new == True:
			# Attach recorders:
			tree = jsonDict['inputJson']['tree']
			feeder.attachRecorders(tree, 'Regulator', 'object', 'regulator')
			feeder.attachRecorders(tree, 'Capacitor', 'object', 'capacitor')
			feeder.attachRecorders(tree, 'Inverter', 'object', 'inverter')
			feeder.attachRecorders(tree, 'Windmill', 'object', 'windturb_dg')
			feeder.attachRecorders(tree, 'CollectorVoltage', None, None)
			feeder.attachRecorders(tree, 'Climate', 'object', 'climate')
			feeder.attachRecorders(tree, 'OverheadLosses', None, None)
			feeder.attachRecorders(tree, 'UndergroundLosses', None, None)
			feeder.attachRecorders(tree, 'TriplexLosses', None, None)
			feeder.attachRecorders(tree, 'TransformerLosses', None, None)
			feeder.groupSwingKids(tree)
			# Modify the glm with time variables:
			feeder.adjustTime(tree=tree, simLength=self.simLength, simLengthUnits=str(self.simLengthUnits), simStartDate=self.simStartDate)

	# WARNING! Run does not care about performance and will happily run for a long, long time. Spawn a thread or process for this nonsense.
	def _agg(self, series, func, level):
		if level in ['days','months']:
			return util.aggSeries(stamps, series, func, level)
		else:
			return series	

	def run(self):
		# Execute the solver, the process output.
		rawOut = solvers.gridlabd.run(self)
		if rawOut == False: return False
		cleanOut = {}
		# Std Err and Std Out
		cleanOut['stderr'] = rawOut['stderr']
		cleanOut['stdout'] = rawOut['stdout']
		# Time Stamps
		for key in rawOut:
			if '# timestamp' in rawOut[key]:
				cleanOut['timeStamps'] = rawOut[key]['# timestamp']
				break
			elif '# property.. timestamp' in rawOut[key]:
				cleanOut['timeStamps'] = rawOut[key]['# property.. timestamp']
			else:
				cleanOut['timeStamps'] = []
		# Day/Month Aggregation Setup:
		stamps = cleanOut.get('timeStamps',[])
		level = self.simLengthUnits

		def avg(x):
			return sum(x)/len(x)
		# Climate
		for key in rawOut:
			if key.startswith('Climate_') and key.endswith('.csv'):
				cleanOut['climate'] = {}
				cleanOut['climate']['Rain Fall (in/h)'] = self._agg(rawOut[key].get('rainfall'), sum, level)
				cleanOut['climate']['Wind Speed (m/s)'] = self._agg(rawOut[key].get('wind_speed'), avg, level)
				cleanOut['climate']['Temperature (F)'] = self._agg(rawOut[key].get('temperature'), max, level)
				cleanOut['climate']['Snow Depth (in)'] = self._agg(rawOut[key].get('snowdepth'), max, level)
				cleanOut['climate']['Direct Insolation (W/m^2)'] = self._agg(rawOut[key].get('solar_direct'), sum, level)
		# Voltage Band
		if 'VoltageJiggle.csv' in rawOut:
			cleanOut['allMeterVoltages'] = {}
			cleanOut['allMeterVoltages']['Min'] = self._agg(rawOut['VoltageJiggle.csv']['min(voltage_12.mag)'], min, level)
			cleanOut['allMeterVoltages']['Mean'] = self._agg(rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)'], avg, level)
			cleanOut['allMeterVoltages']['StdDev'] = self._agg(rawOut['VoltageJiggle.csv']['std(voltage_12.mag)'], avg, level)
			cleanOut['allMeterVoltages']['Max'] = self._agg(rawOut['VoltageJiggle.csv']['max(voltage_12.mag)'], max, level)
		# Capacitor Activation
		for key in rawOut:
			if key.startswith('Capacitor_') and key.endswith('.csv'):
				if 'Capacitors' not in cleanOut:
					cleanOut['Capacitors'] = {}
				capName = key[10:-4]
				cleanOut['Capacitors'][capName] = {}
				for switchKey in rawOut[key]:
					if switchKey != '# timestamp':
						cleanOut['Capacitors'][capName][switchKey] = self._agg(rawOut[key][switchKey], avg, level)
		# Study Details
		glmTree = rawOut['glmTree']
		names = [glmTree[x]['name'] for x in glmTree if 'name' in glmTree[x]]
		cleanOut['componentNames'] = list(set(names))
		# Regulator Powerflow
		for key in rawOut:
			if key.startswith('Regulator_') and key.endswith('.csv'):
				if 'Regulators' not in cleanOut: cleanOut['Regulators'] = {}
				regName = key[10:-4]
				cleanOut['Regulators'][regName] = {}
				cleanOut['Regulators'][regName]['Tap A Position'] = self._agg(rawOut[key]['tap_A'], avg, level)
				cleanOut['Regulators'][regName]['Tap B Position'] = self._agg(rawOut[key]['tap_B'], avg, level)
				cleanOut['Regulators'][regName]['Tap C Position'] = self._agg(rawOut[key]['tap_C'], avg, level)
				realA = rawOut[key]['power_in_A.real']
				realB = rawOut[key]['power_in_B.real']
				realC = rawOut[key]['power_in_C.real']
				imagA = rawOut[key]['power_in_A.imag']
				imagB = rawOut[key]['power_in_B.imag']
				imagC = rawOut[key]['power_in_C.imag']
				cleanOut['Regulators'][regName]['Power Factor'] = self._agg(util.threePhasePowFac(realA,realB,realC,imagA,imagB,imagC), avg, level)
				cleanOut['Regulators'][regName]['Tap A App Power'] = self._agg(util.vecPyth(realA,imagA), avg, level)
				cleanOut['Regulators'][regName]['Tap B App Power'] = self._agg(util.vecPyth(realB,imagB), avg, level)
				cleanOut['Regulators'][regName]['Tap C App Power'] = self._agg(util.vecPyth(realC,imagC), avg, level)
		# Meter Powerflow
		for key in rawOut:
			if key.startswith('meterRecorder_') and key.endswith('.csv'):
				if 'Meters' not in cleanOut: cleanOut['Meters'] = {}
				meterName = key[14:-4]
				cleanOut['Meters'][meterName] = {}
				cleanOut['Meters'][meterName]['Voltage (V)'] = self._agg(util.vecPyth(rawOut[key]['voltage_12.real'],rawOut[key]['voltage_12.imag']), avg, level)
				cleanOut['Meters'][meterName]['Load (kW)'] = self._agg(rawOut[key]['measured_power'], avg, level)
		# Power Consumption
		cleanOut['Consumption'] = {}
		for key in rawOut:
			if key.startswith('SwingKids_') and key.endswith('.csv'):
				oneSwingPower = self._agg(util.vecPyth(rawOut[key]['sum(power_in.real)'],rawOut[key]['sum(power_in.imag)']), avg, level)
				if 'Power' not in cleanOut['Consumption']:
					cleanOut['Consumption']['Power'] = oneSwingPower
				else:
					cleanOut['Consumption']['Power'] = util.vecSum(oneSwingPower,cleanOut['Consumption']['Power'])
			elif key.startswith('Inverter_') and key.endswith('.csv'): 	
				realA = rawOut[key]['power_A.real']
				realB = rawOut[key]['power_B.real']
				realC = rawOut[key]['power_C.real']
				imagA = rawOut[key]['power_A.imag']
				imagB = rawOut[key]['power_B.imag']
				imagC = rawOut[key]['power_C.imag']
				oneDgPower = self._agg(util.vecSum(util.vecPyth(realA,imagA),util.vecPyth(realB,imagB),util.vecPyth(realC,imagC)), avg, level)
				if 'DG' not in cleanOut['Consumption']:
					cleanOut['Consumption']['DG'] = oneDgPower
				else:
					cleanOut['Consumption']['DG'] = util.vecSum(oneDgPower,cleanOut['Consumption']['DG'])
			elif key.startswith('Windmill_') and key.endswith('.csv'):
				vrA = rawOut[key]['voltage_A.real']
				vrB = rawOut[key]['voltage_B.real']
				vrC = rawOut[key]['voltage_C.real']
				viA = rawOut[key]['voltage_A.imag']
				viB = rawOut[key]['voltage_B.imag']
				viC = rawOut[key]['voltage_C.imag']
				crB = rawOut[key]['current_B.real']
				crA = rawOut[key]['current_A.real']
				crC = rawOut[key]['current_C.real']
				ciA = rawOut[key]['current_A.imag']
				ciB = rawOut[key]['current_B.imag']
				ciC = rawOut[key]['current_C.imag']
				powerA = util.vecProd(util.vecPyth(vrA,viA),util.vecPyth(crA,ciA))
				powerB = util.vecProd(util.vecPyth(vrB,viB),util.vecPyth(crB,ciB))
				powerC = util.vecProd(util.vecPyth(vrC,viC),util.vecPyth(crC,ciC))
				oneDgPower = self._agg(util.vecSum(powerA,powerB,powerC), avg, level)
				if 'DG' not in cleanOut['Consumption']:
					cleanOut['Consumption']['DG'] = oneDgPower
				else:
					cleanOut['Consumption']['DG'] = util.vecSum(oneDgPower,cleanOut['Consumption']['DG'])
			elif key in ['OverheadLosses.csv', 'UndergroundLosses.csv', 'TriplexLosses.csv', 'TransformerLosses.csv']:
				realA = rawOut[key]['sum(power_losses_A.real)']
				imagA = rawOut[key]['sum(power_losses_A.imag)']
				realB = rawOut[key]['sum(power_losses_B.real)']
				imagB = rawOut[key]['sum(power_losses_B.imag)']
				realC = rawOut[key]['sum(power_losses_C.real)']
				imagC = rawOut[key]['sum(power_losses_C.imag)']
				oneLoss = self._agg(util.vecSum(util.vecPyth(realA,imagA),util.vecPyth(realB,imagB),util.vecPyth(realC,imagC)), avg, level)
				if 'Losses' not in cleanOut['Consumption']:
					cleanOut['Consumption']['Losses'] = oneLoss
				else:
					cleanOut['Consumption']['Losses'] = util.vecSum(oneLoss,cleanOut['Consumption']['Losses'])
		# Aggregate up the timestamps:
		if level=='days':
			cleanOut['timeStamps'] = util.aggSeries(stamps, stamps, lambda x:x[0][0:10], 'days')
		elif level=='months':
			cleanOut['timeStamps'] = util.aggSeries(stamps, stamps, lambda x:x[0][0:7], 'months')
		
		# Put the results into the self variable:
		self.outputJson = cleanOut
		return True

def _tests():
	import storage
	import json
	store = storage.Filestore('data')
	# Pull in a study.
	# testStudy = Gridlabd('IndySolar', 'zSolar Trio', store.getMetadata('Study','zSolar Trio---IndySolar'), store.get('Study','zSolar Trio---IndySolar'))
	testStudy = Gridlabd(json.load(open("data/Study/public_zSolar Trio---IndySolar.json")))

	print testStudy.name, dir(testStudy)
	# Run the study.
	testStudy.run()
	print testStudy.outputJson.keys()

if __name__ == '__main__':
	_tests()
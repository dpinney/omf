#!/usr/bin/env python

import os
import feeder
import shutil
import subprocess
import json
import __util__ as util
import analysis

with open('./studies/gridlabd.html','r') as configFile: configHtmlTemplate = configFile.read()

def create(analysisName, simLength, simLengthUnits, simStartDate, studyConfig):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyConfig['studyName']
	# make the study folder:
	os.mkdir(studyPath)
	# copy over the feeder files:
	feederPath = 'feeders/' + studyConfig['feederName']
	for fileName in  os.listdir(feederPath):
		shutil.copyfile(feederPath + '/' + fileName, studyPath + '/' + fileName)
	# Attach recorders:
	tree = feeder.parse(studyPath + '/main.glm')
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
	feeder.adjustTime(tree=tree, simLength=simLength, simLengthUnits=str(simLengthUnits), simStartDate=simStartDate)
	# write the glm:
	with open(studyPath + '/main.glm','w') as glmFile:
		glmFile.write(feeder.write(tree))
	# copy over tmy2 and replace the dummy climate.tmy2.
	shutil.copyfile('tmy2s/' + studyConfig['tmy2name'], studyPath + '/climate.tmy2')
	# add the metadata:
	metadata = {'sourceFeeder':str(studyConfig['feederName']), 'climate':str(studyConfig['tmy2name']), 'studyType':str(studyConfig['studyType'])}
	with open(studyPath + '/metadata.json','w') as mdFile:
		json.dump(metadata, mdFile)
	return

# WARNING! Run does not care about performance and will happily run for a long, long time. Spawn a thread or process for this nonsense.
def run(analysisName, studyName):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyName
	# RUN GRIDLABD (EXPENSIVE!)
	with open(studyPath + '/stdout.txt','w') as stdout, open(studyPath + '/stderr.txt','w') as stderr:
		# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		proc = subprocess.Popen(['gridlabd','-w','main.glm'], cwd=studyPath, stdout=stdout, stderr=stderr)
		# Put PID.
		with open(studyPath + '/PID.txt','w') as pidFile:
			pidFile.write(str(proc.pid))
		proc.wait()
		# Remove PID to indicate completion.
		try: 
			os.remove(studyPath + '/PID.txt')
		except:
			# Terminated, return false so analysis knows to not run any more studies.
			return False
	# Study run succesfully, do post-proc.
	generateReferenceOutput(analysisName, studyPath)
	# Return true to indicate success.
	return True

def generateReferenceOutput(analysisName, studyPath):
	# Setting up:
	rawOut = util.anaDataTree(studyPath, lambda x:True) # Lambda x:true means get every csv.
	cleanOut = {}
	# Std Err and Std Out
	with open(studyPath + '/stderr.txt','r') as stderrFile:
		cleanOut['stderr'] = stderrFile.read().strip()
	with open(studyPath + '/stdout.txt','r') as stdoutFile:
		cleanOut['stdout'] = stdoutFile.read().strip()
	# Time Stamps
	for key in rawOut:
		if '# timestamp' in rawOut[key]:
			cleanOut['timeStamps'] = rawOut[key]['# timestamp']
			break
		elif '# property.. timestamp' in rawOut[key]:
			cleanOut['timeStamps'] = rawOut[key]['# property.. timestamp']
	# Day/Month Aggregation Setup:
	stamps = cleanOut['timeStamps']
	level = analysis.getMetadata(analysisName)['simLengthUnits']
	def agg(series, func):
		if level in ['days','months']:
			return util.aggSeries(stamps, series, func, level)
		else:
			return series
	def avg(x):
		return sum(x)/len(x)
	# Climate
	if 'Climate_climate.csv' in rawOut:
		cleanOut['climate'] = {}
		cleanOut['climate']['Rain Fall (in/h)'] = agg(rawOut['Climate_climate.csv']['rainfall'], sum)
		cleanOut['climate']['Wind Speed (m/s)'] = agg(rawOut['Climate_climate.csv']['wind_speed'], avg)
		cleanOut['climate']['Temperature (F)'] = agg(rawOut['Climate_climate.csv']['temperature'], max)
		cleanOut['climate']['Snow Depth (in)'] = agg(rawOut['Climate_climate.csv']['snowdepth'], max)
		cleanOut['climate']['Direct Insolation (W/m^2)'] = agg(rawOut['Climate_climate.csv']['solar_direct'], sum)
	# Voltage Band
	if 'VoltageJiggle.csv' in rawOut:
		cleanOut['allMeterVoltages'] = {}
		cleanOut['allMeterVoltages']['Min'] = agg(rawOut['VoltageJiggle.csv']['min(voltage_12.mag)'], min)
		cleanOut['allMeterVoltages']['Mean'] = agg(rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)'], avg)
		cleanOut['allMeterVoltages']['StdDev'] = agg(rawOut['VoltageJiggle.csv']['std(voltage_12.mag)'], avg)
		cleanOut['allMeterVoltages']['Max'] = agg(rawOut['VoltageJiggle.csv']['max(voltage_12.mag)'], max)
	# Capacitor Activation
	for key in rawOut:
		if key.startswith('Capacitor_') and key.endswith('.csv'):
			if 'Capacitors' not in cleanOut:
				cleanOut['Capacitors'] = {}
			capName = key[10:-4]
			cleanOut['Capacitors'][capName] = {}
			for switchKey in rawOut[key]:
				if switchKey != '# timestamp':
					cleanOut['Capacitors'][capName][switchKey] = agg(rawOut[key][switchKey], avg)
	# Study Details
	glmTree = feeder.parse(studyPath + '/main.glm')
	names = [glmTree[x]['name'] for x in glmTree if 'name' in glmTree[x]]
	cleanOut['componentNames'] = list(set(names))
	# Regulator Powerflow
	for key in rawOut:
		if key.startswith('Regulator_') and key.endswith('.csv'):
			if 'Regulators' not in cleanOut: cleanOut['Regulators'] = {}
			regName = key[10:-4]
			cleanOut['Regulators'][regName] = {}
			cleanOut['Regulators'][regName]['Tap A Position'] = agg(rawOut[key]['tap_A'], avg)
			cleanOut['Regulators'][regName]['Tap B Position'] = agg(rawOut[key]['tap_B'], avg)
			cleanOut['Regulators'][regName]['Tap C Position'] = agg(rawOut[key]['tap_C'], avg)
			realA = rawOut[key]['power_in_A.real']
			realB = rawOut[key]['power_in_B.real']
			realC = rawOut[key]['power_in_C.real']
			imagA = rawOut[key]['power_in_A.imag']
			imagB = rawOut[key]['power_in_B.imag']
			imagC = rawOut[key]['power_in_C.imag']
			cleanOut['Regulators'][regName]['Power Factor'] = agg(util.threePhasePowFac(realA,realB,realC,imagA,imagB,imagC), avg)
			cleanOut['Regulators'][regName]['Tap A App Power'] = agg(util.vecPyth(realA,imagA), avg)
			cleanOut['Regulators'][regName]['Tap B App Power'] = agg(util.vecPyth(realB,imagB), avg)
			cleanOut['Regulators'][regName]['Tap C App Power'] = agg(util.vecPyth(realC,imagC), avg)
	# Meter Powerflow
	for key in rawOut:
		if key.startswith('meterRecorder_') and key.endswith('.csv'):
			if 'Meters' not in cleanOut: cleanOut['Meters'] = {}
			meterName = key[14:-4]
			cleanOut['Meters'][meterName] = {}
			cleanOut['Meters'][meterName]['Voltage (V)'] = agg(util.vecPyth(rawOut[key]['voltage_12.real'],rawOut[key]['voltage_12.imag']), avg)
			cleanOut['Meters'][meterName]['Load (kW)'] = agg(rawOut[key]['measured_power'], avg)
	# Power Consumption
	cleanOut['Consumption'] = {}
	for key in rawOut:
		if key.startswith('SwingKids_') and key.endswith('.csv'):
			oneSwingPower = agg(util.vecPyth(rawOut[key]['sum(power_in.real)'],rawOut[key]['sum(power_in.imag)']), avg)
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
			oneDgPower = agg(util.vecSum(util.vecPyth(realA,imagA),util.vecPyth(realB,imagB),util.vecPyth(realC,imagC)), avg)
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
			oneDgPower = agg(util.vecSum(powerA,powerB,powerC), avg)
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
			oneLoss = agg(util.vecSum(util.vecPyth(realA,imagA),util.vecPyth(realB,imagB),util.vecPyth(realC,imagC)), avg)
			if 'Losses' not in cleanOut['Consumption']:
				cleanOut['Consumption']['Losses'] = oneLoss
			else:
				cleanOut['Consumption']['Losses'] = util.vecSum(oneLoss,cleanOut['Consumption']['Losses'])
	# Aggregate up the timestamps:
	if level=='days':
		cleanOut['timeStamps'] = util.aggSeries(stamps, stamps, lambda x:x[0][0:10], 'days')
	elif level=='months':
		cleanOut['timeStamps'] = util.aggSeries(stamps, stamps, lambda x:x[0][0:7], 'months')
	# Writing clean output.
	with open(studyPath + '/cleanOutput.json','w') as cleanFile:
		json.dump(cleanOut, cleanFile, indent=4)
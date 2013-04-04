#!/usr/bin/env python

import os
import feeder
import shutil
import subprocess
import json
import __util__ as util

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
	studyDir = 'analyses/' + analysisName + '/studies/' + studyName
	# RUN GRIDLABD (EXPENSIVE!)
	with open(studyDir + '/stdout.txt','w') as stdout, open(studyDir + '/stderr.txt','w') as stderr:
		# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		proc = subprocess.Popen(['gridlabd','-w','main.glm'], cwd=studyDir, stdout=stdout, stderr=stderr)
		# Put PID.
		with open(studyDir + '/PID.txt','w') as pidFile:
			pidFile.write(str(proc.pid))
		proc.wait()
		# Remove PID to indicate completion.
		try: 
			os.remove(studyDir + '/PID.txt')
		except:
			# Terminated, return false so analysis knows to not run any more studies.
			return False
	# Study run succesfully, do post-proc.
	generateReferenceOutput(studyDir)
	# Return true to indicate success.
	return True

def generateReferenceOutput(studyPath):
	# Pull in the raw output:
	rawOut = util.anaDataTree(studyPath, lambda x:True) # Lambda function gets everything.
	# Writing raw output.
	with open(studyPath + '/output.json','w') as outFile:
		json.dump(rawOut, outFile, indent=4)
	# Cleaning up.
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
			break
	# Climate
	if 'Climate_climate.csv' in rawOut:
		cleanOut['climate'] = {}
		cleanOut['climate']['Rain Fall (in/h)'] = rawOut['Climate_climate.csv']['rainfall']
		cleanOut['climate']['Wind Speed (m/s)'] = rawOut['Climate_climate.csv']['wind_speed']
		cleanOut['climate']['Temperature (F)'] = rawOut['Climate_climate.csv']['temperature']
		cleanOut['climate']['Snow Depth (in)'] = rawOut['Climate_climate.csv']['snowdepth']
		cleanOut['climate']['Direct Insolation (W/m^2)'] = rawOut['Climate_climate.csv']['solar_direct']
	# Voltage Band
	if 'VoltageJiggle.csv' in rawOut:
		cleanOut['allMeterVoltages'] = {}
		cleanOut['allMeterVoltages']['Min'] = rawOut['VoltageJiggle.csv']['min(voltage_12.mag)']
		cleanOut['allMeterVoltages']['Mean'] = rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)']
		cleanOut['allMeterVoltages']['StdDev'] = rawOut['VoltageJiggle.csv']['std(voltage_12.mag)']
		cleanOut['allMeterVoltages']['Max'] = rawOut['VoltageJiggle.csv']['max(voltage_12.mag)']
	# Capacitor Activation
	for key in rawOut:
		if key.startswith('Capacitor_') and key.endswith('.csv'):
			if 'Capacitors' not in cleanOut:
				cleanOut['Capacitors'] = {}
			capName = key[10:-4]
			cleanOut['Capacitors'][capName] = {}
			for switchKey in rawOut[key]:
				if switchKey != '# timestamp':
					cleanOut['Capacitors'][capName][switchKey] = rawOut[key][switchKey]
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
			cleanOut['Regulators'][regName]['Tap A Position'] = rawOut[key]['tap_A']
			cleanOut['Regulators'][regName]['Tap B Position'] = rawOut[key]['tap_B']
			cleanOut['Regulators'][regName]['Tap C Position'] = rawOut[key]['tap_C']
			realA = rawOut[key]['power_in_A.real']
			realB = rawOut[key]['power_in_B.real']
			realC = rawOut[key]['power_in_C.real']
			imagA = rawOut[key]['power_in_A.imag']
			imagB = rawOut[key]['power_in_B.imag']
			imagC = rawOut[key]['power_in_C.imag']
			cleanOut['Regulators'][regName]['Power Factor'] = util.threePhasePowFac(realA,realB,realC,imagA,imagB,imagC)
			cleanOut['Regulators'][regName]['Tap A App Power'] = util.vecPyth(realA,imagA)
			cleanOut['Regulators'][regName]['Tap B App Power'] = util.vecPyth(realB,imagB)
			cleanOut['Regulators'][regName]['Tap C App Power'] = util.vecPyth(realC,imagC)
	# Meter Powerflow
	for key in rawOut:
		if key.startswith('meterRecorder_') and key.endswith('.csv'):
			if 'Meters' not in cleanOut: cleanOut['Meters'] = {}
			meterName = key[14:-4]
			cleanOut['Meters'][meterName] = {}
			cleanOut['Meters'][meterName]['Voltage (V)'] = util.vecPyth(rawOut[key]['voltage_12.real'],rawOut[key]['voltage_12.imag'])
			cleanOut['Meters'][meterName]['Load (kW)'] = rawOut[key]['measured_power']
	# Power Consumption
	pass
	# Writing clean output.
	with open(studyPath + '/cleanOutput.json','w') as cleanFile:
		json.dump(cleanOut, cleanFile, indent=4)
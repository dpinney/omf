# imports --------------------------------------------------------------------------

import json, csv, datetime, time, copy
import numpy as np
from datetime import datetime, timedelta
from omf import omfDir, feeder, loadModeling
from omf.solvers import gridlabd

# user inputs ----------------------------------------------------------------------

WORKING_DIR = omfDir + '/scratch/faultLabeledMeterData'


TIMEZONE = 'PST+8PDT'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
SIM_START_TIME = '2000-01-01 00:00:00 PST'
SIM_STOP_TIME = '2000-01-02 00:00:00 PST'

THEFT_LINE_LENGTH = 100
THEFT_ON_TIME = 12*3600
THEFT_OFF_TIME = 12*3600
THEFT_POWER = 8000
THEFT_POWER_STDDEV = 10
MALFUNCTION_POWER = 4000
SHORTED_TRANSFORMER_PERCENTAGE = 0.9

CIRCUIT_PATHS = [
	'/static/publicFeeders/DEC Red Base.omd', 
	'/static/publicFeeders/ABEC Columbia.omd', 
	'/static/publicFeeders/Olin Barre GH.omd', 
	'/static/publicFeeders/Olin Barre GH.omd', 
	'/static/publicFeeders/Olin Barre GH.omd',
	'/static/publicFeeders/Olin Barre GH.omd',
	'/static/publicFeeders/Olin Barre GH.omd']
CONDITION_METERS = [
	'tn_B_645', 
	'nodeS1808-31-0011808-31-003_A', 
	'node62463133906T62463072031', 
	'node62463024800T62463023775', 
	'node62463021692T62463021663',
	'node62463027798T62463027880',
	'node62463020586T62463020670']
CONDITION_TRANSFORMERS = [
	'CTTF_B_645', 
	'1808-31-003_A', 
	'T62463072031', 
	'T62463023775',
	'T62463021663',
	'T62463027880',
	'T62463020670'] 
METER_FILENAMES = [
	'meterDEC.csv', 
	'meterABEC.csv', 
	'meterOlin.csv', 
	'meterOlin.csv', 
	'meterOlin.csv',
	'meterOlin.csv',
	'meterOlin.csv']
OUTPUT_FILENAMES = [
	'dataDEC.csv', 
	'dataABEC.csv', 
	'dataOlin-1.csv', 
	'dataOlin-2.csv', 
	'dataOlin-3.csv',
	'dataOlin-1a.csv',
	'dataOlin-1b.csv']

CONDITION_TYPES = [ 'None', 'theft', 'equipmentMafunction', 'transformerShort' ]
# CONDITION_TYPES = [ 'None', 'theft', 'equipmentMafunction', 'transformerShort']

METRICS_OF_INTEREST = 'measured_voltage_1.real, ' + \
'measured_voltage_2.real, ' + \
'measured_voltage_N.real, ' + \
'measured_current_1.real, ' + \
'measured_current_2.real, ' + \
'measured_current_N.real, ' + \
'indiv_measured_power_1.real, ' + \
'indiv_measured_power_2.real, ' + \
'indiv_measured_power_N.real'
RECORDER_INTERVAL_SECS = 900
RECORDER_LIMIT = 40000 

# helper function definitions ------------------------------------------------------

def generateTreeWithCondition(tree, condition):

	treeCopy = copy.deepcopy(tree)

	if condition == 'None':
		pass

	elif condition == 'transformerShort':

		for key in treeCopy:
			objectName = treeCopy[key].get('name','')
			if objectName == CONDITION_TRANSFORMER:
				config = treeCopy[key]['configuration']
				treeCopy[key]['configuration'] = 'shortedTransformer' 
				break;

		for key in treeCopy:
			objectName = treeCopy[key].get('name','')
			if objectName == config:
				shortedTransformer = copy.deepcopy(treeCopy[key])
				secondaryVoltage = shortedTransformer.get('secondary_voltage')
				if secondaryVoltage is not None:
					secondaryVoltage = float(secondaryVoltage)
					break;

		if secondaryVoltage is None:
			raise Exception('Secondary voltage not specified for transformer')

		shortedTransformer['name'] = 'shortedTransformer' 
		shortedTransformer['secondary_voltage'] = SHORTED_TRANSFORMER_PERCENTAGE \
		 * secondaryVoltage
		treeCopy[feeder.getMaxKey(treeCopy) + 1] = shortedTransformer

	
	elif condition == 'theft':
		
		timezoneString = SIM_START_TIME[-4:]
		startTime = datetime.strptime(SIM_START_TIME[:-4], TIME_FORMAT)
		stopTime = datetime.strptime(SIM_STOP_TIME[:-4], TIME_FORMAT)
		delta = timedelta(seconds=RECORDER_INTERVAL_SECS)
		
		currentTime = startTime
		switchTime = startTime
		off = True
		
		with open( 'theftLoad.csv', 'w' ) as outputFile:
			writer = csv.writer(outputFile, delimiter=',')
		
			while currentTime <= stopTime:

				timestamp = currentTime.strftime(TIME_FORMAT) + ' ' + TIMEZONE[0:3]
				
				timeSinceSwitch = (currentTime - switchTime).seconds
				if off:
					value = 0
					if timeSinceSwitch >= THEFT_OFF_TIME:
						off = not off
						switchTime = currentTime
				else:
					value = THEFT_POWER + np.random.normal(0,THEFT_POWER_STDDEV)
					if timeSinceSwitch >= THEFT_ON_TIME:
						off = not off
						switchTime = currentTime

				writer.writerow([timestamp, value])
				currentTime = currentTime + delta

		seenMeter, seenTransformer, seenConfig = False, False, False
		for key in treeCopy:
			
			objectName = treeCopy[key].get('name','')
			objectType = treeCopy[key].get('object','')
			if objectName == CONDITION_METER:
				phases = treeCopy[key]['phases']
				voltage = treeCopy[key]['nominal_voltage']
				seenMeter = True
			elif objectName == CONDITION_TRANSFORMER:
				transformerTo = treeCopy[key]['to']
				treeCopy[key]['to'] = 'theftLoc'
				seenTransformer = True
			elif objectType == 'line_configuration':
				configuration = objectName
				seenConfig = True

			if seenMeter and seenTransformer and seenConfig:
				break

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'node',
			'name': 'theftLoc',
			'phases': phases,
			'nominal_voltage': voltage }

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'triplex_line_conductor',
			'name': 'triplexLineConductor',
			'geometric_mean_radius': 0.01111,
			'resistance': 0.97 }

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'triplex_line_configuration',
			'name': 'triplexLineonfiguration',
			'diameter': 0.368,
			'conductor_1': 'triplexLineConductor',
			'conductor_2': 'triplexLineConductor',
			'conductor_N': 'triplexLineConductor',
			'insulation_thickness': 0.08 }

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'triplex_line',
			'name': 'theftLocToMeter',
			'phases': phases,
			'from': 'theftLoc',
			'to': CONDITION_METER,
			'length': THEFT_LINE_LENGTH,
			'configuration': 'triplexLineonfiguration' }

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'class': 'player',
			'double': 'value' }

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'player',
			'file': 'theftLoad.csv',
			'property': 'value',
			'name': 'theftLoads',
			'loop': 0 }

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'triplex_load', 
			'impedance_pf_12': 1,
			'name': 'theftLoad',
			'parent': 'theftLoc',
			'phases': phases,
			'power_pf_12': 1,
			'power_fraction_12': 1,
			'impedance_fraction_12': 1,
			'nominal_voltage': voltage,
			'base_power_12': 'theftLoads.value' }
			
		
	elif condition == 'equipmentMafunction':
		# model load on meter
		
		for key in treeCopy:
			objectName = treeCopy[key].get('name','')
			if objectName == CONDITION_METER:
				phases = treeCopy[key]['phases']
				voltage = treeCopy[key]['nominal_voltage']
				break;

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'triplex_node',
			'name': 'malfunctionLoad',
			'power_12': MALFUNCTION_POWER,
			'parent': CONDITION_METER,
			'phases': phases,
			'nominal_voltage': voltage }

	return treeCopy

# load circuit ---------------------------------------------------------------------

for circuitNum in [6]:

	CIRCUIT_PATH = omfDir + CIRCUIT_PATHS[circuitNum]
	CONDITION_METER = CONDITION_METERS[circuitNum]
	CONDITION_TRANSFORMER = CONDITION_TRANSFORMERS[circuitNum]
	METER_FILENAME = METER_FILENAMES[circuitNum]
	OUTPUT_FILENAME = OUTPUT_FILENAMES[circuitNum]

	# if circuit is defined in a glm file 
	if CIRCUIT_PATH.endswith('.glm'):
		tree = feeder.parse(CIRCUIT_PATH)
		attachments = []

	# if circuit is defined in a omd file
	elif CIRCUIT_PATH.endswith('.omd'):
		omd = json.load(open(CIRCUIT_PATH))
		tree = omd.get('tree', {})
		attachments = omd.get('attachments',[])

	else: # incorrect file type
		raise Exception('Invalid input file type. We require a .glm or .omd.')

	if 'ABEC Columbia.omd' in CIRCUIT_PATH:
		loadModeling.addScaledRandomHouses(tree)


	# modify circuit to facilitate data recording ------------------------------------------

	# assume circuit doesnt have a clock for keeping time or a tape module for recording
	clockExists = False
	tapeModuleExists = False

	# go through every entry in the circuit definition
	for key in tree.keys():

		# check to see if the clock actually exists and update timings if it does
		if clockExists == False and tree[key].get('clock','') != '':
			clockExists = True
			tree[key]['starttime'] = '\"' + SIM_START_TIME + '\"'
			tree[key]['stoptime'] = '\"' + SIM_STOP_TIME + '\"'

		# check to see if the tape module actually exists
		if tapeModuleExists == False and tree[key].get('argument','') == 'tape':
			tapeModuleExists = True

	# if there is no clock, add it
	if clockExists == False:
		tree[feeder.getMaxKey(tree) + 1] = {
			'clock': 'clock',
			'timezone': TIMEZONE, 
			'starttime': '\"' + SIM_START_TIME + '\"', 
			'stoptime': '\"' + SIM_STOP_TIME + '\"',
		}

	# if there is no tape module, add it
	if tapeModuleExists == False:
		tree[feeder.getMaxKey(tree) + 1] = {'module': 'tape'}

	# add recorder object
	tree[feeder.getMaxKey(tree) + 1] = {
		'object': 'recorder', 
		'name': 'meterRecorder',
		'parent': '\"' + CONDITION_METER + '\"',
		'property': METRICS_OF_INTEREST,
		'file': METER_FILENAME,
		'interval': RECORDER_INTERVAL_SECS,
		'limit': RECORDER_LIMIT
	}

	# Run Gridlab simutlations and generate data ---------------------------------------

	print(OUTPUT_FILENAME)
	with open( OUTPUT_FILENAME, 'w' ) as outputFile:
		writer = csv.writer(outputFile, delimiter=',')

		headerCreated = False
		for condition in CONDITION_TYPES:

			treeCopy = generateTreeWithCondition( tree, condition )

			start = time.time()
			gridlabOut = gridlabd.runInFilesystem( treeCopy, 
				attachments=attachments, workDir=WORKING_DIR )
			end = time.time()
			print((end - start)/60.0)

			with open( METER_FILENAME,'r' ) as meterFile:
				reader = csv.reader(meterFile, delimiter=',')

				#loop past header
				for row in reader:
					if '# timestamp' in row:
						if headerCreated == False:
							# create header
							toWrite = ['meterID', 'timestamp']
							toWrite += row[1:]
							toWrite.append('condition')
							writer.writerow(toWrite)
							headerCreated = True
						break

				# read acctual data
				for row in reader:

					toWrite = [CONDITION_METER]
					toWrite += row
					toWrite.append(condition)
					writer.writerow(toWrite)

# ----------------------------------------------------------------------------------
print('DONE')
# ----------------------------------------------------------------------------------


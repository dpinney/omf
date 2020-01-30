# imports --------------------------------------------------------------------------

import json, csv, datetime, time, copy
from omf import omfDir, feeder
from omf.solvers import gridlabd

# user inputs ----------------------------------------------------------------------

WORKING_DIR = omfDir + '/scratch/faultLabeledMeterData'
CIRCUIT_PATH = omfDir + '/static/publicFeeders/Olin Barre GH.omd'

TIMEZONE = 'PST+8PDT'
SIM_START_TIME = '2000-01-01 00:00:00 PST'
SIM_STOP_TIME = '2000-01-02 00:00:00 PST'
CONDITION_LINE = '70924'
CONDITION_METER = 'node62463133906T62463072031'
CONDITION_TRANSFORMER = 'T62463072031'
CONDITION_TYPES = ['None', 'TLG', 'theft', 'equipmentMafunction']
# CONDITION_TYPES = [ 'None',
# 	'SLG-A', 'SLG-B', 'SLG-C', 'DLG-AB', 'DLG-BC', 'DLG-CA', 'LL-AB',
# 	'LL-BC', 'LL-CA', 'TLG', 'OC1-A', 'OC1-B', 'OC1-C', 'OC2-AB', 
# 	'OC2-BC', 'OC2-CA', 'OC3', 'theft', 'equipmentMafunction']

METER_FILENAME = 'meter.csv'
OUTPUT_FILENAME = 'data.csv'
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
	
	elif condition == 'theft':
		# model load on transformer
		
		seenMeter, seenTransformer = False, False

		for key in treeCopy:
			
			objectName = treeCopy[key].get('name','')
			if objectName == CONDITION_METER:
				phases = treeCopy[key]['phases']
				voltage = treeCopy[key]['nominal_voltage']
				seenMeter = True
			elif objectName == CONDITION_TRANSFORMER:
				transformerTo = treeCopy[key]['to']
				treeCopy[key]['to'] = 'theftLoc'
				seenTransformer = True

			if seenMeter and seenTransformer:
				break

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'node',
			'name': 'theftLoc',
			'phases': phases,
			'nominal_voltage': voltage }

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'link',
			'name': 'theftLocToMeter',
			'phases': phases,
			'from': 'theftLoc',
			'to': CONDITION_METER }

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'triplex_node',
			'name': 'theftLoad',
			'power_12': 100,
			'parent': 'theftLoc',
			'phases': phases,
			'nominal_voltage': voltage }
			
		
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
			'power_12': 100,
			'parent': objectName,
			'phases': phases,
			'nominal_voltage': voltage }
	
	else:

		# induce fault
		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'fault_check ',
			'name': 'test_fault',
			'check_mode': 'ONCHANGE',
			'eventgen_object': 'ManualEventGen',
			'output_filename': 'Fault_check_out.txt'
		}

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'power_metrics',
			'name': 'PwrMetrics',
			'base_time_value': '1 h'
		}

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'module': 'reliability',
			'maximum_event_length': 300,
			'report_event_log': 'TRUE'
		}

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'metrics',
			'name': 'RelMetrics',
			'report_file': 'Metrics_Output.csv',
			'module_metrics_object': 'PwrMetrics',
			'metrics_of_interest': '"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"',
			'customer_group': '"class=triplex_meter"',
			'metric_interval': '5 h',
			'report_interval': '5 h'
		}

		treeCopy[feeder.getMaxKey(treeCopy) + 1] = {
			'object': 'eventgen',
			'name': 'ManualEventGen',
			'parent': 'RelMetrics',
			'fault_type': '\"' + condition + '\"',
			'manual_outages': '\"' + 
				CONDITION_LINE + ',' + \
				SIM_START_TIME + ',' + \
				SIM_STOP_TIME + '\"'
		}

	return treeCopy


# load circuit ---------------------------------------------------------------------

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


# modify circuit to enable data recording ------------------------------------------

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


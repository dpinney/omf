# imports --------------------------------------------------------------------------

import json, csv, datetime
from omf import omfDir, feeder
from omf.solvers import gridlabd

# user inpots ----------------------------------------------------------------------

WORKING_DIR = omfDir + '/scratch/faultLabeledMeterData'
CIRCUIT_PATH = omfDir + '/static/publicFeeders/Olin Barre Fault.omd'

TIMEZONE = 'PST+8PDT'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
SIM_START_TIME = '2000-01-01 00:00:00 PST'
SIM_STOP_TIME = '2000-03-01 00:00:00 PST'
FAULT_START_TIME = '2000-01-01 00:00:00 PST'
FAULT_STOP_TIME = '2000-01-05 00:00:00 PST'
FAULT_METER = 'node62463133906T62463072031'
FAULT_LOCATION = '19384'
# FAULT_METER = 'node62463000348T62463000400'
# FAULT_LOCATION = '17720'
# FAULT_METER = 'node62463022720T62463022676'
# FAULT_LOCATION = '20050'
FAULT_TYPE = 'SLG-A'

RECORDER_INTERVAL_SECS = 900
RECORDER_LIMIT = 40000 

METER_FILENAME = 'meter.csv'

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


# modify circuit -------------------------------------------------------------------

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
	'parent': '\"' + FAULT_METER + '\"',
	'property': 'measured_real_power',
	'file': METER_FILENAME,
	'interval': RECORDER_INTERVAL_SECS,
	'limit': RECORDER_LIMIT
}

# add fault to circuit -------------------------------------------------------------

faultStartTime = datetime.datetime.strptime(FAULT_START_TIME[:-4], TIME_FORMAT)
faultStopTime = datetime.datetime.strptime(FAULT_STOP_TIME[:-4], TIME_FORMAT)
simStartTime = datetime.datetime.strptime(SIM_START_TIME[:-4], TIME_FORMAT)
simStopTime = datetime.datetime.strptime(SIM_STOP_TIME[:-4], TIME_FORMAT)

if (faultStopTime >= simStartTime):

	tree[feeder.getMaxKey(tree) + 1] = {
		'object': 'fault_check ',
		'name': 'test_fault',
		'check_mode': 'ONCHANGE',
		'eventgen_object': 'ManualEventGen',
		'output_filename': 'Fault_check_out.txt'
	}

	tree[feeder.getMaxKey(tree) + 1] = {
		'object': 'power_metrics',
		'name': 'PwrMetrics',
		'base_time_value': '1 h'
	}

	tree[feeder.getMaxKey(tree) + 1] = {
		'module': 'reliability',
		'maximum_event_length': 300,
		'report_event_log': 'TRUE'
	}

	tree[feeder.getMaxKey(tree) + 1] = {
		'object': 'metrics',
		'name': 'RelMetrics',
		'report_file': 'Metrics_Output.csv',
		'module_metrics_object': 'PwrMetrics',
		'metrics_of_interest': '"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"',
		'customer_group': '"class=triplex_meter"',
		'metric_interval': '5 h',
		'report_interval': '5 h'
	}

	tree[feeder.getMaxKey(tree) + 1] = {
		'object': 'eventgen',
		'name': 'ManualEventGen',
		'parent': 'RelMetrics',
		'fault_type': '\"' + FAULT_TYPE + '\"',
		'manual_outages': '\"' + 
			FAULT_LOCATION + ',' + \
			FAULT_START_TIME + ',' + \
			FAULT_STOP_TIME + '\"'
	}

# Run Gridlab ----------------------------------------------------------------------

gridlabOut = gridlabd.runInFilesystem( tree, 
	attachments=attachments, workDir=WORKING_DIR )

# Generate clean csv ---------------------------------------------------------------


with open( METER_FILENAME,'r' ) as meterFile:
	reader = csv.reader(meterFile, delimiter=',')
	with open( 'data.csv', 'w' ) as outputFile:
		writer = csv.writer(outputFile, delimiter=',')

		#loop past header
		for row in reader:
			if '# timestamp' in row:
				row.append('fault')
				row.append('meterID')
				writer.writerow(row)
				break

		# read acctual data
		for row in reader:

			timestamp = row[0][:-4]
			timestamp = datetime.datetime.strptime(timestamp, TIME_FORMAT)

			# if no fault
			if (timestamp < faultStartTime) or (timestamp > faultStopTime):
				row.append('None')
			else: # fault
				row.append(FAULT_TYPE)

			row.append(FAULT_METER)

			writer.writerow(row)

# ----------------------------------------------------------------------------------
print('DONE')
# ----------------------------------------------------------------------------------
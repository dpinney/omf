import json, omf, csv
from os.path import join as pJoin

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *

# Visualize the circuit.
#omf.distNetViz.viz('trip37.glm')

# Read it in.
tree = omf.feeder.parse('trip37.glm')
tree2 = tree.copy()

# Modify all line lengths.
for key in tree:
	if tree[key].get('object','') == 'overhead_line':
		print tree[key]['name']
		tree[key]['length'] = '5'

# Write new output.
with open('trip37tinyLines.glm','w') as outFile:
	myStr = omf.feeder.sortedWrite(tree)
	outFile.write(myStr)

# add fault object to tree
simTime='2000-01-01 0:00:00'
nodeLabs='Name'
edgeLabs=None
faultLoc='C_node744-729'
faultType='TLG'

def safeInt(x):
	try: return int(x)
	except: return 0
biggestKey = max([safeInt(x) for x in tree.keys()])
# Add Reliability module
tree[str(biggestKey*10)] = {'module':'reliability','maximum_event_length':'18000','report_event_log':'true'}
CLOCK_START = simTime
dt_start = parser.parse(CLOCK_START)
dt_end = dt_start + relativedelta(seconds=+20)
CLOCK_END = str(dt_end)
CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END
if faultType != None:
	# Add eventgen object (the fault)
	tree[str(biggestKey*10 + 1)] = {'object':'eventgen','name':'ManualEventGen','parent':'RelMetrics', 'fault_type':faultType, 'manual_outages':faultLoc + ',' + CLOCK_RANGE}
	# Add fault_check object
	tree[str(biggestKey*10 + 2)] = {'object':'fault_check','name':'test_fault','check_mode':'ONCHANGE', 'eventgen_object':'ManualEventGen', 'output_filename':'Fault_check_out.txt'}
	# Add reliabilty metrics object
	tree[str(biggestKey*10 + 3)] = {'object':'metrics', 'name':'RelMetrics', 'report_file':'Metrics_Output.csv', 'module_metrics_object':'PwrMetrics', 'metrics_of_interest':'"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"', 'customer_group':'"groupid=METERTEST"', 'metric_interval':'5 h', 'report_interval':'5 h'}
	# Add power_metrics object
	tree[str(biggestKey*10 + 4)] = {'object':'power_metrics','name':'PwrMetrics','base_time_value':'1 h'}
	
	#add meters to the tree
	index = 5
	for key in tree2:
		if tree2[key].get('object','') in ['load']:
			tree[str(biggestKey*10 + index)] = {'object':'meter','groupid':'METERTEST','phases':tree2[key]['phases'],'name':tree2[key]['name'] + ' meter' ,'nominal_voltage':tree2[key]['nominal_voltage'],'parent':tree2[key]['name']}
			index = index + 1

	# HACK: set groupid for all meters so outage stats are collected.
	noMeters = True
	for key in tree:
		if tree[key].get('object','') in ['meter', 'triplex_meter']:
			tree[key]['groupid'] = "METERTEST"
			noMeters = False
	if noMeters:
		raise Exception('No meters detected on the circuit. Please add at least one meter to allow for collection of outage statistics.')

for key in tree:
	if 'clock' in tree[key]:
		tree[key]['starttime'] = "'" + CLOCK_START + "'"
		tree[key]['stoptime'] = "'" + CLOCK_END + "'"

# dictionary to hold info on lines present in glm
edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator', 'fuse', 'switch'], False)
# Map to speed up name lookups.
nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}

# Run the .glm.
tree1 = omf.feeder.parse('trip37tinyLines.glm')
attachments = []

gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments)
	# read voltDump values into a dictionary.
try:
	dumpFile = open('trip37 xVoltDump.csv','r')
except:
	raise Exception('GridLAB-D failed to run with the following errors:\n' + gridlabOut['stderr'])

# Pulling out a mean voltage.
lines = open('trip37 xVoltDump.csv').readlines()
data = list(csv.DictReader(lines[1:]))
accum = 0
for row in data:
	phaseAvolt = complex(float(row['voltA_real']), float(row['voltA_imag']))
	accum = accum + abs(phaseAvolt)
print 'MEAN!', accum / len(data)
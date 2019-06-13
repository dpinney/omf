import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import matplotlib
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
plt.switch_backend('Agg')

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *

def recloserAnalysis(pathToGlm, lineNameForRecloser, outageGenerationStats={}):
	tree = omf.feeder.parse(pathToGlm)
	#add fault object to tree
	simTime='2000-01-01 0:00:00'
	nodeLabs='Name'
	edgeLabs=None
	faultType='TLG'
	workDir = None
	
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	# Add Reliability module
	tree[str(biggestKey*10)] = {'module':'reliability','maximum_event_length':'18000','report_event_log':'true'}
	
	CLOCK_START = simTime
	dt_start = parser.parse(CLOCK_START)
	dt_end = dt_start + relativedelta(months=+13)
	CLOCK_END = str(dt_end)
	CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END
	if faultType != None:
		# Add eventgen object (the fault)
		tree[str(biggestKey*10 + 1)] = {'object':'eventgen','name':'RandEvent','parent':'RelMetrics', 'target_group':'class=underground_line','fault_type':faultType}
		# Add fault_check object
		tree[str(biggestKey*10 + 2)] = {'object':'fault_check','name':'test_fault','check_mode':'ONCHANGE', 'eventgen_object':'RandEvent', 'output_filename':'Fault_check_out.txt'}
		# Add reliabilty metrics object
		tree[str(biggestKey*10 + 3)] = {'object':'metrics', 'name':'RelMetrics', 'report_file':'Metrics_Output.csv', 'module_metrics_object':'PwrMetrics', 'metrics_of_interest':'"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"', 'customer_group':'"groupid=METERTEST"', 'metric_interval':'0 s', 'report_interval':'1 yr'}
		# Add power_metrics object
		tree[str(biggestKey*10 + 4)] = {'object':'power_metrics','name':'PwrMetrics','base_time_value':'1 h'}
		
	
	for key in tree:
		if 'clock' in tree[key]:
			tree[key]['starttime'] = "'" + CLOCK_START + "'"
			tree[key]['stoptime'] = "'" + CLOCK_END + "'"
	
	# dictionary to hold info on lines present in glm
	edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator', 'fuse', 'switch'], False)
	# Map to speed up name lookups.
	nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}
	# Get rid of schedules and climate and check for all edge types:
	for key in tree.keys():
		obtype = tree[key].get("object","")
		if obtype == 'underground_line':
			edge_bools['underground_line'] = True
		elif obtype == 'overhead_line':
			edge_bools['overhead_line'] = True
		elif obtype == 'triplex_line':
			edge_bools['triplex_line'] = True
		elif obtype == 'transformer':
			edge_bools['transformer'] = True
		elif obtype == 'regulator':
			edge_bools['regulator'] = True
		elif obtype == 'fuse':
			edge_bools['fuse'] = True
		elif obtype == 'switch':
			edge_bools['switch'] = True
		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
			del tree[key]
	# Make sure we have a voltage dump and current dump:
	tree[str(biggestKey*10 + 5)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + 6)] = {"object":"currdump","filename":"currDump.csv"}
	
	#add meters to the tree
	index = 7
	for key in tree2:
		if tree2[key].get('object','') in ['load']:
			if 'parent' not in tree2[key]:
				tree[str(biggestKey*10 + index)] = {'object':'meter','groupid':'METERTEST','phases':tree2[key]['phases'],'name':tree2[key]['name'] + '_meter' ,'nominal_voltage':tree2[key]['nominal_voltage'],'parent':tree2[key]['name']}
				index = index + 1
	
	# HACK: set groupid for all meters so outage stats are collected.
	noMeters = True
	for key in tree:
		if tree[key].get('object','') in ['meter', 'triplex_meter']:
			tree[key]['groupid'] = "METERTEST"
			noMeters = False
	if noMeters:
		raise Exception('No meters detected on the circuit. Please add at least one meter to allow for collection of outage statistics.')
	
	# Line rating dumps
	tree[omf.feeder.getMaxKey(tree) + 1] = {
		'module': 'tape'
	}
	for key in edge_bools.keys():
		if edge_bools[key]:
			tree[omf.feeder.getMaxKey(tree) + 1] = {
				'object':'group_recorder', 
				'group':'"class='+key+'"',
				'property':'continuous_rating',
				'file':key+'_cont_rating.csv'
			}
	
	for key in tree:
		if tree[key]['name'] == lineNameForRecloser:
			tree[str(biggestKey*10 + index)] = {'object':'recloser','phases':tree[key]['phases'],'name':tree[key]['name'] + '_recloser' , 'from':tree[key]['from'], 'to':tree[key]['to'], 'retry_time': '1 s', 'max_number_of_tries': '3'}
			del tree[key]
			index = index + 1
	
	# Record initial status readout of each fuse/recloser/switch/sectionalizer before running
	# Reminder: fuse objects have 'phase_X_status' instead of 'phase_X_state'
	protDevices = dict.fromkeys(['fuse', 'recloser', 'switch', 'sectionalizer'], False)
	#dictionary of protective device initial states for each phase
	protDevInitStatus = {}
	#dictionary of protective devices final states for each phase after running Gridlab-D
	protDevFinalStatus = {}
	#dictionary of protective device types to help the testing and debugging process
	protDevTypes = {}
	protDevOpModes = {}
	for key in tree:
		obj = tree[key]
		obType = obj.get('object')
		if obType in protDevices.keys():
			obName = obj.get('name', '')
			protDevTypes[obName] = obType
			if obType != 'fuse':
				protDevOpModes[obName] = obj.get('operating_mode', 'INDIVIDUAL')
	
			protDevices[obType] = True
			protDevInitStatus[obName] = {}
			protDevFinalStatus[obName] = {}
			for phase in ['A', 'B', 'C']:
				if obType != 'fuse':
					phaseState = obj.get('phase_' + phase + '_state','CLOSED')
				else:
					phaseState = obj.get('phase_' + phase + '_status','GOOD')
				if phase in obj.get('phases', ''):
					protDevInitStatus[obName][phase] = phaseState
				#print protDevInitStatus
	
	#Create a recorder for protective device states
	for key in protDevices.keys():
		if protDevices[key]:
			for phase in ['A', 'B', 'C']:
				if key != 'fuse':
					tree[omf.feeder.getMaxKey(tree) + 1] = {
									'object':'group_recorder', 
									'group':'"class='+key+'"',
									'property':'phase_' + phase + '_state',
									'file':key + '_phase_' + phase + '_state.csv'
								}
				else:
					tree[omf.feeder.getMaxKey(tree) + 1] = {
									'object':'group_recorder', 
									'group':'"class='+key+'"',
									'property':'phase_' + phase + '_status',
									'file':key + '_phase_' + phase + '_state.csv'
								}
	
	attachments = []
	
	# Write new output.
	with open('testgrid.glm','w') as outFile:
		myStr = omf.feeder.sortedWrite(tree)
		outFile.write(myStr)
	
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)
	
	#Record final status readout of each fuse/recloser/switch/sectionalizer after running
	for key in protDevices.keys():
		if protDevices[key]:
			for phase in ['A', 'B', 'C']:
				with open(pJoin(workDir,key+'_phase_'+phase+'_state.csv'),'r') as statusFile:
					reader = csv.reader(statusFile)
					# loop past the header, 
					keys = []
					vals = []
					for row in reader:
						if '# timestamp' in row:
							keys = row
							i = keys.index('# timestamp')
							keys.pop(i)
							vals = reader.next()
							vals.pop(i)
					for pos,key2 in enumerate(keys):
						protDevFinalStatus[key2][phase] = vals[pos]
	#print protDevFinalStatus
	
	#compare initial and final states of protective devices
	#quick compare to see if they are equal
	print cmp(protDevInitStatus, protDevFinalStatus)
	#find which values changed
	changedStates = {}
	
	
	#read voltDump values into a dictionary.
	try:
		dumpFile = open(pJoin(workDir,'voltDump.csv'),'r')
	except:
		raise Exception('GridLAB-D failed to run with the following errors:\n' + gridlabOut['stderr'])
	reader = csv.reader(dumpFile)
	reader.next() # Burn the header.
	keys = reader.next()
	
	voltTable = []
	for row in reader:
		rowDict = {}
		for pos,key in enumerate(keys):
			rowDict[key] = row[pos]
		voltTable.append(rowDict)
	# read currDump values into a dictionary
	with open(pJoin(workDir,'currDump.csv'),'r') as currDumpFile:
		reader = csv.reader(currDumpFile)
		reader.next() # Burn the header.
		keys = reader.next()
		currTable = []
		for row in reader:
			rowDict = {}
			for pos,key in enumerate(keys):
				rowDict[key] = row[pos]
			currTable.append(rowDict)
	# read line rating values into a single dictionary
	lineRatings = {}
	rating_in_VA = []
	for key1 in edge_bools.keys():
		if edge_bools[key1]:		
			with open(pJoin(workDir,key1+'_cont_rating.csv'),'r') as ratingFile:
				reader = csv.reader(ratingFile)
				# loop past the header, 
				keys = []
				vals = []
				for row in reader:
					if '# timestamp' in row:
						keys = row
						i = keys.index('# timestamp')
						keys.pop(i)
						vals = reader.next()
						vals.pop(i)
				for pos,key2 in enumerate(keys):
					lineRatings[key2] = abs(float(vals[pos]))
	#edgeTupleRatings = lineRatings copy with to-from tuple as keys for labeling
	edgeTupleRatings = {}
	for edge in lineRatings:
		for obj in tree.values():
			if obj.get('name','').replace('"','') == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				ratingVal = lineRatings.get(edge)
				edgeTupleRatings[coord] = ratingVal
				# Calculate average node voltage deviation. First, helper functions.
	def digits(x):
		''' Returns number of digits before the decimal in the float x. '''
		return math.ceil(math.log10(x+1))
	def avg(l):
		''' Average of a list of ints or floats. '''
		# HACK: add a small value to the denominator to avoid divide by zero for out of service locations (i.e. zero voltage).
		return sum(l)/(len(l) + 0.00000000000000001)
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	
	#Pull out SAIDI/SAIFI values
	lines = open('Metrics_Output.csv').readlines()
	data = list(csv.DictReader(lines))
	for row in data:
		for k in row:
			if row[k].startswith('SAIFI'):
				for i in row[k].split():
					try:
						reclSAIFI = float(i)
						break
					except:
						continue
			if row[k].startswith('SAIDI'):
				for i in row[k].split():
					try:
						reclSAIDI = float(i)
						break
					except:
						continue
	return {
		'noRecl-SAIDI':1.0,
		'noRecl-SAIFI':1.0,
		'recl-SAIDI':reclSAIDI,
		'recl-SAIFI':reclSAIFI
	}

def optimalRecloserAnalysis(pathToGlm):

	tree = omf.feeder.parse(pathToGlm)
	#add fault object to tree
	simTime='2000-01-01 0:00:00'
	nodeLabs='Name'
	edgeLabs=None
	faultType='TLG'
	workDir = None
	
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	# Add Reliability module
	tree[str(biggestKey*10)] = {'module':'reliability','maximum_event_length':'18000','report_event_log':'true'}
	
	CLOCK_START = simTime
	dt_start = parser.parse(CLOCK_START)
	dt_end = dt_start + relativedelta(months=+13)
	CLOCK_END = str(dt_end)
	CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END
	if faultType != None:
		# Add eventgen object (the fault)
		tree[str(biggestKey*10 + 1)] = {'object':'eventgen','name':'RandEvent','parent':'RelMetrics', 'target_group':'class=underground_line','fault_type':faultType}
		# Add fault_check object
		tree[str(biggestKey*10 + 2)] = {'object':'fault_check','name':'test_fault','check_mode':'ONCHANGE', 'eventgen_object':'RandEvent', 'output_filename':'Fault_check_out.txt'}
		# Add reliabilty metrics object
		tree[str(biggestKey*10 + 3)] = {'object':'metrics', 'name':'RelMetrics', 'report_file':'Metrics_Output.csv', 'module_metrics_object':'PwrMetrics', 'metrics_of_interest':'"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"', 'customer_group':'"groupid=METERTEST"', 'metric_interval':'0 s', 'report_interval':'1 yr'}
		# Add power_metrics object
		tree[str(biggestKey*10 + 4)] = {'object':'power_metrics','name':'PwrMetrics','base_time_value':'1 h'}
		
	
	for key in tree:
		if 'clock' in tree[key]:
			tree[key]['starttime'] = "'" + CLOCK_START + "'"
			tree[key]['stoptime'] = "'" + CLOCK_END + "'"
	
	# dictionary to hold info on lines present in glm
	edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator', 'fuse', 'switch'], False)
	# Map to speed up name lookups.
	nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}
	# Get rid of schedules and climate and check for all edge types:
	for key in tree.keys():
		obtype = tree[key].get("object","")
		if obtype == 'underground_line':
			edge_bools['underground_line'] = True
		elif obtype == 'overhead_line':
			edge_bools['overhead_line'] = True
		elif obtype == 'triplex_line':
			edge_bools['triplex_line'] = True
		elif obtype == 'transformer':
			edge_bools['transformer'] = True
		elif obtype == 'regulator':
			edge_bools['regulator'] = True
		elif obtype == 'fuse':
			edge_bools['fuse'] = True
		elif obtype == 'switch':
			edge_bools['switch'] = True
		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
			del tree[key]
	# Make sure we have a voltage dump and current dump:
	tree[str(biggestKey*10 + 5)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + 6)] = {"object":"currdump","filename":"currDump.csv"}
	
	#add meters to the tree
	index = 7
	for key in tree2:
		if tree2[key].get('object','') in ['load']:
			if 'parent' not in tree2[key]:
				tree[str(biggestKey*10 + index)] = {'object':'meter','groupid':'METERTEST','phases':tree2[key]['phases'],'name':tree2[key]['name'] + '_meter' ,'nominal_voltage':tree2[key]['nominal_voltage'],'parent':tree2[key]['name']}
				index = index + 1
	
	# HACK: set groupid for all meters so outage stats are collected.
	noMeters = True
	for key in tree:
		if tree[key].get('object','') in ['meter', 'triplex_meter']:
			tree[key]['groupid'] = "METERTEST"
			noMeters = False
	if noMeters:
		raise Exception('No meters detected on the circuit. Please add at least one meter to allow for collection of outage statistics.')
	
	# Line rating dumps
	tree[omf.feeder.getMaxKey(tree) + 1] = {
		'module': 'tape'
	}
	for key in edge_bools.keys():
		if edge_bools[key]:
			tree[omf.feeder.getMaxKey(tree) + 1] = {
				'object':'group_recorder', 
				'group':'"class='+key+'"',
				'property':'continuous_rating',
				'file':key+'_cont_rating.csv'
			}

	bestRecloser = ''
	bestSAIDI = 5.0

	# Find the optimal recloser placement based on SAIDI values
	for key in tree2:
		if tree2[key].get('object','') in ['underground_line', 'overhead_line', 'triplex_line']:
			if 'parent' not in tree2[key]:
				tree = tree2.copy()
				tree[str(biggestKey*10 + index)] = {'object':'recloser','phases':tree2[key]['phases'],'name':tree2[key]['name'] + '_recloser' , 'from':tree2[key]['from'], 'to':tree2[key]['to'], 'retry_time': '1 s', 'max_number_of_tries': '3'}
				del tree[key]
				index = index + 1
	
				# Record initial status readout of each fuse/recloser/switch/sectionalizer before running
				# Reminder: fuse objects have 'phase_X_status' instead of 'phase_X_state'
				protDevices = dict.fromkeys(['fuse', 'recloser', 'switch', 'sectionalizer'], False)
				#dictionary of protective device initial states for each phase
				protDevInitStatus = {}
				#dictionary of protective devices final states for each phase after running Gridlab-D
				protDevFinalStatus = {}
				#dictionary of protective device types to help the testing and debugging process
				protDevTypes = {}
				protDevOpModes = {}
				for key in tree:
					obj = tree[key]
					obType = obj.get('object')
					if obType in protDevices.keys():
						obName = obj.get('name', '')
						protDevTypes[obName] = obType
						if obType != 'fuse':
							protDevOpModes[obName] = obj.get('operating_mode', 'INDIVIDUAL')
						protDevices[obType] = True
						protDevInitStatus[obName] = {}
						protDevFinalStatus[obName] = {}
						for phase in ['A', 'B', 'C']:
							if obType != 'fuse':
								phaseState = obj.get('phase_' + phase + '_state','CLOSED')
							else:
								phaseState = obj.get('phase_' + phase + '_status','GOOD')
							if phase in obj.get('phases', ''):
								protDevInitStatus[obName][phase] = phaseState
				#print protDevInitStatus
	
				#Create a recorder for protective device states
				for key in protDevices.keys():
					if protDevices[key]:
						for phase in ['A', 'B', 'C']:
							if key != 'fuse':
								tree[omf.feeder.getMaxKey(tree) + 1] = {
									'object':'group_recorder', 
									'group':'"class='+key+'"',
									'property':'phase_' + phase + '_state',
									'file':key + '_phase_' + phase + '_state.csv'
								}
							else:
								tree[omf.feeder.getMaxKey(tree) + 1] = {
									'object':'group_recorder', 
									'group':'"class='+key+'"',
									'property':'phase_' + phase + '_status',
									'file':key + '_phase_' + phase + '_state.csv'
								}
	
				attachments = []
	
				# Write new output.
				with open('testgrid.glm','w') as outFile:
					myStr = omf.feeder.sortedWrite(tree)
					outFile.write(myStr)
	
				# Run Gridlab.
				if not workDir:
					workDir = tempfile.mkdtemp()
					print '@@@@@@', workDir
				gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)
	
				#Record final status readout of each fuse/recloser/switch/sectionalizer after running
				for key in protDevices.keys():
					if protDevices[key]:
						for phase in ['A', 'B', 'C']:
							with open(pJoin(workDir,key+'_phase_'+phase+'_state.csv'),'r') as statusFile:
								reader = csv.reader(statusFile)
								# loop past the header, 
								keys = []
								vals = []
								for row in reader:
									if '# timestamp' in row:
										keys = row
										i = keys.index('# timestamp')
										keys.pop(i)
										vals = reader.next()
										vals.pop(i)
								for pos,key2 in enumerate(keys):
									protDevFinalStatus[key2][phase] = vals[pos]
				#print protDevFinalStatus
	
				#compare initial and final states of protective devices
				#quick compare to see if they are equal
				print cmp(protDevInitStatus, protDevFinalStatus)
				#find which values changed
				changedStates = {}
	

					#read voltDump values into a dictionary.
				try:
					dumpFile = open(pJoin(workDir,'voltDump.csv'),'r')
				except:
					raise Exception('GridLAB-D failed to run with the following errors:\n' + gridlabOut['stderr'])
				reader = csv.reader(dumpFile)
				reader.next() # Burn the header.
				keys = reader.next()
	
				voltTable = []
				for row in reader:
					rowDict = {}
					for pos,key in enumerate(keys):
						rowDict[key] = row[pos]
					voltTable.append(rowDict)
				# read currDump values into a dictionary
				with open(pJoin(workDir,'currDump.csv'),'r') as currDumpFile:
					reader = csv.reader(currDumpFile)
					reader.next() # Burn the header.
					keys = reader.next()
					currTable = []
					for row in reader:
						rowDict = {}
						for pos,key in enumerate(keys):
							rowDict[key] = row[pos]
						currTable.append(rowDict)
				# read line rating values into a single dictionary
				lineRatings = {}
				rating_in_VA = []
				for key1 in edge_bools.keys():
					if edge_bools[key1]:		
						with open(pJoin(workDir,key1+'_cont_rating.csv'),'r') as ratingFile:
							reader = csv.reader(ratingFile)
							# loop past the header, 
							keys = []
							vals = []
							for row in reader:
								if '# timestamp' in row:
									keys = row
									i = keys.index('# timestamp')
									keys.pop(i)
									vals = reader.next()
									vals.pop(i)
							for pos,key2 in enumerate(keys):
								lineRatings[key2] = abs(float(vals[pos]))
				#edgeTupleRatings = lineRatings copy with to-from tuple as keys for labeling
				edgeTupleRatings = {}
				for edge in lineRatings:
					for obj in tree.values():
						if obj.get('name','').replace('"','') == edge:
							nodeFrom = obj.get('from')
							nodeTo = obj.get('to')
							coord = (nodeFrom, nodeTo)
							ratingVal = lineRatings.get(edge)
							edgeTupleRatings[coord] = ratingVal
				# Calculate average node voltage deviation. First, helper functions.
				def digits(x):
					''' Returns number of digits before the decimal in the float x. '''
					return math.ceil(math.log10(x+1))
				def avg(l):
					''' Average of a list of ints or floats. '''
					# HACK: add a small value to the denominator to avoid divide by zero for out of service locations (i.e. zero voltage).
					return sum(l)/(len(l) + 0.00000000000000001)
				# Detect the feeder nominal voltage:
				for key in tree:
					ob = tree[key]
					if type(ob)==dict and ob.get('bustype','')=='SWING':
						feedVoltage = float(ob.get('nominal_voltage',1))
	
				#Pull out SAIDI value
				lines = open('Metrics_Output.csv').readlines()
				data = list(csv.DictReader(lines))
				for row in data:
					for k in row:
						if row[k].startswith('SAIFI = '):
							for i in row[k].split():
								try:
									reclSAIFI = float(i)
									break
								except:
									continue
						if row[k].startswith('SAIDI'):
							for i in row[k].split():
								try:
									reclSAIDI = float(i)
									break
								except:
									continue
				if bestSAIDI > reclSAIDI:
					bestSAIDI = reclSAIDI
					bestRecloser = tree[key]['name']
	return{
		'bestSAIDI': bestSAIDI
	}

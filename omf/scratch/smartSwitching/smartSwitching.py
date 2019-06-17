import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.offline as pyo
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


def recloserAnalysis(pathToGlm, lineNameForRecloser, failureDistribution, restorationDistribution):
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
		tree[str(biggestKey*10 + 1)] = {'object':'eventgen','name':'RandEvent','parent':'RelMetrics', 'target_group':'class=underground_line','fault_type':faultType, 'failure_dist':failureDistribution, 'restoration_dist':restorationDistribution}
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
	
	tree[str(biggestKey*10 + 5)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + 6)] = {"object":"currdump","filename":"currDump.csv"}
	
	tree2 = tree.copy()
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

	attachments = []
	
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

	#Pull out SAIDI/SAIFI values
	with open(workDir + '\Metrics_Output.csv', 'rb') as csvfile:
		file = csv.reader(csvfile)
		for line in file:
			k = 0
			while k < len(line):
				if 'SAIFI' in line[k]:
					for i in line[k].split():
						try:
							noReclSAIFI = float(i)
							break
						except:
							continue
				if 'SAIDI' in line[k]:
					for i in line[k].split():
						try:
							noReclSAIDI = float(i)
							break
						except:
							continue
				k += 1

	#add a recloser
	for key in tree:
		if tree[key].get('name', '') == lineNameForRecloser:
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

	#Pull out SAIDI/SAIFI values
	with open(workDir + '\Metrics_Output.csv', 'rb') as csvfile:
		file = csv.reader(csvfile)
		for line in file:
			k = 0
			while k < len(line):
				if 'SAIFI' in line[k]:
					for i in line[k].split():
						try:
							reclSAIFI = float(i)
							break
						except:
							continue
				if 'SAIDI' in line[k]:
					for i in line[k].split():
						try:
							reclSAIDI = float(i)
							break
						except:
							continue
				k += 1
	return {
		'noRecl-SAIDI':noReclSAIDI,
		'noRecl-SAIFI':noReclSAIFI,
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
	
	tree2 = tree.copy()
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


	attachments = []
	
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

	#Pull out SAIDI/SAIFI values
	with open(workDir + '\Metrics_Output.csv', 'rb') as csvfile:
		file = csv.reader(csvfile)
		for line in file:
			k = 0
			while k < len(line):
				if 'SAIFI' in line[k]:
					for i in line[k].split():
						try:
							noReclSAIFI = float(i)
							break
						except:
							continue
				if 'SAIDI' in line[k]:
					for i in line[k].split():
						try:
							noReclSAIDI = float(i)
							break
						except:
							continue
				k += 1

	bestSAIDI = 5.0
	bestSAIFI = 5.0
	bestSAIDI_name = ''
	bestSAIFI_name = ''

	tree2 = tree.copy()
	# Find the optimal recloser placement based on SAIDI values
	for key in tree2:
		if tree2[key].get('object','') in ['underground_line', 'overhead_line', 'triplex_line']:
			if 'parent' not in tree2[key]:
				tree = tree2.copy()
				tree[str(biggestKey*10 + index)] = {'object':'recloser','phases':tree2[key]['phases'],'name':tree2[key]['name'] + '_recloser' , 'from':tree2[key]['from'], 'to':tree2[key]['to'], 'retry_time': '1 s', 'max_number_of_tries': '3'}
				SAIDI_name = tree2[key]['name']
				SAIFI_name = tree2[key]['name']
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
	
				#Pull out SAIDI/SAIFI values
				with open(workDir + '\Metrics_Output.csv', 'rb') as csvfile:
					file = csv.reader(csvfile)
					for line in file:
						k = 0
						while k < len(line):
							if 'SAIFI' in line[k]:
								for i in line[k].split():
									try:
										reclSAIFI = float(i)
										break
									except:
										continue
							if 'SAIDI' in line[k]:
								for i in line[k].split():
									try:
										reclSAIDI = float(i)
										break
									except:
										continue
							k += 1
				if bestSAIDI > reclSAIDI:
					bestSAIDI = reclSAIDI
					for key in tree:
						if tree[key].get('object','') in 'recloser':
							bestSAIDI_name = SAIDI_name
				if bestSAIFI > reclSAIFI:
					bestSAIFI = reclSAIFI
					for key in tree:
						if tree[key].get('object', '') in 'recloser':
							bestSAIFI_name = SAIFI_name
	return {
		'noRecl-SAIDI': noReclSAIDI,
		'bestSAIDI': bestSAIDI,
		'bestSAIDI_name': bestSAIDI_name,
		'noRecl-SAIFI': noReclSAIFI,
		'bestSAIFI': bestSAIFI,
		'bestSAIFI_name': bestSAIFI_name
	}

test1 = recloserAnalysis(omf.omfDir + '/scratch/CIGAR/' + 'test_ieee37nodeFaultTester.glm', 'node709-708', 'EXPONENTIAL', 'PARETO')
print(test1)
row = test1.keys()
col = test1.values()
#data = [go.Bar(x = row, y = col)]
#py.iplot(data, filename='metrics_of_interest')
plt.bar(row, col)
plt.show()
plt.savefig('metrics.png')


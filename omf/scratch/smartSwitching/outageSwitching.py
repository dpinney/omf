import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
import scipy.stats as stats
from plotly import tools
import plotly as py
import json
import plotly.graph_objs as go
import plotly.figure_factory as ff
from plotly.tools import make_subplots
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
import itertools as it
from shutil import copyfile
from __neoMetaModel__ import *
from omf.models import __neoMetaModel__
import random

# OMF imports
import omf.feeder as feeder
from omf.solvers import gridlabd

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *

# Model metadata:
tooltip = "smartSwitching gives the expected reliability improvement from adding reclosers to a circuit."
modelName, template = metadata(__file__)
hidden = False

def pullOutValues(tree, workDir, sustainedOutageThreshold):
	'helper function which pulls out reliability metric data (SAIDI/SAIFI).'
	attachments = []
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

	#Pull out number of customers
	numberOfCustomers = 0.0
	with open(workDir + '/Metrics_Output.csv', 'rb') as csvfile:
		file = csv.reader(csvfile)
		for line in file:
			k = 0
			while k < len(line):
				if 'Number of customers' in line[k]:
					for i in line[k].split():
						try:
							numberOfCustomers = float(i)
							break
						except:
							continue
		# old way of finding SAIDI/SAIFI... manual calculation is better as it allows an input of threshold for sustained outage 
				#if 'SAIFI' in line[k]:
				#	for i in line[k].split():
				#		try:
				#			SAIFI_returned = float(i)
				#			break
				#		except:
				#			continue
				#if 'SAIDI' in line[k]:
				#	for i in line[k].split():
				#		try:
				#			SAIDI_returned = float(i)
				#			break
				#		except:
				#			continue
				k += 1

	def get_footer(file_):
		'helper function returning the length of a variable footer'
		with open(file_) as f:
			g = it.dropwhile(lambda x: 'SAIFI' not in x, f)
			footer_len = len([i for i, _ in enumerate(g)])
		return footer_len

	# return the Metrics_Output fault data for a year, without any extra data in a cvs format
	footer_len = get_footer(workDir + '/Metrics_Output.csv')
	row_count = sum(1 for row in csv.reader(open(workDir + '/Metrics_Output.csv'))) - footer_len - 8
	mc = pd.read_csv(workDir + '/Metrics_Output.csv', skiprows=6, nrows=row_count)
	mc = mc.rename(columns={'Metric Interval Event #': 'Task', 'Starting DateTime (YYYY-MM-DD hh:mm:ss)': 'Start', 'Ending DateTime (YYYY-MM-DD hh:mm:ss)': 'Finish'})

	# find SAIDI/SAIFI/MAIFI measures by calculating manually based on a given sustained outage threshold
	SAIDI_returned, SAIFI_returned, MAIFI_returned = manualOutageStats(numberOfCustomers, mc, sustainedOutageThreshold)

	return numberOfCustomers, SAIFI_returned, SAIDI_returned, MAIFI_returned, mc

def manualOutageStats(numberOfCustomers, mc_orig, sustainedOutageThreshold):
	'function which manually computes outage stats given a threshold for a sustained outage'
	# copy DataFrame so original object remains unchanged
	mc = pd.DataFrame.copy(mc_orig, deep=True)

	# calculate SAIDI
	customerInterruptionDurations = 0.0
	row = 0
	row_count_mc = mc.shape[0]
	while row < row_count_mc:
		if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) > int(sustainedOutageThreshold):
			customerInterruptionDurations += (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) * int(mc.loc[row, 'Number customers affected']) / 3600
		row += 1

	SAIDI = customerInterruptionDurations / numberOfCustomers

	# calculate SAIFI
	row = 0
	totalInterruptions = 0.0
	customersAffected = 0
	while row < row_count_mc:
		if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) > int(sustainedOutageThreshold):
			customersAffected += int(mc.loc[row, 'Number customers affected'])
		row += 1
	SAIFI = float(customersAffected) / numberOfCustomers

	# calculate CAIDI
	CAIDI = SAIDI / SAIFI

	# calculate ASAI
	ASAI = (numberOfCustomers * 8760 - customerInterruptionDurations) / (numberOfCustomers * 8760)

	# calculate MAIFI
	sumCustomersAffected = 0.0
	row = 0
	while row < row_count_mc:
		if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) <= int(sustainedOutageThreshold):
			sumCustomersAffected += int(mc.loc[row, 'Number customers affected'])
		row += 1

	MAIFI = sumCustomersAffected / numberOfCustomers

	return SAIDI, SAIFI, MAIFI


def setupSystem(pathToGlm, pathToCsv, workDir, lineNameForRecloser, simTime, faultType):
	'helper function to set-up reliability module on a glm given its path'
	tree = omf.feeder.parse(pathToGlm)
	mc = pd.read_csv(pathToCsv)
	
	#add fault object to tree
	nodeLabs='Name'
	edgeLabs=None

	def safeInt(x):
		try: return int(x)
		except: return 0

	biggestKey = max([safeInt(x) for x in tree.keys()])
	smallestKey = min(tree, key=tree.get)
	currentKey = smallestKey
	while tree.get(str(currentKey)) != None:
		currentKey += 1
	seed = np.random.randint(1,1000)
	tree[str(currentKey)] = {'omftype': '#set', 'argument': 'randomseed=' + str(seed)}

	# Add Reliability module
	tree[str(biggestKey*10)] = {'module':'reliability','maximum_event_length':'18000','report_event_log':'true'}
	
	CLOCK_START = simTime
	dt_start = parser.parse(CLOCK_START)
	dt_end = dt_start + relativedelta(months=+12, weeks=+1, day=0, hour=0, minute=0, second=0)
	CLOCK_END = str(dt_end)
	CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END
	index = 1
	if faultType != None:
		
		row_count_mc = mc.shape[0]
		
		index = 1
		row = 0
		while row < row_count_mc:
			
			#if (datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S').month == 1):
			if (str(mc.loc[row, 'Object Name']) != lineNameForRecloser):
				manualOutages = ''
				manualOutages += str(mc.loc[row, 'Object Name'])
				manualOutages += ', '
				#print(str(mc.loc[row, 'Start']))
				manualOutages += str(mc.loc[row, 'Start'])
				manualOutages += ', '
				#print(str(mc.loc[row, 'Finish']))
				manualOutages += str(mc.loc[row, 'Finish'])
				tree[str(biggestKey*10 + index)] = {'object':'eventgen','name':'ManualEventGen_' + str(index),'parent':'RelMetrics','fault_type':faultType, "manual_outages": '"' + manualOutages + '"'}
				index += 1
			row += 1

		# Add eventgen object (the fault)
		
		# Add fault_check object
		tree[str(biggestKey*10 + index + 1)] = {'object':'fault_check','name':'test_fault','check_mode':'ONCHANGE', 'eventgen_object':'ManualEventGen_1', 'output_filename':'Fault_check_out.txt', 'strictly_radial': 'true'}
		# Add reliabilty metrics object
		tree[str(biggestKey*10 + index + 2)] = {'object':'metrics', 'name':'RelMetrics', 'report_file':'Metrics_Output.csv', 'module_metrics_object':'PwrMetrics', 'metrics_of_interest':'"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"', 'customer_group':'"groupid=METERTEST"', 'metric_interval':'0 s', 'report_interval':'1 yr'}
		# Add power_metrics object
		tree[str(biggestKey*10 + index + 3)] = {'object':'power_metrics','name':'PwrMetrics','base_time_value':'1 h'}
		with open('result.json', 'w') as fp:
			json.dump(tree, fp)
		tree2 = tree.copy()

		#add meters to the tree
		index = 7 + index
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
			raise Exception("No meters detected on the circuit. Please add at least one meter to allow for collection of outage statistics.")
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
		if tree[key].get("argument","") == '"schedules.glm"' or tree[key].get("tmyfile","") != "":
			del tree[key]
	
	# create volt and current line dumps for debugging purposes
	tree[str(biggestKey*10 + index + 1)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + index + 2)] = {"object":"currdump","filename":"currDump.csv"}
	
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

	#Record initial status readout of each fuse/recloser/switch/sectionalizer before running
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

	
	return tree, workDir, biggestKey, index

def protection(tree):
	'create dictionary of protective devices'
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
	return tree

def recloserAnalysis(pathToGlm, pathToCsv, workDir, lineNameForRecloser, simTime, faultType, sustainedOutageThreshold):
	'function that returns a .csv of the random faults generated and the SAIDI/SAIFI values for a given glm, line for recloser, and distribution data'
	
	tree1, workDir, biggestKey, index = setupSystem(pathToGlm, pathToCsv, workDir, lineNameForRecloser, simTime, faultType)

	tree1 = protection(tree1)

	numberOfCustomers, noReclSAIFI, noReclSAIDI, noReclMAIFI, mc1 = pullOutValues(tree1, workDir, sustainedOutageThreshold)
	
	tree, workDir, biggestKey, index = setupSystem(pathToGlm, pathToCsv, workDir, lineNameForRecloser, simTime, faultType)

	#add a recloser
	for key in tree:
		if tree[key].get('name', '') == lineNameForRecloser:
			tree[str(biggestKey*10 + index)] = {'object':'recloser','phases':tree[key]['phases'],'name':tree[key]['name'] + '_addedRecloser' , 'from':tree[key]['from'], 'to':tree[key]['to'], 'retry_time': '1 s', 'max_number_of_tries': '3'}
			del tree[key]
			index = index + 1
	
	tree = protection(tree)
	
	numberOfCustomers, reclSAIFI, reclSAIDI, reclMAIFI, mc2 = pullOutValues(tree, workDir, sustainedOutageThreshold)
	
	return numberOfCustomers, mc1, mc2, tree, {
		'noRecl-SAIDI':noReclSAIDI,
		'noRecl-SAIFI':noReclSAIFI,
		'recl-SAIDI':reclSAIDI,
		'recl-SAIFI':reclSAIFI
		
	}, {
		'noRecl-MAIFI':noReclMAIFI,
		'recl-MAIFI':reclMAIFI
	}

def datetime_to_float(d):
	'helper function which convert a datetime object to a float'
	epoch = datetime.datetime.utcfromtimestamp(0)
	total_seconds = (d - epoch).total_seconds()
	return total_seconds

def valueOfAdditionalRecloser(pathToGlm, pathToCsv, workDir, lineNameForRecloser, kwh_cost, restoration_cost, average_hardware_cost, simTime, faultType, sustainedOutageThreshold):
	'analyzes the value of adding an additional recloser to a feeder system'

	# check to see if work directory is specified
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	
	# perform analyses on the glm
	numberOfCustomers, mc1, mc2, tree1, test1, test2 = recloserAnalysis(pathToGlm, pathToCsv, workDir, lineNameForRecloser, simTime, faultType, sustainedOutageThreshold)

	# Find SAIDI/SAIFI/MAIFI manually from Metrics_Output
	manualNoReclSAIDI, manualNoReclSAIFI, manualNoReclMAIFI = manualOutageStats(numberOfCustomers, mc1, sustainedOutageThreshold)
	manualReclSAIDI, manualReclSAIFI, manualReclMAIFI = manualOutageStats(numberOfCustomers, mc2, sustainedOutageThreshold)

	# calculate average consumption over the feeder system given meter data
	numberOfMeters = 0
	sumOfVoltages = 0.0
	for key in tree1:
		if tree1[key].get('object','') in ['meter', 'triplex_meter']:
			numberOfMeters += 1
			sumOfVoltages += float(tree1[key]['nominal_voltage'])
	average_consumption = sumOfVoltages/numberOfMeters

	# Calculate initial and final outage costs
	# calculate customer costs
	initialCustomerCost = int(test1.get('noRecl-SAIDI')*numberOfCustomers*float(average_consumption))
	finalCustomerCost = int(test1.get('recl-SAIDI')*numberOfCustomers*float(average_consumption))

	# calculate restoration costs
	initialDuration = 0.0
	finalDuration = 0.0
	row = 0
	row_count_mc1 = mc1.shape[0]
	row_count_mc2 = mc2.shape[0]
	while row < row_count_mc1:
		initialDuration +=  datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
		row = row + 1
	row = 0
	while row < row_count_mc2:
		finalDuration +=  datetime_to_float(datetime.datetime.strptime(mc2.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc2.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
		row = row + 1

	initialRestorationCost = int(initialDuration*float(restoration_cost))
	finalRestorationCost = int(finalDuration*float(restoration_cost))

	# calculate hardware costs
	initialHardwareCost = int(row_count_mc1 * float(average_hardware_cost))
	finalHardwareCost = int(row_count_mc2 * float(average_hardware_cost))

	# put it all together and calculate outage costs
	initialOutageCost = initialCustomerCost + initialRestorationCost + initialHardwareCost
	finalOutageCost = finalCustomerCost + finalRestorationCost + finalHardwareCost

	def costStatsCalc(initCustCost=None, finCustCost=None, initRestCost=None, finRestCost=None, initHardCost=None, finHardCost=None, initOutCost=None, finOutCost=None):
		new_html_str = """
			<table cellpadding="0" cellspacing="0">
				<thead>
					<tr>
						<th></th>
						<th>No-Recloser</th>
						<th>Recloser</th>
					</tr>
				</thead>
				<tbody>"""
		new_html_str += "<tr><td><b>Lost kWh Sales</b></td><td>"+str(initCustCost)+"</td><td>"+str(finCustCost)+"</td></tr>"
		new_html_str += "<tr><td><b>Restoration Labor Cost</b></td><td>"+str(initRestCost)+"</td><td>"+str(finRestCost)+"</td></tr>"
		new_html_str += "<tr><td><b>Restoration Hardware Cost</b></td><td>"+str(initHardCost)+"</td><td>"+str(finHardCost)+"</td></tr>"
		new_html_str += "<tr><td><b>Outage Cost</b></td><td>"+str(initOutCost)+"</td><td>"+str(finOutCost)+"</td></tr>"
		new_html_str +="""</tbody></table>"""

		return new_html_str


	# print all intermediate and final costs
	costStatsHtml = costStatsCalc(
		initCustCost = initialCustomerCost,
		finCustCost = finalCustomerCost,
		initRestCost = initialRestorationCost,
		finRestCost = finalRestorationCost,
		initHardCost = initialHardwareCost,
		finHardCost = finalHardwareCost,
		initOutCost = initialOutageCost,
		finOutCost = finalOutageCost)
	with open(pJoin(workDir, "costStatsCalc.html"), "w") as costFile:
		costFile.write(costStatsHtml)

	# bar chart to show change in SAIDI/SAIFI values
	row1 = sorted(test1)
	col1 = [value for (key, value) in sorted(test1.items())]
	dataSaidi = go.Bar(x = row1, y = col1, name = 'SAIDI SAIFI Recloser Analysis')

	# bar chart to show change in MAIFI values
	row2 = sorted(test2)
	col2 = [value for (key, value) in sorted(test2.items())]
	dataMaifi = go.Bar(x = row2, y = col2, name = 'MAIFI Recloser Analysis')

	fig1 = make_subplots(rows=1, cols=2)

	fig1.add_trace(dataSaidi, row=1, col=1)
	fig1.add_trace(dataMaifi, row=1, col=2)
	fig1.layout.update(showlegend=False)

	# stacked bar chart to show outage timeline without the recloser
	row = 0
	date = [[] for _ in range(365)]
	row_count_mc1 = mc1.shape[0]
	while row < row_count_mc1:
		dt = datetime.datetime.strptime(mc1.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')
		day = int(dt.strftime('%j')) - 1
		date[day].append(datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S')))
		row += 1
	# convert array of durations into jagged numpy object
	jaggedData = np.array(date)
	# get lengths of each row of data
	lens = np.array([len(i) for i in jaggedData])
	# mask of valid places in each row to fill with zeros
	mask = np.arange(lens.max()) < lens[:,None]
	# setup output array and put elements from jaggedData into masked positions
	data = np.zeros(mask.shape, dtype=jaggedData.dtype)
	data[mask] = np.concatenate(jaggedData)
	numCols = data.shape[1]
	graphData = []
	currCol = 0
	while currCol < numCols:
		graphData.append(go.Bar(name='Fault ' + str(currCol+1), x = list(range(365)), y = data[:,currCol]))
		currCol += 1
	fig3 = go.Figure(data = graphData)
	fig3.layout.update(
		barmode='stack',
		showlegend=False,
		xaxis=go.layout.XAxis(
			title=go.layout.xaxis.Title(text='Day of the year')
		),
		yaxis=go.layout.YAxis(
			title=go.layout.yaxis.Title(text='Outage time (seconds)')
		)
	)

	# feeder chart with recloser
	outGraph = nx.Graph()
	for key in tree1:
		item = tree1[key]
		if 'name' in item.keys():
			obType = item.get('object')
			reclDevices = dict.fromkeys(['recloser'], False)
			if (obType in reclDevices.keys() and 'addedRecloser' in item.get('name', '')):
				# HACK: set the recloser as a swingNode in order to make it hot pink
				outGraph.add_edge(item['from'],item['to'], attr_dict={'type':'swingNode'})
			elif (obType in reclDevices.keys() and 'addedRecloser' not in item.get('name','')):
				outGraph.add_edge(item['from'],item['to'])
			elif 'parent' in item.keys() and obType not in reclDevices:
				outGraph.add_edge(item['name'],item['parent'], attr_dict={'type':'parentChild','phases':1})
				outGraph.node[item['name']]['type']=item['object']
				# Note that attached houses via gridEdit.html won't have lat/lon values, so this try is a workaround.
				try: outGraph.node[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
				except: outGraph.node[item['name']]['pos']=(0.0,0.0)
			elif 'from' in item.keys():
				myPhase = feeder._phaseCount(item.get('phases','AN'))
				outGraph.add_edge(item['from'],item['to'],attr_dict={'name':item.get('name',''),'type':item['object'],'phases':myPhase})
			elif item['name'] in outGraph:
				# Edge already led to node's addition, so just set the attributes:
				outGraph.node[item['name']]['type']=item['object']
			else:
				outGraph.add_node(item['name'],attr_dict={'type':item['object']})
			if 'latitude' in item.keys() and 'longitude' in item.keys():
				try: outGraph.node.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
				except: outGraph.node.get(item['name'],{})['pos']=(0.0,0.0)
	feeder.latLonNxGraph(outGraph, labels=True, neatoLayout=True, showPlot=True)
	plt.savefig(workDir + '/feeder_chart')
	return {'costStatsHtml': costStatsHtml, 'fig1': fig1, 'fig3': fig3}

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}
	# Write the feeder
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	omf.feeder.omdToGlm(modelDir + '/' + feederName + '.omd', modelDir)
	#test the main functions of the program
	with open(pJoin(modelDir, inputDict['outageFileName']), 'w') as f:
		pathToData = f.name
		f.write(inputDict['outageData'])
	plotOuts = valueOfAdditionalRecloser(
		modelDir + '/' + feederName + '.glm', #GLM Path
		pathToData,
		modelDir, #Work directory.
		inputDict['recloserLocation'],
		inputDict['kwh_cost'], #'1'
		inputDict['restoration_cost'], #'1',
		inputDict['average_hardware_cost'], #'1',
		inputDict['simTime'], #'2000-01-01 0:00:00',
		inputDict['faultType'], #'TLG',
		inputDict['sustainedOutageThreshold']) #'300')
	#bestLocationForRecloser(omf.omfDir + '/scratch/CIGAR/test_ieee37nodeFaultTester.glm', None, 'underground_line', 'node709-708', 'EXPONENTIAL', '3.858e-7', '0.0', 'PARETO', '1.0', '1.0002778', '432000 s', '2000-01-01 0:00:00', 'TLG', '300')
	
	# Textual outputs of cost statistic
	with open(pJoin(modelDir,"costStatsCalc.html"),"rb") as inFile:
		outData["costStatsHtml"] = inFile.read()
	
	# Image outputs.
	with open(pJoin(modelDir,"feeder_chart.png"),"rb") as inFile:
		outData["feeder_chart.png"] = inFile.read().encode("base64")
	
	# Plotly outputs.
	layoutOb = go.Layout()
	outData["fig1Data"] = json.dumps(plotOuts.get('fig1',{}), cls=py.utils.PlotlyJSONEncoder)
	outData["fig1Layout"] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData["fig3Data"] = json.dumps(plotOuts.get('fig3',{}), cls=py.utils.PlotlyJSONEncoder)
	outData["fig3Layout"] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)

	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"feederName1": "ieee37nodeFaultTester",
		"recloserLocation": "node730-709",
		'kwh_cost': '1',
		'restoration_cost': '1',
		'average_hardware_cost': '1',
		'simTime': '2000-01-01 0:00:00',
		'faultType': 'TLG',
		'sustainedOutageThreshold': '60',
		"outageFileName": "outagesNew4.csv",
		"outageData": open(pJoin(__neoMetaModel__._omfDir,"scratch","smartSwitching","outagesNew4.csv"), "r").read(),
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import dates as dt
import matplotlib
import scipy.stats as stats
from plotly import tools
import plotly as py
import plotly.graph_objs as go
import plotly.figure_factory as ff
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
import time
from shutil import copyfile
from omf.models import __neoMetaModel__
from omf.models import voltageDrop as vd
from __neoMetaModel__ import *

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *

# helper function to pull out reliability metric data (SAIDI/SAIFI) 
def pullOutValues(tree, workDir):
	numberOfCustomers = 0.0
	SAIFI_returned = 0.0
	SAIDI_returned = 0.0
	attachments = []
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

	#Pull out SAIDI/SAIFI values and number of customers
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
				if 'SAIFI' in line[k]:
					for i in line[k].split():
						try:
							SAIFI_returned = float(i)
							break
						except:
							continue
				if 'SAIDI' in line[k]:
					for i in line[k].split():
						try:
							SAIDI_returned = float(i)
							break
						except:
							continue
				k += 1
	mc = pd.read_csv(workDir + '/Metrics_Output.csv', skiprows=6, nrows=400)
	mc = mc.rename(columns={'Metric Interval Event #': 'Task', 'Starting DateTime (YYYY-MM-DD hh:mm:ss)': 'Start', 'Ending DateTime (YYYY-MM-DD hh:mm:ss)': 'Finish'})
	return numberOfCustomers, SAIFI_returned, SAIDI_returned, mc

# helper function to set-up reliability module on a glm given its path
def setupSystem(pathToGlm, workDir, lineFaultType, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType):
	tree = omf.feeder.parse(pathToGlm)
	#add fault object to tree
	nodeLabs='Name'
	edgeLabs=None

	def safeInt(x):
		try: return int(x)
		except: return 0

	#seedKey = max([safeInt(x) for x in tree.keys()])
	#tree[str(seedKey*10)] = {'omftype': '#set', 'argument': 'randomseed=5'}

	biggestKey = max([safeInt(x) for x in tree.keys()])
	# Add Reliability module
	tree[str(biggestKey*10)] = {'module':'reliability','maximum_event_length':'18000','report_event_log':'true'}
	
	CLOCK_START = simTime
	dt_start = parser.parse(CLOCK_START)
	dt_end = dt_start + relativedelta(months=+12, weeks=+0, day=0, hour=0, minute=0, second=0)
	CLOCK_END = str(dt_end)
	CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END
	if faultType != None:
		# Add eventgen object (the fault)
		tree[str(biggestKey*10 + 1)] = {'object':'eventgen','name':'RandEvent','parent':'RelMetrics', 'target_group':'class=' + lineFaultType,'fault_type':faultType, 'failure_dist':failureDistribution, 'restoration_dist':restorationDistribution, 'failure_dist_param_1':failure_1, 'failure_dist_param_2':failure_2, 'restoration_dist_param_1':rest_1, 'restoration_dist_param_2':rest_2, 'max_outage_length':maxOutageLength}
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
		if tree[key].get("argument","") == '"schedules.glm"' or tree[key].get("tmyfile","") != "":
			del tree[key]
	
	# create volt and current line dumps for debugging purposes
	tree[str(biggestKey*10 + 5)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + 6)] = {"object":"currdump","filename":"currDump.csv"}

	tree[str(biggestKey*10 + 7)] = {'#set randomseed=5':''}
	
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
	
	return tree, workDir, biggestKey, index

# create dictionary of protective devices
def protection(tree):
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
	return tree

# function that returns a .csv of the random faults generated and the SAIDI/SAIFI values for a given glm, line for recloser, and distribution data
def recloserAnalysis(pathToGlm, workDir, lineFaultType, lineNameForRecloser, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType):
	
	tree, workDir, biggestKey, index = setupSystem(pathToGlm, workDir, lineFaultType, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType)

	numberOfCustomers, noReclSAIFI, noReclSAIDI, mc1 = pullOutValues(tree, workDir)
	
	#add a recloser
	for key in tree:
		if tree[key].get('name', '') == lineNameForRecloser:
			tree[str(biggestKey*10 + index)] = {'object':'recloser','phases':tree[key]['phases'],'name':tree[key]['name'] + '_recloser' , 'from':tree[key]['from'], 'to':tree[key]['to'], 'retry_time': '1 s', 'max_number_of_tries': '3'}
			del tree[key]
			index = index + 1
	
	tree = protection(tree)
	
	numberOfCustomers, reclSAIFI, reclSAIDI, mc2 = pullOutValues(tree, workDir)

	return numberOfCustomers, mc1, mc2, tree, {
		'noRecl-SAIDI':noReclSAIDI,
		'noRecl-SAIFI':noReclSAIFI,
		'recl-SAIDI':reclSAIDI,
		'recl-SAIFI':reclSAIFI
	}
	distributiongraph(failureDistribution, failure_1, failure_2, 'failure distribution')

# function that finds the optimal placement for an additional recloser
#WARNING: time-intensive
def optimalRecloserAnalysis(pathToGlm, workDir, lineFaultType, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType):

	tree, workDir, biggestKey, index = setupSystem(pathToGlm, workDir, lineFaultType, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType)

	numberOfCustomers, noReclSAIFI, noReclSAIDI, mc = pullOutValues(tree, workDir)

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
	
				tree = protection(tree)
	
				numberOfCustomers, reclSAIFI, reclSAIDI, mc = pullOutValues(tree, workDir)

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
	return bestSAIDI_name, bestSAIFI_name, tree, {
		'noRecl-SAIDI': noReclSAIDI,
		'noRecl-SAIFI': noReclSAIFI,
		'recl-SAIDI': bestSAIDI,
		'recl-SAIFI': bestSAIFI
	}

# finds the best location for a new recloser in a feeder system
# WARNING: takes a lot of time to run
def bestLocationForRecloser(pathToGlm, workDir, lineFaultType, lineNameForRecloser, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType):
	numberOfCustomers, mc1, mc2, tree1, test1 = recloserAnalysis(pathToGlm, workDir, lineFaultType, lineNameForRecloser, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType)
	row1 = sorted(test1)
	col1 = [value for (key, value) in sorted(test1.items())]
	trace1 = go.Bar(x = row1, y = col1, name = 'Recloser Analysis')

	bestSAIDI, bestSAIFI, tree2, test2 = optimalRecloserAnalysis(pathToGlm, workDir, lineFaultType, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType)
	row2 = sorted(test2)
	col2 = [value for (key, value) in sorted(test2.items())]
	trace2 = go.Bar(x = row2, y = col2, name= 'Optimal Recloser Analysis')

	print('Best location based on SAIDI = ' + str(bestSAIDI))
	print('Best location based on SAIFI = ' + str(bestSAIFI))

	data = [trace1, trace2]
	layout = go.Layout(barmode='group', title='SAIDI/SAIFI Analysis')
	figure = go.Figure(data=data, layout=layout)
	py.offline.plot(figure, filename='best_location_for_recloser', auto_open=False)

# helper function to convert a datetime object to a float
def datetime_to_float(d):
	epoch = datetime.datetime.utcfromtimestamp(0)
	total_seconds = (d - epoch).total_seconds()
	return total_seconds

# analyzes the value of adding an additional recloser to a feeder system
def valueOfAdditionalRecloser(pathToGlm, workDir, lineFaultType, lineNameForRecloser, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, average_consumption, kwh_cost, restoration_cost, average_hardware_cost, simTime, faultType):
	numberOfCustomers, mc1, mc2, tree1, test1 = recloserAnalysis(pathToGlm, workDir, lineFaultType, lineNameForRecloser, failureDistribution, failure_1, failure_2, restorationDistribution, rest_1, rest_2, maxOutageLength, simTime, faultType)
	
	# Calculate initial and final outage costs
	initialCustomerCost = test1.get('noRecl-SAIDI')*numberOfCustomers*float(average_consumption)
	finalCustomerCost = test1.get('recl-SAIDI')*numberOfCustomers*float(average_consumption)

	initialDuration = 0.0
	finalDuration = 0.0
	row = 0
	while row < 400:
		initialDuration +=  datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
		finalDuration +=  datetime_to_float(datetime.datetime.strptime(mc2.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc2.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
		row = row + 1

	initialRestorationCost = initialDuration*float(restoration_cost)
	finalRestorationCost = finalDuration*float(restoration_cost)

	hardwareCost = 400 * float(average_hardware_cost)

	initialOutageCost = initialCustomerCost + initialRestorationCost + hardwareCost
	finalOutageCost = finalCustomerCost + finalRestorationCost + hardwareCost

	print('Initial Customer Cost = ' + str(initialCustomerCost))
	print('Final Customer Cost = ' + str(finalCustomerCost))
	print('Initial Restoration Cost = ' + str(initialRestorationCost))
	print('Final Restoration Cost = ' + str(finalRestorationCost))
	print('Hardware Cost = ' + str(hardwareCost))
	print('Initial Outage Cost = ' + str(initialOutageCost))
	print('Final Outage Cost = ' + str(finalOutageCost))

	# bar chart to show change in SAIDI/SAIFI values
	row1 = sorted(test1)
	col1 = [value for (key, value) in sorted(test1.items())]
	data = [go.Bar(x = row1, y = col1, name = 'Recloser Analysis')]
	py.offline.plot(data, filename='recloser_analysis', auto_open=False)

	# gantt plot
	fig = ff.create_gantt(mc2, colors=['#333F44', '#93e4c1'], index_col='Task', show_colorbar=True,
                      bar_width=0.3, showgrid_x=True, showgrid_y=True, title='Fault Timeline')
	py.offline.plot(fig, filename='gantt_timeline', auto_open=False)
	
	# graph failure distribution	
	distributiongraph(failureDistribution, failure_1, failure_2, 'failure distribution')
	
	plt.close('all')

	# graph restoration distribution
	distributiongraph(restorationDistribution, rest_1, rest_2, 'restoration distribution')
	
	# feeder chart with recloser
	outGraph = nx.Graph()
	for key in tree1:
		item = tree1[key]
		if 'name' in item.keys():
			obType = item.get('object')
			reclDevices = dict.fromkeys(['recloser'], False)
			if obType in reclDevices.keys():
				outGraph.add_edge(item['from'],item['to'], edge_color='g')
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
	plt.savefig('feeder chart')

# function that graphs the dsitribution data
def distributiongraph(dist, param_1, param_2, nameOfGraph):
	if 'UNIFORM' == dist:
		x = np.linspace(float(param_1) - 0.5, float(param_2) + 0.5, 100)
		rv = stats.uniform(float(param_1), float(param_2)-float(param_1))
		plt.plot(x, rv.pdf(x), label=nameOfGraph)
	elif 'NORMAL' == dist:
		mean = float(param_1)
		std = float(param_2)
		x = np.linspace(mean-4*std, mean+4*std, 100)
		dist=stats.norm(mean, std)
		plt.plot(x,dist.pdf(x))
	elif 'BERNOULLI' == dist:
		x = np.linspace(0, 1, 100)
		dist = stats.bernoulli(param_1)
		plt.plot(x, dist.pdf(x))
	elif 'LOGNORMAL' == dist:
		mean = float(param_1)
		std = float(param_2)
		x = np.linspace(0.0, mean+10*std, 100)
		dist = stats.lognorm(mean, std)
		plt.plot(x, dist.pdf(x))
	elif 'PARETO' == dist:
		xm = float(param_2) # scale 
		alphas = [float(param_1)] # shape parameters
		x = np.linspace(0, 15, 1000)
		output = np.array([stats.pareto.pdf(x, scale = xm, b = a) for a in alphas])
		plt.plot(x, output.T)
	elif 'EXPONENTIAL' == dist:
		x = np.linspace(float(param_1)-1, float(param_1)+10, 100)
		rv = stats.expon.pdf(x, float(param_1))
		plt.plot(x, rv)
	elif 'WEIBULL' == dist:
		k = float(param_2)
		lam = float(param_1)
		mu = 0
		x = np.linspace(lam-k, lam+k, 1000)
		dist = stats.dweibull(k, mu, lam)
		plt.plot(x, dist.pdf(x))
	elif 'GAMMA' == dist:
		x = np.linspace (0, 100, 200) 
		y1 = stats.gamma.pdf(x, a=float(param_1), loc=1/float(param_2)) 
		plt.plot(x, y1) 
	elif 'BETA' == dist:
		alpha = float(param_1)
		beta = float(param_2)
		x = np.linspace(0, alpha + beta, 100)
		dist = stats.beta(alpha, beta)
		plt.plot(x, dist.pdf(x))
	elif 'TRIANGLE' == dist:
		a = float(param_1)
		b = float(param_2)
		x = np.linspace(0, 10, 100)
		dist = stats.triang(a + (a+b)/2, a)
		plt.plot(x, dist.pdf(x))
	plt.xlabel('Time until event occurs (seconds)')
	plt.ylabel('Probability distribution function')
	plt.show()
	plt.savefig(nameOfGraph)

#test the main functions of the program
valueOfAdditionalRecloser(omf.omfDir + '/scratch/CIGAR/' + 'test_ieee37nodeFaultTester.glm', None, 'underground_line', 'node709-708', 'EXPONENTIAL', '3.858e-7', '0.0', 'PARETO', '1.0', '1.0002778', '432000 s', '1', '1', '1', '1', '2000-01-01 0:00:00', 'TLG')
#bestLocationForRecloser(omf.omfDir + '/scratch/CIGAR/' + 'test_ieee37nodeFaultTester.glm', None, 'underground_line', 'node709-708', 'EXPONENTIAL', '3.858e-7', '0.0', 'PARETO', '1.0', '1.0002778', '432000 s', '2000-01-01 0:00:00', 'TLG' )
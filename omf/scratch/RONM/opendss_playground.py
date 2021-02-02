import random, re, datetime, json, os, tempfile, shutil, csv, math, base64
from os.path import join as pJoin
import subprocess
import pandas as pd
import numpy as np
import scipy
import collections
from scipy import spatial
import scipy.stats as st
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import plotly as py
import plotly.graph_objs as go
from plotly.tools import make_subplots

# OMF imports
import omf
from omf import geo
from omf import distNetViz
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.models import flisr
from omf.solvers.opendss import dssConvert
from omf.solvers import opendss

# Model metadata:
# tooltip = 'outageCost calculates reliability metrics and creates a leaflet graph based on data from an input csv file.'
# modelName, template = __neoMetaModel__.metadata(__file__)
# hidden = True

def play(pathToOmd, pathToDss, pathToTieLines, workDir, microgrids, faultedLine, radial):
	# 1) isolate the fault (using step one of flisr model)
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)

	# read in the tree
	with open(pathToOmd) as inFile:
		tree = json.load(inFile)['tree']

	# find a node associated with the faulted line
	faultedNode = ''
	faultedNode2 = ''
	for key in tree.keys():
		if tree[key].get('name','') == faultedLine:
			faultedNode = tree[key]['from']
			faultedNode2 = tree[key]['to']

	# initialize the list of ties closed and reclosers opened
	bestTies = []
	bestReclosers = []

	buses = []
	for key in microgrids.keys():
		buses.append(microgrids[key].get('gen_bus', ''))
	tree, bestReclosers, badBuses = flisr.cutoffFault(tree, faultedNode, bestReclosers, workDir, radial, buses)
	print(bestReclosers)
	# 2) get a list of loads associated with each microgrid component
	# and create a loadshape containing all said loads
	tree = playOneStep(tree, bestReclosers, badBuses, pathToDss)

	# read in the set of tie lines in the system as a dataframe
	tieLines = pd.read_csv(pathToTieLines)

	#start the restoration piece of the algorithm
	index = 0
	terminate = False
	goTo4 = False
	goTo3 = False
	goTo2 = True
	while terminate == False:
		# Step 2
		if goTo2 == True:
			goTo2 = False
			goTo3 = True
			unpowered, powered, potentiallyViable = flisr.listPotentiallyViable(tree, tieLines, workDir)
			print(potentiallyViable)
		# Step 3
		if goTo3 == True:
			goTo3 = False
			goTo4 = True
			openSwitch = flisr.chooseOpenSwitch(potentiallyViable)
		# Step 4
		if goTo4 == True:
			goTo4 = False
			tree, potentiallyViable, tieLines, bestTies, bestReclosers, goTo2, goTo3, terminate, index = flisr.addTieLines(tree, faultedNode, potentiallyViable, unpowered, powered, openSwitch, tieLines, bestTies, bestReclosers, workDir, goTo2, goTo3, terminate, index, radial)
			if goTo2 == True:
				tree = playOneStep(tree, bestReclosers, badBuses, pathToDss)

def playOneStep(tree, bestReclosers, badBuses, pathToDss):
	buses = []
	sortvals = {}
	for key in microgrids:
		sortvals[key] = microgrids[key].get('max_potential','')
	sortvals = sorted(sortvals.items(), key=lambda x: x[1], reverse=True)

	for key in sortvals:
		buses.append(microgrids[key[0]].get('gen_bus', ''))
	buses = [x for x in buses if x not in badBuses]

	subtrees = {}
	busShapes = {}
	leftOverBusShapes = {}
	shape_insert_list = {}
	gen_insert_list = {}
	leftOverLoad = {}
	i = 0
	j = 0
	# for each power source
	while len(buses) > 0:
		# create an adjacency list representation of tree connectivity
		adjacList, reclosers, vertices = flisr.adjacencyList(tree)
		bus = buses[0]
		loadShapes = {}
		alreadySeen = False
		# check to see if there is a path between the power source and the fault 
		subtree = flisr.getMaxSubtree(adjacList, bus)
		for key in subtrees:
			if set(subtrees[key]) == set(subtree):
				# if a larger generator is already supplying power, have a smaller generator only pick up the remaining load
				dieselShapes = {}
				leftOverShapes = {}
				dieselShapesNew = {}
				leftOverHere = {}
				maximum = 1.0
				for entry in microgrids:
					if bus == microgrids[entry].get('gen_bus', ''):
						maximum = microgrids[entry].get('max_potential', '')
						k = 0
						while k < 3:
							val = 0
							while val < len(leftOverLoad[key][k]):
								if k == 0:
									if not '.1' in dieselShapes.keys():
										dieselShapes['.1'] = []
									if leftOverLoad[key][k][val] == True:
										dieselShapes['.1'].append(leftOverBusShapes[key][k][val])
									else:
										dieselShapes['.1'].append(0.0)
								if k == 1:
									if not '.2' in dieselShapes.keys():
										dieselShapes['.2'] = []
									if leftOverLoad[key][k][val] == True:
										dieselShapes['.2'].append(leftOverBusShapes[key][k][val])
									else:
										dieselShapes['.2'].append(0.0)
								if k == 2:
									if not '.3' in dieselShapes.keys():
										dieselShapes['.3'] = []
									if leftOverLoad[key][k][val] == True:
										dieselShapes['.3'].append(leftOverBusShapes[key][k][val])
									else:
										dieselShapes['.3'].append(0.0)
								val += 1
							k += 1
						for shape in dieselShapes:
							if not shape in dieselShapesNew.keys():
								dieselShapesNew[shape] = []
							if not shape in leftOverShapes.keys():
								leftOverShapes[shape] = []
							if not shape in leftOverHere.keys():
								leftOverHere[shape] = []
							for entry in dieselShapes[shape]:
								if (float(maximum) - float(entry)) >= 0:
									dieselShapesNew[shape].append(float(entry))
									leftOverShapes[shape].append(0.0)
									leftOverHere[shape].append(False)
								else:
									dieselShapesNew[shape].append(float(maximum))
									leftOverShapes[shape].append(float(entry)-float(maximum))
									leftOverHere[shape].append(True)
				alreadySeen = True
		if 'sourcebus' in subtree:
			del(buses[0])
			continue
		for node in subtree:
			for key in tree.keys():
				obtype = tree[key].get('object','')
				if obtype == 'load' or obtype == 'triplex_load':
					if tree[key].get('parent','').startswith(str(node)):
						loadshapeName = tree[key].get('yearly', '')
						for key1 in tree.keys():
							if tree[key1].get('name','') == loadshapeName:
								loadshape = eval(tree[key1].get('mult',''))
								if '.1' in tree[key].get('!CONNCODE',''):
									if '.1' in loadShapes:
										loadShapes['.1'] = [a + b for a, b in zip(loadShapes.get('.1',''), loadshape)]
									else: loadShapes['.1'] = loadshape
								if '.2' in tree[key].get('!CONNCODE',''):
									if '.2' in loadShapes:
										loadShapes['.2'] = [a + b for a, b in zip(loadShapes.get('.2',''), loadshape)]
									else: loadShapes['.2'] = loadshape
								if '.3' in tree[key].get('!CONNCODE',''):
									if '.3' in loadShapes:
										loadShapes['.3'] = [a + b for a, b in zip(loadShapes.get('.3',''), loadshape)]
									else: loadShapes['.3'] = loadshape

# 3) obtain the diesel loadshape by subtracting off solar from load
		dieselShapes = {}
		leftOverShapes = {}
		dieselShapesNew = {}
		leftOverHere = {}
		maximum = 1.0
		for key in tree.keys():
			if tree[key].get('object','').startswith('generator'):
				if tree[key].get('name','').startswith('solar') and tree[key].get('parent','') == bus:
					solarshapeName = tree[key].get('yearly','')
					for key1 in tree.keys():
						if tree[key1].get('name','') == solarshapeName:
							solarshape = eval(tree[key1].get('mult',''))
							if alreadySeen == False:
								for entry in microgrids:
									if buses[0] == microgrids[entry].get('gen_bus', ''):
										maximum = microgrids[entry].get('max_potential', '')
										if '.1' in loadShapes:
											dieselShapes['.1'] = [a - b for a, b in zip(loadShapes.get('.1',''), solarshape)]
										if '.2' in loadShapes:
											dieselShapes['.2'] = [a - b for a, b in zip(loadShapes.get('.2',''), solarshape)]
										if '.3' in loadShapes:
											dieselShapes['.3'] = [a - b for a, b in zip(loadShapes.get('.3',''), solarshape)]
								for shape in dieselShapes:
									if not shape in dieselShapesNew.keys():
										dieselShapesNew[shape] = []
									if not shape in leftOverShapes.keys():
										leftOverShapes[shape] = []
									if not shape in leftOverHere.keys():
										leftOverHere[shape] = []
									for entry in dieselShapes[shape]:
										if (float(maximum) - float(entry)) >= 0:
											dieselShapesNew[shape].append(float(entry))
											leftOverShapes[shape].append(0.0)
											leftOverHere[shape].append(False)
										else:
											dieselShapesNew[shape].append(float(maximum))
											leftOverShapes[shape].append(float(entry)-float(maximum))
											leftOverHere[shape].append(True)
		busShapes[buses[0]] = [dieselShapesNew.get('.1',''), dieselShapesNew.get('.2',''), dieselShapesNew.get('.3','')]
		leftOverBusShapes[buses[0]] = [leftOverShapes.get('.1',''), leftOverShapes.get('.2',''), leftOverShapes.get('.3','')]
		leftOverLoad[buses[0]] = [leftOverHere.get('.1',''), leftOverHere.get('.2',''), leftOverHere.get('.3','')]
		subtrees[bus] = subtree
	# 4) add diesel generation to the opendss formatted system and solve
		phase=1
		while phase < 4:
			if phase == 1:
				angle = '240.000000'
				amps = '219.969000'
			elif phase == 2:
				angle = '120.000000'
				amps = '65.000000'
			else:
				angle = '0.000000'
				amps = '169.120000'
			if alreadySeen == False:
				shape_name = 'newdiesel_' + str(buses[0]) + '_' + str(phase) + '_shape'
				shape_data = dieselShapes.get('.' + str(phase),'')
				shape_insert_list[i] = {
						'!CMD': 'new',
						'object': f'loadshape.{shape_name}',
						'npts': f'{len(shape_data)}',
						'interval': '1',
						'useactual': 'no',
						'mult': str(list(shape_data)).replace(' ','')
					}
				i+=1
				gen_name = 'isource.isource_newdiesel' + str(buses[0]) + '_' + str(phase) + '_shape'
				gen_insert_list[j] = {
						'!CMD': 'new',
						'object': f'"{gen_name}"',
						'bus1': str(buses[0]) + '.' + str(phase),
						'phases': '1',
						'angle': str(angle),
						'amps': str(amps),
						'daily': 'newdiesel_' + str(buses[0]) + '_' + str(phase) + '_shape'
					}
				j+=1
			gen_name = 'isource.isource_solar' + str(buses[0]) + '_' + str(phase) + '_shape'
			gen_insert_list[j] = {
					'!CMD': 'new',
					'object': f'"{gen_name}"',
					'bus1': str(buses[0]) + '.' + str(phase),
					'phases': '1',
					'angle': str(angle),
					'amps': str(amps),
					'daily': 'solar_' + str(buses[0]) + '_shape'
				}
			j+=1
			phase += 1
		del (buses[0])

	# insert new diesel loadshapes and isource generators
	treeDSS = dssConvert.dssToTree(pathToDss)
	tree2 = treeDSS.copy()
	# print(tree2)
	for thing in tree2:
		if (thing.get('object','').startswith('generator')):
			treeDSS.remove(thing)
	for key in shape_insert_list:
		convertedKey = collections.OrderedDict(shape_insert_list[key])
		min_pos = min(shape_insert_list.keys())
		treeDSS.insert(min_pos, convertedKey)
	max_pos = 100000000
	for key in gen_insert_list:
		convertedKey = collections.OrderedDict(gen_insert_list[key])
		treeDSS.insert(max_pos, convertedKey)
		max_pos+=1

	treeDSS.insert(max_pos, {'!CMD': 'solve'})
	# print(treeDSS)

	# Write new DSS file.
	FULL_NAME = 'lehigh_full_newDiesel.dss'
	dssConvert.treeToDss(treeDSS, FULL_NAME)
	# print(treeDSS)

	actions = {}
	key = 0
	max_pos = 1000000000
	while key < len(bestReclosers):
		recloserName = bestReclosers[key].get('name','')
		open_line = 'open object=line.' + f'{recloserName}' + ' term=1'
		actions[max_pos] = open_line
		max_pos+=1
		key+=1
	# print(treeDSS)

	opendss.newQstsPlot(FULL_NAME,
		stepSizeInMinutes=60, 
		numberOfSteps=24*20,
		keepAllFiles=False,
		actions=actions
	)

	def make_chart(csvName, category_name, x, y_list):
		gen_data = pd.read_csv(csvName)
		data = []
		for ob_name in set(gen_data[category_name]):
			for y_name in y_list:
				this_series = gen_data[gen_data[category_name] == ob_name]
				trace = py.graph_objs.Scatter(
					x = this_series[x],
					y = this_series[y_name],
					name = ob_name + '_' + y_name
				)
				data.append(trace)
		layout = py.graph_objs.Layout(
			title = f'{csvName} Output',
			xaxis = dict(title = x),
			yaxis = dict(title = str(y_list))
		)
		fig = py.graph_objs.Figure(data, layout)
		py.offline.plot(fig, filename=f'{csvName}.plot.html')
	
	# make_chart('timeseries_gen.csv', 'Name', 'hour', ['P1(kW)','P2(kW)','P3(kW)'])
	make_chart('timeseries_load.csv', 'Name', 'hour', ['V1','V2','V3'])
	make_chart('timeseries_source.csv', 'Name', 'hour', ['P1(kW)','P2(kW)','P3(kW)'])
	make_chart('timeseries_control.csv', 'Name', 'hour', ['Tap(pu)'])

	return(tree)

microgrids = {
	'm1': {
		'loads': ['634a_supermarket','634b_supermarket','634c_supermarket'],
		'switch': '632633',
		'gen_bus': '634',
		'max_potential': '0.7'
	},
	'm2': {
		'loads': ['675a_residential1','675b_residential1','675c_residential1'],
		'switch': '671692',
		'gen_bus': '675',
		'max_potential': '0.65'
	},
	'm3': {
		'loads': ['671_hospital','652_med_apartment'],
		'switch': '671684',
		'gen_bus': '684',
		'max_potential': '0.9'
	},
	'm4': {
		'loads': ['645_warehouse1','646_med_office'],
		'switch': '632645',
		'gen_bus': '646',
		'max_potential': '0.8'
	}
}

play('C:/Users/granb/microgridup-main/lehigh.dss.omd', 'C:/Users/granb/microgridup-main/lehigh_base_phased.dss', 'C:/Users/granb/omf/omf/scratch/RONM/tiedata.csv', None, microgrids, '670671', False)
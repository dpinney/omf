import random, re, datetime, json, os, tempfile, shutil, csv, math, platform, base64
from os.path import join as pJoin
import pandas as pd
import numpy as np
import scipy
from scipy import spatial
import scipy.stats as st
from sklearn.preprocessing import LabelEncoder
import plotly as py
import plotly.graph_objs as go
import matplotlib
if platform.system() == 'Darwin':
	matplotlib.use('TkAgg')
else:
	matplotlib.use('Agg')
from matplotlib import pyplot as plt
import networkx as nx
# OMF imports
from omf import feeder, geo
import omf
import omf.feeder
import omf.geo
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
tooltip = 'smartSwitching gives the expected reliability improvement from adding reclosers to a circuit.'
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def safeInt(x):
	try: return int(x)
	except: return 0

def getMaxSubtree(graph, start):
	'helper function that returns all the nodes connected to a starting node in a graph'
	visited, stack = set(), [start]
	while stack:
		vertex = stack.pop()
		if vertex not in visited:
			visited.add(vertex)
			stack.extend(graph[vertex] - visited)
	return visited

def findPathToFault(graph, start, finish):
	'helper function that returns a path from the starting point to finishing point in a graph'
	stack = [(start, [start])]
	while stack:
		(vertex, path) = stack.pop()
		for next in graph[(vertex)] - set(path):
			if next == finish:
				yield path + [next]
			else:
				stack.append((next, path + [next]))

def mergeContigLines(tree, faultedLine):
	'helper function to remove repeated lines'
	removedKeys = 1
	while removedKeys != 0:
		treeKeys = len(tree.keys())
		obs = list(tree.values())
		n2k = omf.feeder.nameIndex(tree)
		for o in obs:
			if 'to' in o:
				top = o
				node = tree[n2k[o['to']]]
				allBottoms = []
				for o2 in obs:
					if o2.get('from', None) == node['name']:
						allBottoms.append(o2)
				if len(allBottoms) == 1:
					bottom = allBottoms[0]
					if (top.get('object', '') == bottom.get('object', '')) and (top.get('name', '') != faultedLine) and (bottom.get('name', '') != faultedLine) and (top.get('object', '') != 'recloser') and (bottom.get('object', '') != 'recloser'):
						# delete node and bottom line, make top line length = sum of both lines and connect to bottom to.
						if ('length' in top) and ('length' in bottom):
							newLen = float(top['length']) + float(bottom['length'])
							try:
								topTree = tree[n2k[o['name']]]
								topTree['length'] = str(newLen)
								topTree['to'] = bottom['to']
								topTree['configuration'] = bottom['configuration']
								del tree[n2k[node['name']]]
								del tree[n2k[bottom['name']]]
							except:
								continue #key weirdness
		removedKeys = treeKeys - len(tree.keys())
	return tree

def adjacencyList(tree):
	'helper function which creates an adjacency list representation of graph connectivity'
	adjacList = {}
	reclosers = []
	vertices = set()
	for key in tree.keys():
		obtype = tree[key].get('object','')
		if obtype.startswith('underground_line') or obtype.startswith('overhead_line') or obtype.startswith('triplex_line') or obtype.startswith('switch') or obtype.startswith('recloser') or obtype.startswith('transformer') or obtype.startswith('fuse') or obtype.startswith('regulator'):
			if obtype.startswith('recloser'):
				reclosers.append(tree[key])
			if 'from' in tree[key].keys() and 'to' in tree[key].keys():
				if not tree[key]['from'] in adjacList.keys():
					adjacList[tree[key]['from']] = set()
					vertices.add(tree[key].get('from', ''))
				if not tree[key]['to'] in adjacList.keys():
					adjacList[tree[key]['to']] = set()
					vertices.add(tree[key].get('to', ''))
				adjacList[tree[key]['from']].add(tree[key]['to'])
				adjacList[tree[key]['to']].add(tree[key]['from'])
	return adjacList, reclosers, vertices

def removeRecloser(tree, treeCopy, recloser, bestReclosers, found):
	'helper function which removes a recloser (closed switch) from the tree'
	found = True
	bestReclosers.append(recloser)
	for key in treeCopy.keys():
		if treeCopy[key] == recloser:
			del (tree[key])
	
	return tree, bestReclosers, found

def cutoffFault(tree, faultedNode, bestReclosers, workDir, radial):	
	'Step 1: isolate the fault from all power sources'
	buses = []
	# create a list of all power sources
	tree2 = tree.copy()
	for key in tree2.keys():
		if bool(tree2[key].get('bustype','')) is True:
			buses.append(tree[key]['name'])
	# for each power source
	while len(buses) > 0:
		# create an adjacency list representation of tree connectivity
		adjacList, reclosers, vertices = adjacencyList(tree)
		bus = buses[0]
		# check to see if there is a path between the power source and the fault 
		subtree = getMaxSubtree(adjacList, bus)
		if faultedNode in subtree:
			# find a path to the fault
			path = findPathToFault(adjacList, bus, faultedNode)
			for lis in path:
				row = len(lis) - 1
				# for each path, remove the recloser nearest to the fault
				while row > -1:
					found = False
					for recloser in reclosers:
						if recloser['from'] == lis[row]:
							if recloser['to'] == lis[row-1]:
								tree, bestReclosers, found = removeRecloser(tree, tree2, recloser, bestReclosers, found)
								break
						if recloser['to'] == lis[row]:
							if recloser['from'] == lis[row-1]:
								tree, bestReclosers, found = removeRecloser(tree, tree2, recloser, bestReclosers, found)
								break
					if found == True:
						if radial == True:
							del (buses[0])
						break
					row -= 1
				break
			# if there is no way to isolate the fault, notify the user!
			if found == False:
				print('This system is unsolvable with respect to FLISR!')
				break
		else:
			del (buses[0])
	return tree, bestReclosers

def listPotentiallyViable(tree, tieLines, workDir):
	'Step 2: find the powered and unpowered subtrees and the subset of potentially viable open switches'
	# find the adjacency list representation of connectivity
	adjacList, reclosers, vertices = adjacencyList(tree)
	# create the powered and unpowered subtrees
	powered = set()
	for key in tree.keys():
		if bool(tree[key].get('bustype','')) is True:
			powered |= getMaxSubtree(adjacList, tree[key]['name'])
	unpowered = vertices - powered
	
	# create a list of dict objects that represents the subset of potentially viable open switches
	potentiallyViable = []
	tie_row_count = tieLines.shape[0]
	entry = 0
	while entry < tie_row_count:
		if (tieLines.loc[entry, 'to'] in unpowered) and (tieLines.loc[entry, 'from'] in powered):
			potentiallyViable.append({'object':tieLines.loc[entry, 'object'], 'phases':tieLines.loc[entry, 'phases'], 'name':tieLines.loc[entry, 'name'], 'from':tieLines.loc[entry, 'from'], 'to':tieLines.loc[entry, 'to']})
		if tieLines.loc[entry, 'from'] in unpowered and tieLines.loc[entry, 'to'] in powered:
			potentiallyViable.append({'object':tieLines.loc[entry, 'object'], 'phases':tieLines.loc[entry, 'phases'], 'name':tieLines.loc[entry, 'name'], 'from':tieLines.loc[entry, 'from'], 'to':tieLines.loc[entry, 'to']})
		entry += 1

	return unpowered, powered, potentiallyViable

def chooseOpenSwitch(potentiallyViable):
	'Step 3: pick an open switch from the subset of potentially viable open switches'
	if len(potentiallyViable) > 0:
		openSwitch = potentiallyViable[0]
	else:
		openSwitch = None
	return openSwitch

def addTieLines(tree, faultedNode, potentiallyViable, unpowered, powered, openSwitch, tieLines, bestTies, bestReclosers, workDir, goTo2, goTo3, terminate, index, radial):
	'Step 4: Close open switches and open closed switches to power unpowered connected components'
	biggestKey = max([safeInt(x) for x in tree.keys()])
	tree2 = tree.copy()
	# continue the algorithm until there are no more switches in the subset of potentially viable open switches
	if openSwitch != None:
		# find the node of the switch in the unpowered subtree
		if openSwitch.get('to', '') in unpowered:
			tieNode = openSwitch.get('to', '')
		else:
			tieNode = openSwitch.get('from', '')
		while (goTo2 == False) and (goTo3 == False):
			# get an adjacency list representation of tree connectivity
			adjacList, reclosers, vertices = adjacencyList(tree)
			# check if the faulted node is in the same subtree as the node connected to the unpowered subtree
			subtree = getMaxSubtree(adjacList, tieNode)
			if faultedNode in subtree:
				# find a path between the switch and the fault
				path = findPathToFault(adjacList, tieNode, faultedNode)
				for lis in path:
					row = len(lis) - 1
					# open the recloser nearest to the fault
					while row > -1:
						found = False
						for recloser in reclosers:
							if recloser['to'] == lis[row]:
								if recloser['from'] == lis[row-1]:
									tree, bestReclosers, found = removeRecloser(tree, tree2, recloser, bestReclosers, found)
									break
							if recloser['from'] == lis[row]:
								if recloser['to'] == lis[row-1]:
									tree, bestReclosers, found = removeRecloser(tree, tree2, recloser, bestReclosers, found)
									break
						if found == True:
							if radial == True:
								goTo2 = True
								bestTies.append(openSwitch)
								index += 1
								tree[str(biggestKey*10 + index)] = {'object':openSwitch.get('object',''), 'phases':openSwitch.get('phases',''), 'name':openSwitch.get('name',''), 'from':openSwitch.get('from',''), 'to':openSwitch.get('to','')}
								entry = 0
								while entry < tieLines.shape[0]:
									if openSwitch.get('name', '') == tieLines.loc[entry, 'name']:
										tieLines.drop(tieLines.index[[entry]], inplace=True)
										tieLines = tieLines.reset_index(drop=True)
										break
									entry += 1
							break
						row -= 1
					break
				# if there is no such recloser, then the switch is deleted from the subset of potentially viable switches
				if found == False:
					goTo3 = True
					del (potentiallyViable[0])
			# if there is no path between the switch and fault, close the switch
			else:
				goTo2 = True
				bestTies.append(openSwitch)
				index += 1
				tree[str(biggestKey*10 + index)] = {'object':openSwitch.get('object',''), 'phases':openSwitch.get('phases',''), 'name':openSwitch.get('name',''), 'from':openSwitch.get('from',''), 'to':openSwitch.get('to','')}
				entry = 0
				while entry < tieLines.shape[0]:
					if openSwitch.get('name', '') == tieLines.loc[entry, 'name']:
						tieLines.drop(tieLines.index[[entry]], inplace=True)
						tieLines = tieLines.reset_index(drop=True)
						break
					entry += 1
	# if the subset of potentially viable switches is empty, end the algorithm
	else:
		terminate = True
	return tree, potentiallyViable, tieLines, bestTies, bestReclosers, goTo2, goTo3, terminate, index

def flisr(pathToOmd, pathToTieLines, faultedLine, workDir, radial):
	'run the FLISR algorithm to isolate the fault and restore power'
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)

	# read in the tree
	with open(pathToOmd) as inFile:
		tree = json.load(inFile)['tree']

	# find a node associated with the faulted line
	faultedNode = ''
	for key in tree.keys():
		if tree[key].get('name','') == faultedLine:
			faultedNode = tree[key]['from']

	# simplify the system to decrease runtime
	tree = mergeContigLines(tree, faultedLine)

	# initialize the list of ties closed and reclosers opened
	bestTies = []
	bestReclosers = []

	# Step 1
	tree, bestReclosers = cutoffFault(tree, faultedNode, bestReclosers, workDir, radial)

	# read in the set of tie lines in the system as a dataframe
	tieLines = pd.read_csv(pathToTieLines)

	# start the restoration piece of the algorithm
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
			unpowered, powered, potentiallyViable = listPotentiallyViable(tree, tieLines, workDir)
		# Step 3
		if goTo3 == True:
			goTo3 = False
			goTo4 = True
			openSwitch = chooseOpenSwitch(potentiallyViable)
		# Step 4
		if goTo4 == True:
			goTo4 = False
			tree, potentiallyViable, tieLines, bestTies, bestReclosers, goTo2, goTo3, terminate, index = addTieLines(tree, faultedNode, potentiallyViable, unpowered, powered, openSwitch, tieLines, bestTies, bestReclosers, workDir, goTo2, goTo3, terminate, index, radial)
	print(bestReclosers)
	print(bestTies)
	# Run powerflow on the optimal solution
	biggestKey = max([safeInt(x) for x in tree.keys()])
	tree[str(biggestKey*10 + index + 1)] = {'module':'powerflow','solver_method':'FBS'}
	attachments = []
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

	# feeder chart with recloser
	plt.close('all')
	outGraph = nx.Graph()
	for key in tree:
		item = tree[key]
		if 'name' in item.keys():
			obType = item.get('object')
			reclDevices = dict.fromkeys(['recloser'], False)
			if ('tie' in item.get('name', '')):
				# HACK: set the recloser as a swingNode in order to make it hot pink
				outGraph.add_edge(item['from'],item['to'],type='swingNode')
			elif (obType in reclDevices.keys()):
				outGraph.add_edge(item['from'],item['to'])
			elif 'parent' in item.keys() and obType not in reclDevices:
				outGraph.add_edge(item['name'],item['parent'],type='parentChild',phases=1)
				outGraph.nodes[item['name']]['type']=item['object']
				# Note that attached houses via gridEdit.html won't have lat/lon values, so this try is a workaround.
				try: outGraph.nodes[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
				except: outGraph.nodes[item['name']]['pos']=(0.0,0.0)
			elif 'from' in item.keys():
				myPhase = feeder._phaseCount(item.get('phases','AN'))
				outGraph.add_edge(item['from'],item['to'],name=item.get('name',''),type=item['object'],phases=myPhase)
			elif item['name'] in outGraph:
				# Edge already led to node's addition, so just set the attributes:
				outGraph.nodes[item['name']]['type']=item['object']
			else:
				outGraph.add_node(item['name'],type=item['object'])
			if 'latitude' in item.keys() and 'longitude' in item.keys():
				try: outGraph.nodes.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
				except: outGraph.nodes.get(item['name'],{})['pos']=(0.0,0.0)
	feeder.latLonNxGraph(outGraph, labels=True, neatoLayout=True, showPlot=False)
	plt.savefig(workDir + '/feeder_chart')

	return {'bestReclosers':bestReclosers, 'bestTies':bestTies}

#flisr('C:/Users/granb/omf/omf/static/publicFeeders/Olin Barre Fault Test 2.omd', 'C:/Users/granb/omf/omf/scratch/blackstart/test.csv', "19186", None, True)

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}
	# Write the feeder
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict['feederName1'] = feederName
	#test the main functions of the program
	with open(pJoin(modelDir, inputDict['tieFileName']), 'w') as f:
		pathToData = f.name
		f.write(inputDict['tieData'])
	plotOuts = flisr(
		modelDir + '/' + feederName + '.omd', #OMD Path
		pathToData, #Tie Line Data Path
		inputDict['faultedLine'], #'19186'
		modelDir, #Work directory.
		inputDict['radial']) #'True') 
	
	# # Textual outputs of cost statistic
	# with open(pJoin(modelDir,'costStatsCalc.html')) as inFile:
	# 	outData['costStatsHtml'] = inFile.read()
	
	# Image outputs.
	with open(pJoin(modelDir,'feeder_chart.png'),'rb') as inFile:
		outData['feeder_chart.png'] = base64.standard_b64encode(inFile.read()).decode()

	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,'scratch','blackstart','testOlinBarreFault.csv')) as f:
		tie_data = f.read()
	defaultInputs = {
		'modelType': modelName,
		'feederName1': 'Olin Barre Fault Test 2',
		'faultedLine': '19186',
		'radial': 'True',
		'runPowerflow': 'True',
		'tieFileName': 'testOlinBarreFault.csv',
		'tieData': tie_data
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, 'scratch', 'blackstart', defaultInputs['feederName1']+'.omd'), pJoin(modelDir, defaultInputs['feederName1']+'.omd'))
	except:
		return False
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
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
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()

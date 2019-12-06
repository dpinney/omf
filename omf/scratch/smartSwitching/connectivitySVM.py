import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
import math
import omf
import networkx as nx
import scipy.stats as stats
from plotly import tools
import plotly as py
import csv
from operator import itemgetter
import re
from sklearn import svm
from sklearn import metrics
from numpy import array
import plotly.graph_objs as go
import plotly.figure_factory as ff
from plotly.tools import make_subplots
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx

# OMF imports
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf import geo, feeder

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *
	
def nodeToCoords(outageMap, nodeName):
	'get the latitude and longitude of a given node in string format'
	coords = ''
	for key in outageMap['features']:
		if (nodeName in key['properties'].get('name','')):
			current = key['geometry']['coordinates']
			p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
			coords = [float(i) for i in p.findall(str(current))]
			coord1 = coords[0]
			coord2 = coords[1]
	return coord1, coord2

workDir = None

def generateData(pathToOmd, workDir, inputData, outputData):
	omd = json.load(open(pathToOmd))
	tree = omd.get('tree', {})
	attachments = omd.get('attachments',[])

	# check to see if work directory is specified
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir


	def safeInt(x):
			try: return int(x)
			except: return 0

	biggestKey = max([safeInt(x) for x in tree.keys()])

	CLOCK_START = '2000-01-01 0:00:00'
	dt_start = parser.parse(CLOCK_START)
	dt_end = dt_start + relativedelta(day=0, hour=0, minute=5, second=0)
	CLOCK_END = str(dt_end)
	CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END

	index = 1
	for key in tree:
		if 'clock' in tree[key]:
			tree[key]['starttime'] = "'" + CLOCK_START + "'"
			tree[key]['stoptime'] = "'" + CLOCK_END + "'"

	# create volt and current line dumps
	tree[str(biggestKey*10 + index)] = {"object":"voltdump","filename":"voltDump.csv", 'runtime': 'INIT'}

	attachments = []
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

	outageMap = geo.omdGeoJson(pathToOmd, conversion = False)
	with open(workDir + '/nodes.csv', mode='wb') as nodes:

		fieldnames = ['node_name', 'coord1', 'coord2']
		writer = csv.DictWriter(nodes, fieldnames)
		writer.writeheader()

		for key in tree.keys():
			obtype = tree[key].get("object","")
			if obtype == 'node' or obtype == 'load' or obtype == 'capacitor' or obtype == 'meter':
				coord1, coord2 = nodeToCoords(outageMap, tree[key]['name'])
				writer.writerow({'node_name': tree[key]['name'], 'coord1': coord1, 'coord2': coord2})
	nodes.close()

	with open(workDir + '/connectivity.csv', mode= 'wb') as connectivity:

		fieldnames = ['first_node', 'second_node']
		writer = csv.DictWriter(connectivity, fieldnames)
		writer.writeheader()

		for key in tree.keys():
			obtype = tree[key].get("object","")
			if obtype == 'underground_line' or obtype == 'overhead_line' or obtype == 'triplex_line':
				writer.writerow({'first_node': tree[key]['from'], 'second_node': tree[key]['to']})
	connectivity.close()

	connectivity = pd.read_csv(workDir + '/connectivity.csv')
	print(connectivity)

	nodes = pd.read_csv(workDir + '/nodes.csv')

	row = 0
	number_of_nodes = nodes.shape[0]
	bad_nodes = []
	while row < number_of_nodes:
		if (not connectivity['first_node'].str.contains(nodes.loc[row, 'node_name']).any()) and (not connectivity['second_node'].str.contains(nodes.loc[row, 'node_name']).any()):
			bad_nodes.append(nodes.loc[row, 'node_name'])
		row += 1

	row = 0
	number_of_bad = len(bad_nodes)
	while row < number_of_bad:
		delete_row = nodes[nodes['node_name']==bad_nodes[row]].index
		nodes = nodes.drop(delete_row)
		row += 1
	
	nodes.dropna()
	nodes = nodes.sort_values('node_name')
	nodes.to_csv(workDir + '/nodes1.csv')
	nodes = pd.read_csv(workDir + '/nodes1.csv')
	print(nodes)

	volt = pd.read_csv(workDir + '/voltDump.csv', skiprows=1)

	row = 0
	number_of_volt = volt.shape[0]
	bad_nodes = []
	while row < number_of_volt:
		if (not connectivity['first_node'].str.contains(volt.loc[row, 'node_name']).any()) and (not connectivity['second_node'].str.contains(volt.loc[row, 'node_name']).any()):
			bad_nodes.append(volt.loc[row, 'node_name'])
		row += 1
	number_of_bad = len(bad_nodes)
	row = 0
	while row < number_of_bad:
		delete_row = volt[volt['node_name']==bad_nodes[row]].index
		volt = volt.drop(delete_row)
		row += 1
	volt = volt.sort_values('node_name')
	volt.to_csv(workDir + '/volt1.csv')
	volt = pd.read_csv(workDir + '/volt1.csv')
	print(volt)
	row_count = nodes.shape[0]
	inputDataDist = [[0 for x in range(row_count)] for y in range(row_count)]
	inputGraphDist = nx.Graph()
	row = 0
	while row < row_count:
		column = 0
		while column < row_count:
			data = []
			if ((nodes.loc[row, 'coord1'] - nodes.loc[column, 'coord1'])**2 + (nodes.loc[row, 'coord2'] - nodes.loc[column, 'coord2'])**2) > 10e-10:
				distance = math.sqrt((nodes.loc[row, 'coord1'] - nodes.loc[column, 'coord1'])**2 + (nodes.loc[row, 'coord2'] - nodes.loc[column, 'coord2'])**2)
			else:
				distance = 0.0
					
			if distance > 10e-15:
				data.append(distance)
				#data.append(distance*10e5*1.09359893099)
			else:
				data.append(10e15)

			inputDataDist[row][column] = sum(data)
			if not inputGraphDist.has_edge(row, column):
				inputGraphDist.add_edge(row, column, weight=inputDataDist[row][column])
			column += 1
		row += 1

	row_count = volt.shape[0]
	inputDataVolt = [[0 for x in range(row_count)] for y in range(row_count)]
	inputGraphVolt = nx.Graph()
	row = 0
	while row < row_count:
		column = 0
		while column < row_count:
			data = []
			if (float(volt.loc[row, 'voltA_real']) > 10e-10 or float(volt.loc[row, 'voltA_imag']) > 10e-10 or float(volt.loc[row, 'voltA_real']) < -10e-10 or float(volt.loc[row, 'voltA_imag']) < -10e-10):
				if (math.sqrt((float(volt.loc[row, 'voltA_real']) - float(volt.loc[column, 'voltA_real']))**2 + (float(volt.loc[row, 'voltA_imag']) - float(volt.loc[column, 'voltA_imag']))**2)) > 0:
					data.append(math.sqrt((float(volt.loc[row, 'voltA_real']) - float(volt.loc[column, 'voltA_real']))**2 + (float(volt.loc[row, 'voltA_imag']) - float(volt.loc[column, 'voltA_imag']))**2))
				else:
					data.append(100.0)
			else:
				data.append(100.0)
			if (float(volt.loc[row, 'voltB_real']) > 10e-10 or float(volt.loc[row, 'voltB_imag']) > 10e-10 or float(volt.loc[row, 'voltB_real']) < -10e-10 or float(volt.loc[row, 'voltB_imag']) < -10e-10):
				if (math.sqrt((float(volt.loc[row, 'voltB_real']) - float(volt.loc[column, 'voltB_real']))**2 + (float(volt.loc[row, 'voltB_imag']) - float(volt.loc[column, 'voltB_imag']))**2)) > 0:
					data.append(math.sqrt((float(volt.loc[row, 'voltB_real']) - float(volt.loc[column, 'voltB_real']))**2 + (float(volt.loc[row, 'voltB_imag']) - float(volt.loc[column, 'voltB_imag']))**2))
				else:
					data.append(100.0)
			else:
				data.append(100.0)
			if (float(volt.loc[row, 'voltC_real']) > 10e-10 or float(volt.loc[row, 'voltC_imag']) > 10e-10 or float(volt.loc[row, 'voltC_real']) < -10e-10 or float(volt.loc[row, 'voltC_imag']) < -10e-10):
				if (math.sqrt((float(volt.loc[row, 'voltC_real']) - float(volt.loc[column, 'voltC_real']))**2 + (float(volt.loc[row, 'voltC_imag']) - float(volt.loc[column, 'voltC_imag']))**2)) > 0:
					data.append(math.sqrt((float(volt.loc[row, 'voltC_real']) - float(volt.loc[column, 'voltC_real']))**2 + (float(volt.loc[row, 'voltC_imag']) - float(volt.loc[column, 'voltC_imag']))**2))
				else:
					data.append(100.0)
			else:
				data.append(100.0)
			inputDataVolt[row][column] = sum(data)
			if not inputGraphVolt.has_edge(row, column):
				inputGraphVolt.add_edge(row, column, weight=inputDataVolt[row][column])
			column += 1
		row += 1

	nodes_count = nodes.shape[0]
	connectivity_count = connectivity.shape[0]
	row = 0
	outputData = [[0 for x in range(nodes_count)] for y in range(nodes_count)]
	outputGraph = nx.Graph()
	while row < nodes_count:
		column = 0
		while column < nodes_count:
			rowName = nodes.loc[row, 'node_name']
			colName = nodes.loc[column, 'node_name']
			conEntry = 0
			found = False
			while conEntry < connectivity_count:
				if ((rowName == connectivity.loc[conEntry, 'first_node'] and colName == connectivity.loc[conEntry, 'second_node']) or (rowName == connectivity.loc[conEntry, 'second_node'] and colName == connectivity.loc[conEntry, 'first_node'])):
					outputData[row][column] = -1
					if not outputGraph.has_edge(row, column):
						outputGraph.add_edge(row, column, weight=-1)
					found = True
					break
				conEntry += 1
			if found == False:
				if not outputGraph.has_edge(row, column):
					outputData[row][column] = 0
					outputGraph.add_edge(row, column, weight=0)
			column += 1
		row += 1
	print(len(outputData))
	print(len(inputDataDist))
	return inputDataDist, inputGraphDist, inputDataVolt, inputGraphVolt, outputData, outputGraph

def prim(graph):
	# initialize the MST and set X to keep track of vertices
	MST = set()
	X = set()

	# select a vertex to begin
	X.add(0)
	while len(X) != len(graph):
		crossing = set()
		for x in X:
			for k in range(len(graph)):
				if k not in X and graph[x][k] != 0:
					crossing.add((x, k))
		
		# find the edge with smallest crossing weight
		if len(crossing) == 0: break
		edge = sorted(crossing, key=lambda e:graph[e[0]][e[1]])[0]
		# add the edge found to the MST
		MST.add(edge)
		# add the new vertex to X
		X.add(edge[1])
	return MST

# feeder.glmToOmd('C:/Users/granb/omf/omf/scratch/CIGAR/test_large-R5-35.00-1.glm_CLEAN.glm', 'C:/Users/granb/omf/omf/scratch/CIGAR/test_large-R5-35.00-1.glm_CLEAN.omd', attachFilePaths=[])
#inputDataDist, inputGraphDist, inputDataVolt, inputGraphVolt, outputData, outputGraph = generateData(omf.omfDir + '/scratch/smartSwitching/test_ieee123nodeBetter.omd', None, None, None)
inputDataDist, inputGraphDist, inputDataVolt, inputGraphVolt, outputData, outputGraph = generateData(omf.omfDir + '/static/publicFeeders/ieee37nodeFaultTester.omd', None, None, None)
# inputDataDist, inputGraphDist, inputDataVolt, inputGraphVolt, outputData, outputGraph = generateData('C:/Users/granb/omf/omf/scratch/CIGAR/test_large-R5-35.00-1.glm_CLEAN.omd', None, None, None)

expectedDist = prim(inputDataDist)
expectedVolt = prim(inputDataVolt)
actual = prim(outputData)

size = len(inputDataDist)
distMST = [[0 for x in range(size)] for y in range(size)]
voltMST = [[0 for x in range(size)] for y in range(size)]
actualMST = [[0 for x in range(size)] for y in range(size)]

xMST1D = []
yMST1D = []

for val in expectedDist:
	distMST[val[0]][val[1]] = 1

for val in expectedVolt:
	voltMST[val[0]][val[1]] = 1

for val in actual:
	actualMST[val[0]][val[1]] = 1

row = 0
while row < size:
	column = 0
	while column < size:
		mstTemp = []
		mstTemp.append(distMST[row][column])
		mstTemp.append(voltMST[row][column])
		xMST1D.append(mstTemp)
		yMST1D.append(actualMST[row][column])
		column += 1
	row += 1

print(len(xMST1D))
print(len(yMST1D))

print('DistDif1:',expectedDist.difference(actual))
print('DistDif2:',actual.difference(expectedDist))

print('VoltDif1:',expectedVolt.difference(actual))
print('VoltDif2:',actual.difference(expectedVolt))

print('Distance Accuracy:',(1.0 - (abs(float(len(expectedDist.difference(actual)))))/float(len(actual))))
print('Voltage Accuracy:',(1.0 - (abs(float(len(expectedVolt.difference(actual)))))/float(len(actual))))

N = int(len(xMST1D) * .9)

X_train = []
y_train = []
X_test = []
y_test = []
row = 0

while row < N:
	X_train.append(xMST1D[row])
	y_train.append(yMST1D[row])
	row += 1

while row < len(xMST1D):
	X_test.append(xMST1D[row])
	y_test.append(yMST1D[row])
	row += 1

X_train = array(X_train)
y_train = array(y_train)
X_test = array(X_test)
y_test = array(y_test)

#print(X_train)
#print(y_train)

#print(X_test)

#print(y_test)

clf = svm.SVC(kernel='sigmoid')

clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

print(y_pred)
print(y_test)

print('Accuracy:',metrics.accuracy_score(y_test, y_pred))

print('Precision:',metrics.precision_score(y_test, y_pred))
print('Recall:',metrics.recall_score(y_test, y_pred))
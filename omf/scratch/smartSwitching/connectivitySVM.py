import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib
import math
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

	nodes = pd.read_csv(workDir + '/nodes.csv')
	nodes = nodes.sort_values('node_name')

	volt = pd.read_csv(workDir + '/voltDump.csv', skiprows=1)
	volt = volt.sort_values('node_name')

	if inputData == None:
		inputData = []

	row_count = volt.shape[0]
	row = 0
	while row < row_count:
		column = 0
		while column < row_count:
			if ((nodes.loc[row, 'coord1'] - nodes.loc[column, 'coord1'])**2 + (nodes.loc[row, 'coord2'] - nodes.loc[column, 'coord2'])**2) > 10e-10:
				distance = math.sqrt((nodes.loc[row, 'coord1'] - nodes.loc[column, 'coord1'])**2 + (nodes.loc[row, 'coord2'] - nodes.loc[column, 'coord2'])**2)
			else:
				distance = 0.0
			data = []
			if float(volt.loc[row, 'voltA_real']) > 10e-10:
				data.append(math.sqrt((float(volt.loc[row, 'voltA_real']) - float(volt.loc[column, 'voltA_real']))**2 + (float(volt.loc[row, 'voltA_imag']) - float(volt.loc[column, 'voltA_imag']))**2))
			else:
				data.append(0.0)
			if float(volt.loc[row, 'voltB_real']) > 10e-10:
				data.append(math.sqrt((float(volt.loc[row, 'voltB_real']) - float(volt.loc[column, 'voltB_real']))**2 + (float(volt.loc[row, 'voltB_imag']) - float(volt.loc[column, 'voltB_imag']))**2))
			else:
				data.append(0.0)
			if float(volt.loc[row, 'voltC_real']) > 10e-10:
				data.append(math.sqrt((float(volt.loc[row, 'voltC_real']) - float(volt.loc[column, 'voltC_real']))**2 + (float(volt.loc[row, 'voltC_imag']) - float(volt.loc[column, 'voltC_imag']))**2))
			else:
				data.append(0.0)
			if distance > 10e-10:
				data.append(math.sqrt((nodes.loc[row, 'coord1'] - nodes.loc[column, 'coord1'])**2 + (nodes.loc[row, 'coord2'] - nodes.loc[column, 'coord2'])**2))	
			else:
				data.append(0.0)

			inputData.append(data)
			column += 1
		row += 1

	nodes_count = nodes.shape[0]
	connectivity_count = connectivity.shape[0]
	row = 0
	if outputData == None:
		outputData = []
	while row < nodes_count:
		column = 0
		while column < nodes_count:
			rowName = nodes.loc[row, 'node_name']
			colName = nodes.loc[column, 'node_name']
			conEntry = 0
			found = False
			while conEntry < connectivity_count:
				if ((rowName == connectivity.loc[conEntry, 'first_node'] and colName == connectivity.loc[conEntry, 'second_node']) or (rowName == connectivity.loc[conEntry, 'second_node'] and colName == connectivity.loc[conEntry, 'first_node'])):
					outputData.append(1)
					found = True
					break
				conEntry += 1
			if found == False:
				outputData.append(0)
			column += 1
		row += 1
	return inputData, outputData

#feeder.glmToOmd('C:/Users/granb/omf/omf/scratch/CIGAR/test_large-R5-35.00-1.glm_CLEAN.glm', 'C:/Users/granb/omf/omf/scratch/CIGAR/test_large-R5-35.00-1.glm_CLEAN.omd', attachFilePaths=[])
inputData, outputData = generateData('C:/Users/granb/omf/omf/static/publicFeeders/ieee37nodeFaultTester.omd', None, None, None)
inputData, outputData = generateData('C:/Users/granb/omf/omf/scratch/smartSwitching/test_ieee123nodeBetter.omd', None, inputData, outputData)
#inputData, outputData = generateData('C:/Users/granb/omf/omf/scratch/CIGAR/test_large-R5-35.00-1.glm_CLEAN.omd', None, inputData, outputData)

print(inputData)
print(outputData)

N = int(len(inputData) * .9)

X_train = []
y_train = []
X_test = []
y_test = []
row = 0

while row < N:
	X_train.append(inputData[row])
	y_train.append(outputData[row])
	row += 1

while row < len(inputData):
	X_test.append(inputData[row])
	y_test.append(outputData[row])
	row += 1

X_train = array(X_train)
y_train = array(y_train)
X_test = array(X_test)
y_test = array(y_test)

clf = svm.SVC(kernel='linear')

clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

print('Accuracy:',metrics.accuracy_score(y_test, y_pred))
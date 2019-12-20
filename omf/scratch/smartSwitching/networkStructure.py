import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
import pandas as pd
import numpy as np
import math
from matplotlib import pyplot as plt
import omf
import networkx as nx
import scipy.stats as stats
import csv
from operator import itemgetter
import re
from sklearn import svm
from sklearn import metrics
from numpy import array
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from jinja2 import Template
from __neoMetaModel__ import *
from omf.models import __neoMetaModel__

# OMF imports
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf import geo, feeder

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *

# Model metadata:
tooltip = "networkStructure determines whether connectivity information is correct, given voltage and/or distance information."
modelName, template = metadata(__file__)
hidden = True
	
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

def generateData(pathToOmd, pathToCsv, workDir, useDist, useVolt):
	omd = json.load(open(pathToOmd))
	tree = omd.get('tree', {})
	attachments = omd.get('attachments',[])

	# # check to see if work directory is specified
	# if not workDir:
	# 	workDir = tempfile.mkdtemp()
	# 	print '@@@@@@', workDir

	# if useVolt == 'True':
	# 	def safeInt(x):
	# 			try: return int(x)
	# 			except: return 0

	# 	biggestKey = max([safeInt(x) for x in tree.keys()])

	# 	CLOCK_START = '2000-01-01 0:00:00'
	# 	dt_start = parser.parse(CLOCK_START)
	# 	dt_end = dt_start + relativedelta(day=0, hour=0, minute=5, second=0)
	# 	CLOCK_END = str(dt_end)
	# 	CLOCK_RANGE = CLOCK_START + ',' + CLOCK_END

	# 	index = 1
	# 	for key in tree:
	# 		if 'clock' in tree[key]:
	# 			tree[key]['starttime'] = "'" + CLOCK_START + "'"
	# 			tree[key]['stoptime'] = "'" + CLOCK_END + "'"

	# 	# create volt and current line dumps
	# 	tree[str(biggestKey*10 + index)] = {"object":"voltdump","filename":"voltDump.csv", 'runtime': 'INIT'}

	# 	attachments = []
	# 	# Run Gridlab.
	# 	if not workDir:
	# 		workDir = tempfile.mkdtemp()
	# 		print '@@@@@@', workDir
	# 	gridlabOut = gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

	outageMap = geo.omdGeoJson(pathToOmd, conversion = False)

	if useDist == 'True':
		with open(workDir + '/nodes.csv', mode='wb') as nodes:

			fieldnames = ['node_name', 'coord1', 'coord2']
			writer = csv.DictWriter(nodes, fieldnames)
			writer.writeheader()

			for key in tree.keys():
				obtype = tree[key].get("object","")
				if obtype.startswith('node') or obtype.startswith('load') or obtype.startswith('capacitor') or obtype.startswith('meter') or obtype.startswith('triplex_node') or obtype.startswith('triplex_meter'):
					coord1, coord2 = nodeToCoords(outageMap, tree[key]['name'])
					writer.writerow({'node_name': tree[key]['name'], 'coord1': coord1, 'coord2': coord2})
		nodes.close()

	with open(workDir + '/connectivity.csv', mode= 'wb') as connectivity:

		fieldnames = ['first_node', 'second_node']
		writer = csv.DictWriter(connectivity, fieldnames)
		writer.writeheader()

		for key in tree.keys():
			obtype = tree[key].get("object","")
			if obtype.startswith('underground_line') or obtype.startswith('overhead_line') or obtype.startswith('triplex_line') or obtype.startswith('switch') or obtype.startswith('recloser') or obtype.startswith('transformer') or obtype.startswith('fuse'):
				if 'from' in tree[key].keys() and 'to' in tree[key].keys():
					writer.writerow({'first_node': tree[key]['from'], 'second_node': tree[key]['to']})
	connectivity.close()

	connectivity = pd.read_csv(workDir + '/connectivity.csv')

	if useDist == 'True':
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

	if useVolt == 'True':
		volt = pd.read_csv(pathToCsv)
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
		volt.to_csv(workDir + '/volt2.csv')
		volt = pd.read_csv(workDir + '/volt2.csv')
	
	if useDist == 'True':
		row_count = nodes.shape[0]
	elif useVolt == 'True':
		row_count = volt.shape[0]
	else: raise ValueError('Either voltage or distance data must be used.')

	connectivity_count = connectivity.shape[0]

	inputDataDist = [[0 for x in range(row_count)] for y in range(row_count)]
	inputDataVolt = [[0 for x in range(row_count)] for y in range(row_count)]
	outputData = [[0 for x in range(row_count)] for y in range(row_count)]

	row = 0
	while row < row_count:
		column = row
		while column < row_count:
			if useDist == 'True':
				dataDist = []
				rowName = nodes.loc[row, 'node_name']
				colName = nodes.loc[column, 'node_name']
			if useVolt == 'True':
				dataVolt = []
				rowName = volt.loc[row, 'node_name']
				colName = volt.loc[column, 'node_name']
			
			if useDist == 'True':
				if ((nodes.loc[row, 'coord1'] - nodes.loc[column, 'coord1'])**2 + (nodes.loc[row, 'coord2'] - nodes.loc[column, 'coord2'])**2) > 10e-15:
					distance = math.sqrt((nodes.loc[row, 'coord1'] - nodes.loc[column, 'coord1'])**2 + (nodes.loc[row, 'coord2'] - nodes.loc[column, 'coord2'])**2)
				else:
					distance = 0.0
				if distance > 10e-15:
					dataDist.append(distance)
				else:
					dataDist.append(0.0)
			if useVolt == 'True':
				if (math.sqrt((float(volt.loc[row, 'voltA_real']) - float(volt.loc[column, 'voltA_real']))**2 + (float(volt.loc[row, 'voltA_imag']) - float(volt.loc[column, 'voltA_imag']))**2)) > 0:
					dataVolt.append(math.sqrt((float(volt.loc[row, 'voltA_real']) - float(volt.loc[column, 'voltA_real']))**2 + (float(volt.loc[row, 'voltA_imag']) - float(volt.loc[column, 'voltA_imag']))**2))
				else:
					dataVolt.append(0.0)	
				if (math.sqrt((float(volt.loc[row, 'voltB_real']) - float(volt.loc[column, 'voltB_real']))**2 + (float(volt.loc[row, 'voltB_imag']) - float(volt.loc[column, 'voltB_imag']))**2)) > 0:
					dataVolt.append(math.sqrt((float(volt.loc[row, 'voltB_real']) - float(volt.loc[column, 'voltB_real']))**2 + (float(volt.loc[row, 'voltB_imag']) - float(volt.loc[column, 'voltB_imag']))**2))
				else:
					dataVolt.append(0.0)
				if (math.sqrt((float(volt.loc[row, 'voltC_real']) - float(volt.loc[column, 'voltC_real']))**2 + (float(volt.loc[row, 'voltC_imag']) - float(volt.loc[column, 'voltC_imag']))**2)) > 0:
					dataVolt.append(math.sqrt((float(volt.loc[row, 'voltC_real']) - float(volt.loc[column, 'voltC_real']))**2 + (float(volt.loc[row, 'voltC_imag']) - float(volt.loc[column, 'voltC_imag']))**2))
				else:
					dataVolt.append(0.0)

			conEntry = 0
			found = False
			while conEntry < connectivity_count:
				if ((rowName == connectivity.loc[conEntry, 'first_node'] and colName == connectivity.loc[conEntry, 'second_node']) or (rowName == connectivity.loc[conEntry, 'second_node'] and colName == connectivity.loc[conEntry, 'first_node'])):
					outputData[row][column] = -1
					outputData[column][row] = -1
					found = True
					break
				conEntry += 1
			
			if found == False:
				outputData[row][column] = 0
				outputData[column][row] = 0
			
			if useVolt == 'True':
				inputDataVolt[row][column] = sum(dataVolt)
				inputDataVolt[column][row] = sum(dataVolt)

			if useDist == 'True':
				inputDataDist[row][column] = sum(dataDist)
				inputDataDist[column][row] = sum(dataDist)
			
			column += 1
		row += 1
	
	if useDist == 'False':
		nodes = None
	if useVolt == 'False':
		volt = None
	
	return nodes, volt, tree, workDir, inputDataDist, inputDataVolt, outputData

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
				if k not in X and graph[x][k] != 0.0:
					crossing.add((x, k))
		
		# find the edge with smallest crossing weight
		if len(crossing) == 0: break
		edge = sorted(crossing, key=lambda e:graph[e[0]][e[1]])[0]
		# add the edge found to the MST
		MST.add(edge)
		# add the new vertex to X
		X.add(edge[1])
	return MST

def testingSimple(testPath, pathToCsv, workDir, useDist, useVolt):

	# feeder.glmToOmd('C:/Users/granb/omf/omf/solvers/gridlabdnew/taxonomy_feeders/autotest/test_R1-12.47-2.glm', 'C:/Users/granb/omf/omf/scratch/smartSwitching/test_R1-12.47-2.omd', attachFilePaths=[])
	# nodes, tree, workDir, inputDataDist, inputDataVolt, outputData = generateData(omf.omfDir + '/scratch/smartSwitching/test_ieee123nodeBetter.omd', None, None, None)
	nodes, volt, tree, workDir, inputDataDist, inputDataVolt, outputData = generateData(testPath, pathToCsv, workDir, useDist, useVolt)
	# nodes, tree, workDir, inputDataDist, inputDataVolt, outputData = generateData(omf.omfDir + '/scratch/smartSwitching/test_R1-12.47-2.omd', None, None, None)
	if useDist == 'True':
		size = len(inputDataDist)
	else:
		size = len(inputDataVolt)

	distMST = [[0 for x in range(size)] for y in range(size)]
	voltMST = [[0 for x in range(size)] for y in range(size)]
	actualMST = [[0 for x in range(size)] for y in range(size)]

	expectedDist = prim(inputDataDist)
	expectedVolt = prim(inputDataVolt)
	actual = prim(outputData)

	X_test = []
	xdistMST1D = []
	xvoltMST1D = []
	y_test = []

	for val in expectedDist:
		distMST[val[0]][val[1]] = 1

	for val in expectedVolt:
	 	voltMST[val[0]][val[1]] = 1

	for val in actual:
		actualMST[val[0]][val[1]] = 1

	def graph(graphname, mst):
		plt.close()
		outGraph = nx.Graph()
		for key in tree:
			item = tree[key]
			if 'name' in item.keys():
				obType = item.get('object')
				if 'parent' in item.keys():
					outGraph.add_edge(item['name'],item['parent'], attr_dict={'type':'parentChild','phases':1})
					outGraph.node[item['name']]['type']=item['object']
					# Note that attached houses via gridEdit.html won't have lat/lon values, so this try is a workaround.
					try: outGraph.node[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
					except: outGraph.node[item['name']]['pos']=(0.0,0.0)
				elif item['name'] in outGraph:
					# Edge already led to node's addition, so just set the attributes:
					outGraph.node[item['name']]['type']=item['object']
				else:
					outGraph.add_node(item['name'],attr_dict={'type':item['object']})
				if 'latitude' in item.keys() and 'longitude' in item.keys():
					try: outGraph.node.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
					except: outGraph.node.get(item['name'],{})['pos']=(0.0,0.0)
		size = len(mst)
		row = 0
		while row < size:
			column = 0
			while column < size:
				if mst[row][column] == 1:
					if useDist == 'True':
						outGraph.add_edge(str(nodes.loc[row,'node_name']),str(nodes.loc[column,'node_name']))
					else:
						outGraph.add_edge(str(volt.loc[row,'node_name']),str(volt.loc[column,'node_name']))
				column += 1
			row += 1
		feeder.latLonNxGraph(outGraph, labels=True, neatoLayout=True, showPlot=True)
		plt.savefig(workDir + graphname)

	graph('/actual_graph.png', actualMST)
	graph('/distance_graph.png', distMST)
	graph('/voltage_graph.png', voltMST)

	row = 0
	while row < size:
		column = 0
		while column < size:
			mstTemp = []
			mstTemp.append(distMST[row][column])
			mstTemp.append(voltMST[row][column])
			X_test.append(mstTemp)
			xdistMST1D.append(distMST[row][column])
			xvoltMST1D.append(voltMST[row][column])
			y_test.append(actualMST[row][column])
			column += 1
		row += 1

	# print(xdistMST1D)
	# print(xvoltMST1D)
	# print(y_test)

	#print('DistDif1:',expectedDist.difference(actual))
	#print('DistDif2:',actual.difference(expectedDist))

	#print('VoltDif1:',expectedVolt.difference(actual))
	#print('VoltDif2:',actual.difference(expectedVolt))

	distanceAccuracy = 1.0 - (abs(float(len(actual.difference(expectedDist)))))/float(len(actual))
	voltageAccuracy = 1.0 - (abs(float(len(actual.difference(expectedVolt)))))/float(len(actual))

	def testRandom(numberOfNodes, accuracy):
		nodesCorrect = math.floor(numberOfNodes * accuracy)

		# calculate the probability that the number of correctly-guessed edges in the MST could have been arrived at randomly
		s = lambda numberOfNodes, nodesCorrect : sum(float(pow(numberOfNodes - i, i)) / float(pow(numberOfNodes, numberOfNodes - 2)) for i in range(0, int(numberOfNodes - nodesCorrect)))
		if s(numberOfNodes, nodesCorrect) < 3e-7:
			return True
		return False

	distanceTest = 'Failed'
	voltageTest = 'Failed'

	distanceSigma = testRandom(len(inputDataDist), distanceAccuracy)
	if useDist == 'True':
		if distanceSigma is True:
			distanceTest = 'Passed'

	voltageSigma = testRandom(len(inputDataVolt), voltageAccuracy)
	if useVolt == 'True':
		if voltageSigma is True:
			voltageTest = 'Passed'

	def connectivityHTML(distanceAccuracy, voltageAccuracy, distanceTest, voltageTest):
		html_str = """
			<div style="text-align:center">
				<p style="padding-top:10px; padding-bottom:10px;"><b>Distance Test:</b><span style="padding-left:1em">"""+str(distanceTest)+"""</span><span style="padding-left:2em"><b>Voltage Test:</b><span style="padding-left:1em">"""+str(voltageTest)+"""</span><span style="padding-left:2em"><b>Distance Percent Similar:</b><span style="padding-left:1em">"""+str(int(distanceAccuracy * 100))+"""</span><span style="padding-left:2em"><b>Voltage Percent Similar:</b><span style="padding-left:1em">"""+str(int(voltageAccuracy * 100))+"""</span></span></p>
			</div>"""
		return html_str

	connectivityStats = connectivityHTML(
			distanceAccuracy = distanceAccuracy,
			voltageAccuracy = voltageAccuracy,
			distanceTest = distanceTest,
			voltageTest = voltageTest)

	with open(pJoin(workDir, "statsCalc.html"), "w") as statsFile:
		statsFile.write(connectivityStats)

	return {'X_test': X_test, 'y_test': y_test, 'distanceAccuracy': distanceAccuracy, 'distanceSigma': distanceSigma, 'voltageAccuracy': voltageAccuracy, 'voltageSigma': voltageSigma}, X_test, y_test

def createTrainingData(trainPath, pathToCsv, workDir, X_train, y_train, useDist, useVolt):

	nodes, volt, tree, workDir, inputDataDist, inputDataVolt, outputData = generateData(trainPath, pathToCsv, workDir, useDist, useVolt)

	if X_train == None or y_train == None:
		X_train = []
		y_train = []

	size = len(inputDataDist)
	distMST = [[0 for x in range(size)] for y in range(size)]
	voltMST = [[0 for x in range(size)] for y in range(size)]
	actualMST = [[0 for x in range(size)] for y in range(size)]

	expectedDist = prim(inputDataDist)
	expectedVolt = prim(inputDataVolt)
	actual = prim(outputData)

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
			X_train.append(mstTemp)
			y_train.append(actualMST[row][column])
			column += 1
		row += 1

	return X_train, y_train

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}
	# Write the feeder
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName

	with open(pJoin(modelDir, inputDict['voltageFileName']), 'w') as f:
		pathToData = f.name
		f.write(inputDict['voltageData'])

	plotOuts, X_test, y_test = testingSimple(
		modelDir + '/' + feederName + '.omd', #OMD Path
		pathToData,
		modelDir, #Work directory.
		inputDict['useDist'], # 'True'
		inputDict['useVolt']) # 'True')

	if inputDict['useSVM'] == 'True':
		X_train, y_train = createTrainingData(omf.omfDir + '/static/publicFeeders/ieee37nodeFaultTester.omd', omf.omfDir + '/scratch/smartSwitching/volt1.csv', modelDir, None, None, inputDict['useDist'], inputDict['useVolt'])
		# X_train, y_train = createTrainingData(omf.omfDir + '/static/publicFeeders/test_ieee123nodeBetter.omd', omf.omfDir + '/scratch/smartSwitching/volttest_ieee123nodeBetter.csv', modelDir, X_train, y_train, inputDict['useDist'], inputDict['useVolt'])
		# X_train, y_train = createTrainingData(omf.omfDir + '/static/publicFeeders/test_R1-12.47-3.omd', omf.omfDir + '/scratch/smartSwitching/volttest_R1-12.47-3.csv', modelDir, X_train, y_train, inputDict['useDist'], inputDict['useVolt'])

		X_train = array(X_train)
		y_train = array(y_train)
		X_test = array(X_test)
		y_test = array(y_test)

		clf = svm.SVC(kernel='sigmoid')

		clf.fit(X_train, y_train)

		y_pred = clf.predict(X_test)

		print('Accuracy:',metrics.accuracy_score(y_test, y_pred))
		print('Precision:',metrics.precision_score(y_test, y_pred))
		print('Recall:',metrics.recall_score(y_test, y_pred))

	# Image outputs.
	with open(pJoin(modelDir,"distance_graph.png"),"rb") as inFile:

		outData["distance_graph.png"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"voltage_graph.png"),"rb") as inFile:
		outData["voltage_graph.png"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"actual_graph.png"),"rb") as inFile:
		outData["actual_graph.png"] = inFile.read().encode("base64")

	# Textual outputs of cost statistic
	with open(pJoin(modelDir,"statsCalc.html"),"rb") as inFile:
		outData["statsCalc"] = inFile.read()

	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"feederName1": "ieee37nodeFaultTester",
		"useDist": "True",
		"useVolt": "True",
		"useSVM": "False",
		"voltageFileName": "volt1.csv",
		"voltageData": open(pJoin(__neoMetaModel__._omfDir,"scratch","smartSwitching","volt1.csv"), "r").read(),
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
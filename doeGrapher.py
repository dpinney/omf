#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import matplotlib as m
m.use('Agg')
import matplotlib.pyplot as p
import math
from subprocess import call
import treeParser
import networkx as nx
import matplotlib.patheffects as pe


# Take a filename to a list of timeseries vectors.
def csvToTimeseries(fileName):
	# Helper function that translates csv values to reasonable floats (or header values to strings):
	def strClean(x):
		if x == 'OPEN':
			return 1.0
		elif x == 'CLOSED':
			return 0.0
		elif x[0] == '+':
			return float(x[1:])
		elif x[0] == '-':
			return float(x)
		elif x[0].isdigit() and x[-1].isdigit():
			return float(x)
		else:
			return x
	openfile = open(fileName)
	data = openfile.read()
	lines = data.splitlines()
	array = map(lambda x:x.split(','), lines)
	cleanArray = [map(strClean, x) for x in array]
	# Magic number 8 is the number of header rows in each csv.
	arrayNoHeaders = cleanArray[8:]
	# Drop the timestamp column:
	trimmedArray = [line[1:] for line in arrayNoHeaders]
	timeSeriesList = zip(*trimmedArray)
	return timeSeriesList

def crossProd(realVec,imVec):
	return map(lambda x:math.sqrt(x[0]*x[0]+x[1]*x[1]), zip(realVec, imVec))

def graphVoltFile(voltFile):
	voltTSL = csvToTimeseries(voltFile)
	p.title(voltFile)
	p.plot(crossProd(voltTSL[0][1:],voltTSL[1][1:]))
	p.plot(crossProd(voltTSL[2][1:],voltTSL[3][1:]))
	p.plot(crossProd(voltTSL[4][1:],voltTSL[5][1:]))

def graphCapFile(capFile):
	capTsl = csvToTimeseries(capFile)
	p.title(capFile)
	p.ylim(-0.2,1.2)
	p.plot(capTsl[0][1:])
	p.plot(capTsl[1][1:])
	p.plot(capTsl[2][1:])

def graphRegFile(regFile, partNumber):
	# Note: there are 5 parts that come from any one reg file.
	regSeriesList = csvToTimeseries(regFile)
	if partNumber == 1:
		p.title(regFile + ' Tap Positions')
		p.plot(regSeriesList[0][1:])
		p.plot(regSeriesList[1][1:])
		p.plot(regSeriesList[2][1:])
	elif partNumber == 2:
		p.title(regFile + ' Real Power')
		p.plot(regSeriesList[3][1:])
		p.plot(regSeriesList[5][1:])
		p.plot(regSeriesList[7][1:])
	elif partNumber == 3:
		p.title(regFile + ' Reactive Power')
		p.plot(regSeriesList[4][1:])
		p.plot(regSeriesList[6][1:])
		p.plot(regSeriesList[8][1:])
	elif partNumber == 4:
		p.title(regFile + ' Apparent Power')
		p.plot(crossProd(regSeriesList[3][1:],regSeriesList[4][1:]))
		p.plot(crossProd(regSeriesList[5][1:],regSeriesList[6][1:]))
		p.plot(crossProd(regSeriesList[7][1:],regSeriesList[8][1:]))
	elif partNumber == 5:
		p.title(regFile + ' Power Factor')
		TotalRealPower = map(sum, zip(regSeriesList[3][1:],regSeriesList[5][1:],regSeriesList[7][1:]))
		TotalReactivePower = map(sum, zip(regSeriesList[4][1:],regSeriesList[6][1:],regSeriesList[8][1:]))
		TotalPowerFactor = map(lambda x:math.cos(math.atan(x[0]/x[1])), zip(TotalReactivePower,TotalRealPower))
		p.plot(TotalPowerFactor)

def graphGlmFile(glmFile):
	glmTree = treeParser.parse(glmFile)
	glmGraph = nx.Graph()
	nodeNodes = []
	for x in glmTree:
		if 'from' in glmTree[x] and 'to' in glmTree[x]:
			glmGraph.add_edge(glmTree[x]['from'],glmTree[x]['to'])
		if 'parent' in glmTree[x] and 'name' in glmTree[x]:
			glmGraph.add_edge(glmTree[x]['name'],glmTree[x]['parent'])
		if 'object' in glmTree[x] and glmTree[x]['object'] == 'node':
			nodeNodes.append(glmTree[x]['name'])
	nodeNodes = set(nodeNodes).intersection(set(glmGraph.nodes()))
	notNodes = set(glmGraph.nodes()) - nodeNodes
	layout = nx.spring_layout(glmGraph)
	nx.draw_networkx_nodes(glmGraph,layout,notNodes,alpha=0.7,node_size=150)
	nx.draw_networkx_nodes(glmGraph,layout,nodeNodes,alpha=0.7,node_color='b')
	nx.draw_networkx_edges(glmGraph,layout,alpha=0.9)
	# Labels only if we have few nodes:
	if len(glmGraph.nodes()) < 25:
		labels = nx.draw_networkx_labels(glmGraph,layout)
		for key in labels:
			p.setp(labels[key], path_effects=[pe.withStroke(linewidth=3, foreground="w")])
	p.axis('off')
	p.title(glmFile)

def buildFromDir(workDir):
	# Gather all the csv files we can process.
	allFiles = os.listdir(workDir)
	allCsvs = [x for x in allFiles if x.endswith('.csv')]
	voltageCsvs = [x for x in allCsvs if x.startswith('Voltage_')]
	regulatorCsvs = [x for x in allCsvs if x.startswith('Regulator_')]
	capacitorCsvs = [x for x in allCsvs if x.startswith('Capacitor_')]
	glm = 'main.glm'
	# Graph everything.
	for fileName in regulatorCsvs:
		for x in xrange(5):
			p.clf()
			graphRegFile(workDir + '/' + fileName, x + 1)
			p.savefig(workDir + '/' + fileName + '_' + str(x) + '.png', dpi=60)
	for fileName in voltageCsvs:
		p.clf()
		graphVoltFile(workDir + '/' + fileName)
		p.savefig(workDir + '/' + fileName + '.png', dpi=60)
	for fileName in capacitorCsvs:
		p.clf()
		graphCapFile(workDir + '/' + fileName)
		p.savefig(workDir + '/' + fileName + '.png', dpi=60)
	p.clf()
	graphGlmFile(workDir + '/' + glm)
	p.savefig(workDir + '/' + glm + '.png', dpi=60)

def main():
	buildFromDir('static/analyses/chicken')

if __name__ == '__main__':
	main()
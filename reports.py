#!/usr/bin/env python

import os
import math
import itertools

def listAll():
	allAttributes = globals().keys()
	return [x for x in allAttributes if not x.startswith('_') and x not in ['os', 'math', 'itertools', 'listAll']]


# def powerflow(analysisName):
# 	pngs = []
# 	for study in os.listdir('static/analyses/' + analysisName + '/studies/'):
# 		for fileName in os.listdir('static/analyses/' + analysisName + '/studies/' + study):
# 			if fileName.endswith('.png'): pngs.append('studies/' + study + '/' + fileName)
# 	return {'reportType':'powerflow', 'pngs':pngs}

def runtimeStats(analysisName):
	stdouts = []
	for study in os.listdir('static/analyses/' + analysisName + '/studies/'):
		with open('static/analyses/' + analysisName + '/studies/' + study + '/stdout.txt', 'r') as stdout:
		# Hack: drop leading \r newlines:
			stdouts.append(study.upper() + '\n\n' + stdout.read().replace('\r',''))
	return {'reportType':'runtimeStats', 'stdouts':stdouts}

def capacitorActivation(analysisName):
	dataTree = {}
	pathPrefix = './static/analyses/' + analysisName
	for study in os.listdir(pathPrefix + '/studies/'):
		dataTree[study] = {}
		capFileNames = filter(lambda x:x.startswith('Capacitor_') and x.endswith('.csv'), os.listdir(pathPrefix + '/studies/' + study))
		for capacitor in capFileNames:
			dataTree[study][capacitor.replace('.csv','')] = __csvToArray__(pathPrefix + '/studies/' + study + '/' + capacitor)
	return {'reportType':'capacitorActivation', 'dataTree':dataTree}

def regulatorPowerflow(analysisName):
	dataTree = {}
	pathPrefix = './static/analyses/' + analysisName
	for study in os.listdir(pathPrefix + '/studies/'):
		dataTree[study] = {}
		regFileNames = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('Regulator_') and x.endswith('.csv')]
		for regulator in regFileNames:
			cleanReg = regulator.replace('.csv','')
			dataTree[study][cleanReg] = {}
			fullArray = __csvToArray__(pathPrefix + '/studies/' + study + '/' + regulator)
			dataTree[study][cleanReg]['realPower'] = [[row[0], row[4], row[6], row[8]] for row in fullArray]
			dataTree[study][cleanReg]['reactivePower'] = [[row[0], row[5], row[7], row[9]] for row in fullArray]
			dataTree[study][cleanReg]['tapPositions'] = [[row[0],row[1],row[2],row[3]] for row in fullArray]
			# NOTE: we operate on the values [1:] then put the headers back in a second step.
			dataTree[study][cleanReg]['apparentPower'] = [[row[0], __pyth__(row[4],row[5]), __pyth__(row[6],row[7]), __pyth__(row[8],row[9])] for row in fullArray[1:]]
			dataTree[study][cleanReg]['apparentPower'].insert(0,['# timestamp','Tap_A','Tap_B','Tap_C'])
			dataTree[study][cleanReg]['powerFactor'] = [[row[0], math.cos(math.atan((row[5]+row[7]+row[9])/(row[4]+row[6]+row[8])))] for row in fullArray[1:]]
			dataTree[study][cleanReg]['powerFactor'].insert(0,['# timestamp','Power Factor'])
	return {'reportType':'regulatorPowerflow', 'dataTree':dataTree}

def studyDetails(analysisName):
	studies = []
	climates = [['location','marker']]
	pathPrefix = './static/analyses/' + analysisName
	with open(pathPrefix + '/metadata.txt','r') as anaMdFile:
		created = eval(anaMdFile.read())['created']
	for study in os.listdir(pathPrefix + '/studies/'):
		with open(pathPrefix + '/studies/' + study + '/metadata.txt', 'r') as mdFile:
			metadata = eval(mdFile.read())
		climates.append([metadata['climate'],1])
		studies.append([metadata['name'], metadata['sourceFeeder']])
	return {'reportType':'studyDetails', 'climates':climates, 'studies':studies, 'created':created}

def voltageBand(analysisName):
	dataTree = {}
	pathPrefix = './static/analyses/' + analysisName
	for study in os.listdir(pathPrefix + '/studies/'):
		dataTree[study] = {}
		for fileName in os.listdir(pathPrefix + '/studies/' + study):
			if fileName.startswith('Voltage_') and fileName.endswith('.csv'):
				fullArray = __csvToArray__(pathPrefix + '/studies/' + study + '/' + fileName)
				dataTree[study][fileName] = [[row[0], __pyth__(row[1],row[2]),__pyth__(row[3],row[4]),__pyth__(row[5],row[6])] for row in fullArray[1:]]
				dataTree[study][fileName].insert(0,[fullArray[0][0],'A','B','C'])
		# INSANE ONE-LINER: join all the voltage data on timestamp.
		dataTree[study] = zip(*[dataTree[study][key] for key in dataTree[study]])
		# Then flatten without the head:
		dataTree[study] = map(__flat1__, dataTree[study][1:])
		# Then filter:
		def filterStrings(aList):
			return [aList[0]] + filter(lambda x:type(x) is not str, aList[1:])
		dataTree[study] = map(filterStrings, dataTree[study][1:])
		# Then min/max/avg:
		dataTree[study] = map(lambda x:[x[0],min(x[1:]),sum(x[1:])/len(x[1:]),max(x[1:])], dataTree[study])
		# Then put the head back on.
		dataTree[study].insert(0,['# timestamp','min','avg','max'])
	return {'reportType':'voltageBand', 'dataTree':dataTree}

def __csvToArray__(fileName):
	''' Take a filename to a list of timeseries vectors. Internal method. '''
	def strClean(x):
		# Helper function that translates csv values to reasonable floats (or header values to strings):
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
	with open(fileName) as openfile:
		data = openfile.read()
	lines = data.splitlines()
	array = map(lambda x:x.split(','), lines)
	cleanArray = [map(strClean, x) for x in array]
	# Magic number 8 is the number of header rows in each csv.
	arrayNoHeaders = cleanArray[8:]
	# Drop the timestamp column:
	return arrayNoHeaders

def __pyth__(x,y):
	''' helper function to compute the third side of the triangle'''
	return math.sqrt(x**2 + y**2)

def __flat1__(aList):
	''' Flatten one level. Go from e.g. [[1],[2],[3,4],[[5,6],[7,8]]] to [1,2,3,4,[5,6],[7,8]]'''
	return list(itertools.chain(*aList))

# # TEST CODE
# stuff = regulatorPowerflow('clothing')
# from pprint import pprint
# pprint(stuff)
# stuff = voltageBand('clothing')
# sample = stuff['dataTree']['shirt']
# print sample

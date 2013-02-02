#!/usr/bin/env python

import time
import os
import csv
from pprint import pformat
from pprint import pprint
import re

analysisPath = '../analyses/zSolar Trio/'

def seriesTranspose(theArray):
	return {i[0]:list(i)[1:] for i in zip(*theArray)}

def csvToArray(fileName):
	''' Take a filename to a list of timeseries vectors. Internal method. '''
	def strClean(x):
		# Helper function that translates csv values to reasonable floats (or header values to strings):
		if x == 'OPEN':
			return 1.0
		elif x == 'CLOSED':
			return 0.0
		elif x[0].isdigit() and x[-1].isdigit():
			return float(x)
		# Look for strings of the type '+32.0+68.32d':
		elif re.findall('[+-]\d+.*[+-]\d+.*d',x) != []:
			embedNums = re.findall('-*\d+',x)
			floatConv = map(float, embedNums)
			squares = map(lambda x:x**2, floatConv)
			return math.sqrt(sum(squares))
		elif x[0] == '+':
			return float(x[1:])
		elif x[0] == '-':
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

def anaSuck(analysisPath):
	studyNames = os.listdir(analysisPath + '/studies/')
	data = {}
	for study in studyNames:
		data[study] = {}
		csvFiles = os.listdir(analysisPath + '/studies/' + study)
		for cName in csvFiles:
			if cName.endswith('.csv'):
				arr = csvToArray(analysisPath + '/studies/' + study + '/' + cName)
				data[study][cName] = seriesTranspose(arr)
				# with open(analysisPath + '/studies/' + study + '/' + cName, 'rb') as csvFile:
				# 	reader = csv.reader(csvFile)
				# 	data[study][cName] = list(reader)
	return data

def anaSubSuck(analysisPath, fileNameTest):
	''' Take a study and put all its data into a nested object {studyName:{fileName:{metricName:[...]}}} '''
	studyNames = os.listdir(analysisPath + '/studies/')
	data = {}
	for study in studyNames:
		data[study] = {}
		csvFiles = os.listdir(analysisPath + '/studies/' + study)
		for cName in csvFiles:
			if fileNameTest(cName) and cName.endswith('.csv'):
				arr = csvToArray(analysisPath + '/studies/' + study + '/' + cName)
				data[study][cName] = seriesTranspose(arr)
	return data

x = anaSuck(analysisPath)
y = anaSubSuck(analysisPath, lambda z:z.startswith('Climate_'))

pprint(y, depth=3)
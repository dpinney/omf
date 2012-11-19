#!/usr/bin/env python

import os
import re
from pprint import pprint
from datetime import datetime as dt
import math

# Helper function:
def csvToArray(fileName):
	''' Take a filename to a list of timeseries vectors. Internal method. '''
	def strClean(x):
		# Helper function that translates csv values to reasonable floats (or header values to strings):
		if x == 'OPEN':
			return 1.0
		elif x == 'CLOSED':
			return 0.0
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
	return arrayNoHeaders

def aggCsv(csvArray, listFuncOrFuncs, level):
	# Different substring depending on what level we aggregate to:
	if level=='month':
		endPos = 7
	elif level=='day':
		endPos = 10
	# List of the dates we'll aggregate up to:
	dateList = list(set([row[0][0:endPos] for row in csvArray]))
	dateList.sort()
	# for each date, calculate the listFuncOrFuncs of each column:
	def aggDateGroup(date):
		listMatr = [row for row in csvArray if row[0][0:endPos]==date]
		transposedNoHeaders = [list(colRow) for colRow in zip(*listMatr)[1:]]
		# If we've got a single listFunc, use that:
		if hasattr(listFuncOrFuncs, '__call__'):
			return map(listFuncOrFuncs, transposedNoHeaders)
		# Or, if we have {1:fun, 2:fun2, etc.} apply one to each column:
		elif hasattr(listFuncOrFuncs, 'keys'):
			return [listFuncOrFuncs[rowNum](transposedNoHeaders[rowNum]) for rowNum in xrange(0,len(transposedNoHeaders))]
	# find the aggregated version for each date item:
	return [[date] + aggDateGroup(date) for date in dateList]

def avg(inList):
	return sum(inList)/len(inList)


dirPath = '../analyses/HourRez2BigFeeder/studies/test/'
csvNames = [x for x in os.listdir(dirPath) if x.endswith('.csv')]

swingPath = dirPath + 'SwingKids_transformer.csv'
capPath = dirPath + 'Capacitor_CAP1.csv'
climatePath = dirPath + 'Climate_Climate.csv'
regulatorPath = dirPath + 'Regulator_Reg1.csv'
voltagePath = dirPath + 'VoltageJiggle.csv'

# Avg the swingKids. We'll also want to max them and add that on, but first we have to calculate the apparent power.
print swingPath
swingData = csvToArray(swingPath)
pprint(swingData[0:3])
print '...'
pprint([swingData[0]] + aggCsv(swingData[1:], lambda x:sum(x)/len(x), 'day'))
pprint([swingData[0]] + aggCsv(swingData[1:], lambda x:sum(x)/len(x), 'month'))
print '\n\n\n'

# Caps get averaged.
print capPath
capData = csvToArray(capPath)
pprint(capData[0:3])
print '...'
pprint([capData[0]] + aggCsv(capData[1:], lambda x:sum(x)/len(x), 'day'))
pprint([capData[0]] + aggCsv(capData[1:], lambda x:sum(x)/len(x), 'month'))
print '\n\n\n'

# Maxing climate but summing insolation, rain.
print climatePath
climateData = csvToArray(climatePath)
pprint(climateData[0:3])
print '...'
funs = {0:max, 1:sum, 2:max, 3:sum, 4:max}
pprint([climateData[0]] + aggCsv(climateData[1:], lambda x:max(x), 'day'))
pprint([climateData[0]] + aggCsv(climateData[1:], lambda x:max(x), 'month'))
print '\n\n\n'

# Regulators get...
print regulatorPath
regData = csvToArray(regulatorPath)
pprint(regData[0:3])
print '...'
pprint([regData[0]] + aggCsv(regData[1:], lambda x:max(x), 'day'))
pprint([regData[0]] + aggCsv(regData[1:], lambda x:max(x), 'month'))
print '\n\n\n'

# Voltages get various things.
print voltagePath
voltData = csvToArray(voltagePath)
pprint(voltData[0:3])
print '...'
# TODO: must make this more mathematically rigorous than average stdDevs!!
funs = {0:min,1:lambda x:sum(x)/len(x),2:max,3:lambda x:sum(x)/len(x)}
pprint([voltData[0]] + aggCsv(voltData[1:], funs, 'day'))
pprint([voltData[0]] + aggCsv(voltData[1:], funs, 'month'))
print '\n\n\n'

# # Some code showing how a list of functions can be applied to a matrix:
# transposedNoHeaders = [[1,2,3],[4,5,6]]
# listFuncOrFuncs = {0:lambda x:max(x), 1:lambda y:sum(y)}
# print [listFuncOrFuncs[rowNum](transposedNoHeaders[rowNum]) for rowNum in xrange(0,len(transposedNoHeaders))]
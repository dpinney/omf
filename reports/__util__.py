#!/usr/bin/env python

import math
import re

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
	# Drop the timestamp column:
	return arrayNoHeaders

def aggCsv(csvArray, listFuncOrFuncs, level):
	''' Take a csv at the hour granularity, and aggregate to the day/month level '''
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

def pyth(x,y):
	''' helper function to compute the third side of the triangle--BUT KEEP SIGNS THE SAME FOR DG '''
	def sign(z):
		return (-1 if z<0 else 1)
	fullSign = sign(sign(x)*x*x + sign(y)*y*y)
	return fullSign*math.sqrt(x*x + y*y)

def flat1(aList):
	''' Flatten one level. Go from e.g. [[1],[2],[3,4],[[5,6],[7,8]]] to [1,2,3,4,[5,6],[7,8]]'''
	return list(itertools.chain(*aList))

def vecSum(*args):
	return map(sum,zip(*args))
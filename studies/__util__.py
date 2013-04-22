#!/usr/bin/env python

import math
import re
import os

def csvToArray(fileName):
	''' Take a filename to a list of timeseries vectors. Internal method. '''
	def strClean(x):
		# Helper function that translates csv values to reasonable floats (or header values to strings):
		if x == 'OPEN':
			return 1.0
		elif x == 'CLOSED':
			return 0.0
		# Look for strings of the type '+32.0+68.32d':
		elif x == '-1.#IND':
			return 0.0
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

def anaDataTree(studyPath, fileNameTest):
	''' Take a study and put all its data into a nested object {fileName:{metricName:[...]}} '''
	def seriesTranspose(theArray):
		return {i[0]:list(i)[1:] for i in zip(*theArray)}
	data = {}
	csvFiles = os.listdir(studyPath)
	for cName in csvFiles:
		if fileNameTest(cName) and cName.endswith('.csv'):
			arr = csvToArray(studyPath + '/' + cName)
			data[cName] = seriesTranspose(arr)
	return data

def aggSeries(timeStamps, timeSeries, func, level):
	''' Aggregate a list + timeStamps up to the required time level. '''
	# Different substring depending on what level we aggregate to:
	if level=='months': endPos = 7
	elif level=='days': endPos = 10
	combo = zip(timeStamps, timeSeries)
	def groupBy(inL, func):
		''' Take a list and func, and group items in place comparing with func. Make sure the func is an equivalence relation, or your brain will hurt. '''
		if inL == []: return inL
		if len(inL) == 1: return [inL]
		newL = [[inL[0]]]
		for item in inL[1:]:
			if func(item, newL[-1][0]):
				newL[-1].append(item)
			else:
				newL.append([item])
		return newL	
	# Group by level:
	groupedCombo = groupBy(combo, lambda x1,x2: x1[0][0:endPos]==x2[0][0:endPos])
	# Get rid of the timestamps:
	groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
	return map(func, groupedRaw)

def pyth(x,y):
	''' helper function to compute the third side of the triangle--BUT KEEP SIGNS THE SAME FOR DG '''
	def sign(z):
		return (-1 if z<0 else 1)
	fullSign = sign(sign(x)*x*x + sign(y)*y*y)
	return fullSign*math.sqrt(x*x + y*y)

def prod(inList):
	return reduce(lambda x,y:x*y, inList, 1)

def vecPyth(vx,vy):
	rows = zip(vx,vy)
	return map(lambda x:pyth(*x), rows)

def vecSum(*args):
	return map(sum,zip(*args))

def vecProd(*args):
	return map(prod, zip(*args))

def threePhasePowFac(ra,rb,rc,ia,ib,ic):
	rows = zip(ra,rb,rc,ia,ib,ic)
	def pfRow(row):
		return math.cos(math.atan((row[0]+row[1]+row[2])/(row[3]+row[4]+row[5])))
	return map(pfRow, rows)

def roundSig(x, sig=3):
	def roundPosSig(y):
		return round(y, sig-int(math.floor(math.log10(y)))-1)
	if x == 0: return 0
	elif x < 0: return -1*roundPosSig(-1*x)
	else: return roundPosSig(x)

def roundSeries(ser):
	return map(lambda x:roundSig(x,4), ser)


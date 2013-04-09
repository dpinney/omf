#!/usr/bin/env python

import math
import re
import os
from time import mktime
from datetime import datetime
import itertools
import json

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

def aggSeries(timeStamps, timeSeries, func, level):
	# Different substring depending on what level we aggregate to:
	if level=='month': endPos = 7
	elif level=='day': endPos = 10
	combo = zip(timeStamps, timeSeries)
	# Group by level:
	groupedCombo = groupBy(combo, lambda x1,x2: x1[0][0:endPos]==x2[0][0:endPos])
	# Get rid of the timestamps:
	groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
	return map(func, groupedRaw)

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

def anaDataTree(analysisPath, fileNameTest):
	''' Take a study and put all its data into a nested object {studyName:{fileName:{metricName:[...]}}} '''
	def seriesTranspose(theArray):
		return {i[0]:list(i)[1:] for i in zip(*theArray)}
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

def defaultGraphObject(resolution, startTimeStamp):
	timeMap = {'minutes':1,'hours':60,'days':1440}
	pointInterval = timeMap[resolution]*60*1000
	maxZoom = pointInterval*30
	def getPointStart(dateTimeStamp):
		if dateTimeStamp[-1].isdigit():
			stampOb = datetime.strptime(dateTimeStamp,'%Y-%m-%d')
		else:
			# Handle those dang arbitrary timezones.
			stampOb = datetime.strptime(dateTimeStamp.rsplit(' ',1)[0],'%Y-%m-%d %H:%M:%S')
		return int(mktime(stampOb.timetuple()))*1000
	pointStart = getPointStart(startTimeStamp)
	graphParameters = {
		'chart':{'renderTo':'', 'marginRight':20, 'marginBottom':20, 'zoomType':'x'},
		'title':{'text':None},
		'yAxis':{'title':{'text':None, 'style':{'color':'gray'}}},
		'legend':{'layout':'horizontal', 'align':'top', 'verticalAlign':'top', 'x':50, 'y':-10, 'borderWidth':0},
		'credits':{'enabled':False},
		'xAxis':{'type':'datetime','maxZoom':maxZoom, 'tickColor':'gray','lineColor':'gray'},
		'plotOptions':{'line':{'marker':{'enabled':False}}, 'series':{'shadow':False, 'pointInterval':pointInterval, 'pointStart':pointStart}},
		'series':[]
	}
	return graphParameters

def fileSlurp(fileName):
	with open(fileName,'r') as openFile:
		return openFile.read()

def roundSig(x, sig=3):
	def roundPosSig(y):
		return round(y, sig-int(math.floor(math.log10(y)))-1)
	if x == 0: return 0
	elif x < 0: return -1*roundPosSig(-1*x)
	else: return roundPosSig(x)

def roundSeries(ser):
	return map(lambda x:roundSig(x,4), ser)

def getResolution(analysisName):
	with open('analyses/' + analysisName + '/metadata.json') as mdFile:
		md = json.load(mdFile)
	return md['simLengthUnits']

def rainbow(dic, key, colorList):
	pos = dic.keys().index(key)
	modPos = pos % len(colorList)
	return colorList[modPos]
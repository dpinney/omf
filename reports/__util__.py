#!/usr/bin/env python

import math
import re
import os
from time import mktime
from datetime import datetime
import itertools
import json

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

def totalEnergy(series, res):
	resMap = {'minutes':1.0/60.0,'hours':1,'days':24}
	return sum(series)*resMap[res]

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

def getStartDate(analysisName):
	with open('analyses/' + analysisName + '/metadata.json') as mdFile:
		md = json.load(mdFile)
	return md['simStartDate']

def rainbow(dic, key, colorList):
	pos = dic.keys().index(key)
	modPos = pos % len(colorList)
	return colorList[modPos]
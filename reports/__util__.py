#!/usr/bin/env python

import math
import re
import os
from time import mktime
from datetime import datetime
import itertools
import json

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
		try:
			return int(mktime(stampOb.timetuple()))*1000
		except OverflowError:
			return 0
	pointStart = getPointStart(startTimeStamp)
	graphParameters = {
		'chart':{'renderTo':'', 'marginRight':20, 'marginBottom':20, 'zoomType':'x'},
		'title':{'text':None},
		'yAxis':{'title':{'text':None, 'style':{'color':'gray'}}},
		'legend':{'layout':'horizontal', 'align':'top', 'verticalAlign':'top', 'x':50, 'y':-10, 'borderWidth':0},
		'credits':{'enabled':False},
		'xAxis':{'type':'datetime','maxZoom':maxZoom, 'tickColor':'gray','lineColor':'gray'},
		'plotOptions':{'line':{'marker':{'enabled':False}}, 'series':{'shadow':False, 'pointInterval':pointInterval, 'pointStart':pointStart}},
		'tooltip':{'valueDecimals':1},
		'series':[]
	}
	return graphParameters

def totalEnergy(series, res):
	resMap = {'minutes':1.0/60.0,'hours':1,'days':24}
	return sum(series)*resMap[res]

def fileSlurp(fileName):
	with open(fileName,'r') as openFile:
		return openFile.read()

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

#!/usr/bin/env python

import os
import re
import __util__ as util
from copy import copy
import math
import json
from jinja2 import Template

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
with open('./reports/monetizationConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read()

def outputHtml(analysisName):
	# Get all the data from the run:
	pathPrefix = 'analyses/' + analysisName
	studies = os.listdir(pathPrefix + '/studies/')
	# Get the report input:
	with open (pathPrefix + '/reports/monetization.txt') as reportFile:
		reportOptions = eval(reportFile.read())
	distrEnergyRate = float(reportOptions['distrEnergyRate'])
	distrCapacityRate = float(reportOptions['distrCapacityRate'])
	equipAndInstallCost = float(reportOptions['equipAndInstallCost'])
	opAndMaintCost = float(reportOptions['opAndMaintCost'])
	# Find the resolution and interval size (in seconds):
	with open(pathPrefix + '/metadata.txt','r') as mdFile:
		resolution = eval(mdFile.read())['simLengthUnits']
		intervalMap = {'minutes':60, 'hours':3600, 'days':86400}
		interval = intervalMap[resolution]
	# Gather data for all the studies.
	data = util.anaDataTree('./analyses/' + analysisName, lambda x:x.startswith('SwingKids_'))
	fullData = {study:{} for study in data}
	for study in data:
		for swingFile in data[study]:
			rPow = data[study][swingFile]['sum(power_in.real)']
			iPow = data[study][swingFile]['sum(power_in.real)']
			appPow = map(lambda x:util.pyth(x[0],x[1])/1000, zip(rPow,iPow))
			if 	'totAppPower' in data[study]:
				fullData[study]['totAppPower'] = util.vecSum(data[study]['totAppPower'], appPow)
			else:
				fullData[study]['totAppPower'] = appPow
				fullData[study]['time'] = data[study][swingFile]['# property.. timestamp']
		fullData[study]['yearPercentage'] = interval*len(fullData[study]['totAppPower'])/(365*24*60*60.0)
	# Calculate energy from power:
	for study in fullData:
		fullData[study]['totEnergy'] = [x*interval/3600.0 for x in fullData[study]['totAppPower']]
	# Make the study list:
	studyList = [{	'name':study,
					'firstStudy':study==fullData.keys()[0],
					'equipAndInstallCost':(0 if study==fullData.keys()[0] else equipAndInstallCost),
					'opAndMaintCost':(0 if study==fullData.keys()[0] else opAndMaintCost)
				} for study in fullData]
	# Do day-level aggregation if necessary:
	if 'days' == resolution:
		for study in fullData:
			fullData[study]['totAppPower'] = util.aggSeries(fullData[study]['time'], fullData[study]['totAppPower'], max, 'day')
			fullData[study]['totEnergy'] = util.aggSeries(fullData[study]['time'], fullData[study]['totEnergy'], lambda x:sum(x)/len(x), 'day')
	# Monetize stuff, then get per-study totals:
	for study in fullData:
		fullData[study]['monthlyPower'] = util.flat1(util.aggSeries(fullData[study]['time'], fullData[study]['totAppPower'], lambda x:[max(x)/len(x)]*len(x), 'month'))
		fullData[study]['capTotal'] = sum(fullData[study]['monthlyPower'])
		fullData[study]['monthlyEnergy'] = util.flat1(util.aggSeries(fullData[study]['time'], fullData[study]['totEnergy'], lambda x:[sum(x)/len(x)]*len(x), 'month'))
		fullData[study]['energyTotal'] = sum(fullData[study]['monthlyEnergy'])
	capTotals = {study:sum(fullData[study]['monthlyPower']) for study in fullData}
	energyTotals = {study:sum(fullData[study]['monthlyEnergy']) for study in fullData}
	# Start time for all graphs:
	startTime = fullData[fullData.keys()[0]]['time'][0]
	# Money power graph:
	monPowParams = util.defaultGraphObject(resolution, startTime)
	monPowParams['chart']['height'] = 200
	monPowParams['chart']['width'] = 500
	monPowParams['chart']['renderTo'] = 'monetizedPowerTimeSeries'
	monPowParams['chart']['type'] = 'line'
	monPowParams['yAxis']['title']['text'] = 'Capacity Cost ($)'
	colorMap = {0:'salmon',1:'red',2:'darkred',3:'crimson',4:'firebrick',5:'indianred'}
	for study in fullData:
		monPowParams['series'].append({'name':study,'data':[],'color':colorMap[fullData.keys().index(study)%6]})
	# Money energy graph:
	monEnergyParams = util.defaultGraphObject(resolution, startTime)
	monEnergyParams['chart']['height'] = 200
	monEnergyParams['chart']['width'] = 500
	monEnergyParams['chart']['renderTo'] = 'monetizedEnergyBalance'
	monEnergyParams['chart']['type'] = 'line'
	monEnergyParams['yAxis']['title']['text'] = 'Energy Cost ($)'
	colorMap = {0:'goldenrod', 1:'orange', 2:'darkorange', 3:'gold', 4:'chocolate'}
	for study in fullData:
		monEnergyParams['series'].append({'name':study,'data':[],'color':colorMap[fullData.keys().index(study)%5]})
	# Cost growth graph:
	savingsGrowthParams = util.defaultGraphObject(resolution, startTime)
	savingsGrowthParams['chart']['height'] = 200
	savingsGrowthParams['chart']['width'] = 1000
	savingsGrowthParams['chart']['renderTo'] = 'costGrowthContainer'
	savingsGrowthParams['chart']['type'] = 'line'
	savingsGrowthParams['yAxis']['title']['text'] = 'Cumulative Savings ($)'
	savingsGrowthParams['xAxis']['title'] = {'text':'Years After Install'}
	savingsGrowthParams['xAxis']['type'] = 'linear'
	savingsGrowthParams['xAxis']['maxZoom'] = 1
	savingsGrowthParams['plotOptions']['series'] = {'shadow':False}	
	savingsGrowthParams['xAxis']['plotLines'] = []
	del savingsGrowthParams['xAxis']['maxZoom']
	colorMapGray = {0:'dimgray',1:'darkgray',2:'gainsboro',3:'silver'}
	for study in fullData:
		savingsGrowthParams['series'].append({'name':study,'data':[],'color':colorMapGray[fullData.keys().index(study)%3]})
		savingsGrowthParams['xAxis']['plotLines'] = [{'color':'silver','width':1,'value':interval*len(fullData[study]['totAppPower'])/(365*24*60*60.0)}]
	# Get the template in.
	with open('./reports/monetizationOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(monPowParams=json.dumps(monPowParams), monEnergyParams=json.dumps(monEnergyParams), savingsGrowthParams=json.dumps(savingsGrowthParams),
							distrEnergyRate=distrEnergyRate, distrCapacityRate=distrCapacityRate, studyList=studyList, fullData=json.dumps(fullData))

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
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
		intervalMap = {'minutes':60,'hours':3600,'days':86400}
		interval = intervalMap[resolution]
	# Gather data for all the studies.
	data = util.anaDataTree('./analyses/' + analysisName, lambda x:x.startswith('SwingKids_'))
	newData = {study:{} for study in data}
	for study in data:
		for swingFile in data[study]:
			rPow = data[study][swingFile]['sum(power_in.real)']
			iPow = data[study][swingFile]['sum(power_in.real)']
			appPow = map(lambda x:util.pyth(x[0],x[1])/1000, zip(rPow,iPow))
			if 	'totAppPower' in data[study]:
				newData[study]['totAppPower'] = util.vecSum(data[study]['totAppPower'], appPow)
			else:
				newData[study]['totAppPower'] = appPow
				newData[study]['time'] = data[study][swingFile]['# property.. timestamp']
	# Calculate energy from power:
	for study in newData:
		newData[study]['totEnergy'] = [x*interval/3600.0 for x in newData[study]['totAppPower']]
	# Make the study list:
	studyList = [{'name':study, 'firstStudy':study==newData.keys()[0], 'equipAndInstallCost':equipAndInstallCost, 'opAndMaintCost':opAndMaintCost} for study in newData]
	# Do day-level aggregation if necessary:
	if 'days' == resolution:
		for study in newData:
			newData[study]['totAppPower'] = util.aggSeries(newData[study]['time'], newData[study]['totAppPower'], max, 'day')
			newData[study]['totEnergy'] = util.aggSeries(newData[study]['time'], newData[study]['totEnergy'], lambda x:sum(x)/len(x), 'day')
	# Monetize stuff, then get per-study totals:
	for study in newData:
		newData[study]['monPower'] = util.aggSeries(newData[study]['time'], newData[study]['totAppPower'], lambda x:max(x)*len(x)*distrCapacityRate, 'month')
		newData[study]['monEnergy'] = util.aggSeries(newData[study]['time'], newData[study]['totEnergy'], lambda x:sum(x)*distrEnergyRate, 'month')
	energyTotals = {study:sum(newData[study]['monPower']) for study in newData}
	capTotals = {study:sum(newData[study]['monEnergy']) for study in newData}
	# Time scale for all graphs:
	startTime = newData[newData.keys()[0]]['time'][0]
	# Power graph:
	powGraphParams = util.defaultGraphObject(resolution, startTime)
	powGraphParams['chart']['renderTo'] = 'monPowerTimeSeries'
	powGraphParams['chart']['type'] = 'line'
	powGraphParams['chart']['height'] = 200
	powGraphParams['yAxis']['title']['text'] = 'Power (kW)'
	colorMap = {0:'salmon',1:'red',2:'darkred',3:'crimson',4:'firebrick',5:'indianred'}
	for study in newData:
		powGraphParams['series'].append({'name':study,'data':newData[study]['totAppPower'],'color':colorMap[newData.keys().index(study)%6]})
	# Money power graph:
	monPowGraphParams = util.defaultGraphObject(resolution, startTime)
	monPowGraphParams['chart']['height'] = 200
	monPowGraphParams['chart']['width'] = 500
	monPowGraphParams['chart']['renderTo'] = 'monetizedPowerTimeSeries'
	monPowGraphParams['chart']['type'] = 'line'
	monPowGraphParams['yAxis']['title']['text'] = 'Capacity Cost ($)'
	for study in newData:
		monPowGraphParams['series'].append({'name':study,'data':newData[study]['monPower'],'color':colorMap[newData.keys().index(study)%6]})
	# Money energy graph:
	monEnergyGraphParams = util.defaultGraphObject(resolution, startTime)
	monEnergyGraphParams['chart']['height'] = 200
	monEnergyGraphParams['chart']['width'] = 500
	monEnergyGraphParams['chart']['renderTo'] = 'monetizedEnergyBalance'
	monEnergyGraphParams['chart']['type'] = 'line'
	monEnergyGraphParams['yAxis']['title']['text'] = 'Energy Cost ($)'
	colorMap = {0:'goldenrod', 1:'orange', 2:'darkorange', 3:'gold', 4:'chocolate'}
	for study in newData:
		monEnergyGraphParams['series'].append({'name':study,'data':newData[study]['monPower'],'color':colorMap[newData.keys().index(study)%5]})
	# Get the template in.
	with open('./reports/monetizationOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(powGraphParams=json.dumps(powGraphParams), monPowGraphParams=json.dumps(monPowGraphParams), 
							monEnergyGraphParams=json.dumps(monEnergyGraphParams), distrEnergyRate=distrEnergyRate,
							distrCapacityRate=distrCapacityRate, studyList=studyList,
							energyTotals=json.dumps(energyTotals), capTotals=json.dumps(capTotals))

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
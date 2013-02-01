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
	interval = 0
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
	studyList = []
	powerTimeSeries = []
	energyTimeSeries = []
	for study in studies:
		firstStudyQ = studies.index(study)==0
		studyList.append({	'name':str(study), 
							'firstStudy':firstStudyQ,
							'equipAndInstallCost':(0 if firstStudyQ else equipAndInstallCost),
							'opAndMaintCost':(0 if firstStudyQ else opAndMaintCost)	})
		powerToAdd = []
		swingFileNames = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('SwingKids_') and x.endswith('.csv')]
		for swingFile in swingFileNames:
			fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + swingFile)
			fullArray[0] = ['', str(study)]
			fullArray[1:] = [[row[0],(-1 if row[1]<0 else 1)*math.sqrt(row[1]**2+row[2]**2)/1000] for row in fullArray[1:]]
			if [] == powerToAdd:
				powerToAdd = fullArray
			else:
				for rowNum in xrange(len(fullArray)):
					powerToAdd[rowNum][1] = powerToAdd[rowNum][1] + fullArray[rowNum][1]
		if [] == powerTimeSeries:
			powerTimeSeries = powerToAdd
		else:
			powerTimeSeries = [powerTimeSeries[rowNum] + [powerToAdd[rowNum][1]] for rowNum in xrange(len(powerTimeSeries))]
	# Get the energy data from the power data:
	energyTimeSeries = copy(powerTimeSeries)
	energyTimeSeries[1:] = [[row[0]] + map(lambda x:x*interval/3600.0, row[1:]) for row in energyTimeSeries[1:]]	
	# Do day-level aggregation if necessary:
	if 'days' == resolution:
		# TODO: must do more than just maxes!!
		powerTimeSeries = [powerTimeSeries[0]] + util.aggCsv(powerTimeSeries[1:], max, 'day')
		energyTimeSeries  = [energyTimeSeries[0]] + util.aggCsv(energyTimeSeries[1:], lambda x:sum(x)/len(x), 'day')
	# Monetize stuff, then get per-study totals:
	monetizedPower = [powerTimeSeries[0]] + processMonths(powerTimeSeries[1:], lambda x:max(x)/len(x)*distrCapacityRate)
	monetizedEnergy = [energyTimeSeries[0]] + processMonths(energyTimeSeries[1:], lambda x:sum(x)/len(x)*distrEnergyRate)
	energyTotals = {col[0]:sum(col[1:])/distrEnergyRate for col in zip(*monetizedEnergy)[1:]}
	capTotals = {col[0]:sum(col[1:])/distrCapacityRate for col in zip(*monetizedPower)[1:]}
	# Power graph:
	powGraphParams = util.defaultGraphObject(resolution, powerTimeSeries[1][0])
	powGraphParams['chart']['renderTo'] = 'monPowerTimeSeries'
	powGraphParams['chart']['type'] = 'line'
	powGraphParams['chart']['height'] = 200	
	powGraphParams['yAxis']['title']['text'] = 'Power (kW)'
	colorMap = {0:'salmon',1:'red',2:'darkred',3:'crimson',4:'firebrick',5:'indianred'}
	for x in range(1,len(powerTimeSeries[0])):
		powGraphParams['series'].append({'name':powerTimeSeries[0][x],'data':[y[x] for y in powerTimeSeries[1:]],'marker':{'enabled':False},'color':colorMap[x%6]})
	# Money power graph:
	monPowGraphParams = util.defaultGraphObject(resolution, monetizedPower[1][0])
	monPowGraphParams['chart']['height'] = 200
	monPowGraphParams['chart']['width'] = 500
	monPowGraphParams['chart']['renderTo'] = 'monetizedPowerTimeSeries'
	monPowGraphParams['chart']['type'] = 'line'
	monPowGraphParams['yAxis']['title']['text'] = 'Capacity Cost ($)'
	for x in range(1,len(monetizedPower[0])):
		monPowGraphParams['series'].append({'name':monetizedPower[0][x],'data':[y[x] for y in monetizedPower[1:]],'marker':{'enabled':False},'color':colorMap[x%6]})
	# Money energy graph:
	monEnergyGraphParams = util.defaultGraphObject(resolution, monetizedEnergy[1][0])
	monEnergyGraphParams['chart']['height'] = 200
	monEnergyGraphParams['chart']['width'] = 500
	monEnergyGraphParams['chart']['renderTo'] = 'monetizedEnergyBalance'
	monEnergyGraphParams['chart']['type'] = 'line'
	monEnergyGraphParams['yAxis']['title']['text'] = 'Energy Cost ($)'
	colorMap = {0:'goldenrod', 1:'orange', 2:'darkorange', 3:'gold', 4:'chocolate'}
	for x in range(1,len(monetizedEnergy[0])):
		monEnergyGraphParams['series'].append({'name':monetizedEnergy[0][x],'data':[y[x] for y in monetizedEnergy[1:]],'marker':{'enabled':False},'color':colorMap[x%5]})
	# Get the template in.
	with open('./reports/monetizationOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	return template.render(powGraphParams=json.dumps(powGraphParams), monPowGraphParams=json.dumps(monPowGraphParams), 
							monEnergyGraphParams=json.dumps(monEnergyGraphParams), distrEnergyRate=distrEnergyRate,
							distrCapacityRate=distrCapacityRate, studyList=studyList,
							energyTotals=json.dumps(energyTotals), capTotals=json.dumps(capTotals))

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

def processMonths(inList, listFunc):
	# get monthly proc'd months.
	monthList = set([row[0][0:7] for row in inList])
	# for each month, this function calculates the listFunc of each column.
	def funcMon(month):
		listMatr = [row for row in inList if row[0][0:7]==month]
		transposedNoHeaders = [list(colRow) for colRow in zip(*listMatr)[1:]]
		return map(listFunc, transposedNoHeaders)
	# find the processed version for each month
	monthVects = {month:funcMon(month) for month in monthList}
	# return the rewritten matrix.
	return [[row[0]] + monthVects[row[0][0:7]] for row in inList]

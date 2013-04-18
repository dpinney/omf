#!/usr/bin/env python

import os
import re
import __util__ as util
from copy import copy
import math
import json
from jinja2 import Template

with open('./reports/monetizationConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read()

def outputHtml(analysisName):
	# Get all the data from the run:
	pathPrefix = 'analyses/' + analysisName
	studies = os.listdir(pathPrefix + '/studies/')
	resolution = util.getResolution(analysisName)
	startTime = util.getStartDate(analysisName)
	# Get the report input:
	inputData = {}
	with open (pathPrefix + '/reports/monetization.json') as reportFile:
		reportOptions = json.load(reportFile)
		inputData['distrEnergyRate'] = float(reportOptions['distrEnergyRate'])
		inputData['distrCapacityRate'] = float(reportOptions['distrCapacityRate'])
		inputData['equipAndInstallCost'] = float(reportOptions['equipAndInstallCost'])
		inputData['opAndMaintCost'] = float(reportOptions['opAndMaintCost'])
	# Pull in the power data:
	studyDict = {}
	for study in studies:
		studyDict[study] = {}
		with open(pathPrefix + '/studies/' + study + '/cleanOutput.json') as outFile:
			studyJson = json.load(outFile)
			studyDict[study]['Power'] = studyJson['Consumption']['Power']
	# Monetize stuff, then get per-study totals:
	# Money power graph:
	monPowParams = util.defaultGraphObject(resolution, startTime)
	monPowParams['chart']['height'] = 200
	monPowParams['chart']['width'] = 500
	monPowParams['chart']['renderTo'] = 'monetizedPowerTimeSeries'
	monPowParams['chart']['type'] = 'line'
	monPowParams['yAxis']['title']['text'] = 'Capacity Cost ($)'
	for study in studyDict:
		color = util.rainbow(studyDict,study,['salmon','red','darkred','crimson','firebrick','indianred'])
		monPowParams['series'].append({'name':study,'data':[],'color':color})
	# Money energy graph:
	monEnergyParams = util.defaultGraphObject(resolution, startTime)
	monEnergyParams['chart']['height'] = 200
	monEnergyParams['chart']['width'] = 500
	monEnergyParams['chart']['renderTo'] = 'monetizedEnergyBalance'
	monEnergyParams['chart']['type'] = 'line'
	monEnergyParams['yAxis']['title']['text'] = 'Energy Cost ($)'
	for study in studyDict:
		color = util.rainbow(studyDict,study,['goldenrod','orange','darkorange','gold','chocolate'])
		monEnergyParams['series'].append({'name':study,'data':[],'color':color})
	# Cost growth graph:
	savingsGrowthParams = util.defaultGraphObject(resolution, startTime)
	savingsGrowthParams['chart']['height'] = 200
	savingsGrowthParams['chart']['width'] = 1000
	savingsGrowthParams['chart']['renderTo'] = 'costGrowthContainer'
	savingsGrowthParams['chart']['type'] = 'line'
	savingsGrowthParams['yAxis']['title']['text'] = 'Cumulative Savings ($)'
	savingsGrowthParams['xAxis']['title'] = {'text':'Years After Install'}
	savingsGrowthParams['xAxis']['type'] = 'linear'
	savingsGrowthParams['xAxis']['plotLines'] = []
	del savingsGrowthParams['xAxis']['maxZoom']
	for study in studyDict:
		color = util.rainbow(studyDict,study,['dimgray','darkgray','gainsboro','silver'])
		savingsGrowthParams['series'].append({'name':study,'data':[],'color':color})
		# savingsGrowthParams['xAxis']['plotLines'] = [{'color':'silver','width':1,'value':interval*len(studyDict[study]['totAppPower'])/(365*24*60*60.0)}]
	# Get the template in.
	with open('./reports/monetizationOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(monPowParams=json.dumps(monPowParams), monEnergyParams=json.dumps(monEnergyParams), savingsGrowthParams=json.dumps(savingsGrowthParams),
							inputData=json.dumps(inputData), studyDict=json.dumps(studyDict))

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
#!/usr/bin/env python

import os
import __util__ as util
import math
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','regulatorPowerflow')

def outputHtml(analysisName):
	# Put the title in:
	pathPrefix = './analyses/' + analysisName + '/studies/'
	resolution = util.getResolution(analysisName)
	studyList = []
	for study in os.listdir(pathPrefix + '/studies/'):
		regFileNames = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('Regulator_') and x.endswith('.csv')]
		with open(pathPrefix + study + '/cleanOutput.json','r') as outFile:
			cleanOut = json.load(outFile)
		if 'Regulators' in cleanOut:
			newStudy = {'studyName':study}
			# Do apparent power chart:
			appPowerParams = util.defaultGraphObject(resolution, apparentPower[1][0])
			appPowerParams['chart']['height'] = 150
			appPowerParams['yAxis']['title']['text'] = 'App. Power (kW)'			
			appPowerParams['chart']['renderTo'] = 'regApparentChart' + study + regulator
			colorMap = {0:'crimson',1:'red',2:'firebrick'}
			for x in range(1,len(apparentPower[0])):
				appPowerParams['series'].append({'name':apparentPower[0][x],'data':util.roundSeries([y[x] for y in apparentPower[1:]]),'marker':{'enabled':False},'color':colorMap[x%3]})
			# Do power factor chart:
			powerFactorParams = util.defaultGraphObject(resolution, powerFactor[1][0])
			powerFactorParams['chart']['height'] = 150
			powerFactorParams['chart']['renderTo'] = 'regPowFactChart' + study + regulator
			powerFactorParams['yAxis']['title']['text'] = 'Power Factor (%)'
			powerFactorParams['series'] = [{'name':powerFactor[0][1],'data':util.roundSeries([y[1] for y in powerFactor[1:]]),'marker':{'enabled':False},'color':'red'}]
			# Do regulator tap position chart:
			tapPosParams = util.defaultGraphObject(resolution, tapPositions[1][0])
			tapPosParams['chart']['height'] = 150
			tapPosParams['chart']['renderTo'] = 'regTapsChart' + study + regulator
			tapPosParams['yAxis']['title']['text'] = 'Tap Multiplier'
			colorMapGray = {0:'gainsboro',1:'silver',2:'gray'}
			for x in range(1,len(tapPositions[0])):
				tapPosParams['series'].append({'name':tapPositions[0][x],'data':util.roundSeries([y[x] for y in tapPositions[1:]]),'marker':{'enabled':False},'color':colorMapGray[x%3]})
	# Get the template in.
	with open('./reports/climateOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(studyList=studyList)

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
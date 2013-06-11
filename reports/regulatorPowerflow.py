#!/usr/bin/env python

import os
import __util__ as util
import math
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','regulatorPowerflow')

def outputHtml(analysisObject, studyList):
	# Put the title in:
	resolution = analysisObject.simLengthUnits
	startDate = analysisObject.simStartDate
	outputList = []
	for study in studyList:
		regFileNames = [x for x in os.listdir(pathPrefix + study) if x.startswith('Regulator_') and x.endswith('.csv')]
		cleanOut = study.outputJson
		if 'Regulators' in cleanOut:
			newStudy = {'studyName':study, 'regs':[]}
			for reg in cleanOut['Regulators']:		
				newReg = {'regName':reg}
				# Do apparent power chart:
				appPowerParams = util.defaultGraphObject(resolution, startDate)
				appPowerParams['chart']['height'] = 150
				appPowerParams['yAxis']['title']['text'] = 'App. Power (kW)'			
				appPowerParams['chart']['renderTo'] = 'regApparentChart' + study + reg
				appPowerParams['series'] = [{	'name':tap.replace(' App Power',''),
														'data':cleanOut['Regulators'][reg][tap],
														'color':util.rainbow(cleanOut['Regulators'][reg],tap,['crimson','red','firebrick'])}
													for tap in cleanOut['Regulators'][reg] if tap.endswith('App Power')]
				newReg['appPowerParams'] = json.dumps(appPowerParams)
				# Do power factor chart:
				powerFactorParams = util.defaultGraphObject(resolution, startDate)
				powerFactorParams['chart']['height'] = 150
				powerFactorParams['chart']['renderTo'] = 'regPowFactChart' + study + reg
				powerFactorParams['yAxis']['title']['text'] = 'Power Factor (%)'
				powerFactorParams['series'] = [{	'name':'Total',
															'data':cleanOut['Regulators'][reg]['Power Factor'],
															'color':'red'}]
				newReg['powerFactorParams'] = json.dumps(powerFactorParams)
				# Do regulator tap position chart:
				tapPosParams = util.defaultGraphObject(resolution, startDate)
				tapPosParams['chart']['height'] = 150
				tapPosParams['chart']['renderTo'] = 'regTapsChart' + study + reg
				tapPosParams['yAxis']['title']['text'] = 'Tap Multiplier'
				tapPosParams['series'] = [{	'name':tap.replace(' Position',''),
														'data':cleanOut['Regulators'][reg][tap],
														'color':util.rainbow(cleanOut['Regulators'][reg],tap,['gainsboro','silver','gray'])}
													for tap in cleanOut['Regulators'][reg] if tap.endswith('Position')]
				newReg['tapPosParams'] = json.dumps(tapPosParams)
				newStudy['regs'].append(newReg)
			outputList.append(newStudy)
	# Get the template in.
	with open('./reports/regulatorPowerflowOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(outputList=outputList)
#!/usr/bin/env python

import os
import __util__ as util
import math
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','meterPowerflow')

def outputHtml(analysisObject, reportConfig):
	# Build up the data:
	resolution = analysisObject.simLengthUnits
	startDate = analysisObject.simStartDate
	studyList = []
	for study in analysisObject.studies:
		cleanOut = study.outputJson
		if 'Meters' in cleanOut:
			newStudy = {'studyName':study.name}
			# Power graph:
			newStudy['powerParameters'] = util.defaultGraphObject(resolution, startDate)	
			newStudy['powerParameters']['chart']['height'] = 150
			newStudy['powerParameters']['chart']['renderTo'] = 'meterPowerChart' + study.name
			newStudy['powerParameters']['yAxis']['title']['text'] = 'Load (kW)'
			newStudy['powerParameters']['series'] = [{	'name':meter,
														'data':cleanOut['Meters'][meter]['Load (kW)'],
														'color':util.rainbow(cleanOut['Meters'],meter,['salmon','red','darkred','crimson','firebrick','indianred'])}
													for meter in cleanOut['Meters']]
			newStudy['powerParameters'] = json.dumps(newStudy['powerParameters'])
			# Voltage graph:
			newStudy['voltParameters'] = util.defaultGraphObject(resolution, startDate)	
			newStudy['voltParameters']['chart']['height'] = 150
			newStudy['voltParameters']['chart']['renderTo'] = 'meterVoltChart' + study.name
			newStudy['voltParameters']['yAxis']['title']['text'] = 'Voltage (V)'
			newStudy['voltParameters']['series'] = [{	'name':meter,
														'data':cleanOut['Meters'][meter]['Voltage (V)'],
														'color':util.rainbow(cleanOut['Meters'],meter,['lightblue','blue','darkblue','cornflowerblue','cyan'])}
													for meter in cleanOut['Meters']]
			newStudy['voltParameters'] = json.dumps(newStudy['voltParameters'])
			studyList.append(newStudy)
	# Get the template in.
	with open('./reports/meterPowerflowOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(studyList=studyList)
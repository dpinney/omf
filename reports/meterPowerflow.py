#!/usr/bin/env python

import os
import __util__ as util
import math
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','meterPowerflow')

def outputHtml(analysisName):
	# Build up the data:
	pathPrefix = './analyses/' + analysisName + '/studies/'
	resolution = util.getResolution(analysisName)
	startDate = util.getStartDate(analysisName)
	studyList = []
	for study in os.listdir(pathPrefix):
		with open(pathPrefix + study + '/cleanOutput.json') as outFile:
			cleanOut = json.load(outFile)
		if 'Meters' in cleanOut:
			newStudy = {'studyName':study}
			# Power graph:
			newStudy['powerParameters'] = util.defaultGraphObject(resolution, startDate)	
			newStudy['powerParameters']['chart']['height'] = 150
			newStudy['powerParameters']['chart']['renderTo'] = 'meterPowerChart' + study
			newStudy['powerParameters']['yAxis']['title']['text'] = 'Load (kW)'
			newStudy['powerParameters']['series'] = [{	'name':meter,
														'data':cleanOut['Meters'][meter]['Load (kW)'],
														'color':util.rainbow(cleanOut['Meters'],meter,['salmon','red','darkred','crimson','firebrick','indianred'])}
													for meter in cleanOut['Meters']]
			newStudy['powerParameters'] = json.dumps(newStudy['powerParameters'])
			# Voltage graph:
			newStudy['voltParameters'] = util.defaultGraphObject(resolution, startDate)	
			newStudy['voltParameters']['chart']['height'] = 150
			newStudy['voltParameters']['chart']['renderTo'] = 'meterVoltChart' + study
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


def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
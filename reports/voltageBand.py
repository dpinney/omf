#!/usr/bin/env python

import os
import __util__ as util
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','voltageBand')

def outputHtml(analysisObject, studyList):
	# Build up the data:
	outputList = []
	for study in studyList:
		cleanOut = study.outputJson
		# Set up the graph.
		if 'allMeterVoltages' in cleanOut:
			newStudy = {'studyName':study.name}
			graphParameters = util.defaultGraphObject(analysisObject.simLengthUnits, analysisObject.simStartDate)
			graphParameters['chart']['type'] = 'line'
			graphParameters['chart']['renderTo'] = 'voltChartDiv' + study.name
			graphParameters['series'].append({'name':'Min','data':cleanOut['allMeterVoltages']['Min'],'marker':{'enabled':False},'color':'gray'})
			graphParameters['series'].append({'name':'Mean','data':cleanOut['allMeterVoltages']['Mean'],'marker':{'enabled':False},'color':'blue'})
			graphParameters['series'].append({'name':'Max','data':cleanOut['allMeterVoltages']['Max'],'marker':{'enabled':False},'color':'gray'})
			newStudy['graphParams'] = json.dumps(graphParameters)
			outputList.append(newStudy)
	# Get the template in.
	with open('./reports/voltageBandOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(outputList=outputList)
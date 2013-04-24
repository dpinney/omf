#!/usr/bin/env python

import os
import __util__ as util
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','voltageBand')

def outputHtml(analysisName):
	# Build up the data:
	pathPrefix = './analyses/' + analysisName
	resolution = util.getResolution(analysisName)
	studyList = []
	for study in os.listdir(pathPrefix + '/studies/'):
		with open(pathPrefix + '/studies/' + study + '/cleanOutput.json','r') as outFile:
			cleanOut = json.load(outFile)
		# Set up the graph.
		if 'allMeterVoltages' in cleanOut:
			newStudy = {'studyName':study}
			graphParameters = util.defaultGraphObject(resolution, util.getStartDate(analysisName))
			graphParameters['chart']['type'] = 'line'
			graphParameters['chart']['renderTo'] = 'voltChartDiv' + study
			graphParameters['series'].append({'name':'Min','data':cleanOut['allMeterVoltages']['Min'],'marker':{'enabled':False},'color':'gray'})
			graphParameters['series'].append({'name':'Mean','data':cleanOut['allMeterVoltages']['Mean'],'marker':{'enabled':False},'color':'blue'})
			graphParameters['series'].append({'name':'Max','data':cleanOut['allMeterVoltages']['Max'],'marker':{'enabled':False},'color':'gray'})
			newStudy['graphParams'] = json.dumps(graphParameters)
			studyList.append(newStudy)
	# Get the template in.
	with open('./reports/voltageBandOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(studyList=studyList)

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

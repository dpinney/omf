#!/usr/bin/env python

import os
import __util__ as util
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','climate')


'''
source info:
http://www.gridlabd.org/documents/doxygen/latest_dev/climate_8h-source.html
'''

def outputHtml(analysisObject, reportConfig):
	# Collect study variables:
	resolution = analysisObject.simLengthUnits
	climates = analysisObject.climate.count('.tmy2')
	studyList = []
	title = True
	for study in analysisObject.studies:
		cleanOut = study.outputJson
		if 'climate' in cleanOut:
			studyDict = {'studyName':study}
			# Setting up the graph options:
			graphParameters = util.defaultGraphObject(resolution, cleanOut['timeStamps'][0] if cleanOut['timeStamps'] else "0001-01-01")
			graphParameters['chart']['renderTo'] = 'climateChartDiv' + str(study)
			graphParameters['chart']['type'] = 'line'
			graphParameters['yAxis'] = {'title':{'text':'Climate Units', 'style':{'color':'gray'}}}
			for varName in cleanOut['climate']:
				colorChoice = util.rainbow(cleanOut['climate'], varName, ['dimgray','darkgray','darkgray','gainsboro','gainsboro'])
				graphParameters['series'].append({'name':varName,'data':cleanOut['climate'][varName],'marker':{'enabled':False},'color':colorChoice})
			studyDict['graphParameters'] = json.dumps(graphParameters)
			studyList.append(studyDict)
	# Get the template in.
	with open('./reports/climateOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# If we've only got one real climate, hide the dups.
	if climates < 2:
		studyList = [studyList[0]] if studyList else ''
		title = False
	# Write the results.
	return template.render(studyList=studyList, title=title)

if __name__ == '__main__':
	# tests go here.
	os.chdir('..')
	outputHtml('SolarTrio')
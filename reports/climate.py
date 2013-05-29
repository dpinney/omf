#!/usr/bin/env python

import os
import __util__ as util
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','climate')

def outputHtml(analysisName):
	# Collect study variables:
	pathPrefix = './analyses/' + analysisName + '/studies/'
	studies = os.listdir(pathPrefix)
	with open('./analyses/' + analysisName + '/metadata.json') as mdFile:
		md = json.load(mdFile)
		resolution = md['simLengthUnits']
		climates = md['climate'].count('.tmy2')
	studyList = []
	title = True
	for study in studies:
		with open(pathPrefix + study + '/cleanOutput.json') as outFile:
			cleanOut = json.load(outFile)
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


def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

def main():
	# tests go here.
	os.chdir('..')
	outputHtml('SolarTrio')

if __name__ == '__main__':
	main()


'''

source info:
http://www.gridlabd.org/documents/doxygen/latest_dev/climate_8h-source.html

'''

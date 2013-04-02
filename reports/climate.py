#!/usr/bin/env python

import os
import __util__ as util
import json

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','climate')

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Climate</p>\n'
	outputBuffer += '<div id="climateReport" class="tightContent" style="position:relative">\n'
	# Collect study variables:
	pathPrefix = './analyses/' + analysisName
	resolution = json.loads(util.fileSlurp(pathPrefix + '/metadata.json'))['simLengthUnits']
	studies = os.listdir(pathPrefix + '/studies/')
	metadatas = map(lambda x:util.fileSlurp(pathPrefix + '/studies/' + x + '/metadata.json'), studies)
	climates = set(map(lambda x:json.loads(x)['climate'], metadatas))
	# If we have more than one study, just show one climate:
	if 1 == len(climates):
		studies = [studies[0]]
		title = False
	else:
		title = True
	# Turn each study into graphics:
	for study in studies:
		climateFiles = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('Climate_')]
		fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + climateFiles[0])
		fullArray[0] = ['Timestamp','Temperature (dF)','D.Insolation (W/m^2)', 'Wind Speed', 'Rainfall (in/h)', 'Snow Depth (in)']
		if 'days' == resolution:
			# Aggregate to the day level, maxing climate but averaging insolation, summing rain:
			funs = {0:max, 1:lambda x:sum(x)/len(x), 2:max, 3:sum, 4:max}
			fullArray = [fullArray[0]] + util.aggCsv(fullArray[1:], funs, 'day')
			fullArray[0] = ['Timestamp','Max Temp (dF)','Avg Insol (W/m^2)', 'Max Wind Speed', 'Rainfall (in/h)', 'Max Snow Depth (in)']
		# Setting up the graph options:
		graphParameters = util.defaultGraphObject(resolution, fullArray[1][0])
		graphParameters['chart']['renderTo'] = 'climateChartDiv' + str(study)
		graphParameters['chart']['type'] = 'line'
		graphParameters['yAxis'] = {'title':{'text':'Climate Units', 'style':{'color':'gray'}}}
		colorMap = {1:'dimgray',2:'darkgray',3:'darkgray',4:'gainsboro',5:'gainsboro'}
		for x in [1,2,3,4,5]:
			graphParameters['series'].append({'name':fullArray[0][x],'data':util.roundSeries([float(y[x]) for y in fullArray[1:]]),'marker':{'enabled':False},'color':colorMap[x]})
		# Write one study's worth of HTML:
		outputBuffer += '<div id="climateStudy' + study + '" class="studyContainer">\n'
		outputBuffer += '<div id="climateChartDiv' + study + '" style="height:250px"></div>\n'
		if True == title:
			outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>\n'
		outputBuffer += '<script>new Highcharts.Chart(' + json.dumps(graphParameters) + ')</script>\n'
		outputBuffer += '</div>\n'
	return outputBuffer + '</div>\n\n'

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
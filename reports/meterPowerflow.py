#!/usr/bin/env python

import os
import __util__ as util
import math
import json

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = '''<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a>
						<table class='reportOptions'>
							<tr>
								<td>Report Name</td>
								<td class='reportName'>meterPowerflow</td>
							</tr>
						</table>'''

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Meter Powerflow</p><div id="meterPowerflowReport" class="tightContent" style="position:relative">'
	# Build up the data:
	pathPrefix = './analyses/' + analysisName
	resolution = json.loads(util.fileSlurp(pathPrefix + '/metadata.json'))['simLengthUnits']
	studies = os.listdir(pathPrefix + '/studies/')
	for study in studies:
		voltMatrix = []
		powerMatrix = []
		# Add the data from each recorder in this study:
		for fileName in os.listdir(pathPrefix + '/studies/' + study):
			if fileName.startswith('meterRecorder') and fileName.endswith('.csv'):
				fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + fileName)
				# If we haven't added a time series yet, put the datestamp stuff on there:
				if voltMatrix == [] and powerMatrix == []:
					voltMatrix = [[row[0]] for row in fullArray]
					powerMatrix = [[row[0]] for row in fullArray]
				# Now add a timeseries for each study:
				voltMatrix[0] += [str(fileName.replace('.csv','').replace('meterRecorder_',''))]
				voltMatrix[1:] = [voltMatrix[rowNum+1] + [math.sqrt(fullArray[rowNum+1][2]**2 + fullArray[rowNum+1][3]**2)/2] for rowNum in xrange(len(fullArray)-1)]
				powerMatrix[0] += [str(fileName.replace('.csv','').replace('meterRecorder_',''))]
				powerMatrix[1:] = [powerMatrix[rowNum+1] + [fullArray[rowNum+1][1]/1000] for rowNum in xrange(len(fullArray)-1)]
		# Do day-level aggregation:
		if 'days' == resolution:
			# TODO: must do more than just maxes!!
			voltMatrix = [voltMatrix[0]] + util.aggCsv(voltMatrix[1:], max, 'day')
			powerMatrix  = [powerMatrix[0]] + util.aggCsv(powerMatrix[1:], max, 'day')
		# Study container and title:
		outputBuffer += '<div id="meterPowerflow' + study + '" class="studyContainer">'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		# Power graph:
		graphParameters = util.defaultGraphObject(resolution, powerMatrix[1][0])	
		graphParameters['chart']['height'] = 150
		graphParameters['chart']['renderTo'] = 'meterPowerChart' + study
		graphParameters['yAxis']['title']['text'] = 'Load (kW)'
		colorMap = {0:'salmon',1:'red',2:'darkred',3:'crimson',4:'firebrick',5:'indianred'}
		for x in range(1,len(powerMatrix[0])):
			graphParameters['series'].append({'name':powerMatrix[0][x],'data':util.roundSeries([y[x] for y in powerMatrix[1:]]),'marker':{'enabled':False},'color':colorMap[x%6]})
		outputBuffer += '<div id="meterPowerChart' + study + '"><script>new Highcharts.Chart(' + json.dumps(graphParameters) + ')</script></div>'
		# Voltage graph:
		graphParameters['chart']['renderTo'] = 'meterVoltChart' + study
		graphParameters['yAxis']['title']['text'] = 'Voltage (V)'
		colorMap2 = {0:'lightblue',1:'blue',2:'darkblue',3:'cornflowerblue',4:'cyan'}
		graphParameters['series'] = []
		for x in range(1,len(voltMatrix[0])):
			graphParameters['series'].append({'name':voltMatrix[0][x],'data':util.roundSeries([y[x] for y in voltMatrix[1:]]),'marker':{'enabled':False},'color':colorMap2[x%5]})
		outputBuffer += '<div id="meterVoltChart' + study + '"><script>new Highcharts.Chart(' + json.dumps(graphParameters) + ')</script></div>'
		outputBuffer += '</div>'
	return outputBuffer + '</div>\n\n'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
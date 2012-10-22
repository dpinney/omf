#!/usr/bin/env python

import os
import __util__
import math

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = '''<div id='REMOVALID' class='content'>
							<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a>
							<table class='reportOptions'>
								<tr>
									<td>Report Name</td>
									<td class='reportName'>meterPowerflow</td>
								</tr>
							</table>
						</div> '''

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Meter Powerflow</p><div id="meterPowerflowReport" class="tightContent" style="position:relative">'
	# Build up the data:
	dataTree = {}
	pathPrefix = './analyses/' + analysisName
	for study in os.listdir(pathPrefix + '/studies/'):
		voltMatrix = []
		powerMatrix = []
		# Add the data from each recorder in this study:
		for fileName in os.listdir(pathPrefix + '/studies/' + study):
			if fileName.startswith('meterRecorder') and fileName.endswith('.csv'):
				fullArray = __util__.csvToArray(pathPrefix + '/studies/' + study + '/' + fileName)
				# If we haven't added a time series yet, put the datestamp stuff on there:
				if voltMatrix == [] and powerMatrix == []:
					voltMatrix = [[row[0]] for row in fullArray]
					powerMatrix = [[row[0]] for row in fullArray]
				# Now add a timeseries for each blahblahblah
				voltMatrix[0] += [str(fileName.replace('.csv','').replace('meterRecorder_',''))]
				voltMatrix[1:] = [voltMatrix[rowNum+1] + [math.sqrt(fullArray[rowNum+1][2]**2 + fullArray[rowNum+1][3]**2)/2] for rowNum in xrange(len(fullArray)-1)]
				powerMatrix[0] += [str(fileName.replace('.csv','').replace('meterRecorder_',''))]
				powerMatrix[1:] = [powerMatrix[rowNum+1] + [fullArray[rowNum+1][1]/1000] for rowNum in xrange(len(fullArray)-1)]
		# Write one study's worth of HTML:
		outputBuffer += '<div id="meterPowerflow' + study + '" class="studyContainer">'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		outputBuffer += '<div id="meterPowerChart' + study + '" style="height:150px"></div>'
		powerGraphOptions = "{vAxis:{title:'Load (kW)'}, chartArea:{left:60,top:20,height:'70%',width:'90%'}, hAxis:{textPosition:'none', title:'Time'}, colors:['red','darkred','salmon'], legend:{position:'top'}}"
		outputBuffer += "<script>drawLineChart(" + str(powerMatrix) + ",'" + 'meterPowerChart' + str(study) + "'," + powerGraphOptions + ")</script>"
		#TODO: throw some voltage on there. 
		outputBuffer += '<div id="meterVoltChart' + study + '" style="height:150px"></div>'
		voltGraphOptions = "{vAxis:{title:'Voltage (V)'}, chartArea:{left:60,top:20,height:'70%',width:'90%'}, hAxis:{textPosition:'none', title:'Time'}, colors:['lightblue','blue','darkblue'], legend:{position:'top'}}"
		outputBuffer += "<script>drawLineChart(" + str(voltMatrix) + ",'" + 'meterVoltChart' + str(study) + "'," + voltGraphOptions + ")</script>"
		outputBuffer += '</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
#!/usr/bin/env python

import os
import __util__
from pprint import pprint

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = '''<div id='REMOVALID' class='content'>
							<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a>
							<table class='reportOptions'>
								<tr>
									<td>Report Name</td>
									<td class='reportName'>climate</td>
								</tr>
							</table>
						</div> '''

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Climate</p><div id="climateReport" class="tightContent" style="position:relative">'
	pathPrefix = './analyses/' + analysisName
	for study in os.listdir(pathPrefix + '/studies/'):
		climateFiles = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('Climate_')]
		fullArray = __util__.csvToArray(pathPrefix + '/studies/' + study + '/' + climateFiles[0])
		# Write one study's worth of HTML:
		outputBuffer += '<div id="climateStudy' + study + '" class="studyContainer">'
		outputBuffer += '<div id="climateChartDiv' + study + '" style="height:250px"></div>'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		graphOptions = "{chartArea:{left:60,top:20,height:'80%'}, hAxis:{textPosition:'none', title:'Time'}, colors:['dimgray','darkgray','darkgray','gainsboro','gainsboro']}"
		outputBuffer += "<script>drawLineChart(" + str(fullArray) + ",'" + 'climateChartDiv' + str(study) + "'," + graphOptions + ")</script>"
		outputBuffer += '</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.


'''

source info:
http://www.gridlabd.org/documents/doxygen/latest_dev/climate_8h-source.html



'''
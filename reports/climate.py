#!/usr/bin/env python

import os
import __util__ as util
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
	# Collect study variables:
	pathPrefix = './analyses/' + analysisName
	with open(pathPrefix + '/metadata.txt','r') as mdFile:
		resolution = eval(mdFile.read())['simLengthUnits']
	studies = os.listdir(pathPrefix + '/studies/')
	# If we have more than one study, just show one climate:
	def fileSlurp(fileName):
		with open(fileName,'r') as openFile:
			return openFile.read()
	metadatas = map(lambda x:fileSlurp(pathPrefix + '/studies/' + x + '/metadata.txt'), studies)
	climates = set(map(lambda x:eval(x)['climate'], metadatas))
	title = True
	if 1 == len(climates):
		studies = [studies[0]]
		title = False
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
		# Write one study's worth of HTML:
		outputBuffer += '<div id="climateStudy' + study + '" class="studyContainer">'
		outputBuffer += '<div id="climateChartDiv' + study + '" style="height:250px"></div>'
		if True == title:
			outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		graphOptions = "{chartArea:{left:60,top:20,height:'80%', width:'93%'}, hAxis:{textPosition:'none', title:'Time'}, colors:['dimgray','darkgray','darkgray','gainsboro','gainsboro'],legend:{position:'top'}}"
		outputBuffer += "<script>drawLineChart(" + str(fullArray) + ",'" + 'climateChartDiv' + str(study) + "'," + graphOptions + ")</script>"
		outputBuffer += '</div>'
	return outputBuffer + '</div>'

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
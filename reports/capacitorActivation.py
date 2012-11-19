#!/usr/bin/env python

import os
import __util__ as util

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<div id='REMOVALID' class='content capacitorActivation'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>capacitorActivation</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer =  '<p class="reportTitle">Capacitor Activation</p>'
	outputBuffer += '<div id="capActReport" class="tightContent">'
	# Build up the data:
	pathPrefix = './analyses/' + analysisName
	with open(pathPrefix + '/metadata.txt','r') as mdFile:
		resolution = eval(mdFile.read())['simLengthUnits']
	for study in os.listdir(pathPrefix + '/studies/'):
		capFileNames = filter(lambda x:x.startswith('Capacitor_') and x.endswith('.csv'), os.listdir(pathPrefix + '/studies/' + study))
		outputBuffer += '<div id="capStudy' + study + '" class="studyContainer">'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		for capacitor in capFileNames:
			cap = capacitor.replace('.csv','')
			fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + capacitor)
			if 'days' == resolution:
				# Aggregate to the day level, averaging to percentage charging:
				fullArray = [fullArray[0]] + util.aggCsv(fullArray[1:], lambda x:sum(x)/len(x), 'day')
			outputBuffer += '<div id="chartDiv' + study + cap + '" class="capChart" style="height:90px"></div>'
			chartOptions = '{chartArea:{left:60,top:15,height:60}, hAxis:{title:"Time",textPosition:"none"}, vAxis:{title:"On/Off", gridlines:{count:2}}, colors:["gainsboro","silver","gray"]}'
			outputBuffer += '<script>drawAreaChart(' + str(fullArray) + ',' + '"chartDiv' + study + cap + '",' + chartOptions + ')</script>'
		outputBuffer += '</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
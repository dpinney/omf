#!/usr/bin/env python

import os
import __util__

configHtmlTemplate = "<div id='REMOVALID' class='content REPORTNAME'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>✖</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>REPORTNAME</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer =  '<p class="reportTitle">Capacitor Activation</p>'
	outputBuffer += '<div id="capActReport" class="tightContent">'
	# Build up the data:
	dataTree = {}
	pathPrefix = './analyses/' + analysisName
	for study in os.listdir(pathPrefix + '/studies/'):
		dataTree[study] = {}
		capFileNames = filter(lambda x:x.startswith('Capacitor_') and x.endswith('.csv'), os.listdir(pathPrefix + '/studies/' + study))
		outputBuffer += '<div id="capStudy' + study + '" class="studyContainer">'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		for capacitor in capFileNames:
			cap = capacitor.replace('.csv','')
			dataTree[study][cap] = __util__.csvToArray(pathPrefix + '/studies/' + study + '/' + capacitor)
			outputBuffer += '<div id="chartDiv' + study + cap + '" class="capChart"></div>'
			outputBuffer += '<script>drawAreaChart(' + str(dataTree[study][cap]) + ',' + '"chartDiv' + study + cap + '",' + '["gainsboro","silver","gray"])</script>'
		outputBuffer += '</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
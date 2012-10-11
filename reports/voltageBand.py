#!/usr/bin/env python

import os
import __util__

configHtmlTemplate = "<div id='REMOVALID' class='content voltageBand'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>✖</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>voltageBand</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Triplex Meter Voltages</p><div id="voltageBandReport" class="tightContent" style="position:relative">'
	# Build up the data:
	dataTree = {}
	pathPrefix = './analyses/' + analysisName
	for study in os.listdir(pathPrefix + '/studies/'):
		dataTree[study] = {}
		for fileName in os.listdir(pathPrefix + '/studies/' + study):
			if 'VoltageJiggle.csv' == fileName:
				fullArray = __util__.csvToArray(pathPrefix + '/studies/' + study + '/' + fileName)
				dataTree[study] = [[row[0],row[1]/2,row[2]/2,row[3]/2] for row in fullArray[1:]]
				dataTree[study].insert(0,[fullArray[0][0],fullArray[0][1],fullArray[0][2],fullArray[0][3]])
		# Write one study's worth of HTML:
		outputBuffer += '<div id="voltStudy' + study + '" class="studyContainer">'
		outputBuffer += '<div id="voltChartDiv' + study + '" class="voltChart"></div>'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		graphOptions = "{vAxis:{title:'Volts'}, chartArea:{left:60,top:20,height:'70%'}, hAxis:{textPosition:'none', title:'Time'}, colors:['gray','blue','gray']}"
		outputBuffer += "<script>drawLineChart(" + str(dataTree[study]) + ",'" + 'voltChartDiv' + str(study) + "'," + graphOptions + ")</script>"
		outputBuffer += '</div>'
	return outputBuffer

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
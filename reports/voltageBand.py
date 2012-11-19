#!/usr/bin/env python

import os
import __util__ as util

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<div id='REMOVALID' class='content voltageBand'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>voltageBand</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Triplex Meter Voltages</p><div id="voltageBandReport" class="tightContent" style="position:relative">'
	# Build up the data:
	pathPrefix = './analyses/' + analysisName
	# Check the resolution:
	with open(pathPrefix + '/metadata.txt','r') as mdFile:
		resolution = eval(mdFile.read())['simLengthUnits']
	for study in os.listdir(pathPrefix + '/studies/'):
		voltMatrix = []
		for fileName in os.listdir(pathPrefix + '/studies/' + study):
			if 'VoltageJiggle.csv' == fileName:
				fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + fileName)
				if 'days' == resolution:
					# Aggregate to the day level:
					# TODO: must make this more mathematically rigorous than average stdDevs!!
					funs = {0:min,1:lambda x:sum(x)/len(x),2:max,3:lambda x:sum(x)/len(x)}
					fullArray = [fullArray[0]] + util.aggCsv(fullArray[1:], funs, 'day')
				voltMatrix = [[row[0],row[1]/2,row[2]/2,row[3]/2] for row in fullArray[1:]]
				# voltMatrix.insert(0,[fullArray[0][0],fullArray[0][1],fullArray[0][2],fullArray[0][3]])
				voltMatrix.insert(0,[fullArray[0][0],'Min','Mean','Max'])
		# Write one study's worth of HTML:
		outputBuffer += '<div id="voltStudy' + study + '" class="studyContainer">'
		outputBuffer += '<div id="voltChartDiv' + study + '" class="voltChart" style="height:150px"></div>'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		graphOptions = "{vAxis:{title:'Volts'}, chartArea:{left:60,top:20,height:'70%', width:'85%'}, hAxis:{textPosition:'none', title:'Time'}, colors:['gray','blue','gray']}"
		outputBuffer += "<script>drawLineChart(" + str(voltMatrix) + ",'" + 'voltChartDiv' + str(study) + "'," + graphOptions + ")</script>"
		outputBuffer += '</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

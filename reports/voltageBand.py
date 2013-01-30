#!/usr/bin/env python

import os
import __util__ as util
import json

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>voltageBand</td></tr></table>"

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
		# Set up the graph.
		graphParameters = {
			'chart':{'renderTo':'', 'type':'line', 'marginRight':20, 'marginBottom':20, 'zoomType':'x'},
			'title':{'text':None},
			'yAxis':{'title':{'text':None},'plotLines':[{'value':0, 'width':1, 'color':'gray'}]},
			'legend':{'layout':'horizontal', 'align':'top', 'verticalAlign':'top', 'x':50, 'y':-10, 'borderWidth':0},
			'credits':{'enabled':False},
			'xAxis':{'categories':[],'labels':{'enabled':False},'maxZoom':20,'tickColor':'gray','lineColor':'gray'},
			'plotOptions':{'line':{'shadow':False}},
			'series':[]
		}
		graphParameters['chart']['renderTo'] = 'voltChartDiv' + str(study)
		graphParameters['xAxis']['categories'] = [x[0] for x in voltMatrix[1:]]
		graphParameters['series'].append({'name':voltMatrix[0][1],'data':[x[1] for x in voltMatrix[1:]],'marker':{'enabled':False},'color':'gray'})
		graphParameters['series'].append({'name':voltMatrix[0][2],'data':[x[2] for x in voltMatrix[1:]],'marker':{'enabled':False},'color':'blue'})
		graphParameters['series'].append({'name':voltMatrix[0][3],'data':[x[3] for x in voltMatrix[1:]],'marker':{'enabled':False},'color':'gray'})
		# Write one study's worth of HTML:
		outputBuffer += '<div id="voltStudy' + study + '" class="studyContainer">'
		outputBuffer += '<div id="voltChartDiv' + study + '" class="voltChart" style="height:150px"></div>'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		outputBuffer += '<script>new Highcharts.Chart(' + json.dumps(graphParameters) + ')</script>\n'
		outputBuffer += '</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

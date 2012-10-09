#!/usr/bin/env python

import os
import treeParser as tp

configHtmlTemplate = "<div id='REMOVALID' class='content gridComparison'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>✖</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>gridComparison</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = "<p class='reportTitle'>Grid Comparison</p><div id='gridComparisonReport' class='tightContent'>"
	# Build up the data:
	dataTree = {}
	pathPrefix = './analyses/' + analysisName + '/studies/'
	for study in os.listdir('./analyses/' + analysisName + '/studies/'):
		glmTree = tp.parse(pathPrefix + study + '/main.glm')
		names = [glmTree[x]['name'] for x in glmTree if 'name' in glmTree[x]]
		dataTree[str(study)] = set(names)
	# Partition the names into common names and those unique to each feeder:
	commonNames = reduce(lambda x,y:x.intersection(y), dataTree.values())
	uniqueNames = {study:dataTree[study].difference(commonNames) for study in dataTree}
	uniqueNameCounts = {study:len(uniqueNames[study]) for study in uniqueNames}
	uniqueNameCounts['Common to All'] = len(commonNames)
	# Put the data into a chart-friendly format, and chart it:
	pieChartData = [['Study','Components']] + [[study, uniqueNameCounts[study]] for study in uniqueNameCounts]
	graphOptions = '{title:"Unique Grid Components", colors:["gainsboro","silver","gray"]}'
	outputBuffer += "<div id='comparisonPieChart'><script>drawPieChart(" + str(pieChartData) + ",'comparisonPieChart'," + graphOptions + ")</script></div>"
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
#!/usr/bin/env python

import os
import __util__
import treeParser as tp

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<div id='REMOVALID' class='content studyDetails'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>studyDetails</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer =  '<p class="reportTitle">Study Details</p>'
	outputBuffer += '<div id="studyDetails" class="detailsContainer tightContent" style="height:400px;padding:10px;position:relative;">'
	# Build up the data:
	studies = []
	climates = [['location','marker']]
	pathPrefix = './analyses/' + analysisName
	# put the map and table in:
	for study in os.listdir(pathPrefix + '/studies/'):
		with open(pathPrefix + '/studies/' + study + '/metadata.txt', 'r') as mdFile:
			metadata = eval(mdFile.read())
		climates.append([str(metadata['climate']),1])
		studies.append([metadata['name'], metadata['sourceFeeder']])
	outputBuffer += '<div id="mapDiv" style="position:absolute;width:500px;height:400px;top:0px;left:500px"><script>drawMap(' + str(climates) + ',"mapDiv")</script></div>'
	# handle the creation date:
	with open(pathPrefix + '/metadata.txt','r') as anaMdFile:
		created = eval(anaMdFile.read())['created']
	outputBuffer += '<div id="detailsDiv" style="position:absolute;width:500px;height:250px;left:0px;top:0px;padding:10px";overflow:auto><p>Analysis created ' + created + '</p>'
	# add the feeder table:
	outputBuffer += '<table id="detailsTable" style="padding-top:10px"><tr><th>Study</th><th>Source Feeder</th></tr>'
	for row in studies:
		sourceFeedName = row[1]
		outputBuffer += '<tr><td>' + row[0] + '</td><td><a href="/model/' + sourceFeedName + '">' + sourceFeedName + '</a></td></tr>'
	outputBuffer += '</table></div>'
	# add the pie chart:
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
	graphOptions = '{title:"Grid Components", colors:["gainsboro","silver","gray"], titleTextStyle:{fontSize:14},chartArea:{left:10}}'
	outputBuffer += '<div id="comparisonPieChart" style="position:absolute;width:500px;height:150px;left:0px;top:250px"><script>drawPieChart(' + str(pieChartData) + ',"comparisonPieChart",' + graphOptions + ')</script></div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.



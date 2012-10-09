#!/usr/bin/env python

import os
import __util__

configHtmlTemplate = "<div id='REMOVALID' class='content studyDetails'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>✖</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>studyDetails</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer =  '<p class="reportTitle">Study Details</p>'
	outputBuffer += '<div id="studyDetails" class="detailsContainer tightContent">'
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
	outputBuffer += '<div id="mapDiv"></div>'	
	outputBuffer += '<script>drawMap(' + str(climates) + ',"mapDiv")</script>'
	# handle the creation date:
	with open(pathPrefix + '/metadata.txt','r') as anaMdFile:
		created = eval(anaMdFile.read())['created']
	# put in the created date:
	outputBuffer += '<div id="detailsDiv"><p>Analysis created ' + created + '</p></div>'
	# add the feeder table:
	outputBuffer += '<table id="detailsTable"><tr><th>Study</th><th>Source Feeder</th></tr>'
	for row in studies:
		sourceFeedName = row[1]
		outputBuffer += '<tr><td>' + row[0] + '</td><td><a href="/model/' + sourceFeedName + '">' + sourceFeedName + '</a></td></tr>'
	outputBuffer += '</table>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
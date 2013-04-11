#!/usr/bin/env python

import os
import __util__
import feeder
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','studyDetails')

def outputHtml(analysisName):
	# General variables:
	pathPrefix = './analyses/' + analysisName
	# Gather analysis variables:
	with open(pathPrefix + '/metadata.json','r') as anaMdFile:
		anaMd = json.load(anaMdFile)
		ana = {}
		ana['name'] = analysisName
		ana['created'] = anaMd['created']
		ana['simLength'] = anaMd['simLength']
		ana['simLengthUnits'] = anaMd['simLengthUnits']
		ana['simStartDate'] = anaMd['simStartDate']
	# Gather study data:
	climates = {}
	studyList = []
	for study in os.listdir(pathPrefix + '/studies/'):
		newStudy = {'studyName':study}
		with open(pathPrefix + '/studies/' + study + '/metadata.json', 'r') as mdFile:
			md = json.load(mdFile)
			# Study metadata:
			newStudy['sourceFeederName'] = md['sourceFeeder']
			# Climate data:
			if md['climate'] in climates:
				climates[md['climate']] += 1
			else:
				climates[md['climate']] = 1
		with open(pathPrefix + '/studies/' + study + '/cleanOutput.json','r') as outFile:
			out = json.load(outFile)
			# newStudy['componentNames'] = out['componentNames']
		studyList.append(newStudy)
	climates = [[key, climates[key]] for key in climates]
	# Partition the names into common names and those unique to each feeder:
	pie = {}
	# commonNames = reduce(lambda x,y:x.intersection(y), dataTree.values())
	# uniqueNames = {study:dataTree[study].difference(commonNames) for study in dataTree}
	# uniqueNameCounts = {study:len(uniqueNames[study]) for study in uniqueNames}
	# uniqueNameCounts['Common to All'] = len(commonNames)
	# Put the data into a chart-friendly format, and chart it:
	# pieChartData = [['Study','Components']] + [[study, uniqueNameCounts[study]] for study in uniqueNameCounts]
	# graphOptions = '{title:"Grid Components", colors:["gainsboro","silver","gray"], titleTextStyle:{fontSize:14},chartArea:{left:10}}'
	# outputBuffer += '<div id="comparisonPieChart" style="position:absolute;width:500px;height:150px;left:0px;top:250px"><script>drawPieChart(' + str(pieChartData) + ',"comparisonPieChart",' + graphOptions + ')</script></div>'
	# Get the template in.
	with open('./reports/studyDetailsOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	print ana
	print studyList
	print climates
	print pie
	# Write the results.
	return template.render(studyList=studyList, ana=ana, climates=json.dumps(climates), pie=json.dumps(pie))



def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
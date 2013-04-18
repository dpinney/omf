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
	allComponents = set()
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
			newStudy['componentNames'] = set(out['componentNames'])
			allComponents.update(out['componentNames'])
		studyList.append(newStudy)
	climates = [['Climate','Studies']] + [[key.replace('.tmy2',''), climates[key]] for key in climates]
	# Partition the names into common names and those unique to each feeder:
	uniqueNameCounts = {x['studyName']:len(allComponents.difference(x['componentNames'])) for x in studyList}
	uniqueNameCounts['Common to All'] = len(allComponents)
	pieChartData = [['Study','Components']] + [[x, uniqueNameCounts[x]] for x in uniqueNameCounts]
	# Get the template in.
	with open('./reports/studyDetailsOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(studyList=studyList, ana=ana, climates=json.dumps(climates), pieChartData=json.dumps(pieChartData))



def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
#!/usr/bin/env python

import os
import __util__
import feeder
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','studyDetails')

def outputHtml(analysisObject, studyList):
	# Gather analysis variables:
	ana = {}
	ana['name'] = analysisObject.name
	ana['created'] = analysisObject.created
	ana['simLength'] = analysisObject.simLength
	ana['simLengthUnits'] = analysisObject.simLengthUnits
	ana['simStartDate'] = analysisObject.simStartDate
	# Gather study data:
	climates = {}
	outputList = []
	allComponents = set()
	for study in studyList:
		newStudy = {'studyName':study.name}
		# Study metadata:
		newStudy['sourceFeederName'] = study.sourceFeeder
		# Climate data:
		if study.climate in climates:
			climates[study.climate] += 1
		else:
			climates[study.climate] = 1
		out = study.outputJson
		newStudy['componentNames'] = set(out.get('componentNames', []))
		allComponents.update(out.get('componentNames', []))
		outputList.append(newStudy)
	climates = [['Climate','Studies']] + [[key.replace('.tmy2',''), climates[key]] for key in climates]
	# Partition the names into common names and those unique to each feeder:
	# Debug here: change allComponents.difference to allComponents.intersection
	uniqueNameCounts = {x['studyName']:len(allComponents.intersection(x['componentNames'])) for x in outputList}
	# uniqueNameCounts['Common to All'] = len(allComponents)
	pieChartData = [['Study','Components']] + [[x, uniqueNameCounts[x]] for x in uniqueNameCounts]
	# Get the template in.
	with open('./reports/studyDetailsOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(outputList=outputList, ana=ana, climates=json.dumps(climates), pieChartData=json.dumps(pieChartData))
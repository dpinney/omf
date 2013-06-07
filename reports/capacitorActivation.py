﻿#!/usr/bin/env python

import os
import __util__ as util
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','capacitorActivation')

def outputHtml(analysisObject, reportConfig):
	# Build up the data:
	resolution = analysisObject.simLengthUnits
	studyList = []
	for study in analysisObject.studies:
		cleanOut = study.outputJson
		if 'Capacitors' in cleanOut:
			newStudy = {'studyName':study.name, 'capList':[]}
			for cap in cleanOut['Capacitors']:
				newCap = {'capName':cap}
				# Draw the graphs:
				graphParams = util.defaultGraphObject(resolution, cleanOut['timeStamps'][0] if cleanOut['timeStamps'] else "0001-01-01")
				graphParams['chart']['renderTo'] = 'chartDiv' + study.name + cap
				graphParams['chart']['height'] = 90
				graphParams['chart']['type'] = 'area'
				graphParams['legend']['enabled'] = False
				graphParams['plotOptions']['area'] = {'stacking':'normal','marker':{'enabled':False},'fillOpacity':1}
				graphParams['series'] =	[	{'type':'area','name':'PhaseA','data':cleanOut['Capacitors'][cap]['switchA'],'color':'gainsboro'},
											{'type':'area','name':'PhaseB','data':cleanOut['Capacitors'][cap]['switchB'],'color':'darkgray'},
											{'type':'area','name':'PhaseC','data':cleanOut['Capacitors'][cap]['switchC'],'color':'gray'}
										]
				newCap['graphParams'] = json.dumps(graphParams)
				newStudy['capList'].append(newCap)
			studyList.append(newStudy)
	# Get the template inserted.
	with open('./reports/capacitorActivationOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(studyList=studyList)
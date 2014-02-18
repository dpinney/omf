#!/usr/bin/env python

import os
import re
import math
import __util__ as util
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','feederPowerConsumption')

def outputHtml(analysisObject, studyList):
	# Variables for the whole analysis:
	allData = {}
	for studyObject in studyList:
		study = studyObject.name
		allData[study] = {}
		studyJson = studyObject.outputJson
		allData[study]['Power'] = studyJson.get('Consumption', {}).get('Power', [])
		allData[study]['totalEnergy'] = util.totalEnergy(allData[study]['Power'], analysisObject.simLengthUnits)
		allData[study]['Losses'] = util.totalEnergy(studyJson.get('Consumption', {}).get('Losses', []), analysisObject.simLengthUnits)
		allData[study]['Loads'] = allData[study]['totalEnergy'] - allData[study]['Losses']
		if 'DG' in studyJson.get('Consumption', {}):
			allData[study]['DG'] = util.totalEnergy(studyJson['Consumption']['DG'], analysisObject.simLengthUnits)
			allData[study]['Loads'] = allData[study]['totalEnergy'] - allData[study]['Losses'] + allData[study]['DG']
		else:
			allData[study]['DG'] = 0
	# Add the power time series graph:
	powGraphParams = util.defaultGraphObject(analysisObject.simLengthUnits, analysisObject.simStartDate)
	powGraphParams['chart']['renderTo'] = 'powerTimeSeries'
	powGraphParams['chart']['type'] = 'line'
	powGraphParams['chart']['height'] = 250	
	powGraphParams['yAxis']['title']['text'] = 'Power (W)'
	colorMap = {0:'salmon',1:'red',2:'darkred'}
	for study in allData:
		color = util.rainbow(allData,study,['salmon','red','darkred'])
		powGraphParams['series'].append({'name':study,'data':allData[study]['Power'],'marker':{'enabled':False},'color':color})
	# Add the energy graph:
	energyGraphParams = {
		'chart':{'renderTo':'energyBalance', 'marginRight':20, 'marginBottom':20, 'height':250},
		'title':{'text':None},
		'yAxis':{'title':{'text':'Energy (Wh)', 'style':{'color':'gray'}}},
		'legend':{'layout':'horizontal', 'align':'top', 'verticalAlign':'top', 'x':50, 'y':-10, 'borderWidth':0},
		'credits':{'enabled':False},
		'xAxis':{'categories':[study for study in allData],'tickColor':'gray','lineColor':'gray'},
		'plotOptions':{'spline':{'shadow':False, 'lineWidth':0,'marker':{'radius':8}}, 'column':{'stacking':'normal','shadow':False}},
		'tooltip':{'valueDecimals':1},
		'series':[	{'type':'column','name':'Losses','data':[allData[study]['Losses'] for study in allData], 'color':'orangered'},
					{'type':'column','name':'Loads','data':[allData[study]['Loads'] for study in allData], 'color':'darkorange'},
					{'type':'spline','name':'DG','data':[allData[study]['DG'] for study in allData if 'DG' in allData[study]], 'color':'seagreen'}
				]
	}
	# Get the template in.
	with open('./reports/feederPowerConsumptionOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(powGraphParams=json.dumps(powGraphParams), energyGraphParams=json.dumps(energyGraphParams))

def _tests():
	# Tests go here!
	os.chdir('..')
	os.listdir('.')
	print outputHtml('Loss Test')

if __name__ == '__main__':
	_tests()
#!/usr/bin/env python

import os
import __util__ as util
import math
import json
from copy import copy

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>regulatorPowerflow</td></tr></table>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer =  '<p class="reportTitle">Regulator Powerflow</p>\n'
	outputBuffer += '<div id="regPowReport" class="tightContent">\n'
	pathPrefix = './analyses/' + analysisName
	with open(pathPrefix + '/metadata.txt','r') as mdFile:
		resolution = eval(mdFile.read())['simLengthUnits']
	for study in os.listdir(pathPrefix + '/studies/'):
		regFileNames = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('Regulator_') and x.endswith('.csv')]
		outputBuffer += '<div id="regulatorStudy' + study + '" class="studyContainer">\n'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>\n'
		for regulator in regFileNames:
			cleanReg = regulator.replace('.csv','')
			fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + regulator)
			# realPower = [[row[0], row[4], row[6], row[8]] for row in fullArray]
			# reactivePower = [[row[0], row[5], row[7], row[9]] for row in fullArray]
			tapPositions = [[row[0],row[1],row[2],row[3]] for row in fullArray]
			# NOTE: we operate on the values [1:] then put the headers back in a second step.
			apparentPower = [['# timestamp','Tap_A','Tap_B','Tap_C']] + [[row[0], util.pyth(row[4],row[5]), util.pyth(row[6],row[7]), util.pyth(row[8],row[9])] for row in fullArray[1:]]
			powerFactor = [['# timestamp','Power Factor']] + [[row[0], math.cos(math.atan((row[5]+row[7]+row[9])/(row[4]+row[6]+row[8])))] for row in fullArray[1:]]
			# Do day-level aggregation.
			if 'days' == resolution:
				# TODO: don't just max the power! Figure out what to do with tap positions!
				# realPower = [realPower[0]] + util.aggCsv(realPower[1:], max, 'day')
				# reactivePower = [reactivePower[0]] + util.aggCsv(reactivePower[1:], max, 'day')
				tapPositions = [tapPositions[0]] + util.aggCsv(tapPositions[1:], lambda x:sum(x)/len(x), 'day')
				apparentPower = [apparentPower[0]] + util.aggCsv(apparentPower[1:], max, 'day')
				powerFactor = [powerFactor[0]] + util.aggCsv(powerFactor[1:], lambda x:sum(x)/len(x), 'day')
				pass
			# New graphing:
			powGraphParams = {
				'chart':{'renderTo':'', 'type':'line', 'marginRight':20, 'marginBottom':20, 'height':150, 'zoomType':'x'},
				'title':{'text':None},
				'yAxis':{'title':{'text':'App. Power (kW)', 'style':{'color':'gray'}},'plotLines':[{'value':0, 'width':1, 'color':'gray'}]},
				'legend':{'layout':'horizontal', 'align':'top', 'verticalAlign':'top', 'x':50, 'y':-10, 'borderWidth':0},
				'credits':{'enabled':False},
				'xAxis':{'categories':[x[0] for x in apparentPower[1:]],'minTickInterval':len(apparentPower)/100,'labels':{'enabled':False},'maxZoom':20,'tickColor':'gray','lineColor':'gray'},
				'plotOptions':{'line':{'shadow':False}},
				'series':[]
			}
			outputBuffer += '<div id="regCharts' + study + regulator + '"></div>\n'
			# Do apparent power chart:
			appPowerParams = copy(powGraphParams)
			appPowerParams['chart']['renderTo'] = 'regApparentChart' + study + regulator
			colorMap = {0:'crimson',1:'red',2:'firebrick'}
			for x in range(1,len(apparentPower[0])):
				appPowerParams['series'].append({'name':apparentPower[0][x],'data':[y[x] for y in apparentPower[1:]],'marker':{'enabled':False},'color':colorMap[x%3]})
			outputBuffer += '<div id="regApparentChart' + study + regulator + '"></div>\n'
			outputBuffer += '<script>new Highcharts.Chart(' + json.dumps(appPowerParams) + ')</script>\n'
			# Do power factor chart:
			powerFactorParams = copy(powGraphParams)
			powerFactorParams['chart']['renderTo'] = 'regPowFactChart' + study + regulator
			powerFactorParams['yAxis']['title']['text'] = 'Power Factor (%)'
			powerFactorParams['series'] = [{'name':powerFactor[0][1],'data':[y[1] for y in powerFactor[1:]],'marker':{'enabled':False},'color':'red'}]
			outputBuffer += '<div id="regPowFactChart' + study + regulator + '"></div>\n'
			outputBuffer += '<script>new Highcharts.Chart(' + json.dumps(powerFactorParams) + ')</script>\n'
			# Do regulator tap position chart:
			tapPosParams = copy(powGraphParams)
			tapPosParams['chart']['renderTo'] = 'regTapsChart' + study + regulator
			tapPosParams['yAxis']['title']['text'] = 'Tap Multiplier'
			colorMapGray = {0:'gainsboro',1:'silver',2:'gray'}
			tapPosParams['series'] = []
			for x in range(1,len(tapPositions[0])):
				tapPosParams['series'].append({'name':tapPositions[0][x],'data':[y[x] for y in tapPositions[1:]],'marker':{'enabled':False},'color':colorMapGray[x%3]})
			outputBuffer += '<div id="regTapsChart' + study + regulator + '"></div>\n'
			outputBuffer += '<script>new Highcharts.Chart(' + json.dumps(tapPosParams) + ')</script>\n'
		# Close the study div:
		outputBuffer += '</div>'
	return outputBuffer + '</div>\n\n'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
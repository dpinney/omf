#!/usr/bin/env python

import os
import __util__ as util
import math

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>regulatorPowerflow</td></tr></table>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer =  '<p class="reportTitle">Regulator Powerflow</p>'
	outputBuffer += '<div id="regPowReport" class="tightContent">'
	outputBuffer += '''<style type="text/css" scoped>
							div.regContainer {position: relative; height:270px; padding:0px;}
							div.regContainer > div {position: absolute; padding:0px;}
							div.realPowChart {left:0px; top:0px; width:600px; height:90px;}
							div.reacPowChart {left:0px; top:90px; width:600px; height:90px;}
							div.appPowChart {left:0px; top:180px; width:600px; height:90px;}
							div.tapsChart {right:0px; top:0px; width:400px; height:135px;}
							div.powFactChart {right:0px; top:135px; width:400px; height:135px;}
						</style>'''
	pathPrefix = './analyses/' + analysisName
	with open(pathPrefix + '/metadata.txt','r') as mdFile:
		resolution = eval(mdFile.read())['simLengthUnits']
	for study in os.listdir(pathPrefix + '/studies/'):
		regFileNames = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('Regulator_') and x.endswith('.csv')]
		for regulator in regFileNames:
			cleanReg = regulator.replace('.csv','')
			fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + regulator)
			realPower = [[row[0], row[4], row[6], row[8]] for row in fullArray]
			reactivePower = [[row[0], row[5], row[7], row[9]] for row in fullArray]
			tapPositions = [[row[0],row[1],row[2],row[3]] for row in fullArray]
			# NOTE: we operate on the values [1:] then put the headers back in a second step.
			apparentPower = [[row[0], util.pyth(row[4],row[5]), util.pyth(row[6],row[7]), util.pyth(row[8],row[9])] for row in fullArray[1:]]
			apparentPower.insert(0,['# timestamp','Tap_A','Tap_B','Tap_C'])
			powerFactor = [[row[0], math.cos(math.atan((row[5]+row[7]+row[9])/(row[4]+row[6]+row[8])))] for row in fullArray[1:]]
			powerFactor.insert(0,['# timestamp','Power Factor'])
			# Do day-level aggregation.
			if 'days' == resolution:
				# TODO: don't just max the power! Figure out what to do with tap positions!
				realPower = [realPower[0]] + util.aggCsv(realPower[1:], max, 'day')
				reactivePower = [reactivePower[0]] + util.aggCsv(reactivePower[1:], max, 'day')
				tapPositions = [tapPositions[0]] + util.aggCsv(tapPositions[1:], lambda x:sum(x)/len(x), 'day')
				apparentPower = [apparentPower[0]] + util.aggCsv(apparentPower[1:], max, 'day')
				powerFactor = [powerFactor[0]] + util.aggCsv(powerFactor[1:], lambda x:sum(x)/len(x), 'day')
				pass
			# Start to build HTML + graph here.
			chartOptionsRed = '{chartArea:{left:10,top:10}, hAxis:{textPosition:"none"}, colors:["crimson","red","firebrick"]}'
			chartOptionsGray = '{chartArea:{left:10,top:10}, hAxis:{textPosition:"none"}, colors:["gainsboro","silver","gray"]}'
			chartOptionsPowerFactor = '{chartArea:{left:10,top:10}, hAxis:{textPosition:"none"}, vAxis:{minValue:0, maxValue:1}, colors:["crimson","red","firebrick"]}'
			outputBuffer += '<div id="regContainer' + study + regulator + '" class="regContainer">'
			outputBuffer += '<div id="chartRealPow' + study + regulator + '" class="realPowChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(realPower) + ', "chartRealPow' + study + regulator + '", ' + chartOptionsRed + ')</script>'
			outputBuffer += '<div id="chartReactPow' + study + regulator + '" class="reacPowChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(reactivePower) + ', "chartReactPow' + study + regulator + '", ' + chartOptionsRed + ')</script>'
			outputBuffer += '<div id="chartAppPow' + study + regulator + '" class="appPowChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(apparentPower) + ', "chartAppPow' + study + regulator + '", ' + chartOptionsRed + ')</script>'
			outputBuffer += '<div id="chartTaps' + study + regulator + '" class="tapsChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(tapPositions) + ', "chartTaps' + study + regulator + '", ' + chartOptionsGray + ')</script>'
			outputBuffer += '<div id="chartPowFact' + study + regulator + '" class="powFactChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(powerFactor) + ', "chartPowFact' + study + regulator + '", ' + chartOptionsPowerFactor + ')</script>'
			outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
			outputBuffer += '</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
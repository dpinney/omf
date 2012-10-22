#!/usr/bin/env python

import os
import __util__
import math

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<div id='REMOVALID' class='content regulatorPowerflow'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>regulatorPowerflow</td></tr></table></div>"

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
	dataTree = {}
	pathPrefix = './analyses/' + analysisName
	for study in os.listdir(pathPrefix + '/studies/'):
		dataTree[study] = {}
		regFileNames = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('Regulator_') and x.endswith('.csv')]
		for regulator in regFileNames:
			cleanReg = regulator.replace('.csv','')
			dataTree[study][cleanReg] = {}
			fullArray = __util__.csvToArray(pathPrefix + '/studies/' + study + '/' + regulator)
			dataTree[study][cleanReg]['realPower'] = [[row[0], row[4], row[6], row[8]] for row in fullArray]
			dataTree[study][cleanReg]['reactivePower'] = [[row[0], row[5], row[7], row[9]] for row in fullArray]
			dataTree[study][cleanReg]['tapPositions'] = [[row[0],row[1],row[2],row[3]] for row in fullArray]
			# NOTE: we operate on the values [1:] then put the headers back in a second step.
			dataTree[study][cleanReg]['apparentPower'] = [[row[0], __util__.pyth(row[4],row[5]), __util__.pyth(row[6],row[7]), __util__.pyth(row[8],row[9])] for row in fullArray[1:]]
			dataTree[study][cleanReg]['apparentPower'].insert(0,['# timestamp','Tap_A','Tap_B','Tap_C'])
			dataTree[study][cleanReg]['powerFactor'] = [[row[0], math.cos(math.atan((row[5]+row[7]+row[9])/(row[4]+row[6]+row[8])))] for row in fullArray[1:]]
			dataTree[study][cleanReg]['powerFactor'].insert(0,['# timestamp','Power Factor'])
			# Start to build HTML + graph here.
			chartOptionsRed = '{chartArea:{left:10,top:10}, hAxis:{textPosition:"none"}, colors:["crimson","red","firebrick"]}'
			chartOptionsGray = '{chartArea:{left:10,top:10}, hAxis:{textPosition:"none"}, colors:["gainsboro","silver","gray"]}'
			outputBuffer += '<div id="regContainer' + study + regulator + '" class="regContainer">'
			outputBuffer += '<div id="chartRealPow' + study + regulator + '" class="realPowChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(dataTree[study][cleanReg]['realPower']) + ', "chartRealPow' + study + regulator + '", ' + chartOptionsRed + ')</script>'
			outputBuffer += '<div id="chartReactPow' + study + regulator + '" class="reacPowChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(dataTree[study][cleanReg]['reactivePower']) + ', "chartReactPow' + study + regulator + '", ' + chartOptionsRed + ')</script>'
			outputBuffer += '<div id="chartAppPow' + study + regulator + '" class="appPowChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(dataTree[study][cleanReg]['apparentPower']) + ', "chartAppPow' + study + regulator + '", ' + chartOptionsRed + ')</script>'
			outputBuffer += '<div id="chartTaps' + study + regulator + '" class="tapsChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(dataTree[study][cleanReg]['tapPositions']) + ', "chartTaps' + study + regulator + '", ' + chartOptionsGray + ')</script>'
			outputBuffer += '<div id="chartPowFact' + study + regulator + '" class="powFactChart"></div>'
			outputBuffer += '<script>drawLineChart(' + str(dataTree[study][cleanReg]['powerFactor']) + ', "chartPowFact' + study + regulator + '", ' + chartOptionsRed + ')</script>'
			outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
			outputBuffer += '</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
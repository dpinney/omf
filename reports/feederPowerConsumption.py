#!/usr/bin/env python

import os
import re
import math
import __util__ as util
import json

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>feederPowerConsumption</td></tr></table>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = "<p class='reportTitle'>Power Consumption From Transmission System</p><div id='feederPowerConsumptionReport' class='tightContent'>"
	# Variables for the whole analysis:
	pathPrefix = 'analyses/' + analysisName + '/studies/'
	studies = os.listdir(pathPrefix)
	# Figure out what the time interval was:
	with open(pathPrefix + studies[0] + '/main.glm') as testGlm:
		glmContent = testGlm.read()
		intervalText = re.findall('interval\s+(\d+)', glmContent)
		if [] != intervalText:
			interval = float(intervalText[0])
		else:
			interval = 0.0
	# Figure out the stated resolution (can be different than interval):
	with open('./analyses/' + analysisName + '/metadata.txt','r') as mdFile:
		resolution = eval(mdFile.read())['simLengthUnits']
	# Collect the power stats:
	powerTimeSeries = []
	energyTotals = [['Study Name','Energy Used']]
	for study in studies:
		powerToAdd = []
		swingFileNames = [x for x in os.listdir(pathPrefix + study) if x.startswith('SwingKids_') and x.endswith('.csv')]
		for swingFile in swingFileNames:
			fullArray = util.csvToArray(pathPrefix + study + '/' + swingFile)
			fullArray[0] = ['Timestamp', str(study)]
			fullArray[1:] = [[row[0],(-1 if row[1]<0 else 1)*math.sqrt(row[1]**2+row[2]**2)/1000] for row in fullArray[1:]]
			if 'days' == resolution:
				# Aggregate to the day level and max power:
				fullArray = [fullArray[0]] + util.aggCsv(fullArray[1:], max, 'day')
			if [] == powerToAdd:
				powerToAdd = fullArray
			else: 
				for rowNum in xrange(len(fullArray)):
					powerToAdd[rowNum][1] = powerToAdd[rowNum][1] + fullArray[rowNum][1]
		if [] == powerTimeSeries:
			powerTimeSeries = powerToAdd
		else:
			powerTimeSeries = [powerTimeSeries[rowNum] + [powerToAdd[rowNum][1]] for rowNum in xrange(len(powerTimeSeries))]
	# Collect the energy stats
	def totalEnergy(studyName, isRelevantFile, isSinglePhaseNotThree):
		# Helper function for one file:
		def sumEnergy(lossOrGenFilePath, isSinglePhaseNotThree):
			fullData = util.csvToArray(lossOrGenFilePath)
			if isSinglePhaseNotThree:
				apparentPower = [['Datetime','AppPower(kW)']] + [[r[0],util.pyth(r[1],r[2])/1000] for r in fullData[1:]]
			else:
				apparentPower = [['Datetime','AppPower(kW)']] + [[r[0],(util.pyth(r[1],r[2])+util.pyth(r[3],r[4])+util.pyth(r[5],r[6]))/1000] for r in fullData[1:]]
			totalEnergyKwh = sum([interval * row[1] / 3600.0 for row in apparentPower[1:]])
			return totalEnergyKwh
		# Sum energy over all files for a given study:
		studyPrefix = pathPrefix + studyName + '/'
		lossesFiles = [x for x in os.listdir(studyPrefix) if isRelevantFile(x)]
		energies = map(lambda x:sumEnergy(studyPrefix + x, isSinglePhaseNotThree), lossesFiles)
		return sum(energies)
	losses = map(lambda x:totalEnergy(x, lambda y:y in ['TriplexLosses.csv','OverheadLosses.csv','UndergroundLosses.csv','TransformerLosses.csv'], False), studies)
	distGen = map(lambda x:totalEnergy(x, lambda y:y.startswith('Inverter_'), False), studies)
	substation = map(lambda x:totalEnergy(x, lambda y:y.startswith('SwingKids_'), True), studies)
	energyMatrix = [['#'] + map(str,studies),
					['DG'] + distGen,
					['Loads'] + util.vecSum(substation, distGen, [x*-1 for x in losses]),
					['Losses'] + losses]
	energyTotals = [list(r) for r in zip(*energyMatrix)]
	# Add the power time series graph:
	powGraphParams = util.defaultGraphObject(resolution, powerTimeSeries[1][0])
	powGraphParams['chart']['renderTo'] = 'powerTimeSeries'
	powGraphParams['chart']['type'] = 'line'
	powGraphParams['chart']['height'] = 250	
	powGraphParams['yAxis']['title']['text'] = 'Power (kW)'
	colorMap = {0:'salmon',1:'red',2:'darkred'}
	for x in range(1,len(powerTimeSeries[0])):
		powGraphParams['series'].append({'name':powerTimeSeries[0][x],'data':[y[x] for y in powerTimeSeries[1:]],'marker':{'enabled':False},'color':colorMap[x%3]})
	outputBuffer += '<div id="powerTimeSeries"><script>new Highcharts.Chart(' + json.dumps(powGraphParams) + ')</script></div>\n'
	# Add the energy graph:
	energyGraphParams = {
		'chart':{'renderTo':'energyBalance', 'marginRight':20, 'marginBottom':20, 'height':250},
		'title':{'text':None},
		'yAxis':{'title':{'text':'Energy (kWh)', 'style':{'color':'gray'}}},
		'legend':{'layout':'horizontal', 'align':'top', 'verticalAlign':'top', 'x':50, 'y':-10, 'borderWidth':0},
		'credits':{'enabled':False},
		'xAxis':{'categories':[x[0] for x in energyTotals[1:]],'tickColor':'gray','lineColor':'gray'},
		'plotOptions':{'spline':{'shadow':False, 'lineWidth':0,'marker':{'radius':8}}, 'column':{'stacking':'normal','shadow':False}},
		'series':[	{'type':'column','name':energyTotals[0][3],'data':[x[3] for x in energyTotals[1:]], 'color':'orangered'},
					{'type':'column','name':energyTotals[0][2],'data':[x[2] for x in energyTotals[1:]], 'color':'darkorange'},
					{'type':'spline','name':energyTotals[0][1],'data':[x[1] for x in energyTotals[1:]], 'color':'seagreen'}
				]
	}
	outputBuffer += '<div id="energyBalance"><script>new Highcharts.Chart(' + json.dumps(energyGraphParams) + ')</script></div>\n'
	return outputBuffer + '</div>\n\n'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

def main():
	# Tests go here!
	os.chdir('..')
	os.listdir('.')
	print outputHtml('Loss Test')

if __name__ == '__main__':
	main()
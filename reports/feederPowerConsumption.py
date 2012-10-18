#!/usr/bin/env python

import os
import re
import __util__

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<div id='REMOVALID' class='content feederPowerConsumption'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>feederPowerConsumption</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = "<p class='reportTitle'>Power Consumption From Transmission System</p><div id='feederPowerConsumptionReport' class='tightContent'>"
	powerTimeSeries = []
	interval = 0
	energyTotals = [['Study Name','Energy Used']]
	pathPrefix = 'analyses/' + analysisName
	studies = os.listdir(pathPrefix + '/studies/')
	with open(pathPrefix + '/studies/' + studies[0] + '/main.glm') as testGlm:
		glmContent = testGlm.read()
		intervalText = re.findall('interval\s+(\d+)', glmContent)
		if [] != intervalText:
			interval = int(intervalText[0])
	for study in studies:
		energyToAdd = [str(study),0]
		powerToAdd = []
		swingFileNames = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('SwingKids_') and x.endswith('.csv')]
		for swingFile in swingFileNames:
			# fullArray = __csvToArray__(pathPrefix + '/studies/' + study + '/' + swingFile)
			fullArray = __util__.csvToArray(pathPrefix + '/studies/' + study + '/' + swingFile)
			fullArray[0] = ['', str(study)]
			fullArray[1:] = [[row[0],(row[1]+row[2])/1000] for row in fullArray[1:]]
			if [] == powerToAdd:
				powerToAdd = fullArray
			else: 
				for rowNum in xrange(len(fullArray)):
					powerToAdd[rowNum][1] = powerToAdd[rowNum][1] + fullArray[rowNum][1]
			energyToAdd[1] += sum([float(interval) * row[1] / 3600.0 for row in fullArray[1:]])
		energyTotals += [energyToAdd]
		if [] == powerTimeSeries:
			powerTimeSeries = powerToAdd
		else:
			powerTimeSeries = [powerTimeSeries[rowNum] + [powerToAdd[rowNum][1]] for rowNum in xrange(len(powerTimeSeries))]
	# Add the power time series graph:
	powerGraphOptions = "{vAxis:{title:'Power (kW)'}, chartArea:{left:60,top:20,width:'90%',height:'80%'}, hAxis:{title:'Time', textPosition:'none'}, colors:['red','darkred','salmon'], legend:{position:'top'}}"
	outputBuffer += "<div id='powerTimeSeries'><script>drawLineChart(" + str(powerTimeSeries) + ",'powerTimeSeries'," + powerGraphOptions + ")</script></div>"
	# Add the energy graph:
	energyGraphOptions = "{isStacked:true, chartArea:{left:60,top:20,width:'100%'}, hAxis:{title:'Energy (kWH)', gridlines:{count:15}}, vAxis:{textPosition:'in'}, legend:{position:'none'}, colors:['darkorange']}"
	outputBuffer += "<div id='energyBalance'><script>drawBarChart(" + str(energyTotals) + ",'energyBalance'," + energyGraphOptions + ")</script></div>"
	return outputBuffer + "</div>"

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
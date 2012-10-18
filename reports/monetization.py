#!/usr/bin/env python

import os
import re
import __util__
from pprint import pprint
from copy import copy

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = '''
<div id='REMOVALID' class='content monetization' style='background:red'>
	<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a>
	<table class='reportOptions'>
		<tr>
			<td>Report Name</td>
			<td><p class='reportName'>monetization</p></td>
		</tr>
		<tr>
			<td>G&T Energy Cost</td>
			<td><input type='text' class='gtEnergyCost'></td>
		</tr>
		<tr>
			<td>Fixed Hardware Cost</td>
			<td><input type='text' class='fixedHardwareCost'></td>
		</tr>
	</table>
</div>
'''

def outputHtml(analysisName):
	# Start with an output buffer containing the title.
	outputBuffer = '<p class="reportTitle">Cost Benefit Analysis</p><div id="monetizationReport" class="tightContent" style="position:relative;height:650px">'
	# Get all the data from the run:
	powerTimeSeries = []
	energyTimeSeries = []
	interval = 0
	pathPrefix = 'analyses/' + analysisName
	studies = os.listdir(pathPrefix + '/studies/')
	# Get the report input:
	with open (pathPrefix + '/reports/monetization.txt') as reportFile:
		reportOptions = eval(reportFile.read())
	gtEnergyCost = float(reportOptions['gtEnergyCost'])
	# Find the interval size (in seconds):
	with open(pathPrefix + '/studies/' + studies[0] + '/main.glm') as testGlm:
		glmContent = testGlm.read()
		intervalText = re.findall('interval\s+(\d+)', glmContent)
		if [] != intervalText:
			interval = float(intervalText[0])
	# Gather data for all the studies.
	for study in studies:
		powerToAdd = []
		swingFileNames = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('SwingKids_') and x.endswith('.csv')]
		for swingFile in swingFileNames:
			fullArray = __util__.csvToArray(pathPrefix + '/studies/' + study + '/' + swingFile)
			fullArray[0] = ['', str(study)]
			fullArray[1:] = [[row[0],(row[1]+row[2])/1000] for row in fullArray[1:]]
			if [] == powerToAdd:
				powerToAdd = fullArray
			else:
				for rowNum in xrange(len(fullArray)):
					powerToAdd[rowNum][1] = powerToAdd[rowNum][1] + fullArray[rowNum][1]
		if [] == powerTimeSeries:
			powerTimeSeries = powerToAdd
		else:
			powerTimeSeries = [powerTimeSeries[rowNum] + [powerToAdd[rowNum][1]] for rowNum in xrange(len(powerTimeSeries))]
	energyTimeSeries = copy(powerTimeSeries)
	energyTimeSeries[1:] = [[row[0]] + map(lambda x:x*interval/3600.0, row[1:]) for row in energyTimeSeries[1:]]
	print 'INTERVAL: ' + str(interval)
	# Add the power time series graph:
	powerGraphOptions = '{vAxis:{title:"Power (kW)"}, chartArea:{left:60,top:20,width:"90%",height:"80%"}, hAxis:{title:"Time", textPosition:"none"}, colors:["red","darkred","salmon"], legend:{position:"top"}}'
	energyGraphOptions = '{vAxis:{title:"Energy (kWh)"}, chartArea:{left:60,top:20,width:"90%",height:"80%"}, hAxis:{title:"Time", textPosition:"none"}, colors:["orange","darkorange","chocolate"], legend:{position:"top"}}'
	outputBuffer += '<div id="monPowerTimeSeries" style="position:absolute;top:0px;left:0px;width:500px;height:200px"><script>drawLineChart(' + str(powerTimeSeries) + ',"monPowerTimeSeries",' + powerGraphOptions + ')</script></div>'
	# Add the energy graph:
	outputBuffer += '<div id="monEnergyBalance" style="position:absolute;top:0px;left:500px;width:500px;height:200px"><script>drawLineChart(' + str(energyTimeSeries) + ',"monEnergyBalance",' + energyGraphOptions + ')</script></div>'
	moneyPowerGraphOptions = '{vAxis:{title:"Power (kW)"}, chartArea:{left:60,top:20,width:"90%",height:"80%"}, hAxis:{title:"Time", textPosition:"none"}, colors:["red","darkred","salmon"], legend:{position:"top"}}'
	moneyEnergyGraphOptions = '{vAxis:{title:"Energy Cost ($)"}, chartArea:{left:60,top:20,width:"90%",height:"80%"}, hAxis:{title:"Time", textPosition:"none"}, colors:["orange","darkorange","chocolate"], legend:{position:"top"}}'
	# Monetized power graph:
	outputBuffer += '<div id="monetizedPowerTimeSeries" style="position:absolute;top:200px;left:0px;width:500px;height:200px"><script>drawLineChart(' + str(powerTimeSeries) + ',"monetizedPowerTimeSeries",' + moneyPowerGraphOptions + ')</script></div>'
	# Monetized energy graph:
	monetizedEnergy = [energyTimeSeries[0]] + [[row[0]] + map(lambda x:x*gtEnergyCost, row[1:]) for row in energyTimeSeries[1:]]
	outputBuffer += '<div id="monetizedEnergyBalance" style="position:absolute;top:200px;left:500px;width:500px;height:200px"><script>drawLineChart(' + str(monetizedEnergy) + ',"monetizedEnergyBalance",' + moneyEnergyGraphOptions + ')</script></div>'
	# Other metrics table:
	outputBuffer += '<div id="additionalMetrics" style="position:absolute;top:410px;left:0px;width:1000px;height:240px">'
	tableOptions = '{}'
	outputBuffer += '<script>drawTable(' + str(powerTimeSeries) + ',"additionalMetrics",' + tableOptions + ')</script>'
	outputBuffer +='</div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
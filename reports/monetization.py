#!/usr/bin/env python

import os
import re
import __util__
from pprint import pprint
from copy import copy

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = '''
<div id='REMOVALID' class='content monetization'>
	<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a>
	<table class='reportOptions'>
		<tr>
			<td>Report Name</td>
			<td><p class='reportName'>monetization</p></td>
		</tr>
		<tr>
			<td>Distribution Co-op Energy Rate ($/kWh)</td>
			<td><input type='text' class='distrEnergyRate'></td>
		</tr>
		<tr>
			<td>Distribution Co-op Capacity Rate ($/kW)</td>
			<td><input type='text' class='distrCapacityRate'></td>
		</tr>
		<tr>
			<td>Equipment and Installation Cost ($)</td>
			<td><input type='text' class='equipAndInstallCost'></td>
		</tr>
		<tr>
			<td>Operating and Maintenance Cost ($/Month)</td>
			<td><input type='text' class='opAndMaintCost'></td>
		</tr>
	</table>
</div>
'''

def outputHtml(analysisName):
	# Start with an output buffer containing the title.
	outputBuffer = '<p class="reportTitle">Cost Benefit Analysis</p><div id="monetizationReport" class="tightContent" style="position:relative;height:600px">'
	# Get all the data from the run:
	powerTimeSeries = []
	energyTimeSeries = []
	interval = 0
	pathPrefix = 'analyses/' + analysisName
	studies = os.listdir(pathPrefix + '/studies/')
	# Get the report input:
	with open (pathPrefix + '/reports/monetization.txt') as reportFile:
		reportOptions = eval(reportFile.read())
	distrEnergyRate = float(reportOptions['distrEnergyRate'])
	distrCapacityRate = float(reportOptions['distrCapacityRate'])
	equipAndInstallCost = float(reportOptions['equipAndInstallCost'])
	opAndMaintCost = float(reportOptions['opAndMaintCost'])
	# Find the interval size (in seconds):
	with open(pathPrefix + '/studies/' + studies[0] + '/main.glm') as testGlm:
		glmContent = testGlm.read()
		intervalText = re.findall('interval\s+(\d+)', glmContent)
		if [] != intervalText:
			interval = float(intervalText[0])
	# Insert the metrics table framework.
	outputBuffer += '<div id="additionalMetrics" style="position:absolute;top:410px;left:0px;width:1000px;height:190px;overflow-y:auto;overflow-x:hidden">'
	outputBuffer += '<div style="width:1000px;height:40px;padding:0px 5px 0px 5px">Co-op Energy Rate ($/kWh) <input id="distrEnergyRate" value="' + str(distrEnergyRate) + '"/> Capacity Rate ($/kW) <input id="distrCapacityRate" value="' + str(distrCapacityRate) + '"/> <button style="width:100px" onclick="recalculateCostBenefit()">Recalculate</button></div>'
	outputBuffer += '<table style="width:980px"><thead><tr><th>Study</th><th>Baseline</th><th>Capital Cost</th><th>O&amp;M Cost</th><th>Capacity Cost</th><th>Energy Cost</th><th>NPV</th><th>C/B</th></tr></thead><tbody id="additionalMetricsTable">'
	# Gather data for all the studies. firstStudy indicates our default baseline.
	firstStudy = True
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
		# Add this study's row to the metrics table:
		outputBuffer += '<tr><td class="studyName">' + study + '</td>' + \
					'<td><input type="radio" name="baseline" class="baseline"' + ('checked' if firstStudy else '') + '/></td>' + \
					'<td><input class="capCost" value="' + ('0' if firstStudy else str(equipAndInstallCost)) + '"/></td>' + \
					'<td><input class="omCost" value="' + ('0' if firstStudy else str(opAndMaintCost)) + '"/></td>' + \
					'<td class="capacityCost">calcMe</td>' + \
					'<td class="enerCost">calcMe</td>' + \
					'<td class="NPV">calcMe</td>' + \
					'<td class="costBen">calcMe</td></tr>'
		# After the first study, unset the indicator:
		firstStudy = False
	# Get the energy data from the power data:
	energyTimeSeries = copy(powerTimeSeries)
	energyTimeSeries[1:] = [[row[0]] + map(lambda x:x*interval/3600.0, row[1:]) for row in energyTimeSeries[1:]]	
	# Monetize stuff, then get per-study totals:
	monetizedPower = [powerTimeSeries[0]] + processMonths(powerTimeSeries[1:], lambda x:max(x)/len(x)*distrCapacityRate)
	monetizedEnergy = [energyTimeSeries[0]] + processMonths(energyTimeSeries[1:], lambda x:sum(x)/len(x)*distrEnergyRate)
	energyTotals = {col[0]:sum(col[1:])/distrEnergyRate for col in zip(*monetizedEnergy)[1:]}
	capTotals = {col[0]:sum(col[1:])/distrCapacityRate for col in zip(*monetizedPower)[1:]}
	# Add the calculation script and close the table elements.
	outputBuffer += '</tbody></table>'
	outputBuffer += '<script>energyTotals=' + str(energyTotals) + ';capTotals=' + str(capTotals) + '</script>'
	outputBuffer += ''' <script>
							function recalculateCostBenefit() {
								baseCost = 0
								energyRate = parseFloat(gebi('distrEnergyRate').value)
								capRate = parseFloat(gebi('distrCapacityRate').value)
								tableRows = gebi('additionalMetricsTable').childNodes
								totalRows = tableRows.length
								for (rowNum=0;rowNum<totalRows;rowNum++) {
									daRow = tableRows[rowNum]
									studyName = daRow.querySelector('.studyName').innerHTML
									isBaseline = daRow.querySelector('.baseline').checked
									capacityCost = parseFloat((capRate * capTotals[studyName]).toPrecision(4))
									daRow.querySelector('.capacityCost').innerHTML = capacityCost
									enerCost = parseFloat((energyRate * energyTotals[studyName]).toPrecision(4))
									daRow.querySelector('.enerCost').innerHTML = enerCost
									if (isBaseline) {
										daRow.querySelector('.NPV').innerHTML = '0'
										daRow.querySelector('.costBen').innerHTML = 'N/A'
										capCost = parseFloat(daRow.querySelector('.capCost').value)
										omCost = parseFloat(daRow.querySelector('.omCost').value)
										console.log(capacityCost, enerCost, capCost, omCost, baseCost)
										baseCost = capCost + omCost + enerCost + capacityCost
									}
								}
								for (rowNum=0;rowNum<totalRows;rowNum++) {
									daRow = tableRows[rowNum]
									isBaseline = daRow.querySelector('.baseline').checked
									if (!isBaseline) {
										capacityCost = parseFloat(daRow.querySelector('.capacityCost').innerHTML)
										enerCost = parseFloat(daRow.querySelector('.enerCost').innerHTML)
										capCost = parseFloat(daRow.querySelector('.capCost').value)
										omCost = parseFloat(daRow.querySelector('.omCost').value)
										console.log(capacityCost, enerCost, capCost, omCost, baseCost)
										thisRowCost = capacityCost + enerCost + capCost + omCost
										NPV = baseCost - thisRowCost
										daRow.querySelector('.NPV').innerHTML = NPV
										daRow.querySelector('.costBen').innerHTML = thisRowCost/NPV
									}
								}
							}
							recalculateCostBenefit()
						</script> '''
	outputBuffer += '</div>'
	# Power graph:
	powerGraphOptions = '{vAxis:{title:"Power (kW)"}, chartArea:{left:60,top:20,width:"93%",height:"80%"}, hAxis:{title:"Time", textPosition:"none"}, colors:["red","darkred","salmon"], legend:{position:"top"}}'
	outputBuffer += '<div id="monPowerTimeSeries" style="position:absolute;top:0px;left:0px;width:1000px;height:200px"><script>drawLineChart(' + str(powerTimeSeries) + ',"monPowerTimeSeries",' + powerGraphOptions + ')</script></div>'
	# Money power graph:
	moneyPowerGraphOptions = '{vAxis:{title:"Capacity Cost ($)"}, chartArea:{left:60,top:20,width:"85%",height:"80%"}, hAxis:{title:"Time", textPosition:"none"}, colors:["red","darkred","salmon"], legend:{position:"top"}}'
	outputBuffer += '<div id="monetizedPowerTimeSeries" style="position:absolute;top:200px;left:0px;width:500px;height:200px"><script>drawLineChart(' + str(monetizedPower) + ',"monetizedPowerTimeSeries",' + moneyPowerGraphOptions + ')</script></div>'
	# Money energy graph:
	moneyEnergyGraphOptions = '{vAxis:{title:"Energy Cost ($)"}, chartArea:{left:60,top:20,width:"85%",height:"80%"}, hAxis:{title:"Time", textPosition:"none"}, colors:["orange","darkorange","chocolate"], legend:{position:"top"}}'
	outputBuffer += '<div id="monetizedEnergyBalance" style="position:absolute;top:200px;left:500px;width:500px;height:200px"><script>drawLineChart(' + str(monetizedEnergy) + ',"monetizedEnergyBalance",' + moneyEnergyGraphOptions + ')</script></div>'
	return outputBuffer + '</div>'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

def processMonths(inList, listFunc):
	# Given a month chunk, replace values so they're all equal to the listFunc ones.
	def peakPower(monthList):
		colForm = zip(*monthList)
		header = colForm[0]
		def replaceWithMax(inList):
			maximum = listFunc(inList)
			return map(lambda x:maximum, inList)
		peaks = [header] + map(replaceWithMax, colForm[1:])
		return [list(x) for x in zip(*peaks)]
	# Walk the full inList, split it into months, and process each month chunk.
	workList = copy(inList)
	monthYear = workList[0][0][0:7]
	startRow = 0
	for rowNum in xrange(len(inList)):
		if workList[rowNum][0][0:7] == monthYear and rowNum != len(inList)-1:
			pass
		else:
			monthYear = workList[rowNum][0][0:7]
			workList[startRow:rowNum+1] = peakPower(workList[startRow:rowNum+1])
			startRow = rowNum
	return workList
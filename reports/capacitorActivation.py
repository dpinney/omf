#!/usr/bin/env python

import os
import __util__ as util
import json

configHtmlTemplate = "<a onclick='javascript:removeStudyReport(this)' class='removeStudyReport'>&#10006;</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>capacitorActivation</td></tr></table>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer =  '<p class="reportTitle">Capacitor Activation</p>'
	outputBuffer += '<div id="capActReport" class="tightContent">'
	# Build up the data:
	pathPrefix = './analyses/' + analysisName
	resolution = json.loads(util.fileSlurp(pathPrefix + '/metadata.json'))['simLengthUnits']
	for study in os.listdir(pathPrefix + '/studies/'):
		capFileNames = filter(lambda x:x.startswith('Capacitor_') and x.endswith('.csv'), os.listdir(pathPrefix + '/studies/' + study))
		outputBuffer += '<div id="capStudy' + study + '" class="studyContainer">'
		outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>'
		for capacitor in capFileNames:
			cap = capacitor.replace('.csv','')
			fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + capacitor)
			if 'days' == resolution:
				# Aggregate to the day level, averaging to percentage charging:
				fullArray = [fullArray[0]] + util.aggCsv(fullArray[1:], lambda x:sum(x)/len(x), 'day')
			# Draw the graphs:
			graphParams = util.defaultGraphObject(resolution, fullArray[1][0])
			graphParams['chart']['renderTo'] = 'chartDiv' + study + cap
			graphParams['chart']['height'] = 90
			graphParams['chart']['type'] = 'area'
			graphParams['legend']['enabled'] = False
			graphParams['plotOptions']['area'] = {'stacking':'normal','marker':{'enabled':False},'fillOpacity':1}
			graphParams['series'] = [	{'type':'area','name':'PhaseA','data':util.roundSeries([x[1] for x in fullArray[1:]]),'color':'gainsboro'},
										{'type':'area','name':'PhaseB','data':util.roundSeries([x[2] for x in fullArray[1:]]),'color':'darkgray'},
										{'type':'area','name':'PhaseC','data':util.roundSeries([x[3] for x in fullArray[1:]]),'color':'gray'}
									]
			outputBuffer += '<div id="chartDiv' + study + cap + '" class="capChart" style="height:90px"><script>new Highcharts.Chart(' + json.dumps(graphParams) + ')</script></div>\n'
		outputBuffer += '</div>'
	return outputBuffer + '</div>\n\n'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
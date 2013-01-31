#!/usr/bin/env python

import os
import __util__ as util
import json

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = "<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>capacitorActivation</td></tr></table>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer =  '<p class="reportTitle">Capacitor Activation</p>'
	outputBuffer += '<div id="capActReport" class="tightContent">'
	# Build up the data:
	pathPrefix = './analyses/' + analysisName
	with open(pathPrefix + '/metadata.txt','r') as mdFile:
		resolution = eval(mdFile.read())['simLengthUnits']
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
			graphParams = {
				'chart':{'renderTo':'chartDiv' + study + cap, 'marginRight':20, 'marginBottom':10, 'marginTop':0, 'zoomType':'x', 'height':90},
				'title':{'text':None},
				'yAxis':{'title':{'text':None}, 'labels':{'enabled':False}, 'gridLineWidth':0},
				'legend':{'enabled':False},
				'credits':{'enabled':False},
				'xAxis':{'categories':[x[0] for x in fullArray[1:]],'minTickInterval':len(fullArray)/100,'tickColor':'gray','lineColor':'gray','labels':{'enabled':False},'maxZoom':20},
				'plotOptions':{'area':{'shadow':False,'stacking':'normal','marker':{'enabled':False},'fillOpacity':1,}},
				'series':[	{'type':'area','name':'PhaseA','data':[x[1] for x in fullArray[1:]],'color':'gainsboro'},
							{'type':'area','name':'PhaseB','data':[x[2] for x in fullArray[1:]],'color':'darkgray'},
							{'type':'area','name':'PhaseC','data':[x[3] for x in fullArray[1:]],'color':'gray'}
						]
			}
			outputBuffer += '<div id="chartDiv' + study + cap + '" class="capChart" style="height:90px"><script>new Highcharts.Chart(' + json.dumps(graphParams) + ')</script></div>\n'
		outputBuffer += '</div>'
	return outputBuffer + '</div>\n\n'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
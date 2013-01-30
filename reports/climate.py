#!/usr/bin/env python

import os
import __util__ as util
from pprint import pprint
import sys
from os.path import dirname
# go two layers up and add that to this file's temp path
sys.path.append(dirname(dirname(os.getcwd())))
import lib
import json

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = '''<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>x</a>
						<table class='reportOptions'>
							<tr>
								<td>Report Name</td>
								<td class='reportName'>climate</td>
							</tr>
						</table>
						'''

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Climate</p>\n<div id="climateReport" class="tightContent" style="position:relative">\n'
	# Collect study variables:
	pathPrefix = './analyses/' + analysisName
	resolution = eval(lib.fileSlurp(pathPrefix + '/metadata.txt'))['simLengthUnits']
	studies = os.listdir(pathPrefix + '/studies/')
	metadatas = map(lambda x:lib.fileSlurp(pathPrefix + '/studies/' + x + '/metadata.txt'), studies)
	climates = set(map(lambda x:eval(x)['climate'], metadatas))
	# If we have more than one study, just show one climate:
	if 1 == len(climates):
		studies = [studies[0]]
		title = False
	else:
		title = True
	# Turn each study into graphics:
	for study in studies:
		climateFiles = [x for x in os.listdir(pathPrefix + '/studies/' + study) if x.startswith('Climate_')]
		fullArray = util.csvToArray(pathPrefix + '/studies/' + study + '/' + climateFiles[0])
		fullArray[0] = ['Timestamp','Temperature (dF)','D.Insolation (W/m^2)', 'Wind Speed', 'Rainfall (in/h)', 'Snow Depth (in)']
		if 'days' == resolution:
			# Aggregate to the day level, maxing climate but averaging insolation, summing rain:
			funs = {0:max, 1:lambda x:sum(x)/len(x), 2:max, 3:sum, 4:max}
			fullArray = [fullArray[0]] + util.aggCsv(fullArray[1:], funs, 'day')
			fullArray[0] = ['Timestamp','Max Temp (dF)','Avg Insol (W/m^2)', 'Max Wind Speed', 'Rainfall (in/h)', 'Max Snow Depth (in)']
		# Setting up the graph options:
		graphParameters = {
			'chart':{'renderTo':'', 'type':'line', 'marginRight':20, 'marginBottom':20, 'zoomType':'x'},
			'title':{'text':None},
			'yAxis':{'title':{'text':None},'plotLines':[{'value':0, 'width':1, 'color':'#808080'}]},
			'legend':{'layout':'horizontal', 'align':'top', 'verticalAlign':'top', 'x':50, 'y':0, 'borderWidth':0},
			'credits':{'enabled':False},
			'xAxis':{'categories':[],'labels':{'enabled':False},'maxZoom':20},
			'plotOptions':{'line':{'shadow':False}},
			'series':[]
		}
		graphParameters['chart']['renderTo'] = 'climateChartDiv' + str(study)
		graphParameters['xAxis']['categories'] = [x[0] for x in fullArray[1:]]
		graphParameters['series'].append({'name':fullArray[0][1],'data':[x[1] for x in fullArray[1:]],'marker':{'enabled':False},'color':'dimgray'})
		graphParameters['series'].append({'name':fullArray[0][2],'data':[x[2] for x in fullArray[1:]],'marker':{'enabled':False},'color':'darkgray'})
		graphParameters['series'].append({'name':fullArray[0][3],'data':[x[3] for x in fullArray[1:]],'marker':{'enabled':False},'color':'darkgray'})
		graphParameters['series'].append({'name':fullArray[0][4],'data':[x[4] for x in fullArray[1:]],'marker':{'enabled':False},'color':'gainsboro'})
		graphParameters['series'].append({'name':fullArray[0][5],'data':[x[5] for x in fullArray[1:]],'marker':{'enabled':False},'color':'gainsboro'})
		# Write one study's worth of HTML:
		outputBuffer += '<div id="climateStudy' + study + '" class="studyContainer">\n'
		outputBuffer += '<div id="climateChartDiv' + study + '" style="height:250px"></div>\n'
		if True == title:
			outputBuffer += '<div class="studyTitleBox"><p class="studyTitle">' + study + '</p></div>\n'
		outputBuffer += '<script>\n'
		outputBuffer += 'new Highcharts.Chart(' + json.dumps(graphParameters) + ');\n'
		outputBuffer += '</script>\n'
		outputBuffer += '</div>\n'
	return outputBuffer + '</div>\n'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

def main():
	# tests go here.
	os.chdir('..')
	outputHtml('SolarTrio')

if __name__ == '__main__':
	main()


'''

source info:
http://www.gridlabd.org/documents/doxygen/latest_dev/climate_8h-source.html

'''
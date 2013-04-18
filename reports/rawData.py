#!/usr/bin/env python

import os
import __util__ as util
import json

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','rawData')

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Full Output Data</p>\n'
	outputBuffer += '<div id="rawData" class="tightContent">\n'
	# Collect study variables:
	data = {}
	for study in os.listdir('./analyses/' + analysisName + '/studies/'):
		with open('./analyses/' + analysisName + '/studies/' + study + '/cleanOutput.json','r') as outFile:
			data[study] = json.load(outFile)
	outputBuffer += '<script>allOutputData = ' + json.dumps(data) + '</script>\n'
	outputBuffer += '<p style="padding:10px">Look at JSON variable "allOutputData" in the console.</p>'
	return outputBuffer + '</div>\n\n'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

def main():
	# tests go here.
	os.chdir('..')
	print outputHtml('SolarTrio')

if __name__ == '__main__':
	main()
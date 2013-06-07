﻿#!/usr/bin/env python

import os
import __util__ as util
import json

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','rawData')

def outputHtml(analysisObject, reportConfig):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Full Output Data</p>\n'
	outputBuffer += '<div id="rawData" class="tightContent">\n'
	# Collect study variables:
	data = {}
	for study in analysisObject.studies:
		data[study.name] = study.outputJson
	outputBuffer += '<script>allOutputData = ' + json.dumps(data) + '</script>\n'
	outputBuffer += '<p style="padding:10px">Look at JSON variable "allOutputData" in the console.</p>'
	return outputBuffer + '</div>\n\n'

if __name__ == '__main__':
	# tests go here.
	os.chdir('..')
	print outputHtml('SolarTrio')

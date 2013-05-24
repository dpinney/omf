#!/usr/bin/env python

import os
import textwrap
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','runtimeStats')

def outputHtml(analysisName):
	# Collect pre tag info for each study:
	pathPrefix = 'analyses/' + analysisName + '/studies/'
	stdList = []
	for study in os.listdir(pathPrefix):
		with open(pathPrefix + study + '/cleanOutput.json','r') as outFile:
			cleanOut = json.load(outFile)
		stderrText = cleanOut.get('stderr', '')
		stdoutText = cleanOut.get('stdout', '')
		if 'ERROR' in stderrText or 'WARNING' in stderrText:
			# Error'd out, so show it:
			cleanPre = study.upper() + '\n\n' + stderrText
		else:
			# No errors, so get stdout:
			cleanPre = study.upper() + '\n\n' + stdoutText
		stdList.append(cleanPre)
	# Get the template in.
	with open('./reports/runtimeStatsOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(stdList=stdList)

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.

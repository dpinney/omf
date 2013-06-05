#!/usr/bin/env python

import os
import textwrap
import json
from jinja2 import Template

with open('./reports/defaultConfig.html','r') as configFile:
	configHtmlTemplate = configFile.read().replace('{{reportName}}','runtimeStats')

def outputHtml(analysisObject, reportConfig):
	# Collect pre tag info for each study:
	stdList = []
	for study in analysisObject.studies:
		cleanOut = study.outputJson
		stderrText = cleanOut.get('stderr', '')
		stdoutText = cleanOut.get('stdout', '')
		if 'ERROR' in stderrText or 'WARNING' in stderrText:
			# Error'd out, so show it:
			cleanPre = study.name.upper() + '\n\n' + stderrText
		else:
			# No errors, so get stdout:
			cleanPre = study.name.upper() + '\n\n' + stdoutText
		stdList.append(cleanPre)
	# Get the template in.
	with open('./reports/runtimeStatsOutput.html','r') as tempFile:
		template = Template(tempFile.read())
	# Write the results.
	return template.render(stdList=stdList)
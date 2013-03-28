#!/usr/bin/env python

import os
import textwrap

configHtmlTemplate = "<a onclick='javascript:removeStudyReport(this)' class='removeStudyReport'>&#10006;</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>runtimeStats</td></tr></table>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = "<p class='reportTitle'>Model Runtime Statistics</p><div id='runtimeStatsReport' class='content stdouts'>"
	# Collect pre tag info for each study:
	for study in os.listdir('analyses/' + analysisName + '/studies/'):
		with open('analyses/' + analysisName + '/studies/' + study + '/stdout.txt', 'r') as stdout, open('analyses/' + analysisName + '/studies/' + study + '/stderr.txt', 'r') as stderr:
			stderrText = textwrap.fill(stderr.read().strip(), 62).replace('ERROR','\n\nERROR').replace('WARNING','\n\nWARNING').replace('FATAL','\n\nFATAL')
			stdoutText = stdout.read().strip()
			if 'ERROR' in stderrText or 'WARNING' in stderrText:
				# Error'd out, so show it:
				cleanPre = study.upper() + '\n\n' + stderrText
			else:
				# No errors, so get stdout:
				cleanPre = study.upper() + '\n\n' + stdoutText
			outputBuffer += "<pre class='stdoutBlock'>" + cleanPre + "</pre>"
	return outputBuffer + '</div>\n\n'

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
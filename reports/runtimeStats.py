#!/usr/bin/env python

import os

configHtmlTemplate = "<div id='REMOVALID' class='content REPORTNAME'><a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>✖</a><table class='reportOptions'><tr><td>Report Name</td><td class='reportName'>REPORTNAME</td></tr></table></div>"

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = "<p class='reportTitle'>Model Runtime Statistics</p><div id='runtimeStatsReport' class='content stdouts'>"
	# Collect pre tag info for each study:
	for study in os.listdir('analyses/' + analysisName + '/studies/'):
		with open('analyses/' + analysisName + '/studies/' + study + '/stdout.txt', 'r') as stdout:
			# Hack: drop leading \r newlines:
			cleanPre = study.upper() + '\n\n' + stdout.read().replace('\r','')
			outputBuffer += "<pre class='stdoutBlock'>" + cleanPre + "</pre>"
	return outputBuffer + "</div>"

def modifyStudy(analysisName):
	pass
	#TODO: implement if needed.
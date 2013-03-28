#!/usr/bin/env python

import os
import __util__ as util
import json

# The config template, when inserted, will have the string REMOVALID replaced with a unique GUID.
configHtmlTemplate = '''<a href='javascript:removeStudyReport(REMOVALID)' class='removeStudyReport'>&#10006;</a>
						<table class='reportOptions'>
							<tr>
								<td>Report Name</td>
								<td class='reportName'>rawData</td>
							</tr>
						</table>
						'''

def outputHtml(analysisName):
	# Put the title in:
	outputBuffer = '<p class="reportTitle">Full Output Data</p>\n'
	outputBuffer += '<div id="rawData" class="tightContent">\n'
	# Collect study variables:
	data = util.anaDataTree('./analyses/' + analysisName, lambda x:True)
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


'''

source info:
http://www.gridlabd.org/documents/doxygen/latest_dev/climate_8h-source.html

'''
#!/usr/bin/env python
# encoding: utf-8

import os
import shutil
import datetime as dt
import reports

class Analysis:
	def __init__(self, jsonDict):
		self.status = jsonDict.get('status','')
		self.sourceFeeder = jsonDict.get('sourceFeeder','')
		self.climate = jsonDict.get('climate','')
		self.created = jsonDict.get('created','')
		self.simStartDate = jsonDict.get('simStartDate','')
		self.simLength = jsonDict.get('simLength',0)
		self.simLengthUnits = jsonDict.get('simLengthUnits','')
		self.runTime = jsonDict.get('runTime','')
		self.name = jsonDict.get('name','')
		self.reports = jsonDict.get('reports', [])
		self.studyNames = jsonDict.get('studyNames', [])

	def generateReportHtml(self, studyList):
		# Iterate over reports and collect what we need: 
		reportList = []
		for report in self.reports:
			# call the relevant reporting function by name.
			reportModule = getattr(reports, report['reportType'])
			reportList.append(reportModule.outputHtml(self, studyList))
		return reportList

	def run(self, studyList):
		# NOTE! We are running studies serially. We use lower levels of RAM/CPU, potentially saving time if swapping were to occur.
		self.status = 'running'
		startTime = dt.datetime.now()
		for study in studyList:
			exitStatus = study.run()
			if exitStatus == False:
				self.status = 'terminated'
				self.runTime = ''
				return
		if self.status not in ['terminated','ERROR']:
			endTime = dt.datetime.now()
			self.runTime = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
			self.status = 'postRun'

if __name__ == '__main__':
	pass
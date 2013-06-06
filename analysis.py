#!/usr/bin/env python
# encoding: utf-8

import os
import shutil
import datetime as dt
import feeder
import subprocess
import copy
import json
import studies
import reports
import storage

store = storage.Filestore('data')

class Analysis:
	# Metadata attributes
	name = ''
	status = ''
	sourceFeeder = ''
	climate = ''
	created = ''
	simStartDate = ''
	simLength = ''
	simLengthUnits = 0
	runTime = ''
	# Data attributes
	reports = []
	studyNames = []
	# Internal attributes
	studies = []

	def __init__(self, name, jsonMdDict, jsonDict):
		self.status = jsonMdDict.get('status','')
		self.sourceFeeder = jsonMdDict.get('sourceFeeder','')
		self.climate = jsonMdDict.get('climate','')
		self.created = jsonMdDict.get('created','')
		self.simStartDate = jsonMdDict.get('simStartDate','')
		self.simLength = jsonMdDict.get('simLength',0)
		self.simLengthUnits = jsonMdDict.get('simLengthUnits','')
		self.runTime = jsonMdDict.get('runTime','')
		self.reports = jsonDict.get('reports', [])
		self.studyNames = jsonDict.get('studyNames', [])
		self.name = name
		# TODO: Support study types that aren't Gridlab!!!
		self.studies = [studies.gridlabd.GridlabStudy(studyName, self.name, store.getMetadata('Study', self.name + '---' + studyName), store.get('Study', self.name + '---' + studyName)) for studyName in self.studyNames]

	def generateReportHtml(self):
		# Iterate over reports and collect what we need: 
		reportList = []
		for report in self.reports:
			# call the relevant reporting function by name.
			reportModule = getattr(reports, report['reportType'])
			reportList.append(reportModule.outputHtml(self, report))
		return reportList

	def run(self):
		# NOTE! We are running studies serially. We use lower levels of RAM/CPU, potentially saving time if swapping were to occur.
		self.status = 'running'
		startTime = dt.datetime.now()
		for study in self.studies:
			try:
				study.run()
			except Exception:
				self.status = 'ERROR'
		if self.status not in ['terminated','ERROR']:
			endTime = dt.datetime.now()
			self.runTime = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
			self.status = 'postRun'

	def terminate(self):
		# Get all the pids.
		pids = []
		studiesDir = 'analyses/' + analysisName + '/studies/'
		for studyName in os.listdir(studiesDir):
			studyFiles = os.listdir(studiesDir + studyName)
			if 'PID.txt' in studyFiles:
				with open(studiesDir + studyName + '/PID.txt','r') as pidFile: pids.append(int(pidFile.read()))
				os.remove(studiesDir + studyName + '/PID.txt')
		try:
			for pid in pids: os.kill(pid, 15)
		except:
			print 'We could not kill some PIDs. They may have already completed normally.'
		# Update that analysis status.
		md = getMetadata(analysisName)
		md['status'] = 'terminated'
		putMetadata(analysisName, md)
		return

	def toJson(self):
		return {'reports':self.reports, 'studyNames':self.studyNames}

	def mdToJson(self):
		return {'name':self.name, 'status':self.status, 'sourceFeeder':self.sourceFeeder, 'climate':self.climate, 'created':self.created, 'simStartDate':self.simStartDate, 'simLength':self.simLength, 'simLengthUnits':self.simLengthUnits, 'runTime':self.runTime}

if __name__ == '__main__':
	pass

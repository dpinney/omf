#!/usr/bin/env python
# encoding: utf-8

# This is a library to manage analysis objects.
# Note that it doesn't care about performance and will happily lock up any thread its methods are called in.
# So spawn some worker threads to do this stuff.

import os
import shutil
import datetime as dt
import feeder
import subprocess
import copy
import json
import studies
import reports

def listAll():
	if 'analyses' not in os.listdir('.'):
		os.mkdir('analyses')
	return os.listdir('analyses')

def getMetadata(analysisName):
	try:
		with open('analyses/' + analysisName + '/metadata.json','r') as mdFile:
			md = json.load(mdFile)
			md['name'] = str(analysisName)
			return md
	except:
		# The file didn't exist, i.e. the database is corrupt.
		return {'name':str(analysisName)}

def putMetadata(analysisName, metadataDict):
	try:
		with open('analyses/' + analysisName + '/metadata.json','w') as mdFile:
			json.dump(metadataDict, mdFile)
		return True
	except:
		# The file didn't exist, i.e. the database is corrupt.
		return False

def delete(analysisName):
	allAnalyses = listAll()
	if analysisName in allAnalyses:
		shutil.rmtree('analyses/' + analysisName)
		print 'Success. Analysis deleted.'
	else:
		print 'Deletion failure. Analysis does not exist.'

def create(analysisName, simLength, simLengthUnits, simStartDate, studyList, reportList):
	# make the analysis folder structure:
	os.mkdir('analyses/' + analysisName)
	os.mkdir('analyses/' + analysisName + '/studies')
	os.mkdir('analyses/' + analysisName + '/reports')
	for studyConf in studyList:
		studyModule = getattr(studies, studyConf['studyType'])
		studyModule.create(analysisName, simLength, simLengthUnits, simStartDate, studyConf)
	for report in reportList:
		with open('analyses/' + analysisName + '/reports/' + report['reportType'] + '.json','w') as mdFile:
			mdFile.write(str(report))
	# write a file with the current status (preRun, running or postRun), source feeder and climate.
	def uniqJoin(inList, key):
		theSet = set([x[key] for x in inList if key in x])
		return ', '.join(theSet)
	metadata = {'status':'preRun',
				'sourceFeeder':uniqJoin(studyList,'feederName'),
				'climate':uniqJoin(studyList,'tmy2name'),
				'created':str(dt.datetime.now()),
				'simStartDate':simStartDate,
				'simLength':simLength,
				'simLengthUnits':simLengthUnits }
	putMetadata(analysisName, metadata)
	print 'Success. Analysis created.'

def run(analysisName):
	studyNames = os.listdir('analyses/' + analysisName + '/studies/')
	# NOTE! We are running studies serially. We use lower levels of RAM/CPU, potentially saving time if swapping were to occur.
	# Update status to running.
	md = getMetadata(analysisName)
	md['status'] = 'running'
	putMetadata(analysisName, md)
	startTime = dt.datetime.now()
	for studyName in studyNames:
		# If we've been terminated, don't run any more studies.
		if md['status'] == 'terminated': return False
		with open('analyses/' + analysisName + '/studies/' + studyName + '/metadata.json') as studyMd:
			studyType = json.load(studyMd)['studyType']
		studyModule = getattr(studies, studyType)
		studyModule.run(analysisName, studyName)
	# Update status to postRun and include running time IF WE DIDN'T TERMINATE.
	md = getMetadata(analysisName)
	if md['status'] != 'terminated':
		endTime = dt.datetime.now()
		md['runTime'] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
		md['status'] = 'postRun'
		putMetadata(analysisName, md)

def terminate(analysisName):
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

def generateReportHtml(analysisName):
	# Get some variables.
	reportFiles = os.listdir('analyses/' + analysisName + '/reports/')
	reportList = []
	# Iterate over reports and collect what we need: 
	for report in reportFiles:
		# call the relevant reporting function by name.
		reportModule = getattr(reports, report.replace('.json',''))
		reportList.append(reportModule.outputHtml(analysisName))
	return reportList

#WARNING: TIME ESTIMATES TAKE ABOUT A MINUTE
#BIGGER WARNING: THIS DOESN'T WORK AT THE MOMENT
def runtimeEstimate(anaSpec):
	# if we're running less than 2 days then fahgeddaboudit.
	if anaSpec['simLengthUnits'] == 'minutes' \
	or (anaSpec['simLengthUnits'] == 'hours' and int(anaSpec['simLength']) < 48) \
	or (anaSpec['simLengthUnits'] == 'days' and int(anaSpec['simLength']) < 2):
		return 'minutes';
	# do a test for x hours.
	def testHours(anaSpec, hours):
		anaSpecTest = copy.deepcopy(anaSpec)
		anaSpecTest['simLengthUnits'] = 'hours'
		anaSpecTest['simLength'] = hours
		anaSpecTest['analysisName'] = anaSpec['analysisName'] + str(hours) + 'HourTest'
		create(anaSpecTest)
		run(anaSpecTest['analysisName'])
		anaSpecTestMd = getMetadata(anaSpecTest['analysisName'])
		delete(anaSpecTest['analysisName'])
		return float(anaSpecTestMd['runTime'])
	# how long does each hour of simulation take? Use hoursToAvg to set the length we'll run for interpolation purposes.
	hoursToAvg = 10
	secondsPerHour = (testHours(anaSpec, hoursToAvg) - testHours(anaSpec, 1))/(hoursToAvg-1)
	# how long was our simulation set for?
	if anaSpec['simLengthUnits'] == 'minutes':
		lengthInHours = float(anaSpec['simLength']) / 60
	elif anaSpec['simLengthUnits'] == 'hours':
		lengthInHours = float(anaSpec['simLength'])
	elif anaSpec['simLengthUnits'] == 'days':
		lengthInHours = float(anaSpec['simLength']) * 24
	# final estimate in seconds:
	return secondsPerHour * lengthInHours

def main():
	delete('chicken')
	create({'analysisName':'chicken', 'tmy2name':'AK-ANCHORAGE.tmy2', 'feederName':'13 Node Reference Feeder', 'simLength':'24', 'simLengthUnits':'minutes'})
	print getMetadata('chicken')
	run('chicken')
	#delete('chicken')

if __name__ == '__main__':
	main()
#!/usr/bin/env python
# encoding: utf-8

# This is a library to manage analysis objects.
# Note that it doesn't care about performance and will happily lock up any thread its methods are called in.
# So spawn some worker threads to do this stuff.

import os
import time
import shutil
import datetime as dt
import feeder
import subprocess
import copy
import studies
import reports

def listAll():
	if 'analyses' not in os.listdir('.'):
		os.mkdir('analyses')
	return os.listdir('analyses')

def getMetadata(analysisName):
	try:
		with open('analyses/' + analysisName + '/metadata.txt','r') as mdFile:
			mdString = mdFile.readlines()[0]
		return eval(mdString)
	except:
		# The file didn't exist, i.e. the database is corrupt.
		return {}

def putMetadata(analysisName, metadataDict):
	mdFile = open('analyses/' + analysisName + '/metadata.txt','w')
	mdFile.writelines(str(metadataDict))
	mdFile.close()
	return 'Sucess. Metadata updated.'

def delete(analysisName):
	allAnalyses = listAll()
	if analysisName in allAnalyses:
		shutil.rmtree('analyses/' + analysisName)
		print 'Success. Analysis deleted.'
	else:
		print 'Deletion failure. Analysis does not exist.'

def createAnalysis(analysisName, simLength, simLengthUnits, simStartDate, studies, reports):
	# make the analysis folder structure:
	os.mkdir('analyses/' + analysisName)
	os.mkdir('analyses/' + analysisName + '/studies')
	os.mkdir('analyses/' + analysisName + '/reports')
	for study in studies:
		studyFolder = 'analyses/' + analysisName + '/studies/' + study['studyName']
		# make the study folder:
		os.mkdir(studyFolder)
		# copy over the feeder files:
		feederFiles = os.listdir('feeders/' + study['feederName'])
		for fileName in feederFiles:
			shutil.copyfile('feeders/' + study['feederName'] + '/' + fileName, studyFolder + '/' + fileName)
		# Attach recorders:
		tree = feeder.parse(studyFolder + '/main.glm')
		feeder.attachRecorders(tree, 'Regulator', 'object', 'regulator')
		feeder.attachRecorders(tree, 'Capacitor', 'object', 'capacitor')
		feeder.attachRecorders(tree, 'Inverter', 'object', 'inverter')
		feeder.attachRecorders(tree, 'Windmill', 'object', 'windturb_dg')
		feeder.attachRecorders(tree, 'CollectorVoltage', None, None)
		feeder.attachRecorders(tree, 'Climate', 'object', 'climate')
		feeder.attachRecorders(tree, 'OverheadLosses', None, None)
		feeder.attachRecorders(tree, 'UndergroundLosses', None, None)
		feeder.attachRecorders(tree, 'TriplexLosses', None, None)
		feeder.attachRecorders(tree, 'TransformerLosses', None, None)
		feeder.groupSwingKids(tree)
		# Modify the glm with time variables:
		feeder.adjustTime(tree=tree, simLength=simLength, simLengthUnits=str(simLengthUnits), simStartDate=simStartDate)
		# write the glm:
		outString = feeder.write(tree)
		with open(studyFolder + '/main.glm','w') as glmFile:
			glmFile.write(outString)
		# copy over tmy2 and replace the dummy climate.tmy2.
		shutil.copyfile('tmy2s/' + study['tmy2name'], studyFolder + '/climate.tmy2')
		# add the metadata:
		metadata = {'name':str(study['studyName']), 'sourceFeeder':str(study['feederName']), 'climate':str(study['tmy2name'])}
		with open(studyFolder + '/metadata.txt','w') as mdFile:
			mdFile.write(str(metadata))
	for report in reports:
		with open('analyses/' + analysisName + '/reports/' + report['reportType'] + '.txt','w') as mdFile:
			mdFile.write(str(report))
	# write a file with the current status (preRun, running or postRun), source feeder and climate.
	def uniqJoin(inList, key):
		return ', '.join(set([x[key] for x in inList]))
	metadata = {'name':str(analysisName), 'status':'preRun', 'sourceFeeder':str(uniqJoin(studies,'feederName')), 'climate':str(uniqJoin(studies,'tmy2name')), 'created':str(dt.datetime.now()), 'simStartDate':str(simStartDate), 'simLength':simLength, 'simLengthUnits':str(simLengthUnits)}
	with open('analyses/' + analysisName + '/metadata.txt','w') as mdFile:
		mdFile.write(str(metadata))
	print 'Success. Analysis created.'

def run(analysisName):
	studyNames = os.listdir('analyses/' + analysisName + '/studies/')
	# NOTE! We are running studies serially. We use lower levels of RAM/CPU, potentially saving time if swapping were to occur.
	# Update status to running.
	metadata = getMetadata(analysisName)
	metadata['status'] = 'running'
	putMetadata(analysisName, metadata)
	startTime = dt.datetime.now()
	for study in studyNames:
		studyDir = 'analyses/' + analysisName + '/studies/' + study
		# Setup: pull in metadata before each study:
		metadata = getMetadata(analysisName)
		# HACK: if we've been terminated, don't run any more studies.
		if metadata['status'] == 'terminated':
			return False
		# RUN GRIDLABD (EXPENSIVE!)
		stdout = open(studyDir + '/stdout.txt','w')
		stderr = open(studyDir + '/stderr.txt','w')
		# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		proc = subprocess.Popen(['gridlabd','-w','main.glm'], cwd=studyDir, stdout=stdout, stderr=stderr)
		# Update PID.
		metadata['PID'] = proc.pid
		putMetadata(analysisName, metadata)
		proc.wait()
		stdout.close()
		stderr.close()
	# Update status to postRun and include running time IF WE DIDN'T TERMINATE.
	metadata = getMetadata(analysisName)
	if metadata['status'] != 'terminated':
		endTime = dt.datetime.now()
		metadata['runTime'] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
		metadata['status'] = 'postRun'
		putMetadata(analysisName, metadata)

def terminate(analysisName):
	md = getMetadata(analysisName)
	try:
		os.kill(int(md['PID']), 15)
	except:
		print 'We could not kill PID ' + str(md['PID']) + '. It may already have completed normally.'
	md['status'] = 'terminated'
	putMetadata(analysisName, md)

def generateReportHtml(analysisName):
	# Get some variables.
	reportFiles = os.listdir('analyses/' + analysisName + '/reports/')
	reportList = []
	# Iterate over reports and collect what we need: 
	for report in reportFiles:
		# call the relevant reporting function by name.
		reportModule = getattr(reports, report.replace('.txt',''))
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
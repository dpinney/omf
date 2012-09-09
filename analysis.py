#!/usr/bin/env python
# encoding: utf-8

# This is a library to manage analysis objects.
# Note that it doesn't care about performance and will happily lock up any thread its methods are called in. So spawn some worker threads to do this stuff.

import os
import time
import shutil
import datetime as dt
import treeParser as tp
import subprocess
import copy

def listAll():
	return os.listdir('static/analyses')

def getMetadata(analysisName):
	mdFile = open('static/analyses/' + analysisName + '/metadata.txt','r')
	mdString = mdFile.readlines()[0]
	mdFile.close()
	return eval(mdString)

def putMetadata(analysisName, metadataDict):
	mdFile = open('static/analyses/' + analysisName + '/metadata.txt','w')
	mdFile.writelines(str(metadataDict))
	mdFile.close()
	return 'Sucess. Metadata updated.'

def delete(analysisName):
	allAnalyses = listAll()
	if analysisName in allAnalyses:
		shutil.rmtree('static/analyses/' + analysisName)
		print 'Success. Analysis deleted.'
	else:
		print 'Deletion failure. Analysis does not exist.'

def createAnalysis(analysisName, simLength, simLengthUnits, studies, reports):
	# make the analysis folder structure:
	os.mkdir('static/analyses/' + analysisName)
	os.mkdir('static/analyses/' + analysisName + '/studies')	
	os.mkdir('static/analyses/' + analysisName + '/reports')	
	for study in studies:
		studyFolder = 'static/analyses/' + analysisName + '/studies/' + study['studyName']
		# make the study folder:
		os.mkdir(studyFolder)
		# copy over the feeder files:
		feederFiles = os.listdir('feeders/' + study['feederName'])
		for fileName in feederFiles:
			shutil.copyfile('feeders/' + study['feederName'] + '/' + fileName, studyFolder + '/' + fileName)
		# Attach recorders:
		tree = tp.parse(studyFolder + '/main.glm')
		tp.attachRecorders(tree, 'Regulator', 'regulator')
		tp.attachRecorders(tree, 'Capacitor', 'capacitor')
		tp.attachRecorders(tree, 'Voltage', 'triplex_meter')		
		# Modify the glm with time variables:
		tp.adjustTime(tree=tree, simLength=simLength, simLengthUnits=simLengthUnits)
		# write the glm:
		outString = tp.write(tree)
		with open(studyFolder + '/main.glm','w') as glmFile:
			glmFile.write(outString)
		# copy over tmy2 and replace the dummy climate.tmy2.
		shutil.copyfile('tmy2s/' + study['tmy2name'], studyFolder + '/climate.tmy2')
		# add the metadata:
		metadata = {'name':study['studyName'], 'sourceFeeder':study['feederName'], 'climate':study['tmy2name']}
		with open(studyFolder + '/metadata.txt','w') as mdFile:
			mdFile.write(str(metadata))
	for report in reports:
		with open('static/analyses/' + analysisName + '/reports/' + report['reportType'] + '.txt','w') as mdFile:
			mdFile.write(str({'reportType':report['reportType']}))
	# write a file with the current status (preRun, running or postRun), source feeder and climate.
	def uniqJoin(inList, key):
		return ', '.join(set([x[key] for x in inList]))
	metadata = {'name':analysisName, 'status':'preRun', 'sourceFeeder':uniqJoin(studies,'feederName'), 'climate':uniqJoin(studies,'tmy2name'), 'created':str(dt.datetime.now())}
	with open('static/analyses/' + analysisName + '/metadata.txt','w') as mdFile:
		mdFile.write(str(metadata))
	print 'Success. Analysis created.'

def run(analysisName):
	studyNames = os.listdir('static/analyses/' + analysisName + '/studies/')
	# NOTE! We are running studies serially. We save RAM and lose time.
	# Update status to running.
	metadata = getMetadata(analysisName)
	metadata['status'] = 'running'
	putMetadata(analysisName, metadata)
	startTime = dt.datetime.now()
	for study in studyNames:
		studyDir = 'static/analyses/' + analysisName + '/studies/' + study
		# Setup: pull in metadata before each study:
		metadata = getMetadata(analysisName)
		# HACK: if we've been terminated, don't run any more studies.
		if metadata['status'] == 'terminated':
			return False
		# RUN GRIDLABD (EXPENSIVE!)
		stdout = open(studyDir + '/stdout.txt','w')
		stderr = open(os.devnull,'w')
		# TODO: turn standerr back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		#stderr = open('static/analyses/' + analysisName + '/' + study + '/stderr.txt','w')
		proc = subprocess.Popen(['gridlabd','main.glm'], cwd=studyDir, stdout=stdout, stderr=stderr)
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
		metadata['runTime'] = (endTime - startTime).total_seconds()
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

#WARNING: TIME ESTIMATES TAKE ABOUT A MINUTE 
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
	#create(analysisName='chicken',tmy2name='AK-ANCHORAGE.tmy2', feederName='Simple Market System', simLength='24')
	create({'analysisName':'chicken', 'tmy2name':'AK-ANCHORAGE.tmy2', 'feederName':'13 Node Reference Feeder', 'simLength':'24', 'simLengthUnits':'minutes'})
	print getMetadata('chicken')
	run('chicken')
	#delete('chicken')

if __name__ == '__main__':
	main()
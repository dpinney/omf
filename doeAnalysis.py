#!/usr/bin/env python
# encoding: utf-8

# This is a library to manage analysis objects.
# Note that it doesn't care about performance and will happily lock up any thread its methods are called in. So spawn some worker threads to do this stuff.

import os
import time
import shutil
import doeGrapher
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

def create(formDict):
	analysisName = formDict['analysisName']
	tmy2name = formDict['tmy2name']
	feederName = formDict['feederName']
	simLength = int(formDict['simLength'])
	simLengthUnits = formDict['simLengthUnits']
	# TODO: REWRITE THIS!
	allAnalyses = listAll()
	if analysisName in allAnalyses:
		print 'Creation failure. Analysis already exists.'
	else:
		# make the analysis folder:
		os.mkdir('static/analyses/' + analysisName)
		# copy over the feeder files:
		feederFiles = os.listdir('feeders/' + feederName)
		for fileName in feederFiles:
			shutil.copyfile('feeders/' + feederName + '/' + fileName, 'static/analyses/' + analysisName + '/' + fileName)
		# Modify the glm with time variables:
		tree = tp.parse('static/analyses/' + analysisName + '/main.glm')
		tp.adjustTime(tree=tree, simLength=simLength, simLengthUnits=simLengthUnits)
		# write the glm:
		outString = tp.write(tree)
		glmFile = open('static/analyses/' + analysisName + '/main.glm','w')
		glmFile.write(outString)
		glmFile.close()
		# copy over tmy2 and replace the climate.tmy2.
		shutil.copyfile('tmy2s/' + tmy2name, 'static/analyses/' + analysisName + '/climate.tmy2')
		# write a file with the current status (preRun, running or postRun), source feeder and climate.
		metadata = {'name':analysisName, 'status':'preRun', 'sourceFeeder':feederName, 'climate': tmy2name, 'created':str(dt.datetime.now())}
		mdFile = open('static/analyses/' + analysisName + '/metadata.txt','w')
		mdFile.writelines(str(metadata))
		mdFile.close()
		# TODO: adjust running time. Attach recorders?
		print 'Success. Analysis created.'

def run(analysisName):
	allAnalyses = listAll()
	if analysisName in allAnalyses:
		# Update status to running.
		metadata = getMetadata(analysisName)
		metadata['status'] = 'running'
		putMetadata(analysisName, metadata)
		# RUN GRIDLABD (EXPENSIVE!)
		startTime = dt.datetime.now()
		stdout = open('static/analyses/' + analysisName + '/stdout.txt','w')
		stderr = open(os.devnull,'w')
		# TODO: turn standerr back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		#stderr = open('static/analyses/' + analysisName + '/stderr.txt','w')
		proc = subprocess.Popen(['gridlabd','main.glm'], cwd='static/analyses/' + analysisName, stdout=stdout, stderr=stderr)
		# Update PID.
		metadata = getMetadata(analysisName)
		metadata['PID'] = proc.pid
		putMetadata(analysisName, metadata)
		proc.wait()
		stdout.close()
		stderr.close()
		endTime = dt.datetime.now()
		# GRAPH IT (KINDA EXPENSIVE!)
		try:
			doeGrapher.buildFromDir('static/analyses/' + analysisName)
		except:
			print 'Data got messed up somewhere. Try running again.'
		# Update status to postRun and include running time.
		metadata['runTime'] = (endTime - startTime).total_seconds()
		metadata['status'] = 'postRun'
		putMetadata(analysisName, metadata)
	else:
		print 'Run failure. Analysis does not exist.'

def terminate(analysisName):
	md = getMetadata(analysisName)
	try:
		os.kill(int(md['PID']), 15)
	except:
		print 'We could not kill PID ' + str(md['PID']) + '. It may already have completed normally.'
	md['status'] = 'preRun'
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
#!/usr/bin/env python

if __name__ == '__main__':
	# Setup for tests.
	import os, sys
	os.chdir('./../..')
	sys.path.append(os.getcwd())

import sys, struct, subprocess, os, platform, re, feeder, datetime, shutil, traceback, math

def run(studyObject):
	# Choose our platform:
	thisFile = os.path.realpath(__file__)
	solverRoot = os.path.split(thisFile)[0]
	enviro = os.environ
	if sys.platform == 'win32' or sys.platform == 'cygwin':
		if platform.machine().endswith('64'):
			binary = solverRoot + "\\win64\\gridlabd.exe"
			enviro['GRIDLABD'] = solverRoot + "\\win64"
			enviro['GLPATH'] = solverRoot + "\\win64\\"
		else:
			binary = solverRoot + "\\win32\\gridlabd.exe"
			enviro['GRIDLABD'] = solverRoot + "\\win32"
			enviro['GLPATH'] = solverRoot + "\\win32\\"
	elif sys.platform == 'darwin':
		# Implement me, maybe.
		pass
	elif sys.platform == 'linux2':
		binary = solverRoot + "/linx64/gridlabd.bin"
		enviro['GRIDLABD'] = solverRoot + "/linx64"
		enviro['GLPATH'] = solverRoot + "/linx64"
		# Uncomment the following line if we ever get all the linux libraries bundled. Hard!
		# enviro['LD_LIBRARY_PATH'] = enviro['LD_LIBRARY_PATH'] + ':' + solverRoot + "/linx64"
	else:
		print "Platform not supported ", sys.platform
		return False
	try:
		# Create a running directory and fill it.
		studyPath = 'running/' + studyObject.analysisName + '---' + studyObject.name + '___' + str(datetime.datetime.now()).replace(':','_') + '/'
		os.makedirs(studyPath)
		# Write attachments and glm.
		attachments = studyObject.inputJson['attachments']
		for attach in attachments:
			with open (studyPath + attach,'w') as attachFile:
				attachFile.write(attachments[attach])
		glmString = feeder.sortedWrite(studyObject.inputJson['tree'])
		with open(studyPath + 'main.glm','w') as glmFile:
			glmFile.write(glmString)
		# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
		with open(studyPath + '/stdout.txt','w') as stdout, open(studyPath + '/stderr.txt','w') as stderr, open(studyPath + '/PID.txt','w') as pidFile:
			# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
			proc = subprocess.Popen([binary,'-w','main.glm'], cwd=studyPath, stdout=stdout, stderr=stderr, env=enviro)
			pidFile.write(str(proc.pid))
		returnCode = proc.wait()
		if returnCode == 15:
			# Stop running studies because we were terminated.
			shutil.rmtree(studyPath)
			return False
		# Build raw JSON output.
		rawOut = anaDataTree(studyPath, lambda x:True)
		with open(studyPath + '/stderr.txt','r') as stderrFile:
			rawOut['stderr'] = stderrFile.read().strip()
		with open(studyPath + '/stdout.txt','r') as stdoutFile:
			rawOut['stdout'] = stdoutFile.read().strip()
		rawOut['glmTree'] = feeder.parse(studyPath + '/main.glm')
		# Delete the folder and return.
		shutil.rmtree(studyPath)
		return rawOut
	except:
		traceback.print_exc()
		return False

def runInFilesystem(feederTree, attachments=[], keepFiles=False):
	''' Execute gridlab in the local filesystem. Return a nice dictionary of results. '''
	try:
		# Create a running directory and fill it.
		studyPath = 'running/' + str(datetime.datetime.now()).replace(':','_') + '/'
		os.makedirs(studyPath)
		# Need to zero out lat/lon data because it frequently breaks Gridlab.
		for key in feederTree:
			if 'latitude' in feederTree[key]: feederTree[key]['latitude'] = '0'
			if 'longitude' in feederTree[key]: feederTree[key]['longitude'] = '0'
		# Write attachments and glm.
		for attach in attachments:
			with open (studyPath + attach,'w') as attachFile:
				attachFile.write(attachments[attach])
		glmString = feeder.sortedWrite(feederTree)
		with open(studyPath + 'main.glm','w') as glmFile:
			glmFile.write(glmString)
		# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
		with open(studyPath + '/stdout.txt','w') as stdout, open(studyPath + '/stderr.txt','w') as stderr, open(studyPath + '/PID.txt','w') as pidFile:
			# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
			proc = subprocess.Popen(['gridlabd','-w','main.glm'], cwd=studyPath, stdout=stdout, stderr=stderr)
			pidFile.write(str(proc.pid))
		returnCode = proc.wait()
		# Build raw JSON output.
		rawOut = anaDataTree(studyPath, lambda x:True)
		with open(studyPath + '/stderr.txt','r') as stderrFile:
			rawOut['stderr'] = stderrFile.read().strip()
		with open(studyPath + '/stdout.txt','r') as stdoutFile:
			rawOut['stdout'] = stdoutFile.read().strip()
		# Delete the folder and return.
		if not keepFiles:
			# HACK: if we don't sleep 1 second, windows intermittantly fails to delete things and an exception is thrown.
			# Probably cus dropbox is monkeying around in these folders on my dev machine. Disabled for now since it works when dropbox is off.
			# time.sleep(1)
			shutil.rmtree(studyPath)
		return rawOut
	except:
		traceback.print_exc()
		return {}

def _strClean(x):
	# Helper function that translates csv values to reasonable floats (or header values to strings):
	if x == 'OPEN':
		return 1.0
	elif x == 'CLOSED':
		return 0.0
	# Look for strings of the type '+32.0+68.32d':
	elif x == '-1.#IND':
		return 0.0
	if x.endswith('d'):
		matches = re.findall('^([+-]?\d+\.?\d*e?[+-]?\d+)[+-](\d+\.?\d*e?[+-]?\d*)d$',x)
		if len(matches)==0:
			return 0.0
		else:
			floatConv = map(float, matches[0])
			squares = map(lambda x:x**2, floatConv)
			return math.sqrt(sum(squares))
	elif re.findall('^([+-]?\d+\.?\d*e?[+-]?\d*)$',x) != []:
		matches = re.findall('([+-]?\d+\.?\d*e?[+-]?\d*)',x)
		if len(matches)==0:
			return 0.0
		else:
			return float(matches[0])
	else:
		return x

def csvToArray(fileName):
	''' Take a Gridlab-export csv filename, return a list of timeseries vectors. Internal method. 
		testStringsThatPass = ['+954.877', '+2.18351e+006', '+7244.99+1.20333e-005d', '+7244.99+120d', '+3.76184','1','+7200+0d','']
	'''

	with open(fileName) as openfile:
		data = openfile.read()
	lines = data.splitlines()
	array = map(lambda x:x.split(','), lines)
	cleanArray = [map(_strClean, x) for x in array]
	# Magic number 8 is the number of header rows in each csv.
	arrayNoHeaders = cleanArray[8:]
	# Drop the timestamp column:
	return arrayNoHeaders

def _seriesTranspose(theArray):
	return {i[0]:list(i)[1:] for i in zip(*theArray)}

def anaDataTree(studyPath, fileNameTest):
	''' Take a study and put all its data into a nested object {fileName:{metricName:[...]}} '''

	data = {}
	csvFiles = os.listdir(studyPath)
	for cName in csvFiles:
		if fileNameTest(cName) and cName.endswith('.csv'):
			arr = csvToArray(studyPath + '/' + cName)
			data[cName] = _seriesTranspose(arr)
	return data

def _tests():
	# On the Python side, this test runs fine, but it gets fatal errors in gridlab because it is looking for a file called "climate.tmy2"
	import json
	# import storage, studies
	# store = storage.Filestore('data')
	# testStudy = studies.gridlabd.Gridlabd('NoSolar', 'zSolar Trio', store.getMetadata('Study','zSolar Trio---NoSolar'), store.get('Study','zSolar Trio---NoSolar'))
	with open("data\\Feeder\\public_Olin Barre.json") as feederFile:
		feederJson = json.load(feederFile)
	print "tree:", feederJson["tree"]
	print "attachments:", feederJson["attachments"]
	testStudy = runInFilesystem(feederJson["tree"], feederJson["attachments"])
	# print testStudy.name, 
	print dir(testStudy)
	# rawOut = run(testStudy)
	# print rawOut.keys()
	print "testStudy.keys():", testStudy.keys()
	print "testStudy['stdout']:", testStudy['stdout']
	print "testStudy['stderr']:", testStudy['stderr']

if __name__ == '__main__':
	_tests()

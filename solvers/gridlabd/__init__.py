#!/usr/bin/env python

if __name__ == '__main__':
	# Setup for tests.
	import os, sys
	os.chdir('./../..')
	sys.path.append(os.getcwd())

import sys, struct, subprocess, os, platform, re, feeder, datetime, shutil

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
	with open(studyPath + '/stdout.txt','w') as stdout, open(studyPath + '/stderr.txt','w') as stderr:
		# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		proc = subprocess.Popen([binary,'-w','main.glm'], cwd=studyPath, stdout=stdout, stderr=stderr, env=enviro)
		# Put PID.
		with open(studyPath + '/PID.txt','w') as pidFile:
			pidFile.write(str(proc.pid))
		returnCode = proc.wait()
		print '!!!!!!', returnCode
		if returnCode != 0:
			# Stop running studies, set status=terminated.
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

def csvToArray(fileName):
	''' Take a filename to a list of timeseries vectors. Internal method. '''
	def strClean(x):
		# Helper function that translates csv values to reasonable floats (or header values to strings):
		if x == 'OPEN':
			return 1.0
		elif x == 'CLOSED':
			return 0.0
		# Look for strings of the type '+32.0+68.32d':
		elif x == '-1.#IND':
			return 0.0
		elif re.findall('[+-]\d+.*[+-]\d+.*d',x) != []:
			embedNums = re.findall('-*\d+',x)
			floatConv = map(float, embedNums)
			squares = map(lambda x:x**2, floatConv)
			return math.sqrt(sum(squares))
		elif x[0] == '+':
			return float(x[1:])
		elif x[0] == '-':
			return float(x)
		elif x[0].isdigit() and x[-1].isdigit():
			return float(x)
		else:
			return x
	with open(fileName) as openfile:
		data = openfile.read()
	lines = data.splitlines()
	array = map(lambda x:x.split(','), lines)
	cleanArray = [map(strClean, x) for x in array]
	# Magic number 8 is the number of header rows in each csv.
	arrayNoHeaders = cleanArray[8:]
	# Drop the timestamp column:
	return arrayNoHeaders

def anaDataTree(studyPath, fileNameTest):
	''' Take a study and put all its data into a nested object {fileName:{metricName:[...]}} '''
	def seriesTranspose(theArray):
		return {i[0]:list(i)[1:] for i in zip(*theArray)}
	data = {}
	csvFiles = os.listdir(studyPath)
	for cName in csvFiles:
		if fileNameTest(cName) and cName.endswith('.csv'):
			arr = csvToArray(studyPath + '/' + cName)
			data[cName] = seriesTranspose(arr)
	return data

if __name__ == '__main__':
	import storage, studies
	store = storage.Filestore('data')
	testStudy = studies.gridlabd.GridlabStudy('NoSolar', 'zSolar Trio', store.getMetadata('Study','zSolar Trio---NoSolar'), store.get('Study','zSolar Trio---NoSolar'))
	print testStudy.name, dir(testStudy)
	rawOut = run(testStudy)
	print rawOut.keys()

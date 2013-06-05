#!/usr/bin/env python

import sys, struct, subprocess, os, platform, re

def run(analysisName, studyName):
	# Choose our platform:
	thisFile = os.path.realpath(__file__)
	solverRoot = os.path.split(thisFile)[0]
	# Get current environment variables:
	enviro = os.environ
	# print solverRoot
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
	# Path to glm etc.:
	studyPath = 'analyses/' + analysisName + '/studies/' + studyName
	
	# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
	with open(studyPath + '/stdout.txt','w') as stdout, open(studyPath + '/stderr.txt','w') as stderr:
		# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		proc = subprocess.Popen([binary,'-w','main.glm'], cwd=studyPath, stdout=stdout, stderr=stderr, env=enviro)
		# Put PID.
		with open(studyPath + '/PID.txt','w') as pidFile:
			pidFile.write(str(proc.pid))
		proc.wait()
		# Remove PID to indicate completion.
		try: 
			os.remove(studyPath + '/PID.txt')
		except:
			# Terminated, return false so analysis knows to not run any more studies.
			return False
	# Return raw JSON output.
	return anaDataTree(studyPath, lambda x:True)

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
	# os.chdir('../..')
	# run('zSolar Trio','NoSolar')
	# with open('analyses/zSolar Trio/studies/NoSolar/stdout.txt') as stdout:
	# 	print stdout.read()
	pass

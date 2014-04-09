''' Code for running Gridlab and getting results into pythonic data structures. '''

import sys, os, subprocess, platform, re, datetime, shutil, traceback, math, time
from os.path import join as pJoin

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(os.path.dirname(_myDir))
sys.path.append(_omfDir)

# OMF imports.
import feeder

def _getPlatform():
	''' Figure out what platform we're on and choose a suitable Gridlab binary. '''
	# TODO: work this into runInFilesystem.
	enviro = os.environ
	if sys.platform == 'win32' or sys.platform == 'cygwin':
		if platform.machine().endswith('64'):
			binary = _myDir + "\\win64\\gridlabd.exe"
			enviro['GRIDLABD'] = _myDir + "\\win64"
			enviro['GLPATH'] = _myDir + "\\win64\\"
		else:
			binary = _myDir + "\\win32\\gridlabd.exe"
			enviro['GRIDLABD'] = _myDir + "\\win32"
			enviro['GLPATH'] = _myDir + "\\win32\\"
	elif sys.platform == 'darwin':
		# Implement me, maybe.
		pass
	elif sys.platform == 'linux2':
		binary = _myDir + "/linx64/gridlabd.bin"
		enviro['GRIDLABD'] = _myDir + "/linx64"
		enviro['GLPATH'] = _myDir + "/linx64"
		# Uncomment the following line if we ever get all the linux libraries bundled. Hard!
		# enviro['LD_LIBRARY_PATH'] = enviro['LD_LIBRARY_PATH'] + ':' + solverRoot + "/linx64"
	else:
		print "Platform not supported ", sys.platform
		return False

def runInFilesystem(feederTree, attachments=[], keepFiles=False, workDir=None):
	''' Execute gridlab in the local filesystem. Return a nice dictionary of results. '''
	try:
		# Create a running directory and fill it, unless we've specified where we're running.
		if not workDir:
			workDir = pJoin('running',str(datetime.datetime.now()).replace(':','_'))
			os.makedirs(workDir)
		# Need to zero out lat/lon data because it frequently breaks Gridlab.
		for key in feederTree:
			if 'latitude' in feederTree[key]: feederTree[key]['latitude'] = '0'
			if 'longitude' in feederTree[key]: feederTree[key]['longitude'] = '0'
		# Write attachments and glm.
		for attach in attachments:
			with open (pJoin(workDir,attach),'w') as attachFile:
				attachFile.write(attachments[attach])
		glmString = feeder.sortedWrite(feederTree)
		with open(pJoin(workDir,'main.glm'),'w') as glmFile:
			glmFile.write(glmString)
		# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
		with open(pJoin(workDir,'stdout.txt'),'w') as stdout, open(pJoin(workDir,'stderr.txt'),'w') as stderr, open(pJoin(workDir,'PID.txt'),'w') as pidFile:
			# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
			proc = subprocess.Popen(['gridlabd','-w','main.glm'], cwd=workDir, stdout=stdout, stderr=stderr)
			pidFile.write(str(proc.pid))
		returnCode = proc.wait()
		# Build raw JSON output.
		rawOut = anaDataTree(workDir, lambda x:True)
		with open(pJoin(workDir,'stderr.txt'),'r') as stderrFile:
			rawOut['stderr'] = stderrFile.read().strip()
		with open(pJoin(workDir,'stdout.txt'),'r') as stdoutFile:
			rawOut['stdout'] = stdoutFile.read().strip()
		# Delete the folder and return.
		if not keepFiles and not workDir:
			# NOTE: if we've specify a working directory, don't just blow it away.
			# HACK: if we don't sleep 1 second, windows intermittantly fails to delete things and an exception is thrown.
			# Probably cus dropbox is monkeying around in these folders on my dev machine. Disabled for now since it works when dropbox is off.
			for attempt in range(5):
				try:
					shutil.rmtree(workDir)
					break
				except WindowsError:
					time.sleep(2)
		return rawOut
	except:
		traceback.print_exc()
		return {}

def _strClean(x):
	''' Helper function that translates csv values to reasonable floats (or header values to strings). '''
	# TODO: write tests for this crazy function.
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
	''' Take a Gridlab-export csv filename, return a list of timeseries vectors.
		testStringsThatPass = ['+954.877', '+2.18351e+006', '+7244.99+1.20333e-005d', '+7244.99+120d', '+3.76184','1','+7200+0d','']'''
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
	''' Transpose every matrix that's a value in a dictionary. Yikes. '''
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
	# TODO: On the Python side, this test runs fine, but it gets fatal errors in gridlab because it is looking for a file called "climate.tmy2"
	import json
	with open(pJoin(_omfDir,"data","Feeder","public","Olin Barre.json"),"r") as feederFile:
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

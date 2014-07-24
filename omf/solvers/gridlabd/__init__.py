''' Code for running Gridlab and getting results into pythonic data structures. '''

import sys, os, subprocess, platform, re, datetime, shutil, traceback, math, time, tempfile, json
from os.path import join as pJoin
from copy import deepcopy

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(os.path.dirname(_myDir))
sys.path.append(_omfDir)

# OMF imports.
import feeder

def _addGldToPath():
	''' Figure out what platform we're on and choose a suitable Gridlab binary.
	Returns full path to binary as result. '''
	# Do we have a version of GridlabD available?
	if 0 == subprocess.call(["gridlabd"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
		# There's a system-level install of Gridlab, so use it:
		return "gridlabd"
	else:
		# No system-level version of Gridlab available, so add ours to the path.
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
			return binary
		elif sys.platform == 'darwin':
			# Implement me, maybe.
			pass
		elif sys.platform == 'linux2':
			binary = _myDir + "/linx64/gridlabd.bin"
			enviro['GRIDLABD'] = _myDir + "/linx64"
			enviro['GLPATH'] = _myDir + "/linx64"
			# Uncomment the following line if we ever get all the linux libraries bundled. Hard!
			# enviro['LD_LIBRARY_PATH'] = enviro['LD_LIBRARY_PATH'] + ':' + solverRoot + "/linx64"
			return binary
		else:
			# Platform not supported, so just return the standard binary and pray it works:
			return "gridlabd"

def runInFilesystem(feederTree, attachments=[], keepFiles=False, workDir=None):
	''' Execute gridlab in the local filesystem. Return a nice dictionary of results. '''
	try:
		binaryName = "gridlabd"
		# Create a running directory and fill it, unless we've specified where we're running.
		if not workDir:
			workDir = tempfile.mkdtemp()
			print "gridlabD runInFilesystem with no specified workDir. Working in", workDir
		# Need to zero out lat/lon data on copy because it frequently breaks Gridlab.
		localTree = deepcopy(feederTree)
		for key in localTree.keys():
			try:
				del localTree[key]["latitude"]
				del localTree[key]["longitude"]
			except:
				pass # No lat lons.
		# Write attachments and glm.
		for attach in attachments:
			with open (pJoin(workDir,attach),'w') as attachFile:
				attachFile.write(attachments[attach])
		glmString = feeder.sortedWrite(localTree)
		glmName = "main." + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".glm"
		with open(pJoin(workDir, glmName),'w') as glmFile:
			glmFile.write(glmString)
		# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
		with open(pJoin(workDir,'stdout.txt'),'w') as stdout, open(pJoin(workDir,'stderr.txt'),'w') as stderr, open(pJoin(workDir,'PID.txt'),'w') as pidFile:
			# MAYBEFIX: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
			proc = subprocess.Popen([binaryName,'-w', glmName], cwd=workDir, stdout=stdout, stderr=stderr)
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
		with open(pJoin(workDir, "stderr.txt"), "a+") as stderrFile:
			traceback.print_exc(file = stderrFile)
		return {}

def _strClean(x):
	''' Helper function that translates csv values to reasonable floats (or header values to strings). '''
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
	''' Take a Gridlab-export csv filename, return a list of timeseries vectors.'''
	with open(fileName) as openfile:
		data = openfile.read()
	lines = data.splitlines()
	array = map(lambda x:x.split(','), lines)
	cleanArray = [map(_strClean, x) for x in array]
	# Magic number 8 is the number of header rows in each GridlabD csv.
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
	print "Full path to Gridlab executable we're using:", _addGldToPath()
	print "Testing string cleaning."
	strTestCases = [("+954.877", 954.877),
		("+2.18351e+006", 2183510.0),
		("+7244.99+1.20333e-005d", 7244.99),
		# ("+7244.99+120d", 7245.98372204), # Fails due to float rounding but should pass.
		("+3.76184", 3.76184),
		("1", 1.0),
		("-32.4", -32.4),
		("+7200+0d", 7200.0)]
	for (string, result) in strTestCases:
		assert _strClean(string) == result, "A _strClean operation failed on: " + string
	# Get a test feeder and test climate.
	print "Testing GridlabD solver."
	with open(pJoin(_omfDir,"data","Feeder","public","Simple Market System.json"),"r") as feederFile:
		feederJson = json.load(feederFile)
	with open(pJoin(_omfDir,"data","Climate","AL-HUNTSVILLE.tmy2"),"r") as climateFile:
		tmyStr = climateFile.read()
	# Add climate in.
	feederJson["attachments"]["climate.tmy2"] = tmyStr
	testStudy = runInFilesystem(feederJson["tree"], feederJson["attachments"])
	assert testStudy != {}, "Gridlab run failed and we got blank output."
	print "GridlabD standard error:", testStudy['stderr']
	print "GridlabD standard output:", testStudy['stdout']

if __name__ == '__main__':
	_tests()

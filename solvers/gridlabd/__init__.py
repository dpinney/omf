#!/usr/bin/env python

import sys, struct, subprocess, os

def run(analysisName, studyName):
	# Choose our platform:
	if sys.platform == 'win32' or sys.platform == 'cygwin':
		if 8*struct.calcsize("P") == 64:
			binary = "solvers/gridlabd/win64/gridlabd.exe"
		else:
			binary = "solvers/gridlabd/win32/gridlabd.exe"
	elif sys.platform == 'darwin':
		# Implement me, maybe.
		pass
	elif sys.platform == 'linux2':
		binary = "solvers/gridlabd/linx64/gridlabd"
	else:
		print "Platform not supported ", sys.platform
	# Path to glm etc.:
	studyPath = 'analyses/' + analysisName + '/studies/' + studyName
	# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
	with open(studyPath + '/stdout.txt','w') as stdout, open(studyPath + '/stderr.txt','w') as stderr:
		# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		proc = subprocess.Popen(['gridlabd','-w','main.glm'], cwd=studyPath, stdout=stdout, stderr=stderr)
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
	# Return true to indicate success.
	return True

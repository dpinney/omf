#!/usr/bin/env python

import sys, struct, subprocess, os, platform

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
	# Return true to indicate success.
	return True

def main():
	# os.chdir('../..')
	# run('zSolar Trio','NoSolar')
	# with open('analyses/zSolar Trio/studies/NoSolar/stdout.txt') as stdout:
	# 	print stdout.read()
	pass

if __name__ == '__main__':
	main()

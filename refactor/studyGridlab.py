#!/usr/bin/env python

import tempfile
import datetime
import os
import subprocess
import datetime as dt
import results
import grid
import utility


class StudyGridlab:
	# metadata
	name = None
	status = 'preRun'
	pid = None
	runTime = None
	grid = None
	# not metadata
	results = None
	includeFiles = None

	def __init__(self, name, grid, includeFiles=None):
		#TODO: add an option to just pull in a full directory?
		self.name = name
		self.grid = grid
		self.includeFiles = includeFiles

	def run(self):
		# Set up a temporary directory to work in.
		tempDir = tempfile.gettempdir() + '\\' + self.name + str(datetime.datetime.now()).replace('.','-').replace(':','-') + '\\'
		os.mkdir(tempDir)
		# write the files to disk.
		for x in self.includeFiles:
			with open(tempDir + x, 'w') as tempFile:
				tempFile.write(self.includeFiles[x])
		with open(tempDir + 'main.glm', 'w') as mainFile:
			mainFile.write(self.grid.toGlmString())
		# Update our status.
		self.status = 'running'
		# RUN GRIDLABD (EXPENSIVE!)
		startTime = dt.datetime.now()
		with open(tempDir + 'stdout.txt', 'w') as stdout, open(os.devnull, 'w') as stderr:
			# TODO: turn standerr back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
			proc = subprocess.Popen(['gridlabd','main.glm'], cwd=tempDir, stdout=stdout, stderr=stderr)
			# Update PID.
			self.pid = proc.pid
			proc.wait()
		endTime = dt.datetime.now()
		# Pull in the results (kinda expensive?)
		self.results = results.Results(directory=tempDir)
		# Update status to postRun and include running time.
		self.runTime = (endTime - startTime).total_seconds()
		self.status = 'postRun'

def main():
	print 'Testing here.'
	#direc = '../feeders/13 Node Reference Feeder/'
	direc = '../feeders/Simple Market System/'
	includes = {}
	for x in os.listdir(direc):
		if (x.endswith('.glm') and x != 'main.glm') or x.endswith('.tmy2') or x.endswith('.player'):
			with open(direc + x, 'r') as openFile:
				includes[x] = openFile.read()
	with open(direc+'main.glm', 'r') as mainFile:
		glmString = mainFile.read()
	print includes.keys()
	test = StudyGridlab('chicken', grid.Grid(glmString), includes)
	print test
	test.run()
	print test.results.recorders.keys()
	utility.printNestDicts(test.results.recorders)
	return test

if __name__ == '__main__':
	main()
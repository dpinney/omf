#!/usr/bin/env python

import os
import feeder
import shutil
import subprocess
import json

def create(analysisName, simLength, simLengthUnits, simStartDate, studyConfig):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyConfig['studyName']
	# make the study folder:
	os.mkdir(studyPath)
	# copy over the feeder files:
	feederPath = 'feeders/' + studyConfig['feederName']
	for fileName in  os.listdir(feederPath):
		shutil.copyfile(feederPath + '/' + fileName, studyPath + '/' + fileName)
	# Attach recorders:
	tree = feeder.parse(studyPath + '/main.glm')
	feeder.attachRecorders(tree, 'Regulator', 'object', 'regulator')
	feeder.attachRecorders(tree, 'Capacitor', 'object', 'capacitor')
	feeder.attachRecorders(tree, 'Inverter', 'object', 'inverter')
	feeder.attachRecorders(tree, 'Windmill', 'object', 'windturb_dg')
	feeder.attachRecorders(tree, 'CollectorVoltage', None, None)
	feeder.attachRecorders(tree, 'Climate', 'object', 'climate')
	feeder.attachRecorders(tree, 'OverheadLosses', None, None)
	feeder.attachRecorders(tree, 'UndergroundLosses', None, None)
	feeder.attachRecorders(tree, 'TriplexLosses', None, None)
	feeder.attachRecorders(tree, 'TransformerLosses', None, None)
	feeder.groupSwingKids(tree)
	# Modify the glm with time variables:
	feeder.adjustTime(tree=tree, simLength=simLength, simLengthUnits=str(simLengthUnits), simStartDate=simStartDate)
	# write the glm:
	with open(studyPath + '/main.glm','w') as glmFile:
		glmFile.write(feeder.write(tree))
	# copy over tmy2 and replace the dummy climate.tmy2.
	shutil.copyfile('tmy2s/' + studyConfig['tmy2name'], studyPath + '/climate.tmy2')
	# add the metadata:
	metadata = {'sourceFeeder':str(studyConfig['feederName']), 'climate':str(studyConfig['tmy2name']), 'studyType':str(studyConfig['studyType'])}
	with open(studyPath + '/metadata.txt','w') as mdFile:
		mdFile.write(str(metadata))
	return

# WARNING! Run does not care about performance and will happily run for a long, long time. Spawn a thread or process for this nonsense.
def run(analysisName, studyName):
	studyDir = 'analyses/' + analysisName + '/studies/' + studyName
	# RUN GRIDLABD (EXPENSIVE!)
	with open(studyDir + '/stdout.txt','w') as stdout, open(studyDir + '/stderr.txt','w') as stderr:
		# TODO: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
		proc = subprocess.Popen(['gridlabd','-w','main.glm'], cwd=studyDir, stdout=stdout, stderr=stderr)
		# Put PID.
		with open(studyDir + '/PID.txt','w') as pidFile:
			pidFile.write(str(proc.pid))
		proc.wait()
		# Remove PID to indicate completion.
		try: 
			os.remove(studyDir + '/PID.txt')
		except:
			# Terminated, return false so analysis knows to not run any more studies.
			return False
	# Study run succesfully, indicate in return.
	return True
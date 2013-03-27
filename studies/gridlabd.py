#!/usr/bin/env python

import os

def create(analysisName, studyName):
	# for study in studies:
	# 	studyFolder = 'analyses/' + analysisName + '/studies/' + study['studyName']
	# 	# make the study folder:
	# 	os.mkdir(studyFolder)
	# 	# copy over the feeder files:
	# 	feederFiles = os.listdir('feeders/' + study['feederName'])
	# 	for fileName in feederFiles:
	# 		shutil.copyfile('feeders/' + study['feederName'] + '/' + fileName, studyFolder + '/' + fileName)
	# 	# Attach recorders:
	# 	tree = feeder.parse(studyFolder + '/main.glm')
	# 	feeder.attachRecorders(tree, 'Regulator', 'object', 'regulator')
	# 	feeder.attachRecorders(tree, 'Capacitor', 'object', 'capacitor')
	# 	feeder.attachRecorders(tree, 'Inverter', 'object', 'inverter')
	# 	feeder.attachRecorders(tree, 'Windmill', 'object', 'windturb_dg')
	# 	feeder.attachRecorders(tree, 'CollectorVoltage', None, None)
	# 	feeder.attachRecorders(tree, 'Climate', 'object', 'climate')
	# 	feeder.attachRecorders(tree, 'OverheadLosses', None, None)
	# 	feeder.attachRecorders(tree, 'UndergroundLosses', None, None)
	# 	feeder.attachRecorders(tree, 'TriplexLosses', None, None)
	# 	feeder.attachRecorders(tree, 'TransformerLosses', None, None)
	# 	feeder.groupSwingKids(tree)
	# 	# Modify the glm with time variables:
	# 	feeder.adjustTime(tree=tree, simLength=simLength, simLengthUnits=str(simLengthUnits), simStartDate=simStartDate)
	# 	# write the glm:
	# 	outString = feeder.write(tree)
	# 	with open(studyFolder + '/main.glm','w') as glmFile:
	# 		glmFile.write(outString)
	# 	# copy over tmy2 and replace the dummy climate.tmy2.
	# 	shutil.copyfile('tmy2s/' + study['tmy2name'], studyFolder + '/climate.tmy2')
	# 	# add the metadata:
	# 	metadata = {'name':str(study['studyName']), 'sourceFeeder':str(study['feederName']), 'climate':str(study['tmy2name'])}
	# 	with open(studyFolder + '/metadata.txt','w') as mdFile:
	# 		mdFile.write(str(metadata))
	pass

def run(analysisName, studyName):
	pass
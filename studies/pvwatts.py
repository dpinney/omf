#!/usr/bin/env python

import json
import os
import shutil

with open('./studies/pvwatts.html','r') as configFile: configHtmlTemplate = configFile.read()

def create(analysisName, simLength, simLengthUnits, simStartDate, studyConfig):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyConfig['studyName']
	# make the study folder:
	os.mkdir(studyPath)
	# copy over tmy2 and replace the dummy climate.tmy2.
	shutil.copyfile('tmy2s/' + studyConfig['tmy2name'], studyPath + '/climate.tmy2')
	# add the metadata:
	md = {'climate':str(studyConfig['tmy2name']), 'studyType':str(studyConfig['studyType'])}
	with open(studyPath + '/metadata.json','w') as mdFile:
		json.dump(md, mdFile)
	return

def run(analysisName, studyName):
	pass
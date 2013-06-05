#!/usr/bin/env python

import os
import json

os.chdir('../data')

print os.listdir('.')

def jslurp(filePath):
	with open(filePath,'r') as openFile:
		return json.load(openFile)

analysisMds = {name.replace('.md.json',''):jslurp('Analysis/' + name) for name in os.listdir('Analysis') if name.endswith('.md.json')}

studyNames = [name for name in os.listdir('Study') if name.endswith('.md.json')]

print analysisMds

for studyName in studyNames:
	myAnaName = studyName.split('---')[0]
	with open('Study/' + studyName, 'r') as studyFile:
		metadata = json.load(studyFile)
		metadata['simStartDate'] = analysisMds[myAnaName]['simStartDate']
		metadata['simLength'] = analysisMds[myAnaName]['simLength']
		metadata['simLengthUnits'] = analysisMds[myAnaName]['simLengthUnits']
		print metadata
	with open('Study/' + studyName, 'w') as studyWriter:
		json.dump(metadata, studyWriter)
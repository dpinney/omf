#!/usr/bin/env python

''' Let's get that texas coop's feeder working in Gridlab. '''

# First, do the path nonsense to import omf libraries.
import os, sys, json
def popPath(path):
	return os.path.split(path)[0]
thisFile = os.path.realpath(__file__)
sys.path.append(popPath(popPath(popPath(thisFile))))
import feeder

# Pull in json, write GLM.
with open('Rector2413.json','r') as feedFile:
	allJson = json.load(feedFile)
	tree = allJson.get('tree',{})
	attachments = allJson.get('attachments',{})

glm = feeder.sortedWrite(tree)

with open('Rector2413.glm','w') as glmFile:
	glmFile.write(glm)

for key in attachments:
	with open(key, 'w') as attachFile:
		attachFile.write(attachments.get(key,''))
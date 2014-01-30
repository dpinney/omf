#!/usr/bin/env python

import os
import json

os.chdir('../../feeders/')
print 'Working dir:', os.getcwd()

allFeedDirs = os.listdir('.')

for feed in allFeedDirs:
	print 'Working on:', feed
	with open(feed + '/main.json','r') as mainJsonFile:
		feedObject = json.load(mainJsonFile)
		feedObject['attachments'] = {}
		files = os.listdir(feed)
		for fileName in files:
			if fileName not in ['main.json','main.glm']:
				print '\tAttaching', fileName
				with open(feed + '/' + fileName) as attachFile:
					feedObject['attachments'][fileName] = attachFile.read()
		with open(feed + '.json','w') as newJsonFile:
			json.dump(feedObject, newJsonFile, indent=4)
#!/usr/bin/env python

import json

with open('schedules.glm','r') as schedulesFile:
	schedString = schedulesFile.read()

testJson = {'tree':{},'magic':34,'scheds':[schedString,schedString],'testarray':[1,2,3,4,'pies']}

with open('out.json','w') as outFile:
	json.dump(testJson, outFile, indent=4)

with open('out.json','r') as inFile:
	backAgain = json.load(inFile)
	with open('schedules2.glm','w') as schedFile2:
		schedFile2.write(backAgain['scheds'][0])

#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import feeder as tp
import json

with open('main.json','r') as inFile:
	jsonBlob = json.load(inFile)
	tree = jsonBlob['tree']

print jsonBlob.keys()
print tree.keys()

outString = tp.sortedWrite(tree)

tp.dictToString(tree['7140'])

# The problem we were running into was the house thermal_integrity values were integers but needed to be strings. So the darn thing was saving wrong. Lesson learned!
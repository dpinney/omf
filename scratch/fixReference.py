#!/usr/bin/env python

''' take a PNNL reference feeder and clean up the object name:number convention.'''

import sys
sys.path.append('C:/Users/dwp0/Dropbox/OMF/omf')
import feeder as tp
from pprint import pprint
import re

# INPUT
filename = 'main3.glm'

# get the tree
tree = tp.parse(filename)

# modify the tree
for leafId in tree:
	leaf = tree[leafId]
	if 'object' in leaf:
		# fix the config naming.
		for key in leaf:
			if key in ['configuration','spacing','conductor_A','conductor_B','conductor_C','conductor_N']:
				leaf[key] = leaf[key].replace(':','_')
		# fix those without names.
		if 'name' not in leaf and 'recorder' != leaf['object']:
			leaf['name'] = leaf['object'].replace(':','_')
		# last, fix the object.
		colon = leaf['object'].find(':')
		if colon != -1:
			leaf['object'] = leaf['object'][:colon]

# write the tree
outString = tp.sortedWrite(tree)
with open('test.glm', 'w') as glmFile:
	glmFile.write(outString)
#!/usr/bin/env python

import os
import sys
sys.path.append('/Users/dwp0/Dropbox/OMF/windmilToGridlab')
import treeParser as tp
from pprint import pprint

glmTree = tp.parse('ILEC-Rembrandt-Handedit.glm')

lineCoords = [x for x in glmTree if 'object' in glmTree[x] and (glmTree[x]['object'] == 'underground_line' or glmTree[x]['object'] == 'overhead_line')]
print lineCoords

# Here are the keys for a line:
print [x for x in glmTree[14]]

# Replace the embedded configurations with refs to config objects.
for coord in lineCoords:
	intKeys = [x for x in glmTree[coord] if type(x) is int]
	if len(intKeys) == 1:
		target = intKeys[0]
		del glmTree[coord][target]
		if glmTree[coord]['object'] == 'underground_line':
			glmTree[coord]['configuration'] = 'lc_7211'
		elif glmTree[coord]['object'] == 'overhead_line':
			glmTree[coord]['configuration'] = 'ohconfig'

# Just write it out.
outGlmString = tp.sortedWrite(glmTree)
with open('ILEC-Rembrandt-SYNTH.glm','w') as synthFile:
	synthFile.write(outGlmString)
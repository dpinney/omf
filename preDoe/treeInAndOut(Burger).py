#!/usr/bin/env python

import treeParser as tp
import treeWriter as tw

tree = tp.parse('testglms/IEEE_13_house_vvc_2hrDuration.glm')

for x in tree:
	if 'clock' in tree[x]:
		print (x, tree[x])

glm = tw.write(tree)

outputFile = open('testglms/13_SYNTH.glm','w')
outputFile.write(glm)


# First, write the includes and modules.
# Then write everything else. Note that parent-child relationships could give us trouble in some cases.

#!/usr/bin/env python

import treeParser as tp
import treeWriter as tw

tree = tp.parse('testglms/Simple_System.glm')

glm = tw.write(tree)

outputFile = open('C:\\Users\\dwp0\\Dropbox\\OMF\\13 Node CVR\\simple system test glm\\Simple_System_SYNTH.glm','w')
outputFile.write(glm)


# First, write the includes and modules.
# Then write everything else. Note that parent-child relationships could give us trouble in some cases.

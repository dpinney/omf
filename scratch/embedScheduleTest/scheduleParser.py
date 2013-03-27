#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import feeder as tp
from pprint import pformat

tree=tp.parse('main.glm')
with open('out.txt','w') as outFile:
	outFile.write(pformat(tree))

with open('out.glm','w') as outGlm:
	outGlm.write(tp.sortedWrite(tree))
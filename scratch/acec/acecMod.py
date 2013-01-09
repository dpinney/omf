#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import treeParser as tp
import milToGridlab
from pprint import pprint

# Get ACEC-Frienship into a GLM:
outGlm = milToGridlab.convert('../../uploads/ACEC-Friendship.std','../../uploads/ACEC.seq')
outGlm += 'object voltdump {\nfilename output_voltage.csv;\n};'
with open('ACEC-Friendship-AUTOSYNTH.glm','w') as outFile:
	outFile.write(outGlm)
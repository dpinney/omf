#!/usr/bin/env python

'''
Get the ACEC Friendship feeder into a GLM file.
'''

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import treeParser as tp
import milToGridlab
from pprint import pprint

outGlm = milToGridlab.convert('../../uploads/ACEC-Friendship.std','../../uploads/ACEC.seq')
outGlm += 'object voltdump {\nfilename output_voltage.csv;\n};'
with open('ACEC-Friendship-NEOSYNTH.glm','w') as outFile:
	outFile.write(outGlm)
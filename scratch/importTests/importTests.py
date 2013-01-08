#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import treeParser as tp
import milToGridlab
from pprint import pprint
import traceback

filesToTest = [	['ACEC-COLOMA_SUB','ACEC.seq'],
				['ACEC-Friendship','ACEC.seq'],
				['ILEC-Gilmore_City_Sub','ILEC.seq'],
				['ILEC-Rembrandt','ILEC.seq'],
				['Owen-Bromley','Owen.seq'],
				['Owen-Burlington','Owen.seq']]

def testFile(stdName, seqName):
	try:
		outGlm = milToGridlab.convert('../../uploads/' + stdName + '.std','../../uploads/' + seqName)
		with open(stdName + '.glm','w') as outFile:
			outFile.write(outGlm)
		print stdName + ' converted.'
	except:
		print 'Conversion error! With ' + stdName
		traceback.print_exc(file=sys.stdout)

# Test all files:
for pair in filesToTest:
	testFile(pair[0],pair[1])
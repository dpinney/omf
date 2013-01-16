#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import treeParser as tp
import milToGridlab
from pprint import pprint
import traceback
import subprocess

filesToTest = [	['ACEC-COLOMA_SUB','ACEC.seq'],
				['ACEC-Friendship','ACEC.seq'],
				['ILEC-Gilmore_City_Sub','ILEC.seq'],
				['ILEC-Rembrandt','ILEC.seq'],
				['Owen-Bromley','Owen.seq'],
				['Owen-Burlington','Owen.seq']]

def testFile(stdName, seqName):
	try:
		outGlmString = milToGridlab.convert('../../uploads/' + stdName + '.std','../../uploads/' + seqName)
		outGlmString += 'object voltdump {\nfilename ' + stdName + '.VOLTS.csv;\n};'
		with open(stdName + '.glm','w') as outFile:
			outFile.write(outGlmString)
		print stdName + ' converted.'
		proc = subprocess.Popen(['gridlabd','-w', stdName + '.glm'], cwd='.')
		proc.wait()
	except:
		print 'Conversion error! With ' + stdName
		traceback.print_exc(file=sys.stdout)

# Clear and then test all files:
for fileName in os.listdir('.'):
	if fileName.endswith('.csv') or fileName.endswith('.glm'):
		os.remove(fileName)
for pair in filesToTest:
	testFile(pair[0], pair[1])
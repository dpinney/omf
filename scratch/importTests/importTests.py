#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import feeder as tp
import milToGridlab
from pprint import pprint
import traceback
import subprocess

filesToTest = [	['ABEC-COLUMBIA','ABEC.seq'],
				['ABEC-FRANK','ABEC.seq'],
				['INEC-GRAHAM','INEC.seq'],
				['INEC-RENOIR','INEC.seq'],
				['Olin-Barre','Olin.seq'],
				['Olin-Brown','Olin.seq']]

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
	if fileName.endswith('.csv') or (fileName.endswith('.glm') and not fileName.startswith('schedules.')):
		os.remove(fileName)
for pair in filesToTest:
	testFile(pair[0], pair[1])
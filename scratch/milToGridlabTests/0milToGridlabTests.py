''' Import all the Windmil feeders we have, run them through Gridlab, then volt-graph the results.'''

import sys
sys.path.append('../..')
sys.path.append('../../solvers/')
import milToGridlab as m2g, feeder, os, gridlabd, json, traceback
from pprint import pprint as pp
from matplotlib import pyplot as plt

pathPrefix = '../../uploads/'
testFiles = [('INEC-RENOIR.std','INEC.seq'), ('INEC-GRAHAM.std','INEC.seq'),
	('Olin-Barre.std','Olin.seq'), ('Olin-Brown.std','Olin.seq'),
	('ABEC-Frank.std','ABEC.seq'), ('ABEC-COLUMBIA.std','ABEC.seq')]

for stdPath, seqPath in testFiles:
	try:
		# Conver the std+seq.
		with open(pathPrefix + stdPath,'r') as stdFile, open(pathPrefix + seqPath,'r') as seqFile:
			outGlm,x,y = m2g.convert(stdFile.read(),seqFile.read())
		with open(stdPath.replace('.std','.glm'),'w') as outFile:
			outFile.write(feeder.sortedWrite(outGlm))
		print 'WROTE GLM FOR', stdPath
		try:
			# Draw the GLM.
			myGraph = feeder.treeToNxGraph(outGlm)
			feeder.latLonNxGraph(myGraph, neatoLayout=False)
			plt.savefig(stdPath.replace('.std','.png'))
		except:
			print 'FAILED DRAWING', stdPath
		try:
			# Run powerflow on the GLM.
			output = gridlabd.runInFilesystem(outGlm, keepFiles=False)
			with open(stdPath.replace('.std','.json'),'w') as outFile:
				json.dump(output, outFile, indent=4)
		except:
			print 'POWERFLOW FAILED', stdPath
	except:
		print 'FAILED CONVERTING', stdPath
		traceback.print_exc()

print os.listdir('.')
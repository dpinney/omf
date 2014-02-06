''' Import all the Windmil feeders we have, run them through Gridlab, then volt-graph the results.'''

import sys
sys.path.append('../..')
import milToGridlab as m2g, feeder, os
from pprint import pprint as pp

pathPrefix = '../../uploads/'
testFiles = [('INEC-RENOIR.std','INEC.seq'), ('INEC-GRAHAM.std','INEC.seq'),
	('Olin-Barre.std','Olin.seq'), ('Olin-Brown.std','Olin.seq'),
	('ABEC-Frank.std','ABEC.seq'), ('ABEC-COLUMBIA.std','ABEC.seq')]

for stdPath, seqPath in testFiles:
	try:
		with open(pathPrefix + stdPath,'r') as stdFile, open(pathPrefix + seqPath,'r') as seqFile:
			outGlm,x,y = m2g.convert(stdFile.read(),seqFile.read())
		with open(stdPath.replace('.std','.glm'),'w') as outFile:
			outFile.write(feeder.sortedWrite(outGlm))
		print 'WROTE GLM FOR', stdPath
		try:
			# Draw the GLM to a PNG.
			pass
		except:
			pass
		try:
			# Run powerflow on the GLM.
			pass
		except:
			pass
	except:
		print 'FAILED CONVERTING', stdPath

print os.listdir('.')
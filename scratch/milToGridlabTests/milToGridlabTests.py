import sys
sys.path.append('../..')
import milToGridlab as m2g, feeder, os
from pprint import pprint as pp

pathPrefix = '../../uploads/'
#testFiles = [('INEC-RENOIR.std','INEC.seq')]
testFiles = [('INEC-RENOIR.std','INEC.seq'),('Olin-Barre.std','Olin.seq'), ('ABEC-Frank.std','ABEC.seq')]

for stdPath, seqPath in testFiles:
	with open(pathPrefix + stdPath,'r') as stdFile, open(pathPrefix + seqPath,'r') as seqFile:
		outGlm,x,y = m2g.convert(stdFile.read(),seqFile.read())
	print 'Writing GLM for', stdPath
	pp(outGlm)
	with open(stdPath.replace('.std','.glm'),'w') as outFile:
		outFile.write(feeder.sortedWrite(outGlm))

print os.listdir('.')
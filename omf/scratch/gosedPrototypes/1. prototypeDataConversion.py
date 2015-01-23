''' Code to convert all the feeders we have for GOSED. '''

def convertTests():
	''' Test convert every windmil feeder we have (in uploads). Return number of exceptions we hit. '''
	import os, json, traceback, shutil, sys
	from matplotlib import pyplot as plt
	sys.path.append('../..')
	import feeder, milToGridlab
	from solvers import gridlabd
	exceptionCount = 0
	testFiles = [('AutocliAlberich.std','AutocliAlberich.seq'),('OlinBarre.std','OlinBarre.seq'),('OlinBeckenham.std','OlinBeckenham.seq')]
	for stdString, seqString in testFiles:
		try:
			# Convert the std+seq.
			with open(stdString,'r') as stdFile, open(seqString,'r') as seqFile:
				outGlm,x,y = milToGridlab.convert(stdFile.read(),seqFile.read())
			with open(stdString.replace('.std','.glm'),'w') as outFile:
				outFile.write(feeder.sortedWrite(outGlm))
			print 'WROTE GLM FOR', stdString
			try:
				# Draw the GLM.
				myGraph = feeder.treeToNxGraph(outGlm)
				feeder.latLonNxGraph(myGraph, neatoLayout=False)
				plt.savefig(stdString.replace('.std','.png'))
				print 'DREW GLM OF', stdString
			except:
				exceptionCount += 1
				print 'FAILED DRAWING', stdString
			try:
				# Run powerflow on the GLM.
				output = gridlabd.runInFilesystem(outGlm, keepFiles=False)
				with open(stdString.replace('.std','.json'),'w') as outFile:
					json.dump(output, outFile, indent=4)
				print 'RAN GRIDLAB ON', stdString					
			except:
				exceptionCount += 1
				print 'POWERFLOW FAILED', stdString
		except:
			print 'FAILED CONVERTING', stdString
			exceptionCount += 1
			traceback.print_exc()
	print exceptionCount

if __name__ == '__main__':
	convertTests()
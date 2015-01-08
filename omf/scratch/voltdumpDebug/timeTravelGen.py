''' Working towards a timeTravel chart. '''
import omf, json, os
from omf.solvers.gridlabd import runInFilesystem, anaDataTree

def main():
	''' JSON manipulation, Gridlab running, etc. goes here. '''
	feedJson = json.load(open('./ABEC Frank Calibrated.json'))
	# Add recorders here.
	stub = {'object':'group_recorder', 'group':'"class=node"', 'property':'voltage_A', 'interval':3600, 'file':'aVoltDump.csv'}
	for phase in ['A','B','C']:
		copyStub = dict(stub)
		copyStub['property'] = 'voltage_' + phase
		copyStub['file'] = phase.lower() + 'VoltDump.csv'
		feedJson['tree'][omf.feeder.getMaxKey(feedJson['tree']) + 1] = copyStub
	# Run gridlab.
	allOutputData = runInFilesystem(feedJson['tree'], attachments=feedJson['attachments'], keepFiles=True, workDir=".")
	print allOutputData.keys()

if __name__ == '__main__':
	main()
	pass
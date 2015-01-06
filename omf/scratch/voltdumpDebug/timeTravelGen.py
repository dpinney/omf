''' Working towards a timeTravel chart. '''
import omf, json, os

def feedJsonToFiles():
	''' Convert our JSON feeder into GLMs and stuff. '''
	feedJson = json.load(open('./ABEC Frank Calibrated.json'))
	with open('ABEC Frank Calibrated.glm','w') as outFile:
		# Add recorders here.
		stub = {'object':'group_recorder', 'group':'"class=node"', 'property':'voltage_A', 'interval':3600, 'file':'aVoltDump.csv'}
		for phase in ['A','B','C']:
			copyStub = dict(stub)
			copyStub['property'] = 'voltage_' + phase
			copyStub['file'] = phase.lower() + 'VoltDump.csv'
			feedJson['tree'][omf.feeder.getMaxKey(feedJson['tree']) + 1] = copyStub
		# Then write.
		outFile.write(omf.feeder.sortedWrite(feedJson['tree']))
	for name in feedJson['attachments'].keys():
		with open(name, 'w') as outFile:
			outFile.write(feedJson['attachments'][name])

if __name__ == '__main__':
	feedJsonToFiles()
	#addGroupRecorders()
	pass
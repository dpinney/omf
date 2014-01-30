#!/usr/bin/env python

from pprint import pprint
import csv
import random

# Grab the input data.
def csvToArray(csvFileName):
	with open(csvFileName,'r') as csvFile:
		csvReader = csv.reader(csvFile)
		outArray = []
		for row in csvReader:
			outArray += [row]
		return outArray

# Drop the first row which is metadata (n.b. these are not headers)
components = csvToArray('FRIENDSHIP.std')[1:]
hardwareStats = csvToArray('ACEC for NRECA CVR Improved.seq')[1:]

# Database testing.
def testTheDatabase():
	print '------TESTING THE DATABASE---------'
	print 'Component count: ' + str(len(components))
	print 'Hardware types count: ' + str(len(hardwareStats))
	print 'Example component: ' + str(components[0])
	print 'Example hardwareStat: ' + str(hardwareStats[0])

	# Get a list of all the equipment names:
	compNames = []
	for item in hardwareStats:
		compNames.append(item[0])

	# Check to see if any of a component's attributes is in the equipment list:
	def checkItem(item):
		matchList = []
		for attr in item:
			if attr in compNames and not attr.isdigit():
				matchList.append(attr)
		return matchList

	print 'Is item 43 in the database? Yes if this is an array: ' + str(checkItem(components[43]))
	print '------TESTING THE DATABASE---------\n\n\n'

testTheDatabase()

print '--------------ARE THE NAMES UNIQUE?--------------'
names = set([x[0] for x in components])
print 'Component count: ' + str(len(components))
print 'Unique names: ' + str(len(names))
print '--------------ARE THE NAMES UNIQUE?--------------\n\n\n'


print '------INVESTIGATING COMPONENTS---------'
elementFields = {	1 : 'Overhead Line (Type 1)',
					2 : 'Capacitor (Type 2)',
					3 : 'Underground Line (Type 3)',
					4 : 'Regulator (Type 4)',
					5 : 'Transformer (Type 5)',
					6 : 'Switch (Type 6)',
					8 : 'Node (Type 8)',
					9 : 'Source (Type 9)',
					10 : 'Overcurrent Device (Type 10)',
					11 : 'Motor (Type 11)',
					12 : 'Generator (Type 12)',
					13 : 'Consumer (Type 13)' }

for key in elementFields:
	componentMatches = [x for x in components if x[1] == str(key)]
	print elementFields[key] + ': ' + str(len(componentMatches))
print '------INVESTIGATING COMPONENTS---------\n\n\n'


print '------INVESTIGATING OVERHEADLINES---------'
overheadLines = [x for x in components if x[1]=='1']
testObject = overheadLines[25]
print testObject
print [testObject[8],testObject[9],testObject[10],testObject[11],testObject[13]]
print '------INVESTIGATING OVERHEADLINES---------\n\n\n'


print '-----------WE DONT GOT NO LINE SPACINGS----------------'
print 'Spacings referenced in overhead lines: ' + str([x[13] for x in overheadLines])
print 'Eqdb line spacings available (likely defaults): ' + str([x for x in hardwareStats if x[1]=='8'])
print '-----------WE DONT GOT NO LINE SPACINGS----------------\n\n\n'

print '-----------REGULATOR THOUGHTS----------------'
regulators = [x for x in components if x[1]=='4']
print 'Regulator voltages: ' + str([[x[14],x[15],x[16]] for x in regulators])
print '-----------HAVE TRANSFORMER DATA?----------------\n\n\n'

print '-----------HAVE TRANSFORMER DATA?----------------'
transformers = [x for x in components if x[1]=='5']
print 'Transformer windings: ' + str(set([x[8] for x in transformers]))
print 'phases:' + str([x[2] for x in transformers])
print '(input, output) kVolts: ' + str([(x[10],x[13]) for x in transformers])
print 'conductor counts:' + str([len([y for y in [x[9],x[24],x[25],x[26]] if y!='NONE' and y!='']) for x in transformers])
print 'conductors referenced: ' + str([[x[9],x[24],x[25],x[26]] for x in transformers])
print 'conductors available: ' + str([x for x in hardwareStats if x[1]=='5'])
print '-----------HAVE TRANSFORMER DATA?----------------\n\n\n'




'''
def debugging():
	import random

	#Test the components and connectivity arrangements.
	print 'SHOW ME SOME RANDOM COMPONENTS CONVERTED:'
	for x in range(5):
		print random.choice(convertedComponents)

	# Different object connectivity classes:
	fromToable = ['overhead_line','underground_line','regulator','transformer','switch','fuse']
	nodable = ['node']
	parentable = ['capacitor','ZIPload','diesel_dg','load']

	#TESTING SOME BAD CASES WE CAN'T SUPPORT LOGICALLY
	print 'Number of error cases where nodes have bogus parents:'
	print len([x for x in convertedComponents if x['object'] in nodable and parentType(x) in nodable])
	print len([x for x in convertedComponents if x['object'] in nodable and parentType(x) in parentable])
	print len([x for x in convertedComponents if x['object'] in nodable and parentType(x) in fromToable])
	print 'Number of other error cases:'
	print len([x for x in convertedComponents if x['object'] in parentable and parentType(x) in parentable])
	print len([x for x in convertedComponents if x['object'] in fromToable and parentType(x) in parentable])
	print 'Sanity test: links connecting to other links:'
	print len([x for x in convertedComponents if x['object'] in fromToable and parentType(x) in fromToable])

	for x in range(5):
		print random.choice(convertedComponents)

debugging()

'''
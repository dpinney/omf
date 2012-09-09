#!/usr/bin/env python

import datetime
import copy

def tokenizeGlm(glmFileName):
    import re
    file = open(glmFileName)
    data = file.read()
    # Get rid of http for stylesheets because we don't need it and it conflicts with comment syntax.
    data = re.sub(r'http:\/\/', '', data)  
    # Strip comments.
    data = re.sub(r'\/\/.*\n', '', data)
    # TODO: If the .glm creator has been lax with semicolons, add them back.
    # Also strip non-single whitespace because it's only for humans:
    data = data.replace('\n','').replace('\r','').replace('\t',' ')
    # Tokenize around semicolons, braces and whitespace.
    tokenized = re.split(r'(;|\}|\{|\s)',data)
    # Get rid of whitespace strings.
    basicList = filter(lambda x:x!='' and x!=' ', tokenized)
    return basicList

def parseTokenList(tokenList):
	# Tree variables.
	tree = {}
	guid = 0
	guidStack = []
	# Helper function to add to the current leaf we're visiting.
	def currentLeafAdd(key, value):
		current = tree
		for x in guidStack:
			current = current[x]
		current[key] = value
	# Helper function to turn a list of strings into one string with some decent formatting.
	# TODO: formatting could be nicer, i.e. remove the extra spaces this function puts in.
	def listToString(listIn):
		if len(listIn) == 0:
			return ''
		else:
			return reduce(lambda x,y:str(x)+' '+str(y),listIn[1:-1])
	# Pop off a full token, put it on the tree, rinse, repeat.
	while tokenList != []:
		# Pop, then keep going until we have a full token (i.e. 'object house', not just 'object')
		fullToken = []
		while fullToken == [] or fullToken[-1] not in ['{',';','}']:
			fullToken.append(tokenList.pop(0))
		# Work with what we've collected.
		if fullToken[-1] == ';':
			# Special case when we have zero-attribute items (like #include, #set, module).
			if guidStack == [] and fullToken != [';']:
				tree[guid] = {'omftype':fullToken[0],'argument':listToString(fullToken)}
				guid += 1
			# We process if it isn't the empty token (';')
			elif len(fullToken) > 1:
				currentLeafAdd(fullToken[0],listToString(fullToken))
		elif fullToken[-1] == '}':
			if len(fullToken) > 1:
				currentLeafAdd(fullToken[0],listToString(fullToken))
			guidStack.pop()
		elif fullToken[-1] == '{':
			currentLeafAdd(guid,{})
			guidStack.append(guid)
			guid += 1
			# Wrapping this currentLeafAdd is defensive coding so we don't crash on malformed glms.
			if len(fullToken) > 1:
				# Do we have a clock/object or else an embedded configuration object?
				if len(fullToken) < 4:
					currentLeafAdd(fullToken[0],fullToken[-2])
				else:
					currentLeafAdd('omfEmbeddedConfigObject', fullToken[0] + ' ' + listToString(fullToken))
	return tree

def parse(glmFileName):
	tokens = tokenizeGlm(glmFileName)
	return parseTokenList(tokens)

def dictToString(inDict):
	# Helper function: given a single dict, concatenate it into a string.
	def gatherKeyValues(inDict, keyToAvoid):
		otherKeyValues = ''
		for key in inDict:
			if type(key) is int:
				# WARNING: RECURSION HERE
				# TODO (cosmetic): know our depth, and indent the output so it's more human readable.
				otherKeyValues += dictToString(inDict[key])
			elif key != keyToAvoid:
				otherKeyValues += (key + ' ' + inDict[key] + ';\n')
		return otherKeyValues
	# Handle the different types of dictionaries that are leafs of the tree root:
	if 'omftype' in inDict:
		return inDict['omftype'] + ' ' + inDict['argument'] + ';'
	elif 'module' in inDict:
		return 'module ' + inDict['module'] + ' {\n' + gatherKeyValues(inDict, 'module') + '};\n'
	elif 'clock' in inDict:
		return 'clock {\n' + gatherKeyValues(inDict, 'clock') + '};\n'
	elif 'object' in inDict:
		return 'object ' + inDict['object'] + ' {\n' + gatherKeyValues(inDict, 'object') + '};\n'
	elif 'omfEmbeddedConfigObject' in inDict:
		return inDict['omfEmbeddedConfigObject'] + ' {\n' + gatherKeyValues(inDict, 'omfEmbeddedConfigObject') + '};\n'

def write(inTree):
	'''write(inTreeDict)->stringGlm'''
	output = ''
	for key in inTree:
		output += dictToString(inTree[key]) + '\n'
	return output

def sortedWrite(inTree):
	sortedKeys = sorted(inTree.keys(), key=int)
	output = ''
	for key in sortedKeys:
		output += dictToString(inTree[key]) + '\n'
	return output

def adjustTime(tree, simLength, simLengthUnits):
	# translate LengthUnits to minutes.
	if simLengthUnits == 'minutes':
		lengthInSeconds = simLength * 60
		interval = 60
	elif simLengthUnits == 'hours':
		lengthInSeconds = 1440 * simLength
		interval = 1440
	elif simLengthUnits == 'days':
		lengthInSeconds = 86400 * simLength
		interval = 86400

	starttime = datetime.datetime(2000,1,1)
	stoptime = starttime + datetime.timedelta(seconds=lengthInSeconds)

	# alter the clocks and recorders:
	for x in tree:
		leaf = tree[x]
		if 'clock' in leaf:
			# Ick, Gridlabd wants time values wrapped in single quotes:
			leaf['starttime'] = "'" + str(starttime) + "'"
			leaf['stoptime'] = "'" + str(stoptime) + "'"
		if 'object' in leaf and leaf['object'] == 'recorder':
			leaf['interval'] = str(interval)
			leaf['limit'] = str(simLength)

def fullyDeEmbed(glmTree):
	# TODO: fix problem with deEmbedding sub-objects called by name i.e. config object triplexconfig {blah}.
	def deEmbedOnce(glmTree):
		iterTree = copy.deepcopy(glmTree)
		for x in iterTree:
			for y in iterTree[x]:
				if type(iterTree[x][y]) is dict and 'object' in iterTree[x][y]:
					# set the parent and name attributes:
					glmTree[x][y]['parent'] = glmTree[x]['name']
					glmTree[x][y]['name'] = glmTree[x]['name'] + glmTree[x][y]['object'] + str(y)
					# check for key collision, which should technically be impossible:
					if y in glmTree.keys(): print 'KEY COLLISION!'
					# put the embedded object back up in the glmTree:
					glmTree[y] = glmTree[x][y]
					# delete the embedded copy:
					del glmTree[x][y]
	lenDiff = 1
	while lenDiff != 0:
		currLen = len(glmTree)
		deEmbedOnce(glmTree)
		lenDiff = len(glmTree) - currLen

def attachRecorders(tree, recorderType, objectToJoin, sample=False):
	# TODO: if sample is a percentage, only attach to that percentage of nodes chosen at random.
	# HACK: the biggestKey assumption only works for a flat tree or one that has a flat node for the last item...
	biggestKey = int(sorted(tree.keys())[-1]) + 1
	# Types of recorders we can attach:
	recorders = {	'Regulator':{'interval': '1', 'parent': 'X', 'object': 'recorder', 'limit': '1', 'file': 'Regulator_Y.csv', 'property': 'tap_A,tap_B,tap_C,power_in_A.real,power_in_A.imag,power_in_B.real,power_in_B.imag,power_in_C.real,power_in_C.imag,power_in.real,power_in.imag'},
					'Voltage':{'interval': '1', 'parent': 'X', 'object': 'recorder', 'limit': '1', 'file': 'Voltage_Y.csv', 'property': 'voltage_1.real,voltage_1.imag,voltage_2.real,voltage_2.imag,voltage_12.real,voltage_12.imag'},
					'Capacitor':{'interval': '1', 'parent': 'X', 'object': 'recorder', 'limit': '1', 'file': 'Capacitor_Y.csv', 'property': 'switchA,switchB,switchC'}
				}
	# Walk the tree. Don't worry about a recursive walk (yet).
	staticTree = copy.copy(tree)
	for key in staticTree:
		leaf = staticTree[key]
		if 'object' in leaf and 'name' in leaf:
			parentObject = leaf['name']
			if leaf['object'] == objectToJoin:
				# DEBUGGING MESSAGE: print 'just joined ' + parentObject
				newLeaf = copy.copy(recorders[recorderType])
				newLeaf['parent'] = parentObject
				newLeaf['file'] = recorderType + '_' + parentObject + '.csv'
				tree[biggestKey] = newLeaf
				biggestKey += 1

#Some test code follows:
#tokens = ['clock','{','clockey','valley','}','object','house','{','name','myhouse',';','object','ZIPload','{','inductance','bigind',';','power','newpower','}','size','234sqft','}']
#simpleTokens = tokenizeGlm('testglms/Simple_System.glm')
#print parseTokenList(simpleTokens)

# recorder attachment test
# tree = parse('./feeders/Simple Market System/main.glm')
# attachRecorders(tree, 'reg', 'regulator')
# attachRecorders(tree, 'volt', 'node')
# from pprint import pprint
# pprint(tree)
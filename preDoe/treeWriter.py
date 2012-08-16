#!/usr/bin/env python

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
	output = ''
	for key in inTree:
		output += dictToString(inTree[key]) + '\n'
	return output

# Note that we might have to change this up so we're sure the #set statements and modules (etc.) are written first. There might also be problems with parent-child relationships.
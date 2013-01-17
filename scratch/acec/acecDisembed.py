#!/usr/bin/env python

'''
Get the ACEC Friendship feeder into a GLM file.
'''

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import treeParser as tp
import milToGridlab
from pprint import pprint
import pickle


if 'disembed.pickle' in os.listdir('.'):
	with open('disembed.pickle','r') as pickFile:
		glm = pickle.load(pickFile)
else:
	glm = tp.parse('ACEC-Friendship-NEOSYNTH.glm')
	tp.fullyDeEmbed(glm)
	with open('disembed.pickle','w') as pickFile:
		pickle.dump(glm, pickFile)

def dedupGlm(compName, glmRef):
	'''
	Assume compName is transformer_configuration
	1. pull out a list of all transformer_configuration dicts.
	2. process to make redundant ones into tuples
	3. go through the list backwards and collapse chains of references. or fold carefully until we can't fold any more.
	4. actually replace the names on other objects and then delete the tuples.
	'''
	def isSameMinusName(x,y):
		newX = {val:x[val] for val in x if val != 'name'}
		newY = {val:y[val] for val in y if val != 'name'}
		return newX==newY
	def dupToTup(inList):
		# Go through a list of components, and given two identicals (up to name) in a row, replace the first one with (name1, name2).
		for i in xrange(0,len(inList)-1):
			if isSameMinusName(inList[i], inList[i+1]):
				inList[i] = (inList[i]['name'], inList[i+1]['name'])
			else:
				pass
	def dechain(tupleList):
		# Go backwards through a list of tuples and change e.g. (1,2),(2,3),(3,4) into (1,4),(2,4),(3,4).
		for i in xrange(len(tupleList)-1,0,-1):
			if tupleList[i][0] == tupleList[i-1][1]:
				tupleList[i-1] = (tupleList[i-1][0], tupleList[i][1])
			else:
				pass

	# sort the components, ignoring their names:
	compList = sorted([glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object']==compName], key=lambda x:{val:x[val] for val in x if val != 'name'})

	dupToTup(compList)

	nameMaps = [x for x in compList if type(x) is tuple]
	realConfigs = [x for x in compList if type(x) is dict]

	dechain(nameMaps)

	#Debug: print the amount of collapse:
 	print 'WORKING ON ' + compName
 	print 'Mappings:'
	print len(nameMaps)
	print 'Real configs:'
	print len(realConfigs)
	print 'Total:'
	print len(nameMaps) + len(realConfigs)

	nameDictMap = {x[0]:x[1] for x in nameMaps}

	# Killing duplicate objects
	iterKeys = glmRef.keys()
	for x in iterKeys:
		if 'name' in glmRef[x] and glmRef[x]['name'] in nameDictMap.keys():
			del glmRef[x]

	# Rewiring all objects
	iterKeys = glmRef.keys()
	if compName == 'transformer_configuration': 
		transformers = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'transformer']
		for tranny in transformers:
			if tranny['configuration'] in nameDictMap.keys(): tranny['configuration'] = nameDictMap[tranny['configuration']]
	elif compName == 'regulator_configuration': 
		regulators = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'regulator']
		for reggy in regulators:
			if reggy['configuration'] in nameDictMap.keys(): reggy['configuration'] = nameDictMap[reggy['configuration']]
	elif compName == 'line_spacing': 
		lineConfigs = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'line_configuration']
		for config in lineConfigs:
			if config['spacing'] in nameDictMap.keys(): config['spacing'] = nameDictMap[config['spacing']]
	elif compName == 'overhead_line_conductor' or compName == 'underground_line_conductor': 
		lineConfigs = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'line_configuration']
		for config in lineConfigs:
			if config['conductor_A'] in nameDictMap.keys(): config['conductor_A'] = nameDictMap[config['conductor_A']]
			if config['conductor_B'] in nameDictMap.keys(): config['conductor_B'] = nameDictMap[config['conductor_B']]
			if config['conductor_C'] in nameDictMap.keys(): config['conductor_C'] = nameDictMap[config['conductor_C']]
			if config['conductor_N'] in nameDictMap.keys(): config['conductor_N'] = nameDictMap[config['conductor_N']]
	elif compName == 'line_configuration': 
		lines = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] in ['overhead_line','underground_line']]
		for line in lines:
			if line['configuration'] in nameDictMap.keys(): line['configuration'] = nameDictMap[line['configuration']]


dedupGlm('transformer_configuration', glm)
dedupGlm('regulator_configuration', glm)
dedupGlm('line_spacing', glm)
dedupGlm('overhead_line_conductor', glm)
dedupGlm('underground_line_conductor', glm)
# NOTE: This last dedup has to come last, because it relies on doing conductors and spacings first!
dedupGlm('line_configuration', glm)


outString = tp.sortedWrite(glm)
with open('ACEC-Friendship-DISEMB.glm','w') as outFile:
	outFile.write(outString)
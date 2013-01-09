#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.getcwd())))
import treeParser as tp
from pprint import pprint
import pickle

haveCache = False
dirFiles = os.listdir('.')
if 'acec.pickle' in dirFiles:
	haveCache = True
	with open('acec.pickle') as cache:
		glm = pickle.load(cache)
else:
	glm = tp.parse('ACEC-Friendship-handedit.glm')

allLoads = [glm[x] for x in glm if 'object' in glm[x] and glm[x]['object']=='load']
allTransformers = [glm[x] for x in glm if 'object' in glm[x] and glm[x]['object']=='transformer']
print 'Number of loads (some group on one transformer):'
print len(allLoads)
nodesOnLoadsNames = list(set([x['parent'] for x in allLoads]))
print 'Number of nodes on loads:'
print len(nodesOnLoadsNames)
print 'Number of transformers:'
print len(allTransformers)
allTransformersToLoads = [x for x in allTransformers if (x['from'] in nodesOnLoadsNames or x['to'] in nodesOnLoadsNames)]
print 'Number of transformers leading immediately to loads:'
print len(allTransformersToLoads)

for x in allLoads:
	testPhases = set('ABCN') - set(x['phases'])
	for y in testPhases:
		testPow = 'constant_power_' + y
		if testPow in x and x[testPow] != '0': print 'Load FAIL on ' + x['name']

if haveCache == False:
	with open('acec.pickle', 'w') as cache:
		pickle.dump(glm, cache)
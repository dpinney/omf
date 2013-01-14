#!/usr/bin/env python

'''
We need to change:
1. Loads into triplex nodes with constant power.
2. Nodes on loads into meters.

'''

import os
import sys
from os.path import dirname
# go two layers up and add that to this file's temp path
sys.path.append(dirname(dirname(os.getcwd())))
import treeParser as tp
from pprint import pprint
import pickle

# caching our import and save 20 seconds every gol'durned run.
haveCache = False
dirFiles = os.listdir('.')
if 'acec.pickle' in dirFiles:
	haveCache = True
	with open('acec.pickle') as cache:
		glm = pickle.load(cache)
else:
	glm = tp.parse('ACEC-Friendship-handedit.glm')


allLoadKeys = [x for x in glm if 'object' in glm[x] and glm[x]['object']=='load']

print 'Number of loads (some group on one transformer):'
print str(len(allLoadKeys)) + '\n'

allNamesNodesOnLoads = list(set([glm[key]['parent'] for key in allLoadKeys]))
print 'Number of nodes on loads:'
print str(len(allNamesNodesOnLoads)) + '\n'

allNodesOnLoadsKeys = [x for x in glm if 'name' in glm[x] and glm[x]['name'] in allNamesNodesOnLoads]

print 'Example node:'
print glm[allNodesOnLoadsKeys[1]]
print 'Example load:'
print glm[allLoadKeys[1]]

# Fix da nodes.
# {'phases': 'BN', 'object': 'node', 'nominal_voltage': '2400', 'name': 'nodeS1806-32-065T14102'}
# object triplex_meter { phases BS; nominal_voltage 120; };
for nodeKey in allNodesOnLoadsKeys:
	newDict = {}
	newDict['object'] = 'triplex_meter'
	newDict['name'] = glm[nodeKey]['name']
	newDict['phases'] = sorted(glm[nodeKey]['phases'])[0] + 'S'
	newDict['nominal_voltage'] = '120'
	glm[nodeKey] = newDict

# Fix da loads.
#{'phases': 'BN', 'object': 'load', 'name': 'S1806-32-065', 'parent': 'nodeS1806-32-065T14102', 'load_class': 'R', 'constant_power_C': '0', 'constant_power_B': '1.06969', 'constant_power_A': '0', 'nominal_voltage': '120'}
for loadKey in allLoadKeys:
	newDict = {}
	newDict['object'] = 'triplex_node'
	newDict['name'] = glm[loadKey]['name']
	newDict['phases'] = sorted(glm[loadKey]['phases'])[0] + 'S'
	a = glm[loadKey]['constant_power_A']
	b = glm[loadKey]['constant_power_B']
	c = glm[loadKey]['constant_power_C']
	powList = [x for x in [a,b,c] if x!='0' and x!='0.0']
	newDict['power_12'] = ('0' if len(powList)==0 else str(float(powList.pop())*1000))
	newDict['parent'] = glm[loadKey]['parent']
	newDict['nominal_voltage'] = '120'
	glm[loadKey] = newDict


# Gotta fix the transformers too...
allTransKeys = [x for x in glm if 'object' in glm[x] and glm[x]['object'] == 'transformer']
for key in allTransKeys:
	fromName = glm[key]['from']
	toName = glm[key]['to']
	fromToPhases = [glm[x]['phases'] for x in glm if 'name' in glm[x] and glm[x]['name'] in [fromName, toName]]
	glm[key]['phases'] = set('ABC').intersection(*map(set, fromToPhases)).pop() + 'S'


# cache update.
if haveCache == False:
	with open('acec.pickle', 'w') as cache:
		pickle.dump(glm, cache)

# print out
with open('ACEC-Friendship-handedit-PNNL.glm','w') as outFile:
	outString = tp.sortedWrite(glm)
	outFile.write(outString)
#!/usr/bin/env python

'''
We need to change:
1. Loads into triplex nodes with constant power.
2. Nodes on loads into meters.
3. Transformer phase fix.
4. Length and power order of magnitude fixes.

'''

import os
import sys
from os.path import dirname
# go two layers up and add that to this file's temp path
sys.path.append(dirname(dirname(os.getcwd())))
import feeder as tp
from pprint import pprint

glm = tp.parse('ACEC-Friendship-AUTOSYNTH.glm')

def secondarySystemFix(glm):
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


	all2ndTransKeys = []
	all2ndLoadKeys = []
	all2ndNodeKeys = []
	def nameToKey(name):
		hits = [x for x in glm if 'name' in glm[x] and glm[x]['name'] == name]
		if len(hits) == 0:
			return []
		else:
			return hits

	for key in glm:
		if 'object' in glm[key] and glm[key]['object'] == 'transformer':
			fromName = glm[key]['from']
			toName = glm[key]['to']
			if fromName in allNamesNodesOnLoads:
				all2ndTransKeys.append(key)
				all2ndNodeKeys.extend(nameToKey(fromName))
				all2ndLoadKeys.extend([x for x in glm if 'parent' in glm[x] and 'object' in glm[x] and glm[x]['object'] == 'load' and glm[x]['parent'] == fromName])				
			elif toName in allNamesNodesOnLoads:
				all2ndTransKeys.append(key)
				all2ndNodeKeys.extend(nameToKey(toName))
				all2ndLoadKeys.extend([x for x in glm if 'parent' in glm[x] and 'object' in glm[x] and glm[x]['object'] == 'load' and glm[x]['parent'] == toName])
			else:
				# this ain't no poletop transformer
				pass

	allTransKeys = [x for x in glm if 'object' in glm[x] and glm[x]['object'] == 'transformer']

	print 'All transformers:'
	print len(allTransKeys)
	print 'All secondary system transformers:'
	print len(all2ndTransKeys)

	# Fix da nodes.
	# {'phases': 'BN', 'object': 'node', 'nominal_voltage': '2400', 'name': 'nodeS1806-32-065T14102'}
	# object triplex_meter { phases BS; nominal_voltage 120; };
	for nodeKey in all2ndNodeKeys:
		newDict = {}
		newDict['object'] = 'triplex_meter'
		newDict['name'] = glm[nodeKey]['name']
		newDict['phases'] = sorted(glm[nodeKey]['phases'])[0] + 'S'
		newDict['nominal_voltage'] = '120'
		glm[nodeKey] = newDict

	# Fix da loads.
	#{'phases': 'BN', 'object': 'load', 'name': 'S1806-32-065', 'parent': 'nodeS1806-32-065T14102', 'load_class': 'R', 'constant_power_C': '0', 'constant_power_B': '1.06969', 'constant_power_A': '0', 'nominal_voltage': '120'}
	for loadKey in all2ndLoadKeys:
		newDict = {}
		newDict['object'] = 'triplex_node'
		newDict['name'] = glm[loadKey]['name']
		newDict['phases'] = sorted(glm[loadKey]['phases'])[0] + 'S'
		a = glm[loadKey]['constant_power_A']
		b = glm[loadKey]['constant_power_B']
		c = glm[loadKey]['constant_power_C']
		powList = [x for x in [a,b,c] if x!='0' and x!='0.0']
		newDict['power_12'] = ('0' if len(powList)==0 else powList.pop())
		newDict['parent'] = glm[loadKey]['parent']
		newDict['nominal_voltage'] = '120'
		glm[loadKey] = newDict

	# Gotta fix the transformer phases too...
	for key in all2ndTransKeys:
		fromName = glm[key]['from']
		toName = glm[key]['to']
		fromToPhases = [glm[x]['phases'] for x in glm if 'name' in glm[x] and glm[x]['name'] in [fromName, toName]]
		glm[key]['phases'] = set('ABC').intersection(*map(set, fromToPhases)).pop() + 'S'
		configKey = [x for x in glm[key] if type(x) is int].pop()
		glm[key][configKey]['connect_type'] = 'SINGLE_PHASE_CENTER_TAPPED'

secondarySystemFix(glm)

# print out
with open('ACEC-Friendship-Full.glm','w') as outFile:
	outString = tp.sortedWrite(glm)
	outFile.write(outString)
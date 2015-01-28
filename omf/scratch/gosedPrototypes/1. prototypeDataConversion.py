''' Code to convert all the feeders we have for GOSED.
And some debug stuff. ''' 

import os, json, traceback, shutil, sys
from matplotlib import pyplot as plt
sys.path.append('../..')
import feeder, milToGridlab
from solvers import gridlabd

def convertTests():
	''' Test convert every windmil feeder we have (in uploads). Return number of exceptions we hit. '''
	exceptionCount = 0
	testFiles = [('OrvilleTreePond.std','OrvilleTreePond.seq')]
	# ,('OlinBarre.std','OlinBarre.seq'),('OlinBeckenham.std','OlinBeckenham.seq'), ('AutocliAlberich.std','AutocliAlberich.seq')
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

def getTreeOrCache():
	# Cache this; it takes 30 seconds on my laptop to get the dang thing going.
	if 'AutocliAlberichCache.json' not in os.listdir('.'):
		tree = feeder.parse('2. edited.glm')
		with open('AutocliAlberichCache.json','w') as cFile:
			json.dump(tree, cFile, indent=4)
	else:
		with open('AutocliAlberichCache.json', 'r') as iFile:
			tree = json.load(iFile)
	return tree

def alberichFix():
	tree = getTreeOrCache()
	# Make a map so we can look up lots of names fast.
	nameMap = nameToIndexMap(tree)
	# Look at every transformer and fix it.
	for ob in tree.values():
		if ob.get('object','') == 'transformer':
			fromOb = tree.get(nameMap.get(ob.get('from')))
			toOb = tree.get(nameMap.get(ob.get('to')))
			configOb = tree.get(nameMap.get(ob.get('configuration')))
			if configOb.get('connect_type') == 'SINGLE_PHASE_CENTER_TAPPED' and toOb.get('object') != 'triplex_meter':
				# Look before you leap:
				# print 'TRN', ob.get('name'), fromOb.get('phases'), ob.get('phases'), toOb.get('phases'), configOb.get('name')
				# DO THE FIX HERE
				configOb['connect_type'] = 'SINGLE_PHASE'
	# Line conductor issue inspection.
	for ob in tree.values():
		if ob.get('object') in ['overhead_line','underground_line']:
			configOb = tree.get(nameMap.get(ob.get('configuration')))
			configPhases = ''.join([str(x)[-1:] for x in configOb.keys() if x.startswith('conductor_')])
			if not set(ob.get('phases')).issubset(configPhases):
				# Look before you leap:
				print ob.get('name'), ob.get('phases'), ''.join(configPhases)
				# FIX: add "conductor_B OHx19126-S19538_conductor_C;" to OHx20021-LINECONFIG.
	# PHASE MISMATCH ISSUE AGAIN
	'''
	object transformer_configuration {
	name OTx192315_B-CONFIG-CENTER;
	primary_voltage 14400.0;
	secondary_voltage 120.0;
	connect_type SINGLE_PHASE;
	impedance 0.00033+0.0022j;
	powerB_rating 37.5;
	power_rating 37.5;
	};
	'''
	# Duplicate some CENTERS because there was overlap!
	for ob in tree.values():
		if ob.get('object')=='transformer':
			fromOb = tree.get(nameMap.get(ob.get('from')))
			toOb = tree.get(nameMap.get(ob.get('to')))
			configOb = tree.get(nameMap.get(ob.get('configuration')))
			# if 'S' in ob.get('phases') and configOb.get('connect_type')=='SINGLE_PHASE':
				# # Look before you leap.
				# print ob.get('name'), ob.get('phases'), configOb.get('connect_type')
				# # Make a new config object.
				# configCopy = dict(configOb)
				# configCopy['connect_type'] = 'SINGLE_PHASE_CENTER_TAPPED'
				# configCopy['name'] = configOb.get('name') + '-CENTER'
				# # Connect the new config and point at it.
				# tree[feeder.getMaxKey(tree)] = configCopy
				# ob['configuration'] = configCopy.get('name')
	# writeFeeder(tree, '2. edited.glm')
	for ob in tree.values():
		if ob.get('object') in ['underground_line', 'overhead_line', 'transformer']:
			fromOb = tree.get(nameMap.get(ob.get('from')))
			toOb = tree.get(nameMap.get(ob.get('to')))
			if len(set(toOb.get('phases'))-set('NS')) > len(set(ob.get('phases'))):
				print ob.get('name'), ob.get('phases'), toOb.get('phases')

def writeFeeder(tree, fname):
	with open(fname, 'w') as outFile:
		outFile.write(feeder.sortedWrite(tree))

def nameToIndexMap(tree):
	''' Given a feeder tree, return a dict mapping names of objects to their index.
		If you need to look up more than 1 name in a feeder, making one of these maps is going to save you a HUGE amount of time. '''
	index = {}
	for key, val in tree.iteritems():
		index[val.get('name','')] = key
	return index

if __name__ == '__main__':
	convertTests()
	# alberichFix()
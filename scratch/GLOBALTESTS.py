#!/usr/bin/env python

# How big is a pickled analysis?

import os, sys
os.chdir('..')
sys.path.append(os.getcwd())

def test1():
	import pickle, analysis, storage
	store = storage.Filestore('data')

	obj = analysis.Analysis('zCVR ACEC 3M',store.getMetadata('Analysis', 'zCVR ACEC 3M'),store.get('Analysis', 'zCVR ACEC 3M'))

	with open('./scratch/testPickle.pickle','w') as pickFile:
		pickle.dump(obj, pickFile)

	print os.stat('./scratch/testPickle.pickle')

	os.remove('./scratch/testPickle.pickle')

	# ONLY 7 MB!
	# What about a json version?

	with open('./scratch/testJson.json','w') as jsonFile:
		import json
		json.dump([obj.mdToJson(),obj.toJson(),[x.toDict() for x in obj.studies]],jsonFile, indent=4)

	print os.stat('./scratch/testJson.json')

	import jsonpickle

	jsonpick = jsonpickle.encode(obj)
	with open('./scratch/testPickJson.json','w') as jsonPickFile:
		jsonPickFile.write(jsonpick)


	neoObj = jsonpickle.decode(jsonpick)

	print neoObj.studies

	os.remove('./scratch/testPickle.pickle')

# test1()

# How much slower is it to read a bunch of studies than a single analysis?

import timeit
setup = '''
import json, os
def fullAnalysis():
	with open('data/Analysis/zBattery Comp.md.json','r') as anaFile:
		print json.load(anaFile)

def byStudy():
	studnames = [x for x in os.listdir('data/Study/') if x.startswith('zBattery') and x.endswith('.md.json')]
	for stud in studnames:
		with open('data/Study/' + stud, 'r') as studFile:
			print json.load(studFile)
'''

a = timeit.timeit('fullAnalysis()', setup=setup, number=20)
b = timeit.timeit('byStudy()', setup=setup, number=20)
print '#####FULL ANALYSIS', a
print '#####BY STUDY', b

# Five times slower.
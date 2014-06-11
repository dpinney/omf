#!/usr/bin/env python

# How big is a pickled analysis?

import os, sys, json
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


import timeit
setup = '''
import os, json
def fullAnalysis():
	with open('data/Analysis/zBattery Comp.md.json','r') as anaFile:
		json.load(anaFile)

def byStudy():
	studnames = [x for x in os.listdir('data/Study/') if x.startswith('zBattery') and x.endswith('.md.json')]
	for stud in studnames:
		with open('data/Study/' + stud, 'r') as studFile:
			json.load(studFile)

def loadAll():
	with open('data/Study/zCVR ACEC 3M---CVR.json','r') as openFile:
		json.load(openFile)

def loadMd():
	with open('data/Study/zCVR ACEC 3M---CVR.md.json','r') as openFile:
		json.load(openFile)

def loadNormal():
	with open('scratch/monolithicjsontest.json','r') as openFile:
		json.load(openFile)

def loadSelected():
	with open('scratch/monolithicjsontest.json','r') as openFile:
		test = openFile.read()
		test.split(',')
'''



# How much slower is it to read a bunch of studies than a single analysis?
# Ten times slower.

a = timeit.timeit('fullAnalysis()', setup=setup, number=200)
b = timeit.timeit('byStudy()', setup=setup, number=200)
print '#####FULL ANALYSIS', a
print '#####BY STUDY', b

# How long does it take to read a md file versus a plain file?
# Over 100 times slower!

c = timeit.timeit('loadMd()', setup=setup, number=20)
d = timeit.timeit('loadAll()', setup=setup, number=20)
print '#####LOAD MD', c
print '#####LOAD FULL', d

# Hey, what about a custom json deserialization?

c = timeit.timeit('loadNormal()', setup=setup, number=20)
d = timeit.timeit('loadSelected()', setup=setup, number=20)
print '#####NORMAL', c
print '#####REDUCED', d

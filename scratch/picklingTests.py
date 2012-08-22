#!/usr/bin/env python

''' Is it faster to have separate metadata? '''

import time
import cPickle as pickle
import studyGridlab as sg
import utility
import grid
import os
import tempfile

# Start by creating a study 'test'
print 'Testing here.'
direc = '../feeders/13 Node Reference Feeder/'
includes = {}
for x in os.listdir(direc):
	if (x.endswith('.glm') and x != 'main.glm') or x.endswith('.tmy2') or x.endswith('.player'):
		with open(direc + x, 'r') as openFile:
			includes[x] = openFile.read()
with open(direc+'main.glm', 'r') as mainFile:
	glmString = mainFile.read()
test = sg.StudyGridlab('chicken', grid.Grid(glmString), includes)
print test

# Also create a basic metadata.

md = {'name':'johnson','created':'lastweek','size':56,'status':'preRun'}

# Test em.

with open('test.md','wb') as tmpMd, open('test.pickle','wb') as tmpPickle:
	pickle.dump(test,tmpPickle)
	tmpMd.write(str(md))

start = time.clock()
with open('test.md','r') as tmpMd:
	data = eval(tmpMd.read())
	print md['status']
end = time.clock()
print 'Metadata access: ' + str(end-start)

start = time.clock()
with open('test.pickle','r') as tmpPickle:
	study = pickle.load(tmpPickle)
	print study.status
end = time.clock()
print 'Pickle access: ' + str(end-start)

os.remove('test.md')
os.remove('test.pickle')

# Conclusion: accessing that metadata is A LOT FASTER (1000 times!).
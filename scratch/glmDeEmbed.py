#!/usr/bin/env python

''' Try to flatten a glm. '''

import treeParser as tp
import copy

tree = tp.parse('./feeders/13 Node Reference Feeder/main.glm')

print str(len(tree.keys())) + ' keys:' + str(tree.keys())

tp.fullyDeEmbed(tree)

print str(len(tree.keys())) + ' keys:' + str(tree.keys())

outData = tp.write(tree)

with open('main.glm','w') as outFile:
	outFile.write(outData)

def safeRename(glmTree):
	pass

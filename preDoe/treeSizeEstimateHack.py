#!/usr/bin/env python

# how big is a tree?
# 13 node CVR we'll consider a big tree.

import treeParser as tp
import os

tree = tp.parse('testglms/13_SYNTH.glm')

out = open('test.txt','w')
out.writelines(str(tree))
out.close()

print 'making a file estimate: ' + str(os.path.getsize('test.txt')/1000) + ' KB'
print 'strLength estimate: ' + str(len(str(tree))/1000) + ' KB'
# Wow, that's about 1 MB per tree.

os.remove('test.txt')

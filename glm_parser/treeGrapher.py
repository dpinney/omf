#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import treeParser
import networkx as nx
import matplotlib.pyplot as plot

def testGlm(glmTree):
	# How many nodes do we have?
	y = 0
	for x in glmTree:
		if 'object' in glmTree[x] and glmTree[x]['object'] == 'node':
			y += 1
	print 'This .glm has ' + str(y) + ' nodes.\n'

	# Print what and how many objects we have.
	countDict = dict([])
	for x in glmTree:
		if 'object' in glmTree[x]:
			object = glmTree[x]['object']
			if object in countDict:
				countDict[object] += 1
			else:
				countDict[object] = 1
	print 'What are the types and counts of the objects we have?'
	print countDict

	# Graph it.
	glmGraph = nx.Graph()
	nodeNodes = []
	for x in glmTree:
		if 'from' in glmTree[x] and 'to' in glmTree[x]:
			glmGraph.add_edge(glmTree[x]['from'],glmTree[x]['to'])
		if 'parent' in glmTree[x] and 'name' in glmTree[x]:
			glmGraph.add_edge(glmTree[x]['name'],glmTree[x]['parent'])
		if 'object' in glmTree[x] and glmTree[x]['object'] == 'node':
			nodeNodes.append(glmTree[x]['name'])
	nodeNodes = set(nodeNodes).intersection(set(glmGraph.nodes()))
	notNodes = set(glmGraph.nodes()) - nodeNodes
	layout = nx.spring_layout(glmGraph)
	nx.draw_networkx_nodes(glmGraph,layout,notNodes,alpha=0.7,node_size=150)
	nx.draw_networkx_nodes(glmGraph,layout,nodeNodes,alpha=0.7,node_color='b')
	nx.draw_networkx_edges(glmGraph,layout,alpha=0.9)
	# Labels only if we have few nodes:
	if len(glmGraph.nodes()) < 15:
		nx.draw_networkx_labels(glmGraph,layout,alpha=0.3)
	plot.axis('off')
	plot.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
	plot.show()

def sanity(tree):
	for x in tree:
		print (x, tree[x])

def main():
	tokenList = treeParser.tokenizeGlm('testglms/IEEE_13_house_vvc_2hrDuration.glm')
	#tokenList = treeParser.tokenizeGlm('testglms/PinneyEdit-MWGLD-2.glm')
	#tokenList = treeParser.tokenizeGlm('testglms/Simple_System.glm')
	tree = treeParser.parseTokenList(tokenList)
	sanity(tree)
	testGlm(tree)



if __name__ == '__main__':
	main()


import random, re, datetime, json, os, tempfile, shutil, csv, math
from os.path import join as pJoin
import pandas as pd
import numpy as np
import scipy
from scipy import spatial
import scipy.stats as st
from sklearn.preprocessing import LabelEncoder
import plotly as py
import plotly.graph_objs as go
# OMF imports
import omf
import omf.feeder
import omf.geo
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

def getMaxSubtree(graph, start):
	visited, stack = set(), [start]
	while stack:
		vertex = stack.pop()
		if vertex not in visited:
			visited.add(vertex)
			stack.extend(graph[vertex] - visited)
	return visited

def findPathToFault(graph, start, finish):
	stack = [(start, [start])]
	while stack:
		(vertex, path) = stack.pop()
		for next in graph[(vertex)] - set(path):
			if next == finish:
				yield path + [next]
			else:
				stack.append((next, path + [next]))

def cutoffFault(pathToOmd, faultedLine, workDir=None):
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)

	with open(pathToOmd) as inFile:
		tree = json.load(inFile)['tree']
	outageMap = omf.geo.omdGeoJson(pathToOmd, conversion = False)

	faultedNode = ''
	for key in tree.keys():
		if tree[key].get('name','') == faultedLine:
			faultedNode = tree[key]['from']
	# print(faultedNode)
		
	print(len(tree))
	removedKeys = 1
	while removedKeys != 0:
		treeKeys = len(tree.keys())
		obs = list(tree.values())
		n2k = omf.feeder.nameIndex(tree)
		for o in obs:
			if 'to' in o:
				top = o
				node = tree[n2k[o['to']]]
				allBottoms = []
				for o2 in obs:
					if o2.get('from', None) == node['name']:
						allBottoms.append(o2)
				# print 'TOPLINE', o['name'], 'NODE', node['name'], len(allBottoms)
				if len(allBottoms) == 1:
					bottom = allBottoms[0]
					if (top.get('object', '') == bottom.get('object', '')) and (top.get('name', '') != faultedLine) and (bottom.get('name', '') != faultedLine) and (top.get('object', '') != 'recloser') and (bottom.get('object', '') != 'recloser'):
					#if top.get('configuration','NTC') == bottom.get('configuration','NBC'):
						# print 'MATCH!', top['name'], top['length'], bottom['name'], bottom['length'], 'TOTAL', float(top['length']) + float(bottom['length'])
						# delete node and bottom line, make top line length = sum of both lines and connect to bottom to.
						if ('length' in top) and ('length' in bottom):
							newLen = float(top['length']) + float(bottom['length'])
							try:
								topTree = tree[n2k[o['name']]]
								topTree['length'] = str(newLen)
								topTree['to'] = bottom['to']
								topTree['configuration'] = bottom['configuration']
								del tree[n2k[node['name']]]
								del tree[n2k[bottom['name']]]
							except:
								continue #key weirdness
		removedKeys = treeKeys - len(tree.keys())
	print(len(tree))

	adjacList = {}
	reclosers = []
	for key in tree.keys():
		obtype = tree[key].get('object','')
		if obtype.startswith('underground_line') or obtype.startswith('overhead_line') or obtype.startswith('triplex_line') or obtype.startswith('switch') or obtype.startswith('recloser') or obtype.startswith('transformer') or obtype.startswith('fuse') or obtype.startswith('regulator'):
			if obtype.startswith('recloser'):
				reclosers.append(tree[key])
			if 'from' in tree[key].keys() and 'to' in tree[key].keys():
				if not tree[key]['from'] in adjacList.keys():
					adjacList[tree[key]['from']] = set()
				if not tree[key]['to'] in adjacList.keys():
					adjacList[tree[key]['to']] = set()
				adjacList[tree[key]['from']].add(tree[key]['to'])
				adjacList[tree[key]['to']].add(tree[key]['from'])
	#print(reclosers)

	# def findPathToFault(graph, start, finish):
	# 	queue = [(start, [start])]
	# 	while queue:
	# 		(vertex, path) = queue.pop(0)
	# 		for next in graph[vertex] - set(path):
	# 			if next == finish:
	# 				yield path + [next]
	# 			else:
	# 				queue.append((next, path + [next]))
	
	bestReclosers = {}
	tree2 = tree.copy()
	for key in tree2.keys():
		if bool(tree2[key].get('bustype','')) is True:
			subtree = getMaxSubtree(adjacList, tree[key]['name'])
			if faultedNode in subtree:
				found = False
				path = findPathToFault(adjacList, tree[key]['name'], faultedNode)
				for lis in path:
					# print(lis)
					row = len(lis) - 1
					while row > -1:
						for recloser in reclosers:
							if recloser['from'] == lis[row]:
								if recloser['to'] == lis[row-1]:
									found = True
									bestReclosers[tree2[key]['name']] = recloser
									for key in tree2.keys():
										if tree2[key] == recloser:
											del (tree[key])
									break
							if recloser['to'] == lis[row]:
								if recloser['from'] == lis[row-1]:
									found = True
									bestReclosers[tree2[key]['name']] = recloser
									for key in tree2.keys():
										if tree2[key] == recloser:
											del (tree[key])
									break
						if found == True:
							break
						row -= 1
				if found == False:
					bestReclosers[tree[key]['name']] = None
	print(bestReclosers)
	return tree, bestReclosers

def addTieLines(tree, tieLines, workDir, bestTies, bestReclosers):

	adjacList = {}
	reclosers = []
	vertices = set()
	for key in tree.keys():
		obtype = tree[key].get('object','')
		if obtype.startswith('underground_line') or obtype.startswith('overhead_line') or obtype.startswith('triplex_line') or obtype.startswith('switch') or obtype.startswith('recloser') or obtype.startswith('transformer') or obtype.startswith('fuse') or obtype.startswith('regulator'):
			if obtype.startswith('recloser'):
				reclosers.append(tree[key])
			if 'from' in tree[key].keys() and 'to' in tree[key].keys():
				if not tree[key]['from'] in adjacList.keys():
					adjacList[tree[key]['from']] = set()
					vertices.add(tree[key].get('from', ''))
				if not tree[key]['to'] in adjacList.keys():
					adjacList[tree[key]['to']] = set()
					vertices.add(tree[key].get('to', ''))
				adjacList[tree[key]['from']].add(tree[key]['to'])
				adjacList[tree[key]['to']].add(tree[key]['from'])

	powered = set()
	for key in tree.keys():
		if bool(tree[key].get('bustype','')) is True:
			powered |= getMaxSubtree(adjacList, tree[key]['name'])

	def safeInt(x):
		try: return int(x)
		except: return 0

	biggestKey = max([safeInt(x) for x in tree.keys()])

	unpowered = vertices - powered
	tie_row_count = tieLines.shape[0]
	entry = 0
	index = 0
	while entry < tie_row_count:
		tieNode = None
		found = False
		if tieLines.loc[entry, 'to'] in unpowered and tieLines.loc[entry, 'from'] in powered:
			tieNode = tieLines.loc[entry, 'to']
		if tieLines.loc[entry, 'from'] in unpowered and tieLines.loc[entry, 'to'] in powered:
			tieNode = tieLines.loc[entry, 'from']
		if tieNode != None:
			subtree = getMaxSubtree(adjacList, tieNode)
			if faultedNode in subtree:
				path = findPathToFault(adjacList, tieNode, faultedNode)
				for lis in path:
					# print(lis)
					row = len(lis) - 1
					while row > -1:
						for recloser in reclosers:
							if recloser['from'] == lis[row]:
								if recloser['to'] == lis[row-1]:
									found = True
									bestReclosers.append(recloser)
									for key in tree2.keys():
										if tree2[key] == recloser:
											del (tree[key])
									break
							if recloser['to'] == lis[row]:
								if recloser['from'] == lis[row-1]:
									found = True
									bestReclosers.append(recloser)
									for key in tree2.keys():
										if tree2[key] == recloser:
											del (tree[key])
									break
						if found == True:
							break
						row -= 1
					if found == True:
						bestTies.append(tieLines.loc[row, 'name'])
						index += 1
						tree[str(biggestKey*10 + index)] = {'object':tieLines.loc[row, 'object'], 'phases':tieLines.loc[row, 'phases'], 'name':tieLines.loc[row, 'name'], 'from':tieLines.loc[row, 'from'], 'to':tieLines.loc[row, 'to']}
						tieLines.drop(tieLines.index[[row]])
						tree, tieLines, bestTies, bestReclosers = addTieLines(tree, tieLines, workDir, bestTies, bestReclosers)
			else:
				found = True
				bestTies.append(tieLines.loc[row, 'name'])
				index += 1
				tree[str(biggestKey*10 + index)] = {'object':tieLines.loc[row, 'object'], 'phases':tieLines.loc[row, 'phases'], 'name':tieLines.loc[row, 'name'], 'from':tieLines.loc[row, 'from'], 'to':tieLines.loc[row, 'to']}
				tieLines.drop(tieLines.index[[row]])
				tree, tieLines, bestTies, bestReclosers = addTieLines(tree, tieLines, workDir, bestTies, bestReclosers)
			if found == True:
				break
		entry += 1
	return tree, tieLines, bestTies, bestReclosers

# bestTies = []
# bestReclosers = []

# def safeInt(x):
# 	try: return int(x)
# 	except: return 0

# biggestKey = max([safeInt(x) for x in tree.keys()])
# tree[str(biggestKey*10)] = {'module':'powerflow','solver_method':'FBS'}
# attachments = []
# gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir)

# cutoffFault('C:/Users/granb/omf/omf/static/publicFeeders/ABECColumbia.omd', "824984")

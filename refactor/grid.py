#!/usr/bin/env python

import networkx as nx
import matplotlib as m
m.use('Agg')
import matplotlib.pyplot as p
import matplotlib.patheffects as pe
import re
import networkx as nx
import utility

class Grid:
	tree = None
	def __init__(self, glmString):
		tokens = self.tokenizeGlm(glmString)
		self.tree = self.parseTokenList(tokens)

	def toGraph(self):
		glmGraph = nx.Graph()
		nodeNodes = []
		for x in self.tree:
			if 'from' in self.tree[x] and 'to' in self.tree[x]:
				glmGraph.add_edge(self.tree[x]['from'],self.tree[x]['to'])
			if 'parent' in self.tree[x] and 'name' in self.tree[x]:
				glmGraph.add_edge(self.tree[x]['name'],self.tree[x]['parent'])
			if 'object' in self.tree[x] and self.tree[x]['object'] == 'node':
				nodeNodes.append(self.tree[x]['name'])
		nodeNodes = set(nodeNodes).intersection(set(glmGraph.nodes()))
		notNodes = set(glmGraph.nodes()) - nodeNodes
		layout = nx.spring_layout(glmGraph)
		fig = p.figure()
		nx.draw_networkx_nodes(glmGraph,layout,notNodes,alpha=0.7,node_size=150)
		nx.draw_networkx_nodes(glmGraph,layout,nodeNodes,alpha=0.7,node_color='b')
		nx.draw_networkx_edges(glmGraph,layout,alpha=0.9)
		# Labels only if we have few nodes:
		if len(glmGraph.nodes()) < 25:
			labels = nx.draw_networkx_labels(glmGraph,layout)
			for key in labels:
				p.setp(labels[key], path_effects=[pe.withStroke(linewidth=3, foreground="w")])
		p.axis('off')
		#p.title('PutMeHere!')
		return fig
		#TODO: If you want to show it, do p.show() and comment out the m.use('Agg') thing so we get Tcl back.

	def toD3json(self):
		#TODO: figure out how this damn thing works.
		node_group_dict = {'unknown':0}
		def toGraph(glmTree):
			def node_attrs(node_dict, group=None):
				attr_dict = {}
				if group:
					attr_dict['group'] = group;
				for key in node_dict:
					if key not in ['group', 'object']:
						try:
							attr_dict['_'+key] = node_dict[key]
						except TypeError:
							pass
				if 'object' in node_dict:
					attr_dict['_type'] = node_dict['object']
					if node_dict['object'] not in node_group_dict:
						node_group_dict[node_dict['object']] = len(node_group_dict)
					attr_dict['group'] = node_group_dict[node_dict['object']]
				else:
					attr_dict['group'] = node_group_dict['unknown']
				return attr_dict
			glmGraph = nx.Graph()
			nodeNodes = []
			for x in glmTree:
				if 'from' in glmTree[x] and 'to' in glmTree[x]:
					glmGraph.add_edge(glmTree[x]['from'],glmTree[x]['to'])
					# glmGraph.add_node(glmTree[x]['from'], group=1)
					# glmGraph.add_node(glmTree[x]['to'], group=2)
				elif 'parent' in glmTree[x] and 'name' in glmTree[x]:
					glmGraph.add_edge(glmTree[x]['name'],glmTree[x]['parent'])
					# glmGraph.add_node(glmTree[x]['name'], group=3)
					# glmGraph.add_node(glmTree[x]['parent'], group=4)
				if 'object' in glmTree[x] and glmTree[x]['object'] in ['triplex_meter', 'house', 'node', 'meter', 'load']:
					name = "unset"
					try:
						name = glmTree[x]['name']
					except KeyError:
						pass
					glmGraph.add_node(name, node_attrs(glmTree[x]))
			return glmGraph
		graph = toGraph(self.tree)
		# graph_json = {'nodes':map(lambda x:{'name':x[0],'group':x[1]['group'],(x:y) in x[1]},graph.nodes(data=True))}
		graph_json = {'nodes':map(lambda x:dict({'name':x[0]},**x[1]),graph.nodes(data=True))}
		
		ints_graph = nx.convert_node_labels_to_integers(graph, discard_old_labels=False)
		graph_edges = ints_graph.edges(data=True)
		# Build up edge dictionary in JSON format
		json_edges = list()
		for j, k, w in graph_edges:
			e = {'source' : j, 'target' : k}
			if any(map(lambda k: k=='weight', w.keys())):
				e['value'] = w['weight']
			else:
				e['value'] = 1
			json_edges.append(e)
		graph_json['links'] = json_edges
		return graph_json

	def tokenizeGlm(self, glmString):
	    # Get rid of http for stylesheets because we don't need it and it conflicts with comment syntax.
	    data = re.sub(r'http:\/\/', '', glmString)  
	    # Strip comments.
	    data = re.sub(r'\/\/.*\n', '', data)
	    # TODO: If the .glm creator has been lax with semicolons, add them back.
	    # Also strip non-single whitespace because it's only for humans:
	    data = data.replace('\n','').replace('\r','').replace('\t',' ')
	    # Tokenize around semicolons, braces and whitespace.
	    tokenized = re.split(r'(;|\}|\{|\s)',data)
	    # Get rid of whitespace strings.
	    basicList = filter(lambda x:x!='' and x!=' ', tokenized)
	    return basicList

	def parseTokenList(self, tokenList):
		# Tree variables.
		tree = {}
		guid = 0
		guidStack = []
		# Helper function to add to the current leaf we're visiting.
		def currentLeafAdd(key, value):
			current = tree
			for x in guidStack:
				current = current[x]
			current[key] = value
		# Helper function to turn a list of strings into one string with some decent formatting.
		# TODO: formatting could be nicer, i.e. remove the extra spaces this function puts in.
		def listToString(listIn):
			if len(listIn) == 0:
				return ''
			else:
				return reduce(lambda x,y:str(x)+' '+str(y),listIn[1:-1])
		# Pop off a full token, put it on the tree, rinse, repeat.
		while tokenList != []:
			# Pop, then keep going until we have a full token (i.e. 'object house', not just 'object')
			fullToken = []
			while fullToken == [] or fullToken[-1] not in ['{',';','}']:
				fullToken.append(tokenList.pop(0))
			# Work with what we've collected.
			if fullToken[-1] == ';':
				# Special case when we have zero-attribute items (like #include, #set, module).
				if guidStack == [] and fullToken != [';']:
					tree[guid] = {'omftype':fullToken[0],'argument':listToString(fullToken)}
					guid += 1
				# We process if it isn't the empty token (';')
				elif len(fullToken) > 1:
					currentLeafAdd(fullToken[0],listToString(fullToken))
			elif fullToken[-1] == '}':
				if len(fullToken) > 1:
					currentLeafAdd(fullToken[0],listToString(fullToken))
				guidStack.pop()
			elif fullToken[-1] == '{':
				currentLeafAdd(guid,{})
				guidStack.append(guid)
				guid += 1
				# Wrapping this currentLeafAdd is defensive coding so we don't crash on malformed glms.
				if len(fullToken) > 1:
					# Do we have a clock/object or else an embedded configuration object?
					if len(fullToken) < 4:
						currentLeafAdd(fullToken[0],fullToken[-2])
					else:
						currentLeafAdd('omfEmbeddedConfigObject', fullToken[0] + ' ' + listToString(fullToken))
		return tree

	def toGlmString(self):
		# Helper function: take a nested set of dicts and make them a string.
		def dictToString(inDict):
			# Helper function: given a single dict, concatenate it into a string.
			def gatherKeyValues(inDict, keyToAvoid):
				otherKeyValues = ''
				for key in inDict:
					if type(key) is int:
						# WARNING: RECURSION HERE
						# TODO (cosmetic): know our depth, and indent the output so it's more human readable.
						otherKeyValues += dictToString(inDict[key])
					elif key != keyToAvoid:
						otherKeyValues += (key + ' ' + inDict[key] + ';\n')
				return otherKeyValues
			# Handle the different types of dictionaries that are leafs of the tree root:
			if 'omftype' in inDict:
				return inDict['omftype'] + ' ' + inDict['argument'] + ';'
			elif 'module' in inDict:
				return 'module ' + inDict['module'] + ' {\n' + gatherKeyValues(inDict, 'module') + '};\n'
			elif 'clock' in inDict:
				return 'clock {\n' + gatherKeyValues(inDict, 'clock') + '};\n'
			elif 'object' in inDict:
				return 'object ' + inDict['object'] + ' {\n' + gatherKeyValues(inDict, 'object') + '};\n'
			elif 'omfEmbeddedConfigObject' in inDict:
				return inDict['omfEmbeddedConfigObject'] + ' {\n' + gatherKeyValues(inDict, 'omfEmbeddedConfigObject') + '};\n'
		output = ''
		for key in self.tree:
			output += dictToString(self.tree[key]) + '\n'
		return output

	def attachRecorders(self):
		#TODO: implement this
		pass

	def adjustTime(self, simLength, simLengthUnits):
		# translate LengthUnits to minutes.
		if simLengthUnits == 'minutes':
			lengthInSeconds = simLength * 60
			interval = 60
		elif simLengthUnits == 'hours':
			lengthInSeconds = 1440 * simLength
			interval = 1440
		elif simLengthUnits == 'days':
			lengthInSeconds = 86400 * simLength
			interval = 86400

		starttime = datetime.datetime(2000,1,1)
		stoptime = starttime + datetime.timedelta(seconds=lengthInSeconds)

		# alter the clocks and recorders:
		for x in self.tree:
			leaf = self.tree[x]
			if 'clock' in leaf:
				# Ick, Gridlabd wants time values wrapped in single quotes:
				leaf['starttime'] = "'" + str(starttime) + "'"
				leaf['stoptime'] = "'" + str(stoptime) + "'"
			if 'object' in leaf and leaf['object'] == 'recorder':
				leaf['interval'] = str(interval)
				leaf['limit'] = str(simLength)


def main():
	print 'testing this class.'
	inFile = open('../preDoe/testglms/Simple_System.glm', 'r')
	data = inFile.read()
	testGrid = Grid(data)
	utility.printNestDicts(testGrid.tree)
	print 'When we output to GLM we get ' + str(len(testGrid.toGlmString())) + ' lines.'
	figure = testGrid.toGraph()
	figure.savefig('test.png')
	print testGrid.toD3json()

if __name__ == '__main__':
	main()
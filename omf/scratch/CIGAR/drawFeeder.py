import omf
import sys
from matplotlib import pyplot as plt
import tempfile
from os.path import join as pJoin
import csv
import math
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx

# FNAME = 'smsSingle.glm'
# FNAME = 'dist_gen_solar_all.glm'
FNAME = 'ieee37node.glm'


# help(omf.feeder.parse)

feed = omf.feeder.parse(FNAME)

# All object types.
x = set()
for obj in feed.values():
	if 'object' in obj:
		x.add(obj['object'])
#print x

# Draw it.
# omf.feeder.latLonNxGraph(omf.feeder.treeToNxGraph(feed), labels=False, neatoLayout=True, showPlot=False)
# plt.savefig('blah.png')

def voltPlot(glmPath, workDir=None, neatoLayout=False):
	''' Draw a color-coded map of the voltage drop on a feeder.
	Returns a matplotlib object. '''
	tree = omf.feeder.parse(glmPath)

	#dictionary to hold info on lines present in glm
	edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator'], False)

	# # Get rid of schedules and climate and check for all edge types:
	for key in tree.keys():
		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
			del tree[key]
		obtype = tree[key].get("object","")
		if obtype == 'underground_line':
			edge_bools['underground_line'] = True
		elif obtype == 'overhead_line':
			edge_bools['overhead_line'] = True
		elif obtype == 'triplex_line':
			edge_bools['triplex_line'] = True
		elif obtype == 'transformer':
			edge_bools['transformer'] = True
		elif obtype == 'regulator':
			edge_bools['regulator'] = True

	# Make sure we have a voltDump:
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	tree[str(biggestKey*10)] = {"object":"voltdump","filename":"voltDump.csv"}
	tree[str(biggestKey*10 + 1)] = {"object":"currdump","filename":"currDump.csv"}
	# Line rating dumps
	tree[omf.feeder.getMaxKey(tree) + 1] = {
		'module': 'tape'
	}
	for key in edge_bools.keys():
		if edge_bools[key]:
			tree[omf.feeder.getMaxKey(tree) + 1] = {
				'object':'group_recorder', 
				'group':'"class='+key+'"',
				'limit':1,
				'property':'continuous_rating',
				'file':key+'_cont_rating.csv'
			}
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=[], workDir=workDir)
	# read voltDump values into a dictionary
	with open(pJoin(workDir,'voltDump.csv'),'r') as dumpFile:
		reader = csv.reader(dumpFile)
		reader.next() # Burn the header.
		keys = reader.next()
		voltTable = []
		for row in reader:
			rowDict = {}
			for pos,key in enumerate(keys):
				rowDict[key] = row[pos]
			voltTable.append(rowDict)
	# read currDump values into a dictionary
	with open(pJoin(workDir,'currDump.csv'),'r') as currDumpFile:
		reader = csv.reader(currDumpFile)
		reader.next() # Burn the header.
		keys = reader.next()
		currTable = []
		for row in reader:
			rowDict = {}
			for pos,key in enumerate(keys):
				rowDict[key] = row[pos]
			currTable.append(rowDict)
	# read line rating values into a single dictionary
	lineRatings = {}
	for key in edge_bools.keys():
		if edge_bools[key]:		
			with open(pJoin(workDir,key+'_cont_rating.csv'),'r') as ratingFile:
				reader = csv.reader(ratingFile)
				# loop past the header, 
				keys = []
				vals = []
				for row in reader:
					if '# timestamp' in row:
						keys = row
						i = keys.index('# timestamp')
						keys.pop(i)
						vals = reader.next()
						vals.pop(i)
				for pos,key in enumerate(keys):
					lineRatings[key] = abs(float(vals[pos]))
	edgeTupleRatings = {}
	for edge in lineRatings:
		for obj in tree.values():
			if obj.get('name') == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				ratingVal = lineRatings.get(edge)
				edgeTupleRatings[coord] = ratingVal
	# Calculate average node voltage deviation. First, helper functions.
	def digits(x):
		''' Returns number of digits before the decimal in the float x. '''
		return math.ceil(math.log10(x+1))
	def avg(l):
		''' Average of a list of ints or floats. '''
		return sum(l)/len(l)
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	# Tot it all up.
	nodeVolts = {}
	for row in voltTable:
		allVolts = []
		for phase in ['A','B','C']:
			phaseVolt = abs(float(row['volt'+phase+'_real']))
			if phaseVolt != 0.0:
				if digits(phaseVolt)>3:
					# Normalize to 120 V standard
					phaseVolt = phaseVolt*(120/feedVoltage)
				allVolts.append(phaseVolt)
		nodeVolts[row.get('node_name','')] = avg(allVolts)
		# Use float("{0:.2f}".format(avg(allVolts))) if displaying the node labels
	nodeNames = {}
	for key in nodeVolts.keys():
		nodeNames[key] = key
	# Add up currents.
	edgeCurrents = {}
	for row in currTable:
		phaseCurr = 0.0
		for phase in ['A','B','C']:
			phaseCurr += abs(float(row['curr'+phase+'_real']))
		edgeCurrents[row.get('link_name','')] = phaseCurr
	# create edgeCurrent copy with to and from tuple as keys for labeling
	edgeTupleCurrents = {}
	for edge in edgeCurrents:
		for obj in tree.values():
			if obj.get('name') == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				currVal = edgeCurrents.get(edge)
				edgeTupleCurrents[coord] = "{0:.2f}".format(currVal)
	#create edgeCurrents dict with values normalized per unit by line ratings
	edgeCurrentsPU = {}
	edgeTuplePower = {}
	edgeTupleCurrentsPU = {}
	for edge in edgeCurrents:
		for obj in tree.values():
			if obj.get('name') == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				lineVoltage = avg([nodeVolts.get(nodeFrom), nodeVolts.get(nodeTo)])
				lineCurrent = edgeCurrents.get(edge)
				lineRating = lineRatings.get(edge)
				currValPU = (lineVoltage*lineCurrent)/lineRating
				edgeTuplePower[coord] = "{0:.2f}".format((lineCurrent * lineVoltage)/1000)
				edgeCurrentsPU[edge] = currValPU
				edgeTupleCurrentsPU[coord] = "{0:.2f}".format(currValPU)
	# dict with to-from tuples as keys and names as values for debugging
	edgeTupleNames = {}
	for edge in edgeCurrents:
		for obj in tree.values():
			if obj.get('name') == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				edgeTupleNames[coord] = edge

	# Build the graph.
	fGraph = omf.feeder.treeToNxGraph(tree)
	voltChart = plt.figure(figsize=(15,15))
	plt.axes(frameon = 0)
	plt.axis('off')
	voltChart.gca().set_aspect('equal')
	plt.tight_layout()
	# Need to get edge names from pairs of connected node names.
	edgeNames = []
	for e in fGraph.edges():
		edgeNames.append(fGraph.edge[e[0]][e[1]].get('name','BLANK'))
	#set axes step equal
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
	edgeIm = nx.draw_networkx_edges(fGraph,
		pos = positions,
		edge_color = [edgeCurrents.get(n,1) for n in edgeNames],
		width = 1,
		edge_vmin = 0,
		edge_vmax = 2,
		edge_cmap = plt.cm.coolwarm)
	edgeLabelsIm = nx.draw_networkx_edge_labels(fGraph,
		pos = positions,
		edge_labels = edgeTupleRatings,
		font_size = 8)
	nodeIm = nx.draw_networkx_nodes(fGraph,
		pos = positions,
		node_color = [nodeVolts.get(n,1) for n in fGraph.nodes()],
		linewidths = 0,
		node_size = 30,
		vmin = 0,
		vmax = 2,
		cmap = plt.cm.coolwarm)
	# nodeLabelsIm = nx.draw_networkx_labels(fGraph,
	# 	pos = positions,
	# 	labels = nodeNames,
	# 	font_size = 8)

	plt.sci(nodeIm)
	# plt.clim(110,130)
	plt.colorbar()
	return voltChart

# Test code for parsing/modifying feeders.
# tree = omf.feeder.parse('smsSingle.glm')
# tree[35]['name'] = 'OH NO CHANGED'

chart = voltPlot(FNAME, neatoLayout=True)
chart.savefig("./VOLTOUT.png")
# from pprint import pprint as pp
# pp(chart)

# Viz it interactively.
# sys.path.append('../distNetViz/')
# import distNetViz
# distNetViz.viz(FNAME, forceLayout=True, outputPath=None)
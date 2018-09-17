import omf
import sys
from matplotlib import pyplot as plt
import tempfile
from os.path import join as pJoin
import csv
import math
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
import math

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
	edge_type_pow = ['transformer','regulator']

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
			# if key in edge_type_pow:
			# 	tree[omf.feeder.getMaxKey(tree) + 1] = {
			# 	'object':'group_recorder', 
			# 	'group':'"class='+key+'"',
			# 	'limit':1,
			# 	'property':'continuous_rating', #need to change to a property for nominal volt amps
			# 	'file':key+'_nom_power.csv'
			# }
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
	rating_in_VA = []
	for key1 in edge_bools.keys():
		if edge_bools[key1]:		
			with open(pJoin(workDir,key1+'_cont_rating.csv'),'r') as ratingFile:
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
				for pos,key2 in enumerate(keys):
					lineRatings[key2] = abs(float(vals[pos]))
					if key1 in edge_type_pow:
						rating_in_VA.append(key2)
			# if key1 in edge_type_pow:
			# 	with open(pJoin(workDir,key1+'_nom_power.csv'),'r') as powerFile:
			# 		reader = csv.reader(ratingFile)
			# 		keys = []
			# 		vals = []
			# 		for row in reader:
			# 			if '# timestamp' in row:
			# 				keys = row
			# 				i = keys.index('# timestamp')
			# 				keys.pop(i)
			# 				vals = reader.next()
			# 				vals.pop(i)
			# 		for pos,key2 in enumerate(keys):
			# 			line_power[key2] = abs(float(vals[pos]))
			# 			edge_name_pow_bool[key2] = True
	#edgeTupleRatings = lineRatings copy with to-from tuple as keys for labeling
	edgeTupleRatings = {}
	for edge in lineRatings:
		for obj in tree.values():
			if obj.get('name','').replace('"','') == edge:
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
			realVolt = abs(float(row['volt'+phase+'_real']))
			imagVolt = abs(float(row['volt'+phase+'_imag']))
			phaseVolt = math.sqrt((realVolt ** 2) + (imagVolt ** 2))
			if phaseVolt != 0.0:
				# Normalize to 120 V standard
				phaseVolt = 2 * (phaseVolt/feedVoltage)
				allVolts.append(phaseVolt)
		nodeVolts[row.get('node_name','')] = avg(allVolts)
		# Use float("{0:.2f}".format(avg(allVolts))) if displaying the node labels
	nodeNames = {}
	for key in nodeVolts.keys():
		nodeNames[key] = key
	# find edge currents by parsing currdump
	edgeCurrentSum = {}
	edgeCurrentMax = {}
	for row in currTable:
		allCurr = []
		for phase in ['A','B','C']:
			realCurr = abs(float(row['curr'+phase+'_real']))
			imagCurr = abs(float(row['curr'+phase+'_imag']))
			phaseCurr = math.sqrt((realCurr ** 2) + (imagCurr ** 2))
			allCurr.append(phaseCurr)
		edgeCurrentSum[row.get('link_name','')] = sum(allCurr)
		edgeCurrentMax[row.get('link_name','')] = max(allCurr)
	# When just showing current as labels, use sum of the three lines' current values, when showing the per unit values (current/rating), use the max of the three

	#edgeTupleCurrents = edgeCurrents copy with to-from tuple as keys for labeling
	edgeTupleCurrents = {}
	#edgeValsPU = values normalized per unit by line ratings
	edgeValsPU = {}
	#edgeTupleValsPU = edgeValsPU copy with to-from tuple as keys for labeling
	edgeTupleValsPU = {}
	#edgeTuplePower = dict with to-from tuples as keys and sim power as values for debugging
	edgeTuplePower = {}
	#edgeTupleNames = dict with to-from tuples as keys and names as values for debugging
	edgeTupleNames = {}
	for edge in edgeCurrentSum:
		for obj in tree.values():
			obname = obj.get('name','').replace('"','')
			if obname == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				coord = (nodeFrom, nodeTo)
				currVal = edgeCurrentSum.get(edge)
				voltVal = avg([nodeVolts.get(nodeFrom), nodeVolts.get(nodeTo)])
				lineRating = lineRatings.get(edge)
				if obname in rating_in_VA:
					edgePerUnitVal = (voltVal * edgeCurrentMax.get(edge))/lineRating
				else:
					edgePerUnitVal = (edgeCurrentMax.get(edge))/lineRating
				edgeTupleCurrents[coord] = "{0:.2f}".format(currVal)
				edgeTuplePower[coord] = "{0:.2f}".format((currVal * voltVal)/1000)
				edgeValsPU[edge] = edgePerUnitVal
				edgeTupleValsPU[coord] = "{0:.2f}".format(edgePerUnitVal)
				edgeTupleNames[coord] = edge

	#define which dict will be used for edge line color
	edgeColors = edgeValsPU
	#define which dict will be used for edge label
	edgeLabels = edgeTupleCurrents

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
		edgeNames.append((fGraph.edge[e[0]][e[1]].get('name','BLANK')).replace('"',''))
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
		edge_color = [edgeColors.get(n,1) for n in edgeNames],
		width = 1,
		edge_vmin = 0,
		edge_vmax = 2,
		edge_cmap = plt.cm.coolwarm)
	edgeLabelsIm = nx.draw_networkx_edge_labels(fGraph,
		pos = positions,
		edge_labels = edgeLabels,
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
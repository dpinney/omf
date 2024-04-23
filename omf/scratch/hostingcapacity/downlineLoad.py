import networkx as nx
from pathlib import Path
import pandas as pd
import math
import warnings
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import json

import omf
from omf.solvers import opendss
import os
from omf.models import hostingCapacity

def myConvertOMD(pathToOmdFile):
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = nx.DiGraph()
	for key in tree:
		#Account for nodes that are missing names when creating edges
		item = tree[key]
		print( item )
		try:
			sourceEdge = item['source']['name']
		except KeyError:
			try:
				sourceEdge = str(item['target']['name']) + ' Source'
			except KeyError:
				sourceEdge = str(item['source']) + ' Missing Name'
		try:
			targetEdge = item['target']['name']
		except KeyError:
			try:
				targetEdge = item['target']['name'] + ' Target'
			except KeyError:
				targetEdge = str(item['target']) + ' Missing Name'
		#nxG.add_edge(key['source']['name'], key['target']['name'])
		nxG.add_edge(sourceEdge, targetEdge)
		nxG.nodes[sourceEdge]['pos'] = (float(item['source']['y']), float(item['source']['x']))
		nxG.nodes[targetEdge]['pos'] = (float(item['target']['y']), float(item['target']['x']))
		try:
			nxG.nodes[sourceEdge]['type'] = item['source']['objectType']
		except KeyError:
			nxG.nodes[sourceEdge]['type'] = 'Undefined'
		try:
			nxG.nodes[targetEdge]['type'] = item['target']['objectType']
		except KeyError:
			nxG.nodes[targetEdge]['type'] = 'Undefined'
	for nodeToChange in nx.get_node_attributes(nxG, 'pos'):
		#nxG.node[nodeToChange]['pos'] = (latitudeCenter + nxG.node[nodeToChange]['pos'][1]/latitude_max, longitudeCenter 
		#								+ nxG.node[nodeToChange]['pos'][0]/longitude_max)
		#print(nxG.node[nodeToChange]['pos'][1], nxG.node[nodeToChange]['pos'][0])
		#print(statePlaneToLatLon(nxG.node[nodeToChange]['pos'][1], nxG.node[nodeToChange]['pos'][0]))
		nxG.nodes[nodeToChange]['pos'] = omf.geo.statePlaneToLatLon(nxG.nodes[nodeToChange]['pos'][1], nxG.nodes[nodeToChange]['pos'][0])
	return nxG

def my_NetworkPlot(filePath, figsize=(20,20), output_name='networkPlot.png', show_labels=True, node_size=300, font_size=8):
	''' Plot the physical topology of the circuit.
	Returns a networkx graph of the circuit as a bonus. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	opendss.runDSS(filePath)
	coords = my_GetCoords(filePath)
	opendss.runDssCommand(f'export voltages "{dssFileLoc}/volts.csv"')
	volts = pd.read_csv(dssFileLoc + '/volts.csv')

	# JENNY - Deleted radius
	coords.columns = ['Bus', 'X', 'Y']
	G = nx.Graph()
	# Get the coordinates.
	pos = {}
	for index, row in coords.iterrows():
		try:
			bus_name = str(int(row['Bus']))
		except:
			bus_name = row['Bus']
		G.add_node(bus_name, pos=(float(row['X']), float(row['Y'])))
		pos[bus_name] = (float(row['X']), float(row['Y']))

	# Get the connecting edges using Pandas.
	lines = opendss.dss.utils.lines_to_dataframe()
	edges = []
	for index, row in lines.iterrows():
		#HACK: dss upercases everything in the coordinate output.
		bus1 = row['Bus1'].split('.')[0].upper()
		bus2 = row['Bus2'].split('.')[0].upper()
		edges.append((bus1, bus2))
	G.add_edges_from(edges)

	# JENNY ?? - WILL THERE BE BUSES WITH LOADS WITHOUT COORDS?
	# Remove buses withouts coords
	no_pos_nodes = set(G.nodes()) - set(pos)
	if len(no_pos_nodes) > 0:
		warnings.warn(f'Node positions missing for {no_pos_nodes}')
	G.remove_nodes_from(list(no_pos_nodes))


	# We'll color the nodes according to voltage.
	volt_values = {}
	labels = {}
	for index, row in volts.iterrows():
		if row['Bus'].upper() in [x.upper() for x in pos]:
			volt_values[row['Bus']] = row[' pu1']
			labels[row['Bus']] = row['Bus']
	colorCode = [volt_values.get(node, 0.0) for node in G.nodes()]


	# Start drawing.
	plt.figure(figsize=figsize) 
	nodes = nx.draw_networkx_nodes(G, pos, node_color=colorCode, node_size=node_size)
	edges = nx.draw_networkx_edges(G, pos)
	if show_labels:
		nx.draw_networkx_labels(G, pos, labels, font_size=font_size)
	plt.colorbar(nodes)
	plt.legend()
	plt.title('Network Voltage Layout')
	plt.tight_layout()
	plt.savefig(dssFileLoc + '/' + output_name)
	plt.clf()
	return G

def omd_to_nx_fulldata( dssFilePath, tree=None ):
	''' Combines dss_to_networkX and opendss.networkPlot together.

	Creates a networkx directed graph from a dss files. If a tree is provided, build graph from that instead of the file.
	Creates a .png picture of the graph.
	Adds data to certain DSS node types ( loads )
	
	args:
		filepath (str of file name):- dss file path
		tree (list): None - tree representation of dss file
		output_name (str):- name of png
		show_labels (bool): true - show node label names
		node_size (int): 300 - size of node circles in png
		font_size (int): 8 - font size for png labels
	return:
		A networkx graph of the circuit 
	'''
	if tree == None:
		tree = opendss.dssConvert.dssToTree( dssFilePath )

	G = nx.DiGraph()
	pos = {}

	setbusxyList = [x for x in tree if '!CMD' in x and x['!CMD'] == 'setbusxy']
	x_coords = [x['x'] for x in setbusxyList if 'x' in x]
	y_coords = [x['y'] for x in setbusxyList if 'y' in x]
	bus_names = [x['bus'] for x in setbusxyList if 'bus' in x]
	for bus, x, y in zip( bus_names, x_coords, y_coords):
		G.add_node(bus, pos=(x, y))
		pos[bus] = (x, y)

	lines = [x for x in tree if x.get('object', 'N/A').startswith('line.')]
	bus1_lines = [x.split('.')[0] for x in [x['bus1'] for x in lines if 'bus1' in x]]
	bus2_lines = [x.split('.')[0] for x in [x['bus2'] for x in lines if 'bus2' in x]]
	edges = []
	for bus1, bus2 in zip( bus1_lines, bus2_lines):
		edges.append( (bus1, bus2) )
	G.add_edges_from(edges)

	# Need edges from bus --- trasnformr info ---> load
	transformers = [x for x in tree if x.get('object', 'N/A').startswith('transformer.')]
	transformer_bus_names = [x['buses'] for x in transformers if 'buses' in x]
	bus_to_transformer_pairs = {}
	for transformer_bus in transformer_bus_names:
		strip_paren = transformer_bus.strip('[]')
		split_buses = strip_paren.split(',')
		bus = split_buses[0].split('.')[0]
		transformer_name = split_buses[1].split('.')[0]
		bus_to_transformer_pairs[transformer_name] = bus
	
	loads = [x for x in tree if x.get('object', 'N/A').startswith('load.')] # This is an orderedDict
	load_names = [x['object'].split('.')[1] for x in loads if 'object' in x and x['object'].startswith('load.')]
	load_transformer_name = [x.split('.')[0] for x in [x['bus1'] for x in loads if 'bus1' in x]]

	# Connects loads to buses via transformers
	labels = {}
	for load_name, load_transformer in zip(load_names, load_transformer_name):
    # Add edge from bus to load, with transformer name as an attribute
		if load_transformer in bus_to_transformer_pairs:
			bus = bus_to_transformer_pairs[load_transformer]
			G.add_edge(bus, load_name, transformer=load_transformer)
		else:
			G.add_edge(load_transformer, load_name )
		pos[load_name] = pos[load_transformer]
		# print(f"load_name: {load_name}, pos[load_name]: { pos[load_name]}")
		labels[load_name] = load_name
	# TEMP: Remove transformer nodes added from coordinates. Transformer data is edges, not nodes.
	for transformer_name in load_transformer_name:
		if transformer_name in G.nodes:
			G.remove_node( transformer_name )
			pos.pop( transformer_name )

	# print( pos.keys() )
	
	load_kw = [x['kw'] for x in loads if 'kw' in x]
	for load, kw in zip( load_names, load_kw ):
		G.nodes[load]['kw'] = kw
	
	return [G, pos, labels]

def drawNXGraph(G, pos, outputPath, labels: list=[], colorCode: list=[], figSize=(20,20), nodeSize: int=300 , fontSize: int=8):

	# Start drawing.
	plt.figure(figsize=figSize) 
	nodes = nx.draw_networkx_nodes(G, pos, node_size=nodeSize)
	edges = nx.draw_networkx_edges(G, pos)
	if len(labels) > 0:
		nx.draw_networkx_labels(G, pos, labels, font_size=fontSize)
	plt.colorbar(nodes)
	plt.legend()
	plt.title('Network Voltage Layout')
	plt.tight_layout()
	plt.savefig(outputPath)
	plt.clf()

if __name__ == '__main__':
	'''
	Wants: 
	- Directed graph
	-> Can have it be optional.
	- Buses, loads as nodes
	- Transformers not as nodes, but as edges
	- Data for loads/transformers/buses be attributes

	Sanity Checks:
	Test descendents of bus1002 

	['bus1003', 'bus1004', 'bus1005', 'bus1006', 'bus1007', 'bus1008', 'bus1009', 'bus1010',
	'bus1011', 'bus1012', 'bus1013', 'bus1014', 'bus1015', 'bus1016', 'bus1017',
	'load_1003', 'load_1004', 'load_1005', 'load_1006', 'load_1007', 'load_1008', 'load_1009', 'load_1010',
	'load_1011' 'load_1012', 'load_1013', 'load_1014', 'load_1015', 'load_1016', 'load_1017']
	'''

	'''
	#################################################### 
	Func 1: convertOmd(pathToOmdFile) in geo.py
	Issue 1: Not directed.
	Issue 2: Function gets tree from "links" key. for iowa240.clean.dss.omd, there's nothing in links -> FAILS

	Test:
		coGraph = omf.geo.convertOmd ( starting_omd_test_file )
	Output:
		Graph with 0 nodes and 0 edges
	
	Attempted fixes: 
	- Making it directed and using the "tree" key

	Test: myConvertOMD( starting_omd_test_file )
	Output: 	
		File "/home/jenny/nreca/omf/omf/scratch/hostingcapacity/downlineLoad.py", line 39, in myConvertOMD
			sourceEdge = str(item['source']) + ' Missing Name'
		KeyError: 'source'

	# During handling of the above exception, another exception occurred:

	# Traceback (most recent call last):
	#   File "/home/jenny/nreca/omf/omf/scratch/hostingcapacity/again.py", line 20, in convertOmd
	#     sourceEdge = str(item['target']['name']) + ' Source'
	# KeyError: 'target'

	# Summary: Fails because of the other lines.. its not designed to deal with them. Would need to be modified but is used in other places
	####################################################

	####################################################
	# Func 1: treeToNxGraph in Feeder.py
	# Issue 1: Has nodes that shouldn't be there
	# graph nodes from omf.feeder.treeToNxGraph function:  ['clear', '240_node_test_system', 'source', 'eq_source_bus', 'oh_3p_type1', 'oh_2p_type2', 'oh_1p_type2', 'oh_3p_type5', 'oh_1p_type5', 'ug_3p_type1', 'ug_3p_type2', 'ug_1p_type2' .. 'reg_contr_a', 'reg_contr_b', 'reg_contr_c', 'cap_201', 'cap_301', 'makebuslist', 'set']
	# Issue 2: no descendents, no edges? Even though I specified a directed graph?
	#
	tree = omf.feeder.parse(beginning_test_file.resolve())
	tree = opendss.dssConvert.omdToTree( beginning_test_file.resolve() )
	with open(beginning_test_file) as f:
		feederJson = json.load(f)
	tree = feederJson.get("tree",{})
	g2 = omf.feeder.treeToNxGraph( tree, digraph=True )
	print( "graph nodes from omf.feeder.treeToNxGraph function: ", g2.nodes )
	Has data that doesn't need to be in here but its ok. but idk what the edges are..
	test_descendents_bus_list = sorted(nx.descendants(g2, 't_bus1004_l'))
	Even though I specified a digraph - this bus has no descendants even though it should.
	print( g2.get_edge_data('t_bus1004_l', 'load_1004') ) - THIS PRINTS NONE... that's awkward...

	Summary: Also failed. Would need to be modified but is used in other places
	####################################################

	####################################################
	# Func 3: dss_to_networkx in dssConvert
	tree = opendss.dssConvert.omdToTree( beginning_test_file.resolve() ) # this tree is a list
	opendss.dssConvert.treeToDss(tree, Path(modelDir, circuit_file))

	# This graph is directed
	# But this has a lot of other stuff. The other one is just buses which I think we want...
	# Copied and pasted here to get physical drawing - it is SO OFF!!!!!
	# dss_to_nx.png <- ????
	# dssConvert_graph = dss_to_networkx( os.path.join( modelDir, circuit_file), tree )
	# print( "info about graph made from dss_to_networkx: ", dssConvert_graph )
	# test_descendents_bus_list = sorted(nx.descendants(dssConvert_graph, 't_bus1004_l'))
	# print( dssConvert_graph.get_edge_data('t_bus1004_l', 'load_1004') ) #PRINTS NONE -- THATS TOUGH
	# Doesn't have the loads or edges for them, same issue as networkPlot
	# but also, this visually for some reason is SO OFF? NetworkPlot isn't

	Only reference is function: get_subtree_obs - and this function isn't used anywhere.
	I feel like... it should be deleted to reduce confusion in the future.

	####################################################
	# Funct 4: networkPlot in __init__ in solvers/opendss
	#  Issue 1: Undirected
	# Issue 2: my_NetworkPlot and my_GetCoords both need to be changed to remove radius

	my_NP_graph = my_NetworkPlot( os.path.join( modelDir, circuit_file) )
	print( "info about graph made from networkplot: ", my_NP_graph )
	# networkPlot.png - looks like how I want it to look. This is a good sign

	# Gotta make it directed.
	# Gotta add loads/load data instead of transformers
	Lets build up from here
	Isn't used anywhere but has the best picture so don't want to delete

	# Simply changed it to directed doesn't work.
	# Issue 1: 
	# netPlotDirected - WHAT HAPPENED?
	# Issue 2: Dependents aren't there still.

	another major issue: myCoords and openDSS cmds don't work for me
	because of the linux capital directory issue.
	'''

	'''
	Planning new function from what I have now: omd_to_nx
	- Want to have the drawing like the original networkX
	- Want hosting capacity coloring
	- Want attributes for nodes/edges ( optional? )
	- Get rid of volt stuff
	'''

	modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')
	starting_omd_test_file = Path( omf.omfDir, 'static', 'publicFeeders', 'iowa240.clean.dss.omd')
	tree = opendss.dssConvert.omdToTree( starting_omd_test_file )
	opendss.dssConvert.treeToDss(tree, Path(modelDir, 'downlineLoad.dss'))
	graphList = omd_to_nx_fulldata( Path(modelDir, 'downlineLoad.dss') )
	graph = graphList[0]
	pos = graphList[1] # <- keys are str, not nodes
	posFromGraph = nx.get_node_attributes(graph, 'pos')

	print( pos.keys() )
	print( "posFromGraph['bus1002']: ", posFromGraph['bus1002'] )

	print("posFromGraph['load_1003']: ", posFromGraph['load_1003'] )


	drawNXGraph( graph, posFromGraph, Path( modelDir, "myplot.png"), graphList[2] )

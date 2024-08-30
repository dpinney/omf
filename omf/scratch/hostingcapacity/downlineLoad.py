import networkx as nx
from pathlib import Path
import pandas as pd
import math
import warnings
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import numpy as np
import json
import os

import omf
from omf.solvers import opendss
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

def my_GetCoords(dssFilePath):
	'''Takes in an OpenDSS circuit definition file and outputs the bus coordinates as a dataframe.'''
	dssFileLoc = os.path.dirname(dssFilePath)
	opendss.runDSS(dssFilePath)
	opendss.runDssCommand(f'export buscoords "{dssFileLoc}/coords.csv"')
	coords = pd.read_csv(dssFileLoc + '/coords.csv', header=None)
	# JENNY - Deleted Radius and everything after.
	coords.columns = ['Element', 'X', 'Y']
	return coords

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

	for key in pos.keys():
		print( "type(key): in networkplot: ", type(key) )
		break

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

def dss_to_nx_fulldata( dssFilePath, tree=None, fullData = True ):
	''' Combines dss_to_networkX and opendss.networkPlot together.

	Creates a networkx directed graph from a dss files. If a tree is provided, build graph from that instead of the file.
	Adds data to certain DSS node types ( loads )
	
	args:
		filepath (str of file name):- dss file path
		tree (list): None - tree representation of dss file
	return:
		A networkx graph of the circuit 
	'''
	if tree == None:
		tree = opendss.dssConvert.dssToTree( dssFilePath )

	G = nx.MultiDiGraph()

	# A MultiDiGraph allows for multiple edges between the same nodes
	# Chosen because of multiple transformers between 2 of the same nodes.
	# Edges have a u, v, and key value. u, v = node1, node2. Key is a unique identifier.
	# line.x, transformer.y <- x and y are the unique key values, their "names" so to speak.

	pos = {}

	# Add nodes for buses
	setbusxyList = [x for x in tree if '!CMD' in x and x['!CMD'] == 'setbusxy']
	x_coords = [x['x'] for x in setbusxyList if 'x' in x]
	y_coords = [x['y'] for x in setbusxyList if 'y' in x]
	bus_names = [x['bus'] for x in setbusxyList if 'bus' in x]
	for bus, x, y in zip( bus_names, x_coords, y_coords):
		float_x = float(x)
		float_y = float(y)
		G.add_node(bus, pos=(float_x, float_y))
		pos[bus] = (float_x, float_y)

	# Add edges from lines
	# new object=line.645646 bus1=645.2 bus2=646.2 phases=1 linecode=mtx603 length=300 units=ft
	# line.x <- is this the name?
	lines = [x for x in tree if x.get('object', 'N/A').startswith('line.')]
	lines_bus1 = [x.split('.')[0] for x in [x['bus1'] for x in lines if 'bus1' in x]]
	lines_bus2 = [x.split('.')[0] for x in [x['bus2'] for x in lines if 'bus2' in x]]
	lines_name = [x.split('.')[1] for x in [x['object'] for x in lines if 'object' in x]]
	edges = []
	for bus1, bus2, name in zip(lines_bus1, lines_bus2, lines_name ):
		edges.append( (bus1, bus2, {'key': name}) )
	G.add_edges_from( edges )

	# Need to add data for lines
	# some lines have "switch"
	# How to add data when sometimes there sometimes not
	# print( "G.edges: ", G.edges(data=True) )
	# G.edges:  [('rg60', '632', {'key': '650632'})
	
	# If there is a transformer tied to a load, we get it from here.
	loads = [x for x in tree if x.get('object', 'N/A').startswith('load.')] # This is an orderedDict
	load_names = [x['object'].split('.')[1] for x in loads if 'object' in x and x['object'].startswith('load.')]
	load_bus = [x.split('.')[0] for x in [x['bus1'] for x in loads if 'bus1' in x]]
	for load, bus in zip(load_names, load_bus):
		pos_tuple_of_bus = pos[bus]
		G.add_node(load, pos=pos_tuple_of_bus)
		pos[load] = pos_tuple_of_bus

	if fullData:	
		# Attributes for all loads
		load_phases = [x['phases'] for x in loads if 'phases' in x]
		load_conn = [x['conn'] for x in loads if 'conn' in x]
		load_kv = [x['kv'] for x in loads if 'kv' in x]
		load_kw = [x['kw'] for x in loads if 'kw' in x]
		load_kvar = [x['kvar'] for x in loads if 'kvar' in x]
		for load, phases, conn, kv, kw, kvar in zip( load_names, load_phases, load_conn, load_kv, load_kw, load_kvar):
			G.nodes[load]['phases'] = phases
			G.nodes[load]['conn'] = conn
			G.nodes[load]['kv'] = kv
			G.nodes[load]['kw'] = kw
			G.nodes[load]['kvar'] = kvar

	print( G.nodes )

		# Need edges from bus --- transformer info ---> bus
	transformers = [x for x in tree if x.get('object', 'N/A').startswith('transformer.')]
	transformer_buses = [x['buses'] for x in transformers if 'buses' in x]
	print( "transformer_buses: ", transformer_buses )
	transformer_buses_names_split = [[prefix.split('.')[0].strip() for prefix in sublist.strip('[]').split(',')] for sublist in transformer_buses]
	print( "transformer_buses_names_split: ", transformer_buses_names_split)
	transformer_name = [x.split('.')[1] for x in [x['object'] for x in transformers if 'object' in x]]
	print( "transformer_name: ", transformer_name)
	transformer_edges = []
	for bus_pair, t_name in zip(transformer_buses_names_split, transformer_name):
		if bus_pair[0] and bus_pair[1] in G.nodes:
			transformer_edges.append ( (bus_pair[0], bus_pair[1], {'key': t_name}) )
	G.add_edges_from(transformer_edges)

	# Need to add data for transformers
	# Some have windings.
	
	# if fullData:
	# 	#  %loadloss=0.01
	# 	transformer_edges_with_attributes = {}
	# 	transformer_phases = [x['phases'] for x in lines if 'phases' in x]
	# 	transformer_bank = [x['bank'] for x in lines if 'bank' in x]
	# 	transformer_xhl = [x['xhl'] for x in lines if 'xhl' in x]
	# 	transformer_kvas = [x['kvas'] for x in lines if 'kvas' in x]
	# 	transformer_kvs = [x['kvs'] for x in lines if 'kvs' in x]
	# 	transformer_loadloss = [x['loadloss'] for x in lines if 'loadloss' in x]
	# 	for t_edge, phase, bank, xhl_val, kvas_val, kvs_val, loadloss_val in zip(transformer_edges, transformer_phases, transformer_bank, transformer_xhl, transformer_kvas, transformer_kvs, transformer_loadloss):
	# 			t_edge_nodes = (t_edge[0], t_edge[1])
	# 			transformer_edges_with_attributes[t_edge_nodes] = { "phases": phase, "bank": bank, "xhl": xhl_val, "kvas": kvas_val, "kvs": kvs_val, "loadloss": loadloss_val }
	# 			print( '{ "phases": phase, "bank": bank, "xhl": xhl_val, "kvas": kvas_val, "kvs": kvs_val, "loadloss": loadloss_val } ')
	# 			print( "t_edge_nodes: ", t_edge_nodes )
	# 	nx.set_edge_attributes( G, transformer_edges_with_attributes )

	# 	# buses=[650.2,rg60.2] phases=1 bank=reg1 xhl=0.01 kvas=[1666,1666] kvs=[2.4,2.4] %loadloss=0.01
	# 	print( G[ "633"]["634"]["phases"] )
	# 	print( G[ "633"]["634"]["bank"] )
	# 	print( G[ "633"]["634"]["xhl"] )
	# 	print( G[ "633"]["634"]["kvas"] )
	# 	print( G[ "633"]["634"]["kvs"] )
	# 	print( G[ "633"]["634"]["loadloss"] )

	# Are there generators? If so, find them and add them as nodes. Their location is the same as buses.
  # Generators have generator.<x> like solar_634 <- should i save this?
	# loadshape?
	generators = [x for x in tree if x.get('object', 'N/A').startswith('generator.')]
	gen_bus1 = [x.split('.')[0] for x in [x['bus1'] for x in lines if 'bus1' in x]]
	gen_names = [x['object'].split('.')[1] for x in generators if 'object' in x and x['object'].startswith('generator.')]
	gen_phases = [x['phases'] for x in generators if 'phases' in x]
	gen_kv = [x['kv'] for x in generators if 'kv' in x]
	gen_kw = [x['kw'] for x in generators if 'kw' in x]
	gen_pf = [x['pf'] for x in generators if 'pf' in x]
	gen_yearly = [x['yearly'] for x in generators if 'yearly' in x]

	for gen, bus_for_positioning, phases, kv, kw, pf, yearly in zip( gen_names, gen_bus1, gen_phases, gen_kv, gen_kw, gen_pf, gen_yearly ):
		G.add_node( gen, pos=pos[bus_for_positioning] )
		# Need to add gen betwen bus and node.
		# but if what is between them is a transformer, then it'll get removed. then there would be an edge between a deleted node and the generator node.. it has to between the bus.. now im confused.
		G.nodes[gen]['phases'] = phases
		G.nodes[gen]['kv'] = kv
		G.nodes[gen]['kw'] = kw
		G.nodes[gen]['pf'] = pf
		G.nodes[gen]['yearly'] = yearly
	return G

def drawNXGraph(G, pos, outputPath, colorCode = [], labels: list=[], figSize=(20,20), nodeSize: int=300 , fontSize: int=8):
	# Start drawing.
	plt.figure(figsize=figSize) 
	ax = plt.gca() # Get the current axes
	if len(colorCode) != 0:
		nodes = nx.draw_networkx_nodes(G, pos, node_color=colorCode, node_size=nodeSize, cmap=plt.get_cmap('viridis'), ax=ax)
		plt.colorbar( label='Node Values', ax=ax)
	else:
		nodes = nx.draw_networkx_nodes(G, pos, node_size=nodeSize, ax=ax)
	edges = nx.draw_networkx_edges(G, pos, ax=ax)
	if len(labels) > 0:
		nx.draw_networkx_labels(G, pos, labels, font_size=fontSize, ax=ax)
		# nx.draw_networkx_labels(G, pos, labels, font_size=fontSize, bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.1'), ax=ax)

	plt.legend()
	plt.title('Network Voltage Layout')
	plt.tight_layout()
	plt.savefig(outputPath)
	plt.clf()

if __name__ == '__main__':
	''' Sanity Checks
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

	''' Going through old functions
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

	''' Planning new function from what I have now: omd_to_nx
	- Want to have the drawing like the original networkX
	- Want hosting capacity coloring
	- Want attributes for nodes/edges ( optional? )
	- Get rid of volt stuff
	'''

	########## IOWA ##########

	########## Creating Iowa Graph - Iowa240
	modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')
	starting_omd_test_file = Path( omf.omfDir, 'static', 'publicFeeders', 'iowa240.clean.dss.omd')
	tree = opendss.dssConvert.omdToTree( starting_omd_test_file )
	opendss.dssConvert.treeToDss(tree, Path(modelDir, 'downlineLoad.dss'))
	nx_data = opendss.dss_to_nx_fulldata( Path(modelDir, 'downlineLoad.dss') )
	iowa240Graph = nx_data[0]
	iowa240Pos = nx_data[1]
	labels = {}
	for node in iowa240Graph.nodes:
		labels[node] = node
	drawNXGraph(iowa240Graph, iowa240Pos, Path(modelDir, "iowa.png"), labels=labels)
	
	########## Downline Load of Iowa - Iowa240
	buses = opendss.get_all_buses( os.path.join( modelDir, 'downlineLoad.dss') )
	buses_output = {}
	iowa_kw = nx.get_node_attributes(iowa240Graph, 'kw')
	iowa_objects = nx.get_node_attributes(iowa240Graph, 'object')
	# Check if they are buses
	for bus in buses:
		if bus in iowa240Graph.nodes:
			kwSum = 0
			get_dependents = sorted(nx.descendants(iowa240Graph, bus))
			for dependent in get_dependents:
				if dependent in iowa_kw.keys() and iowa_objects[dependent] == 'load':
					kwSum += float(iowa_kw[dependent])
			buses_output[bus] = kwSum
	# print( "\n buses output for kw from iowa240: ", buses_output )

	########## Test Line Data - Iowa240
	# new object=line.cb_101 bus1=bus1.1.2.3 bus2=bus1001.1.2.3 phases=3 switch=true r1=0.0001 r0=0.0001 x1=0 x0=0 c1=0 c0=0
	# new object=line.l_3161_3162 bus1=bus3161.3 bus2=bus3162.3 phases=1 length=176 units=ft linecode=ug_1p_type2 seasons=1 ratings=[400] normamps=400 emergamps=600
	line_name_iowa240 = nx.get_edge_attributes(iowa240Graph, 'line_name')
	phases_iowa240 = nx.get_edge_attributes(iowa240Graph, 'phases')

	transformer_1_iowa240 = nx.get_edge_attributes(iowa240Graph, 'transformer_1')
	# print( transformer_1_iowa240 )

	# print( iowa240Graph.edges('bus3160') )

	# switch_iowa240 = nx.get_edge_attributes(iowa240Graph, 'switch')
	# print( "\nswitch_iowa240: ", switch_iowa240)
	# length_iowa240 = nx.get_edge_attributes(iowa240Graph, 'length')
	# print( "\nlength_iowa240: ", length_iowa240)

	# length_test = ( 'bus3161', 'bus3162' )
	# if length_test in length_iowa240:
	# 	print( "correct length line in length edge results")

	# switch_test = ('bus1', 'bus1001')
	# if switch_test in switch_iowa240:
	# 	print( "correct switch line in switch edge results")

	# if switch_test not in length_iowa240:
	# 	print( "switch line is not in length line")

	########## Test Transformer Data
	# new object=transformer.t_2014 windings=3 buses=[bus2014.2.0,t_bus2014_l.1.0,t_bus2014_l.0.2] phases=1 xhl=3.24 xht=3.24 xlt=2.16 conns=[wye,wye,wye] kvs=[7.9677,0.12,0.12] kvas=[37.5,37.5,37.5] taps=[1,1,1] %rs=[1.8,3.6,3.6]

	# transformer_name_iowa240 = nx.get_edge_attributes( iowa240Graph, 'transformer_name')
	# print( "\n transformer_name: ", transformer_name_iowa240 )

	# This is for multiDigraph that didn't work
	# for item in graph.successors( "bus1002"):
	# 	print( item ) 

	# 	# buses=[650.2,rg60.2] phases=1 bank=reg1 xhl=0.01 kvas=[1666,1666] kvs=[2.4,2.4] %loadloss=0.01
	# 	print( G[ "633"]["634"]["phases"] )
	# 	print( G[ "633"]["634"]["bank"] )
	# 	print( G[ "633"]["634"]["xhl"] )
	# 	print( G[ "633"]["634"]["kvas"] )
	# 	print( G[ "633"]["634"]["kvs"] )
	# 	print( G[ "633"]["634"]["loadloss"] )

	########## LEHIGH TESTING ##########

	lehigh_file = Path( omf.omfDir, 'scratch', 'hostingcapacity', 'lehigh4mgs.dss.omd')
	lehigh_tree = opendss.dssConvert.omdToTree( lehigh_file )
	opendss.dssConvert.treeToDss(lehigh_tree, Path(modelDir, 'lehighOmdToDss.dss'))
	lehigh_data = opendss.dss_to_nx_fulldata( Path(modelDir, 'lehighOmdToDss.dss') )
	lehigh_graph = lehigh_data[0]
	lehigh_labels = {}
	for node in lehigh_graph.nodes:
		lehigh_labels[node] = node
	drawNXGraph(lehigh_graph, lehigh_data[1], Path(modelDir, "lehigh.png"), labels=lehigh_labels)

	# new object=generator.solar_634_existing bus1=634.1 phases=1 kv=0.277 kw=440 pf=1 yearly=solar_634_existing_shap

	########## Lehigh Downline Load
	# print( "Descendents for bus 634 in lehigh4: ", sorted(nx.descendants(lehigh_graph, "634")) )
	buses = opendss.get_all_buses( os.path.join( modelDir, 'lehighOmdToDss.dss') )
	buses_output = {}
	lehigh_kw = nx.get_node_attributes(lehigh_graph, 'kw')
	lehigh_kwRated = nx.get_node_attributes( lehigh_graph, 'kwrated') # Storage attribute
	lehigh_kvFromGraph = nx.get_node_attributes( lehigh_graph, 'kv' )
	# print( "\nlehigh_kw: ", lehigh_kw)
	lehigh_objects = nx.get_node_attributes(lehigh_graph, 'object')
	# print( "\nlehigh_objects: ", lehigh_objects )
	# Check if they are buses
	for bus in buses:
		if bus in lehigh_graph.nodes:
			kwSum = 0
			get_dependents = sorted(nx.descendants(lehigh_graph, bus))
			for dependent in get_dependents:
				if dependent in lehigh_kw.keys() and lehigh_objects[dependent] == 'load':
					kwSum += float(lehigh_kw[dependent])
				elif dependent in lehigh_kw.keys() and lehigh_objects[dependent] == 'generator':
					kwSum -= float(lehigh_kw[dependent])
				elif dependent in lehigh_kwRated.keys() and lehigh_objects[dependent] == 'storage':
					kwSum -= float(lehigh_kwRated[dependent])
				elif dependent in lehigh_kvFromGraph.keys() and lehigh_objects[dependent] == 'pvsystem':
					pfFromGraph = nx.get_node_attributes(lehigh_graph, 'pf')
					# pvsystem has kv, not kw
					kwForPVSys = lehigh_kvFromGraph[dependent] * pfFromGraph[dependent]
					kwSum -= kwForPVSys
			buses_output[bus] = kwSum

	print( "\ndownline kw load output for lehigh with generator and storage: ", buses_output )
	

	''' EPRI-J1.clean.dss - this has pvsystem
	# EPRI-J1.clean.dss - this has pvsystem
	EPRI_J1_file = Path( omf.omfDir, 'solvers', 'opendss', 'EPRI-J1.clean.dss')
	EPRI_J1_data = opendss.dss_to_nx_fulldata( EPRI_J1_file )
	EPRI_J1_graph = EPRI_J1_data[0]

	buses = opendss.get_all_buses( os.path.join( omf.omfDir, 'solvers', 'opendss', 'EPRI-J1.clean.dss' ) )
	buses_output = {}
	EPRI_J1_kwFromGraph = nx.get_node_attributes(EPRI_J1_graph, 'kw')
	EPRI_J1_kwRatedFromGraph = nx.get_node_attributes( EPRI_J1_graph, 'kwrated') # Storage attribute
	EPRI_J1_kvFromGraph = nx.get_node_attributes( EPRI_J1_graph, 'kv' )
	EPRI_J1_objects = nx.get_node_attributes(EPRI_J1_graph, 'object')
	EPRI_J1_labels = {}
	for node in EPRI_J1_graph.nodes:
		EPRI_J1_labels[node] = node
	drawNXGraph(EPRI_J1_graph, EPRI_J1_data[1], Path(modelDir, "EPRI_J1.png"), labels=EPRI_J1_labels)
	# Check if they are buses
	for bus in buses:
		if bus in EPRI_J1_graph.nodes:
			kwSum = 0
			get_dependents = sorted(nx.descendants(EPRI_J1_graph, bus))
			for dependent in get_dependents:
				if dependent in EPRI_J1_kwFromGraph.keys() and EPRI_J1_objects[dependent] == 'load':
					kwSum += float(EPRI_J1_kwFromGraph[dependent])
				elif dependent in EPRI_J1_kwFromGraph.keys() and EPRI_J1_objects[dependent] == 'generator':
					kwSum -= float(EPRI_J1_kwFromGraph[dependent])
				elif dependent in EPRI_J1_kwRatedFromGraph.keys() and EPRI_J1_objects[dependent] == 'storage':
					kwSum -= float(EPRI_J1_kwRatedFromGraph[dependent])
				elif dependent in EPRI_J1_kvFromGraph.keys() and EPRI_J1_objects[dependent] == 'pvsystem':
					pfFromGraph = nx.get_node_attributes(EPRI_J1_graph, 'pf')
					# pvsystem has kv, not kw
					kwForPVSys = EPRI_J1_kvFromGraph[dependent] * pfFromGraph[dependent]
					kwSum -= kwForPVSys
			buses_output[bus] = kwSum

	print( "\ndownline kw load output for EPRI_J1 with pvsystem ", buses_output )
	'''

	

	############################ Drawing stuff.
	# kwFromGraph = nx.get_node_attributes(graph, 'kw') # Dict 
	# kwFromGraph = {key: float(value) for key, value in kwFromGraph.items()} # sets all keys in dict to floats
	
	# # Create a new list for color codes with default values for nodes without a kw
	# colorCode = []
	# for node in graph.nodes():
	# 		if node in kwFromGraph:
	# 				colorCode.append(kwFromGraph[node])
	# 		else:
	# 				colorCode.append(0) # Use 0 for nodes without a kw, which will be mapped to grey

	# # Normalize the colorCode values to the range [0, 1] for the colormap
	# colorCode = np.array(colorCode)
	# colorCode = (colorCode - colorCode.min()) / (colorCode.max() - colorCode.min())

	# drawNXGraph( G=graph, pos=pos, outputPath=Path( modelDir, "myplot.png"), colorCode=colorCode, labels=labels )


	
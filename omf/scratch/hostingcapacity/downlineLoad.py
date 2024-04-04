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

'''
Simply adds up all load further away from the substation than the given bus to estimate rough hosting capacity.
with open(Path(modelDir, 'treefile.txt'), "w") as file:
        for item in tree:
            file.write(f"{item}\n")

voltagePlot 
	getVoltages
'''

def convertOmd(pathToOmdFile):
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = nx.Graph()
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

def dss_to_networkx(dssFilePath, tree=None, omd=None):
	''' Return a networkx directed graph from a dss file. If tree is provided, build graph from that instead of the file. '''
	if tree == None:
		tree = opendss.dssConvert.dssToTree(dssFilePath)
	if omd == None:
		omd = opendss.dssConvert.evilDssTreeToGldTree(tree)

	dssFileLoc = os.path.dirname(os.path.abspath(dssFilePath))

	# Gather edges, leave out source and circuit objects
	edges = [(ob['from'],ob['to']) for ob in omd.values() if 'from' in ob and 'to' in ob]
	edges_sub = [
		(ob['parent'],ob['name']) for ob in omd.values()
		if 'name' in ob and 'parent' in ob and ob.get('object') not in ['circuit', 'vsource']
	]
	full_edges = edges + edges_sub
	G = nx.DiGraph(full_edges)
	pos = {}
	for ob in omd.values():
		if 'latitude' in ob and 'longitude' in ob:
			G.add_node(ob['name'], pos=(float(ob['longitude']), float(ob['latitude'])))
			pos[ob['name']] = ( float(ob['longitude']), float(ob['longitude']) )
		else:
			G.add_node(ob['name'])

	# Start drawing.
	plt.figure(figsize=(20,20)) 
	nodes = nx.draw_networkx_nodes(G, pos,  node_size=300)
	edges = nx.draw_networkx_edges(G, pos)
	plt.colorbar(nodes)
	plt.legend()
	plt.title('Network Voltage Layout')
	plt.tight_layout()
	plt.savefig(dssFileLoc + '/' + 'directedDssConvert.png')
	plt.clf()
	return G

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

def dss_to_nx(dssFilePath, tree=None ):
	''' Return a networkx directed graph from a dss file. If tree is provided, build graph from that instead of the file. '''
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
		bus = bus_to_transformer_pairs[load_transformer]
		G.add_edge(bus, load_name, transformer=load_transformer)
		pos[load_name] = pos[load_transformer]
		labels[load_name] = load_name
		labels[ bus ] = bus
	
	# TEMP: Remove transformer nodes added from coordinates. Transformer data is edges, not nodes.
	for transformer_name in load_transformer_name:
		if transformer_name in G.nodes:
			G.remove_node( transformer_name )
			pos.pop( transformer_name )
	
	load_kw = [x['kw'] for x in loads if 'kw' in x]
	for load, kw in zip( load_names, load_kw ):
		G.nodes[load]['kw'] = kw
	
	return [G, pos, labels]

def drawNXGraph(G, pos, outputPath, labels: list=[], colorCode: list=[], figSize=(20,20), nodeSize: int=300 , fontSize: int=8):
	print( "inside..")
	# Start drawing.
	plt.figure(figsize=figSize) 
	nodes = nx.draw_networkx_nodes(G, pos, node_size=nodeSize)
	edges = nx.draw_networkx_edges(G, pos)
	if ( len(labels) != 0 ):
		nx.draw_networkx_labels(G, pos, labels, font_size=fontSize)
	#plt.colorbar(nodes)
	plt.legend()
	plt.title('Network Voltage Layout')
	plt.tight_layout()
	plt.savefig( outputPath )
	plt.clf()
	plt.show()

if __name__ == '__main__':
	modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')
	beginning_test_file = Path( omf.omfDir, 'static', 'publicFeeders', 'iowa240.clean.dss.omd')
	circuit_file = 'omdToDSScircuit.dss'

	'''
	# NOT USABLE - Geo.py function convertOMD
	# 1 Issue of the start - creates an undirected graph. I think we want directed for this. 
	#
	# This func takes the "links" part of the tree from the OMD file
	# Which, for iowa240.clean.dss.omd, there's nothing in links -> FAILS
	#
	# Then, I tried making my own that gets the "tree" part out of the OMF file -> FAILS
	# {'object': '!CMD', 'name': 'clear'}
	# Traceback (most recent call last):
	#   File "/home/jenny/nreca/omf/omf/scratch/hostingcapacity/again.py", line 17, in convertOmd
	#     sourceEdge = item['source']['name']
	# KeyError: 'source'

	# During handling of the above exception, another exception occurred:

	# Traceback (most recent call last):
	#   File "/home/jenny/nreca/omf/omf/scratch/hostingcapacity/again.py", line 20, in convertOmd
	#     sourceEdge = str(item['target']['name']) + ' Source'
	# KeyError: 'target'

	# Fails because of the other lines.. its not designed to deal with them.

	# graph = convertOmd( beginning_test_file.resolve() )
	# print( "graph nodes frmo convertOmd function: ", graph.nodes )

	####################################################
	# Feeder.py function treeToNxGraph
	# Has nodes that shouldn't be there, no descendents, no edges?
	#
	# tree = omf.feeder.parse(beginning_test_file.resolve())
	# tree = opendss.dssConvert.omdToTree( beginning_test_file.resolve() )
	# with open(beginning_test_file) as f:
	# 	feederJson = json.load(f)
	# tree = feederJson.get("tree",{})
	# g2 = omf.feeder.treeToNxGraph( tree, digraph=True )
	# print( "graph nodes from omf.feeder.treeToNxGraph function: ", g2.nodes )
	# Has data that doesn't need to be in here but its ok. but idk what the edges are..
	# test_descendents_bus_list = sorted(nx.descendants(g2, 't_bus1004_l'))
	# Even though I specified a digraph - this bus has no descendants even though it should.
	# print( g2.get_edge_data('t_bus1004_l', 'load_1004') ) - THIS PRINTS NONE... that's awkward...

	tree = opendss.dssConvert.omdToTree( beginning_test_file.resolve() ) # this tree is a list
	opendss.dssConvert.treeToDss(tree, Path(modelDir, circuit_file))

	# This graph is directed
	# But this has a lot of other stuff. The other one is just buses which I think we want...
	# Copied and pasted here to get physical drawing - it is SO OFF!!!!!
	# dssConvert_graph = dss_to_networkx( os.path.join( modelDir, circuit_file), tree )
	# print( "info about graph made from dss_to_networkx: ", dssConvert_graph )
	# test_descendents_bus_list = sorted(nx.descendants(dssConvert_graph, 't_bus1004_l'))
	# print( dssConvert_graph.get_edge_data('t_bus1004_l', 'load_1004') ) #PRINTS NONE -- THATS TOUGH
	# Doesn't have the loads or edges for them, same issue as networkPlot
	# but also, this visually for some reason is SO OFF? NetworkPlot isn't - I might as well just keep that one.

	# Test bus info
	# t_bus1004_l - should have other desendents and its loads

	# opendss __init__
	# networkx.py
	# my_NetworkPlot and my_GetCoords both changes to remove radius
	my_NP_graph = my_NetworkPlot( os.path.join( modelDir, circuit_file) )
	print( "info about graph made from networkplot: ", my_NP_graph )
	# networkPlot.py - looks like how I want it to look. This is a good sign
	# but its undirected.
	# - NOPE NETWORKPLOT IS THE BEST ONE!!!
	# Gotta make it directed.
	# Gotta add loads/load data.
	'''

	# my_NP_graph = my_NetworkPlot( os.path.join( modelDir, circuit_file), output_name='networkPlotDirected.png' )
	# print( "info about graph made from networkplot: ", my_NP_graph )
	# print( my_NP_graph.edges() )
	# test_descendents_bus_list = sorted(nx.descendants(my_NP_graph, 'T_BUS1003_L'))
	# print( my_NP_graph.get_edge_data('T_BUS1003_L', 'BUS1003') )
	# Changing it to directed is not at easy fix. The bus still doesn't have descendants when I know it does.
	# print( test_descendents_bus_list )

	# Got rid of the volts stuff.
	# A) David mentioned that we don't need any powerflow calculations
	# Take the color stuff out, and color it based on the kw. 
	graphData = dss_to_nx( os.path.join( modelDir, circuit_file) )
	graph = graphData[0]
	print( "info about graph made from temp_func_name_nx: ", graph )
	buses = opendss.get_all_buses( os.path.join( modelDir, circuit_file) )
	buses_output = {}
	kwFromGraph = nx.get_node_attributes(graph, 'kw')
	# print(kwFromGraph)
	for bus in buses:
		#print( 'bus: ', bus)
		if bus in graph.nodes:
			kwSum = 0
			get_dependents = sorted(nx.descendants(graph, bus))
			#print( "get_dependents of bus: ", bus)
			#print( "\n", get_dependents)
			for dependent in get_dependents:
				#print( "dependent 1: ", dependent )
				if dependent in kwFromGraph.keys():
					#print( "dependent: ", dependent )
					kwSum += float(kwFromGraph[dependent])
			buses_output[bus] = kwSum
	downline_output = pd.DataFrame(list(buses_output.items()), columns=['busname', 'kw'] )
	norm = mcolors.Normalize(vmin=min(buses_output.values()), vmax=max(buses_output.values()))
	cmap = plt.get_cmap('viridis')
	node_colors = [cmap(norm(value)) for value in buses_output.values()]
	drawNXGraph( G=graph, pos=graphData[1], outputPath=os.path.join( modelDir, "dssToPng.png"), labels=graphData[2], colorCode=node_colors)
	
	# print( temp_func_graph.edges() )
	

	# buses = opendss.get_meter_buses(circuit_file )
	# kwSum = 0
	# data = []
	# # only load nodes would have these attributes
	# kwFromGraph = nx.get_node_attributes(dssConvert_graph, 'kw')
	# busToLoad = nx.get_node_attributes( dssConvert_graph, 'bus')
	# test_descendents_bus_list = sorted(nx.descendants(dssConvert_graph, 't_bus2060_l'))
	# print( "test_descendents_bus_list: ", test_descendents_bus_list )
	# for bus in buses:
	# 	if bus == "bus2033":
	# 		test_descendents_bus_list = sorted(nx.descendants(dssConvert_graph, 't_bus2060_l'))
	# 		print( "\ntest_descendents_bus_list FROM LOOP: ", test_descendents_bus_list )
	# for bus in buses:
	# 	kwSum = 0
	# 	descendents_bus_list = sorted(nx.descendants(g2, bus))
	# 	# Can be loads or buses
	# 	for descendent in descendents_bus_list:
	# 		if descendent in kwFromGraph:
	# 			kwSum += kwFromGraph[descendent]
	# 	data.append([busToLoad[descendent], kwSum])
	# downlineOutputDF = pd.DataFrame(data, columns=['busName', 'kw'])
	# print( downlineOutputDF.head )

	# print( "kwFromGraph: ", kwFromGraph)
	# print( "kw of t_bus3056_l: ",  kwFromGraph['t_bus3056_l'] )
	# test_descendents_bus_list = sorted(nx.descendants(g2, 'bus2033'))
	# print( "descendants: ", test_descendents_bus_list )
	# kwSum = 0
	# for node in test_descendents_bus_list:
	# 	if node in buses:
	# 		kwSum += kwFromGraph[node]
	# print( "kwSum: ", kwSum)
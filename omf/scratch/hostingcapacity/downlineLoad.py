import networkx as nx
from pathlib import Path
import pandas as pd
import math
import warnings
import matplotlib.pyplot as plt
import numpy as np

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
			# JENNY
			G.nodes[row['Bus']]['max_pu_voltage'] = float(max(row[' pu1'], row[' pu2'],row[' pu3']))
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

def temp_func_name_nx(dssFilePath, tree=None, figsize=(20,20), output_name='directedNetworkPlot.png', show_labels=True, node_size=300, font_size=8):
	''' Return a networkx directed graph from a dss file. If tree is provided, build graph from that instead of the file. '''
	if tree == None:
		tree = opendss.dssConvert.dssToTree(dssFilePath)
	dssFileLoc = os.path.dirname(dssFilePath)

	opendss.runDSS(dssFilePath)
	coords = my_GetCoords(dssFilePath)
	opendss.runDssCommand(f'export voltages "{dssFileLoc}/volts.csv"')
	volts = pd.read_csv(dssFileLoc + '/volts.csv')

	omd = opendss.dssConvert.evilDssTreeToGldTree(tree)

	coords.columns = ['Bus', 'X', 'Y']

	G = nx.DiGraph()
	# Get the coordinates.
	pos = {}
	for index, row in coords.iterrows():
		try:
			bus_name = str(int(row['Bus']))
		except:
			bus_name = row['Bus']
		G.add_node(bus_name.lower(), pos=(float(row['X']), float(row['Y'])))
		pos[bus_name] = (float(row['X']), float(row['Y']))

	#for x in pos.keys():
		#print( str(x) + " => " + str(pos[x]))

	# Gather edges, leave out source and circuit objects
	edges = [(ob['from'],ob['to']) for ob in omd.values() if 'from' in ob and 'to' in ob]
	edges_sub = [
		(ob['parent'],ob['name']) for ob in omd.values()
		if 'name' in ob and 'parent' in ob and ob.get('object') not in ['circuit', 'vsource']
	]
	full_edges = edges + edges_sub
	G.add_edges_from(full_edges)

# We'll color the nodes according to voltage.
	# Getting values from volts.csv and setting it as attributes
	volt_values = {}
	labels = {}
	for index, row in volts.iterrows():
		if row['Bus'] in [x for x in pos]:
			volt_values[row['Bus']] = row[' pu1']
			labels[row['Bus']] = row['Bus']
			# JENNY
			G.nodes[row['Bus'].lower()]['max_pu_voltage'] = float(max(row[' pu1'], row[' pu2'],row[' pu3']))
	colorCode = [volt_values.get(node, 0.0) for node in G.nodes()]

	# Getting values out of tree and setting it as attributes
	# parse load 
	# 		parse bus_name
	# 		get kw
	meters = [x for x in tree if x.get('object','N/A').startswith('load.')]
	bus_names = [x['bus1'] for x in meters if 'bus1' in x]
	kw = [x['kw'] for x in meters if 'kw' in x] # these are lists	
	just_name_no_conn = [x.split('.')[0] for x in bus_names]
	for bus_name, kwVal in zip(just_name_no_conn, kw):
		G.nodes[bus_name.lower()]['kw'] = float(kwVal)


	# Print positions of all nodes
	# for node, position in nx.get_node_attributes(G, 'pos').items():
	# 	print(f"Node: {node}, Position: {position}")

	# Start drawing.
	plt.figure(figsize=figsize) 
	positions = nx.spring_layout( G )
	nodes = nx.draw_networkx_nodes(G, positions, node_color=colorCode, node_size=node_size)
	edges = nx.draw_networkx_edges(G, positions)
	if show_labels:
		nx.draw_networkx_labels(G, pos, labels, font_size=font_size)
	plt.colorbar(nodes)
	plt.legend()
	plt.title('Network Voltage Layout')
	plt.tight_layout()
	plt.savefig(dssFileLoc + '/' + output_name)
	plt.clf()
	return G

def downline_hosting_capacity( FNAME, BUS_LIST ):
  fullpath = os.path.abspath(FNAME)
  tree = opendss.dssConvert.omdToTree(fullpath)

if __name__ == '__main__':
  modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')
  beginning_test_file = Path( omf.omfDir, 'static', 'publicFeeders', 'iowa240.clean.dss.omd')
  circuit_file = 'omdToDSScircuit.dss'

  tree = opendss.dssConvert.omdToTree( beginning_test_file.resolve() ) # this tree is a list
  opendss.dssConvert.treeToDss(tree, Path(modelDir, circuit_file))

  # This graph is undirected.
  # G = my_NetworkPlot( os.path.join( modelDir, circuit_file) )
  # print( "info about graph made from networkplot: ", G )
  # max_pu_voltage = nx.get_node_attributes(G, "max_pu_voltage")
  # pos = nx.get_node_attributes(G,'pos')
  # print( "max_pu_voltage of BUS1006: ",  max_pu_voltage['BUS1006'])
  # print( "pos of BUS1006: ", pos['BUS1006'])

  # This graph is directed
	# But this has a lot of other stuff. The other one is just busses which I think we want...
  g2 = temp_func_name_nx( os.path.join( modelDir, circuit_file), tree )
  buses = opendss.get_meter_buses(circuit_file )
  # print( type( sorted(nx.descendants(g2, 't_bus3056_l'))) )
  # print( sorted(nx.descendants(g2, 'bus2033')) )
  max_pu_voltage = nx.get_node_attributes(g2, "max_pu_voltage")
  kwFromGraph = nx.get_node_attributes(g2, 'kw') 
  print( "type( max_pu_voltage )",  type( max_pu_voltage ))
  print( "kw of t_bus3056_l: ",  kwFromGraph['t_bus3056_l'] )
  print( "max_pu_voltage of t_bus3056_l: ",  max_pu_voltage['t_bus3056_l'] )
  test_descendents_bus_list = sorted(nx.descendants(g2, 'bus2033'))
  # print( max_pu_voltage )
  voltage_sum = 0
  kwSum = 0
  for node in test_descendents_bus_list:
    if node in buses:
      voltage_sum += max_pu_voltage[node]
  print( "voltage_sum: ", voltage_sum)

  # nx.draw(g2, with_labels=True, node_size=1000, node_color='lightblue', font_size=10)
  # print( "info about graph made from my_BIGBOYGRAPH: ", g2 )
  # g2 = netx( Path(modelDir, circuit_file), tree )
  # print( "info about graph made from netx: ", g2 )

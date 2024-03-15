import networkx as nx
from pathlib import Path
import pandas as pd
import math

import omf
from omf.solvers import opendss
import os

'''
Simply adds up all load further away from the substation than the given bus to estimate rough hosting capacity.
with open(Path(modelDir, 'treefile.txt'), "w") as file:
        for item in tree:
            file.write(f"{item}\n")

'''

def myGetCoords(dssFilePath):
	'''Takes in an OpenDSS circuit definition file and outputs the bus coordinates as a dataframe.'''
	dssFileLoc = os.path.dirname(dssFilePath)
	opendss.runDSS(dssFilePath)
	opendss.runDssCommand(f'export buscoords "{dssFileLoc}/coords.csv"')
	coords = pd.read_csv(dssFileLoc + '/coords.csv', header=None)
	#JENNY
	coords.columns = ['Element', 'X', 'Y']
	return coords

def my_networkPlot(filePath, figsize=(20,20), output_name='networkPlot.png', show_labels=True, node_size=300, font_size=8):
	''' Plot the physical topology of the circuit.
	Returns a networkx graph of the circuit as a bonus. '''
	dssFileLoc = os.path.dirname(os.path.abspath(filePath))
	opendss.runDSS(filePath)
	coords = myGetCoords(filePath)
	opendss.runDssCommand(f'export voltages "{dssFileLoc}/volts.csv"')
	volts = pd.read_csv(dssFileLoc + '/volts.csv')
	#JENNY
	coords.columns = ['Bus', 'X', 'Y']
	
	buses = opendss.get_meter_buses(filePath)
	G = nx.Graph()
	# Get the coordinates.
	pos = {}
	for index, row in coords.iterrows():
		try:
			bus_name = str(int(row['Bus']))
		except:
			bus_name = row['Bus']
	# Get the connecting edges using Pandas.
	
	lines = opendss.dss.utils.lines_to_dataframe()
	edges = []
	for index, row in lines.iterrows():
		#HACK: dss upercases everything in the coordinate output.
		bus1 = row['Bus1'].split('.')[0].upper()
		bus2 = row['Bus2'].split('.')[0].upper()
		edges.append((bus1, bus2))
	G.add_edges_from(edges)
	# Remove buses withouts coords
	no_pos_nodes = set(G.nodes()) - set(pos)
	G.remove_nodes_from(list(no_pos_nodes))
	return G

def downline_hosting_capacity( FNAME ):
  fullpath = os.path.abspath(FNAME)
  tree = opendss.dssConvert.omdToTree(fullpath)


if __name__ == '__main__':
  modelDir = Path(omf.omfDir, 'scratch', 'hostingcapacity')
  circuit_file = 'circuit.dss'
  beginning_test_file = Path( omf.omfDir, 'static', 'publicFeeders', 'iowa240.clean.dss.omd')

  tree = opendss.dssConvert.omdToTree(beginning_test_file.resolve()) # this tree is a list

  graph = opendss.networkPlot( os.path.join( modelDir, circuit_file) )
  print( graph )
  # print( graph.nodes )
  #print( nx.descendants(graph, "EQ_SOURCE_BUS") )


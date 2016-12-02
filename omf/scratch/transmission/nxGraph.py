import datetime, copy, os, re, warnings, networkx as nx, json
from os.path import join as pJoin
from matplotlib import pyplot as plt
import network

'''
# Test a basic graph.
G = nx.Graph()
G.add_node(1)
G.add_node(3)
G.add_edge(1,3)
G.add_edge(5,6)
for key in G:
	print key
'''

# Read a .omt. and add lat/lon info.
NETWORK_PATH = pJoin(os.getcwd(),'outData')

# Load in the network.
with open(pJoin(NETWORK_PATH,'case30.omt'),'r') as netFile:
	thisNet = json.load(netFile)

# Force layout of network since it came from matpower which has no lat/lon information.
print "Force laying out the graph..."
# Use graphviz to lay out the graph.
inGraph = network.netToNxGraph(thisNet)
# HACK: work on a new graph without attributes because graphViz tries to read attrs.
cleanG = nx.Graph(inGraph.edges())
# HACK2: might miss nodes without edges without the following.
cleanG.add_nodes_from(inGraph)
pos = nx.nx_agraph.graphviz_layout(cleanG, prog='neato')
# # Charting the feeder in matplotlib:
# feeder.latLonNxGraph(inGraph, labels=False, neatoLayout=True, showPlot=True)
# Insert the latlons.
for compType in thisNet:
	if compType in ['bus']:
		comp = thisNet[compType]
		for compVal in comp:
			for idnum,item in compVal.iteritems():
				obName = item.get('bus_i')
				thisPos = pos.get(obName, None)
				if thisPos != None:
					thisNet[compType][int(float(idnum))-1][idnum]['longitude'] = thisPos[0]
					thisNet[compType][int(float(idnum))-1][idnum]['latitude'] = thisPos[1]

# Write back out.
with open(pJoin(NETWORK_PATH, 'case30_latlon.omt'),"w") as netFile:
	json.dump(thisNet, netFile, indent = 4)
print "Wrote lat/lon info to: %s"%('case30_latlon.omt')
import omf.feeder as feeder, json
import os, networkx as nx
from os.path import join as pJoin
from networkx.drawing.nx_agraph import graphviz_layout

_myDir = os.path.dirname(os.path.abspath(__file__))
IN_PATH_OMD = pJoin(_myDir,'superModel Tomorrow.omd')
OUT_PATH_OMD = pJoin(_myDir,'superModel Tomorrow with latlons.omd')

with open(IN_PATH_OMD,'r') as jsonFile:
	omd = json.load(jsonFile)
	tree = omd['tree']

# Use graphviz to lay out the graph.
inGraph = feeder.treeToNxGraph(tree)
# HACK: work on a new graph without attributes because graphViz tries to read attrs.
cleanG = nx.Graph(inGraph.edges())
# HACK2: might miss nodes without edges without the following.
cleanG.add_nodes_from(inGraph)
pos = graphviz_layout(cleanG, prog='neato')
# # Charting the feeder in matplotlib:
# feeder.latLonNxGraph(inGraph, labels=False, neatoLayout=True, showPlot=True)
# Insert the latlons.
for key in tree:
	obName = tree[key].get('name','')
	thisPos = pos.get(obName, None)
	if thisPos != None:
		tree[key]['longitude'] = thisPos[0]
		tree[key]['latitude'] = thisPos[1]

with open(OUT_PATH_OMD,'w') as outFile:
	json.dump(omd, outFile)

import omf.feeder as feeder, json

IN_PATH_OMD = 'insert_path_here'
OUT_PATH_OMD = '2nd_path_here'

with open(IN_PATH_OMD,'r') as jsonFile:
	omd = json.load(jsonFile)
	tree = omd['tree']

if DO_FORCE_LAYOUT:
	# Use graphviz to lay out the graph.
	inGraph = feeder.treeToNxGraph(tree)
	# HACK: work on a new graph without attributes because graphViz tries to read attrs.
	cleanG = nx.Graph(inGraph.edges())
	# HACK2: might miss nodes without edges without the following.
	cleanG.add_nodes_from(inGraph)
	pos = nx.nx_agraph.graphviz_layout(cleanG, prog='neato')
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

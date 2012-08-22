def to_d3_json(inTree):
	def node_groups(glmTree):
		#helper function:
		def node_attrs(node_dict, group=None):
			attr_dict = {}
			if group:
				attr_dict['group'] = group;
			for key in node_dict:
				if key not in ['group', 'object']:
					try:
						attr_dict['_'+key] = node_dict[key]
					except TypeError:
						pass
			if 'object' in node_dict:
				attr_dict['_type'] = node_dict['object']
				if node_dict['object'] not in node_group_dict:
					node_group_dict[node_dict['object']] = len(node_group_dict)
				attr_dict['group'] = node_group_dict[node_dict['object']]
			else:
				attr_dict['group'] = node_group_dict['unknown']
			return attr_dict
		# Start node_groups:
		glmGraph = nx.Graph()
		nodeNodes = []
		for x in glmTree:
			if 'from' in glmTree[x] and 'to' in glmTree[x]:
				glmGraph.add_edge(glmTree[x]['from'],glmTree[x]['to'],node_attrs(glmTree[x]))
			elif 'parent' in glmTree[x] and 'name' in glmTree[x]:
				glmGraph.add_edge(glmTree[x]['name'],glmTree[x]['parent'])
			if 'object' in glmTree[x] and glmTree[x]['object'] in ['triplex_meter', 'house', 'node', 'meter', 'load', 'ZIPload','waterheater', 'triplex_node','capacitor']:
				name = "unset"
				try:
					name = glmTree[x]['name']
				except KeyError:
					pass
				glmGraph.add_node(name, node_attrs(glmTree[x]))
		return glmGraph
	node_group_dict = {'unknown':0}
	graph = node_groups(inTree)
	graph_json = {'nodes':map(lambda x:dict({'name':x[0]},**x[1]),graph.nodes(data=True))}
	ints_graph = nx.convert_node_labels_to_integers(graph, discard_old_labels=False)
	graph_edges = ints_graph.edges(data=True)
	# Build up edge dictionary in JSON format
	json_edges = list()
	for j, k, w in graph_edges:
		e = {'source' : j, 'target' : k}
		if any(map(lambda k: k=='weight', w.keys())):
			e['value'] = w['weight']
		else:
			e['value'] = 1
		json_edges.append(e)
	
	graph_json['links'] = json_edges
	return graph_json

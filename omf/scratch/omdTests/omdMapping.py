from pyproj import Proj, transform
import webbrowser
import omf, json, warnings, networkx as nx, matplotlib
from matplotlib import pyplot as plt
from omf.feeder import _obToCol

def latLonNxGraphMap(inGraph, labels=False, neatoLayout=False, showPlot=False):
	''' Draw a networkx graph representing a feeder.'''
	from mpl_toolkits.basemap import Basemap
	# Be quiet Matplotlib.
	warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)
	# Set up figure.
	plt.axis('off')
	plt.tight_layout()
	plt.gca().invert_yaxis()
	plt.gca().set_aspect('equal')
	m = Basemap(llcrnrlon=-102.7662,llcrnrlat=32.983,urcrnrlon=-102.7576,urcrnrlat=32.997, epsg=3857)
	m.arcgisimage(service='World_Street_Map', verbose= False)
	# Layout the graph via GraphViz neato. Handy if there's no lat/lon data.
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(inGraph.edges())
		# HACK2: might miss nodes without edges without the following.
		cleanG.add_nodes_from(inGraph)
		pos = nx.nx_agraph.graphviz_layout(cleanG, prog='neato')
	else:
		pos = {}
		pos = {node: nx.get_node_attributes(inGraph, 'pos')[node] for node in nx.get_node_attributes(inGraph, 'pos')}
		#print(node_positions)
		for point in pos:
			pos[point] = (m(pos[point][1], pos[point][0]))
	# Draw all the edges.
	for e in inGraph.edges():
		eType = inGraph.edge[e[0]][e[1]].get('type','underground_line')
		ePhases = inGraph.edge[e[0]][e[1]].get('phases',1)
		standArgs = {'edgelist':[e],
					 'edge_color':_obToCol(eType),
					 'width':2,
					 'style':{'parentChild':'dotted','underground_line':'dashed'}.get(eType,'solid') }
		if ePhases==3:
			standArgs.update({'width':5})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':3,'edge_color':'white'})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':1,'edge_color':_obToCol(eType)})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
		if ePhases==2:
			standArgs.update({'width':3})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':1,'edge_color':'white'})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
		else:
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
	# Draw nodes and optional labels.
	nx.draw_networkx_nodes(inGraph,pos,
						   nodelist=pos.keys(),
						   node_color=[_obToCol(inGraph.node[n].get('type','underground_line')) for n in inGraph],
						   linewidths=0,
						   node_size=40)
	if labels:
		nx.draw_networkx_labels(inGraph,pos,
								font_color='black',
								font_weight='bold',
								font_size=0.25)
	if showPlot: plt.savefig('latlon.png', dpi=1000)

def drawPngGraph():
	#Static reference file for testing now
	from mpl_toolkits.basemap import Basemap
	with open('../../static/publicFeeders/Olin Barre LatLon.omd') as inFile:
		tree = json.load(inFile)['tree']
	plt.switch_backend('TKAgg')
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	#Might need later for setting axes value in draw_network
	latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	#print(latitude_min, latitude_max, longitude_min, longitude_max)
	#Create dict of lat/lon for only nodes that have lat/lon values in feeder
	m = Basemap(llcrnrlon=-102.7662,llcrnrlat=32.983,urcrnrlon=-102.7576,urcrnrlat=32.997, epsg=3857)
	m.arcgisimage(service='World_Street_Map', verbose= True)
	node_positions = {}
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	#print(node_positions)
	for point in node_positions:
		node_positions[point] = (m(node_positions[point][1], node_positions[point][0]))
	nx.draw_networkx(nxG, pos=node_positions, nodelist=[node for node in nxG if node in nx.get_node_attributes(nxG, 'pos')], with_labels=False, node_size=5)
	#m.plot(-102, 32, marker='D', color='m', latlon=True)
	#plt.show()
	plt.savefig('matplotlibmap.png', dpi=1000)

def drawLatLon():
	from mpl_toolkits.basemap import Basemap
	with open('../../static/publicFeeders/Olin Barre LatLon.omd') as inFile:
		tree = json.load(inFile)['tree']
	nxG = omf.feeder.treeToNxGraph(tree)
	plt.switch_backend('TKAgg')
	latLonNxGraphMap(nxG, labels=False, neatoLayout=False, showPlot=True)

def drawHtmlGraph():
	import folium
	with open('../../static/publicFeeders/Olin Barre LatLon.omd') as inFile:
		tree = json.load(inFile)['tree']
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	#Might need later for setting axes value in draw_network
	latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	#print(latitude_min, latitude_max, longitude_min, longitude_max)
	#Create dict of lat/lon for only nodes that have lat/lon values in feeder
	node_positions = {}
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	circleDict = {'objects':[]}
	for i in node_positions:
		circleDict['objects'].append({'circle': {'coordinates':node_positions[i]}})
	#print(circleDict)
	#print(node_positions)
	m = folium.Map(location=[32.99, -102.76],
		zoom_start=16,
		control_scale = True,
		max_zoom=19)
	for node in node_positions:
		folium.Marker([node_positions[node][0], node_positions[node][1]], popup=node).add_to(m)
	#print(nx.edges(nxG))
	lineDict = {'objects':[]}
	for edge in nx.edges(nxG):
		#folium.PolyLine([[45.3288, -121.6625],[45.3311, -121.7113]]).add_to(m)
		folium.PolyLine([[node_positions[edge[0]][0], node_positions[edge[0]][1]],[node_positions[edge[1]][0], node_positions[edge[1]][1]]]).add_to(m)
		lineDict['objects'].append({'line': {'coordinates':[[node_positions[edge[0]][0], node_positions[edge[0]][1]],
			[node_positions[edge[1]][0], node_positions[edge[1]][1]]]}})
	#print(lineDict)
	with open('newnodes.json',"w") as outFile:
		json.dump(circleDict, outFile, indent=4)
	with open('newlines.json',"w") as outFile:
		json.dump(lineDict, outFile, indent=4)
	m.save('leafletmap.html')

def _tests():
	drawPngGraph()
	drawLatLon()
	drawHtmlGraph()

if __name__ == '__main__':
	_tests()
'''
# Small little function to calculate scaling factor for a line.
import math
x1 = 586.094375282
y1 = 445.866492772
x2 = 589.462214662
y2 = 442.843846618
z = 57.339599609375
if __name__ == '__main__':
	print (math.sqrt(pow((x2-x1),2) + pow((y2-y1),2)))/z
'''

# Getting two images to show up on the same matplotlib object and scaled appropriately.
from matplotlib import pyplot as plt
import numpy as np
import networkx as nx
import re

class HazardField(object):
	''' Object to modify a hazard field from an .asc file. '''

	def __init__(self, filePath):
		''' Use parsing function to set up harzard data in dict format in constructor.'''
		self.hazardObj = self.parseHazardFile(filePath)

	def parseHazardFile(self, inPath):
		''' Parse input .asc file. '''
		with open(inPath, "r") as hazardFile: # Parse the file, strip away whitespaces.
			content = hazardFile.readlines()
		content = [x.strip() for x in content]
		hazardObj = {}
		field = []
		for i in range(len(content)): 
			if i <= 5: # First, get the the parameters for the export function below. Each gets their own entry in our object.
				line = re.split(r"\s*",content[i])
				hazardObj[line[0]] = float(line[1])
			if i > 5: # Then, get the numerical data, mapping each number to its appropriate parameter.
				field.insert((i-6),map(float,content[i].split(" "))) 
		field = np.array(field)
		hazardObj["field"] = field
		return hazardObj

	def generateHeatMap(self, ax):

		cmap = plt.cm.Greys
		cmap._init()
		cmap._lut[:, -1] = np.linspace(.7, 1, 259)


		heatMap = ax.imshow(
			self.hazardObj['field'],
			cmap = cmap,
			interpolation = 'nearest',
			extent = [0,1,0,1],
			aspect='auto')

# Drawing networkX graph with lots of styles.

def generateNetwork(ax):
	G = nx.Graph()
	G.add_nodes_from([1, 2, 3, 4])
	G.add_edges_from([(1, 3), (1, 4), (2, 4)])
	nx.draw(G, ax=ax)

def genDiagram(outputDir, feederJson, damageDict, critLoads, ax):
	# print damageDict
	warnings.filterwarnings("ignore")
	# Load required data.
	tree = feederJson.get("tree",{})
	links = feederJson.get("links",{})
	
	# Get swing buses.
	green_list = []
	for node in tree:
		if 'bustype' in tree[node] and tree[node]['bustype'] == 'SWING':
			green_list.append(tree[node]['name'])

	# Generate lat/lons from nodes and links structures.
	for link in links:
		for typeLink in link.keys():
			if typeLink in ['source', 'target']:
				for key in link[typeLink].keys():
					if key in ['x', 'y']:
						objName = link[typeLink]['name']
						for x in tree:
							leaf = tree[x]
							if leaf.get('name','')==objName:
								if key=='x': leaf['latitude'] = link[typeLink][key]
								else: leaf['longitude'] = link[typeLink][key]
	# Remove even more things (no lat, lon or from = node without a position).
	for key in tree.keys():
		aLat = tree[key].get('latitude')
		aLon = tree[key].get('longitude')
		aFrom = tree[key].get('from')
		if aLat is None and aLon is None and aFrom is None:
			 tree.pop(key)
	# Create and save the graphic.
	inGraph = feeder.treeToNxGraph(tree)
	#feeder.latLonNxGraph(nxG) # This function creates a .plt reference which can be saved here.
	labels=False
	neatoLayout=False 
	showPlot=False
	plt.axis('off')
	plt.tight_layout()
	plt.gca().invert_yaxis()
	plt.gca().set_aspect('equal')
	# Layout the graph via GraphViz neato. Handy if there's no lat/lon data.
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(inGraph.edges())
		# HACK2: might miss nodes without edges without the following.
		cleanG.add_nodes_from(inGraph)
		pos = nx.nx_agraph.graphviz_layout(cleanG, prog='neato')
	else:
		pos = {n:inGraph.node[n].get('pos',(0,0)) for n in inGraph}
	# Draw all the edges
	for e in inGraph.edges():
		edgeName = inGraph.edge[e[0]][e[1]].get('name')
		edgeColor = 'black'
		if edgeName in damageDict:
			if damageDict[edgeName] == 1:
				edgeColor = 'yellow'
			if damageDict[edgeName] == 2:
				edgeColor = 'orange'
			if damageDict[edgeName] >= 3:
				edgeColor = 'red'
		eType = inGraph.edge[e[0]][e[1]].get('type','underground_line')
		ePhases = inGraph.edge[e[0]][e[1]].get('phases',1)
		standArgs = {'edgelist':[e],
					 'edge_color':edgeColor,
					 'width':2,
					 'ax':ax,
					 'style':{'parentChild':'dotted','underground_line':'dashed'}.get(eType,'solid') }
		if ePhases==3:
			standArgs.update({'width':5})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':3,'edge_color':'white'})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':1,'edge_color':edgeColor})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
		if ePhases==2:
			standArgs.update({'width':3})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
			standArgs.update({'width':1,'edge_color':'white'})
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
		else:
			nx.draw_networkx_edges(inGraph,pos,**standArgs)
	# Draw nodes and optional labels.
	red_list, blue_list, grey_list  = ([] for i in range(3))
	for key in pos.keys(): # Sort keys into seperate lists. Is there a more elegant way of doing this.
		if key not in green_list:
			load = key[2:6]
			if key in critLoads:
				red_list.append(key)
			elif load == 'load':
				blue_list.append(key)
			else:
				grey_list.append(key)
	nx.draw_networkx_nodes(
		inGraph,
		pos, 
		nodelist=green_list,
		ax=ax,
		node_color='green',
		label='Swing Buses',
		node_size=12
	)
	nx.draw_networkx_nodes(
		inGraph,
		pos,
		nodelist=red_list,
		ax=ax,
		node_color='red',
		label='Critical Loads',
		node_size=12
	)
	nx.draw_networkx_nodes(
		inGraph,
		pos,
		nodelist=blue_list,
		ax=ax,
		node_color='blue',
		label='Regular Loads',
		node_size=12
	)
	nx.draw_networkx_nodes(
		inGraph,
		pos,
		nodelist=grey_list,
		ax=ax,
		node_color='grey',
		label='Other',
		node_size=12
	)
	if labels:
		nx.draw_networkx_labels(
			inGraph,
			pos,
			ax=ax,
			font_color='black',
			font_weight='bold',
			font_size=0.25
		)

if __name__ == "__main__":
	fig, ax = plt.subplots()
	hazard = HazardField("../static/testFiles/wf_clip.asc")
	hazard.generateHeatMap(ax)

	with open('feederFile.txt', 'r') as feederFile, open('damageFile.txt', 'r') as damageFile, open('critLoads.txt', 'r') as critFile:
		feederModel = json.loads(feederFile)
		damageDict = json.loads(damageFile)
		critLoads = json.loads(critLoads)

	genDiagram('.', feederModel, damageDict, critLoads, ax)

	plt.show()
	fig.savefig('result.png')
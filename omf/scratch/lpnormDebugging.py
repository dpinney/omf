from matplotlib import pyplot as plt
import networkx as nx
import numpy as np
import os
import pandas as pd
import random
import shutil

def generateShapeGraphs(testDir, G):
	''' Generate examples with different shapes. '''

	nx.draw(G, with_labels=True, node_color = "skyblue") # Default.
	plt.savefig(testDir + '/Round example.png')
	plt.clf()
	nx.draw(G, with_labels=True, node_color = "skyblue", node_shape="s")
	plt.savefig(testDir + '/Square example.png')
	plt.clf()
	nx.draw(G, with_labels=True, node_color = "skyblue", node_shape="d")
	plt.savefig(testDir + '/Diamond example.png')
	plt.clf()


def generateEdgeStyles(testDir, G):
	''' Generate different edge styles. '''

	nx.draw(G, with_labels=True, node_color = "skyblue", node_shape="s", style="solid") # Square.
	plt.savefig(testDir + '/Solid example.png')
	plt.clf()
	nx.draw(G, with_labels=True, node_color = "skyblue", node_shape="s", style="dotted")
	plt.savefig(testDir + '/Dotted example.png')
	plt.clf()
	nx.draw(G, with_labels=True, node_color = "skyblue", node_shape="s", style="dashed")
	plt.savefig(testDir + '/Dash example.png')
	plt.clf()
	nx.draw(G, with_labels=True, node_color = "skyblue", node_shape="s", style="solid", edge_color="green") # Color edges.
	plt.savefig(testDir + '/Colored example.png')
	plt.clf()

def generateNodeBorderWidths(testDir, G):
	''' Alter values of border edges around the nodes. ''' 

	borderValues = np.linspace(0, 2, 21)
	for value in borderValues:
		nx.draw(G, with_labels=True, linewidths=value)
		plt.savefig(testDir + '/' + str(float(value)) + ' example.png')
		plt.clf()

def generateDependentGraph(testDir):
	''' Demonstrate how you can change selected properties according to edge attributes. '''

	G = nx.Graph() # Easier to do a seperate example here.
	G.add_edge('A', 'B', color='y', weight=2)
	G.add_edge('B', 'C', color='r', weight=4)
	G.add_edge('C', 'D', color='g', weight=6)

	pos = nx.random_layout(G)


	colors = [G[u][v]['color'] for u,v in G.edges()]
	weights = [G[u][v]['weight'] for u,v in G.edges()]

	nx.draw(G, pos, edges=G.edges(), edge_color=colors, width=weights)
	plt.savefig(testDir + '/Dependent Example.png')
	plt.clf()

def generateNodeColors(testDir):
	''' Generate a graph with varying colors depending on the node value. '''

	G = nx.Graph() # Just going to use this until I get the multigraph to work.
	G.add_edges_from(
    [('A', 'B'), ('A', 'C'), ('D', 'B'), ('E', 'C'), ('E', 'F'),
     ('B', 'H'), ('B', 'G'), ('B', 'F'), ('C', 'G')])

	val_map = {'A': 1.0,
           'D': 0.5714285714285714,
           'H': 0.0}

	values = [val_map.get(node, 0.25) for node in G.nodes()]

	nx.draw(G, cmap=plt.get_cmap('viridis'), node_color=values, with_labels=True, font_color='white')
	plt.savefig('Colorful Copied Example.png')
	plt.clf() 

	#G = nx.MultiDiGraph() # For added fun, we'll allow for multiple edges and self loops. Apparently, using OrderDict, you can track the order nodes and neighbors are added.
	#G.add_edge(1, 2, key=5, attr_dict={'A': 'a', 'B': {'C': 'c', 'D': 'd'}}))




def generateAlphaLevels(testDir, G):
	''' Generate a graph with varying transparency values. '''

	alphaValues = np.linspace(0, 1, 11)
	for value in alphaValues:
		nx.draw(G, with_labels=True, alpha=value)
		plt.savefig(testDir + '/' + str(float(value)) + ' example.png')
		plt.clf()

def labelStyles(testDir, G):
	pass

def positionalStyles(testDir, G):
	pass

def generateGraphs(testDirs):
	''' Master function for networkx generation. ''' 

	df = pd.DataFrame({ 'from':['A', 'B', 'C','A'], 'to':['D', 'A', 'E','C']})
	G = nx.from_pandas_dataframe(df, 'from', 'to')

	for pathName in testDirs:
		newPath = os.path.join('.', pathName)
		if not os.path.exists(newPath):
			os.makedirs(newPath)

	generateShapeGraphs(testDirs[0], G)
	generateEdgeStyles(testDirs[1], G)
	generateDependentGraph(testDirs[1])
	generateNodeBorderWidths(testDirs[2], G)
	generateNodeColors(testDirs[3])
	generateAlphaLevels(testDirs[4], G)

def cleanUp(testDirs):
	for roots, dirs, files in os.walk("."):
		for directory in dirs:
			if directory in testDirs:
				shutil.rmtree(directory)

if __name__ == "__main__":
	testDirs = ['shapeExamples', 'edgeExamples', 'nodeBorderExamples', 'colorExamples', 'alphaExamples']
	testGraph = generateGraphs(testDirs)




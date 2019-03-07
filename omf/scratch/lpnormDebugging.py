from matplotlib import pyplot as plt
import networkx as nx
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

def generateNodeColors(testDir, G):

	nx.draw(G, with_labels=True, node_shape="s", style="solid") # Default.
	plt.savefig(testDir + '/Solid example.png')
	plt.clf()
	nx.draw(G, with_labels=True, node_color = "skyblue", node_shape="s", style="dotted")
	plt.savefig(testDir + '/Dotted example.png')
	plt.clf()
	nx.draw(G, with_labels=True, node_color = "skyblue", node_shape="s", style="dashed")
	plt.savefig(testDir + '/Dash example.png')
	plt.clf()

def alphaLevels(testDir, G):
	pass

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

def cleanUp(testDirs):
	for roots, dirs, files in os.walk("."):
		for directory in dirs:
			if directory in testDirs:
				shutil.rmtree(directory)

if __name__ == "__main__":
	testDirs = ['shapeExamples', 'edgeExamples', 'colorExamples']
	testGraph = generateGraphs(testDirs)




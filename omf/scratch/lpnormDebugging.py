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

def generateHeatMap(ax):

	cmap = plt.cm.Greys
	cmap._init()
	cmap._lut[:, -1] = np.linspace(0, 1, 259)


	heatMap = ax.imshow(
		np.random.rand(5, 5),
		cmap = cmap,
		alpha = .7,
		interpolation = 'nearest',
		extent = [0,1,0,1],
		aspect='auto')

# Drawing networkX graph with lots of styles.

def generateNetwork(ax):
	G = nx.Graph()
	G.add_nodes_from([1, 2, 3, 4])
	G.add_edges_from([(1, 3), (1, 4), (2, 4)])
	nx.draw(G, ax=ax)

if __name__ == "__main__":
	fig, ax = plt.subplots()
	generateHeatMap(ax)
	generateNetwork(ax)
	plt.show()
	fig.savefig('result.png')
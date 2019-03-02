from omf import geo, feeder
import json, os, shutil
import networkx as nx
from os.path import join as pJoin
from omf.feeder import _obToCol
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

def kMean(pathToOmdFile):
	'''
	Use kmeans algo for clustering points for omd representation.
	'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = feeder.treeToNxGraph(tree)
	numpyGraph = np.array([nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')])
	plt.switch_backend('TKAgg')
	plt.scatter(numpyGraph[:,0], numpyGraph[:,1], s=50, c='b')
	#plt.show()
	print(numpyGraph.size)

	Kmean = KMeans(n_clusters=50)

	#Kmean.fit(X)
	Kmean.fit(numpyGraph)
	#print(numpyGraph.size)
	#print(Kmean.cluster_centers_)
	plt.scatter(Kmean.cluster_centers_[:,0], Kmean.cluster_centers_[:,1], s=50, c='r')
	#for all edges that connect to this one, delete, for ones that extend out, change the value
	plt.show()

if __name__ == '__main__':
	kMean('../../static/publicFeeders/Olin Barre LatLon.omd')
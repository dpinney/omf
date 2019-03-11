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
	#Numpy array with nodeName, latitude, longitude
	numpyGraph = np.array([[node,
		float(nx.get_node_attributes(nxG, 'pos')[node][0]), float(nx.get_node_attributes(nxG, 'pos')[node][1])]
		for node in nx.get_node_attributes(nxG, 'pos')], dtype=object)
	print(numpyGraph[:,1:3])
	plt.switch_backend('TKAgg')
	#plt.scatter(numpyGraph[:,1], numpyGraph[:,2], s=20, c='b')
	#plt.show()
	print(numpyGraph.size)
	Kmean = KMeans(n_clusters=25)
	Kmean.fit(numpyGraph[:,1:3])
	#plt.scatter(Kmean.cluster_centers_[:,0], Kmean.cluster_centers_[:,1], s=50, c='r')
	#plt.show()
	centerNodes = Kmean.cluster_centers_
	#print([i for i in Kmean.labels_])
	#print(Kmean.cluster_centers_[0])
	labelsArray = Kmean.labels_
	#for i in labelsArray:
		#print(i)
	#	print(centerNodes[i])
	#print(labelsArray)
	clusterDict = {i: numpyGraph[np.where(Kmean.labels_ == i)] for i in range(Kmean.n_clusters)}
	#print(clusterDict)
	#fish = (n for n,d in nxG.nodes(data=True) if d is not None)
	#print(next(fish))
	#print(next(fish))
	#Go through each cluster in the cluster dict
	#Get the lat lon
	#Get the nodes edges
	#If the edges are in the same cluster, remove it
	#Else if the edge connects to another cluster, check if it exists, and if not add an edge from cluster to node that isn't in the cluster  
	#Potetntially add the clustername to the original graph?
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	newGraph = nx.Graph()
	for centerNode in clusterDict:
		currentClusterGroup = clusterDict[centerNode]
		newGraph.add_node('centroid'+str(centerNode),attr_dict={'type':'centroid', 'pos': (centerNodes[centerNode][0], centerNodes[centerNode][1])})
	#print(node_positions)
	print(nx.number_of_edges(nxG))
	for centerNode in clusterDict:
		currentClusterGroup = clusterDict[centerNode]
		#print(currentClusterGroup)
		#print(centerNodes[centerNode][0])
		nxG.add_node('centroid'+str(centerNode),attr_dict={'type':'centroid', 'pos': (centerNodes[centerNode][0], centerNodes[centerNode][1])})
		for i in currentClusterGroup:
			#print('numpy in cluster group '+str(i[0]))
			#print(nx.get_node_attributes(nxG, 'pos')[node])
			#print(nxG)
			currentNode = i[0]
			neighbors = nx.neighbors(nxG, currentNode)
			#check if nodes are in same cluster
			for neighbor in neighbors:
				if currentNode == 'node1764317720' and neighbor == 'node1772017699':
					print('here')
				#print(nx.get_node_attributes(nxG, 'type')[neighbor])
				if nx.get_node_attributes(nxG, 'type')[neighbor] is 'centroid':
					print(neighbor)
					newGraph.add_edge('centroid'+str(centerNode), neighbor)
					nxG.remove_edge(currentNode, neighbor)
				elif neighbor not in currentClusterGroup[:,0]:
					nxG.add_edge('centroid'+str(centerNode), neighbor)
					#pass
				else:
					nxG.remove_edge(currentNode, neighbor)
					#print('same')
	print(nx.number_of_edges(nxG))

	#print(clusterDict[0][0][0])
	print(nxG.edges())
	nxG.add_node('test')
	nx.set_node_attributes(nxG, 'test', 'test')
	nx.get_node_attributes(nxG, 'test')
	print(nxG.number_of_nodes())
	node_positions = {node: nx.get_node_attributes(newGraph, 'pos')[node] for node in nx.get_node_attributes(newGraph, 'pos')}
	nx.draw_networkx(newGraph, pos=node_positions, nodelist=[node for node in nxG if node in nx.get_node_attributes(newGraph, 'pos')], with_labels=False, node_size=2, edge_size=1)
	plt.scatter(Kmean.cluster_centers_[:,0], Kmean.cluster_centers_[:,1], s=50, c='r')
	plt.show()
	#print(nxG.nodes())

	#for i in centerNodes:
		#nxG.add_node('center', attr_dict={'type':'center'})
		#print(nx.get_node_attributes(nxG,'center'))
		#print float(i[1])

if __name__ == '__main__':
	kMean('../../static/publicFeeders/Olin Barre LatLon.omd')
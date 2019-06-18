from __future__ import division
from pyproj import Proj, transform, Geod
import webbrowser
import omf, json, warnings, networkx as nx, matplotlib, numpy as np, os, shutil, math, requests, tempfile, random
from matplotlib import pyplot as plt
from omf.feeder import _obToCol
from scipy.spatial import ConvexHull
from os.path import join as pJoin
from sklearn.cluster import KMeans
from flask import Flask, send_file, render_template

def treeToNxGraph(inTree):
	''' Convert feeder tree to networkx graph. '''
	outGraph = nx.Graph()
	for key in inTree:
		item = inTree[key]
		if 'name' in item.keys():
			if 'parent' in item.keys():
				outGraph.add_edge(item['name'],item['parent'], attr_dict={'type':'parentChild','phases':1})
				outGraph.node[item['name']]['type']=item['object']
				if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
				# Note that attached houses via gridEdit.html won't have lat/lon values, so this try is a workaround.
				try: outGraph.node[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
				except: outGraph.node[item['name']]['pos']=(0.0,0.0)
			elif 'from' in item.keys():
				myPhase = _phaseCount(item.get('phases','AN'))
				outGraph.add_edge(item['from'],item['to'],attr_dict={'name':item.get('name',''),'type':item['object'],'phases':myPhase})
			elif item['name'] in outGraph:
				# Edge already led to node's addition, so just set the attributes:
				outGraph.node[item['name']]['type']=item['object']
				if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
			else:
				outGraph.add_node(item['name'],attr_dict={'type':item['object']})
				if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
			if 'latitude' in item.keys() and 'longitude' in item.keys():
				try: outGraph.node.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
				except: outGraph.node.get(item['name'],{})['pos']=(0.0,0.0)
	return outGraph

def treeToDiNxGraph(inTree):
	''' Convert feeder tree to a DIRECTED networkx graph. '''
	outGraph = nx.DiGraph()
	network_objects = ['regulator', 'overhead_line', 'underground_line', 'transformer', 'fuse', 'switch', 'triplex_line', 'node', 'triplex_node', 'meter', 'triplex_meter', 'load', 'triplex_load', 'series_reactor']
	for key in inTree:
		item = inTree[key]
		if 'object' in item:
			if item['object'] == 'switch':
				if 'OPEN' in item.values(): #super hacky
					continue
		if 'name' in item.keys():#sometimes network objects aren't named!
			if 'parent' in item.keys():
				outGraph.add_edge(item['parent'], item['name'], attr_dict={'type':'parentChild','phases':1, 'length': 0})#jfk. swapped from,to
				outGraph.node[item['name']]['type']=item['object']
				outGraph.node[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
				if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
			elif 'from' in item.keys():
				myPhase = _phaseCount(item.get('phases','AN'))
				outGraph.add_edge(item['from'],item['to'],attr_dict={'type':item['object'],'phases':myPhase, 'length': float(item.get('length',0))})
				if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
			elif item['name'] in outGraph:
				# Edge already led to node's addition, so just set the attributes:
				outGraph.node[item['name']]['type']=item['object']
				if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
			else:
				outGraph.add_node(item['name'],attr_dict={'type':item['object']})
			if 'latitude' in item.keys() and 'longitude' in item.keys():
				outGraph.node.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
			if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
		elif 'object' in item.keys() and item['object'] in network_objects:#when name doesn't exist
			if 'from' in item.keys():
				myPhase = _phaseCount(item.get('phases','AN'))
				outGraph.add_edge(item['from'],item['to'],attr_dict={'type':item['object'],'phases':myPhase, 'length': float(item.get('length',0))})
			if 'latitude' in item.keys() and 'longitude' in item.keys():
				outGraph.node.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
			if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
	return outGraph

def _phaseCount(phaseString):
	''' Return number of phases not including neutrals. '''
	return sum([phaseString.lower().count(x) for x in ['a','b','c']])

def createGraph(pathToOmdFile):
	'''Create networkxgraph from omd'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = treeToDiNxGraph(tree)
	#use conversion for testing other feeders
	nxG = graphValidator(pathToOmdFile, nxG)
	return nxG

def getSubstation(nxG):
	'''Get the substation node from a feeder'''
	return [sub for sub in nx.get_node_attributes(nxG, 'substation')][0]

def setFiber(nxG, edgeType='switch'):
	'''Set fiber on path between certain edgeType (switch is the defualt for now) and the substation'''
	node_positions = {nodewithPosition: nxG.node[nodewithPosition]['pos'] for nodewithPosition in nx.get_node_attributes(nxG, 'pos')}
	edge_types = {edge: nxG[edge[0]][edge[1]]['type'] for edge in nx.get_edge_attributes(nxG, 'type')}
	substation = getSubstation(nxG)
	for node in node_positions:
		for edge in nxG.out_edges(node):
			if edge_types.get(edge,'') == edgeType:
				nxG.node[node]['transmitter'] = True
				nxG.node[node]['bandwidthCapacity'] = 10**4
				shortestPath = nx.bidirectional_shortest_path(nxG, substation, node)
				for i in range(len(shortestPath)-1):
					nxG[shortestPath[i]][shortestPath[i+1]]['fiber'] = True
					nxG[shortestPath[i]][shortestPath[i+1]]['bandwidthUse'] = 0
					nxG[shortestPath[i]][shortestPath[i+1]]['bandwidthCapacity'] = 10**6

def getDistance(nxG, start, end):
	'''Get the distance between two points in a graph'''
	dist = math.sqrt( (nxG.node[end]['pos'][1] - nxG.node[start]['pos'][1])**2 + (nxG.node[end]['pos'][0] - nxG.node[start]['pos'][0])**2 )
	return dist

def findNearestPoint(nxG, reciever, transmitters):
	'''Find the nearest point for a reciever based on a list of transmitters'''
	nearest = min(transmitters, key = lambda transmitter: getDistance(nxG, reciever, transmitter))
	return nearest

def setRF2(nxG):
	'''Add rf edges between recievers and the nearest transmitter'''
	recievers = [reciever for reciever in nx.get_node_attributes(nxG, 'type') if nxG.node[reciever]['type'] in ['meter', 'triplex_meter']]
	transmitters = [transmitter for transmitter  in nx.get_node_attributes(nxG, 'transmitter')]
	for reciever in recievers:
		transmitter = findNearestPoint(nxG, reciever, transmitters)
		nxG.add_edge(transmitter, reciever,attr_dict={'rf': True, 'bandwidthCapacity': (10**3 * 5)})
		nxG.node[reciever]['bandwidthUse'] = 1
	
#change this to be nearest
def setRF(nxG):
	'''Add RF lines to  '''
	node_positions = {nodewithPosition: nxG.node[nodewithPosition]['pos'] for nodewithPosition  in nx.get_node_attributes(nxG, 'pos')}
	substation = getSubstation(nxG)
	for node in node_positions:
		if nxG.out_degree(node) == 0:
			found = False
			current = node
			while not found and current != substation:
				for pred in nxG.predecessors(current):
					if nxG.node[pred].get('transmitter','') == True:
						nxG.add_edge(pred, node,attr_dict={'rf': True})
						found = True
				current = pred

def calcEdgeLengths(nxG):
	'''Calculate the lengths of edges based on lat/lon position'''
	G = Geod(ellps='WGS84')
	for edge in nx.edges(nxG):
		nxG[edge[0]][edge[1]]['length'] = G.inv(nxG.node[edge[0]]['pos'][1], nxG.node[edge[0]]['pos'][0], nxG.node[edge[1]]['pos'][1], nxG.node[edge[1]]['pos'][0])[2]

def getFiberCost(nxG, fiberCostPerMeter):
	'''Calculate the cost of fiber'''
	fiber_cost = sum((nxG[edge[0]][edge[1]]['length'])*fiberCostPerMeter for edge in nx.get_edge_attributes(nxG, 'fiber'))
	return fiber_cost

def getTransmittersCost(nxG, transmitterCost):
	'''Calculate the cost of RF transmitter equipment'''
	transmitter_cost = len([transmitter for transmitter  in nx.get_node_attributes(nxG, 'transmitter')])*transmitterCost
	return transmitter_cost

def getRecieversCost(nxG, recieverCost):
	'''Calculate the cost of RF reciever equipment'''
	reciever_cost = len([reciever for reciever in nx.get_node_attributes(nxG, 'type') if nxG.node[reciever]['type'] in ['meter', 'triplex_meter']])*recieverCost
	return reciever_cost

'''
node10310x2-Ax110310x2-Bx1
(32.98452635678161, -102.75866843482896)
node10310x2-Bx1960605
(32.98452635678161, -102.75866843482896)
node7875x1-Ax17875x1-Bx1
(32.99212825739565, -102.75846672260337)
node533x1-Bx1824834
(32.989693741841, -102.76565214046761)
node7875x1-Bx1824971
(32.99212825739565, -102.75846672260337)
node533x1-Ax1533x1-Bx1
(32.989693741841, -102.76565214046761)
'''

def calcBandwidth(nxG):
	#go through transmitters and recievers
	#adust later to accept different lengh of transmitters
	substation = getSubstation(nxG)
	nxG.node[substation]['bandwidthUse'] = 0
	transmitters = [transmitter for transmitter  in nx.get_node_attributes(nxG, 'transmitter')]
	#print(len(transmitters))
	for transmitter in transmitters:
		nxG.node[transmitter]['bandwidthUse'] = 0
		#print(transmitter)
		#print(nxG.node[transmitter]['pos'])
		#print(nxG.successors(transmitter))
		#if transmitter == 'node10310x2-Bx1960605':
			#print(nxG.successors(transmitter))
			#print('node')
		for reciever in nxG.successors(transmitter):
			if nxG[transmitter][reciever].get('rf',False):
				nxG[transmitter][reciever]['bandwidthUse'] = nxG.node[reciever]['bandwidthUse']
				nxG.node[transmitter]['bandwidthUse'] += nxG.node[reciever]['bandwidthUse']
		shortestPath = nx.bidirectional_shortest_path(nxG, substation, transmitter)
		for i in range(len(shortestPath)-1):
			nxG[shortestPath[i]][shortestPath[i+1]]['bandwidthUse'] += nxG.node[transmitter]['bandwidthUse']
		nxG.node[substation]['bandwidthUse'] += nxG.node[transmitter]['bandwidthUse']


def graphGeoJson(nxG):
	geoJsonDict = {
	"type": "FeatureCollection",
	"features": []
	}
	node_positions = {nodewithPosition: nxG.node[nodewithPosition]['pos'] for nodewithPosition  in nx.get_node_attributes(nxG, 'pos')}
	node_types = {nodewithType: nxG.node[nodewithType]['type'] for nodewithType in nx.get_node_attributes(nxG, 'type')}
	for node in node_positions:
		geoJsonDict['features'].append({
			"type": "Feature", 
			"geometry":{
				"type": "Point",
				"coordinates": [node_positions[node][1], node_positions[node][0]]
			},
			"properties":{
				"name": node,
				"pointType": node_types.get(node,''),
				"substation": nxG.node[node].get('substation',False),
				"transmitter": nxG.node[node].get('transmitter',False),
				"bandwidthUse": nxG.node[node].get('bandwidthUse',''),
				"bandwidthCapacity": nxG.node[node].get('bandwidthCapacity','')

			}
		})
	#Add edges to geoJSON
	edge_types = {edge: nxG[edge[0]][edge[1]]['type'] for edge in nx.get_edge_attributes(nxG, 'type')}
	for edge in nx.edges(nxG):
		geoJsonDict['features'].append({
			"type": "Feature", 
			"geometry":{
				"type": "LineString",
				"coordinates": [[node_positions[edge[0]][1], node_positions[edge[0]][0]],[node_positions[edge[1]][1], node_positions[edge[1]][0]]]
			},
			"properties":{
				"edgeType": edge_types.get(edge,''),
				#"to": nxG[edge[0]][edge[1]].get('to',''),
				"fiber": nxG[edge[0]][edge[1]].get('fiber',False),
				"rf": nxG[edge[0]][edge[1]].get('rf',False),
				"bandwidthUse": nxG[edge[0]][edge[1]].get('bandwidthUse',''),
				"bandwidthCapacity": nxG[edge[0]][edge[1]].get('bandwidthCapacity','')
			}
		})
	return geoJsonDict

def showOnMap(geoJson):
	'''Open a browser to display a geoJSON object on a map.'''
	tempDir = tempfile.mkdtemp()
	shutil.copy('templates/commsNetViz.html', tempDir)
	with open(pJoin(tempDir,'commsGeoJson.js'),"w") as outFile:
		outFile.write("var geojson =")
		json.dump(geoJson, outFile, indent=4)
	webbrowser.open('file://' + pJoin(tempDir,'commsNetViz.html'))

def saveOmc(geoJson, outputPath):
	if not os.path.exists(outputPath):
		os.makedirs(outputPath)
	with open(pJoin(outputPath,'commsGeoJson.omc'),"w") as outFile:
		json.dump(geoJson, outFile, indent=4)

def convertOmd(pathToOmdFile):
	''' Convert sources to networkx graph. Some larger omd files do not have the position information in the tree'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['links']
	nxG = nx.Graph()
	for key in tree:
		#Account for nodes that are missing names when creating edges
		try:
			sourceEdge = key['source']['name']
		except KeyError:
			try:
				sourceEdge = str(key['target']['name']) + ' Source'
			except KeyError:
				sourceEdge = str(key['source']) + ' Missing Name'
		try:
			targetEdge = key['target']['name']
		except KeyError:
			try:
				targetEdge = key['target']['name'] + ' Target'
			except KeyError:
				targetEdge = str(key['target']) + ' Missing Name'

		#nxG.add_edge(key['source']['name'], key['target']['name'])
		nxG.add_edge(sourceEdge, targetEdge)
		nxG.node[sourceEdge]['pos'] = (float(key['source']['y']), float(key['source']['x']))
		nxG.node[targetEdge]['pos'] = (float(key['target']['y']), float(key['target']['x']))
		try:
			nxG.node[sourceEdge]['type'] = key['source']['objectType']
			nxG.node[sourceEdge]['name'] = key['source']['name']
		except KeyError:
			nxG.node[sourceEdge]['type'] = 'Undefined'
		try:
			nxG.node[targetEdge]['type'] = key['target']['objectType']
			nxG.node[targetEdge]['name'] = key['target']['name']
		except KeyError:
			nxG.node[targetEdge]['type'] = 'Undefined'
	for nodeToChange in nx.get_node_attributes(nxG, 'pos'):
		#nxG.node[nodeToChange]['pos'] = (latitudeCenter + nxG.node[nodeToChange]['pos'][1]/latitude_max, longitudeCenter 
		#								+ nxG.node[nodeToChange]['pos'][0]/longitude_max)
		#print(nxG.node[nodeToChange]['pos'][1], nxG.node[nodeToChange]['pos'][0])
		#print(statePlaneToLatLon(nxG.node[nodeToChange]['pos'][1], nxG.node[nodeToChange]['pos'][0]))
		nxG.node[nodeToChange]['pos'] = statePlaneToLatLon(nxG.node[nodeToChange]['pos'][1], nxG.node[nodeToChange]['pos'][0])
	return nxG

def graphValidator(pathToOmdFile, inGraph):
	'''If the nodes/edges positions are not in the tree, the spurces and targets in the links key of the omd.json are used. '''
	try:
		node_positions = {nodewithPosition: inGraph.node[nodewithPosition]['pos'] for nodewithPosition  in nx.get_node_attributes(inGraph, 'pos')}
		for edge in nx.edges(inGraph):
			validator = (node_positions[edge[0]] or nxG.node[edge[1]])
	except KeyError:
		try:
			nxG = latLonValidation(convertOmd(pathToOmdFile))
		except ValueError:
			#No nodes have positions, so create random ones
			nxG = inGraph
			for nodeToChange in nxG.node:
				nxG.node[nodeToChange]['pos'] = (random.uniform(36.9900, 38.8700), random.uniform(-102.0500,-94.5900))
		return nxG
	nxG = latLonValidation(inGraph)
	return nxG

def latLonValidation(inGraph):
	'''Checks if an omd has invalid latlons, and if so, converts to stateplane coordinates or generates random values '''
	#try:
	latitude_min = min([inGraph.node[nodewithPosition]['pos'][1] for nodewithPosition  in nx.get_node_attributes(inGraph, 'pos')])
	longitude_min = min([inGraph.node[nodewithPosition]['pos'][0] for nodewithPosition  in nx.get_node_attributes(inGraph, 'pos')])
	latitude_max = max([inGraph.node[nodewithPosition]['pos'][1] for nodewithPosition  in nx.get_node_attributes(inGraph, 'pos')])
	longitude_max = max([inGraph.node[nodewithPosition]['pos'][0] for nodewithPosition  in nx.get_node_attributes(inGraph, 'pos')])
	if latitude_min < -180 or latitude_max > 180 or longitude_min < -90 or longitude_max > 90:
		for nodeToChange in nx.get_node_attributes(inGraph, 'pos'):
			inGraph.node[nodeToChange]['pos'] = statePlaneToLatLon(inGraph.node[nodeToChange]['pos'][1], inGraph.node[nodeToChange]['pos'][0])
	return inGraph

def statePlaneToLatLon(easting, northing, epsg = None):
	if not epsg:
		# Center of the USA default
		epsg = 26978
	inProj = Proj(init = 'EPSG:' + str(epsg), preserve_units = True)
	outProj = Proj(init = 'EPSG:4326')
	lon, lat = transform(inProj, outProj, easting, northing)
	return (lat, lon)

bitRateEdge = {
	'fiber': 100000000,
	'rf': 50000	
}

bitRatePoint = {
	'substation': 10,
	'fiber': 100000000,
	'rf': 50000	
}

#Amount of data to be transferred (will need to adjust based on sampling rate)
#Sampling rate = 5 mins
#Transfer rate 15 minutes
dataSizes = {
	'meter': 4000,
	'gateway': 0,
	'substation': 0,
	'recloser': 0
}

#1-5 per foot
edgeCosts = {
	'fiber': 3,
	'rf':0
}

#transmitter/tower are associated with the gateway - right now adding tower to all gateways
#meter is for each reciever, added reciever to each meter

pointCosts = {
	'meter': 1000,
	'gateway': 30000,
	'substation': 0,
	'recloser': 0
}

def _tests():
	feeder = createGraph('static/publicFeeders/Olin Barre LatLon.omd')
	setFiber(feeder, edgeType='switch')
	setRF2(feeder)
	calcBandwidth(feeder)
	print('cost of rf transmitter equipment: ' + str(getTransmittersCost(feeder, 10000)))
	print('cost of rf reciever equipment: ' + str(getRecieversCost(feeder, 100)))
	print('cost of fiber: ' + str(getFiberCost(feeder, 4)))
	saveOmc(graphGeoJson(feeder), 'output')
	showOnMap(graphGeoJson(feeder))

if __name__ == '__main__':
	_tests()
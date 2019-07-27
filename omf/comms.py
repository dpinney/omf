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
from collections import defaultdict

def treeToNxGraph(inTree):
	''' Convert feeder tree to networkx graph. '''
	outGraph = nx.Graph()
	for key in inTree:
		item = inTree[key]
		if 'name' in item.keys():
			if 'parent' in item.keys():
				outGraph.add_edge(item['name'],item['parent'], attr_dict={'type':'parentChild'})
				outGraph.node[item['name']]['type']=item['object']
				if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
				# Note that attached houses via gridEdit.html won't have lat/lon values, so this try is a workaround.
				try: outGraph.node[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
				except: outGraph.node[item['name']]['pos']=(0.0,0.0)
			elif 'from' in item.keys():
				outGraph.add_edge(item['from'],item['to'],attr_dict={'name':item.get('name',''),'type':item['object']})
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

def treeToCommsDiNxGraph(inTree):
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
				outGraph.add_edge(item['parent'], item['name'], attr_dict={'type':'parentChild', 'length': 0})#jfk. swapped from,to
				outGraph.node[item['name']]['type']=item['object']
				outGraph.node[item['name']]['pos']=(float(item.get('latitude',0)),float(item.get('longitude',0)))
				if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
			elif 'from' in item.keys():
				outGraph.add_edge(item['from'],item['to'],attr_dict={'type':item['object'], 'length': float(item.get('length',0))})
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
				outGraph.add_edge(item['from'],item['to'],attr_dict={'type':item['object'], 'length': float(item.get('length',0))})
			if 'latitude' in item.keys() and 'longitude' in item.keys():
				outGraph.node.get(item['name'],{})['pos']=(float(item['latitude']),float(item['longitude']))
			if 'bustype' in item.keys():
					outGraph.node[item['name']]['substation'] = True
	return outGraph

def createGraph(pathToOmdFile):
	'''Create networkxgraph from omd'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = treeToCommsDiNxGraph(tree)
	#use conversion for testing other feeders
	nxG = graphValidator(pathToOmdFile, nxG)
	return nxG

def getSubstation(nxG):
	'''Get the substation node from a feeder'''
	return [sub for sub in nx.get_node_attributes(nxG, 'substation')][0]

def setFiber(nxG, edgeType='switch', rfBandwidthCap=1000, fiberBandwidthCap=1000000):
	'''Set fiber on path between certain edgeType (switch is the defualt for now) and the substation'''
	node_positions = {nodewithPosition: nxG.node[nodewithPosition]['pos'] for nodewithPosition in nx.get_node_attributes(nxG, 'pos')}
	edge_types = {edge: nxG[edge[0]][edge[1]]['type'] for edge in nx.get_edge_attributes(nxG, 'type')}
	substation = getSubstation(nxG)
	#collector position will validate that only one collector is added at each position
	collector_positions = []
	for node in node_positions:
		for edge in nxG.out_edges(node):
			if edge_types.get(edge,'') == edgeType:
				if nxG.node[node]['pos'] not in collector_positions:
					collector_positions.append(nxG.node[node]['pos']) 
					nxG.node[node]['rfCollector'] = True
				#move into setRf later
				nxG.node[node]['bandwidthCapacity'] = rfBandwidthCap 
				shortestPath = nx.bidirectional_shortest_path(nxG, substation, node)
				for i in range(len(shortestPath)-1):
					nxG[shortestPath[i]][shortestPath[i+1]]['fiber'] = True
					nxG[shortestPath[i]][shortestPath[i+1]]['bandwidthUse'] = 0
					nxG[shortestPath[i]][shortestPath[i+1]]['bandwidthCapacity'] = fiberBandwidthCap

def getDistance(nxG, start, end):
	'''Get the distance between two points in a graph'''
	dist = math.sqrt( (nxG.node[end]['pos'][1] - nxG.node[start]['pos'][1])**2 + (nxG.node[end]['pos'][0] - nxG.node[start]['pos'][0])**2 )
	return dist

def findNearestPoint(nxG, smartMeter, rfCollectors):
	'''Find the nearest point for a smartMeter based on a list of rfCollectors'''
	nearest = min(rfCollectors, key = lambda rfCollector: getDistance(nxG, smartMeter, rfCollector))
	return nearest

def setRf(nxG, packetSize=10):
	'''Add rf edges between smartMeters and the nearest rfCollector'''
	smartMeters = [smartMeter for smartMeter in nx.get_node_attributes(nxG, 'type') if nxG.node[smartMeter]['type'] in ['meter', 'triplex_meter']]
	rfCollectors = [rfCollector for rfCollector  in nx.get_node_attributes(nxG, 'rfCollector')]
	for smartMeter in smartMeters:
		rfCollector = findNearestPoint(nxG, smartMeter, rfCollectors)
		nxG.add_edge(rfCollector, smartMeter,attr_dict={'rf': True, 'type': 'rf', 'bandwidthCapacity': (10**3 * 5)})
		nxG.node[smartMeter]['bandwidthUse'] = packetSize
		nxG.node[smartMeter]['smartMeter'] = True

def calcEdgeLengths(nxG):
	'''Calculate the lengths of edges based on lat/lon position'''
	G = Geod(ellps='WGS84')
	for edge in nx.edges(nxG):
		nxG[edge[0]][edge[1]]['length'] = G.inv(nxG.node[edge[0]]['pos'][1], nxG.node[edge[0]]['pos'][0], nxG.node[edge[1]]['pos'][1], nxG.node[edge[1]]['pos'][0])[2]

def getFiberCost(nxG, fiberCostPerMeter):
	'''Calculate the cost of fiber'''
	fiber_cost = sum((nxG[edge[0]][edge[1]]['length'])*fiberCostPerMeter for edge in nx.get_edge_attributes(nxG, 'fiber'))
	return fiber_cost

def getrfCollectorsCost(nxG, rfCollectorCost):
	'''Calculate the cost of RF rfCollector equipment'''
	rfCollector_cost = len([rfCollector for rfCollector  in nx.get_node_attributes(nxG, 'rfCollector')])*rfCollectorCost
	return rfCollector_cost

def getsmartMetersCost(nxG, smartMeterCost):
	'''Calculate the cost of RF smartMeter equipment'''
	smartMeter_cost = len([smartMeter for smartMeter in nx.get_node_attributes(nxG, 'type') if nxG.node[smartMeter]['type'] in ['meter', 'triplex_meter']])*smartMeterCost
	return smartMeter_cost

def calcBandwidth(nxG):
	#go through rfCollectors and smartMeters
	#adust later to accept different lengh of rfCollectors
	substation = getSubstation(nxG)
	nxG.node[substation]['bandwidthUse'] = 0
	rfCollectors = [rfCollector for rfCollector  in nx.get_node_attributes(nxG, 'rfCollector')]
	for rfCollector in rfCollectors:
		nxG.node[rfCollector]['bandwidthUse'] = 0
		for smartMeter in nxG.successors(rfCollector):
			if nxG[rfCollector][smartMeter].get('rf',False):
				nxG[rfCollector][smartMeter]['bandwidthUse'] = nxG.node[smartMeter]['bandwidthUse']
				nxG.node[rfCollector]['bandwidthUse'] += nxG.node[smartMeter]['bandwidthUse']
		shortestPath = nx.bidirectional_shortest_path(nxG, substation, rfCollector)
		for i in range(len(shortestPath)-1):
			nxG[shortestPath[i]][shortestPath[i+1]]['bandwidthUse'] += nxG.node[rfCollector]['bandwidthUse']
		nxG.node[substation]['bandwidthUse'] += nxG.node[rfCollector]['bandwidthUse']

def graphGeoJson(nxG):
	'''Create geojson dict for omc file type for communications network'''
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
				"rfCollector": nxG.node[node].get('rfCollector',False),
				"smartMeter": nxG.node[node].get('smartMeter',False),
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

def saveOmc(geoJson, outputPath, fileName=None):
	'''Save comms geojson dict as .omc proprietary format (it is a geojson)'''
	if fileName is None:
		fileName = 'commsGeoJson'
	if not os.path.exists(outputPath):
		os.makedirs(outputPath)
	with open(pJoin(outputPath, fileName + '.omc'),"w") as outFile:
		json.dump(geoJson, outFile, indent=4)

def convertOmd(pathToOmdFile):
	''' Convert sources to networkx graph. Some larger omd files do not have the position information in the tree'''
	with open(pathToOmdFile) as inFile:
		omdFile = json.load(inFile)
		links = omdFile['links']
		tree = omdFile['tree']
	nxG = nx.DiGraph()
	objectNodes = set()
	for key in links:
		objectNodes.add(key['objectType'])
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
		sourceTreeIndex = str(key['source']['treeIndex'])
		targetTreeIndex = str(key['target']['treeIndex'])
		try:
			nxG.node[sourceEdge]['type'] = tree[sourceTreeIndex]['object']
			nxG.node[sourceEdge]['name'] = key['source']['name']
			#Get substation - fix later because this seems a little hacky
			if tree[sourceTreeIndex]['bustype'] == 'SWING':
				nxG.node[sourceEdge]['substation'] = True
		except KeyError:
			nxG.node[sourceEdge]['type'] = 'Undefined'
		try:
			nxG.node[targetEdge]['type'] = tree[targetTreeIndex]['object']
			nxG.node[targetEdge]['name'] = key['target']['name']
		except KeyError:
			nxG.node[targetEdge]['type'] = 'Undefined'
	for nodeToChange in nx.get_node_attributes(nxG, 'pos'):
		#nxG.node[nodeToChange]['pos'] = (latitudeCenter + nxG.node[nodeToChange]['pos'][1]/latitude_max, longitudeCenter 
		#								+ nxG.node[nodeToChange]['pos'][0]/longitude_max)
		#print(nxG.node[nodeToChange]['pos'][1], nxG.node[nodeToChange]['pos'][0])
		#print(statePlaneToLatLon(nxG.node[nodeToChange]['pos'][1], nxG.node[nodeToChange]['pos'][0]))
		nxG.node[nodeToChange]['pos'] = statePlaneToLatLon(nxG.node[nodeToChange]['pos'][1], nxG.node[nodeToChange]['pos'][0])
	#print(nxG.node)
	return nxG

def graphValidator(pathToOmdFile, inGraph):
	'''If the nodes/edges positions are not in the tree, the spurces and targets in the links key of the omd.json are used. '''
	try:
		node_positions = {nodewithPosition: inGraph.node[nodewithPosition]['pos'] for nodewithPosition  in nx.get_node_attributes(inGraph, 'pos')}
		for edge in nx.edges(inGraph):
			validator = (node_positions[edge[0]] or nxG.node[edge[1]])
	except KeyError:
		raise Exception('Network coordinates are not in the .omd tree. Use the anonymize menu in the circuit editor to generate a circuit with valid coordinates.')
		'''
		This code creates random positional information
		try:
			nxG = latLonValidation(convertOmd(pathToOmdFile))
		except ValueError:
			#No nodes have positions, so create random ones
			nxG = inGraph
			for nodeToChange in nxG.node:
				nxG.node[nodeToChange]['pos'] = (random.uniform(36.9900, 38.8700), random.uniform(-102.0500,-94.5900))
		return nxG'''
	#should invalid lat/lons be included
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

#rfCollector/tower are associated with the gateway - right now adding tower to all gateways
#meter is for each smartMeter, added smartMeter to each meter

pointCosts = {
	'meter': 1000,
	'gateway': 30000,
	'substation': 0,
	'recloser': 0
}

def _tests():
	feeder = createGraph('static/publicFeeders/Olin Barre LatLon.omd')
	setFiber(feeder, edgeType='switch')
	#collectorOverlap(feeder)
	setRf(feeder)
	calcBandwidth(feeder)
	print('cost of rf rfCollector equipment: ' + str(getrfCollectorsCost(feeder, 10000)))
	print('cost of rf smartMeter equipment: ' + str(getsmartMetersCost(feeder, 100)))
	print('cost of fiber: ' + str(getFiberCost(feeder, 4)))
	#rfCollectors = sum([(feeder.node[rfCollector]['bandwidthUse']) for rfCollector  in nx.get_node_attributes(feeder, 'rfCollector')])
	sub = getSubstation(feeder)
	#saveOmc(graphGeoJson(feeder), 'output')
	showOnMap(graphGeoJson(feeder))

if __name__ == '__main__':
	_tests()
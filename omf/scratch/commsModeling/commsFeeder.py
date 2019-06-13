from __future__ import division
from pyproj import Proj, transform
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
	nxG = omf.feeder.treeToDiNxGraph(tree)
	#use conversion for testing other feeders
	nxG = graphValidator(pathToOmdFile, nxG)
	#if conversion:
	#	nxG = convertOmd(pathToOmdFile)
	#print([sub for sub in nx.get_node_attributes(nxG, 'substation')][0])
	return nxG

def oldGeo(inGraph):
	nxG = inGraph
	geoJsonDict = {
	"type": "FeatureCollection",
	"features": []
	}
	#from pyproj import Geod
	#G = Geod(ellps='WGS84')
	#print(G.inv(30, 50, 30.0001, 50.000001)[2])
	#Add nodes to geoJSON
	node_positions = {nodewithPosition: nxG.node[nodewithPosition]['pos'] for nodewithPosition  in nx.get_node_attributes(nxG, 'pos')}
	node_types = {nodewithType: nxG.node[nodewithType]['type'] for nodewithType in nx.get_node_attributes(nxG, 'type')}
	#print(set(node_types.values()))
	edge_types = {edge: nxG[edge[0]][edge[1]]['type'] for edge in nx.get_edge_attributes(nxG, 'type')}
	for node in node_positions:
		for edge in nxG.out_edges(node):

			if edge_types.get(edge,'') == 'switch':
				#print(nxG[edge[0]][edge[1]])
				nxG.node[node]['isHub'] = True
				shortestPath = nx.bidirectional_shortest_path(nxG, 'COLOMA SUB', node)
				for i in range(len(shortestPath)-1):
					#print(nxG[shortestPath[i]][shortestPath[i+1]])
					nxG[shortestPath[i]][shortestPath[i+1]]['fiber'] = True
				#print(edge)
				#print(nxG.node[node])
				#print(nxG[edge[0]][edge[1]].get('type',''))
	for node in node_positions:
		if nxG.out_degree(node) == 0:
			#print(node)
			found = False
			current = node
			while not found and current != 'COLOMA SUB':
				for pred in nxG.predecessors(current):
					#print(pred)
					if nxG.node[pred].get('isHub','') == True:
						nxG.add_edge(pred, node,attr_dict={'rf': True})
						print(nxG[pred][node])
						found = True
				current = pred
	#print(nx.edges(nxG))
	for node in node_positions:
			#print(nxG.node[i].get('type',''))
		#print(nxG.node[node])
		#print(nxG.neighbors(node))
		#print(nxG.succ[node].items())
		#print(nxG.in_degree(node), nxG.out_degree(node))
		geoJsonDict['features'].append({
			"type": "Feature", 
			"geometry":{
				"type": "Point",
				"coordinates": [node_positions[node][1], node_positions[node][0]]
			},
			"properties":{
				"name": node,
				"pointType": node_types.get(node,''),
				"substation": nxG.node[node].get('substation',''),
				"isLeaf": nxG.out_degree(node) == 0,
				"isHub": nxG.node[node].get('isHub','')
				#"pointColor": _obToCol(node_types[node])
			}
		})
	#Add edges to geoJSON
	edge_types = {edge: nxG[edge[0]][edge[1]]['type'] for edge in nx.get_edge_attributes(nxG, 'type')}
	edge_phases = {edge: nxG[edge[0]][edge[1]]['phases'] for edge in nx.get_edge_attributes(nxG, 'phases')}
	#print(set(edge_types.values()))
	edge_phases = {edge: nxG[edge[0]][edge[1]]['rf'] for edge in nx.get_edge_attributes(nxG, 'rf')}
	#print(edge_phases)
	for edge in nx.edges(nxG):
		#print(nxG[edge[0]][edge[1]])
		if nxG[edge[0]][edge[1]].get('rf',''):
			print(True) 
		geoJsonDict['features'].append({
			"type": "Feature", 
			"geometry":{
				"type": "LineString",
				"coordinates": [[node_positions[edge[0]][1], node_positions[edge[0]][0]],[node_positions[edge[1]][1], node_positions[edge[1]][0]]]
			},
			"properties":{
				#"phase": edge_phases[edge],
				"edgeType": edge_types.get(edge,''),
				"to": nxG[edge[0]][edge[1]].get('to',''),
				"fiber": nxG[edge[0]][edge[1]].get('fiber',''),
				"rf": nxG[edge[0]][edge[1]].get('rf','')
				#"edgeColor":_obToCol(edge_types[edge])
			}
		})
	#print(geoJsonDict)
	#out degree is zero if end
	#node_subs = {nodewithType: nxG.node[nodewithType]['substation'] for nodewithType in nx.get_node_attributes(nxG, 'substation')}
	#for i in node_subs:
	#	print(nxG.node[i])
	#	print(nxG.pred[i].items())
	#	print(nxG.in_degree(i), nxG.out_degree(i))
	#print(node_subs)

	return geoJsonDict
	#if not os.path.exists(outputPath):
	#	os.makedirs(outputPath)
	#shutil.copy('static/geoPolyLeaflet.html', outputPath)
	#with open(pJoin(outputPath,'geoPointsLines.json'),"w") as outFile:
	#	json.dump(geoJsonDict, outFile, indent=4)

def getSubstation(nxG):
	'''Get the substation node from a feeder'''
	return [sub for sub in nx.get_node_attributes(nxG, 'substation')][0]

def setFiber(nxG, edgeType='switch'):
	'''Set fiber on path between certain edgeType (switch is the defualt for now) and the substation'''
	node_positions = {nodewithPosition: nxG.node[nodewithPosition]['pos'] for nodewithPosition  in nx.get_node_attributes(nxG, 'pos')}
	edge_types = {edge: nxG[edge[0]][edge[1]]['type'] for edge in nx.get_edge_attributes(nxG, 'type')}
	substation = getSubstation(nxG)
	for node in node_positions:
		for edge in nxG.out_edges(node):
			if edge_types.get(edge,'') == edgeType:
				nxG.node[node]['isHub'] = True
				shortestPath = nx.bidirectional_shortest_path(nxG, substation, node)
				for i in range(len(shortestPath)-1):
					nxG[shortestPath[i]][shortestPath[i+1]]['fiber'] = True

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
					if nxG.node[pred].get('isHub','') == True:
						nxG.add_edge(pred, node,attr_dict={'rf': True})
						found = True
				current = pred

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
				"substation": nxG.node[node].get('substation',''),
				"isLeaf": nxG.out_degree(node) == 0,
				"isHub": nxG.node[node].get('isHub','')
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
				"to": nxG[edge[0]][edge[1]].get('to',''),
				"fiber": nxG[edge[0]][edge[1]].get('fiber',''),
				"rf": nxG[edge[0]][edge[1]].get('rf','')
			}
		})
	return geoJsonDict

def showOnMap(geoJson):
	'''Open a browser to display a geoJSON object on a map.'''
	tempDir = tempfile.mkdtemp()
	shutil.copy('commsMap.html', tempDir)
	with open(pJoin(tempDir,'commsGeoJson.js'),"w") as outFile:
		outFile.write("var geojson =")
		json.dump(geoJson, outFile, indent=4)
	webbrowser.open('file://' + pJoin(tempDir,'commsMap.html'))

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

feeder = createGraph('../../static/publicFeeders/Olin Barre LatLon.omd')
setFiber(feeder, edgeType='switch')
setRF(feeder)
showOnMap(graphGeoJson(feeder))
#showOnMap(omdGeoJson('../../static/publicFeeders/Olin Barre LatLon.omd'))
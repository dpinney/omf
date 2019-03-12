from __future__ import division
from pyproj import Proj, transform
import webbrowser
import omf, json, warnings, networkx as nx, matplotlib, numpy as np, os, shutil, math
from matplotlib import pyplot as plt
from omf.feeder import _obToCol
from scipy.spatial import ConvexHull
from os.path import join as pJoin
from sklearn.cluster import KMeans

# Source: https://github.com/fitnr/stateplane/blob/master/stateplane/dicts.py
# These are NAD83 EPSG identifiers.
# If you need others like NAD27, try https://epsg.io
shortToEpsg = {"AK_1":26931,"AK_2":26932,"AK_3":26933,"AK_4":26934,"AK_5":26935,"AK_6":26936,"AK_7":26937,"AK_8":26938,"AK_9":26939,"AK_10,":26940,"AL_E":26929,"AL_W":26930,"AR_N":26951,"AR_S":26952,"AZ_C":26949,"AZ_E":26948,"AZ_W":26950,"CA_1":26941,"CA_2":26942,"CA_3":26943,"CA_4":26944,"CA_5":26945,"CA_6":26946,"CO_C":26954,"CO_N":26953,"CO_S":26955,"CT":26956,"DE":26957,"FL_E":26958,"FL_N":26960,"FL_W":26959,"GA_E":26966,"GA_W":26967,"HI_1":26961,"HI_2":26962,"HI_3":26963,"HI_4":26964,"HI_5":26965,"IA_N":26975,"IA_S":26976,"ID_C":26969,"ID_E":26968,"ID_W":26970,"IL_E":26971,"IL_W":26972,"IN_E":26973,"IN_W":26974,"KS_N":26977,"KS_S":26978,"KY_N":2205,"KY_S":26980,"LA_N":26981,"LA_S":26982,"MA_I":26987,"MA_M":26986,"MD":26985,"ME_E":26983,"ME_W":26984,"MI_C":26989,"MI_N":26988,"MI_S":26990,"MN_C":26992,"MN_N":26991,"MN_S":26993,"MO_C":26997,"MO_E":26996,"MO_W":26998,"MS_E":26994,"MS_W":26995,"MT":32100,"NC":32119,"ND_N":32120,"ND_S":32121,"NE":32104,"NH":32110,"NJ":32111,"NM_C":32113,"NM_E":32112,"NM_W":32114,"NV_C":32108,"NV_E":32107,"NV_W":32109,"NY_C":32116,"NY_E":32115,"NY_LI":32118,"NY_W":32117,"OH_N":32122,"OH_S":32123,"OK_N":32124,"OK_S":32125,"OR_N":32126,"OR_S":32127,"PA_N":32128,"PA_S":32129,"RI":32130,"SC":32133,"SD_N":32134,"SD_S":32135,"TN":32136,"TX_C":32139,"TX_N":32137,"TX_NC":32138,"TX_S":32141,"TX_SC":32140,"UT_C":32143,"UT_N":32142,"UT_S":32144,"VA_N":32146,"VA_S":32147,"VT":32145,"WA_N":32148,"WA_S":32149,"WI_C":32153,"WI_N":32152,"WI_S":32154,"WV_N":32150,"WV_S":32151,"WY_E":32155,"WY_EC":32156,"WY_W":32158,"WY_WC":32157}

# Reverse above dict to map in the other direction.
epsgToShort = {v: k for k, v in shortToEpsg.items()}

def statePlaneToLatLon(easting, northing, epsg = None):
	if not epsg:
		# Center of the USA default
		epsg = 26978
	inProj = Proj(init = 'EPSG:' + str(epsg), preserve_units = True)
	outProj = Proj(init = 'EPSG:4326')
	lon, lat = transform(inProj, outProj, easting, northing)
	return (lat, lon)

def latLonToStatePlane(lat, lon, epsg = None):
	if not epsg:
		# Center of the USA default
		epsg = 26978
	inProj = Proj(init = 'EPSG:4326')
	outProj = Proj(init = 'EPSG:' + str(epsg), preserve_units = True)
	easting, northing = transform(inProj, outProj, lon, lat)
	return (easting, northing)

def dd2dms(dd):
	'Decimal degrees to Degrees/Minutes/Seconds'
	d = int(dd)
	md = abs(dd - d) * 60
	m = int(md)
	sd = (md - m) * 60
	return (d, m, sd)

def dms2dd(degrees, minutes, seconds, direction):
	'Degree/minute/second to decimal degrees'
	dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
	if direction == 'E' or direction == 'N':
		dd *= -1
	return dd;

def openInGoogleMaps(lat, lon):
	"Open a browser to the (lat, lon) in Google Maps"
	loc = 'https://www.google.com/maps/place/{}+{}/'.format(lat,lon)
	webbrowser.open_new(loc)

def hullOfOmd(pathToOmdFile):
	'''Convex hull of an omd in the form of a geojson dictionary with a single ploygon.'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = omf.feeder.treeToNxGraph(tree)
	points = np.array([nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')])
	hull = ConvexHull(points)
	polygon = points[hull.vertices].tolist()
	for point in polygon:
		point.reverse()
	#Add first node to beginning to comply with geoJSON standard
	polygon.append(polygon[0])
	#Create dict and bump to json file
	geoJsonDict = {"type": "FeatureCollection",
		"features": [{
			"type": "Feature", 
			"geometry":{
				"type": "Polygon",
				"coordinates": [polygon]
			}
		}]
	}
	return geoJsonDict

def omdGeoJson(pathToOmdFile, outputPath):
	'''Create a geojson standards compliant file (https://tools.ietf.org/html/rfc7946) from an omd.'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	geoJsonDict = {
	"type": "FeatureCollection",
	"features": []
	}
	#Add nodes to geoJSON
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	node_types = {node: nx.get_node_attributes(nxG, 'type')[node] for node in nx.get_node_attributes(nxG, 'type')}
	for node in node_positions:
		geoJsonDict['features'].append({
			"type": "Feature", 
			"geometry":{
				"type": "Point",
				"coordinates": [node_positions[node][1], node_positions[node][0]]
			},
			"properties":{
				"name": node,
				"pointType": node_types[node],
				"pointColor": _obToCol(node_types[node])
			}
		})
	#Add edges to geoJSON
	edge_types = {edge: nx.get_edge_attributes(nxG, 'type')[edge] for edge in nx.get_edge_attributes(nxG, 'type')}
	edge_phases = {edge: nx.get_edge_attributes(nxG, 'phases')[edge] for edge in nx.get_edge_attributes(nxG, 'phases')}
	for edge in nx.edges(nxG):
		geoJsonDict['features'].append({
			"type": "Feature", 
			"geometry":{
				"type": "LineString",
				"coordinates": [[node_positions[edge[0]][1], node_positions[edge[0]][0]],[node_positions[edge[1]][1], node_positions[edge[1]][0]]]
			},
			"properties":{
				"phase": edge_phases[edge],
				"edgeType": edge_types[edge],
				"edgeColor":_obToCol(edge_types[edge])
			}
		})
	if not os.path.exists(outputPath):
		os.makedirs(outputPath)
	shutil.copy('static/geoPolyLeaflet.html', outputPath)
	with open(pJoin(outputPath,'geoPointsLines.json'),"w") as outFile:
		json.dump(geoJsonDict, outFile, indent=4)

def mapOmd(pathToOmdFile, outputPath, fileFormat):
	'''
	Draw an omd on a map.
	
	fileFormat options: html or png
	Use html option to create a geojson file to be displayed with an interactive leaflet map.
	Use the png file format to create a static png image.
	'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = omf.feeder.treeToNxGraph(tree)
	if fileFormat == 'html':
		geoJsonDict = {
		"type": "FeatureCollection",
		"features": []
		}
		#Add nodes to geoJSON
		node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
		node_types = {node: nx.get_node_attributes(nxG, 'type')[node] for node in nx.get_node_attributes(nxG, 'type')}
		for node in node_positions:
			geoJsonDict['features'].append({
				"type": "Feature", 
				"geometry":{
					"type": "Point",
					"coordinates": [node_positions[node][1], node_positions[node][0]]
				},
				"properties":{
					"name": node,
					"pointType": node_types[node],
					"pointColor": _obToCol(node_types[node])
				}
			})
		#Add edges to geoJSON
		edge_types = {edge: nx.get_edge_attributes(nxG, 'type')[edge] for edge in nx.get_edge_attributes(nxG, 'type')}
		edge_phases = {edge: nx.get_edge_attributes(nxG, 'phases')[edge] for edge in nx.get_edge_attributes(nxG, 'phases')}
		for edge in nx.edges(nxG):
			geoJsonDict['features'].append({
				"type": "Feature", 
				"geometry":{
					"type": "LineString",
					"coordinates": [[node_positions[edge[0]][1], node_positions[edge[0]][0]],[node_positions[edge[1]][1], node_positions[edge[1]][0]]]
				},
				"properties":{
					"phase": edge_phases[edge],
					"edgeType": edge_types[edge],
					"edgeColor":_obToCol(edge_types[edge])
				}
			})
		if not os.path.exists(outputPath):
			os.makedirs(outputPath)
		shutil.copy('static/geoPolyLeaflet.html', outputPath)
		with open(pJoin(outputPath,'geoPointsLines.json'),"w") as outFile:
			json.dump(geoJsonDict, outFile, indent=4)
	elif fileFormat == 'png':
		from mpl_toolkits.basemap import Basemap
		# Be quiet Matplotlib.
		warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)
		# Set up figure.
		plt.axis('off')
		plt.tight_layout()
		plt.gca().invert_yaxis()
		plt.gca().set_aspect('equal')
		plt.switch_backend('TKAgg')

		#Set up basemap for background image
		latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
		longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
		latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
		longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
		m = Basemap(llcrnrlon=longitude_min,llcrnrlat=latitude_min,urcrnrlon=longitude_max,urcrnrlat=latitude_max, epsg=3857)
		m.arcgisimage(service='World_Street_Map', dpi=400, verbose= False)
		#Get positions for graph
		pos = {}
		pos = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
		for point in pos:
			pos[point] = (m(pos[point][1], pos[point][0]))
		# Draw all the edges.
		for e in nxG.edges():
			eType = nxG.edge[e[0]][e[1]].get('type','underground_line')
			ePhases = nxG.edge[e[0]][e[1]].get('phases',1)
			standArgs = {'edgelist':[e],
						 'edge_color':_obToCol(eType),
						 'width':2,
						 'style':{'parentChild':'dotted','underground_line':'dashed'}.get(eType,'solid') }
			if ePhases==3:
				standArgs.update({'width':2})
				nx.draw_networkx_edges(nxG,pos,**standArgs)
				standArgs.update({'width':2,'edge_color':'white'})
				nx.draw_networkx_edges(nxG,pos,**standArgs)
				standArgs.update({'width':1,'edge_color':_obToCol(eType)})
				nx.draw_networkx_edges(nxG,pos,**standArgs)
			if ePhases==2:
				standArgs.update({'width':2})
				nx.draw_networkx_edges(nxG,pos,**standArgs)
				standArgs.update({'width':1,'edge_color':'white'})
				nx.draw_networkx_edges(nxG,pos,**standArgs)
			else:
				nx.draw_networkx_edges(nxG,pos,**standArgs)
		# Draw nodes and optional labels.
		nx.draw_networkx_nodes(nxG,pos,
							   nodelist=pos.keys(),
							   node_color=[_obToCol(nxG.node[n].get('type','underground_line')) for n in nxG],
							   linewidths=0,
							   node_size=2)
		#if labels:
		#	nx.draw_networkx_labels(nxG,pos,
		#							font_color='black',
		#							font_weight='bold',
		#							font_size=0.25)
		if not os.path.exists(outputPath):
			os.makedirs(outputPath)
		plt.savefig(pJoin(outputPath,'latlon.png'), dpi=400, bbox_inches="tight")

def simplifiedOmdShape(pathToOmdFile):
	'''Use kmeans clustering to create simplified geojson object with convex hull and connected clusters from an omd.'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = omf.feeder.treeToNxGraph(tree)

	simplifiedGeoDict = hullOfOmd(pathToOmdFile)
	
	#Kmeans clustering function
	numpyGraph = np.array([[node,
		float(nx.get_node_attributes(nxG, 'pos')[node][0]), float(nx.get_node_attributes(nxG, 'pos')[node][1])]
		for node in nx.get_node_attributes(nxG, 'pos')], dtype=object)
	Kmean = KMeans(n_clusters=20)
	Kmean.fit(numpyGraph[:,1:3])

	#Set up new graph with cluster centers as nodes to use in output
	centerNodes = Kmean.cluster_centers_
	clusterDict = {i: numpyGraph[np.where(Kmean.labels_ == i)] for i in range(Kmean.n_clusters)}
	simplifiedGraph = nx.Graph()
	for centerNode in clusterDict:
		currentClusterGroup = clusterDict[centerNode]
		simplifiedGraph.add_node('centroid'+str(centerNode),attr_dict={'type':'centroid',
			'pos': (centerNodes[centerNode][0], centerNodes[centerNode][1]),
			'clusterSize': np.ma.size(currentClusterGroup,axis=0), 'lineCount': 0})

	#Create edges between cluster centers
	for centerNode in clusterDict:
		currentClusterGroup = clusterDict[centerNode]
		nxG.add_node('centroid'+str(centerNode),attr_dict={'type':'centroid', 'pos': (centerNodes[centerNode][0], centerNodes[centerNode][1])})
		intraClusterLines = 0
		for i in currentClusterGroup:
			currentNode = i[0]
			neighbors = nx.neighbors(nxG, currentNode)
			for neighbor in neighbors:
				#connect centroids
				if nx.get_node_attributes(nxG, 'type')[neighbor] is 'centroid':
					if ('centroid'+str(centerNode), neighbor) not in nx.edges(simplifiedGraph):
						simplifiedGraph.add_edge('centroid'+str(centerNode), neighbor, attr_dict={'type': 'centroidConnector', 'lineCount': 1})
					else:
						simplifiedGraph['centroid'+str(centerNode)][neighbor]['lineCount'] += 1
				#connect centroid to nodes in other clusters, which is replaced in subsequent loops
				elif neighbor not in currentClusterGroup[:,0]:
					nxG.add_edge('centroid'+str(centerNode), neighbor, attr_dict={'type': 'centroidConnector'})
				else:
					simplifiedGraph.node['centroid'+str(centerNode)]['lineCount'] +=1
			if currentNode in simplifiedGraph:
				simplifiedGraph.remove_node(currentNode)

	#Add nodes and edges to dict with convex hull
	for node in simplifiedGraph.node:
		simplifiedGeoDict['features'].append({
			"type": "Feature", 
			"geometry":{
				"type": "Point",
				"coordinates": [simplifiedGraph.node[node]['pos'][1], simplifiedGraph.node[node]['pos'][0]]
			},
			"properties":{
				"name": node,
				"pointType": simplifiedGraph.node[node]['type'],
				"lineCount": simplifiedGraph.node[node]['lineCount']
			}
		})
	#Add edges to dict
	for edge in nx.edges(simplifiedGraph):
		simplifiedGeoDict['features'].append({
			"type": "Feature", 
			"geometry":{
				"type": "LineString",
				"coordinates": [[simplifiedGraph.node[edge[0]]['pos'][1], simplifiedGraph.node[edge[0]]['pos'][0]],
				[simplifiedGraph.node[edge[1]]['pos'][1], simplifiedGraph.node[edge[1]]['pos'][0]]]
			},
			"properties":{
				"lineCount": simplifiedGraph[edge[0]][edge[1]]['lineCount'],
				"edgeType": simplifiedGraph[edge[0]][edge[1]]['type']
			}
		})
	return simplifiedGeoDict

def shortestPathOmd(pathToOmdFile, sourceObjectName, targetObjectName):
	'''Get the shortest path between two points on a feeder'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = omf.feeder.treeToNxGraph(tree)
	tracePath = nx.bidirectional_shortest_path(nxG, sourceObjectName, targetObjectName)
	return tracePath

def numTiles(z):
	''' Helper function to get number of tiles at a given zoom '''
	return(math.pow(2,z))

def sec(x):
	''' Helper fucntion to get secant '''
	return(1/math.cos(x))

def latlon2relativeXY(lat,lon):
	'''Helper function for latlon2xy'''
	x = (lon + 180) / 360
	y = (1 - math.log(math.tan(math.radians(lat)) + sec(math.radians(lat))) / math.pi) / 2
	return(x,y)

def latlon2xy(lat,lon,z):
	'''Helper function to convert lat/lon coordinate to x/y coordinates'''
	n = numTiles(z)
	x,y = latlon2relativeXY(lat,lon)
	return(n*x, n*y)

def tileXY(lat, lon, z):
	'''Helper function to get the tile that contains a lat/lon coordinate at a given zoom level'''
	x,y = latlon2xy(lat,lon,z)
	return(int(x),int(y))

def latEdges(y,z):
	'''Helper function in tileEdges for latitude'''
	n = numTiles(z)
	unit = 1 / n
	relY1 = y * unit
	relY2 = relY1 + unit
	lat1 = mercatorToLat(math.pi * (1 - 2 * relY1))
	lat2 = mercatorToLat(math.pi * (1 - 2 * relY2))
	return(lat1,lat2)

def lonEdges(x,z):
	'''Helper function in tileEdges for longitude'''
	n = numTiles(z)
	unit = 360 / n
	lon1 = -180 + x * unit
	lon2 = lon1 + unit
	return(lon1,lon2)

def tileEdges(x,y,z):
	'''Helper function to get lat/lon of a tile's edges at a given zoom'''
	lat1,lat2 = latEdges(y,z)
	lon1,lon2 = lonEdges(x,z)
	return((lat2, lon1, lat1, lon2)) # S,W,N,E

def mercatorToLat(mercatorY):
	'''Helper function converting mercator to lat'''
	return(math.degrees(math.atan(math.sinh(mercatorY))))

def rasterTilesFromOmd(pathToOmdFile, outputPath):
	'''Save raster tiles of omd to serve from zoom/x/y directory'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	plt.switch_backend('TKAgg')
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	#Lat/lon min/max for caluclating tile coverage later
	latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	#Set the plot settings
	plt.switch_backend('TKAgg')
	fig = plt.figure(frameon=False, figsize=[2.56,2.56])
	ax = fig.add_axes([0, 0, 1, 1])
	ax.axis('off')
	#Create the default tile
	if not os.path.exists(outputPath):
		os.makedirs(outputPath)
	plt.savefig(pJoin(outputPath,'default.png'),frameon=False, pad_inches=0, bbox='tight')
	#map latlon to projection
	epsg3857 = Proj(init='epsg:3857')
	wgs84 = Proj(init='EPSG:4326')
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	for point in node_positions:
		node_positions[point] = transform(wgs84,epsg3857,node_positions[point][1], node_positions[point][0])
	#Go through each zoom level and create tiles for each area covering the feeder
	for zoomLevel in range(0,19):
		#Boundaries covering the omd locations for the current zoom level
		upperRightTile = tileXY(latitude_max, longitude_max, zoomLevel)
		lowerLeftTile = tileXY(latitude_min, longitude_min, zoomLevel)
		firstTileEdges = tileEdges(upperRightTile[0], upperRightTile[1], zoomLevel)
		lastTileEdges = tileEdges(lowerLeftTile[0], lowerLeftTile[1], zoomLevel)
		nx.draw_networkx(nxG, pos=node_positions, nodelist=[node for node in nxG if node in nx.get_node_attributes(nxG, 'pos')], with_labels=False, node_size=2, edge_size=1)
		#Map omd for each x/y tile area
		for tileX in range(lowerLeftTile[0], upperRightTile[0]+1):
			for tileY in range(upperRightTile[1], lowerLeftTile[1]+1):
				currentTileEdges = tileEdges(tileX, tileY, zoomLevel)
				southWest = transform(wgs84,epsg3857,currentTileEdges[1], currentTileEdges[0])
				northEast = transform(wgs84,epsg3857,currentTileEdges[3], currentTileEdges[2])
				# S,W,N,E
				plt.ylim(top=northEast[1], bottom=southWest[1])
				plt.xlim(southWest[0], northEast[0])
				#create directory for tile
				savePath=pJoin(outputPath,str(zoomLevel),str(tileX))
				if not os.path.exists(savePath):
					os.makedirs(savePath)
				plt.savefig(pJoin(savePath,'%s.png' % str(tileY)),frameon=False, pad_inches=0, bbox='tight')

def _tests():
	e, n = 249.2419752733258, 1186.1488466689188
	lat, lon = statePlaneToLatLon(e, n, 2205)
	print (lat, lon) #(37.37267827914456, -89.89482331256504)
	e2, n2 = latLonToStatePlane(lat, lon, epsg=2205)
	print (e2, n2) # (249.24197527189972, 1186.1488466408398)
	# mapOmd('static/publicFeeders/Olin Barre LatLon.omd', 'testOutput', 'png')
	# mapOmd('static/publicFeeders/Olin Barre LatLon.omd', 'testOutput', 'html')
	#print(hullOfOmd('static/publicFeeders/Olin Barre LatLon.omd'))
	#simplifiedOmd = simplifiedOmdShape('static/publicFeeders/Olin Barre LatLon.omd')
	#print(simplifiedOmd)
	#shortestPathOmd('static/publicFeeders/Olin Barre LatLon.omd', 'node62474203981T62474203987_B', 'node1667616792')
	#rasterTilesFromOmd('static/publicFeeders/Olin Barre LatLon.omd', 'tilesOutput')
	# openInGoogleMaps(lat, lon)

if __name__ == '__main__':
	_tests()
from __future__ import division, print_function
from pyproj import Proj, transform
import webbrowser
import omf, json, warnings, networkx as nx, matplotlib, numpy as np, os, shutil, requests, tempfile
from matplotlib import pyplot as plt
from omf.feeder import _obToCol
from scipy.spatial import ConvexHull
from math import pow, log, tan, sin, cos, radians, pi, degrees, atan, sinh
from os.path import join as pJoin

def latLonNxGraphMap(pathToOmdFile, outputPath):
	''' Draw a networkx graph representing a feeder.'''
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	nxG = omf.feeder.treeToNxGraph(tree)
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

def drawLatLon():
	from mpl_toolkits.basemap import Basemap
	with open('../../static/publicFeeders/Olin Barre LatLon.omd') as inFile:
		tree = json.load(inFile)['tree']
	nxG = omf.feeder.treeToNxGraph(tree)
	plt.switch_backend('TKAgg')
	latLonNxGraphMap(nxG, labels=False, neatoLayout=False, showPlot=True)

def drawPngGraph():
	#Static reference file for testing now
	from mpl_toolkits.basemap import Basemap
	with open('../../static/publicFeeders/Olin Barre LatLon.omd') as inFile:
		tree = json.load(inFile)['tree']
	plt.switch_backend('TKAgg')
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	#Might need later for setting axes value in draw_network
	latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	#print(latitude_min, latitude_max, longitude_min, longitude_max)
	#Create dict of lat/lon for only nodes that have lat/lon values in feeder
	m = Basemap(llcrnrlon=-102.7662,llcrnrlat=32.983,urcrnrlon=-102.7576,urcrnrlat=32.997, epsg=3857)
	m.arcgisimage(service='World_Street_Map', dpi=400, verbose=False)
	node_positions = {}
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	#print(node_positions)
	for point in node_positions:
		node_positions[point] = (m(node_positions[point][1], node_positions[point][0]))
	nx.draw_networkx(nxG, pos=node_positions, nodelist=[node for node in nxG if node in nx.get_node_attributes(nxG, 'pos')], with_labels=False, node_size=2, edge_size=1)
	#m.plot(-102, 32, marker='D', color='m', latlon=True)
	#plt.show()
	plt.savefig('matplotlibmap.png', dpi=400, bbox_inches="tight")

def hullOfOmd(pathToOmdFile):
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
	with open('convexHull.json',"w") as outFile:
		json.dump(geoJsonDict, outFile, indent=4)
	#for simplex in hull.simplices:
	#	plt.plot(points[simplex, 0], points[simplex, 1], 'k-')
	#plt.show()

def omdGeoJson(pathToOmdFile, outputPath):
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
			"properties":{}
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
			"properties":{}
		})
	if not os.path.exists(outputPath):
		os.makedirs(outputPath)
	shutil.copy('geoPolyLeaflet.html', outputPath)
	with open(pJoin(outputPath,'geoPointsLines.json'),"w") as outFile:
		json.dump(geoJsonDict, outFile, indent=4)

def drawHtmlGraph():
	import folium
	with open('../../static/publicFeeders/Olin Barre LatLon.omd') as inFile:
		tree = json.load(inFile)['tree']
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	#Might need later for setting axes value in draw_network
	latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	#print(latitude_min, latitude_max, longitude_min, longitude_max)
	#Create dict of lat/lon for only nodes that have lat/lon values in feeder
	node_positions = {}
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	circleDict = {'objects':[]}
	for i in node_positions:
		circleDict['objects'].append({'circle': {'coordinates':node_positions[i]}})
	#print(circleDict)
	#print(node_positions)
	m = folium.Map(location=[32.99, -102.76],
		zoom_start=16,
		control_scale = True,
		max_zoom=19)
	for node in node_positions:
		folium.Marker([node_positions[node][0], node_positions[node][1]], popup=node).add_to(m)
	#print(nx.edges(nxG))
	lineDict = {'objects':[]}
	for edge in nx.edges(nxG):
		#folium.PolyLine([[45.3288, -121.6625],[45.3311, -121.7113]]).add_to(m)
		folium.PolyLine([[node_positions[edge[0]][0], node_positions[edge[0]][1]],[node_positions[edge[1]][0], node_positions[edge[1]][1]]]).add_to(m)
		lineDict['objects'].append({'line': {'coordinates':[[node_positions[edge[0]][0], node_positions[edge[0]][1]],
			[node_positions[edge[1]][0], node_positions[edge[1]][1]]]}})
	#print(lineDict)
	with open('nodes.json',"w") as outFile:
		json.dump(circleDict, outFile, indent=4)
	with open('lines.json',"w") as outFile:
		json.dump(lineDict, outFile, indent=4)
	m.save('leafletmap.html')

def crop(infile,height,width):
    im = Image.open(infile)
    imgwidth, imgheight = im.size
    for i in range(imgheight//height):
        for j in range(imgwidth//width):
            box = (j*width, i*height, (j+1)*width, (i+1)*height)
            yield im.crop(box)

import math
def num2deg(xtile, ytile, zoom):
	n = 2.0 ** zoom
	lon_deg = xtile / n * 360.0 - 180.0
	lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
	lat_deg = math.degrees(lat_rad)
	return (lat_deg, lon_deg)

def deg2num(lat_deg, lon_deg, zoom):
	lat_rad = math.radians(lat_deg)
	n = 2.0 ** zoom
	xtile = int((lon_deg + 180.0) / 360.0 * n)
	ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
	return (xtile, ytile)

def numTiles(z):
  return(pow(2,z))

def sec(x):
  return(1/cos(x))

def latlon2relativeXY(lat,lon):
  x = (lon + 180) / 360
  y = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
  return(x,y)

def latlon2xy(lat,lon,z):
  n = numTiles(z)
  x,y = latlon2relativeXY(lat,lon)
  return(n*x, n*y)
  
def tileXY(lat, lon, z):
  x,y = latlon2xy(lat,lon,z)
  return(int(x),int(y))

def xy2latlon(x,y,z):
  n = numTiles(z)
  relY = y / n
  lat = mercatorToLat(pi * (1 - 2 * relY))
  lon = -180.0 + 360.0 * x / n
  return(lat,lon)

def xy2lonlat(x,y,z):
  n = numTiles(z)
  relY = y / n
  lat = mercatorToLat(pi * (1 - 2 * relY))
  lon = -180.0 + 360.0 * x / n
  return(lon,lat)
  
def latEdges(y,z):
  n = numTiles(z)
  unit = 1 / n
  relY1 = y * unit
  relY2 = relY1 + unit
  lat1 = mercatorToLat(pi * (1 - 2 * relY1))
  lat2 = mercatorToLat(pi * (1 - 2 * relY2))
  return(lat1,lat2)

def lonEdges(x,z):
  n = numTiles(z)
  unit = 360 / n
  lon1 = -180 + x * unit
  lon2 = lon1 + unit
  return(lon1,lon2)
  
def tileEdges(x,y,z):
  lat1,lat2 = latEdges(y,z)
  lon1,lon2 = lonEdges(x,z)
  return((lat2, lon1, lat1, lon2)) # S,W,N,E

def mercatorToLat(mercatorY):
  return(degrees(atan(sinh(mercatorY))))

def tileSizePixels():
  return(256)

def tileLayerExt(layer):
  if(layer in ('oam')):
    return('jpg')
  return('png')

def tileLayerBase(layer):
  layers = { \
    "tah": "http://cassini.toolserver.org:8080/http://a.tile.openstreetmap.org/+http://toolserver.org/~cmarqu/hill/",
    #"tah": "http://tah.openstreetmap.org/Tiles/tile/",
    "oam": "http://oam1.hypercube.telascience.org/tiles/1.0.0/openaerialmap-900913/",
    "mapnik": "http://tile.openstreetmap.org/mapnik/"
    }
  return(layers[layer])
  
def tileURL(x,y,z,layer):
  return "%s%d/%d/%d.%s" % (tileLayerBase(layer),z,x,y,tileLayerExt(layer))

def rasterTilesFromOmd(pathToOmdFile, outputPath):
	#Static reference file for testing now
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	cwd = os.getcwd()
	circuitName = 'Olin Barre LatLon'
	plt.switch_backend('TKAgg')
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	#Might need later for setting axes value in draw_network
	latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	#print(latitude_min, latitude_max, longitude_min, longitude_max)
	#set conversions
	#Set the plot settings
	plt.switch_backend('TKAgg')
	fig = plt.figure(frameon=False, figsize=[2.56,2.56])
	ax = fig.add_axes([0, 0, 1, 1])
	ax.axis('off')
	#map latlon to projection
	import pyproj
	epsg3857 = pyproj.Proj(init='epsg:3857')
	wgs84 = pyproj.Proj(init='EPSG:4326')
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	for point in node_positions:
		node_positions[point] = pyproj.transform(wgs84,epsg3857,node_positions[point][1], node_positions[point][0])
	for zoomLevel in range(0,19):
		numberofTiles = numTiles(zoomLevel)
		upperRightTile = tileXY(latitude_max, longitude_max, zoomLevel)
		lowerLeftTile = tileXY(latitude_min, longitude_min, zoomLevel)
		firstTileEdges = tileEdges(upperRightTile[0], upperRightTile[1], zoomLevel)
		lastTileEdges = tileEdges(lowerLeftTile[0], lowerLeftTile[1], zoomLevel)
		#go through the X coordins=ates
		#print(range(lowerLeftTile[0], upperRightTile[0]+1))
		#print(range(upperRightTile[1], lowerLeftTile[1]+1))
		nx.draw_networkx(nxG, pos=node_positions, nodelist=[node for node in nxG if node in nx.get_node_attributes(nxG, 'pos')], with_labels=False, node_size=2, edge_size=1)
		for tileX in range(lowerLeftTile[0], upperRightTile[0]+1):
			for tileY in range(upperRightTile[1], lowerLeftTile[1]+1):
				#print(tileX, tileY)
				currentTileEdges = tileEdges(tileX, tileY, zoomLevel)
				southWest = pyproj.transform(wgs84,epsg3857,currentTileEdges[1], currentTileEdges[0])
				northEast = pyproj.transform(wgs84,epsg3857,currentTileEdges[3], currentTileEdges[2])
				# S,W,N,E
				plt.ylim(top=northEast[1], bottom=southWest[1])
				plt.xlim(southWest[0], northEast[0])
				#create directory for tiles
				savePath=pJoin(cwd,outputPath,str(zoomLevel),str(tileX))
				if not os.path.exists(savePath):
					os.makedirs(savePath)
				plt.savefig(pJoin(savePath,'%s.png' % str(tileY)),frameon=False, pad_inches=0, bbox='tight')

def mapOmd(pathToOmdFile, outputPath, fileFormat):
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
		shutil.copy('geoPolyLeaflet.html', outputPath)
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

def groupTilesOmd(pathToOmdFile, outputPath):
	from scipy.misc import imread
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	#Might need later for setting axes value in draw_network
	latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	#Set the plot settings
	plt.switch_backend('TKAgg')
	fig = plt.figure(frameon=False, figsize=[10,10])
	ax = fig.add_axes([0, 0, 1, 1])
	ax.axis('off')
	#map latlon to projection
	import pyproj
	epsg3857 = pyproj.Proj(init='epsg:3857')
	wgs84 = pyproj.Proj(init='EPSG:4326')
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	for point in node_positions:
		node_positions[point] = pyproj.transform(wgs84,epsg3857,node_positions[point][1], node_positions[point][0])
	for zoomLevel in range(18,19):
		numberofTiles = numTiles(zoomLevel)
		upperRightTile = tileXY(latitude_max, longitude_max, zoomLevel)
		lowerLeftTile = tileXY(latitude_min, longitude_min, zoomLevel)
		firstTileEdges = tileEdges(upperRightTile[0], upperRightTile[1], zoomLevel)
		lastTileEdges = tileEdges(lowerLeftTile[0], lowerLeftTile[1], zoomLevel)
		mainsouthWest = pyproj.transform(wgs84,epsg3857,lastTileEdges[1], lastTileEdges[0])
		mainnorthEast = pyproj.transform(wgs84,epsg3857,firstTileEdges[3], firstTileEdges[2])
		for tileX in range(lowerLeftTile[0], upperRightTile[0]+1):
			for tileY in range(upperRightTile[1], lowerLeftTile[1]+1):
				#print(tileX, tileY)
				currentTileEdges = tileEdges(tileX, tileY, zoomLevel)
				southWest = pyproj.transform(wgs84,epsg3857,currentTileEdges[1], currentTileEdges[0])
				northEast = pyproj.transform(wgs84,epsg3857,currentTileEdges[3], currentTileEdges[2])
				nx.draw_networkx(nxG, pos=node_positions, nodelist=[node for node in nxG if node in nx.get_node_attributes(nxG, 'pos')], with_labels=False, node_size=2, edge_size=1)
				url = 'https://a.tile.openstreetmap.org/%s/%s/%s.png' % (zoomLevel, tileX, tileY)
				response = requests.get(url, stream=True)
				imgFile = tempfile.TemporaryFile(suffix=".png")
				shutil.copyfileobj(response.raw, imgFile)
				del response
				img = plt.imread(imgFile)
				plt.imshow(img, extent=(southWest[0], northEast[0],southWest[1], northEast[1]))
		plt.ylim(top=mainnorthEast[1], bottom=mainsouthWest[1])
		plt.xlim(mainsouthWest[0], mainnorthEast[0])
		if not os.path.exists(outputPath):
			os.makedirs(outputPath)
		plt.savefig(pJoin(outputPath,'graphOnMap.png'),frameon=False, pad_inches=0, bbox='tight')

def mapboxPNG(pathToOmdFile, outputPath):
	from scipy.misc import imread
	#Static reference file for testing now
	with open(pathToOmdFile) as inFile:
		tree = json.load(inFile)['tree']
	cwd = os.getcwd()
	circuitName = 'Olin Barre LatLon'
	plt.switch_backend('TKAgg')
	#networkx graph to work with
	nxG = omf.feeder.treeToNxGraph(tree)
	#Might need later for setting axes value in draw_network
	latitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_min = min([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	latitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][0] for node in nx.get_node_attributes(nxG, 'pos')])
	longitude_max = max([nx.get_node_attributes(nxG, 'pos')[node][1] for node in nx.get_node_attributes(nxG, 'pos')])
	#print(latitude_min, latitude_max, longitude_min, longitude_max)
	#set conversions
	#Set the plot settings
	#figuresize must match mapbox proportion
	#img = plt.imread("img.png")
	#plt.imshow(img)
	#plt.show()
	#map latlon to projection
	import pyproj
	epsg3857 = pyproj.Proj(init='epsg:3857')
	wgs84 = pyproj.Proj(init='EPSG:4326')
	node_positions = {node: nx.get_node_attributes(nxG, 'pos')[node] for node in nx.get_node_attributes(nxG, 'pos')}
	for point in node_positions:
		node_positions[point] = pyproj.transform(wgs84,epsg3857,node_positions[point][1], node_positions[point][0])
	for zoomLevel in range(13,18):
		numberofTiles = numTiles(zoomLevel)
		upperRightTile = tileXY(latitude_max, longitude_max, zoomLevel)
		lowerLeftTile = tileXY(latitude_min, longitude_min, zoomLevel)
		print(upperRightTile)
		print(lowerLeftTile)
		xTiles = upperRightTile[0] - lowerLeftTile[0] + 1
		yTiles = lowerLeftTile[1] - upperRightTile[1] + 1
		print(xTiles, yTiles)
		tileRatio = xTiles/yTiles
		print(tileRatio)
		yPixels = 1024
		xPixels = int(yPixels*tileRatio)
		firstTileEdges = tileEdges(upperRightTile[0], upperRightTile[1], zoomLevel)
		lastTileEdges = tileEdges(lowerLeftTile[0], lowerLeftTile[1], zoomLevel)
		southWest = pyproj.transform(wgs84,epsg3857,lastTileEdges[1], lastTileEdges[0])
		northEast = pyproj.transform(wgs84,epsg3857,firstTileEdges[3], firstTileEdges[2])
		print(southWest)
		print(northEast)
		# S,W,N,E
		#-102.761922389 32.9896727709
		centerLat = (southWest[1] + northEast[1]) / 2
		centerLon = (southWest[0] + northEast[0]) / 2
		mapboxCenter = pyproj.transform(epsg3857,wgs84,centerLon, centerLat)
		print(centerLat)
		print(centerLon)
		print(mapboxCenter)
		plt.switch_backend('TKAgg')
		fig = plt.figure(frameon=False, figsize=[int(xPixels/100),int(yPixels/100)])
		ax = fig.add_axes([0, 0, 1, 1])
		ax.axis('off')
		#would convex hull help?
		#key is the size of this image
		url = "https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/"+str(mapboxCenter[0])+","+str(mapboxCenter[1])+","+str(zoomLevel)+"/"+str(xPixels)+"x"+str(yPixels)+"/?access_token=pk.eyJ1IjoiZWp0YWxib3QiLCJhIjoiY2ptMHBlOGdjMmZlaTNwb2dwMHE2Mm54NCJ9.xzceVNmAZy49SyFDb3UMaw"
		print(url)
		response = requests.get(url, stream=True)
		print(response)
		imgFile = tempfile.TemporaryFile(suffix=".png")
		shutil.copyfileobj(response.raw, imgFile)
		del response
		#img = plt.imread(imgFile)
		#plt.imshow(img, extent=(southWest[0], northEast[0],southWest[1], northEast[1]))
		plt.ylim(top=northEast[1], bottom=southWest[1])
		plt.xlim(southWest[0], northEast[0])
		#create directory for tiles
		nx.draw_networkx(nxG, pos=node_positions, nodelist=[node for node in nxG if node in nx.get_node_attributes(nxG, 'pos')], with_labels=False, node_size=2, edge_size=1)
		savePath=pJoin(cwd,outputPath,str(zoomLevel),str('test'))
		if not os.path.exists(savePath):
			os.makedirs(savePath)
		plt.savefig(pJoin(savePath,'%s.png' % str('noimg')),frameon=False, pad_inches=0, bbox='tight')

def componentToSubstation(pathToOmdFile, source, target):
		with open(pathToOmdFile) as inFile:
			tree = json.load(inFile)['tree']
		nxG = omf.feeder.treeToNxGraph(tree)
		tracePath = nx.bidirectional_shortest_path(nxG, source, target)
		return tracePath

if __name__ == '__main__':
	#drawPngGraph()
	#drawLatLon()
	#drawHtmlGraph()
	#hullOfOmd('../../static/publicFeeders/Olin Barre LatLon.omd')
	#omdGeoJson('../../static/publicFeeders/Olin Barre LatLon.omd', 'outGeo')
	#rasterTilesFromOmd('../../static/publicFeeders/Olin Barre LatLon.omd', 'tiles')
	#groupTilesOmd('../../static/publicFeeders/Olin Barre LatLon.omd', 'overlaps')
	#mapOmd('../../static/publicFeeders/Olin Barre LatLon.omd', 'newOutput', 'html')
	#mapboxPNG('../../static/publicFeeders/Olin Barre LatLon.omd', 'staticMap')
	componentToSubstation('../../static/publicFeeders/Olin Barre LatLon.omd', 'node62474203981T62474203987_B', 'node1667616792')
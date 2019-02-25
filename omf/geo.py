from pyproj import Proj, transform
import webbrowser
import omf, json, warnings, networkx as nx, matplotlib, numpy as np, os, shutil
from matplotlib import pyplot as plt
from omf.feeder import _obToCol
from scipy.spatial import ConvexHull
from os.path import join as pJoin

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

def _tests():
	e, n = 249.2419752733258, 1186.1488466689188
	lat, lon = statePlaneToLatLon(e, n, 2205)
	print (lat, lon) #(37.37267827914456, -89.89482331256504)
	e2, n2 = latLonToStatePlane(lat, lon, epsg=2205)
	print (e2, n2) # (249.24197527189972, 1186.1488466408398)
	letLat, letLon = decLatLonToLetter(lat, lon)
	print (letLat, letLon) # ('37N22:21.6418049204', '89W53:41.3639252341')
	# mapOmd('static/publicFeeders/Olin Barre LatLon.omd', 'testOutput', 'png')
	# mapOmd('static/publicFeeders/Olin Barre LatLon.omd', 'testOutput', 'html')
	# hullOfOmd('static/publicFeeders/Olin Barre LatLon.omd')
	# openInGoogleMaps(lat, lon)

if __name__ == '__main__':
	_tests()
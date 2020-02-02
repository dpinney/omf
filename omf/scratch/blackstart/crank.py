import json, os, sys, tempfile, re, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
import pandas as pd
from os.path import join as pJoin
from jinja2 import Template

# OMF imports
import omf
import omf.feeder
import omf.geo as geo

def cutoffFault(pathToOmd, faultedLine, workDir=None):
	
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)

	with open(pathToOmd) as inFile:
		tree = json.load(inFile)['tree']
	outageMap = geo.omdGeoJson(pathToOmd, conversion = False)

	# create a dataframe storing data of which nodes are actually connected according to the .omd file
	with open(workDir + '/connectivity.csv', 'w', newline='') as connectivity:

		fieldnames = ['first_node', 'second_node']
		writer = csv.DictWriter(connectivity, fieldnames)
		writer.writeheader()

		for key in tree.keys():
			obtype = tree[key].get('object','')
			if obtype.startswith('underground_line') or obtype.startswith('overhead_line') or obtype.startswith('triplex_line') or obtype.startswith('switch') or obtype.startswith('recloser') or obtype.startswith('transformer') or obtype.startswith('fuse'):
				if 'from' in tree[key].keys() and 'to' in tree[key].keys():
					writer.writerow({'first_node': tree[key]['from'], 'second_node': tree[key]['to']})
	connectivity.close()

	# read in connectivity data
	connectivity = pd.read_csv(workDir + '/connectivity.csv')
	row = 0
	index = 0
	row_count_connectivity = connectivity.shape[0]
	nodes = {}
	while row < row_count_connectivity:
		first = connectivity.loc[row]['first_node']
		second = connectivity.loc[row]['second_node']
		if first not in nodes.keys():
			nodes[first] = index
			index += 1
		if second not in nodes.keys():
			nodes[second] = index
			index += 1
		row += 1

	adjacency = [[100] * len(nodes) for i in range(len(nodes))]
	connectivity_count = connectivity.shape[0]
	row = 0
	while row < connectivity_count:
		first = nodes[connectivity.loc[row]['first_node']]
		second = nodes[connectivity.loc[row]['second_node']]
		adjacency[first][second] = 1
		adjacency[second][first] = 1
		row += 1

	print(adjacency)

	def locationToName(location, lines):
		'get the name of the line component associated with a given location (lat/lon)'
		p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
		coord = [float(i) for i in p.findall(location)]  # Convert strings to float
		coordLat = coord[0]
		coordLon = coord[1]
		# get the coordinates of the two points that make up the edges of the line
		row_count_lines = lines.shape[0]
		row = 0
		while row < row_count_lines:
			p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
			coord1 = [float(i) for i in p.findall(lines.loc[row, 'coords1'])]  # Convert strings to float
			coord1Lat = coord1[0]
			coord1Lon = coord1[1]
			p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
			coord2 = [float(i) for i in p.findall(lines.loc[row, 'coords2'])]  # Convert strings to float
			coord2Lat = coord2[0]
			coord2Lon = coord2[1]
			# use the triangle property to see if the new point lies on the line
			dist1 = math.sqrt((coordLat - coord1Lat)**2 + (coordLon - coord1Lon)**2)
			dist2 = math.sqrt((coord2Lat - coordLat)**2 + (coord2Lon - coordLon)**2)
			dist3 = math.sqrt((coord2Lat - coord1Lat)**2 + (coord2Lon - coord1Lon)**2)
			#threshold value just in case the component is not exactly in between the two points given
			threshold = 10e-10
			# triangle property with threshold
			if (dist1 + dist2 - dist3) < threshold:
				name = lines.loc[row, 'line_name']
				return name
			row += 1
		# if the location does not lie on any line, return 'None' (good for error testing)
		name = 'None'
		return name
		
	def nodeToCoords(outageMap, nodeName):
		'get the latitude and longitude of a given node in string format'
		coords = ''
		for key in outageMap['features']:
			if (nodeName in key['properties'].get('name','')):
				current = key['geometry']['coordinates']
				p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture integer values
				array = [float(i) for i in p.findall(str(current))]
				coord1 = array[0]
				coord2 = array[1]
				coords = str(coord1) + ' ' + str(coord2)
		return coords

	# create a DataFrame with the line name and the coordinates of its edges
	with open(workDir + '/lines.csv', mode='w') as lines:
		fieldnames = ['line_name', 'line_type', 'coords1', 'coords2']
		writer = csv.DictWriter(lines, fieldnames)

		writer.writeheader()

		for key in tree.keys():
			obtype = tree[key].get('object','')
			if obtype == 'underground_line' or obtype == 'overhead_line' or obtype == 'triplex_line' or obtype == 'recloser':
				writer.writerow({'line_name': tree[key]['name'], 'line_type': obtype, 'coords1': nodeToCoords(outageMap, tree[key]['from']), 'coords2': nodeToCoords(outageMap, tree[key]['to'])})

	lines.close()

	lines = pd.read_csv(workDir + '/lines.csv')
	row = 0
	line_row_count = lines.shape[0]
	while row < line_row_count:
		if lines.loc[row]['line_name'] == faultedLine:
			p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
			coord1 = [float(i) for i in p.findall(lines.loc[row, 'coords1'])]  # Convert strings to float
			coord1Lat = coord1[0]
			coord1Lon = coord1[1]
			coord2 = [float(i) for i in p.findall(lines.loc[row, 'coords2'])]  # Convert strings to float
			coord2Lat = coord2[0]
			coord2Lon = coord2[1]
			break
		row += 1
	row = 0
	closest_recloser = None
	nearest_distance = 10e10
	while row < line_row_count:
		if lines.loc[row]['line_type'] == 'recloser':
			p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
			coord1 = [float(i) for i in p.findall(lines.loc[row, 'coords1'])]  # Convert strings to float
			coord1Lat = coord1[0]
			coord1Lon = coord1[1]
			coord2 = [float(i) for i in p.findall(lines.loc[row, 'coords2'])]  # Convert strings to float
			coord2Lat = coord2[0]
			coord2Lon = coord2[1]

cutoffFault('C:/Users/granb/omf/omf/static/publicFeeders/ABECColumbia.omd', "824984")
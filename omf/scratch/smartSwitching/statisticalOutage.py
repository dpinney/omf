import pandas as pd
import numpy as np
from scipy import spatial
import math
import random
from omf import geo, feeder
import re
import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import datetime

def heatMap(mc):
	'create a heat map based on input DataFrame with location, component type, fault type, and cause'
	compType = {}
	location = {}
	cause = {}
	faultType = {}
	row_count_mc = mc.shape[0]
	row = 0
	while row < row_count_mc:
		# comp type will store which causes and fault types can occur for a given line type
		if mc.loc[row, 'Object type'] in compType.keys():
			if mc.loc[row, 'Cause'] not in compType[mc.loc[row, 'Object type']]['causes']:
				compType[mc.loc[row, 'Object type']]['causes'].append(mc.loc[row, 'Cause'])
			if mc.loc[row, 'Implemented Fault Type'] not in compType[mc.loc[row, 'Object type']]['fault_types']:
				compType[mc.loc[row, 'Object type']]['fault_types'].append(mc.loc[row, 'Implemented Fault Type'])
		else:
			compType[mc.loc[row, 'Object type']] = {}
			compType[mc.loc[row, 'Object type']]['causes'] = []
			compType[mc.loc[row, 'Object type']]['fault_types'] = []
			compType[mc.loc[row, 'Object type']]['causes'].append(mc.loc[row, 'Cause'])
			compType[mc.loc[row, 'Object type']]['fault_types'].append(mc.loc[row, 'Implemented Fault Type'])
		# location of the faults as well as the component type, since the latter is completely dependent on the former (if we have no locations for the components)
		if (mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']) in location.keys():
			location[mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']] += 1
		else:
			location[mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']] = 1
		# causes for the faults
		if mc.loc[row, 'Cause'] in cause.keys():
			cause[mc.loc[row, 'Cause']] += 1
		else:
			cause[mc.loc[row, 'Cause']] = 1
		# fault types for the faults
		if mc.loc[row, 'Implemented Fault Type'] in faultType.keys():
			faultType[mc.loc[row, 'Implemented Fault Type']] += 1
		else:
			faultType[mc.loc[row, 'Implemented Fault Type']] = 1
		row += 1
	# find the total number of faults that occur in each dictionary
	totalCause = sum(cause.itervalues(), 0.0)
	totalFaultType = sum(faultType.itervalues(), 0.0)
	totalLocation = sum(location.itervalues(), 0.0)

	# create a heat map by dividing the number of each individual item by the total number found
	location = {k: v / totalLocation for k, v in location.iteritems()}
	cause = {k: v / totalCause for k, v in cause.iteritems()}
	faultType = {k: v / totalFaultType for k, v in faultType.iteritems()}
	# create a single dictionary to store heat map data
	heatMap = {}
	heatMap['compType'] = compType
	heatMap['location'] = location
	heatMap['cause'] = cause
	heatMap['faultType'] = faultType
	return heatMap

def randomFault(pathToCsv, faultsGenerated):
	'using an input csv file with outage data, create a heat map object and generate a random fault'
	mc = pd.read_csv(pathToCsv)
	heatmap = heatMap(mc)
	component_types = []
	locations = []
	causes = []
	fault_types = []
	faultNumber = 0
	while faultNumber < faultsGenerated:
		# choose a random location
		chooseLocationString = np.random.choice(heatmap['location'].keys(), replace=True, p=heatmap['location'].values())
		chooseLocation = chooseLocationString.split()
		location = str(chooseLocation[0]) + ' ' + str(chooseLocation[1])
		# Note: for this method, component type is completely dependent on location
		compType = str(chooseLocation[2])
		# choose a cause that is possible, given the component type
		causeChosen = False
		while causeChosen == False:
			chooseCause = np.random.choice(heatmap['cause'].keys(), replace=True, p=heatmap['cause'].values())
			if chooseCause in heatmap['compType'][compType]['causes']:
				cause = chooseCause
				causeChosen = True
		# choose a fault type that is possible, given the component type
		faultChosen = False
		while faultChosen == False:
			chooseFault = np.random.choice(heatmap['faultType'].keys(), replace=True, p=heatmap['faultType'].values())
			if chooseFault in heatmap['compType'][compType]['fault_types']:
				faultType = chooseFault
				faultChosen = True
		locations.append(location)
		component_types.append(compType)
		causes.append(cause)
		fault_types.append(faultType)
		faultNumber += 1
	data = {'component_type': component_types, 'location': locations, 'cause': causes, 'fault_type': fault_types}
	faults = pd.DataFrame(data)
	return faults

def locationMap(mc, neighbors, gridLines):
	'Create a location heatmap, where the 2D space is partitioned into a set of lattices. The function for the heat map is inversely proportional to the distance of the nth neighbor from each point in the lattice.'
	# lists to hold the latitudes, longitudes, and coordinate pairs of each fault location
	longitudes = []
	latitudes = []
	coords = []
	
	# populate the lists
	row = 0
	row_count_mc = mc.shape[0]
	while row < row_count_mc:
		locString = mc.loc[row, 'Location']
		p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture integer values
		coord = [float(i) for i in p.findall(locString)]
		latitude = coord[0]
		longitude = coord[1]
		latitudes.append(latitude)
		longitudes.append(longitude)
		coords.append(coord)
		row += 1

	# Pull out the minimum and maximum latitudes/longitudes of each fault.
	min_lat = min(latitudes)
	max_lat = max(latitudes)
	min_lon = min(longitudes)
	max_lon = max(longitudes)

	# Divide the 2D space where the feeder system sits into a set of lattices, allowing 5% wiggle room on each side.
	xv = np.linspace(min_lat - (max_lat - min_lat) / 20, max_lat + (max_lat - min_lat) / 20, gridLines)
	yv = np.linspace(min_lon - (max_lon - min_lon) / 20, max_lon + (max_lon - min_lon) / 20, gridLines)

	# For each lattice point, find the distance of the nth nearest outage, optimizing runtime by searching with KDTrees.
	# Store heatmap data in the nth_distance array, where the function describing the heatmap is inversely proportional to the distance between the lattice point and its nth nearest neighbor.
	j = 0
	nth_distance = []
	length_xv = len(xv)
	length_yv = len(yv)
	while j < length_yv:
		i = 0
		while i < length_xv:
			point = []
			point.append(xv[i])
			point.append(yv[j])
			distances, indices = spatial.KDTree(coords).query(point, k=neighbors, p=2)
			if neighbors > 1:
				nth_distance.append(1/max(distances))
			else:
				nth_distance.append(1/distances)
			i += 1
		j += 1
	# normalize
	total_distance = sum(nth_distance)
	nth_distance[:] = [x / total_distance for x in nth_distance]

	return nth_distance, xv, yv

def heatMapRefined(mc):
	'create a heat map based on input DataFrame with component type, fault type, and cause'
	componentType = {}
	compType = {}
	cause = {}
	faultType = {}
	row_count_mc = mc.shape[0]
	row = 0
	while row < row_count_mc:
		# comp type will store which causes and fault types can occur for a given line type
		if mc.loc[row, 'Object type'] in compType.keys():
			if mc.loc[row, 'Cause'] not in compType[mc.loc[row, 'Object type']]['causes']:
				compType[mc.loc[row, 'Object type']]['causes'].append(mc.loc[row, 'Cause'])
			if mc.loc[row, 'Implemented Fault Type'] not in compType[mc.loc[row, 'Object type']]['fault_types']:
				compType[mc.loc[row, 'Object type']]['fault_types'].append(mc.loc[row, 'Implemented Fault Type'])
		else:
			compType[mc.loc[row, 'Object type']] = {}
			compType[mc.loc[row, 'Object type']]['causes'] = []
			compType[mc.loc[row, 'Object type']]['fault_types'] = []
			compType[mc.loc[row, 'Object type']]['causes'].append(mc.loc[row, 'Cause'])
			compType[mc.loc[row, 'Object type']]['fault_types'].append(mc.loc[row, 'Implemented Fault Type'])
		# component type for the faults
		if mc.loc[row, 'Object type'] in componentType.keys():
			componentType[mc.loc[row, 'Object type']] += 1
		else:
			componentType[mc.loc[row, 'Object type']] = 1
		# causes for the faults
		if mc.loc[row, 'Cause'] in cause.keys():
			cause[mc.loc[row, 'Cause']] += 1
		else:
			cause[mc.loc[row, 'Cause']] = 1
		# fault types for the faults
		if mc.loc[row, 'Implemented Fault Type'] in faultType.keys():
			faultType[mc.loc[row, 'Implemented Fault Type']] += 1
		else:
			faultType[mc.loc[row, 'Implemented Fault Type']] = 1
		row += 1
	# find the total number of faults that occur in each dictionary
	totalCause = sum(cause.itervalues(), 0.0)
	totalComponentType = sum(componentType.itervalues(), 0.0)
	totalFaultType = sum(faultType.itervalues(), 0.0)

	# create a heat map by dividing the number of each individual item by the total number found
	cause = {k: v / totalCause for k, v in cause.iteritems()}
	componentType = {k: v / totalComponentType for k, v in componentType.iteritems()}
	faultType = {k: v / totalFaultType for k, v in faultType.iteritems()}
	
	# create a single dictionary to store heat map data
	heatMap = {}
	heatMap['compType'] = compType
	heatMap['componentType'] = componentType
	heatMap['cause'] = cause
	heatMap['faultType'] = faultType
	return heatMap

def randomFaultsRefined(pathToCsv, pathToOmd, workDir, neighbors, gridLines, faultsGenerated):
	'Function that generates a DataFrame with a set of faults based on an original set of data and which selects the location using the lattice method'
	
	# Check that we're in the proper directory
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir

	# Create heatmaps for location and the other three parameters
	mc = pd.read_csv(pathToCsv)
	nth_distance, xv, yv = locationMap(mc, neighbors, gridLines)
	heatMap = heatMapRefined(mc)
	# Create lists to store the new outage data.
	component_types = []
	locations = []
	causes = []
	fault_types = []
	# Generate a set number of new faults.
	faultNumber = 0
	while faultNumber < faultsGenerated:
		# Randomly select the component type based on heatmap data.
		component = np.random.choice(heatMap['componentType'].keys(), replace=True, p=heatMap['componentType'].values())
		compType = component

		# Randomly select a lattice location based on location heatmap data.
		locRandom = random.uniform(0, 1)
		total = nth_distance[0]
		entry = 0
		while total < locRandom:
			entry += 1
			total += nth_distance[entry]
		# Get latitude and longitude by converting the 1D index to a 2D index.
		latitudeChosen = xv[entry % gridLines]
		longitudeChosen = yv[entry / gridLines]
		location = str(latitudeChosen) + ' ' + str(longitudeChosen)

		def nodeToCoords(outageMap, nodeName):
			'get the latitude and longitude of a given node in string format'
			coords = ''
			for key in outageMap['features']:
				if (nodeName in key['properties'].get('name','')):
					current = key['geometry']['coordinates']
					p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
					array = [float(i) for i in p.findall(str(current))]
					coord1 = array[0]
					coord2 = array[1]
					coords = str(coord1) + ' ' + str(coord2)
			return coords

		def nearestLine(location, lines, component):
			'Get the latitude/longitude of the line component closest to a given location, given the component type'
			minDist = 10e10
			trueLatitude = 0.0
			trueLongitude = 0.0
			# Separate the location string into latitude and longitude (floats)
			p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
			coord = [float(i) for i in p.findall(location)]  # Convert strings to float
			x3 = coord[0]
			y3 = coord[1]
			# get the coordinates of the two points that make up the edges of the line
			row_count_lines = lines.shape[0]
			row = 0
			# iterate through all line components
			while row < row_count_lines:
				# get the coordinates of the points on the edge of a line component
				p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
				coord1 = [float(i) for i in p.findall(lines.loc[row, 'coords1'])]  # Convert strings to float
				x1 = coord1[0]
				y1 = coord1[1]
				p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
				coord2 = [float(i) for i in p.findall(lines.loc[row, 'coords2'])]  # Convert strings to float
				x2 = coord2[0]
				y2 = coord2[1]
				# make sure we have a line component
				if x1 != x2 or y1 != y2:
					# find the distance between the point and the given line
					# Note: the point is closest to the line at the tangent to the line that passes through the point
					# In other words, the dot product of the tangent and the line is zero.
					u = ((x3 - x1)*(x2 - x1) + (y3 - y1)*(y2 - y1)) / (math.sqrt((x2 - x1)**2 + (y2 - y1)**2))
					# Get point of intersection of tangent line
					x = x1 + u*(x2 - x1)
					y = y1 + u*(y2 - y1)
					# find distance between point of intersection and the point under consideration
					distance = math.sqrt((x - x3)**2 + (y - y3)**2)
					# if this distance is smaller than any seen so far, use it!
					if distance < minDist:
						minDist = distance
						trueLatitude = x
						trueLongitude = y
				row += 1
			return (str(trueLatitude) + ' ' + str(trueLongitude))

		# create a DataFrame with the line name and the coordinates of its edges
		with open(pathToOmd) as inFile:
			tree = json.load(inFile)['tree']
		outageMap = geo.omdGeoJson(pathToOmd, conversion = False)
		with open(workDir + '/lines.csv', mode='w') as lines:
			fieldnames = ['coords1', 'coords2']
			writer = csv.DictWriter(lines, fieldnames)

			writer.writeheader()

			for key in tree.keys():
				obtype = tree[key].get("object","")
				if obtype == component:
					writer.writerow({'coords1': nodeToCoords(outageMap, tree[key]['from']), 'coords2': nodeToCoords(outageMap, tree[key]['to'])})

		lines.close()
		lines = pd.read_csv(workDir + '/lines.csv')
		# get a location that lies on a line, based on the location heat map generated
		trueLocation = nearestLine(location, lines, component)	
		
		# choose a cause that is possible using the heatmap, given the component type
		causeChosen = False
		while causeChosen == False:
			chooseCause = np.random.choice(heatMap['cause'].keys(), replace=True, p=heatMap['cause'].values())
			if chooseCause in heatMap['compType'][compType]['causes']:
				cause = chooseCause
				causeChosen = True
		
		# choose a fault type that is possible using the heatmap, given the component type
		faultChosen = False
		while faultChosen == False:
			chooseFault = np.random.choice(heatMap['faultType'].keys(), replace=True, p=heatMap['faultType'].values())
			if chooseFault in heatMap['compType'][compType]['fault_types']:
				faultType = chooseFault
				faultChosen = True
		
		# Add this fault to the set of faults.
		locations.append(trueLocation)
		component_types.append(component)
		causes.append(cause)
		fault_types.append(faultType)
		faultNumber += 1
	data = {'component_type': component_types, 'location': locations, 'cause': causes, 'fault_type': fault_types}
	faults = pd.DataFrame(data)
	return faults
	
print(randomFaultsRefined('C:/Users/granb/omf/omf/scratch/smartSwitching/outagesNew3.csv', 'C:/Users/granb/omf/omf/static/publicFeeders/Olin Barre Fault.omd', None, 4, 10, 100))
#print(randomFault('C:/Users/granb/omf/omf/scratch/smartSwitching/outagesNew3.csv', 100))
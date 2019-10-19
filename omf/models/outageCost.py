import pandas as pd
import numpy as np
from scipy import spatial
import random
from omf import geo, feeder
import re
import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import datetime
import plotly as py
import plotly.graph_objs as go
from os.path import join as pJoin
from jinja2 import Template
from __neoMetaModel__ import *
from omf.models import __neoMetaModel__

# OMF imports
import omf.feeder as feeder
from omf.solvers import gridlabd

# Model metadata:
tooltip = "outageCost calculates reliability metrics and creates a leaflet graph based on data from an input csv file."
modelName, template = metadata(__file__)
hidden = False

def datetime_to_float(d):
	'helper function to convert a datetime object to a float'
	epoch = datetime.datetime.utcfromtimestamp(0)
	total_seconds = (d - epoch).total_seconds()
	return total_seconds	

def heatMap(mc):
	'create a heat map based on input DataFrame with location, component type, fault type, and cause'
	compType = {}
	location = {}
	cause = {}
	row_count_mc = mc.shape[0]
	row = 0
	while row < row_count_mc:
		causefault = (mc.loc[row, 'Cause'], mc.loc[row, 'Implemented Fault Type'])
		# comp type will store which causes and fault types can occur for a given line type
		if mc.loc[row, 'Object type'] in compType.keys():
			if causefault not in compType[mc.loc[row, 'Object type']]['causes']:
				compType[mc.loc[row, 'Object type']]['causes'].append(causefault)
		else:
			compType[mc.loc[row, 'Object type']] = {}
			compType[mc.loc[row, 'Object type']]['causes'] = []
			compType[mc.loc[row, 'Object type']]['causes'].append(causefault)
		# location of the faults as well as the component type, since the latter is completely dependent on the former (if we have no locations for the components)
		if (mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']) in location.keys():
			location[mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']] += 1
		else:
			location[mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']] = 1
		# causes and fault types for the faults (note dependency again)
		if causefault in cause.keys():
			cause[causefault] += 1
		else:
			cause[causefault] = 1
		row += 1
	# find the total number of faults that occur in each dictionary
	totalCause = sum(cause.itervalues(), 0.0)
	totalLocation = sum(location.itervalues(), 0.0)

	# create a heat map by dividing the number of each individual item by the total number found
	location = {k: v / totalLocation for k, v in location.iteritems()}
	cause = {k: v / totalCause for k, v in cause.iteritems()}

	# create a single dictionary to store heat map data
	heatMap = {}
	heatMap['compType'] = compType
	heatMap['location'] = location
	heatMap['cause'] = cause

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
		# choose a cause and fault type that is possible (dependency), given the component type
		causeChosen = False
		while causeChosen == False:
			rand = random.random()
			total = 0
			for k, v in heatmap['cause'].items():
				total += v
				if rand <= total:
					chooseCause = k
					break
			if chooseCause in heatmap['compType'][compType]['causes']:
				causefault = chooseCause
				causeChosen = True
		locations.append(location)
		component_types.append(compType)
		causes.append(causefault[0])
		fault_types.append(causefault[1])
		faultNumber += 1
	data = {'component_type': component_types, 'Location': locations, 'Cause': causes, 'fault_type': fault_types}
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

	# Divide the 2D space where the feeder system sits into a lattice, allowing 5% wiggle room on each side.
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
			distances, indices = spatial.KDTree(coords).query(point, k=int(4), p=2)
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
	#faultType = {}
	row_count_mc = mc.shape[0]
	row = 0
	while row < row_count_mc:
		causefault = (mc.loc[row, 'Cause'], mc.loc[row, 'Implemented Fault Type'])
		# component types for faults
		if mc.loc[row, 'Object type'] in componentType.keys():
			componentType[mc.loc[row, 'Object type']] += 1
		else:
			componentType[mc.loc[row, 'Object type']] = 1
		# comp type will store which causes and fault types can occur for a given line type
		if mc.loc[row, 'Object type'] in compType.keys():
			if causefault not in compType[mc.loc[row, 'Object type']]['causes']:
				compType[mc.loc[row, 'Object type']]['causes'].append(causefault)
		else:
			compType[mc.loc[row, 'Object type']] = {}
			compType[mc.loc[row, 'Object type']]['causes'] = []
			compType[mc.loc[row, 'Object type']]['causes'].append(causefault)

		# causes and fault types for the faults
		if causefault in cause.keys():
			cause[causefault] += 1
		else:
			cause[causefault] = 1
		row += 1
	# find the total number of faults that occur in each dictionary
	totalCause = sum(cause.itervalues(), 0.0)
	totalComponentType = sum(componentType.itervalues(), 0.0)

	# create a heat map by dividing the number of each individual item by the total number found
	cause = {k: v / totalCause for k, v in cause.iteritems()}
	componentType = {k: v / totalComponentType for k, v in componentType.iteritems()}

	# create a single dictionary to store heat map data
	heatMap = {}
	heatMap['compType'] = compType
	heatMap['componentType'] = componentType
	heatMap['cause'] = cause

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
		
		# choose a cause and fault type that are possible using the heatmap, given the component type
		causeChosen = False
		while causeChosen == False:
			rand = random.random()
			total = 0
			for k, v in heatMap['cause'].items():
				total += v
				if rand <= total:
					chooseCause = k
					break
			if chooseCause in heatMap['compType'][compType]['causes']:
				causefault = chooseCause
				causeChosen = True
		
		# Add this fault to the set of faults.
		locations.append(trueLocation)
		component_types.append(component)
		causes.append(causefault[0])
		fault_types.append(causefault[1])
		faultNumber += 1
	data = {'component_type': component_types, 'Location': locations, 'Cause': causes, 'fault_type': fault_types}
	faults = pd.DataFrame(data)
	return faults

def outageCostAnalysis(pathToOmd, pathToCsv, workDir, generateRandom, numberOfCustomers, sustainedOutageThreshold, causeFilter, componentTypeFilter, faultTypeFilter, timeMinFilter, timeMaxFilter, meterMinFilter, meterMaxFilter, durationMinFilter, durationMaxFilter, neighborsStr, gridLinesStr, faultsGeneratedStr):
	' calculates outage metrics, plots a leaflet map of faults, and plots an outage timeline'
	# check to see if work directory is specified; otherwise, create a temporary directory
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir
	
	# calculate outage stats
	def statsCalc(saidi=None, saifi=None, caidi=None, asai=None, maifi=None):
		'helper function to convert outage stats into a nice format to be output on the interface'
		html_str = """
			<div style="text-align:center">
				<p style="padding-top:10px; padding-bottom:10px;"><b>SAIDI:</b><span style="padding-left:1em">"""+str(saidi)+"""</span><span style="padding-left:2em"><b>SAIFI:</b><span style="padding-left:1em">"""+str(saifi)+"""</span><span style="padding-left:2em"><b>MAIFI:</b><span style="padding-left:1em">"""+str(maifi)+"""</span><span style="padding-left:2em"><b>CAIDI:</b><span style="padding-left:1em">"""+str(caidi)+"""</span><span style="padding-left:2em"><b>ASAI:</b><span style="padding-left:1em">"""+str(asai)+"""</span></span></p>
			</div>"""
		return html_str

	mc = pd.read_csv(pathToCsv)

	# calculate SAIDI
	if 'Start' in mc.columns:
		customerInterruptionDurations = 0.0
		row = 0
		row_count_mc = mc.shape[0]
		while row < row_count_mc:
			if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) > int(sustainedOutageThreshold):
				entry = str(mc.loc[row, 'Meters Affected'])
				meters = entry.split()
				customerInterruptionDurations += (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) * len(meters) / 3600
			row += 1

		SAIDI = customerInterruptionDurations / int(numberOfCustomers)

		# calculate SAIFI
		row = 0
		totalInterruptions = 0.0
		customersAffected = 0
		while row < row_count_mc:
			if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) > int(sustainedOutageThreshold):
				entry = str(mc.loc[row, 'Meters Affected'])
				meters = entry.split()
				customersAffected += len(meters)
			row += 1
		SAIFI = float(customersAffected) / int(numberOfCustomers)

		# calculate CAIDI
		CAIDI = SAIDI / SAIFI

		# calculate ASAI
		ASAI = (int(numberOfCustomers) * 8760 - customerInterruptionDurations) / (int(numberOfCustomers) * 8760)

		# calculate MAIFI
		sumCustomersAffected = 0.0
		row = 0
		while row < row_count_mc:
			if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) <= int(sustainedOutageThreshold):
				entry = str(mc.loc[row, 'Meters Affected'])
				meters = entry.split()
				sumCustomersAffected += len(meters)
			row += 1

		MAIFI = sumCustomersAffected / int(numberOfCustomers)

		# make the format nice and save as .html
		metrics = statsCalc(
			saidi = SAIDI,
			saifi = SAIFI,
			caidi = CAIDI,
			asai = ASAI,
			maifi = MAIFI)
		with open(pJoin(workDir, "statsCalc.html"), "w") as statsFile:
			statsFile.write(metrics)
	else:
		with open(pJoin(workDir, "statsCalc.html"), "w") as statsFile:
			statsFile.write('No outage stats are available given the input data provided by the user.')

	# Draw a leaflet graph of the feeder with outages
	outageMap = geo.omdGeoJson(pathToOmd, conversion=False)

	mc = pd.read_csv(pathToCsv)

	row = 0
	row_count_mc = mc.shape[0]
	while row < row_count_mc:
		entry = mc.loc[row, 'Location']
		p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture integer values
		coords = [float(i) for i in p.findall(entry)]
		coord1 = coords[0]
		coord2 = coords[1]
		if 'Cause' in mc.columns:
			cause = mc.loc[row, 'Cause']
		else:
			cause = 'None'
		if 'Meters Affected' in mc.columns:
			lis = str(mc.loc[row, 'Meters Affected'])
			meters = lis.split()
			meterCount = len(meters)
		else:
			meters = []
			meterCount = 0
			meterMinFilter = -10e10
			meterMaxFilter = 10e10

		if 'Start' in mc.columns:		
			duration = datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
			time = datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S'))
			timeMin = datetime_to_float(datetime.datetime.strptime(timeMinFilter, '%Y-%m-%d %H:%M:%S'))
			timeMax = datetime_to_float(datetime.datetime.strptime(timeMaxFilter, '%Y-%m-%d %H:%M:%S'))
		else:
			duration = 0.0
			time = 0.0
			timeMin = -10e10
			timeMax = 10e10
			durationMinFilter = -10e10
			durationMaxFilter = 10e10
		if 'component_type' in mc.columns:
			componentType = mc.loc[row, 'component_type']
		else:
			componentType = 'None'
		if 'fault_type' in mc.columns:
			faultType = mc.loc[row, 'fault_type']
		else:
			faultType = 'None'

		Dict = {}
		Dict['geometry'] = {'type': 'Point', 'coordinates': [coord1, coord2]}
		Dict['type'] = 'Feature'
		Dict['properties'] = {'name': 'Old_Fault_' + str(row+1), 'meterCount': int(meterCount), 'time': time, 'timeMin':timeMin, 'timeMax':timeMax, 'meterMinFilter': int(meterMinFilter), 'meterMaxFilter': int(meterMaxFilter), 'cause': str(cause), 'componentType': str(componentType), 'faultType': str(faultType), 'componentFilter':str(componentTypeFilter), 'faultFilter': str(faultTypeFilter), 'causeFilter': causeFilter, 'duration': int(duration), 'durationMinFilter': int(durationMinFilter), 'durationMaxFilter': int(durationMaxFilter), 'meters': str(mc.loc[row, 'Meters Affected']), 'pointColor': 'blue', 'popupContent': '<br><br>Fault start time: <b>' + str(mc.loc[row, 'Start']) + '</b><br> Fault duration: <b>' + str(duration) + ' seconds</b><br>Location: <b>' + str(coords) + '</b><br>Cause: <b>' + str(cause) + '</b><br>Meters Affected: <b><br>' + str(mc.loc[row, 'Meters Affected']) + '</b><br>Count of Meters Affected: <b>' + str(len(meters)) + '</b><br>Line Type: <b>' + str(componentType) + '</b><br>Fault Type: <b>' + str(faultType) + '</b>.'}
		outageMap['features'].append(Dict)
		row += 1

	if generateRandom == '2':
		neighbors = int(neighborsStr)
		gridLines = int(gridLinesStr)
		faultsGenerated = int(faultsGeneratedStr)
		mc1 = randomFaultsRefined(pathToCsv, pathToOmd, workDir, neighbors, gridLines, faultsGenerated)
	if generateRandom == '1':
		faultsGenerated = int(faultsGeneratedStr)
		mc1 = randomFault(pathToCsv, faultsGenerated)
	if (generateRandom == '2' or generateRandom == '1'):
		row = 0
		row_count_mc1 = mc1.shape[0]
		while row < row_count_mc1:
			entry = mc1.loc[row, 'Location']
			p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture integer values
			coords = [float(i) for i in p.findall(entry)]
			coord1 = coords[0]
			coord2 = coords[1]
			if 'Cause' in mc1.columns:
				cause = mc1.loc[row, 'Cause']
			else:
				cause = 'None'
			if 'Meters Affected' in mc1.columns:
				lis = str(mc1.loc[row, 'Meters Affected'])
				meters = lis.split()
				meterCount = len(meters)
			else:
				lis = ''
				meters = []
				meterCount = 0
				meterMinFilter = -10e10
				meterMaxFilter = 10e10
			if 'Start' in mc1.columns:		
				duration = datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
				time = datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S'))
				timeMin = datetime_to_float(datetime.datetime.strptime(timeMinFilter, '%Y-%m-%d %H:%M:%S'))
				timeMax = datetime_to_float(datetime.datetime.strptime(timeMaxFilter, '%Y-%m-%d %H:%M:%S'))
				start = str(mc1.loc[row, 'Start'])
			else:
				duration = 0.0
				time = 0.0
				timeMin = -10e10
				timeMax = 10e10
				durationMinFilter = -10e10
				durationMaxFilter = 10e10
				start = ''

			if 'component_type' in mc1.columns:
				componentType = mc1.loc[row, 'component_type']
			else:
				componentType = 'None'
			if 'fault_type' in mc1.columns:
				faultType = mc1.loc[row, 'fault_type']
			else:
				faultType = 'None'

			Dict = {}
			Dict['geometry'] = {'type': 'Point', 'coordinates': [coord1, coord2]}
			Dict['type'] = 'Feature'
			Dict['properties'] = {'name': 'New_Fault_' + str(row+1), 'meterCount': int(meterCount), 'time': time, 'timeMin':timeMin, 'timeMax':timeMax, 'meterMinFilter': int(meterMinFilter), 'meterMaxFilter': int(meterMaxFilter), 'cause': str(cause), 'componentType': str(componentType), 'faultType': str(faultType), 'componentFilter':str(componentTypeFilter), 'faultFilter': str(faultTypeFilter), 'causeFilter': causeFilter, 'duration': int(duration), 'durationMinFilter': int(durationMinFilter), 'durationMaxFilter': int(durationMaxFilter), 'meters': lis, 'pointColor': 'red', 'popupContent': '<br><br>Fault start time: <b>' + str(start) + '</b><br> Fault duration: <b>' + str(duration) + ' seconds</b><br>Location: <b>' + str(coords) + '</b><br>Cause: <b>' + str(cause) + '</b><br>Meters Affected: <b><br>' + str(lis) + '</b><br>Count of Meters Affected: <b>' + str(len(meters)) + '</b><br>Line Type: <b>' + str(componentType) + '</b><br>Fault Type: <b>' + str(faultType) + '</b>.'}
			outageMap['features'].append(Dict)
			row += 1

	if not os.path.exists(workDir):
		os.makedirs(workDir)
	shutil.copy(omf.omfDir + '/templates/geoJsonMap.html', workDir)
	with open(pJoin(workDir,'geoJsonFeatures.js'),"w") as outFile:
		outFile.write("var geojson =")
		json.dump(outageMap, outFile, indent=4)

	#Save geojson dict to then read into outdata in work function below
	with open(pJoin(workDir,'geoDict.js'),"w") as outFile:
		json.dump(outageMap, outFile, indent=4)

	# stacked bar chart to show outage timeline
	if 'Start' in mc.columns:
		row = 0
		date = [[] for _ in range(365)]
		while row < row_count_mc:
			dt = datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')
			day = int(dt.strftime('%j')) - 1
			date[day].append(datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S')))
			row += 1
		# convert array of durations into jagged numpy object
		jaggedData = np.array(date)
		# get lengths of each row of data
		lens = np.array([len(i) for i in jaggedData])
		# mask of valid places in each row to fill with zeros
		mask = np.arange(lens.max()) < lens[:,None]
		# setup output array and put elements from jaggedData into masked positions
		data = np.zeros(mask.shape, dtype=jaggedData.dtype)
		data[mask] = np.concatenate(jaggedData)
		numCols = data.shape[1]
		graphData = []
		currCol = 0
		while currCol < numCols:
			graphData.append(go.Bar(name='Fault ' + str(currCol+1), x = list(range(365)), y = data[:,currCol]))
			currCol += 1
		timeline = go.Figure(data = graphData)
		timeline.layout.update(
			barmode='stack',
			showlegend=False,
			xaxis=go.layout.XAxis(
				title=go.layout.xaxis.Title(text='Day of the year')
			),
			yaxis=go.layout.YAxis(
				title=go.layout.yaxis.Title(text='Outage time (seconds)')
			)
		)
	else: timeline = None
	return {'timeline': timeline}

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}

	# Write in the feeder
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	# Run the main functions of the program
	with open(pJoin(modelDir, inputDict['outageFileName']), 'w') as f:
		pathToData = f.name
		f.write(inputDict['outageData'])
	plotOuts = outageCostAnalysis(
		modelDir + '/' + feederName + '.omd', #OMD Path
		pathToData,
		modelDir, #Work directory.
		inputDict['generateRandom'],
		inputDict['numberOfCustomers'],
		inputDict['sustainedOutageThreshold'],
		inputDict['causeFilter'],
		inputDict['componentTypeFilter'],
		inputDict['faultTypeFilter'],
		inputDict['timeMinFilter'],
		inputDict['timeMaxFilter'],
		inputDict['meterMinFilter'],
		inputDict['meterMaxFilter'],
		inputDict['durationMinFilter'],
		inputDict['durationMaxFilter'],
		inputDict['neighborsStr'],
		inputDict['gridLinesStr'],
		inputDict['faultsGeneratedStr'])
	
	# Textual outputs of cost statistic
	with open(pJoin(modelDir,"statsCalc.html"),"rb") as inFile:
		outData["statsHtml"] = inFile.read()

	#The geojson dictionary to load into the outageCost.py template
	with open(pJoin(modelDir,"geoDict.js"),"rb") as inFile:
		outData["geoDict"] = inFile.read()

	# Plotly outputs
	layoutOb = go.Layout()
	outData["timelineData"] = json.dumps(plotOuts.get('timeline',{}), cls=py.utils.PlotlyJSONEncoder)
	outData["timelineLayout"] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)

	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"feederName1": "Olin Barre Fault",
		"generateRandom": "2",
		"numberOfCustomers": "192",
		"sustainedOutageThreshold": "300",
		"causeFilter": "0",
		"componentTypeFilter": "All",
		"faultTypeFilter": "All",
		"timeMinFilter": "2000-01-01 00:00:01",
		"timeMaxFilter": "2000-12-31 00:00:30",
		"meterMinFilter": "0",
		"meterMaxFilter": "1000",
		"durationMinFilter": "0",
		"durationMaxFilter": "100000",
		"outageFileName": "outagesNew3.csv",
		"neighborsStr": "5",
		"gridLinesStr": "100",
		"faultsGeneratedStr": "100",
		"outageData": open(pJoin(__neoMetaModel__._omfDir,"scratch","smartSwitching","outagesNew3.csv"), "r").read(),
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	# outageCostAnalysis(omf.omfDir + '/static/publicFeeders/Olin Barre LatLon.omd', omf.omfDir + '/scratch/smartSwitching/Outages.csv', None, '60', '1')
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()

#outageCostAnalysis('C:/Users/granb/omf/omf/static/publicFeeders/Olin Barre LatLon.omd', 'C:/Users/granb/omf/omf/scratch/smartSwitching/Outages.csv', None, '60', '1')
#drawOutageMap('C:/Users/granb/omf/omf/static/publicFeeders/Olin Barre LatLon.omd', 'C:/Users/granb/omf/omf/scratch/smartSwitching/Outages.csv', None, '60', '1')
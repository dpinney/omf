import pandas as pd
import numpy as np
import scipy
from sklearn.preprocessing import LabelEncoder
from scipy import spatial
import scipy.stats as st
import random
import warnings
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
		threshold = 10e-5
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

def generateMultiple(mc):
	if 'Start' in mc.columns:
		row = 0
		row_count_mc = mc.shape[0]
		date = [[] for _ in range(365)]
		print(date)
		while row < row_count_mc:
			dt = datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')
			day = int(dt.strftime('%j')) - 1
			date[day].append(datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S')))
			row += 1
		dayDurations = [None] * 365


	else:
		print('"Start" is not present in the input data.')

def generateDistribution(mc, test, faultsGenerated):
	numberDurations = int(faultsGenerated)
	mc['duration'] = 0

	row_count_mc = mc.shape[0]
	row = 0
	while row < row_count_mc:
		duration = float(datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S')))
		mc.loc[row, 'duration'] = duration
		row += 1

	enc = LabelEncoder()
	label = enc.fit(mc['duration'])
	mc2 = label.transform(mc['duration'])
	np.ndarray.sort(mc2)
	mc2_std = mc2

	dist_names = ['norm', 
				  'weibull_min',
				  'pareto',
				  'uniform',
				  'beta',
				  'gamma',
				  'expon',
				  'lognorm',
				  'triang',
				  'dweibull']
	size = len(mc2_std)
	x = np.arange(len(mc2))
	dist_results = []
	chi_square = []
	p_values = []

	percentile_bins = np.linspace(0, 100, num=50, endpoint=True)
	percentile_cutoffs = np.percentile(mc2_std, percentile_bins)
	mc2_std_range = [mc2_std.min(),mc2_std.max()]
	observed_frequency, bins = (np.histogram(mc2_std, bins = percentile_cutoffs, range=range))
	cumulative_observed_frequency = np.cumsum(observed_frequency)
	cumulative_observed_frequency = [x or 10e-100 for x in cumulative_observed_frequency]

	for dist_name in dist_names:
		dist = getattr(st, dist_name)
		param = dist.fit(mc2_std)
		
		# Applying the Kolmogorov-Smirnov test
		D, p = st.kstest(mc2_std, dist_name, args=param)
		p_values.append(p)

		# get expected counts in percentile bins based on cdf
		cdf_fitted = dist.cdf(percentile_cutoffs, *param[:-2], loc=param[-2], scale=param[-1])
		expected_frequency = []
		for bin in range(len(percentile_bins)-1):
			expected_cdf_area = cdf_fitted[bin+1] - cdf_fitted[bin]
			expected_frequency.append(expected_cdf_area)

		# calculate chi-squared
		expected_frequency = np.array(expected_frequency) * size
		cumulative_expected_frequency = np.cumsum(expected_frequency)

		chisq = sum(((cumulative_expected_frequency - cumulative_observed_frequency)**2) / cumulative_observed_frequency)
		chi_square.append(chisq)

		dist_results.append((dist_name, p))

	results = pd.DataFrame()
	results['Distribution'] = dist_names
	results['chi_square'] = chi_square
	results['p_value'] = p_values
	results.sort_values([test], inplace=True)

	print(results)

	# Get the top distribution
	if test == 'p_value':
		dist = results['Distribution'].iloc[0]
	if test == 'chi_square':
		dist = results['Distribution'].iloc[9]

	# Set up distribution and store distribution paraemters
	best = getattr(st, dist)
	param = best.fit(mc2)

	print('Distribution used for generating faults: ' + str(dist))

	number = 0
	newDurations = []
	while number < numberDurations:
		# we only want positive durations
		newEntry = -1
		if dist == 'norm':
			while newEntry < 0:
				newEntry = scipy.stats.norm.rvs(param[0], param[1])
			newDurations.append(newEntry)
		if dist == 'expon':
			while newEntry < 0:
				newEntry = scipy.stats.expon.rvs(param[0], param[1])
			newDurations.append(newEntry)
		if dist == 'dweibull':
			while newEntry < 0:
				newEntry = scipy.stats.dweibull.rvs(param[0], param[1], param[2])
			newDurations.append(newEntry)
		if dist == 'weibull_min':
			while newEntry < 0:
				newEntry = scipy.stats.weibull_min.rvs(param[0], param[1], param[2])
			newDurations.append(newEntry)
 		if dist == 'pareto':
			while newEntry < 0:
				newEntry = scipy.stats.pareto.rvs(param[0], param[1], param[2])
			newDurations.append(newEntry)
		if dist == 'uniform':
			while newEntry < 0:
				newEntry = scipy.stats.uniform.rvs(param[0], param[1])
			newDurations.append(newEntry)
		if dist == 'triang':
			while newEntry < 0:
				newEntry = scipy.stats.triang.rvs(param[0], param[1], param[2])
			newDurations.append(newEntry)
		if dist == 'beta':
			while newEntry < 0:
				newEntry = scipy.stats.beta.rvs(param[0], param[1], param[2], param[3])
			newDurations.append(newEntry)
		if dist == 'gamma':
			while newEntry < 0:
				newEntry = scipy.stats.gamma.rvs(param[0], param[1], param[2], param[3])
			newDurations.append(newEntry)
		if dist == 'lognorm':
			while newEntry < 0:
				newEntry = scipy.stats.lognorm.rvs(param[0], param[1], param[2])
			newDurations.append(newEntry)
		number += 1

	return newDurations

def heatMap(mc, test):
	'create a heat map based on input DataFrame with location, component type, fault type, and cause'
	compType = {}
	location = {}
	cause = {}
	start = {}
	duration = {}
	durCause = {}
	durTime = {}
	durLocation = {}
	row_count_mc = mc.shape[0]
	row = 0
	while row < row_count_mc:
		if mc.loc[row, 'Fault Type'] != 'None':
			if (test == 'dependent' and 'Finish' in mc.columns and 'Start' in mc.columns):
				thisDuration = datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
			# start and end times for faults (note: if start exists, assume finish also exists)
			if 'Start' in mc.columns:
				if mc.loc[row, 'Start'] in start.keys():
					start[mc.loc[row, 'Start']] += 1
					if (test == 'dependent' and 'Finish' in mc.columns):
						durTime[str(mc.loc[row, 'Start'])] += (' ' + str(thisDuration))
				else:
					start[mc.loc[row, 'Start']] = 1
					if (test == 'dependent' and 'Finish' in mc.columns):
						durTime[str(mc.loc[row, 'Start'])] = (str(thisDuration))
				if 'Finish' in mc.columns:
					if test != 'dependent':
						if datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S')) in duration.keys():
							duration[datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))] += 1
						else:
							duration[datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))] = 1

			causefault = (mc.loc[row, 'Cause'], mc.loc[row, 'Fault Type'])
			# comp type will store which causes and fault types can occur for a given line type
			if mc.loc[row, 'Component Type'] in compType.keys():
				if causefault not in compType[mc.loc[row, 'Component Type']]['causes']:
					compType[mc.loc[row, 'Component Type']]['causes'].append(causefault)
			else:
				compType[mc.loc[row, 'Component Type']] = {}
				compType[mc.loc[row, 'Component Type']]['causes'] = []
				compType[mc.loc[row, 'Component Type']]['causes'].append(causefault)
			# location of the faults as well as the component type and meters affected, since the latter two are completely dependent on the former (if we have no locations for the components)
			if (mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Component Type'] + ' ' + mc.loc[row, 'Meters Affected']) in location.keys():
				location[mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Component Type'] + ' ' + mc.loc[row, 'Meters Affected']] += 1
				if ('Finish' in mc.columns and test == 'dependent'):
					durLocation[str(mc.loc[row, 'Location'])] += (' ' + str(thisDuration))
			else:
				location[mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Component Type'] + ' ' + mc.loc[row, 'Meters Affected']] = 1
				if ('Finish' in mc.columns and test == 'dependent'):
					durLocation[str(mc.loc[row, 'Location'])] = (str(thisDuration))
			# causes and fault types for the faults
			if causefault in cause.keys():
				cause[causefault] += 1
				if ('Finish' in mc.columns and test == 'dependent'):
					durCause[str(causefault)] += (' ' + str(thisDuration)) 
			else:
				cause[causefault] = 1
				if ('Finish' in mc.columns and test == 'dependent'):
					durCause[str(causefault)] = str(thisDuration)
		row += 1

	# find the total number of faults that occur in each dictionary
	# create a heat map by dividing the number of each individual item by the total number found
	totalCause = sum(cause.itervalues(), 0.0)
	cause = {k: v / totalCause for k, v in cause.iteritems()}
	totalStart = sum(start.itervalues(), 0.0)
	start = {k: v / totalStart for k, v in start.iteritems()}
	if test != 'dependent':
		totalDuration = sum(duration.itervalues(), 0.0)
		duration = {k: v / totalDuration for k, v in duration.iteritems()}
	totalLocation = sum(location.itervalues(), 0.0)
	location = {k: v / totalLocation for k, v in location.iteritems()}

	# create a single dictionary to store heat map data
	heatMap = {}
	if bool(compType):
		heatMap['compType'] = compType
	else:
		print('"Component Type" is missing from input data.')
	if bool(location):
		heatMap['location'] = location
	else:
		print('"Location" is missing from input data.')
	if bool(cause):
		heatMap['cause'] = cause
	else:
		print('"Cause" is missing from input data.')
	if bool(start):
		heatMap['start'] = start
	else:
		print('"Start" is missing from input data.')
	if test != 'dependent':
		if bool(duration):
			heatMap['duration'] = duration
		else:
			print('"Finish" is missing from input data.')

	return heatMap, durCause, durTime, durLocation

def randomFault(pathToCsv, faultsGenerated, test, depDist):
	'using an input csv file with outage data, create a heat map object and generate a random fault'
	mc = pd.read_csv(pathToCsv)
	heatmap, durCause, durTime, durLocation = heatMap(mc, test)
	component_types = []
	locations = []
	metersaffected = []
	causes = []
	fault_types = []
	starts = []
	finishes = []
	faultNumber = 0
	if (test == 'chi_square' or test == 'p_value'):
		newDurations = generateDistribution(mc, test, faultsGenerated)
	while faultNumber < faultsGenerated:
		# choose a random location
		chooseLocationString = np.random.choice(heatmap['location'].keys(), replace=True, p=heatmap['location'].values())
		chooseLocation = chooseLocationString.split()
		location = str(chooseLocation[0]) + ' ' + str(chooseLocation[1])
		if heatmap['start']:
			start = np.random.choice(heatmap['start'].keys(), replace=True, p=heatmap['start'].values())
			if test != 'dependent':
				if heatmap['duration']:
					if (test == 'chi_square' or test == 'p_value'):
						duration = np.float64(math.ceil(newDurations[faultNumber]))
						start = str(start)
						finish = str(datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=duration))
					else:
						duration = np.random.choice(heatmap['duration'].keys(), replace=True, p=heatmap['duration'].values())
						start = str(start)
						finish = str(datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=duration))
		# Note: for this method, component type is completely dependent on location
		compType = str(chooseLocation[2])
		
		# draw out meters affected
		meterdata = chooseLocation[3:len(chooseLocation)]
		metersaff = ' '
		metersaff.join(meterdata)

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
		# If we want to generate durations assuming dependency of variables		
		if test == 'dependent':
			def _ss(data):
				"""Return sum of square deviations of sequence data."""
				c = sum(data) / len(data)
				ss = sum((x-c)**2 for x in data)
				return ss

			def stddev(data):
				"""Compute the sample standard deviation."""
				n = len(data)
				if n < 2:
					return 0
				ss = _ss(data)
				pvar = ss/(n-1)
				return pvar**0.5

			avgDuration = 0.0
			stdDuration = 0.0

			if (depDist == '0' or depDist == '1' or depDist == '2' or depDist == '4'):
				causeDurList = list(durCause[str(causefault)].split(' '))
				causeDurList = [float(i) for i in causeDurList]
				avgCause = sum(causeDurList) / len(causeDurList)
				stdCause = stddev(causeDurList)
				avgDuration += avgCause
				stdDuration += stdCause

			if (depDist == '0' or depDist == '1' or depDist == '3' or depDist == '5'):
				timeDurList = list(durTime[str(start)].split(' '))
				timeDurList = [float(i) for i in timeDurList]
				avgTime = sum(timeDurList) / len(timeDurList)
				stdTime = stddev(timeDurList)
				avgDuration += avgTime
				stdDuration += stdTime

			if (depDist == '0' or depDist == '2' or depDist == '3' or depDist == '6'):
				locationDurList = list(durLocation[str(location)].split(' '))
				locationDurList = [float(i) for i in locationDurList]
				avgLocation = sum(locationDurList) / len(locationDurList)
				stdLocation = stddev(locationDurList)
				avgDuration += avgLocation
				stdDuration += stdLocation

			if depDist == '0':
				avgDuration = avgDuration / 3
				stdDuration = stdDuration / 3
			if (depDist == '1' or depDist == '2' or depDist == '3'):
				avgDuration = avgDuration / 2
				stdDuration = stdDuration / 2

			duration = -1
			while duration < 0:
				duration = np.random.normal(loc=avgDuration, scale=stdDuration/1000)
			finish = str(datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=math.ceil(duration)))

		locations.append(location)
		component_types.append(compType)
		causes.append(causefault[0])
		starts.append(start)
		finishes.append(finish)
		metersaffected.append(meterdata)
		fault_types.append(causefault[1])
		faultNumber += 1	
	
	data = {'Start': starts, 'Finish': finishes, 'Component Type': component_types, 'Location': locations, 'Cause': causes, 'Fault Type': fault_types, 'Meters Affected': metersaffected}
	
	faults = pd.DataFrame(data)
	return faults

def locationMap(mc, gridLines, lines, test):
	'Create a location heatmap, where the 2D space is partitioned into a lattice. The function for the heat map is inversely proportional to the distance of the nth neighbor from each point in the lattice.'
	# lists to hold the latitudes, longitudes, and coordinate pairs of each fault location
	longitudes = []
	latitudes = []
	coords = []
	lineNameMeters = {}
	durLocation = {}
	coordDuration = []
	
	# populate the lists
	row = 0
	row_count_mc = mc.shape[0]
	while row < row_count_mc:
		locString = mc.loc[row, 'Location']
		metersAffected = mc.loc[row, 'Meters Affected']
		tempDuration = datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
		p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture integer values
		coord = [float(i) for i in p.findall(locString)]
		latitude = coord[0]
		longitude = coord[1]
		latitudes.append(latitude)
		longitudes.append(longitude)
		coords.append(coord)
		coordDuration.append(tempDuration)
		lineName = locationToName(locString, lines)
		if lineName not in lineNameMeters.keys():
			lineNameMeters[str(lineName)] = metersAffected
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
			nth_distance.append(1/max(distances))
			if test == 'dependent':
				if (str(xv[i]) + ' ' + str(yv[j])) in durLocation.keys():
					durLocation[str(xv[i]) + ' ' + str(yv[j])] += (' ' + str(coordDuration[indices.item(0)]))
				else:
					durLocation[str(xv[i]) + ' ' + str(yv[j])] = str(coordDuration[indices.item(0)])
			i += 1
		j += 1
	# normalize
	total_distance = sum(nth_distance)
	nth_distance[:] = [x / total_distance for x in nth_distance]

	return nth_distance, xv, yv, lineNameMeters, durLocation

def heatMapRefined(mc, test):
	'create a heat map based on input DataFrame with component type, fault type, and cause'
	componentType = {}
	compType = {}
	cause = {}
	start = {}
	duration = {}
	durCause = {}
	durTime = {}
	#faultType = {}
	row_count_mc = mc.shape[0]
	row = 0
	while row < row_count_mc:
		
		if ('Finish' in mc.columns and 'Start' in mc.columns and test == 'dependent'):
			thisDuration = datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
		# start and end times for faults (note: if start exists, assume finish also exists)
		if 'Start' in mc.columns:
			if mc.loc[row, 'Start'] in start.keys():
				start[mc.loc[row, 'Start']] += 1
				if (test == 'dependent' and 'Finish' in mc.columns):
					durTime[str(mc.loc[row, 'Start'])] += (' ' + str(thisDuration))
			else:
				start[mc.loc[row, 'Start']] = 1
				if (test == 'dependent' and 'Finish' in mc.columns):
					durTime[str(mc.loc[row, 'Start'])] = str(thisDuration)
			if 'Finish' in mc.columns:
				if test != 'dependent':
					if datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S')) in duration.keys():
						duration[datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))] += 1
					else:
						duration[datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))] = 1

		causefault = (mc.loc[row, 'Cause'], mc.loc[row, 'Fault Type'])
		# component types for faults
		if mc.loc[row, 'Component Type'] in componentType.keys():
			componentType[mc.loc[row, 'Component Type']] += 1
		else:
			componentType[mc.loc[row, 'Component Type']] = 1
		# comp type will store which causes and fault types can occur for a given line type
		if mc.loc[row, 'Component Type'] in compType.keys():
			if causefault not in compType[mc.loc[row, 'Component Type']]['causes']:
				compType[mc.loc[row, 'Component Type']]['causes'].append(causefault)
		else:
			compType[mc.loc[row, 'Component Type']] = {}
			compType[mc.loc[row, 'Component Type']]['causes'] = []
			compType[mc.loc[row, 'Component Type']]['causes'].append(causefault)

		# causes and fault types for the faults
		if causefault in cause.keys():
			cause[causefault] += 1
			if ('Finish' in mc.columns and test == 'dependent'):
				durCause[str(causefault)] += (' ' + str(thisDuration)) 
		else:
			cause[causefault] = 1
			if ('Finish' in mc.columns and test == 'dependent'):
				durCause[str(causefault)] = str(thisDuration)
		row += 1
	# find the total number of faults that occur in each dictionary
	# create a heat map by dividing the number of each individual item by the total number found
	totalCause = sum(cause.itervalues(), 0.0)
	cause = {k: v / totalCause for k, v in cause.iteritems()}
	totalComponentType = sum(componentType.itervalues(), 0.0)
	componentType = {k: v / totalComponentType for k, v in componentType.iteritems()}
	totalStart = sum(start.itervalues(), 0.0)
	start = {k: v / totalStart for k, v in start.iteritems()}
	if test != 'dependent':
		totalDuration = sum(duration.itervalues(), 0.0)
		duration = {k: v / totalDuration for k, v in duration.iteritems()}

	# create a single dictionary to store heat map data
	heatMap = {}
	if bool(componentType):
		heatMap['componentType'] = componentType
	else:
		print('"Component Type" is missing from input data.')
	if bool(compType):
		heatMap['compType'] = compType
	else:
		print('"CompType is missing from input data.')
	if bool(cause):
		heatMap['cause'] = cause
	else:
		print('"Cause" is missing from input data.')
	if bool(start):
		heatMap['start'] = start
	else:
		print('"Start" is missing from input data.')
	if test != 'dependent':
		if bool(duration):
			heatMap['duration'] = duration
		else:
			print('"Finish" is missing from input data.')

	return heatMap, durCause, durTime

def randomFaultsRefined(pathToCsv, pathToOmd, workDir, gridLines, faultsGenerated, test, component, depDist):
	'Function that generates a DataFrame with a set of faults based on an original set of data and which selects the location using the lattice method'
	
	# Check that we're in the proper directory
	if not workDir:
		workDir = tempfile.mkdtemp()
		print '@@@@@@', workDir

	# Create heatmaps for location and the other three parameters
	mc = pd.read_csv(pathToCsv)
	# create a DataFrame with the line name and the coordinates of its edges
	with open(pathToOmd) as inFile:
		tree = json.load(inFile)['tree']
	outageMap = geo.omdGeoJson(pathToOmd, conversion = False)
	with open(workDir + '/lines.csv', mode='w') as lines:

		fieldnames = ['line_name', 'coords1', 'coords2']
		writer = csv.DictWriter(lines, fieldnames)

		writer.writeheader()

		for key in tree.keys():
			obtype = tree[key].get("object","")
			if obtype == 'underground_line' or obtype == 'overhead_line' or obtype == 'triplex_line':
				writer.writerow({'line_name': tree[key]['name'], 'coords1': nodeToCoords(outageMap, tree[key]['from']), 'coords2': nodeToCoords(outageMap, tree[key]['to'])})

	lines.close()
	lines = pd.read_csv(workDir + '/lines.csv')

	nth_distance, xv, yv, lineNameMeters, durLocation = locationMap(mc, gridLines, lines, test)

	with open(workDir + '/faultLines.csv', mode='w') as faultLines:

		fieldnames = ['line_name', 'coords1', 'coords2']
		writer = csv.DictWriter(faultLines, fieldnames)

		writer.writeheader()

		for key in tree.keys():
			obtype = tree[key].get("object","")
			if obtype == 'underground_line' or obtype == 'overhead_line' or obtype == 'triplex_line':
				if str(tree[key]['name']) in lineNameMeters.keys():
					writer.writerow({'line_name': tree[key]['name'], 'coords1': nodeToCoords(outageMap, tree[key]['from']), 'coords2': nodeToCoords(outageMap, tree[key]['to'])})

	faultLines.close()

	faultLines = pd.read_csv(workDir + '/faultLines.csv')
	heatMap, durCause, durTime = heatMapRefined(mc, test)
	# Create lists to store the new outage data.
	component_types = []
	locations = []
	causes = []
	fault_types = []
	starts = []
	finishes = []
	metersData = []
	if (test == 'chi_square' or test == 'p_value'):
		newDurations = generateDistribution(mc, test, faultsGenerated)
	# Generate a set number of new faults.
	faultNumber = 0
	while faultNumber < faultsGenerated:
		if heatMap['start']:
			start = np.random.choice(heatMap['start'].keys(), replace=True, p=heatMap['start'].values())
			if (test == 'chi_square' or test == 'p_value'):
				duration = np.float64(math.ceil(newDurations[faultNumber]))
				start = str(start)
				finish = str(datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=duration))
			else:
				if test != 'dependent':
					duration = np.random.choice(heatMap['duration'].keys(), replace=True, p=heatMap['duration'].values())
					start = str(start)
					finish = str(datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=duration))

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

		# get a location that lies on a line, based on the location heat map generated, then estimate the meters affected based on nearby lines
		# Note: if the line in question has meters affected data, just use that. Otherwise, approximation is necessary
		trueLocation = nearestLine(location, lines, component)
		nearestLocMeters = nearestLine(location, faultLines, component)
		if 'Meters Affected' in mc.columns:
			if str(locationToName(nearestLocMeters, faultLines)) in lineNameMeters.keys():
				metersAffected = lineNameMeters[str(locationToName(nearestLocMeters, faultLines))]
			else:
				metersAffected = 'None'
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
			if chooseCause in heatMap['compType'][component]['causes']:
				causefault = chooseCause
				causeChosen = True
		
		# If we want to generate durations assuming dependency of variables		
		if test == 'dependent':
			def _ss(data):
				"""Return sum of square deviations of sequence data."""
				c = sum(data) / len(data)
				ss = sum((x-c)**2 for x in data)
				return ss

			def stddev(data):
				"""Compute the sample standard deviation."""
				n = len(data)
				if n < 2:
					return 0
				ss = _ss(data)
				pvar = ss/(n-1)
				return pvar**0.5

			avgDuration = 0.0
			stdDuration = 0.0

			if (depDist == '0' or depDist == '1' or depDist == '2' or depDist == '4'):
				causeDurList = list(durCause[str(causefault)].split(' '))
				causeDurList = [float(i) for i in causeDurList]
				avgCause = sum(causeDurList) / len(causeDurList)
				stdCause = stddev(causeDurList)
				avgDuration += avgCause
				stdDuration += stdCause

			if (depDist == '0' or depDist == '1' or depDist == '3' or depDist == '5'):
				timeDurList = list(durTime[str(start)].split(' '))
				timeDurList = [float(i) for i in timeDurList]
				avgTime = sum(timeDurList) / len(timeDurList)
				stdTime = stddev(timeDurList)
				avgDuration += avgTime
				stdDuration += stdTime

			if (depDist == '0' or depDist == '2' or depDist == '3' or depDist == '6'):
				locationDurList = list(durLocation[str(location)].split(' '))
				locationDurList = [float(i) for i in locationDurList]
				avgLocation = sum(locationDurList) / len(locationDurList)
				stdLocation = stddev(locationDurList)
				avgDuration += avgLocation
				stdDuration += stdLocation

			if depDist == '0':
				avgDuration = avgDuration / 3
				stdDuration = stdDuration / 3
			if (depDist == '1' or depDist == '2' or depDist == '3'):
				avgDuration = avgDuration / 2
				stdDuration = stdDuration / 2

			duration = -1
			while duration < 0:
				duration = np.random.normal(loc=avgDuration, scale=stdDuration/1000)
			finish = str(datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(seconds=math.ceil(duration)))

		# Add this fault to the set of faults.
		locations.append(trueLocation)
		component_types.append(component)
		causes.append(causefault[0])
		metersData.append(metersAffected)
		starts.append(start)
		finishes.append(finish)
		fault_types.append(causefault[1])
		faultNumber += 1
	
	data = {'Start': starts, 'Finish': finishes, 'Component Type': component_types, 'Location': locations, 'Cause': causes, 'Fault Type': fault_types, 'Meters Affected': metersData}

	faults = pd.DataFrame(data)
	return faults

def outageCostAnalysis(pathToOmd, pathToCsv, workDir, generateRandom, graphData, numberOfCustomers, sustainedOutageThreshold, causeFilter, componentTypeFilter, faultTypeFilter, timeMinFilter, timeMaxFilter, meterMinFilter, meterMaxFilter, durationMinFilter, durationMaxFilter, gridLinesStr, faultsGeneratedStr, test, depDist):
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

	def stats(mc):
		# calculate SAIDI
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
		if (SAIDI != 0):
			CAIDI = SAIDI / SAIFI
		else: CAIDI = 'Error: Check sustained outage threshold'
	
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

		return SAIDI, SAIFI, CAIDI, ASAI, MAIFI

	mc = pd.read_csv(pathToCsv)

	if 'Start' in mc.columns:
		SAIDI, SAIFI, CAIDI, ASAI, MAIFI = stats(mc)

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

	# Graph input fault data if the user requests
	if (graphData == '0' or graphData == '1'):
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
			if 'Component Type' in mc.columns:
				componentType = mc.loc[row, 'Component Type']
			else:
				componentType = 'None'
			if 'Fault Type' in mc.columns:
				faultType = mc.loc[row, 'Fault Type']
			else:
				faultType = 'None'

			Dict = {}
			Dict['geometry'] = {'type': 'Point', 'coordinates': [coord1, coord2]}
			Dict['type'] = 'Feature'
			Dict['properties'] = {'name': 'Old_Fault_' + str(row+1), 'meterCount': int(meterCount), 'time': time, 'timeMin':timeMin, 'timeMax':timeMax, 'meterMinFilter': int(meterMinFilter), 'meterMaxFilter': int(meterMaxFilter), 'cause': str(cause), 'componentType': str(componentType), 'faultType': str(faultType), 'componentFilter':str(componentTypeFilter), 'faultFilter': str(faultTypeFilter), 'causeFilter': causeFilter, 'duration': int(duration), 'durationMinFilter': int(durationMinFilter), 'durationMaxFilter': int(durationMaxFilter), 'meters': str(mc.loc[row, 'Meters Affected']), 'pointColor': 'blue', 'popupContent': '<br><br>Fault start time: <b>' + str(mc.loc[row, 'Start']) + '</b><br> Fault duration: <b>' + str(duration) + ' seconds</b><br>Location: <b>' + str(coords) + '</b><br>Cause: <b>' + str(cause) + '</b><br>Meters Affected: <b><br>' + str(mc.loc[row, 'Meters Affected']) + '</b><br>Count of Meters Affected: <b>' + str(len(meters)) + '</b><br>Line Type: <b>' + str(componentType) + '</b><br>Fault Type: <b>' + str(faultType) + '</b>.'}
			outageMap['features'].append(Dict)
			row += 1
	# generate new fault data if the user requests
	if generateRandom == '2':
		gridLines = int(gridLinesStr)
		faultsGenerated = int(faultsGeneratedStr)
		mc1 = randomFaultsRefined(pathToCsv, pathToOmd, workDir, gridLines, faultsGenerated, test, componentTypeFilter, depDist)
	if generateRandom == '1':
		faultsGenerated = int(faultsGeneratedStr)
		mc1 = randomFault(pathToCsv, faultsGenerated, test, depDist)
	# graph the generated faults if the user requests
	if ((generateRandom == '2' or generateRandom == '1') and (graphData == '0' or graphData == '2')):
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

			if 'Component Type' in mc1.columns:
				componentType = mc1.loc[row, 'Component Type']
			else:
				componentType = 'None'
			if 'Fault Type' in mc1.columns:
				faultType = mc1.loc[row, 'Fault Type']
			else:
				faultType = 'None'

			Dict = {}
			Dict['geometry'] = {'type': 'Point', 'coordinates': [coord1, coord2]}
			Dict['type'] = 'Feature'
			Dict['properties'] = {'name': 'New_Fault_' + str(row+1), 'meterCount': int(meterCount), 'time': time, 'timeMin':timeMin, 'timeMax':timeMax, 'meterMinFilter': int(meterMinFilter), 'meterMaxFilter': int(meterMaxFilter), 'cause': str(cause), 'componentType': str(componentType), 'faultType': str(faultType), 'componentFilter':str(componentTypeFilter), 'faultFilter': str(faultTypeFilter), 'causeFilter': causeFilter, 'duration': int(duration), 'durationMinFilter': int(durationMinFilter), 'durationMaxFilter': int(durationMaxFilter), 'meters': lis, 'pointColor': 'red', 'popupContent': '<br><br>Fault start time: <b>' + str(start) + '</b><br> Fault duration: <b>' + str(duration) + ' seconds</b><br>Location: <b>' + str(coords) + '</b><br>Cause: <b>' + str(cause) + '</b><br>Meters Affected: <b><br>' + str(lis) + '</b><br>Count of Meters Affected: <b>' + str(len(meters)) + '</b><br>Line Type: <b>' + str(componentType) + '</b><br>Fault Type: <b>' + str(faultType) + '</b>.'}
			outageMap['features'].append(Dict)
			row += 1

		# stacked bar chart to show outage timeline for generated random faults
		if 'Start' in mc1.columns:
			if 'Meters Affected' in mc1.columns:
				SAIDI1, SAIFI1, CAIDI1, ASAI1, MAIFI1 = stats(mc1)
				print('Reliability Metrics for the new outages:\nSAIDI: ' + str(SAIDI1) + '\nSAIFI: ' + str(SAIFI1) + '\nCAIDI: ' + str(CAIDI1) + '\nASAI: ' + str(ASAI1) + '\nMAIFI: ' + str(MAIFI1))
			else:
				print('There is no data on number of meters affected for the new outages.')
			row = 0
			date = [[] for _ in range(365)]
			while row < row_count_mc1:
				dt = datetime.datetime.strptime(mc1.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')
				day = int(dt.strftime('%j')) - 1
				date[day].append(datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc1.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S')))
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
			timeline1 = go.Figure(data = graphData)
			timeline1.layout.update(
				barmode='stack',
				showlegend=False,
				xaxis=go.layout.XAxis(
					title=go.layout.xaxis.Title(text='Day of the year')
				),
				yaxis=go.layout.YAxis(
					title=go.layout.yaxis.Title(text='Outage time (seconds)')
				)
			)
		else: timeline1 = None
	else: timeline1 = None

	if not os.path.exists(workDir):
		os.makedirs(workDir)
	shutil.copy(omf.omfDir + '/templates/geoJsonMap.html', workDir)
	with open(pJoin(workDir,'geoJsonFeatures.js'),"w") as outFile:
		outFile.write("var geojson =")
		json.dump(outageMap, outFile, indent=4)

	#Save geojson dict to then read into outdata in work function below
	with open(pJoin(workDir,'geoDict.js'),"w") as outFile:
		json.dump(outageMap, outFile, indent=4)

	# stacked bar chart to show outage timeline for input .csv data
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
	else:
		timeline = None
		print('There is no time data for the new outages.')

	return {'timeline': timeline, 'timeline1': timeline1}

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
		inputDict['graphData'],
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
		inputDict['gridLinesStr'],
		inputDict['faultsGeneratedStr'],
		inputDict['test'],
		inputDict['depDist'])
	
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
	outData["timeline1Data"] = json.dumps(plotOuts.get('timeline1',{}), cls=py.utils.PlotlyJSONEncoder)
	outData["timeline1Layout"] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)

	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"feederName1": "Olin Barre Fault",
		"generateRandom": "1",
		"graphData": "0",
		"numberOfCustomers": "192",
		"sustainedOutageThreshold": "200",
		"causeFilter": "0",
		"componentTypeFilter": "overhead_line",
		"faultTypeFilter": "All",
		"timeMinFilter": "2000-01-01 00:00:01",
		"timeMaxFilter": "2000-12-15 00:00:30",
		"meterMinFilter": "0",
		"meterMaxFilter": "100",
		"durationMinFilter": "120",
		"durationMaxFilter": "1000000",
		"outageFileName": "outagesNew3.csv",
		"gridLinesStr": "100",
		"faultsGeneratedStr": "1000",
		"test": "dependent",
		"depDist": "0",
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
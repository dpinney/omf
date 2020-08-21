import random, re, datetime, json, os, tempfile, shutil, csv, math
from os.path import join as pJoin
import pandas as pd
import numpy as np
import scipy
from scipy import spatial
import scipy.stats as st
from sklearn.preprocessing import LabelEncoder
import plotly as py
import plotly.graph_objs as go

# OMF imports
import omf
from omf import geo
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
# tooltip = 'outageCost calculates reliability metrics and creates a leaflet graph based on data from an input csv file.'
# modelName, template = __neoMetaModel__.metadata(__file__)
# hidden = False

def datetime_to_float(d):
	'helper function to convert a datetime object to a float'
	epoch = datetime.datetime.utcfromtimestamp(0)
	total_seconds = (d - epoch).total_seconds()
	return total_seconds

def coordsFromString(entry):
	'helper function to take a location string to two integer values'
	p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture float values
	coord = [float(i) for i in p.findall(str(entry))]  # Convert strings to float
	return coord

def locationToName(location, lines):
	'get the name of the line component associated with a given location (lat/lon)'
	# get the coordinates of the two points that make up the edges of the line
	coord = coordsFromString(location)
	coordLat = coord[0]
	coordLon = coord[1]
	row_count_lines = lines.shape[0]
	row = 0
	while row < row_count_lines:
		coord1Lat, coord1Lon, coord1 = coordsFromString(lines.loc[row, 'coords1'])
		coord2Lat, coord2Lon, coord2 = coordsFromString(lines.loc[row, 'coords2'])
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

def nodeToCoords(feederMap, nodeName):
	'get the latitude and longitude of a given entry in string format'
	coordStr = ''
	for key in feederMap['features']:
		if (nodeName in key['properties'].get('name','')):
			current = key['geometry']['coordinates']
			coordLis = coordsFromString(current)
			coordStr = str(coordLis[0]) + ' ' + str(coordLis[1])
	return coordLis, coordStr

	def lineToCoords(feederMap, lineName):
	'get the latitude and longitude of a given entry in string format'
	coordStr = ''
	for key in feederMap['features']:
		if (lineName in key['properties'].get('name','')):
			current = key['geometry']['coordinates']
			coordLis = coordsFromString(current)
			coordStr = str(coordLis[0]) + ' ' + str(coordLis[1]) + ' ' + str(coordLis[2]) + ' ' + str(coordLis[3])
	return coordLis, coordStr

def adjacencyList(tree):
	'helper function which creates an adjacency list representation of graph connectivity (not including reclosers, which are assumed to be points of coupling)'
	adjacList = {}
	vertices = set()
	for key in tree.keys():
		obtype = tree[key].get('object','')
		if obtype.startswith('underground_line') or obtype.startswith('overhead_line') or obtype.startswith('triplex_line') or obtype.startswith('transformer') or obtype.startswith('fuse') or obtype.startswith('regulator') or obtype.startswith('relay') or obtype.startswith('link') or obtype.startswith('fromTo'):
			if 'from' in tree[key].keys() and 'to' in tree[key].keys():
				if not tree[key]['from'] in adjacList.keys():
					adjacList[tree[key]['from']] = set()
					vertices.add(tree[key].get('from', ''))
				if not tree[key]['to'] in adjacList.keys():
					adjacList[tree[key]['to']] = set()
					vertices.add(tree[key].get('to', ''))
				adjacList[tree[key]['from']].add(tree[key]['to'])
				adjacList[tree[key]['to']].add(tree[key]['from'])
	return adjacList, vertices

def pullDataForGraph(feederMap, outputTimeline):
		device = outputTimeline.loc[row, 'Device']
		action = outputTimeline.loc[row, 'Action']
		if action == 'Load Shed' or action == 'Battery Control' or action == 'Generator Control' or action == 'Load Pickup':
			coordLis, coordStr = nodeToCoords(feederMap, device)
		else:
			coordLis, coordStr = lineToCoords(feederMap, device)
		time = outputTimeline.loc[row, 'Time']
		loadBefore = outputTimeline.loc[row, 'Load Before']
		loadAfter = outputTimeline.loc[row, 'Load After']
		return device, coordLis, coordStr, time, action, loadBefore, loadAfter

def graphMicrogrid(pathToOmd, workDir, outputTimeline, maxTime, faultedLine):
	# read in the OMD file as a tree and create a geojson map of the system
	with open(pathToOmd) as inFile:
		tree = json.load(inFile)['tree']
	feederMap = geo.omdGeoJson(pathToOmd, conversion = False)

	# find a node associated with the faulted line
	faultedNode = ''
	faultedNode2 = ''
	for key in tree.keys():
		if tree[key].get('name','') == faultedLine:
			faultedNode = tree[key]['from']
			faultedNode2 = tree[key]['to']

	# generate a list of substations
	busNodes = []
	for key in tree.keys():
		if tree[key].get('bustype','') == 'SWING':
			busNodes.append(tree[key]['name'])

	Dict = {}
	Dict['geometry'] = {'type': 'LineString', 'coordinates': [nodeToCoords(feederMap, str(faultedNode)), nodeToCoords(feederMap, str(faultedNode2))]}
	Dict['type'] = 'Feature'
	Dict['properties'] = {'name': 'faultedLine',
						  'edgeColor': 'red'}
	feederMap['features'].append(Dict)

	row = 0
	row_count_timeline = outputTimeline.shape[0]
		while row < row_count_timeline:
			device, coordLis, coordStr, time, action, loadBefore, loadAfter = pullDataForGraph(outputTimeline)

			Dict = {}
			if len(coordLis) == 2:
				Dict['geometry'] = {'type': 'Point', 'coordinates': [coordLis[0], coordLis[1]]}
				Dict['type'] = 'Feature'
				Dict['properties'] = {'device': device, 
									  'time': time,
									  'action': action,
									  'loadBefore': loadBefore,
									  'loadAfter': loadAfter,
									  'pointColor': colormap(time, maxTime), 
									  'popupContent': '<br><br>Location: <b>' + str(coords) + '</b><br>Device: <b>' + str(device) + '</b><br>Time: <b>' + str(time) + '</b><br>Action: <b>' + str(action) + '</b><br>Load Before: <b>' + str(loadBefore) + '</b><br>Load After: <b>' + str(loadAfter) + '</b>.'}
				feederMap['features'].append(Dict)
			if len(coordLis) == 4:
				Dict['geometry'] = {'type': 'LineString', 'coordinates': [[coordLis[0], coordLis[1]], [coordLis[2], coordLis[3]]]}
				Dict['type'] = 'Feature'
				Dict['properties'] = {'name': str(tree[key].get('name', '')),
									  'edgeColor': colormap(time, maxTime)
									  'popupContent': '<br><br>Location: <b>' + str(coords) + '</b><br>Device: <b>' + str(device) + '</b><br>Time: <b>' + str(time) + '</b><br>Action: <b>' + str(action) + '</b><br>Load Before: <b>' + str(loadBefore) + '</b><br>Load After: <b>' + str(loadAfter) + '</b>.'}
				outageMap['features'].append(Dict)
			row += 1

	if not os.path.exists(workDir):
		os.makedirs(workDir)
	shutil.copy(omf.omfDir + '/templates/geoJsonMap.html', workDir)
	with open(pJoin(workDir,'geoJsonFeatures.js'),'w') as outFile:
		outFile.write('var geojson =')
		json.dump(feederMap, outFile, indent=4)

	#Save geojson dict to then read into outdata in work function below
	with open(pJoin(workDir,'geoDict.js'),'w') as outFile:
		json.dump(feederMap, outFile, indent=4)

def microgridControl(pathToOmd, outputTimeline, workDir, maxTime):
	# check to see if work directory is specified; otherwise, create a temporary directory
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)
	
	# TODO: update table after calculating outage stats
	def costStatsCalc(initCustCost=None, finCustCost=None, initRestCost=None, finRestCost=None, initHardCost=None, finHardCost=None, initOutCost=None, finOutCost=None):
		new_html_str = """
			<table cellpadding="0" cellspacing="0">
				<thead>
					<tr>
						<th></th>
						<th>No-Recloser</th>
						<th>Recloser</th>
					</tr>
				</thead>
				<tbody>"""
		new_html_str += '<tr><td><b>Lost kWh Sales</b></td><td>'+str(initCustCost)+'</td><td>'+str(finCustCost)+'</td></tr>'
		new_html_str += '<tr><td><b>Restoration Labor Cost</b></td><td>'+str(initRestCost)+'</td><td>'+str(finRestCost)+'</td></tr>'
		new_html_str += '<tr><td><b>Restoration Hardware Cost</b></td><td>'+str(initHardCost)+'</td><td>'+str(finHardCost)+'</td></tr>'
		new_html_str += '<tr><td><b>Outage Cost</b></td><td>'+str(initOutCost)+'</td><td>'+str(finOutCost)+'</td></tr>'
		new_html_str +="""</tbody></table>"""

		return new_html_str

	def stats(outputTimeline):
		# TODO: calculate outage statistics
		outageStats = ''
		return outageStats

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}

	# Write in the feeder
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict['feederName1'] = feederName

	# Run the main functions of the program
	# with open(pJoin(modelDir, inputDict['csvFileName']), 'w') as f:
	# 	pathToData = f.name
	# 	f.write(inputDict['csvData'])

	plotOuts = microgridControl(
		modelDir + '/' + feederName + '.omd', #OMD Path
		pathToData,
		modelDir, #Work directory.
		inputDict['maxTime'], #computational time limit
		inputDict['stepSize'], #time step size
		inputDict['faultedLine'], #line faulted
		inputDict['networked'] # are microgrids networked?
		)
	
	# Textual outputs of cost statistic
	with open(pJoin(modelDir,'statsCalc.html'),'rb') as inFile:
		outData['statsHtml'] = inFile.read().decode()

	#The geojson dictionary to load into the outageCost.py template
	with open(pJoin(modelDir,'geoDict.js'),'rb') as inFile:
		outData['geoDict'] = inFile.read().decode()

	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,'scratch','smartSwitching','outagesNew3.csv')) as f:
		outage_data = f.read()
	defaultInputs = {
		'modelType': modelName,
		'feederName1': 'Olin Barre Geo',
		'maxTime': '3600'
		'networked': 'False'
		'outageData': outage_data
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, 'static', 'publicFeeders', defaultInputs['feederName1']+'.omd'), pJoin(modelDir, defaultInputs['feederName1']+'.omd'))
	except:
		return False
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _debugging():
	# outageCostAnalysis(omf.omfDir + '/static/publicFeeders/Olin Barre LatLon.omd', omf.omfDir + '/scratch/smartSwitching/Outages.csv', None, '60', '1')
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
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
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

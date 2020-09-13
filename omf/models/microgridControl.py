import random, re, datetime, json, os, tempfile, shutil, csv, math
from os.path import join as pJoin
import subprocess
import pandas as pd
import numpy as np
import scipy
from scipy import spatial
import scipy.stats as st
from sklearn.preprocessing import LabelEncoder
import plotly as py
import plotly.graph_objs as go
from plotly.tools import make_subplots

# OMF imports
import omf
from omf import geo
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers.opendss import dssConvert

# Model metadata:
tooltip = 'outageCost calculates reliability metrics and creates a leaflet graph based on data from an input csv file.'
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

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

def lineToCoords(tree, feederMap, lineName):
	'get the latitude and longitude of a given entry in string format'
	coordStr = ''
	coordLis = []
	lineNode = ''
	lineNode2 = ''
	for key in tree.keys():
		if tree[key].get('name','') == lineName:
			lineNode = tree[key]['from']
			print(lineNode)
			lineNode2 = tree[key]['to']
			print(lineNode2)
			coordLis1, coordStr1 = nodeToCoords(feederMap, lineNode)
			print(coordLis1)
			coordLis2, coordStr2 = nodeToCoords(feederMap, lineNode2)
			coordLis = []
			coordLis.append(coordLis1[0])
			coordLis.append(coordLis1[1])
			coordLis.append(coordLis2[0])
			coordLis.append(coordLis2[1])
			coordStr = str(coordLis[0]) + ' ' + str(coordLis[1]) + ' ' + str(coordLis[2]) + ' ' + str(coordLis[3])
	return coordLis, coordStr

def pullDataForGraph(tree, feederMap, outputTimeline, row):
		device = outputTimeline.loc[row, 'device']
		action = outputTimeline.loc[row, 'action']
		if action == 'Load Shed' or action == 'Battery Control' or action == 'Generator Control' or action == 'Load Pickup':
			coordLis, coordStr = nodeToCoords(feederMap, device)
		else:
			coordLis, coordStr = lineToCoords(tree, feederMap, device)
		time = outputTimeline.loc[row, 'time']
		loadBefore = outputTimeline.loc[row, 'loadBefore']
		loadAfter = outputTimeline.loc[row, 'loadAfter']
		return device, coordLis, coordStr, time, action, loadBefore, loadAfter

def createTimeline():
	data = {'time': ['1', '3', '7', '10', '15'],
			'device': ['l2', 's701a', 's713c', '799r', '705'],
			'action': ['Switching', 'Load Shed', 'Load Pickup', 'Battery Control', 'Generator Control'],
			'loadBefore': ['50', '20', '10', '50', '50'],
			'loadAfter': ['0', '10', '20', '60', '40']
			}
	timeline = pd.DataFrame(data, columns = ['time','device','action','loadBefore','loadAfter'])
	return timeline

def colormap(time):
	color = 8438271 - 10*int(time)
	return '{:x}'.format(int(color))

def microgridTimeline(outputTimeline, workDir):
	# check to see if work directory is specified; otherwise, create a temporary directory
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)
	
	# TODO: update table after calculating outage stats
	def timelineStats(outputTimeline):
		new_html_str = """
			<table cellpadding="0" cellspacing="0">
				<thead>
					<tr>
						<th>Device</th>
						<th>Time</th>
						<th>Action</th>
						<th>Load Before</th>
						<th>Load After</th>
					</tr>
				</thead>
				<tbody>"""
		
		row = 0
		while row < len(outputTimeline):
			new_html_str += '<tr><td>' + str(outputTimeline.loc[row, 'device']) + '</td><td>' + str(outputTimeline.loc[row, 'time']) + '</td><td>' + str(outputTimeline.loc[row, 'action']) + '</td><td>' + str(outputTimeline.loc[row, 'loadBefore']) + '</td><td>' + str(outputTimeline.loc[row, 'loadAfter']) + '</td></tr>'
			row += 1

		new_html_str +="""</tbody></table>"""

		return new_html_str

	# print all intermediate and final costs
	timelineStatsHtml = timelineStats(
		outputTimeline = outputTimeline)
	with open(pJoin(workDir, 'timelineStats.html'), 'w') as timelineFile:
		timelineFile.write(timelineStatsHtml)

	return timelineStatsHtml

def graphMicrogrid(pathToOmd, pathToMicro, workDir, maxTime, stepSize, faultedLine):
	# read in the OMD file as a tree and create a geojson map of the system
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)

	# command = 'cmd /c ' + '"julia --project=' + '"C:/Users/granb/PowerModelsONM.jl-master/" ' + 'C:/Users/granb/PowerModelsONM.jl-master/src/cli/entrypoint.jl' + ' -n ' + '"' + str(workDir) + '/circuit.dss' + '"' + ' -o ' + '"C:/Users/granb/PowerModelsONM.jl-master/output.json"'
	# os.system(command)

	with open(pJoin(__neoMetaModel__._omfDir,'scratch','RONM','output.json')) as inFile:
	# with open("C:/Users/granb/PowerModelsONM.jl-master/output.json") as inFile:
		data = json.load(inFile) 
		genProfiles = data['Generator profiles']
		simTimeSteps = []
		for i in data['Simulation time steps']:
			simTimeSteps.append(float(i))
		voltages = data['Voltages']
		loadServed = data['Load served']
		storageSOC = data['Storage SOC (%)']
	
	outputTimeline = createTimeline()

	# Create traces
	gens = go.Figure()
	gens.add_trace(go.Scatter(x=simTimeSteps, y=genProfiles['Diesel DG (kW)'],
							mode='lines',
							name='Diesel DG'))
	gens.add_trace(go.Scatter(x=simTimeSteps, y=genProfiles['Energy storage (kW)'],
							mode='lines',
							name='Energy Storage'))
	gens.add_trace(go.Scatter(x=simTimeSteps, y=genProfiles['Solar DG (kW)'],
							mode='lines',
							name='Solar DG'))
	gens.add_trace(go.Scatter(x=simTimeSteps, y=genProfiles['Grid mix (kW)'],
							mode='lines',
							name='Grid Mix'))
	# Edit the layout
	gens.update_layout(xaxis_title='Hours',
						yaxis_title='Power (kW)')

	volts = go.Figure()
	volts.add_trace(go.Scatter(x=simTimeSteps, y=voltages['Min voltage (p.u.)'],
							mode='lines',
							name='Minimum Voltage'))
	volts.add_trace(go.Scatter(x=simTimeSteps, y=voltages['Max voltage (p.u.)'],
							mode='lines',
							name='Maximum Voltage'))
	volts.add_trace(go.Scatter(x=simTimeSteps, y=voltages['Mean voltage (p.u.)'],
							mode='lines',
							name='Mean Voltage'))
	# Edit the layout
	volts.update_layout(xaxis_title='Hours',
						yaxis_title='Power (p.u.)')

	loads = go.Figure()
	loads.add_trace(go.Scatter(x=simTimeSteps, y=loadServed['Feeder load (%)'],
							mode='lines',
							name='Feeder Load'))
	loads.add_trace(go.Scatter(x=simTimeSteps, y=loadServed['Microgrid load (%)'],
							mode='lines',
							name='Microgrid Load'))
	loads.add_trace(go.Scatter(x=simTimeSteps, y=loadServed['Bonus load via microgrid (%)'],
							mode='lines',
							name='Bonus Load via Microgrid'))
	# Edit the layout
	loads.update_layout(xaxis_title='Hours',
						yaxis_title='Load (%)')

	timelineStatsHtml = microgridTimeline(outputTimeline, workDir)

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
	faultedNodeCoordLis1, faultedNodeCoordStr1 = nodeToCoords(feederMap, str(faultedNode))
	faultedNodeCoordLis2, faultedNodeCoordStr2 = nodeToCoords(feederMap, str(faultedNode2))
	Dict['geometry'] = {'type': 'LineString', 'coordinates': [faultedNodeCoordLis1, faultedNodeCoordLis2]}
	Dict['type'] = 'Feature'
	Dict['properties'] = {'name': faultedLine,
						  'edgeColor': 'red',
						  'popupContent': 'Location: <b>' + str(faultedNodeCoordStr1) + ', ' + str(faultedNodeCoordStr2) + '</b><br>Faulted Line: <b>' + str(faultedLine)}
	feederMap['features'].append(Dict)
	row = 0
	row_count_timeline = outputTimeline.shape[0]
	while row < row_count_timeline:
		device, coordLis, coordStr, time, action, loadBefore, loadAfter = pullDataForGraph(tree, feederMap, outputTimeline, row)

		Dict = {}
		if len(coordLis) == 2:
			Dict['geometry'] = {'type': 'Point', 'coordinates': [coordLis[0], coordLis[1]]}
			Dict['type'] = 'Feature'
			Dict['properties'] = {'device': device, 
								  'time': time,
								  'action': action,
								  'loadBefore': loadBefore,
								  'loadAfter': loadAfter,
								  'pointColor': '#' + str(colormap(time)), 
								  'popupContent': 'Location: <b>' + str(coordStr) + '</b><br>Device: <b>' + str(device) + '</b><br>Time: <b>' + str(time) + '</b><br>Action: <b>' + str(action) + '</b><br>Load Before: <b>' + str(loadBefore) + '</b><br>Load After: <b>' + str(loadAfter) + '</b>.'}
			feederMap['features'].append(Dict)
		else:
			Dict['geometry'] = {'type': 'LineString', 'coordinates': [[coordLis[0], coordLis[1]], [coordLis[2], coordLis[3]]]}
			Dict['type'] = 'Feature'
			Dict['properties'] = {'name': str(tree[key].get('name', '')),
								  'edgeColor': '#' + str(colormap(time)),
								  'popupContent': 'Location: <b>' + str(coordStr) + '</b><br>Device: <b>' + str(device) + '</b><br>Time: <b>' + str(time) + '</b><br>Action: <b>' + str(action) + '</b><br>Load Before: <b>' + str(loadBefore) + '</b><br>Load After: <b>' + str(loadAfter) + '</b>.'}
			feederMap['features'].append(Dict)
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

	return {'timelineStatsHtml': timelineStatsHtml, 'gens': gens, 'loads': loads, 'volts': volts}

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}

	# Write in the feeder
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict['feederName1'] = feederName

	# Output a .dss file, which will be needed for ONM.
	with open(f'{modelDir}/{feederName}.omd', 'r') as omdFile:
		omd = json.load(omdFile)
	tree = omd['tree']
	niceDss = dssConvert.evilGldTreeToDssTree(tree)
	dssConvert.treeToDss(niceDss, f'{modelDir}/circuit.dss')

	# Run the main functions of the program
	with open(pJoin(modelDir, inputDict['microFileName']), 'w') as f:
		pathToData = f.name
		f.write(inputDict['microData'])

	plotOuts = graphMicrogrid(
		modelDir + '/' + feederName + '.omd', #OMD Path
		pathToData,
		modelDir, #Work directory.
		inputDict['maxTime'], #computational time limit
		inputDict['stepSize'], #time step size
		inputDict['faultedLine']) #line faulted
	
	# Textual outputs of cost statistic
	with open(pJoin(modelDir,'timelineStats.html')) as inFile:
		outData['timelineStatsHtml'] = inFile.read()

	#The geojson dictionary to load into the outageCost.py template
	with open(pJoin(modelDir,'geoDict.js'),'rb') as inFile:
		outData['geoDict'] = inFile.read().decode()

	# Plotly outputs.
	layoutOb = go.Layout()
	outData['fig1Data'] = json.dumps(plotOuts.get('gens',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig1Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['fig2Data'] = json.dumps(plotOuts.get('volts',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig2Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['fig3Data'] = json.dumps(plotOuts.get('loads',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig3Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)

	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,'scratch','RONM','microComponents.txt')) as f:
		micro_data = f.read()
	defaultInputs = {
		'modelType': modelName,
		# 'feederName1': 'ieee37nodeFaultTester',
		'feederName1': 'ieee37.dss',
		'maxTime': '20',
		'stepSize': '1',
		'faultedLine': 'l33',
		'microFileName': 'microComponents.txt',
		'microData': micro_data
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

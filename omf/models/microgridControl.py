import random, re, datetime, json, os, tempfile, shutil, csv, math, base64
from os.path import join as pJoin
import subprocess
import pandas as pd
import numpy as np
import scipy
from scipy import spatial
import scipy.stats as st
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
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
		if (nodeName == key['properties'].get('name','')):
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

def customerOutageTable(customerOutageData, outageCost, workDir):
	# check to see if work directory is specified; otherwise, create a temporary directory
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)
	
	# TODO: update table after calculating outage stats
	def customerOutageStats(customerOutageData, outageCost):
		new_html_str = """
			<table cellpadding="0" cellspacing="0">
				<thead>
					<tr>
						<th>Customer Name</th>
						<th>Duration</th>
						<th>Season</th>
						<th>Annual kWh</th>
						<th>Business Type</th>
						<th>Outage Cost</th>
					</tr>
				</thead>
				<tbody>"""
		
		row = 0
		while row < len(customerOutageData):
			new_html_str += '<tr><td>' + str(customerOutageData.loc[row, 'Customer Name']) + '</td><td>' + str(customerOutageData.loc[row, 'Duration']) + '</td><td>' + str(customerOutageData.loc[row, 'Season']) + '</td><td>' + str(customerOutageData.loc[row, 'Annual kWh']) + '</td><td>' + str(customerOutageData.loc[row, 'Business Type']) + '</td><td>' + str(outageCost[row])+ '</td></tr>'
			row += 1

		new_html_str +="""</tbody></table>"""

		return new_html_str

	# print business information and estimated customer outage costs
	customerOutageHtml = customerOutageStats(
		customerOutageData = customerOutageData,
		outageCost = outageCost)
	with open(pJoin(workDir, 'customerOutageTable.html'), 'w') as customerOutageFile:
		customerOutageFile.write(customerOutageHtml)

	return customerOutageHtml

def utilityOutageTable(customerCost, restoration_cost, hardware_cost, outageDuration, workDir):
	# check to see if work directory is specified; otherwise, create a temporary directory
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)
	
	# TODO: update table after calculating outage stats
	def utilityOutageStats(customerCost, restoration_cost, hardware_cost, outageDuration):
		new_html_str = """
			<table cellpadding="0" cellspacing="0">
				<thead>
					<tr>
						<th>Lost kWh Sales</th>
						<th>Restoration Labor Cost</th>
						<th>Restoration Hardware Cost</th>
						<th>Utility Outage Cost</th>
					</tr>
				</thead>
				<tbody>"""
		
		new_html_str += '<tr><td>' + str(int(sum(customerCost))) + '</td><td>' + str(restoration_cost*outageDuration) + '</td><td>' + str(hardware_cost) + '</td><td>' + str(int(sum(customerCost)) + restoration_cost*outageDuration + hardware_cost)+ '</td></tr>'

		new_html_str +="""</tbody></table>"""

		return new_html_str

	# print business information and estimated customer outage costs
	utilityOutageHtml = utilityOutageStats(
		customerCost = customerCost,
		restoration_cost = restoration_cost,
		hardware_cost = hardware_cost,
		outageDuration = outageDuration)
	with open(pJoin(workDir, 'utilityOutageTable.html'), 'w') as utilityOutageFile:
		utilityOutageFile.write(utilityOutageHtml)

	return utilityOutageHtml

def customerCost(workDir, customerName, duration, season, annualkWh, businessType):
	'function to determine customer outage cost based on season, annual kWh usage, and business type'
	duration = int(duration)
	annualkWh = int(annualkWh)

	times = np.array([0,1,2,3,4,5,6,7,8,9,10,11,12])
	# load the customer outage cost data (compared with annual kWh usage) from the 2002 Lawton survey
	kWhTemplate = {}

	# NOTE: We set a maximum kWh value constant so the model doesn't crash for very large annualkWh inputs. However, the
	# model would still likely be very inaccurate for any value above 175000000
	kWhTemplate[5000000000] = np.array([5000000000,5000000000,5000000000,5000000000,5000000000,5000000000,5000000000,5000000000,5000000000,5000000000,5000000000,5000000000,5000000000])
	kWhTemplate[1000000000] = np.array([1000000000,1000000000,1000000000,1000000000,1000000000,1000000000,1000000000,1000000000,1000000000,1000000000,1000000000,1000000000,1000000000])
	kWhTemplate[175000000] = np.array([260000, 325000, 380000, 420000, 430000, 410000, 370000, 310000, 240000, 175000, 120000, 75000, 50000])
	kWhTemplate[17500000] = np.array([5000, 7000, 14000, 21000, 28000, 35000, 42000, 47000, 49000, 47000, 45000, 35000, 28000])
	kWhTemplate[1750000] = np.array([5000, 7000, 13000, 20000, 26000, 34000, 40000, 46000, 48000, 46000, 44000, 34000, 27000])
	kWhTemplate[1182930] = np.array([5000, 7000, 10500, 13750, 17000, 20500, 23500, 26000, 27000, 27000, 26500, 24000, 21000])
	kWhTemplate[118293] = np.array([1000, 1600, 2100, 2450, 2700, 3200, 3500, 4500, 4700, 4600, 4500, 3300, 2900])
	kWhTemplate[11829] = np.array([1000, 1500, 2000, 2250, 2500, 2700, 3000, 3200, 3300, 3200, 3100, 2800, 2600])
	# NOTE: We set a minimum kWh value so the model doesn't crash for low values.
	kWhTemplate[0] = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0])

	def kWhApprox(kWhDict, annualkWh, iterate):
		'helper function for approximating customer outage cost based on annualkWh by iteratively "averaging" the curves'
		step = 0

		# iterate the process a set number of times
		while step < iterate:

			#sort the current kWh values for which we have customer outage costs
			keys = list(kWhDict.keys())
			keys.sort()

			# find the current kWh values estimated that are closest to the annualkWh input...
			# ...then, estimate the outage costs for the kWh value directly between these
			key = 0
			while key < len(keys):
				if annualkWh > keys[key]:			
					key+=1
				else:
					newEntry = (keys[key] + keys[key+1])/2
					averageCost = (kWhDict[keys[key]] + kWhDict[keys[key+1]])/2
					kWhDict[newEntry] = averageCost
					break
			step+=1
			if step == iterate:
				return(kWhDict[newEntry])

	# estimate customer outage cost based on annualkWh
	kWhEstimate = kWhApprox(kWhTemplate, annualkWh, 20)

	# based on the annualkWh usage, import the average relationship between season/business type and outage cost
	# NOTE: This data is also taken from the Lawton survey
	if annualkWh > 1000000:
		winter = np.array([13000, 20000, 32000, 45000, 63000, 79000, 95000, 105000, 108000, 104000, 95000, 80000, 64000])
		summer = np.array([7000, 10000, 14000, 19000, 26000, 34000, 39000, 42000, 43000, 42000, 39000, 34000, 26000])
		manufacturing = np.array([9000, 12000, 19000, 26000, 38000, 48000, 59000, 67000, 69000, 68000, 65000, 56000, 46000])
		construction = np.array([10000, 18000, 27000, 40000, 56000, 72000, 86000, 98000, 102000, 101000, 96000, 82000, 68000])
		finance = np.array([8000, 10000, 17000, 22000, 31000, 40000, 48000, 55000, 58000, 57000, 54000, 45000, 38000])
		public = np.array([6000, 9000, 15000, 17000, 22000, 29000, 35000, 39000, 41000, 41000, 38000, 32000, 27000])
		retail = np.array([6000, 9000, 15000, 17000, 22000, 29000, 35000, 39000, 41000, 41000, 38000, 32000, 27000])
		utilities = np.array([6000, 9000, 14000, 16000, 19000, 23000, 29000, 33000, 35000, 34000, 32000, 26000, 22000])
		services = np.array([5000, 7000, 8000, 10000, 16000, 19000, 22000, 25000, 26000, 25000, 23000, 21000, 18000])

	elif businessType != 'residential':
		winter = np.array([1200, 1800, 2500, 3200, 4100, 4900, 5600, 6200, 6400, 6400, 6200, 5700, 5000])
		summer = np.array([900, 1300, 1700, 2200, 2800, 3300, 3800, 4200, 4400, 4400, 4200, 3900, 3400])
		manufacturing = np.array([1200, 1900, 2600, 3500, 4600, 5700, 6600, 7400, 7800, 7900, 7700, 7100, 6200])
		construction = np.array([900, 1300, 1800, 2500, 3250, 4000, 4600, 5200, 5500, 5600, 5400, 5000, 4400])
		finance = np.array([600, 750, 1150, 1500, 2000, 2400, 2800, 3200, 3350, 3400, 3300, 3100, 2650])
		retail = np.array([600, 700, 1000, 1400, 1700, 2200, 2600, 2850, 3050, 3100, 3000, 2750, 2400])
		services = np.array([500, 600, 800, 1150, 1400, 1750, 2100, 2350, 2400, 2450, 2350, 2200, 1950])
		utilities = np.array([500, 550, 750, 1000, 1300, 1600, 1800, 2050, 2150, 2150, 2100, 1950, 1750])
		public = np.array([350, 500, 600, 800, 1050, 1250, 1500, 1600, 1750, 1750, 1700, 1600, 1400])
	
	# NOTE: if the customer is residential, there is no business type relationship
	else:
		winter = np.array([3, 3, 4, 5, 6, 7, 8, 9, 10, 10, 11, 11, 12])
		summer = np.array([2, 3, 4, 4, 5, 6, 7, 8, 9, 9, 10, 10, 10])

	# adjust the estimated customer outage cost by the difference between the average outage cost and the average seasonal cost
	averageSeason = np.sum((winter + summer)/2)/13
	averageSummer = np.sum(summer)/13
	averageWinter = np.sum(winter)/13
	if season == 'summer':
		seasonMultiplier = averageSummer/averageSeason
	else:
		seasonMultiplier = averageWinter/averageSeason
	kWhEstimate = kWhEstimate * seasonMultiplier

	# adjust the estimated customer outage cost by the difference between the average outage cost and the average business type cost
	if businessType != 'residential':
		averageBusiness = np.sum((manufacturing + construction + finance + retail + services + utilities + public)/7)/13
		if businessType == 'manufacturing':
			averageManufacturing = np.sum(manufacturing)/13
			businessMultiplier = averageManufacturing/averageBusiness
		elif businessType == 'construction':
			averageConstruction = np.sum(construction)/13
			businessMultiplier = averageConstruction/averageBusiness
		elif businessType == 'finance':
			averageFinance = np.sum(finance)/13
			businessMultiplier = averageFinance/averageBusiness
		elif businessType == 'retail':
			averageRetail = np.sum(retail)/13
			businessMultiplier = averageRetail/averageBusiness
		elif businessType == 'services':
			averageServices = np.sum(services)/13
			businessMultiplier = averageServices/averageBusiness
		elif businessType == 'utilities':
			averageUtilities = np.sum(utilities)/13
			businessMultiplier = averageUtilities/averageBusiness
		else:
			averagePublic = np.sum(public)/13
			businessMultiplier = averagePublic/averageBusiness
		kWhEstimate = kWhEstimate * businessMultiplier

	# adjust for inflation from 2002 to 2020 using the CPI
	kWhEstimate = 1.445 * kWhEstimate

	# find the estimated customer outage cost for the customer in question, given the duration of the outage
	times = np.array([0,1,2,3,4,5,6,7,8,9,10,11,12])
	outageCost = kWhEstimate[duration]
	localMax = 0
	row = 0
	while row < 13:
		if kWhEstimate[row] > localMax:
			localMax = kWhEstimate[row]
		row+=1
	
	# plot the expected customer outage cost over the duration of the outage
	# plt.plot(times, kWhEstimate)
	# plt.savefig(workDir + '/customerCostFig')
	# return {'customerOutageCost': outageCost}
	return outageCost, kWhEstimate, times, localMax

def graphMicrogrid(pathToOmd, pathToMicro, pathToCsv, workDir, maxTime, stepSize, faultedLine, timeMinFilter, timeMaxFilter, actionFilter, outageDuration, restoration_cost, hardware_cost, sameFeeder):
	# read in the OMD file as a tree and create a geojson map of the system
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)

	# command = 'cmd /c ' + '"julia --project=' + '"C:/Users/granb/PowerModelsONM.jl-master/" ' + 'C:/Users/granb/PowerModelsONM.jl-master/src/cli/entrypoint.jl' + ' -n ' + '"' + str(workDir) + '/circuit.dss' + '"' + ' -o ' + '"C:/Users/granb/PowerModelsONM.jl-master/output.json"'
	
	if os.path.exists(f'{workDir}/output.json') and sameFeeder:
		with open(f'{workDir}/output.json') as inFile:
			data = json.load(inFile)
			genProfiles = data['Generator profiles']
			simTimeSteps = []
			for i in data['Simulation time steps']:
				simTimeSteps.append(float(i))
			voltages = data['Voltages']
			loadServed = data['Load served']
			storageSOC = data['Storage SOC (%)']
			cached = 'yes'

	else:
		setup_command = f'julia --project="{__neoMetaModel__._omfDir}/solvers/PowerModelsONM.jl" -e "using Pkg; Pkg.update()"'
		os.system(setup_command)

		command = f'julia --project="{__neoMetaModel__._omfDir}/solvers/PowerModelsONM.jl" "{__neoMetaModel__._omfDir}/solvers/PowerModelsONM.jl/src/cli/entrypoint.jl" -n "{workDir}/circuit.dss" -o "{workDir}/onm_output.json"'
		os.system(command)

		with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','output.json')) as inFile:
		# with open(f'{workDir}/onm_output.json') as inFile:
			data = json.load(inFile)
			with open(f'{workDir}/output.json', 'w') as outfile:
				json.dump(data, outfile)
			genProfiles = data['Generator profiles']
			simTimeSteps = []
			for i in data['Simulation time steps']:
				simTimeSteps.append(float(i))
			voltages = data['Voltages']
			loadServed = data['Load served']
			storageSOC = data['Storage SOC (%)']
			cached = 'no'
	
	outputTimeline = createTimeline()

	# Create traces
	gens = go.Figure()
	gens.add_trace(go.Scatter(x=simTimeSteps, y=genProfiles['Diesel DG (kW)'],
							mode='lines',
							name=cached))
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
	Dict['geometry'] = {'type': 'LineString', 'coordinates': [faultedNodeCoordLis2, faultedNodeCoordLis1]}
	Dict['type'] = 'Feature'
	Dict['properties'] = {'name': faultedLine,
						  'edgeColor': 'red',
						  'popupContent': 'Location: <b>' + str(faultedNodeCoordStr1) + ', ' + str(faultedNodeCoordStr2) + '</b><br>Faulted Line: <b>' + str(faultedLine)}
	feederMap['features'].append(Dict)

	timeMin = int(timeMinFilter)
	timeMax = int(timeMaxFilter)

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
								  'timeMin': timeMin, 
								  'timeMax': timeMax,
								  'actionFilter': actionFilter,
								  'pointColor': '#' + str(colormap(time)), 
								  'popupContent': 'Location: <b>' + str(coordStr) + '</b><br>Device: <b>' + str(device) + '</b><br>Time: <b>' + str(time) + '</b><br>Action: <b>' + str(action) + '</b><br>Load Before: <b>' + str(loadBefore) + '</b><br>Load After: <b>' + str(loadAfter) + '</b>.'}
			feederMap['features'].append(Dict)
		else:
			Dict['geometry'] = {'type': 'LineString', 'coordinates': [[coordLis[0], coordLis[1]], [coordLis[2], coordLis[3]]]}
			Dict['type'] = 'Feature'
			Dict['properties'] = {'device': device, 
								  'time': time,
								  'action': action,
								  'loadBefore': loadBefore,
								  'loadAfter': loadAfter,
								  'timeMin': timeMin, 
								  'timeMax': timeMax,
								  'actionFilter': actionFilter,
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

	customerOutageData = pd.read_csv(pathToCsv)
	numberRows = math.ceil(customerOutageData.shape[0]/2)
	fig, axs = plt.subplots(numberRows, 2)
	row = 0
	outageCost = []
	globalMax = 0
	while row < customerOutageData.shape[0]:
		customerName = str(customerOutageData.loc[row, 'Customer Name'])
		duration = str(customerOutageData.loc[row, 'Duration'])
		season = str(customerOutageData.loc[row, 'Season'])
		annualkWh = str(customerOutageData.loc[row, 'Annual kWh'])
		businessType = str(customerOutageData.loc[row, 'Business Type'])

		customerOutageCost, kWhEstimate, times, localMax = customerCost(workDir, customerName, duration, season, annualkWh, businessType)
		outageCost.append(customerOutageCost)
		if localMax > globalMax:
			globalMax = localMax
		print(customerName)
		print(customerOutageCost)
		print(numberRows)
		print(math.floor(row/2))
		print(row%2)
		if numberRows > 1:
			axs[math.floor(row/2), row%2].plot(times, kWhEstimate)
			axs[math.floor(row/2), row%2].set_title(str(customerName))
		else:
			axs[row%2].plot(times, kWhEstimate)
			axs[row%2].set_title(str(customerName))
		row+=1
	for ax in axs.flat:
		ax.set(xlabel='Duration (hrs)', ylabel='Customer Outage Cost')
		ax.set_xlim([0, 12])
		ax.set_ylim([0, globalMax + .05*globalMax])
	for ax in axs.flat:
		ax.label_outer()
	plt.savefig(workDir + '/customerCostFig')

	customerOutageHtml = customerOutageTable(customerOutageData, outageCost, workDir)

	restoration_cost = int(restoration_cost)
	hardware_cost = int(hardware_cost)
	outageDuration = int(outageDuration)

	utilityOutageHtml = utilityOutageTable(outageCost, restoration_cost, hardware_cost, outageDuration, workDir)

	return {'utilityOutageHtml': utilityOutageHtml, 'customerOutageHtml': customerOutageHtml, 'timelineStatsHtml': timelineStatsHtml, 'gens': gens, 'loads': loads, 'volts': volts, 'customerOutageCost': customerOutageCost}

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}

	# Write in the feeder
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict['feederName1'] = feederName
	with open(f'{modelDir}/{feederName}.omd', 'r') as omdFile:
		omd = json.load(omdFile)
	sameFeeder = False

	
	if os.path.exists(f'{modelDir}/feeder.json'):
		sameFeeder = open(f'{modelDir}/feeder.json').read() == omd		

	if not sameFeeder:
		with open(f'{modelDir}/feeder.json', 'wt') as feederFile:
			with open(f'{modelDir}/{feederName}.omd', 'r') as omdFile:
				json.dump(json.load(omdFile), feederFile)


	tree = omd['tree']
	# Output a .dss file, which will be needed for ONM.
	# niceDss = dssConvert.evilGldTreeToDssTree(tree)
	# dssConvert.treeToDss(niceDss, f'{modelDir}/circuit.dss')

	# Run the main functions of the program
	with open(pJoin(modelDir, inputDict['microFileName']), 'w') as f:
		pathToData = f.name
		f.write(inputDict['microData'])
	with open(pJoin(modelDir, inputDict['customerFileName']), 'w') as f1:
		pathToData1 = f1.name
		f1.write(inputDict['customerData'])

	plotOuts = graphMicrogrid(
		modelDir + '/' + feederName + '.omd', #OMD Path
		pathToData,
		pathToData1,
		modelDir, #Work directory.
		inputDict['maxTime'], #computational time limit
		inputDict['stepSize'], #time step size
		inputDict['faultedLine'],#line faulted
		inputDict['timeMinFilter'],
		inputDict['timeMaxFilter'],
		inputDict['actionFilter'],
		inputDict['outageDuration'],
		inputDict['restoration_cost'],
		inputDict['hardware_cost'],
		sameFeeder)
	
	# Textual outputs of outage timeline
	with open(pJoin(modelDir,'timelineStats.html')) as inFile:
		outData['timelineStatsHtml'] = inFile.read()

	# Textual outputs of customer cost statistic
	with open(pJoin(modelDir,'customerOutageTable.html')) as inFile:
		outData['customerOutageHtml'] = inFile.read()

	# Textual outputs of utility cost statistic
	with open(pJoin(modelDir,'utilityOutageTable.html')) as inFile:
		outData['utilityOutageHtml'] = inFile.read()

	#The geojson dictionary to load into the outageCost.py template
	with open(pJoin(modelDir,'geoDict.js'),'rb') as inFile:
		outData['geoDict'] = inFile.read().decode()

	# Image outputs.
	with open(pJoin(modelDir,'customerCostFig.png'),'rb') as inFile:
		outData['customerCostFig.png'] = base64.standard_b64encode(inFile.read()).decode()

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
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','microComponents.json')) as f:
		micro_data = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','customerInfo.csv')) as f1:
		customer_data = f1.read()
	defaultInputs = {
		'modelType': modelName,
		# 'feederName1': 'ieee37nodeFaultTester',
		'feederName1': 'ieee37.dss',
		# 'feederName1': 'ieee240.dss',
		'maxTime': '20',
		'stepSize': '1',
		'faultedLine': 'l32',
		'timeMinFilter': '10',
		'timeMaxFilter': '20',
		'actionFilter': 'All',
		'outageDuration': '5', 
		'restoration_cost': '1000',
		'hardware_cost': '5500',
		'microFileName': 'microComponents.json',
		'microData': micro_data,
		'customerData': customer_data,
		'customerFileName': 'customerInfo.csv'
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	print(creationCode)
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
	with open(f'{modelLoc}/allInputData.json') as file:
		print(json.load(file))
	# Pre-run.
	# renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

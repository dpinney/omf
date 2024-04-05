''' Calculate optimal restoration scheme for distribution system with multiple microgrids. '''
import re, json, os, shutil, csv, math, io
from os.path import join as pJoin
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly as py
import plotly.graph_objs as go
import networkx as nx
# from statistics import quantiles

# OMF imports
import omf
from omf import geo
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.solvers.opendss import dssConvert
from omf.solvers import PowerModelsONM
from omf.comms import createGraph

# Model metadata:
tooltip = 'Calculate load, generator and switching controls to maximize power restoration for a circuit with multiple networked microgrids.'
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def makeCicuitTraversalDict(pathToOmd):
	''' Note: comment out line 99 in comms.py: "nxG = graphValidator(pathToOmdFile, nxG)" as a quick fix for the purpose of this funct
	
		Returns a dictionary of circuit objects and their properties from a given omd file
		with a set of downline loads and a set of downline objects (including loads) 
		added to their properties with the keys 'downlineLoads' and 'downlineObs'.
		
		The specific return format is a dictionary with keys representing circuit objects
		in the format of 'obType.obName' (e.g. load.load_2060) which correspond to values that are 
		dictionaries of circuit object properties such as:
		'name':'load_2060', 'object':'load', 'downlineLoads':{load.load_1002, load.load_1003, ...}, 'downlineObs':{...}, etc.
		'''	
	# TODO: remove first line in docstring once graphValidator is cleaned up
	with open(pathToOmd) as inFile:
		omd = json.load(inFile)
	obDict = {}
	for ob in omd.get('tree',{}).values():
		obType = ob['object']
		obName = ob['name']
		key = f'{obType}.{obName}'
		obDict[key] = ob

	digraph = createGraph(pathToOmd)
	nodes = digraph.nodes()
	namesToKeys = {v.get('name'):k for k,v in obDict.items()}
	for obKey, ob in obDict.items():
		obType = ob['object']
		obName = ob['name']
		obTo = ob.get('to')
		if obName in nodes:
			startingPoint = obName
		elif obTo in nodes:
			startingPoint = obTo
		else:
			continue 
		descendants = nx.descendants(digraph, startingPoint)
		ob['downlineObs'] = set()
		ob['downlineLoads'] = set()
		for circOb in descendants:
			circObKey = namesToKeys.get(circOb)
			circObType = circObKey.split('.')[0]
			ob['downlineObs'].add(circObKey)
			if circObType == 'load':
				ob['downlineLoads'].add(circObKey)
	return obDict

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
	coordLis = []
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
		try:
			if tree[key].get('name','') == lineName:
				lineNode = tree[key]['from']
				# print(lineNode)
				lineNode2 = tree[key]['to']
				# print(lineNode2)
				coordLis1, coordStr1 = nodeToCoords(feederMap, lineNode)
				# print(coordLis1)
				coordLis2, coordStr2 = nodeToCoords(feederMap, lineNode2)
				coordLis = []
				coordLis.append(coordLis1[0])
				coordLis.append(coordLis1[1])
				coordLis.append(coordLis2[0])
				coordLis.append(coordLis2[1])
				coordStr = str(coordLis[0]) + ' ' + str(coordLis[1]) + ' ' + str(coordLis[2]) + ' ' + str(coordLis[3])
		except:
			print('BAD COORDS for', tree[key])
	return coordLis, coordStr

def pullDataForGraph(tree, feederMap, outputTimeline, row):
	'get necessary data to build the activity graph'
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

def microgridTimeline(outputTimeline, modelDir):
	'generate timeline of microgrid events'
	# TODO: update table after calculating outage stats
	def timelineStats(outputTimeline):
		new_html_str = """
			<table class="sortable" cellpadding="0" cellspacing="0">
				<thead>
					<tr>
						<th>Device</th>
						<th>Time</th>
						<th>Action</th>
						<th>Before</th>
						<th>After</th>
					</tr>
				</thead>
				<tbody>"""
		row = 0
		while row < len(outputTimeline):
			loadBeforeStr = outputTimeline.loc[row, 'loadBefore']
			loadAfterStr = outputTimeline.loc[row, 'loadAfter']
			loadStringDict = ["open", "closed", "online", "offline"]
			if str(loadBeforeStr) not in loadStringDict:
				loadBeforeStr = '{0:.3f}'.format(float(loadBeforeStr))
			if str(loadAfterStr) not in loadStringDict:
				loadAfterStr = '{0:.3f}'.format(float(loadAfterStr))
			new_html_str += '<tr><td>' + str(outputTimeline.loc[row, 'device']) + '</td><td>' + str(outputTimeline.loc[row, 'time']) + '</td><td>' + str(outputTimeline.loc[row, 'action']) + '</td><td>' + loadBeforeStr + '</td><td>' + loadAfterStr + '</td></tr>'
			row += 1
		new_html_str +="""</tbody></table>"""
		return new_html_str
	# print all intermediate and final costs
	timelineStatsHtml = timelineStats(
		outputTimeline = outputTimeline)
	with open(pJoin(modelDir, 'timelineStats.html'), 'w') as timelineFile:
		timelineFile.write(timelineStatsHtml)
	return timelineStatsHtml

def customerOutageTable(customerOutageData, outageCost, modelDir):
	'generate html table of customer outages'
	# TODO: update table after calculating outage stats
	def customerOutageStats(customerOutageData, outageCost):
		new_html_str = """
			<table cellpadding="0" cellspacing="0">
				<thead>
					<tr>
						<th>Customer Name</th>
						<th>Duration</th>
						<th>Season</th>
						<th>Average kW/hr</th>
						<th>Business Type</th>
						<th>Load Name</th>
						<th>Outage Cost</th>
					</tr>
				</thead>
				<tbody>"""
		row = 0
		while row < len(customerOutageData):
			new_html_str += '<tr><td>' + str(customerOutageData.loc[row, 'Customer Name']) + '</td><td>' + str(customerOutageData.loc[row, 'Duration']) + '</td><td>' + str(customerOutageData.loc[row, 'Season']) + '</td><td>' + '{0:.2f}'.format(customerOutageData.loc[row, 'Average kW/hr']) + '</td><td>' + str(customerOutageData.loc[row, 'Business Type']) + '</td><td>' + str(customerOutageData.loc[row, 'Load Name']) + '</td><td>' + "${:,.2f}".format(outageCost[row])+ '</td></tr>'
			row += 1
		new_html_str +="""</tbody></table>"""
		return new_html_str

	# print business information and estimated customer outage costs
	try:
		customerOutageHtml = customerOutageStats(
			customerOutageData = customerOutageData,
			outageCost = outageCost)
	except:
		customerOutageHtml = ''
		 #HACKCOBB: work aroun.
	with open(pJoin(modelDir, 'customerOutageTable.html'), 'w') as customerOutageFile:
		customerOutageFile.write(customerOutageHtml)
	return customerOutageHtml

def utilityOutageTable(average_lost_kwh, profit_on_energy_sales, restoration_cost, hardware_cost, outageDuration, modelDir):
	# TODO: update table after calculating outage stats
	def utilityOutageStats(average_lost_kwh, profit_on_energy_sales, restoration_cost, hardware_cost, outageDuration):
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
		
		new_html_str += '<tr><td>' + str(int(sum(average_lost_kwh))*profit_on_energy_sales*outageDuration) + '</td><td>' + "${:,.2f}".format(restoration_cost*outageDuration) + '</td><td>' + "${:,.2f}".format(hardware_cost) + '</td><td>' + "${:,.2f}".format(int(sum(average_lost_kwh))*profit_on_energy_sales*outageDuration + restoration_cost*outageDuration + hardware_cost) + '</td></tr>'

		new_html_str +="""</tbody></table>"""

		return new_html_str

	# print business information and estimated customer outage costs
	utilityOutageHtml = utilityOutageStats(
		average_lost_kwh = average_lost_kwh,
		profit_on_energy_sales = profit_on_energy_sales,
		restoration_cost = restoration_cost,
		hardware_cost = hardware_cost,
		outageDuration = outageDuration)
	with open(pJoin(modelDir, 'utilityOutageTable.html'), 'w') as utilityOutageFile:
		utilityOutageFile.write(utilityOutageHtml)
	return utilityOutageHtml

def customerCost1(duration, season, averagekWperhr, businessType):
	'function to determine customer outage cost based on season, annual kWh usage, and business type'
	duration = float(duration)
	averagekW = float(averagekWperhr)

	times = np.array([0,1,2,3,4,5,6,7,8])
	# load the customer outage cost data (compared with average kW/hr usage) from the 2009 survey
	kWTemplate = {}

	# NOTE: We set a maximum average kW/hr set of values so the model doesn't crash for very large averagekWperhr inputs. However, the
	# model would still likely be very inaccurate for any value above 2500
	
	if businessType != 'residential':
		kWTemplate[5000.0] = np.array([50000,70000,120000,16000,200000,260000,300000,320000,350000,378072,410955,445306,483282,524087,568559,616684,668947,725604,787078,853750,926075,1004524,1089620,1181923,1282046,1390650])
		kWTemplate[2500.0] = np.array([20000,35000,58000,75000,95000,117000,133000,142000,145000,151437,156398,162431,168224,174468,180817,187462,194317,201440,208815,216464,224391,232609,241127,249957,259110,268598])
		kWTemplate[500.0] = np.array([10000,18000,23000,38000,48000,60000,68000,77000,78000,83668,87251,92289,96929,102164,107491,113196,119151,125447,132061,139031,146365,154087,162215,170772,179780,189263])
		kWTemplate[100.0] = np.array([4000,7000,13000,19000,23000,31000,37000,40000,41000,43174,44858,46922,48916,51080,53295,55629,58053,60588,63230,65989,68867,71871,75005,78276,81689,85251])
		kWTemplate[20.0] = np.array([1500,4000,6000,10000,14000,18000,19500,20500,21000,21794,22471,23244,24004,24809,25630,26483,27361,28269,29206,30174,31174,32207,33274,34376,35514,36689])
		kWTemplate[5.0] = np.array([500,900,1400,2050,2800,3600,4200,4850,5300,5955,6599,7363,8187,9119,10148,11298,12575,13998,15581,17343,19304,21486,23915,26618,29626,32974])
		kWTemplate[3.0] = np.array([500,900,1400,2050,2700,3500,3900,4600,5000,5666,6289,7053,7869,8802,9832,10990,12280,13723,15334,17134,19145,21392,23902,26706,29839,33339])
		kWTemplate[1.0] = np.array([400,750,1200,1900,2600,3200,3600,4000,4100,4379,4582,4844,5094,5371,5655,5958,6275,6610,6962,7333,7723,8134,8566,9021,9500,10004])
		kWTemplate[0.25] = np.array([350,700,1100,1700,2400,3000,3300,3500,3600,3760,3897,4054,4209,4374,4543,4719,4901,5090,5286,5489,5700,5919,6146,6381,6625,6878])
	
	else:
		kWTemplate[100.0] = np.array([4,6,7,9,12,14,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33])
		kWTemplate[8.0] = np.array([4,6,7,9,12,14,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33])
		kWTemplate[4.0] = np.array([3,5,6,8,9,11,12,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13,13])
		kWTemplate[2.5] = np.array([3,4,6,7,8,10,11,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12])
		kWTemplate[1.0] = np.array([3,4,5,6,7,8,9,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10,10])
		kWTemplate[0.25] = np.array([2,3,4,5,5,6,7,7,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8,8])
	# NOTE: We set a minimum average kWperhr value so the model doesn't crash for low values.
	kWTemplate[0] = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])

	def kWhApprox(kWDict, averagekWperhr, iterate):
		'helper function for approximating customer outage cost based on annual kWh by iteratively "averaging" the curves'
		step = 0
		# iterate the process a set number of times
		while step < iterate:
			#sort the current kWh values for which we have customer outage costs
			keys = list(kWDict.keys())
			keys.sort()
			# find the current kWh values estimated that are closest to the average kW/hr input...
			# ...then, estimate the outage costs for the kW/hr value directly between these
			key = 0
			newEntry = 0
			while key < len(keys)-1:
				if key == len(keys)-2:
					newEntry = (keys[key] + keys[key+1])/2
					averageCost = (kWDict[keys[key]] + kWDict[keys[key+1]])/2
					kWDict[newEntry] = averageCost
					break
				if float(averagekWperhr) > keys[key+1]:
					key+=1
				else:
					newEntry = (keys[key] + keys[key+1])/2
					averageCost = (kWDict[keys[key]] + kWDict[keys[key+1]])/2
					kWDict[newEntry] = averageCost
					break
			step+=1
			if step == iterate:
				return(kWDict[newEntry])

	# estimate customer outage cost based on annualkWh
	kWperhrEstimate = kWhApprox(kWTemplate, averagekWperhr, 20)

	# based on the annualkWh usage, import the average relationship between season/business type and outage cost
	# NOTE: This data is also taken from the Lawton survey
	if float(averagekWperhr) > 10:
		winter = np.array([10000, 19000, 27000, 41000, 59000, 72000, 83000, 91000, 93000])
		summer = np.array([11000, 20000, 31000, 43000, 60000, 73000, 84000, 92000, 94500])
		manufacturing = np.array([25000, 35000, 54000, 77000, 106000, 127000, 147000, 161000, 165000])
		construction = np.array([27000, 49000, 73000, 102000, 135000, 167000, 190000, 215000, 225000])
		finance = np.array([24000, 32000, 49000, 70000, 90000, 115000, 130000, 144000, 148000])
		public = np.array([7000, 17000, 26000, 40000, 50000, 65000, 75000, 77000, 80000])
		retail = np.array([6000, 14000, 23000, 35000, 40000, 47000, 52000, 55000, 57000])
		utilities = np.array([10000, 20000, 30000, 45000, 65000, 76000, 85000, 93000, 96000])
		mining = np.array([6000, 15000, 24000, 38000, 47000, 54000, 65000, 70000, 72000])
		services = np.array([6000, 15000, 24000, 38000, 47000, 54000, 65000, 70000, 72000])
		agriculture = np.array([5000, 10000, 17000, 22000, 26000, 30000, 37000, 40000, 42000])

	elif businessType != 'residential':
		winter = np.array([600, 1100, 2000, 3000, 4150, 5400, 6500, 7300, 7800])
		summer = np.array([550, 900, 1350, 2000, 2800, 3450, 4000, 4550, 4800])
		manufacturing = np.array([850, 1100, 1900, 2600, 3600, 4500, 5400, 6000, 6300])
		mining = np.array([1000, 1800, 2750, 4000, 5600, 6800, 8000, 8900, 9300])
		construction = np.array([1100, 1900, 3000, 4300, 5900, 7400, 8600, 9500, 10100])
		agriculture = np.array([500, 650, 1300, 1800, 2400, 3300, 4000, 4600, 4800])
		finance = np.array([850, 1100, 1900, 2600, 3600, 4500, 5400, 6000, 6300])
		retail = np.array([500, 650, 1300, 1800, 2300, 3000, 3500, 3900, 4100])
		services = np.array([500, 600, 900, 1500, 2100, 2600, 3000, 3500, 3700])
		utilities = np.array([850, 1100, 1900, 2600, 3600, 4500, 5400, 6000, 6300])
		public = np.array([400, 500, 800, 1200, 1800, 2200, 2600, 3100, 3300])
	
	# NOTE: if the customer is residential, there is no business type relationship
	else:
		summer = np.array([4, 5, 7, 8, 10, 11, 12, 13, 14])
		winter = np.array([3, 4, 5, 6, 8, 9, 10, 11, 11])

	# adjust the estimated customer outage cost by the difference between the average outage cost and the average seasonal cost
	averageSeason = np.sum((winter + summer)/2)/9
	averageSummer = np.sum(summer)/9
	averageWinter = np.sum(winter)/9
	if season == 'summer':
		seasonMultiplier = averageSummer/averageSeason
	else:
		seasonMultiplier = averageWinter/averageSeason
	kWperhrEstimate = kWperhrEstimate * seasonMultiplier

	# adjust the estimated customer outage cost by the difference between the average outage cost and the average business type cost
	if businessType != 'residential':
		averageBusiness = np.sum((manufacturing + construction + finance + retail + services + utilities + public + mining + agriculture)/9)/9
		if businessType == 'manufacturing':
			averageManufacturing = np.sum(manufacturing)/9
			businessMultiplier = averageManufacturing/averageBusiness
		elif businessType == 'construction':
			averageConstruction = np.sum(construction)/9
			businessMultiplier = averageConstruction/averageBusiness
		elif businessType == 'finance':
			averageFinance = np.sum(finance)/9
			businessMultiplier = averageFinance/averageBusiness
		elif businessType == 'retail':
			averageRetail = np.sum(retail)/9
			businessMultiplier = averageRetail/averageBusiness
		elif businessType == 'services':
			averageServices = np.sum(services)/9
			businessMultiplier = averageServices/averageBusiness
		elif businessType == 'utilities':
			averageUtilities = np.sum(utilities)/9
			businessMultiplier = averageUtilities/averageBusiness
		elif businessType == 'agriculture':
			averageAgriculture = np.sum(agriculture)/9
			businessMultiplier = averageAgriculture/averageBusiness
		elif businessType == 'mining':
			averageMining = np.sum(mining)/9
			businessMultiplier = averageMining/averageBusiness
		else:
			averagePublic = np.sum(public)/9
			businessMultiplier = averagePublic/averageBusiness
		kWperhrEstimate = kWperhrEstimate * businessMultiplier

	# adjust for inflation from 2008 to 2020 using the CPI
	kWperhrEstimate = 1.21 * kWperhrEstimate
	# find the estimated customer outage cost for the customer in question, given the duration of the outage
	times = np.array([0,1,2,3,4,5,6,7,8])
	wholeHours = int(math.floor(duration))
	partialHour = duration - wholeHours
	outageCost = (kWperhrEstimate[wholeHours] + (kWperhrEstimate[wholeHours+1] - kWperhrEstimate[wholeHours])*partialHour) * (duration>0)
	localMax = 0
	row = 0
	while row < 9:
		if kWperhrEstimate[row] > localMax:
			localMax = kWperhrEstimate[row]
		row+=1
	return outageCost, kWperhrEstimate, times, localMax

def outageIncidenceGraph(customerOutageData, outputTimeline, startTime, numTimeSteps, loadPriorityFilePath, loadMgDict):
	'''	Returns plotly figures displaying graphs of outage incidences over the course of the event data.
		Unweighted outage incidence at each timestep is calculated as (num loads experiencing outage)/(num loads).
		A load is considered to be "experiencing an outage" at a particular timestep if its "loadBefore" value 
		in outputTimeline is "offline". The last x-value on the graph is the exception, with its value corresponding
		to the "loadAfter" values on the same timestep as the x-value.
		E.g. loadBefore 0, loadBefore 1, ... , loadBefore 23, loadAfter 23

		Weighted outage incidence is calculated similarly, but with loads being weighted in the calculation based
		on their priority given in the Load Priorities JSON file that can be provided as input to the model.
		If a load does not have a priority assigned to it, it is assigned a default priority of 1. 
	'''
	# TODO: Rename function

	loadList = list(loadMgDict.keys())
	mgIDs = set(loadMgDict.values())
	timeList = [*range(startTime, numTimeSteps+1)] # The +1 is because we want the 'before' for each timestep + the 'after' for the last timestep

	# Create a copy of outputTimeline containing only load devices sorted by device name and then time. 
	dfLoadTimeln = outputTimeline.copy(deep=True)
	dfLoadTimeln = dfLoadTimeln[dfLoadTimeln['device'].str.contains('load')]
	dfLoadTimeln['time'] = dfLoadTimeln['time'].astype(int)
	dfLoadTimeln = dfLoadTimeln.sort_values(by=['device','time'])
	
	# Create dataframe of load status before each timestep and after the last timestep
	dfStatus = pd.DataFrame(np.ones((len(timeList),len(loadList))), dtype=int, index=timeList, columns=loadList)
	statusMapping = {'offline':0, 'online':1}
	for loadName in loadList:
		# Create a copy of dfLoadTimeln containing only a single load device, with rows indexed by time
		dfSoloLoadTimeln = dfLoadTimeln[dfLoadTimeln['device'] == loadName].set_index('time')
		# Track reaching timesteps recorded in dfSoloLoadTimeln
		lastRecTimeStep = 0
		recTimeStepReached = False
		#lastRecTimestep and recTimeStepReached are separate variables instead of lastRecTimeStep starting = -1 and testing for that so that the function still works with strange starting times like -1
		for timeStep in timeList:
			if timeStep in dfSoloLoadTimeln.index:
				dfStatus.at[timeStep,loadName] = statusMapping.get(dfSoloLoadTimeln.at[timeStep,'loadBefore'])
				lastRecTimeStep = timeStep
				recTimeStepReached = True
			elif recTimeStepReached and not dfSoloLoadTimeln.empty:
				dfStatus.at[timeStep,loadName] = statusMapping.get(dfSoloLoadTimeln.at[lastRecTimeStep,'loadAfter'])
			else:
				dfStatus.at[timeStep,loadName] = statusMapping.get('online')
	
	# Calculate unweighted outage incidence
	outageIncidence = dfStatus.sum(axis=1,).map(lambda x:100*(1.0-(x/dfStatus.shape[1]))).round(3).values.tolist()

	#Calculate weighted outage incidence based on 'Business Type'
	includeGroupWeights = False
	if includeGroupWeights:
		typeWeights = {'residential': 64, 'retail':32, 'agriculture':16, 'public':8, 'services':4, 'manufacturing':2}
		leftoverCustomers = set(loadList)
		Sum_wc_nc = np.zeros(len(outageIncidence))
		Sum_wc_Nc = 0
		for customerType in typeWeights.keys():
			customersOfType = customerOutageData[customerOutageData['Business Type'].str.contains(customerType)]['Customer Name'].values.tolist()
			dfStatusOfType = dfStatus[customersOfType]
			Nc = dfStatusOfType.shape[1]
			Sum_wc_Nc += typeWeights[customerType]*Nc
			nc = dfStatusOfType.sum(axis=1,).map(lambda x: Nc-x).to_numpy()
			Sum_wc_nc = np.add(Sum_wc_nc,typeWeights[customerType]*nc) 
			leftoverCustomers = leftoverCustomers - set(customersOfType)
		dfStatusOfLeftovers = dfStatus[list(leftoverCustomers)]
		Nc = dfStatusOfLeftovers.shape[1]
		Sum_wc_Nc += 1*Nc
		nc = dfStatusOfLeftovers.sum(axis=1,).map(lambda x: Nc-x).to_numpy()
		Sum_wc_nc = np.add(Sum_wc_nc,1*nc) 
		weightedOutageIncidence = np.around((100*Sum_wc_nc/Sum_wc_Nc), 3).tolist()
	###################################################################################################################################################################
	# TODO: Clean this up to make it more readable. For now though, functionality is the focus.
	###################################################################################################################################################################

	def calcWeightedOI(loadWeights):
		''' Individually weighted outage incidence calculated as
			
			(Sum from i=1 to N of w_i*n_i)/(Sum from i=1 to N of w_i)

			N = number of loads total,
			
			ni = (1-status) of load i,
			
			wi = weight of load i 
		'''
		Sum_wi_ni = np.zeros(len(outageIncidence)) #one entry for each timestep
		Sum_wi = 0
		for load_i in loadList:
			wi = loadWeights.get(load_i,1)
			ni = dfStatus[load_i].map(lambda x: 1-x).to_numpy()
			wi_ni = wi * ni
			Sum_wi += wi
			Sum_wi_ni = np.add(Sum_wi_ni, wi_ni)
		indivWeightedOI = np.around((100*Sum_wi_ni/Sum_wi),3).tolist()
		return indivWeightedOI
	
	# Calculate weighted outage incidence based on individually assigned weights
	with open(loadPriorityFilePath) as inFile:
		loadWeights = json.load(inFile)
	indivWeightedOI = calcWeightedOI(loadWeights)

	# TODO: Run calcWeightedOI with various microgrid masks (1 for loads in microgrid, 0 otherwise. For unweighted, use mask as weight. For weighted, multiply mask element-wise by weight)
	
	
	mgOIFigures = {}
	for targetID in mgIDs:
		mgLoadMask = {load:(1 if id == targetID else 0) for (load,id) in loadMgDict.items()}
		mgLoadWeights = {load:(val*loadWeights.get(load,1)) for (load,val) in mgLoadMask.items()}
		mgOI = calcWeightedOI(mgLoadMask)
		mgOIWeighted = calcWeightedOI(mgLoadWeights)
		mgOIFigures[targetID] = go.Figure()
		mgOIFigures[targetID].add_trace(go.Scatter(
			x=timeList,
			y=mgOI,
			mode='lines',
			name='Unweighted OI',
			hovertemplate=
			'<b>Time Step</b>: %{x}<br>' +
			f'<b>Unweighted OI for Microgrid {targetID}</b>: %{{y:.3f}}%'))
		mgOIFigures[targetID].add_trace(go.Scatter(
			x=timeList,
			y=mgOIWeighted,
			mode='lines',
			name='Priority-Weighted OI',
			hovertemplate=
			'<b>Time Step</b>: %{x}<br>' +
			f'<b>Priority-Weighted OI for Microgrid {targetID}</b>: %{{y:.3f}}%'))
		mgOIFigures[targetID].update_layout(
			xaxis_title='Before Hour X',
			yaxis_title='Load Outage %',
			yaxis_range=[-5,105],
			title=f'Microgrid {targetID}',
			legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

	outageIncidenceFigure = go.Figure()
	outageIncidenceFigure.add_trace(go.Scatter(
		x=timeList,
		y=outageIncidence,
		mode='lines',
		name='Unweighted Outage Incidence',
		hovertemplate=
		'<b>Time Step</b>: %{x}<br>' +
		'<b>Unweighted Outage Incidence</b>: %{y:.3f}%'))
	if includeGroupWeights:
		outageIncidenceFigure.add_trace(go.Scatter(
			x=timeList,
			y=weightedOutageIncidence,
			mode='lines',
			name='Group-Weighted Outage Incidence',
			hovertemplate=
			'<b>Time Step</b>: %{x}<br>' +
			'<b>Group-Weighted Outage Incidence</b>: %{y:.3f}%'))
	outageIncidenceFigure.add_trace(go.Scatter(
		x=timeList,
		y=indivWeightedOI,
		mode='lines',
		name='Priority-Weighted Outage Incidence',
		hovertemplate=
		'<b>Time Step</b>: %{x}<br>' +
		'<b>Priority-Weighted Outage Incidence</b>: %{y:.3f}%'))
	# Edit the layout
	outageIncidenceFigure.update_layout(
		xaxis_title='Before Hour X',
		yaxis_title='Load Outage %',
		yaxis_range=[-5,105],
		legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

	return outageIncidenceFigure, mgOIFigures

def getMicrogridInfo(modelDir, pathToOmd, settingsFile, makeCSV = True):
	'''	Gathers microgrid info including loads and other circuit objects in each microgrid by finding what microgrid each load's parent bus is designated as having. 
		Microgrid assignments to buses are taken from settingsFile so that we can see what microgrid assignments the 
		code is working with, not just what they are intended to be via the microgrid tagging input file

		Returns a dictionary with keys loadMgDict, busMgDict, obMgDict, and mgIDs

		loadMgDict, busMgDict, and obMgDict correspond to dictionaries mapping circuit object names to microgrid labels.
		mgIDs corresponds to a set of the unique microgrid labels derived from the values of busMgDict.	
		
		If makeCSV is True, which is default, creates a file called microgridAssignmentOutputs.csv containing 
		the information from loadMgDict for inspection by users.
	'''

	with open(settingsFile) as inFile:
		settingsData = json.load(inFile)
	busMgDict = {}
	for busName,v in settingsData['bus'].items():	
		busMgDict[busName] = v.get('microgrid_id', 'no MG')
	
	with open(pathToOmd) as inFile:
		omd = json.load(inFile)
	loadMgDict = {}
	obMgDict = {}
	for ob in omd.get('tree',{}).values():
		if ob['object'] == 'load':
			loadMgDict[ob['name']] = busMgDict[ob['parent']]
		if 'parent' in ob.keys():
			obMgDict[ob['name']] = busMgDict.get(ob['parent'],'no MG')
	
	if makeCSV:
		with open(pJoin(modelDir,'microgridAssignmentOutputs.csv'), 'w', newline='') as file:
			writer = csv.writer(file)
			writer.writerow(['load name','microgrid_id'])
			for loadName,mg_id in loadMgDict.items():
				writer.writerow([loadName,mg_id])
			for busName,mg_id in busMgDict.items():
				writer.writerow([busName,mg_id])
			for obName,mg_id in obMgDict.items():
				writer.writerow([obName,mg_id])

	mgIDs = set(busMgDict.values())

	return {'loadMgDict':loadMgDict, 'busMgDict':busMgDict, 'obMgDict':obMgDict, 'mgIDs':mgIDs}

def runMicrogridControlSim(modelDir, solFidelity, eventsFilename, loadPriorityFile, microgridTaggingFile):
	''' Runs a microgrid control simulation using PowerModelsONM to determine optimal control actions during a configured outage event.
		Once the simulation is run, the results are stored in an output file called output.json in the working directory. 
		Before running the simulation, a settings file for the simulation is generated using the feeder file, a load priorities file, and a microgrid tagging file. 
	'''
	# Setup ONM if it hasn't been done already.
	if not PowerModelsONM.check_instantiated():
		PowerModelsONM.install_onm()

	lpFile = loadPriorityFile if loadPriorityFile != None else ''
	mgFile = microgridTaggingFile if microgridTaggingFile != None else ''


	PowerModelsONM.build_settings_file(
		circuitPath=pJoin(modelDir,'circuit.dss'),
		settingsPath=pJoin(modelDir,'settings.json'), 
		loadPrioritiesFile=lpFile, 
		microgridTaggingFile=mgFile)
	
	# get mip_solver_gap info (solFidelity)
	solFidelityVal = 0.05 #default to medium fidelity
	if solFidelity == '0.10':
		solFidelityVal = 0.10
	elif solFidelity == '0.02':
		solFidelityVal = 0.02
	
	PowerModelsONM.run_onm(
		circuitPath=pJoin(modelDir,'circuit.dss'),
		settingsPath=pJoin(modelDir,'settings.json'),
		outputPath=pJoin(modelDir,'output.json'),
		eventsPath=pJoin(modelDir,eventsFilename),
		mip_solver_gap=solFidelityVal
	)	

def genProfilesByMicrogrid(mgIDs, obMgDict, powerflow):
	# TODO: make an informative docstring

	timesteps = range(len(powerflow))
	#Conversion to list and sort is conducted so that they are ordered the same on every run. Otherwise, they take on different colors in the graph between runs
	pfTypes = list(set(powerflow[0].keys())-{'switch','bus'})
	pfTypes.sort()
	pfDataAggregated = {mgID:pd.DataFrame(0, index=timesteps, columns=pfTypes) for mgID in mgIDs.union({'no MG'})}
	pfDataSystemwide = pd.DataFrame(0, index=timesteps, columns=pfTypes)
	
	for timestep in timesteps:
		for pfType in pfTypes:
			for obName, obData in powerflow[timestep][pfType].items():
				obPf = sum(obData['real power setpoint (kW)'])
				obPf *= -1 if pfType == "storage" else 1
				obMg = obMgDict.get(obName, 'no MG')
				pfDataAggregated[obMg].at[timestep,pfType] += obPf
				pfDataSystemwide.at[timestep,pfType] += obPf

	minVal = float('inf')
	maxVal = float('-inf')
	for df in pfDataAggregated.values():
		minVal = min(minVal, df.min().min())
		maxVal = max(maxVal, df.max().max())
	axisPadding = 0.05*(maxVal-minVal)
	graphMin = minVal-axisPadding
	graphMax = maxVal+axisPadding
	
	pfTypeNameMap = {
		'voltage_source':'Grid',
		'solar':'Solar DG',
		'storage':'Energy Storage',
		'generator':'Diesel DG'
	}
	gensFigure = go.Figure()
	for pfType in pfTypes:
		pfTypeRenamed = pfTypeNameMap.get(pfType,pfType)
		gensFigure.add_trace(go.Scatter(
			x=list(timesteps),
			y=pfDataSystemwide[pfType].to_list(),
			mode='lines',
			name=pfTypeRenamed,
			hovertemplate=
			'<b>Time Step</b>: %{x}<br>' +
			f'<b>{pfTypeRenamed}</b>: %{{y:.3f}}%'))
	gensFigure.update_layout(
		xaxis_title='Hours',
		yaxis_title='Power (kW)',
		yaxis_range=[graphMin, graphMax],
		legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

	mgGensFigures = {}
	for mgID in mgIDs:
		mgGensFigures[mgID] = go.Figure()
		for pfType in pfTypes:
			pfTypeRenamed = pfTypeNameMap.get(pfType,pfType)
			mgGensFigures[mgID].add_trace(go.Scatter(
				x=list(timesteps),
				y=pfDataAggregated[mgID][pfType].to_list(),
				mode='lines',
				name=pfTypeRenamed,
				hovertemplate=
				'<b>Time Step</b>: %{x}<br>' +
				f'<b>{pfTypeRenamed} for Microgrid {mgID}</b>: %{{y:.3f}}%'))
		mgGensFigures[mgID].update_layout(
			xaxis_title='Hours',
			yaxis_title='Power (kW)',
			yaxis_range=[graphMin, graphMax],
			title=f'Microgrid {mgID}',
			legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

	return gensFigure, mgGensFigures


def graphMicrogrid(modelDir, pathToOmd, profit_on_energy_sales, restoration_cost, hardware_cost, pathToJson, pathToCsv, loadPriorityFile, loadMgDict, obMgDict, mgIDs):
	''' Run full microgrid control process. '''
	# Gather output data.
	with open(pJoin(modelDir,'output.json')) as inFile:
		data = json.load(inFile)
		genProfiles = data['Generator profiles']
		simTimeSteps = []
		for i in data['Simulation time steps']:
			simTimeSteps.append(float(i))
		numTimeSteps = len(simTimeSteps)
		stepSize = simTimeSteps[1]-simTimeSteps[0]
		voltages = data['Voltages']
		outageDuration = stepSize * numTimeSteps
		loadServed = data['Load served']
		storageSOC = data['Storage SOC (%)']
		switchLoadAction = data['Device action timeline']
		powerflow = data['Powerflow output']
	actionTime = []
	actionDevice = []
	actionAction = []
	actionLoadBefore = []
	actionLoadAfter = []
	loadsShed = []
	cumulativeLoadsShed = []
	startTime = 0
	timestep = startTime
	# timestep = 0
	# timestep = 1 #TODO: switch back to this value if timestep should start at 1, not zero | nevermind. see above fix using startTime
	for key in switchLoadAction:
		# if timestep == 1: #TODO: switch back to this value if timestep should start at 1, not zero | nevermind. see above fix using startTime
		# if timestep == 0:
		if timestep == startTime:
			switchActionsOld = key['Switch configurations']
		else:
			switchActionsNew = key['Switch configurations']
			for entry in switchActionsNew:
				if switchActionsNew[entry] != switchActionsOld[entry]:
					actionDevice.append(entry)
					actionTime.append(str(timestep))
					if switchActionsNew[entry] == 'open':
						actionAction.append('Switch Opening')
					else:
						actionAction.append('Switch Closing')
					actionLoadBefore.append(switchActionsOld[entry])
					actionLoadAfter.append(switchActionsNew[entry])
			switchActionsOld = key['Switch configurations']
		loadShed = key['Shedded loads']
		if len(loadShed) != 0:
			for entry in loadShed:
				cumulativeLoadsShed.append(entry)
				if entry not in loadsShed:
					actionDevice.append(entry)
					actionTime.append(str(timestep))
					actionAction.append('Load Shed')
					actionLoadBefore.append('online')
					actionLoadAfter.append('offline')
					loadsShed.append(entry)
				else:
					actionDevice.append(entry)
					actionTime.append(str(timestep))
					actionAction.append('Load Pickup')
					actionLoadBefore.append('offline')
					actionLoadAfter.append('online')
					loadsShed.remove(entry)
		timestep += 1
	timestep = 0
	# while timestep < 24:
	while timestep < numTimeSteps:
		if timestep == 0:
			powerflowOld = powerflow[timestep]
		else:
			powerflowNew = powerflow[timestep]
			for generator in list(powerflowNew['generator'].keys()):
				entryNew = powerflowNew['generator'][generator]['real power setpoint (kW)'][0]
				if generator in list(powerflowOld['generator'].keys()):
					entryOld = powerflowOld['generator'][generator]['real power setpoint (kW)'][0]
				else:
					entryOld = 0.0
				if math.sqrt(((entryNew - entryOld)/(entryOld + 0.0000001))**2) > 0.5:
					actionDevice.append(generator)
					actionTime.append(str(timestep + startTime))
					# actionTime.append(str(timestep))
					# actionTime.append(str(timestep + 1)) #TODO: switch back to this value if timestep should start at 1, not zero | nevermind. see above fix using startTime
					actionAction.append('Generator Control')
					actionLoadBefore.append(str(entryOld))
					actionLoadAfter.append(str(entryNew))
			for battery in list(powerflowNew['storage'].keys()):
				entryNew = powerflowNew['storage'][battery]['real power setpoint (kW)'][0]
				if battery in list(powerflowOld['storage'].keys()):
					entryOld = powerflowOld['storage'][battery]['real power setpoint (kW)'][0]
				else:
					entryOld = 0.0
				if math.sqrt(((entryNew - entryOld)/(entryOld + 0.0000001))**2) > 0.5:
					actionDevice.append(battery)
					actionTime.append(str(timestep + startTime))
					# actionTime.append(str(timestep))
					# actionTime.append(str(timestep + 1)) #TODO: switch back to this value if timestep should start at 1, not zero | nevermind. see above fix using startTime
					actionAction.append('Battery Control')
					actionLoadBefore.append(str(entryOld))
					actionLoadAfter.append(str(entryNew))
			powerflowOld = powerflow[timestep]
		timestep += 1
	line = {
		'time': actionTime,
		'device': actionDevice,
		'action': actionAction,
		'loadBefore': actionLoadBefore,
		'loadAfter': actionLoadAfter}
	outputTime = pd.DataFrame(line, columns = ['time','device','action','loadBefore','loadAfter'])
	outputTimeline = outputTime.sort_values('time')
	
	# Create traces
	gens, mgGensFigs = genProfilesByMicrogrid(mgIDs, obMgDict, powerflow)

	volts = go.Figure()
	voltsKeysAndNames = [
		('Min voltage (p.u.)','Minimum Voltage'),
		('Max voltage (p.u.)','Maximum Voltage'),
		('Mean voltage (p.u.)','Mean Voltage')]
	for key, name in voltsKeysAndNames:
		volts.add_trace(go.Scatter(
			x=simTimeSteps,
			y=voltages[key],
			mode='lines',
			name=name,
			hovertemplate=
			'<b>Time Step</b>: %{x}<br>' +
			f'<b>{name}</b>: %{{y:.4f}}'))
	# Edit the layout
	volts.update_layout(
		xaxis_title='Hours',
		yaxis_title='Power (p.u.)',
		legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
	
	loads = go.Figure()
	loadsKeysAndNames = [
		('Feeder load (%)','Feeder Load'),
		('Microgrid load (%)','Microgrid Load'),
		('Bonus load via microgrid (%)','Bonus Load via Microgrid')]
	for key,name in loadsKeysAndNames:
		loads.add_trace(go.Scatter(
			x=simTimeSteps,
			y=loadServed[key],
			mode='lines',
			name=name,
			hovertemplate=
			'<b>Time Step</b>: %{x}<br>' +
			f'<b>{name}</b>: %{{y:.2f}}'))
	# Edit the layout
	loads.update_layout(
		xaxis_title='Hours',
		yaxis_title='Load (%)',
		legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
	
	timelineStatsHtml = microgridTimeline(outputTimeline, modelDir)
	with open(pathToOmd) as inFile:
		tree = json.load(inFile)['tree']
	feederMap = geo.omdGeoJson(pathToOmd, conversion = False)
	
	row = 0
	row_count_timeline = outputTimeline.shape[0]
	
	def coordStrFormatter(coordString):
		coordList = coordString.split()
		newCoordString = ""
		count = 0
		for x in coordList:
			if count%2 == 0:
				newCoordString = newCoordString + "(" + x + ", "
			else:
				newCoordString = newCoordString + x + ")"
				if count < len(coordList) - 1:
					newCoordString = newCoordString + ", \n"
			count = count+1
		return newCoordString

	colormap = {
		'Load Shed':'0000FF',
		'Load Pickup':'00C957',
		'Switch Opening':'FF8000',
		'Switch Closing':'9370DB',
		'Battery Control':'FFFF00',
		'Generator Control':'E0FFFF',
	}
	while row < row_count_timeline:
		full_data = pullDataForGraph(tree, feederMap, outputTimeline, row)
		device, coordLis, coordStr, time, action, loadBefore, loadAfter = full_data
		dev_dict = {}
		try:
			dev_dict['type'] = 'Feature'
			dev_dict['properties'] = {
				'device': device, 
				'time': time,
				'action': action,
				'loadBefore': loadBefore,
				'loadAfter': loadAfter,
				'popupContent': f'''Location: <b>{coordStrFormatter(str(coordStr))}</b><br>
									Device: <b>{str(device)}</b><br>
									Time: <b>{str(time)}</b><br>
									Action: <b>{str(action)}</b><br>
									Before: <b>{str(loadBefore)}</b><br>
									After: <b>{str(loadAfter)}</b>.''' }
			if len(coordLis) != 2:
				dev_dict['geometry'] = {'type': 'LineString', 'coordinates': [[coordLis[0], coordLis[1]], [coordLis[2], coordLis[3]]]}
				dev_dict['properties']['edgeColor'] = f'#{colormap[action]}'
			else:
				dev_dict['geometry'] = {'type': 'Point', 'coordinates': [coordLis[0], coordLis[1]]}
				dev_dict['properties']['pointColor'] = f'#{colormap[action]}'
				if loadMgDict != None and str(device).split('_')[0] == 'load':
					mgID = loadMgDict.get(str(device),'no MG ID')
					dev_dict['properties']['microgrid_id'] = mgID
					dev_dict['properties']['popupContent'] += f'<br>Microgrid ID: <b>{mgID}</b>'
			feederMap['features'].append(dev_dict)
		except:
			print('MESSED UP MAPPING on', device, full_data)
		row += 1
	if not os.path.exists(modelDir):
		os.makedirs(modelDir)
	shutil.copy(omf.omfDir + '/templates/geoJsonMap.html', modelDir)
	with open(pJoin(modelDir,'geoJsonFeatures.js'),'w') as outFile:
		outFile.write('var geojson =')
		json.dump(feederMap, outFile, indent=4)
	# Save geojson dict to then read into outdata in work function below
	with open(pJoin(modelDir,'geoDict.js'),'w') as outFile:
		json.dump(feederMap, outFile, indent=4)
	# Generate customer outage outputs
	try:
		# TODO: this should not be customerOutageData... this is the input of customer info. It's later turned into customerOutageData by adding more info, but this same variable should NOT be used for the same thing
		customerOutageData = pd.read_csv(pathToCsv)
	except:
		# TODO: Needs to be updated to provide info for all loads, not just shed loads. Outage Incidence plot is dependent on all loads
		deviceTimeline = data["Device action timeline"]
		loadsShed = []
		for line in deviceTimeline:
			loadsShed.append(line["Shedded loads"])
		customerOutageData = pd.DataFrame(columns=['Customer Name','Season','Business Type','Load Name'])
		for elementDict in tree.values():
			if elementDict['object'] == 'load' and float(elementDict['kw'])>.1 and elementDict['name'] in loadsShed[0]:
				loadName = elementDict['name']
				avgLoad = float(elementDict['kw'])/2.5
				busType = 'residential'*(avgLoad<=10) + 'retail'*(avgLoad>10)*(avgLoad<=20) + 'agriculture'*(avgLoad>20)*(avgLoad<=39) + 'public'*(avgLoad>39)*(avgLoad<=50) + 'services'*(avgLoad>50)*(avgLoad<=100) + 'manufacturing'*(avgLoad>100)
				customerOutageData.loc[len(customerOutageData.index)] =[loadName,'summer',busType,loadName]
	numberRows = max(math.ceil(customerOutageData.shape[0]/2),1)
	fig, axs = plt.subplots(numberRows, 2)
	row = 0
	average_lost_kwh = []
	outageCost = []
	globalMax = 0
	fig = go.Figure()
	businessTypes = set(customerOutageData['Business Type'])
	outageCostsByType = {busType: [] for busType in businessTypes}
	avgkWColumn = []
	durationColumn = []
	dssTree = dssConvert.dssToTree(f'{modelDir}/circuitOmfCompatible_cleanLists.dss')
	loadShapeMeanMultiplier = {}
	loadShapeMeanActual = {}
	for dssLine in dssTree:
		if 'object' in dssLine and dssLine['object'].split('.')[0] == 'loadshape':
			shape = dssLine['mult'].replace('[','').replace('(','').replace(']','').replace(')','').split(',')
			shape = [float(y) for y in shape]
			if 'useactual' in dssLine and dssLine['useactual'] == 'yes': loadShapeMeanActual[dssLine['object'].split('.')[1]] = np.mean(shape)
			else: loadShapeMeanMultiplier[dssLine['object'].split('.')[1]] = np.mean(shape)/np.max(shape)
	while row < customerOutageData.shape[0]:
		customerName = str(customerOutageData.loc[row, 'Customer Name'])
		loadName = str(customerOutageData.loc[row, 'Load Name'])
		businessType = str(customerOutageData.loc[row, 'Business Type'])
		duration = str(0)
		averagekWperhr = str(0)
		for elementDict in dssTree:
			if 'object' in elementDict and elementDict['object'].split('.')[0] == 'load' and elementDict['object'].split('.')[1] == loadName:
				if 'daily' in elementDict: averagekWperhr = float(loadShapeMeanMultiplier.get(elementDict['daily'],0)) * float(elementDict['kw']) + float(loadShapeMeanActual.get(elementDict['daily'],0))
				else: averagekWperhr = float(elementDict['kw'])/2
				duration = str(cumulativeLoadsShed.count(loadName) * stepSize)
		if float(duration) >= .1 and float(averagekWperhr) >= .1:
			durationColumn.append(duration)
			avgkWColumn.append(float(averagekWperhr))
			season = str(customerOutageData.loc[row, 'Season'])
			customerOutageCost, kWperhrEstimate, times, localMax = customerCost1(duration, season, averagekWperhr, businessType)
			average_lost_kwh.append(float(averagekWperhr))
			outageCost.append(customerOutageCost)
			outageCostsByType[businessType].append(customerOutageCost)
			if localMax > globalMax:
				globalMax = localMax
			# creating series
			timesSeries = pd.Series(times)
			kWperhrSeries = pd.Series(kWperhrEstimate)
			trace = py.graph_objs.Scatter(
				x = timesSeries,
				y = kWperhrSeries,
				name = customerName,
				hoverlabel = dict(namelength = -1),
				hovertemplate = 
				'<b>Duration</b>: %{x} h<br>' +
				'<b>Cost</b>: $%{y:.2f}')
			fig.add_trace(trace)
			row += 1
		else:
			customerOutageData = customerOutageData.drop(index=row)
			customerOutageData = customerOutageData.reset_index(drop=True)
	customerOutageData.insert(1, "Duration", durationColumn, True)
	customerOutageData.insert(3, "Average kW/hr", avgkWColumn, True)
	durations = customerOutageData.get('Duration',['0'])
	try:
		maxDuration = max([float(x) for x in durations])
	except:
		maxDuration = 12.0 #HACKCOBB: Duration comes back as 'Duration'
	customersOutByTime = [{busType: 0 for busType in businessTypes} for x in range(math.ceil(maxDuration)+1)]
	customerCostByTime = [{busType: 0.0 for busType in businessTypes} for x in range(math.ceil(maxDuration)+1)]
	customerCountByType = {busType: 0 for busType in businessTypes}
	# def deciles(dList): return [0.0] + quantiles([float(x) for x in dList], n=10) + [max([float(x) for x in dList])]
	# outageDeciles = deciles(customerOutageData['Duration'].tolist())
	# costDeciles = deciles(outageCost)
	if not outageCost: outageCost = [.001]
	minCustomerCost = min(outageCost)
	maxCustomerCost = max(outageCost)
	numBins = 45
	binSize = (maxCustomerCost-minCustomerCost)/numBins
	totalCustomerCost = sum(outageCost)
	meanCustomerCost = totalCustomerCost / len(outageCost)

	fig.update_layout(xaxis_title = 'Duration (hours)',
		yaxis_title = 'Cost ($)',
		legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
	# Customer Outage Histogram
	busColors = {'residential':'#0000ff', 'manufacturing':'#ff0000', 'mining':'#708090', 'construction':'#ff8c00', 'agriculture':'#008000', 'finance':'#d6b600', 'retail':'#ff69b4', 'services':'#191970', 'utilities':'#8b4513', 'public':'#9932cc'}
	custHist = go.Figure()
	# custHist.add_trace(go.Histogram(
	#	x=outageCost,
	#	xbins=dict(
	#		start=minCustomerCost,
	#		end=maxCustomerCost+binSize,
	#		size=binSize
	#	)
	# ))
	for busType in businessTypes:
		custHist.add_trace(go.Histogram(
			x=outageCostsByType[busType],
			name=busType, # name used in legend and hover labels
			xbins=dict(
				start=minCustomerCost,
				end=maxCustomerCost+binSize,
				size=binSize
			),
			bingroup=1,
			marker_color=busColors[busType]
		))
	custHist.update_layout(
		xaxis_title_text='Outage Cost ($)', # xaxis label
		yaxis_title_text='Customer Count', # yaxis label
		barmode='stack',
		bargap=0.1 # gap between bars of adjacent location coordinates
	)
	meanCustomerCostStr = "Mean Outage Cost: $"+"{:.2f}".format(meanCustomerCost)
	# custHist.add_vline(
	#	x=meanCustomerCost,
	#	line_width=3, 
	#	line_dash="dash",
	#	line_color="black",
	#	annotation_text=meanCustomerCostStr, 
	#	annotation_position="top right"
	# )
	custHist.add_shape(
		type="line",
		xref="x", 
		yref="paper", 
		x0=meanCustomerCost, 
		y0=0, 
		x1=meanCustomerCost,
		y1=1.0, 
		line=dict(
			color="black",
			width=3,
			dash="dash"
		)
	)
	custHist.add_annotation(
		xref="x",
		yref="paper",
		x=meanCustomerCost,
		y=1.0,
		xanchor="left",
		text=meanCustomerCostStr,
		showarrow=False
	)

	outageIncidenceFig, mgOIFigs = outageIncidenceGraph(customerOutageData, outputTimeline, startTime, numTimeSteps, loadPriorityFile, loadMgDict)
	
	customerOutageHtml = customerOutageTable(customerOutageData, outageCost, modelDir)
	profit_on_energy_sales = float(profit_on_energy_sales)
	restoration_cost = int(restoration_cost)
	hardware_cost = int(hardware_cost)
	outageDuration = int(outageDuration)
	utilityOutageHtml = utilityOutageTable(average_lost_kwh, profit_on_energy_sales, restoration_cost, hardware_cost, outageDuration, modelDir)
	try: customerOutageCost = customerOutageCost
	except: customerOutageCost = 0
	return {'utilityOutageHtml': utilityOutageHtml, 'customerOutageHtml': customerOutageHtml, 'timelineStatsHtml': timelineStatsHtml, 'outageIncidenceFig': outageIncidenceFig, 'mgOIFigs':mgOIFigs, 'mgGensFigs':mgGensFigs, 'gens': gens, 'loads': loads, 'volts': volts, 'fig': fig, 'customerOutageCost': customerOutageCost, 'numTimeSteps': numTimeSteps, 'stepSize': stepSize, 'custHist': custHist}

def buildCustomEvents(eventsCSV='', feeder='', customEvents='customEvents.json', defaultDispatchable = 'true'):
	def outageSwitchState(outList): return ('open'*(outList[3] == 'closed') + 'closed'*(outList[3]=='open'))
	def eventJson(dispatchable, state, timestep, affected_asset):
		return {
			"event_data": {
				"status": 1,
				"dispatchable": dispatchable,
				"type": "breaker",
				"state": state
			},
			"timestep": timestep,
			"affected_asset": ("line." + affected_asset),
			"event_type": "switch"
		}
	if eventsCSV == '': # Find largest switch, flip it and set to non-dispatchable at timestep 1.
		with open(feeder, 'a') as f:
			f.write('Export Currents')
		with open(feeder, 'r') as f:
			f.read()
	elif ',' in eventsCSV:
		outageReader = csv.reader(io.StringIO(eventsCSV))
	else:
		outageReader = csv.reader(open(eventsCSV))
	if feeder.endswith('.omd'):
		with open(feeder) as omdFile:
			tree = json.load(omdFile)['tree']
		niceDss = dssConvert.evilGldTreeToDssTree(tree)
		dssConvert.treeToDss(niceDss, 'circuitOmfCompatible.dss')
		dssTree = dssConvert.dssToTree('circuitOmfCompatible.dss')
	else: return('Error: Feeder must be an OMD file.')
	outageAssets = [] # formerly row[0] for row in outageReader
	customEventList = []
	for row in outageReader:
		outageAssets.append(row[0])
		try:
			customEventList.append(eventJson('false',outageSwitchState(row),int(row[1]),row[0]))
			if int(row[2])>0:
				customEventList.append(eventJson(row[4],row[3],int(row[2]),row[0]))
		except: pass
	unaffectedOpenAssets = [dssLine['object'].split('.')[1] for dssLine in dssTree if dssLine['!CMD'] == 'open']
	unaffectedClosedAssets = [dssLine['object'].split('.')[1] for dssLine in dssTree if dssLine.get('!CMD') == 'new' \
		and dssLine['object'].split('.')[0] == 'line' \
		and 'switch' in [key for key in dssLine] \
	#   and dssLine['switch'] == 'y'] # \
		and (dssLine['object'].split('.')[1] not in (unaffectedOpenAssets + outageAssets))]
	customEventList += [eventJson(defaultDispatchable,'open',1,asset) for asset in unaffectedOpenAssets] 
	customEventList += [eventJson(defaultDispatchable,'closed',1,asset) for asset in unaffectedClosedAssets]
	customEventList += [eventJson('false',outageSwitchState(row),int(row[1]),row[0]) for row in outageReader]
	customEventList += [eventJson(row.get('dispatchable'),row.get('defaultState',int(row.get('timestep'))),row.get('asset')) for row in outageReader if int(row[2])>0]
	with open(customEvents,'w') as eventsFile:
		json.dump(customEventList, eventsFile)

def copyInputFilesToModelDir(modelDir, inputDict):
	''' Creates local copies of input files in the model directory modelDir.
		Returns a dictionary of paths to the local copies with the following keys:

		'mgTagging', 'loadPriority', 'customerInfo', 'event'
	'''
	pathToLocalFile = {}
	if inputDict['microgridTaggingFileName'] != '':
		try:
			with open(pJoin(modelDir, inputDict['microgridTaggingFileName']), 'w') as mgtFile:
				pathToLocalFile['mgTagging'] = mgtFile.name
				mgtFile.write(inputDict['microgridTaggingData'])
		except:
			pathToLocalFile['mgTagging'] = None
			raise Exception("ERROR - Unable to write microgrid tagging file: " + str(inputDict['microgridTaggingFileName']))
	else:
		pathToLocalFile['mgTagging'] = None

	if inputDict['loadPriorityFileName'] != '':
		try:
			with open(pJoin(modelDir, inputDict['loadPriorityFileName']), 'w') as lpFile:
				pathToLocalFile['loadPriority'] = lpFile.name
				lpFile.write(inputDict['loadPriorityData'])
		except:
			pathToLocalFile['loadPriority'] = None
			raise Exception("ERROR - Unable to write load priority file: " + str(inputDict['loadPriorityFileName']))
	else:
		pathToLocalFile['loadPriority'] = None

	if inputDict['customerFileName']:
		with open(pJoin(modelDir, inputDict['customerFileName']), 'w') as ciFile:
			pathToLocalFile['customerInfo'] = ciFile.name
			ciFile.write(inputDict['customerData'])
	else: 
		with open(pJoin(modelDir, 'customerInfo.csv'), 'w') as ciFile:
			pathToLocalFile['customerInfo'] = ciFile.name
			ciFile.write(inputDict['customerData'])

	with open(pJoin(modelDir, inputDict['eventFileName']), 'w') as eFile:
		pathToLocalFile['event'] = eFile.name
		eFile.write(inputDict['eventData'])
	
	return pathToLocalFile

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}
	# Write in the feeder
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict['feederName1'] = feederName
	with open(f'{modelDir}/{feederName}.omd', 'r') as omdFile:
		omd = json.load(omdFile)
	tree = omd['tree']

	# Output a .dss file, which will be needed for ONM.
	niceDss = dssConvert.evilGldTreeToDssTree(tree)
	dssConvert.treeToDss(niceDss, f'{modelDir}/circuit.dss')
	dssConvert.treeToDss(niceDss, f'{modelDir}/circuitOmfCompatible.dss') # for querying loadshapes
	dssConvert.dss_to_clean_via_save(f'{modelDir}/circuitOmfCompatible.dss', f'{modelDir}/circuitOmfCompatible_cleanLists.dss')

	pathToLocalFile = copyInputFilesToModelDir(modelDir, inputDict)
	
	runMicrogridControlSim(
		modelDir				= modelDir, 
		solFidelity				= inputDict['solFidelity'],
		eventsFilename			= inputDict['eventFileName'],
		loadPriorityFile		= pathToLocalFile['loadPriority'],
		microgridTaggingFile	= pathToLocalFile['mgTagging']
	)
	microgridInfo = getMicrogridInfo(
		modelDir			= modelDir, 
		pathToOmd			= f'{modelDir}/{feederName}.omd', 
		settingsFile		= f'{modelDir}/settings.json'
	)
	plotOuts = graphMicrogrid(
		modelDir				= modelDir, 
		pathToOmd				= f'{modelDir}/{feederName}.omd', 
		profit_on_energy_sales	= inputDict['profit_on_energy_sales'],
		restoration_cost		= inputDict['restoration_cost'],
		hardware_cost			= inputDict['hardware_cost'],
		pathToJson				= pathToLocalFile['event'],
		pathToCsv				= pathToLocalFile['customerInfo'],
		loadPriorityFile		= pathToLocalFile['loadPriority'],
		loadMgDict				= microgridInfo['loadMgDict'],
		obMgDict 				= microgridInfo['obMgDict'],
		mgIDs					= microgridInfo['mgIDs']
	)


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

	outData['outageIncidenceHtml'] = plotOuts.get('outageIncidenceHtml')
	# Image outputs.
	# with open(pJoin(modelDir,'customerCostFig.png'),'rb') as inFile:
	#	outData['customerCostFig.png'] = base64.standard_b64encode(inFile.read()).decode()
	# Plotly outputs.
	layoutOb = go.Layout()
	outData['mgGensFigsData'] = json.dumps(plotOuts.get('mgGensFigs',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['mgGensFigsLayout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['fig1Data'] = json.dumps(plotOuts.get('gens',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig1Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['fig2Data'] = json.dumps(plotOuts.get('volts',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig2Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['fig3Data'] = json.dumps(plotOuts.get('loads',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig3Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['fig4Data'] = json.dumps(plotOuts.get('fig',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig4Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['fig5Data'] = json.dumps(plotOuts.get('custHist',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig5Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['fig6Data'] = json.dumps(plotOuts.get('outageIncidenceFig',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['fig6Layout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	outData['mgOIFigsData'] = json.dumps(plotOuts.get('mgOIFigs',{}), cls=py.utils.PlotlyJSONEncoder)
	outData['mgOIFigsLayout'] = json.dumps(layoutOb, cls=py.utils.PlotlyJSONEncoder)
	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	outData['numTimeSteps'] = plotOuts.get('numTimeSteps', 24)
	outData['stepSize'] = plotOuts.get('stepSize', 1)
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	# ====== For All Test Cases
	cust_file_path = ''
	# ====== Optional inputs for custom load priority and microgrid tagging - set the file path to '' and data to None initially and change their value below if desired
	loadPriority_file_path = ['']
	loadPriority_file_data = None
	microgridTagging_file_path = ['']
	microgridTagging_file_data = None
	# ====== Iowa240 Test Case
	feeder_file_path= [__neoMetaModel__._omfDir,'static','testFiles','iowa240_dwp_22_no_show_voltage.dss.omd']
	event_file_path = [__neoMetaModel__._omfDir,'static','testFiles','iowa240_dwp_22.events.json']
	loadPriority_file_path = [__neoMetaModel__._omfDir,'static','testFiles','iowa240_dwp_22.loadPriority.basic.json']
	loadPriority_file_data = open(pJoin(*loadPriority_file_path)).read()
	microgridTagging_file_path = [__neoMetaModel__._omfDir,'static','testFiles','iowa240_dwp_22.microgridTagging.basic.json']
	microgridTagging_file_data = open(pJoin(*microgridTagging_file_path)).read()
	# ====== Nreca1824 Test Case
	# feeder_file_path = [__neoMetaModel__._omfDir,'static','testFiles','nreca1824_dwp.omd']
	# event_csv_path = [__neoMetaModel__._omfDir,'static','testFiles','nreca1824events.csv']
	# event_file_path = [__neoMetaModel__._omfDir,'static','testFiles','nreca1824_dwp.events.json']
	# loadPriority_file_path = [__neoMetaModel__._omfDir,'static','testFiles','nreca1824_dwp.loadPriority.basic.json']
	# loadPriority_file_data = open(pJoin(*loadPriority_file_path)).read()
	# microgridTagging_file_path = [__neoMetaModel__._omfDir,'static','testFiles','nreca1824_dwp.microgridTagging.basic.json']
	# microgridTagging_file_data = open(pJoin(*microgridTagging_file_path)).read()
	
	# ====== Comment this out if no load priority file is specified
	# loadPriority_file_data = open(pJoin(*loadPriority_file_path)).read()
	# ====== Comment this out if no load microgrid tagging file is specified
	# microgridTagging_file_data = open(pJoin(*microgridTagging_file_path)).read()
	defaultInputs = {
		'modelType': modelName,
		'feederName1': feeder_file_path[-1][0:-4],
		'outageDuration': '5',
		'profit_on_energy_sales': '0.03',
		'restoration_cost': '100',
		'hardware_cost': '550',
		'customerFileName': '',
		'customerData': '',
		'eventFileName': event_file_path[-1],
		'eventData': open(pJoin(*event_file_path)).read(),
		'solFidelity': '0.05',
		'loadPriorityFileName': loadPriority_file_path[-1],
		'loadPriorityData': loadPriority_file_data,
		'microgridTaggingFileName': microgridTagging_file_path[-1],
		'microgridTaggingData': microgridTagging_file_data,
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(*feeder_file_path), pJoin(modelDir, defaultInputs['feederName1']+'.omd'))
	except:
		return False
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _debugging():
	# outageCostAnalysis(omf.omfDir + '/static/publicFeeders/Olin Barre LatLon.omd', omf.omfDir + '/static/testFiles/smartswitch_Outages.csv', None, '60', '1')
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
	# buildCustomSettings(pJoin(omf.omfDir,'static','testFiles','nreca1824events.csv'),pJoin(omf.omfDir,'static','testFiles','nreca1824_dwp.omd'),pJoin(modelLoc,'customSettings.json'))
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
	#_debugging()
	potato='baked'

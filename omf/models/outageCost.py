import pandas as pd
import numpy as np
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
hidden = True

def datetime_to_float(d):
	'helper function to convert a datetime object to a float'
	epoch = datetime.datetime.utcfromtimestamp(0)
	total_seconds = (d - epoch).total_seconds()
	return total_seconds	

def outageCostAnalysis(pathToOmd, pathToCsv, workDir, numberOfCustomers, sustainedOutageThreshold, causeFilter, timeMinFilter, timeMaxFilter, meterMinFilter, meterMaxFilter, durationMinFilter, durationMaxFilter):
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

	# Draw a leaflet graph of the feeder with outages
	outageMap = geo.omdGeoJson(pathToOmd, conversion=False)

	mc = pd.read_csv(pathToCsv)
	
	row = 0
	row_count_mc = mc.shape[0]
	while row < row_count_mc:
		entry = mc.loc[row, 'Location']
		cause = mc.loc[row, 'Cause']
		lis = str(mc.loc[row, 'Meters Affected'])
		meters = lis.split()
		duration = datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))
		time = datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S'))
		timeMin = datetime_to_float(datetime.datetime.strptime(timeMinFilter, '%Y-%m-%d %H:%M:%S'))
		timeMax = datetime_to_float(datetime.datetime.strptime(timeMaxFilter, '%Y-%m-%d %H:%M:%S'))
		print(timeMin)
		print(timeMax)
		meterCount = len(meters)
		p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture integer values
		coords = [float(i) for i in p.findall(entry)]
		coord1 = coords[0]
		coord2 = coords[1]
		Dict = {}
		Dict['geometry'] = {'type': 'Point', 'coordinates': [coord1, coord2]}
		Dict['type'] = 'Feature'
		Dict['properties'] = {'name': 'Fault_' + str(row+1), 'meterCount': int(meterCount), 'time': time, 'timeMin':timeMin, 'timeMax':timeMax, 'meterMinFilter': int(meterMinFilter), 'meterMaxFilter': int(meterMaxFilter), 'cause': str(cause), 'causeFilter': causeFilter, 'duration': int(duration), 'durationMinFilter': int(durationMinFilter), 'durationMaxFilter': int(durationMaxFilter), 'meters': str(mc.loc[row, 'Meters Affected']), 'pointColor': 'blue', 'popupContent': '<br><br>Fault start time: <b>' + str(mc.loc[row, 'Start']) + '</b><br> Fault duration: <b>' + str(duration) + ' seconds</b><br>Location: <b>' + str(coords) + '</b><br>Cause: <b>' + str(cause) + '</b><br>Meters Affected: <b><br>' + str(mc.loc[row, 'Meters Affected']) + '</b><br>Count of Meters Affected: <b>' + str(len(meters)) + '</b>.'}
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
		inputDict['numberOfCustomers'],
		inputDict['sustainedOutageThreshold'],
		inputDict['causeFilter'],
		inputDict['timeMinFilter'],
		inputDict['timeMaxFilter'],
		inputDict['meterMinFilter'],
		inputDict['meterMaxFilter'],
		inputDict['durationMinFilter'],
		inputDict['durationMaxFilter'])
	
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
		"numberOfCustomers": "192",
		"sustainedOutageThreshold": "300",
		"causeFilter": "bird",
		"timeMinFilter": "2000-01-01 00:00:01",
		"timeMaxFilter": "2000-05-06 00:00:30",
		"meterMinFilter": "0",
		"meterMaxFilter": "10",
		"durationMinFilter": "200",
		"durationMaxFilter": "100000",
		"outageFileName": "outagesNew3.csv",
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
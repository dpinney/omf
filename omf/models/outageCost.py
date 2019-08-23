import pandas as pd
from omf import geo, feeder
import re
import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import datetime
import plotly as py
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

def outageCostAnalysis(pathToOmd, pathToCsv, workDir, numberOfCustomers, sustainedOutageThreshold):
	
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
			entry = mc.loc[row, 'Meters Affected']
			p = re.compile(r'\b\d+\b')  # Compile a pattern to capture float values
			meters = [int(i) for i in p.findall(entry)]
			customerInterruptionDurations += (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) * len(meters) / 3600
		row += 1

	SAIDI = customerInterruptionDurations / int(numberOfCustomers)

	# calculate SAIFI
	row = 0
	totalInterruptions = 0.0
	customersAffected = 0
	while row < row_count_mc:
		if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) > int(sustainedOutageThreshold):
			entry = mc.loc[row, 'Meters Affected']
			p = re.compile(r'\b\d+\b')  # Compile a pattern to capture float values
			meters = [int(i) for i in p.findall(entry)]
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
			entry = mc.loc[row, 'Meters Affected']
			p = re.compile(r'\b\d+\b')  # Compile a pattern to capture float values
			meters = [int(i) for i in p.findall(entry)]
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
		p = re.compile(r'-?\d+\.\d+')  # Compile a pattern to capture integer values
		coords = [float(i) for i in p.findall(entry)]
		coord1 = coords[0]
		coord2 = coords[1]
		Dict = {}
		Dict['geometry'] = {'type': 'Point', 'coordinates': [coord1, coord2]}
		Dict['type'] = 'Feature'
		Dict['properties'] = {'name': '<b>_Fault_' + str(row+1) + '</b><br>', 'pointColor': 'blue', 'popupContent': '<br>Fault start time: <b>' + str(mc.loc[row, 'Start']) + '</b><br> Fault end time: <b>' + str(mc.loc[row, 'Finish']) + '</b><br>Location: <b>' + str(coords) + '</b><br>Meters affected: <b>' + str(mc.loc[row, 'Meters Affected']) + '</b>.'}
		outageMap['features'].append(Dict)
		row += 1
	if not os.path.exists(workDir):
		os.makedirs(workDir)
	shutil.copy(omf.omfDir + '/templates/geoJsonMap.html', workDir)
	with open(pJoin(workDir,'geoJsonFeatures.js'),"w") as outFile:
		outFile.write("var geojson =")
		json.dump(outageMap, outFile, indent=4)

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	outData = {}
	#test the main functions of the program
	plotOuts = outageCostAnalysis(
		inputDict['PATH_TO_OMD'],
		inputDict['PATH_TO_CSV'],
		modelDir, #Work directory.
		inputDict['numberOfCustomers'],
		inputDict['sustainedOutageThreshold']) #'1'
	
	# Textual outputs of cost statistic
	with open(pJoin(modelDir,"statsCalc.html"),"rb") as inFile:
		outData["statsHtml"] = inFile.read()

	with open(pJoin(modelDir,"geoJsonMap.html"),"rb") as inFile:
		outData["outageMap"] = inFile.read()

	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"modelType": modelName,
		"PATH_TO_OMD": omf.omfDir + '/static/publicFeeders/Olin Barre LatLon.omd',
		"PATH_TO_CSV": omf.omfDir + '/scratch/smartSwitching/Outages.csv',
		'numberOfCustomers': '60',
		'sustainedOutageThreshold': '1'
	}
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
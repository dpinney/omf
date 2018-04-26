''' Get power and energy limits from PNNL VirtualBatteries (VBAT) load model.'''

import json, os, shutil, subprocess, platform
from os.path import join as pJoin
from jinja2 import Template
import __neoMetaModel__
from __neoMetaModel__ import *


import requests, csv, tempfile



# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "Calculate the virtual battery capacity for a collection of thermostically controlled loads."

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName + ".html"),"r") as tempFile:
	template = Template(tempFile.read())

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	outData = {}
	# Run VBAT code.
	source = inputDict["source"]
	year = inputDict["year"]
	station = inputDict["station"]
	parameter = inputDict["weatherParameter"]
	if source == "METAR":
		outData["data"] = pullMETAR(year,station,parameter)
	
	# Stdout/stderr.
	outData["stdout"] = "Success"
	return outData

def pullMETAR(year, station, datatype): #def pullMETAR(year, station, datatype, outputDir):
	url = ('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=' + station + '&data=' + datatype + '&year1=' + year + 
		'&month1=1&day1=1&year2=' + year + '&month2=12&day2=31&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=1&report_type=2')
	r = requests.get(url)
	data = r.text
	# tempData = []
	# for x in range(8760):
	# 	tempData.append(((data.partition(station + ',')[2]).partition('\n')[0]).partition(',')[2])
	# 	data = data.partition(tempData[x])[2]
	return data
	# with open(outputDir, 'wb') as myfile:
	# 	wr = csv.writer(myfile,lineterminator = '\n')
	# 	for x in range(0,8760): 
	# 		wr.writerow([tempData[x]])

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"source":"METAR",
		"year":"2017",
		"station":"IAD",
		"weatherParameter":"tmpc",
		"modelType":modelName}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

#def defaultValuesAC():
#	power = "1000",
#	capacitance = "2",
#	resistance = "2",
#	cop = "2.5",
#	setpoint = "22.5",
#	deadband = "0.625",
#	return power,capacitance,resistance,cop,setpoint,deadband


def _simpleTest():
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
	renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_simpleTest ()
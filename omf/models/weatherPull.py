''' Get power and energy limits from PNNL VirtualBatteries (VBAT) load model.'''
import json, shutil, math, requests, csv, __neoMetaModel__
from os.path import isdir, join as pJoin
from jinja2 import Template
from __neoMetaModel__ import *
from dateutil.parser import parse as parseDt
from datetime import datetime as dt
from omf.weather import pullAsos, pullUscrn

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Download historical weather data for a given location for use in other models."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	source = inputDict['source']
	station = inputDict['stationASOS'] if source == 'ASOS' else inputDict['stationUSCRN']
	parameter = inputDict['weatherParameterASOS'] if source == 'ASOS' else inputDict['weatherParameterUSCRN']
	inputs = [inputDict['year'], station, parameter]
	data = pullAsos(*inputs) if source == 'ASOS' else pullUscrn(*inputs)
	with open(pJoin(modelDir,'weather.csv'), 'w') as f:
		csv.writer(f).writerows([[x] for x in data])
	return {
		'rawData': data,
		'errorCount': len([e for e in data if e in [-9999.0, -99999.0, -999.0, -99.0]]),
		'stdout': 'Success' }

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		#"source":"ASOS", 
		"source": "USCRN",
		"year": "2013",
		"stationASOS": "LWD",
		"stationUSCRN": "KY_Versailles_3_NNW",
		"weatherParameterUSCRN": "SOLARAD",
		"weatherParameterASOS": "tmpc",
		"modelType": modelName}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	modelLoc = pJoin(__neoMetaModel__._omfDir, "data", "Model", "admin", "Automated Testing of " + modelName)
	if isdir(modelLoc):
		shutil.rmtree(modelLoc)
	new(modelLoc) # Create New.
	renderAndShow(modelLoc) # Pre-run.
	try:
		runForeground(modelLoc) # Run the model.
	except:
		pass # Just ignore errors because sometimes HTTP requests fail.
	renderAndShow(modelLoc) # Show the output.

if __name__ == '__main__':
	_tests()
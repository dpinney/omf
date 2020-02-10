''' Get power and energy limits from PNNL VirtualBatteries (VBAT) load model.'''
import shutil, csv
from os.path import isdir, join as pJoin

import omf.weather
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "Download historical weather data for a given location for use in other models."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	source = inputDict['source']
	if source =='ASOS':
		station = inputDict['stationASOS']
		parameter = inputDict['weatherParameterASOS']
		data = omf.weather.pullAsos(inputDict['year'], station, parameter)
	elif source == 'USCRN':
		station = inputDict['stationUSCRN']
		parameter = inputDict['weatherParameterUSCRN']
		data = omf.weather.pullUscrn(inputDict['year'], station, parameter)
	elif source == 'darkSky':
		lat = inputDict['darkSkyLat']
		lon = inputDict['darkSkyLon']
		parameter = inputDict['weatherParameterdarkSky']
		data = omf.weather.pullDarksky(inputDict['year'], lat, lon, parameter, units='si')
	# station = inputDict['stationASOS'] if source == 'ASOS' else inputDict['stationUSCRN']
	# parameter = inputDict['weatherParameterASOS'] if source == 'ASOS' else inputDict['weatherParameterUSCRN']
	# inputs = [inputDict['year'], station, parameter]
	# data = omf.weather.pullAsos(*inputs) if source == 'ASOS' else omf.weather.pullUscrn(*inputs)
	with open(pJoin(modelDir,'weather.csv'), 'w', newline='') as f:
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
		"darkSkyLat": "39.828362",
		"darkSkyLon": "-98.579490",
		"modelType": modelName}
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def _tests():
	modelLoc = pJoin(__neoMetaModel__._omfDir, "data", "Model", "admin", "Automated Testing of " + modelName)
	if isdir(modelLoc):
		shutil.rmtree(modelLoc)
	new(modelLoc) # Create New.
	__neoMetaModel__.renderAndShow(modelLoc) # Pre-run.
	try:
		__neoMetaModel__.runForeground(modelLoc) # Run the model.
	except:
		pass # Just ignore errors because sometimes HTTP requests fail.
	__neoMetaModel__.renderAndShow(modelLoc) # Show the output.

if __name__ == '__main__':
	_tests()
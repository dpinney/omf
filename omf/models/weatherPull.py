''' Get power and energy limits from PNNL VirtualBatteries (VBAT) load model.'''
import shutil, csv
from os.path import isdir, join as pJoin

from omf import weather
from omf import easySolar
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "Download historical weather data for a given location for use in other models."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory.
		Model takes in parameters from inputDict, and returns a list of data points of type float.
		'''
	print(inputDict)
	source = inputDict['source']
	if source =='ASOS':
		station = inputDict['stationASOS']
		parameter = inputDict['weatherParameterASOS']
		data = weather.pullAsos(inputDict['year'], station, parameter)
	elif source == 'USCRN':
		station = inputDict['stationUSCRN']
		parameter = inputDict['weatherParameterUSCRN']
		data = weather.pullUscrn(inputDict['year'], station, parameter)
	elif source == 'darkSky':
		lat = inputDict['LatInput']
		lon = inputDict['LonInput']
		parameter = inputDict['weatherParameterdarkSky']
		data = weather.pullDarksky(inputDict['year'], lat, lon, parameter, units='si')
	elif source == 'NRSDB':
		nsrdbkey = 'rnvNJxNENljf60SBKGxkGVwkXls4IAKs1M8uZl56'
		latitude = float(inputDict['LatInput'])
		longitude = float(inputDict['LonInput'])
		year = inputDict['year']
		param = inputDict['weatherParameterNRSDB']
		data = weather.get_nrsdb_data('psm', longitude, latitude, year, nsrdbkey, interval=60)
		print(data)
		#Data must be a list. Extract correct column from returned pandas df, return this column as array of int
		data = list(data[param].values[3:].astype(float))
		print(data)
	elif source in ['easySolarGhi', 'easySolarDhi','easySolarDni'] :
		print("EASYSOLAR FOUND")
		station = inputDict['easySolarStation']
		year = inputDict['year']
		data = easySolar.get_synth_dhi_dni(station, year)
		if source == 'easySolarDhi':
			data = list([i[0] for i in data])
			print(data)
		elif source == 'easySolarGhi':
			data = list([i[1] for i in data])
			print(data)
		elif source == 'easySolarDni':
			data = list([i[2] for i in data])
			print(data)
	elif source == 'tmy3':
		param = inputDict['weatherParameterTmy3']
		lat = float(inputDict['LatInput'])
		lon = float(inputDict['LonInput'])
		year = int(inputDict['year'])
		data = weather.tmy3_pull(weather.nearest_tmy3_station(lat, lon))
		#Now get data for the year in question
		data = data.loc[data['year']==year]
		#Extract param from data, convert to int, and pass in values not pandas series
		data = list(data[param].astype(float).values)
	elif source == 'surfrad':
		year = int(inputDict['year'])
		param = inputDict['weatherParameterSurfrad']
		site = inputDict['surfradSite']
		print(year, param, site)
		data = weather.get_radiation_data('surfrad', site, year)
		data = list(data[param].values.astype(float))
		print(data)
	# station = inputDict['stationASOS'] if source == 'ASOS' else inputDict['stationUSCRN']
	# parameter = inputDict['weatherParameterASOS'] if source == 'ASOS' else inputDict['weatherParameterUSCRN']
	# inputs = [inputDict['year'], station, parameter]
	# data = weather.pullAsos(*inputs) if source == 'ASOS' else weather.pullUscrn(*inputs)
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

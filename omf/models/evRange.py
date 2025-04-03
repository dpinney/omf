'''Display up-to-date map of public EV charging locations with an editable EV range radius at each location.'''
import random, requests
from pathlib import Path
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
tooltip = 'Display up-to-date map of public EV charging locations with an editable EV range radius at each location.'
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

class NRELAltFuelStationsAPIError(Exception):
	'''Raised when the API call to NREL fails.'''
	pass

class FuelStationCacheError(Exception):
	'''Raised when there is a problem reading or writing the cache file.'''
	pass

def get_randomized_api_key():
	'''returns a random API key'''
	REOPT_API_KEYS = [
		'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9',
		'Y8GMAFsqcPtxhjIa1qfNj5ILxN5DH5cjV3i6BeNE',
		'etg8hytwTYRf4CD0c4Vl9U7ACEQnQg6HV2Jf4E5W',
		'BNFaSCCwz5WkauwJe89Bn8FZldkcyda7bNwDK1ic',
		'L2e5lfH2VDvEm2WOh0dJmzQaehORDT8CfCotaOcf',
		'08USmh2H2cOeAuQ3sCCLgzd30giHjfkhvsicUPPf'
	]
	return random.choice(REOPT_API_KEYS)

def filter_fuel_stations(full_results):
	keys_to_keep = ['station_name', 'latitude', 'longitude']
	# keys_to_keep = ['id', 'station_name', 'latitude', 'longitude', 'street_address', 'city', 'state', 'zip']
	# keys_to_keep = ['id', 'station_name', 'latitude', 'longitude', 'street_address', 'city', 'state', 'zip', 'ev_network', 'ev_connector_types', 'ev_pricing', 'maximum_vehicle_class', 'ev_level1_evse_num', 'ev_level2_evse_num', 'ev_dc_fast_num', 'access_days_time', 'station_phone', 'date_last_confirmed']
	filtered = []
	for station in full_results:
		filtered_station = { key: station.get(key) for key in keys_to_keep }
		filtered.append(filtered_station)
	return filtered

def call_api():
	api_key = get_randomized_api_key()
	url = 'https://developer.nrel.gov/api/alt-fuel-stations/v1.json'
	params = {
		# 'limit': 50,
        'api_key': api_key,
		'access':'public',
		'fuel_type':'ELEC',
		'ev_network': 'all',
		'ev_charging_level': 'all',
		'ev_connector_type': 'all'
    }
	response = requests.get(url, params=params)
	if response.ok:
		data = response.json()
		fuel_stations = data.get('fuel_stations', [])
		# return fuel_stations
		return filter_fuel_stations(fuel_stations)
	else:
		raise NRELAltFuelStationsAPIError(f'API call failed with status code {response.status_code}: {response.text}')
	
def get_cache_filepath():
    app_root = Path(__neoMetaModel__._omfDir).resolve()
    return app_root / 'static' / 'ev_fueling_stations.json'

def get_cached_results():
	cache_file = get_cache_filepath()
	try:
		if cache_file.exists():
			return json.loads(cache_file.read_text())
		else:
			raise FuelStationCacheError('Cache file does not exist.')
	except Exception as e:
		raise FuelStationCacheError(f'Error reading cached results: {e}')

def cache_new_results(results):
	cache_file = get_cache_filepath()
	cache_file.parent.mkdir(parents=True, exist_ok=True)
	try:
		with tempfile.NamedTemporaryFile('w', dir=str(cache_file.parent), delete=False, encoding='utf-8') as tmp_file:
			json.dump(results, tmp_file)
			temp_path = Path(tmp_file.name)
		temp_path.replace(cache_file)
	except Exception as e:
		raise FuelStationCacheError(f'Failed to cache new results: {e}')
	
def work(modelDir, inputDict):
	outData = {}
	refresh_requested = inputDict.get('refreshCachedResults', False)
	if refresh_requested:
		try:
			results = call_api()
			cache_new_results(results)
			update_message = 'Cache updated successfully.'
		except Exception as e:
			results = get_cached_results()
			update_message = f'Cache update failed: {e}'
	else:
		try:
			results = get_cached_results()
			update_message = 'Using cached results.'
		except Exception as e:
			results = []
			update_message = f'Error retrieving cached results: {e}'
	outData['initial_range_miles'] = inputDict.get('initialRangeMiles', 100)
	outData['fuel_stations'] = results
	outData['cache_message'] = update_message
	return outData
	
def new(modelDir):
	defaultInputs = {
		'modelType': modelName,
		'initialRangeMiles': 100
    }
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

def _tests():
    # Location
	modelLoc = Path(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		pass # No previous test results.
	# Create New.
	new(modelLoc)
	# Pre-run.
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)
	
if __name__ == '__main__':
	_tests()
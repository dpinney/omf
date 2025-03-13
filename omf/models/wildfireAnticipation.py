'''Return wildfire risk for custom geographic regions in the US.'''
import shutil
from pathlib import Path
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.weather import getSubGridData
from shapely.geometry import shape, Point
from shapely.ops import unary_union

# Model metadata:
tooltip = 'Return wildfire risk for custom geographic regions in the US.'
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

def get_subgrid_parameters(geojson_input, resolution=10):
	'''
	Computes the bounding box and subgrid parameters from a GeoJSON input.
	Returns: center_lat, center_lon, distance_lat, distance_lon, resolutionSquare.
	'''
	geojson = json.loads(geojson_input)
	geometries = []
	# Handle different GeoJSON types: FeatureCollection, Feature, or a raw geometry.
	if geojson.get('type') == 'FeatureCollection':
		for feature in geojson['features']:
			geometries.append(shape(feature['geometry']))
	elif geojson.get('type') == 'Feature':
		geometries.append(shape(geojson['geometry']))
	else:
		geometries.append(shape(geojson))
	# Combine geometries into one shape to compute the overall bounding box.
	combined_geom = unary_union(geometries)
	min_lon, min_lat, max_lon, max_lat = combined_geom.bounds
	center_lat = (min_lat + max_lat) / 2.0
	center_lon = (min_lon + max_lon) / 2.0
	# The distances represent half the total extent.
	distance_lat = (max_lat - center_lat)
	distance_lon = (max_lon - center_lon)
	return center_lat, center_lon, distance_lat, distance_lon, resolution

def process_fire_risk(api_results, fire_risk_mapping):
	'''
	Process API results and extract the maximum risk value based on the provided risk mapping.
    '''
	# Initialize risk as lowest (0).
	max_numeric_risk = 0
	
	# Extract parameters from the API result.
	parameters = api_results.get('dwml', {}).get('data', {}).get('parameters', [])
	for param in parameters:
		# Each grid cell (or point) should include a 'fire-weather' key
		fire_weather_list = param.get('fire-weather', [])
		for risk_obj in fire_weather_list:
			for risk_str in risk_obj.get('value', []):
				numeric = fire_risk_mapping.get(risk_str, 0)
				if numeric > max_numeric_risk:
					max_numeric_risk = numeric
	# Reverse mapping: numeric -> risk string.
	rev_mapping = {v: k for k, v in fire_risk_mapping.items()}
	return rev_mapping.get(max_numeric_risk, "Unknown")

def process_risk(api_results, mapping, risk_type):
	'''
	Process API results to extract a risk value for a given risk type. 
	risk_type is a string expected to appear in the risk object's '@type' attribute. 
	mapping is a dictionary mapping risk strings to numeric values.
	Returns the risk string corresponding to the highest numeric value found. 
	'''
	max_numeric = 0
	parameters = api_results.get('dwml', {}).get('data', {}).get('parameters', [])
	for param in parameters:
		fire_weather_list = param.get('fire-weather', [])
		for risk_obj in fire_weather_list:
			if risk_obj.get('@type', '').lower().find(risk_type.lower()) != -1:
				for risk_str in risk_obj.get('value', []):
					numeric = mapping.get(risk_str, 0)
					if numeric > max_numeric:
						max_numeric = numeric
	rev_mapping = {v: k for k, v in mapping.items()}
	return rev_mapping.get(max_numeric, 'Unknown')

def work(modelDir, inputDict):
	outData = {}
	geojson_input = inputDict.get('geojsonInput')
	if not geojson_input:
		outData['fire_risk_map'] = {}
		return outData
	
	fire_risk_mapping = {
		'No Areas': 0,
		'Elevated Areas': 1,
		'Critical Areas': 2
	}

	thunderstorm_risk_mapping = {
		'Isolated': 0,
		'Scattered': 1,
	}

	geojson = json.loads(geojson_input)
	# Handle FeatureCollection, Feature, or raw geometry.
	if geojson.get('type') == 'FeatureCollection':
		features = [feature for feature in geojson['features']]
	elif geojson.get('type') == 'Feature':
		features = [geojson]
	else:
		features = [{'geometry': geojson}]
	
	fire_risk_from_map, thunderstorm_risk_from_map = {}, {}
	for feature in features:
		shape_id = feature.get('properties', {}).get('shape_id')
		geometry = shape(feature['geometry'])
		min_lon, min_lat, max_lon, max_lat = geometry.bounds
		center_lat = (min_lat + max_lat) / 2.0
		center_lon = (min_lon + max_lon) / 2.0
		# Use half the height and width as distances.
		distance_lat = (max_lat - center_lat)
		distance_lon = (max_lon - center_lon)
		resolution = 0.1
		api_results = getSubGridData(center_lat, center_lon, distance_lat, distance_lon, resolution)
		fire_risk = process_risk(api_results, fire_risk_mapping, risk_type="temperature, wind, and relative humidity")
		thunderstorm_risk = process_risk(api_results, thunderstorm_risk_mapping, risk_type="dry thunderstorms")
		fire_risk_from_map[shape_id] = fire_risk
		thunderstorm_risk_from_map[shape_id] = thunderstorm_risk
	outData['fire_risk_from_map'] = fire_risk_from_map
	outData['thunderstorm_risk_from_map'] = thunderstorm_risk_from_map

	return outData

def new(modelDir):
	defaultInputs = {
		'modelType': modelName
    }
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

def _tests():
    # Location
	modelLoc = Path(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
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
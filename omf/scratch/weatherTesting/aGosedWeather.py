''' Pull down historical weather data, put it on a SCADA-calibrated feeder. '''


import json, csv, os, re
from datetime import datetime, timedelta
import requests
from omf import feeder, weather
from omf.solvers.gridlabd import runInFilesystem
from weather_data_type import WeatherDataType, get_first_valid_row, extract_data, merge_hourly_subhourly, celsius_to_fahrenheit, watts_per_meter_sq_to_watts_per_ft_sq


"""
Get data from a USCRN station in a given year, where data consists of air temperature, relative humidity, solar radiation, and windspeed.
We derive 'solar direct' and 'solar diffuse' from the solar radiation data. Hourly windspeed is not given in the hourly dataset, so it must be
calculated from the 5-minute dataset.
- A quality control flag values:
	- 0: good data
	- 1: field-length overflow
	- 3: erronous data
	- However, there are examples of 0 flag values with -9999 data values, which is obviously incorrect
- For hourly data that is indexed from 0:
	- If T_CALC (index: 8) has a value of -9999.0, that datum should be discarded. 
	- If SOLARAD (index: 13) has a value of -99999, that datum should be discarded.
	- If SOLARD_FLAG (index: 14) has a value of 1 or 3, that datum should be discarded
	- If RH_HR_AVG (index: 26) has a value of -9999, that datum should be discarded. This data is erronous most of the time!
	- If RH_HR_AVG_FLAG (index: 27) has a value of 1 or 3, that datum should be discarded
- For sub-hourly data that is indexed from 0:
	- If WIND_1_5 (index: 21) has a value of -99.00, that datum should be discarded.
	- If WIND_FLAG (index: 22) has a value of 1 or 3, that datum should be discarded.
"""


def get_USCRN_data(year, station, frequency):
	# type: (int, str, str) -> list
	""" Get a .txt file from the USCRN server and return the data as a list of lists. """
	url = "https://www1.ncdc.noaa.gov/pub/data/uscrn/products/"
	if frequency == "hourly":
		url += "hourly02/{year}/CRNH0203-{year}-{station}.txt".format(year=year, station=station)
	elif frequency == "subhourly":
		url += "subhourly01/{year}/CRNS0101-05-{year}-{station}.txt".format(year=year, station=station)
	else:
		raise Exception("Please specify a 'hourly' or 'subhourly' frequency.")
	r = requests.get(url)
	if r.status_code == 404:
		return
	return [re.split("\s+", line) for line in r.text.splitlines()]


def attachHistoricalWeather(omd_path, year, station):
	# type: (str, str, str) -> None
	"""
	- Write a csv with columns: datetime, temperature, wind speed, humidity, solar_dir, solar_diff, solar_global
	- Calibrate the omd file with the weather data
	"""
	assert type(year) is int
	assert type(omd_path) is str or type(omd_path) is unicode
	assert type(station) is str or type(omd_path) is unicode
	# Get temperature, humidity, solar_global for the year and station
	hourly_rows = get_USCRN_data(year, station, "hourly")
	if hourly_rows is None:
		raise Exception("Failed to get USCRN data")
	temperature = WeatherDataType(8, -9999.0, flag_index=None, transformation_function=lambda x: round(celsius_to_fahrenheit(x), 1))
	humidity = WeatherDataType(26, -9999, flag_index=27, transformation_function=lambda x: round((x / float(100)), 2))
	solar_dir = WeatherDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.75, 0)))
	solar_diff = WeatherDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.25, 0)))
	solar_global = WeatherDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x), 0)))
	data_types = [temperature, humidity, solar_dir, solar_diff, solar_global]
	first_valid_row = get_first_valid_row(hourly_rows, data_types)
	last_valid_row = get_first_valid_row(hourly_rows, data_types, reverse=True)
	hourly_processed_data = extract_data(first_valid_row, last_valid_row, hourly_rows, data_types, is_subhourly_data=False)
	# Get wind speed for the year and station
	subhourly_rows = get_USCRN_data(year, station, "subhourly")
	if subhourly_rows is None:
		raise Exception("Failed to get USCRN data")
	wind_speed = WeatherDataType(21, -99.00, flag_index=22, transformation_function=lambda x: round(x, 2))
	data_types = [wind_speed]
	first_valid_row = get_first_valid_row(subhourly_rows, data_types)
	last_valid_row = get_first_valid_row(subhourly_rows, data_types, reverse=True)
	subhourly_processed_data = extract_data(first_valid_row, last_valid_row, subhourly_rows, data_types, is_subhourly_data=True)
	# Merge the two datasets
	merged = merge_hourly_subhourly(hourly_processed_data, subhourly_processed_data, 1)
	#csv_path = os.path.join(os.path.dirname(omd_path), "uscrn-weather-data.csv")
	csv_path = os.path.join(os.path.dirname(omd_path), "monday.csv")
	write_csv(merged, csv_path)
	# Calibrate the feeder
	start_date = datetime(year, 1, 1)
	calibrate_omd(start_date, omd_path, csv_path)


def write_csv(data, filepath):
	with open(filepath, 'w') as f:
		writer = csv.writer(f)
		writer.writerows(data)


def calibrate_omd(start_date, omd_path, csv_path):
	# type: (datetime, str, str) -> None
	with open(omd_path, 'r') as f:
		omd = json.load(f)
	tree = omd["tree"]
	# Delete all climate objects from the feeder, then reinsert new climate objects
	reader_name = 'weatherReader'
	climate_name = 'MyClimate'
	for key in tree.keys():
		obName = tree[key].get('name','')
		obType = tree[key].get('object','')
		if obName in [reader_name, climate_name] or obType is 'climate':
			del tree[key]
	oldMax = feeder.getMaxKey(tree)
	tree[oldMax + 1] = {'omftype':'module', 'argument':'tape'}
	tree[oldMax + 2] = {'omftype':'module', 'argument':'climate'}
	csv_name = os.path.basename(csv_path)
	tree[oldMax + 3] = {'object':'csv_reader', 'name':reader_name, 'filename':csv_name}
	tree[oldMax + 4] = {'object':'climate', 'name':climate_name, 'reader': reader_name, 'tmyfile':csv_name}
	# Set the time correctly. Modify certain objects in the feeder (e.g. recorder and clock)
	feeder.adjustTime(tree, 240, 'hours', '{}-{}-{}'.format(start_date.year, start_date.month, start_date.day)) 
	omd["tree"] = tree
	# Add the weather attachment
	with open(csv_path, 'r') as f:
		weatherString = f.read()
	if omd.get("attachments") is None:
		omd["attachments"] = {}
	omd['attachments']['weatheryearDCA.csv'] = weatherString
	with open(omd_path, 'w') as f:
		json.dump(omd, f, indent=4)


def test_gridlabd_weather_sim(year, station):
	""" GridLAB-D intermitently fails """
	glm_path = os.path.join(os.path.dirname(__file__), "IEEE_quickhouse.glm")
	tree = feeder.parse(glm_path)
	omd = {}
	omd["tree"] = tree
	omd_path = os.path.join(os.path.dirname(__file__), "IEEE_quickhouse.omd")
	with open(omd_path, 'w') as f:
		json.dump(omd, f, indent=4)
	attachHistoricalWeather(omd_path, year, station)
	with open(omd_path) as f:
		calibrated_tree = json.load(f)["tree"]
	# Run here to test GridLAB_D
	# The output is NOT a feeder. It's some data in JSON format. This function call does NOT modify myTree.
	rawOut = runInFilesystem(calibrated_tree, attachments=[], keepFiles=True, workDir=os.path.dirname(__file__), glmName='outFile.glm')
	print(rawOut)


"""
def other_test(tree, CSV_NAME):
	omd = {}
	omd["tree"] = tree
	with open(CSV_NAME,'r') as weatherFile:
		weatherString = weatherFile.read()
	omd['attachments']['weatheryearDCA.csv'] = weatherString
	filepath = os.path.join(os.path.dirname(__file__), "new-calibrated-feeder.omd")
	with open(filepath, 'w') as f:
		f.write(str(omd))
	#try: os.remove('./Orville Tree Pond Calibrated With Weather.json')
	#except: pass
	#with open('./Orville Tree Pond Calibrated With Weather.json', 'w') as outFile:
	#	json.dump(outJson, outFile, indent=4)
"""


if __name__ == "__main__":
	year = 2018
	station = "AK_Kenai_29_ENE"
	#start_date = datetime(year, 1, 1)
	#calibrate_omd(start_date, "/Users/austinchang/pycharm/omf/omf/scratch/weatherTesting/IEEE_quickhouse.omd", "/Users/austinchang/pycharm/omf/omf/scratch/weatherTesting/uscrn-weather-data.csv")
	test_gridlabd_weather_sim(year, station)
''' Pull down historical weather data, put it on a SCADA-calibrated feeder. '''


import json, csv, os, re
from datetime import datetime, timedelta
import requests
from omf import feeder, weather
from omf.solvers.gridlabd import runInFilesystem
from weather_data_type import WeatherDataType, get_first_valid_row, extract_data, merge_hourly_subhourly, celsius_to_fahrenheit, watts_per_meter_sq_to_watts_per_ft_sq


"""
12 measurements per hour * 24 hours per day * 365 days per year = 105120 sub-hourly measurements per year per station. 
I should take the mean of 12 wind speed measurements, so 0005 - 0100.

24 hours per daty * 365 days per year = 8760 hourly measurements per year per station
"""

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


def attachHistoricalWeather(omd_path, year, station):
	# type: (str, str, str) -> None
	# Get temperature, humidity, solar_global for the year + station
	hourly_rows = get_USCRN_data(year, station, "hourly")
	temperature = WeatherDataType(8, -9999.0, flag_index=None, transformation_function=lambda x: round(celsius_to_fahrenheit(x), 1))
	humidity = WeatherDataType(26, -9999, flag_index=27, transformation_function=lambda x: round((x / float(100)), 2))
	solar_dir = WeatherDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.75, 0)))
	solar_diff = WeatherDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.25, 0)))
	solar_global = WeatherDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x), 0)))
	data_types = [temperature, humidity, solar_dir, solar_diff, solar_global]
	first_valid_row = get_first_valid_row(hourly_rows, data_types)
	last_valid_row = get_first_valid_row(hourly_rows, data_types, reverse=True)
	hourly_processed_data = extract_data(first_valid_row, last_valid_row, hourly_rows, data_types, is_subhourly_data=False)
	###
	#write_rows_to_csv(hourly_processed_data, "{}-{}-hourly.csv".format(year, station))
	###	
	# Get wind speed for the year + station
	subhourly_rows = get_USCRN_data(year, station, "subhourly")
	wind_speed = WeatherDataType(21, -99.00, flag_index=22, transformation_function=lambda x: round(x, 2))
	data_types = [wind_speed]
	first_valid_row = get_first_valid_row(subhourly_rows, data_types)
	last_valid_row = get_first_valid_row(subhourly_rows, data_types, reverse=True)
	subhourly_processed_data = extract_data(first_valid_row, last_valid_row, subhourly_rows, data_types, is_subhourly_data=True)
	###
	#write_rows_to_csv(subhourly_processed_data, "{}-{}-subhourly.csv".format(year, station))
	###
	merged = merge_hourly_subhourly(hourly_processed_data, subhourly_processed_data, 1)
	csv_filepath = os.path.join(os.path.dirname(omd_path), "uscrn-weather-data.csv")


def write_rows_to_csv(data, filename):
	filepath = os.path.join(os.path.dirname(__file__), filename)
	with open(filepath, 'w') as f:
		writer = csv.writer(f)
		writer.writerows(data)


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


def _write_USCRN_csv(csv_filepath, data):
	# type: (str, list) -> None
	""" Write the data, which is a list of dicts, to the csv filepath. """
	with open(csv_filepath, 'w') as f:
		writer = csv.writer(f)
		writer.writerow("datetime", "temperature", "wind_speed", "humidity", "solar_dir", "solar_diff", "solar_global")
		writer.writerows(data)



def write_weather_csv(INIT_TIME, LOCATION, CSV_NAME):
	""" Make a weather file. """
	data_temp = weather.pullUscrn(str(INIT_TIME.year), LOCATION, 'T_CALC')
	data_hum = weather.pullUscrn(str(INIT_TIME.year), LOCATION, 'RH_HR_AVG')
	data_solar = weather.pullUscrn(str(INIT_TIME.year), LOCATION, 'SOLARAD')
	data_full = []
	for i in range(8760): # 24 hours per day * 365 days per year = 8760 measurements for a USCRN station
		step_time = INIT_TIME + timedelta(hours=i)
		row = [
			'{}:{}:{}:{}:{}'.format(step_time.month, step_time.day, step_time.hour, step_time.minute, step_time.second),
			# str(step_time), 
			data_temp[i],
			0.0, # TODO: get a windspeed
			data_hum[i],
			data_solar[i] * 0.75, # TODO: better solar direct
			data_solar[i] * 0.25, # TODO: better solar diffuse
			data_solar[i]
		]
		data_full.append(row)
	# Write USCRN data to CSV
	with open(CSV_NAME,'w') as wFile:
		weather_writer = csv.writer(wFile)
		weather_writer.writerow(['temperature','wind_speed','humidity','solar_dir','solar_diff','solar_global'])
		for row in data_full:
			weather_writer.writerow(row)


def write_tree_to_file(tree, filename):
	filepath = os.path.join(os.path.dirname(__file__), filename)
	with open(filepath, 'w') as f:
		json.dump(tree, f, indent=4)


def write_omd(tree, csv_filename):
	# type: (dict, str) -> None
	""" An .omd is more than just a tree. It has attachments """
	omd = {}
	omd["tree"] = tree
	with open(csv_filename, 'r') as weather_csv:
		weatherString = weather_csv.read()
	omd['attachments']['weatheryearDCA.csv'] = weatherString
	filepath = os.path.join(os.path.dirname(__file__), "new-calibrated-feeder.omd")
	with open(filepath, 'w') as f:
		f.write(str(omd))
	#try: os.remove('./Orville Tree Pond Calibrated With Weather.json')
	#except: pass
	#with open('./Orville Tree Pond Calibrated With Weather.json', 'w') as outFile:
	#	json.dump(outJson, outFile, indent=4)


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
	omd['attachments']['weatheryearDCA.csv'] = weatherString
	with open(omd_path, 'w') as f:
		f.write(str(omd))


def test_gridlabd_weather_sim():
	# Globals
	INIT_TIME = datetime(2017, 1, 1, 0, 0, 0)
	CSV_PATH = os.path.join(os.path.dirname(__file__), )
	CSV_NAME = 'weatherNewKy.csv'
	LOCATION = 'KY_Versailles_3_NNW'
	GLM_PATH = 'IEEE_quickhouse.glm'

	#write_weather_csv(INIT_TIME, LOCATION, CSV_NAME)

	# Get an uncalibrated feeder from a .glm file
	myTree = feeder.parse(GLM_PATH) 
	write_tree_to_file(myTree, "uncalibrated-tree.json")
	# Delete all climate objects from the feeder, then reinsert new climate objects
	reader_name = 'weatherReader'
	climate_name = 'MyClimate'
	for key in myTree.keys():
		obName = myTree[key].get('name','')
		obType = myTree[key].get('object','')
		if obName in [reader_name, climate_name] or obType is 'climate':
			del myTree[key]
	oldMax = feeder.getMaxKey(myTree)
	myTree[oldMax + 1] = {'omftype':'module', 'argument':'tape'}
	myTree[oldMax + 2] = {'omftype':'module', 'argument':'climate'}
	myTree[oldMax + 3] = {'object':'csv_reader', 'name':reader_name, 'filename':CSV_NAME}
	myTree[oldMax + 4] = {'object':'climate', 'name':climate_name, 'reader': reader_name, 'tmyfile':CSV_NAME}
	# Set the time correctly. Modify certain objects in the feeder (e.g. recorder and clock)
	feeder.adjustTime(myTree, 240, 'hours', '{}-{}-{}'.format(INIT_TIME.year, INIT_TIME.month, INIT_TIME.day)) 
	write_tree_to_file(myTree, "calibrated-tree.json")
	# Run here to test GridLAB_D
	# The output is NOT a feeder. It's some data in JSON format. This function call does NOT modify myTree.
	rawOut = runInFilesystem(myTree, attachments=[], keepFiles=True, workDir='.', glmName='./outFile.glm') # Use the modified tree to run a simulation in gridlabd
	print(rawOut)

"""
def create_omd(tree, CSV_NAME):
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
	attachHistoricalWeather("", 2018, "AK_Kenai_29_ENE")
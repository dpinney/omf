''' Pull down historical weather data, put it on a SCADA-calibrated feeder. '''


import sys, json, csv, os, re
from datetime import datetime, timedelta
import requests
from matplotlib import pyplot as plt
from omf import feeder, weather
from omf.solvers.gridlabd import runInFilesystem


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
	- If RH_HR_AVG (index: 26) has a value of -9999, that datum should be discarded.
	- If RH_HR_AVG_FLAG (index: 27) has a value of 1 or 3, that datum should be discarded
- For sub-hourly data that is indexed from 0:
	- If WIND_1_5 (index: 21) has a value of -99.00, that datum should be discarded.
	- If WIND_FLAG (index: 22) has a value of 1 or 3, that datum should be discarded.
"""


def attachHistoricalWeather(omdPath, initYear, location):
	#TODO: implement.
	# What should the initDateTime be? Whatever the user decides. We only deal in years apparently.
	# What should the location be? Whatever the user decides. How will the user know the location?
	# What hourly measurements do we want? Just 1) air temperature, 2) windspeed, 3) relative humidity, and 4) solar
	#return None #Output is mutation of the OMD? Or new OMD?
	hourly_data = _get_USCRN_data(initYear, location, "hourly")
	hourly_data_types = {
		"T_CALC": 8,
		"SOLARAD": 13,
		"RH_HR_AVG": 26,
	}
	hourly_data = _select_data_types(hourly_data, hourly_data_types, initYear)
	#_add_derived_data(hourly_data, )

	subhourly_data = _get_USCRN_data(initYear, location, "subhourly")






def _get_USCRN_data(year, station, frequency):
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
	return [re.split("\s+", line) for line in r.text.splitlines()]


def _select_data_types(data, data_types, year):
	# type: (list, dict, int) -> list
	""" Get data from specific columns from the original list and return the selected data in a new list of dicts. """
	selected = []
	for line in data:
		sub_select = {}
		for key in data_types:
			sub_select[key] = line[data_types[key]]
		selected.append(sub_select)
	return selected


def _filter_data():
	pass


def _add_derived_data(row, dt):
	# type: (dict, datetime) -> list
	"""
	Get a dict and add the following key-value pairs:
	1) a GridLAB-D-format time measurement
		- The data pulled from the USCRN hourly dataset should contain (24 * 365 = 8760) measurements.
	2) solar direct
	3) solar diffuse
	"""
	start_date = datetime(year, 1, 1, 0, 0, 0)
	idx = 0
	for row in data:
		step_time = start_date + timedelta(hours=idx)
		row["datetime"] = "{month}:{day}:{hour}:{minute}:{second}".format(month=step_time.month, day=step_time.day, hour=step_time.hour, minute=step_time.minute, second=step_time.second)
		row["solar_dir"] = row["solar_global"] * 0.75
		row["solar_diff"] = row["solar_global"] * 0.25
		idx += 1


def _write_USCRN_csv(csv_filepath, data):
	# type: (str, list) -> None
	""" Write the data, which is a list of dicts, to the csv filepath. """
	with open(csv_filepath, 'w') as f:
		writer = csv.writer(f)
		writer.writerow("datetime", "temperature", "wind_speed", "humidity", "solar_dir", "solar_diff", "solar_global")
		writer.writerows(data)







def _filter_flagged_data(data, data_idx, flag_idx, invalid_data_value, valid_flag_value):
	pass


def _filter_unflagged_data(data, data_types):
	# type: (list, dict) -> list
	# {T_CALC: {index: <index>, invalid_value: <invalid value>, last_valid_value: <last valid value>}}

	# {T_CALC: (index, invalid value, last valid value)}
	# {T_CALC: (index, <invalid value>)} -> (T_CALC, (index, <invalid value>))
	#data_types = data_types.items()

	for row in data:
		for key in data_types:
			if row[data_types[key][0]] == data_types[key][1]:
				# bad value
				pass
			else:
				pass


def _filter_unflagged_data(data, data_idx, invalid_data_value):
	# type: (list, int, int) -> 
	pass

	url = "https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/{year}/CRNH0203-{year}-{station}.txt".format(year=year, station=station)
	r = requests.get(url)
	lines = r.text.splitlines()
	for line in lines:
		hourly_data = re.split("\s+", line)
		filtered_hourly_data = filter_list(hourly_data, 8, 13, 14, 26, 27)


	#[line.split() for line in r.text.splitlines()]

	url = "https://www1.ncdc.noaa.gov/pub/data/uscrn/products/subhourly01/{year}/CRNS0101-05-{year}-{station}.txt".format(year=year, station=station)
	r = requests.get(url)
	rows = r.text.splitlines()




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


def run_example():
	# Globals
	INIT_TIME = datetime(2017,1,1,0,0,0)
	CSV_NAME = 'weatherNewKy.csv'
	LOCATION = 'KY_Versailles_3_NNW'
	GLM_PATH = 'IEEE_quickhouse.glm'
	write_weather_csv(INIT_TIME, LOCATION, CSV_NAME)
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
	#rawOut = runInFilesystem(myTree, attachments=[], keepFiles=True, workDir='.', glmName='./outFile.glm') # Use the modified tree to run a simulation in gridlabd
	#print(rawOut)


def create_omd(tree, CSV_NAME):
	""" An .omd is more than just a tree. It has attachments """
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


if __name__ == "__main__":
	#run_example()
	#pullUscrn(2018, "AK_Ivotuk_1_NNE")
	line = "63838 20170101 0100 20161231 2000  2.422  -84.75   38.09     4.4     4.1     4.4     3.9     0.0      0 0      0 0      0 0 C     3.7 0     3.8 0     3.5 0    93 0   0.340   0.341   0.343   0.324   0.410     4.5     4.6     5.3     7.2     9.2"
	my_list = re.split("\s+", line)
	print(my_list)
	new_list = filter_list(my_list, 8, 13, 14, 26, 27)
	print(new_list)
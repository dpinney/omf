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
	- If RH_HR_AVG (index: 26) has a value of -9999, that datum should be discarded. This data is erronous most of the time!
	- If RH_HR_AVG_FLAG (index: 27) has a value of 1 or 3, that datum should be discarded
- For sub-hourly data that is indexed from 0:
	- If WIND_1_5 (index: 21) has a value of -99.00, that datum should be discarded.
	- If WIND_FLAG (index: 22) has a value of 1 or 3, that datum should be discarded.
"""


def attachHistoricalWeather(omdPath, year, station):
	# type: (str, str, str) -> None
	rows = get_USCRN_data(year, station, "hourly")
	#datetime
	temperature = WeatherDataType(8, -9999.0, lambda x: round(celsius_to_fahrenheit(x), 1))
	#wind_speed
	humidity = WeatherDataType(26, -9999, 27, lambda x: round((x / float(100)), 2))
	solar_dir = WeatherDataType(13, -99999, 14, lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.75, 0)))
	solar_diff = WeatherDataType(13, -99999, 14, lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.25, 0)))
	solar_global = WeatherDataType(13, -99999, 14, lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x), 0)))
	data_types = [temperature, humidity, solar_dir, solar_diff, solar_global]

	get_first_valid_row(rows, data_types)

	processed_data = extract_data(x, x, rows, x, is_subhourly_data=False)






	hourly_data = _get_USCRN_data(initYear, location, "hourly")
	hourly_data_types = {
		"T_CALC": 8,
		"SOLARAD": 13,
		"RH_HR_AVG": 26,
	}
	hourly_data = _select_data_types(hourly_data, hourly_data_types, initYear)
	#_add_derived_data(hourly_data, )

	subhourly_data = _get_USCRN_data(initYear, location, "subhourly")


def str_to_num(data):
	if type(data) is str:
		if get_precision(data) == 0:
			return int(data)
		return float(data)
	return data


def get_precision(data):
	# type: (str) -> int
	if type(data) is not str:
		data = str(data)
	if data.find(".") == -1:
		return 0
	return len(re.split("[.]", data)[1])


def watts_per_meter_sq_to_watts_per_ft_sq(w_m_sq):
	# type: (int) -> float
	if type(w_m_sq) is str:
		w_m_sq = str_to_num(w_m_sq)
	return (w_m_sq / ((1 / .3048) ** 2))


def celsius_to_fahrenheit(c):
	if type(c) is str:
		c = str_to_num(c)
	return c * 9 / float(5) + 32


class WeatherDataType(object):


	def __init__(self, data_index, missing_data_value, flag_index=None, transformation_function=None):
		# type: (int, int/float, int, function) -> None
		self.data_index = int(data_index)
		if type(missing_data_value) is str:
			missing_data_value = str_to_num(missing_data_value)
		self.missing_data_value = missing_data_value
		if flag_index is not None:
			flag_index = int(flag_index)
		self.flag_index = flag_index
		self.transformation_function = transformation_function


	def validate(self, row):
		# type: (list) -> bool
		""" Return True if the row has a valid data value for this WeatherDataType, otherwise False """
		if str_to_num(row[self.data_index]) == self.missing_data_value:
			return False
		if self.flag_index is not None and str_to_num(row[self.flag_index]) != 0:
			return False
		return True


	def get_next_valid_value(self, rows, start_row_idx):
		# type: (list, int) -> tuple
		""" Return the closest valid value in the column of the data for this DataType and the row index at which it was found. """
		for i in range(start_row_idx, len(rows)):
			row = rows[i]
			if self.validate(row):
				return (i, str_to_num(row[self.data_index]))
		return (None, None)


	def correct_column(self, rows, start_row_idx, end_row_idx, initial_val, final_val):
		# type: (list, int, int, float, float) -> None
		"""
		Modify the data to interpolate between the most recent valid value and the closest future valid value.
		- start_row_idx and end_row_idx are both inclusive of modification
		- need to maintain the same precision as the original measurement
		"""
		start_row_idx = int(start_row_idx)
		end_row_idx = int(end_row_idx)
		if type(initial_val) is str:
			initial_val = str_to_num(initial_val)
		if type(final_val) is str:
			final_val = str_to_num(final_val)
		precision = get_precision(initial_val)
		increment = (1.0 * final_val - initial_val) / (end_row_idx - start_row_idx + 2)
		count = 1
		for i in range(start_row_idx, end_row_idx + 1):
			row = rows[i]
			val = round((initial_val + increment * count), precision)
			if precision == 0:
				val = int(val)
			row[self.data_index] = val
			if self.flag_index is not None:
				row[self.flag_index] = 0
			count += 1


	def get_value(self, row):
		# type: (list) -> float
		value = row[self.data_index]
		if type(value) is str:
			value = str_to_num(value)
		if self.transformation_function is not None:
			return self.transformation_function(value)
		return value


def get_first_valid_row(rows, data_types, reverse=False):
	# type: (list, list, bool) -> list
	"""
	Iterate over rows and return the first row that has all valid data for the given WeatherDataTypes. If reversed is False, iterate from the earliest
	to the latest time in the year. If reversed is True, iterate from the latest to the earliest time in the year. Don't return a composite row
	because it's possible that a composite row would have values that don't make any sense together (e.g. 0 relative humidity and 12 inches of
	precipitation, each pulled from different datetimes and merged into a single row)
	"""
	if reverse:
		rows = reversed(rows)
	for row in rows:
		valid = True
		for dt in data_types:
			if not dt.validate(row):
				valid = False	
		if valid:
			return row


def get_processed_row(data_types, row):
	# type: (list, list) -> list
	""" The order of the WeatherDataTypes in the data_types list determines the order of the data in the final processed csv row """
	processed_row = []
	for dt in data_types:
		processed_row.append(dt.get_value(row))
	return processed_row


def add_row_to_hourly_avg(row, hourly_avg):
	for j in range(len(row)):
		val = row[j]
		try:
			val = str_to_num(val)
			hourly_avg[j] += val
		except:
			hourly_avg[j] = val


def extract_data(first_valid_row, last_valid_row, rows, data_types, is_subhourly_data=False):
	# type: (list, list, list, list, list, bool) -> list
	most_recent_valid_row = first_valid_row
	processed_data = []
	if is_subhourly_data:
		hourly_avg = [0] * len(rows[0])
	for i in range(len(rows)):
		row = rows[i]
		for dt in data_types:
			if not dt.validate(row):
				end_row_index, next_valid_value = dt.get_next_valid_value(rows, i)
				if end_row_index is None:
					end_row_index = len(rows) - 1
					next_valid_value = str_to_num(last_valid_row[dt.data_index])
				dt.correct_column(rows, i, end_row_index - 1, str_to_num(most_recent_valid_row[dt.data_index]), next_valid_value)
		most_recent_valid_row = row
		if is_subhourly_data:
			add_row_to_hourly_avg(row, hourly_avg)
			if (i + 1) % 12 == 0:
				for j in range(len(row)):
					try:
						hourly_avg[j] = hourly_avg[j] / float(12)
					except:
						pass
				processed_data.append(get_processed_row(data_types, hourly_avg))
				hourly_avg = [0] * len(row)
		else:
			processed_data.append(get_processed_row(data_types, row))
	return processed_data


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
	return [re.split("\s+", line) for line in r.text.splitlines()]


def data_is_valid(rows, frequency):
	# type: (list, str) -> bool
	pass


def _hourly_data_is_valid():
	pass


def _subhourly_data_is_valid():
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
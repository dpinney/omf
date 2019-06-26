''' Pull down historical weather data, put it on a SCADA-calibrated feeder. '''


import json, csv, os, re
from datetime import datetime, timedelta
import requests
from omf import feeder 
from omf.solvers.gridlabd import runInFilesystem
import threading, time


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
	"""
	Get USCRN data for a year and station, write it to a CSV, then calibrate the .omd to use the CSV.

	:param omd_path: the path to the .omd file to calibrate
	:type omd_path: str
	:param year: the year to get USCRN data for
	:type year: int
	:param station: the name of the USCRN station
	:type station: str
	"""
	csv_path = os.path.join(os.path.dirname(omd_path), "uscrn-weather-data.csv")
	write_USCRN_csv(csv_path, year, station)
	start_date = datetime(year, 1, 1)
	calibrate_omd(start_date, omd_path, csv_path)


def calibrate_omd(start_date, omd_path, csv_path):
	"""
	Modify an .omd file so that it will run in GridLAB-D with the CSV of USCRN weather data.

	:param start_date: the starting date of the GridLAB-D simulation
	:type start_date: datetime
	:param omd_path: an absolute path to the .omd file to modify
	:type omd_path: str
	:param csv_path: an absolute path to the CSV file that contains USCRN weather data
	:type csv_path: str
	"""
	with open(omd_path, 'r') as f:
		omd = json.load(f)
	tree = omd["tree"]
	# Delete all climate objects from the feeder. Also delete any csv_reader objects that are also named "WeatherReader"
	weather_reader_name = "WeatherReader"
	for key in tree.keys():
		object_type = tree[key].get("object")	
		object_name = tree[key].get("name")
		if object_type == "climate" or (object_type == "csv_reader" and object_name == weather_reader_name):
			del tree[key]
	# Reinsert a new climate object and an associated csv_reader object
	oldMax = feeder.getMaxKey(tree)
	tree[oldMax + 1] = {'omftype':'module', 'argument':'tape'}
	tree[oldMax + 2] = {'omftype':'module', 'argument':'climate'}
	csv_name = os.path.basename(csv_path)
	tree[oldMax + 3] = {'object':'csv_reader', 'name': weather_reader_name, 'filename': csv_name}
	climate_name = "MyClimate"
	tree[oldMax + 4] = {'object':'climate', 'name':climate_name, 'reader': weather_reader_name, 'tmyfile': csv_name}
	# Set the time correctly. Modify certain objects in the feeder (e.g. recorder and clock)
	feeder.adjustTime(tree, 240, 'hours', '{}-{}-{}'.format(start_date.year, start_date.month, start_date.day)) 
	omd["tree"] = tree
	# Add the weather attachment
	with open(csv_path, 'r') as f:
		weatherString = f.read()
	if omd.get("attachments") is None:
		omd["attachments"] = {}
	omd['attachments'][csv_name] = weatherString
	with open(omd_path, 'w') as f:
		json.dump(omd, f, indent=4)


def write_USCRN_csv(csv_path, year, station):
	"""
	Get data as .txt files from the USCRN server, process the data, and write the processed data to a CSV.

	:param csv_path: the absolute path at which to write the CSV file
	:type csv_path: str
	:param year: the year to get USCRN data from
	:type year: int
	:param station: the station to get USCRN data from
	:type station: str
	"""
	# Get hourly data and process it
	hourly_rows = get_USCRN_data(year, station, "hourly")
	if hourly_rows is None:
		raise Exception("Failed to get USCRN data for year \"{}\" and station \"{}\"".format(year, station))
	data_types = get_hourly_USCRNDataTypes()
	first_valid_row = get_first_valid_row(hourly_rows, data_types)
	last_valid_row = get_first_valid_row(hourly_rows, data_types, reverse=True)
	if first_valid_row is None or last_valid_row is None:
		raise Exception("Relevant hourly data values are missing from the USCRN data for year: \"{}\" and station: \"{}\"".format(year, station))
	hourly_processed_data = extract_data(first_valid_row, last_valid_row, hourly_rows, data_types, is_subhourly_data=False)
	# Get subhourly data and process it
	subhourly_rows = get_USCRN_data(year, station, "subhourly")
	if subhourly_rows is None:
		raise Exception("Failed to get USCRN data for year \"{}\" and station \"{}\"".format(year, station))
	data_types = get_subhourly_USCRNDataTypes()
	first_valid_row = get_first_valid_row(subhourly_rows, data_types)
	last_valid_row = get_first_valid_row(subhourly_rows, data_types, reverse=True)
	if first_valid_row is None or last_valid_row is None:
		raise Exception("Relevant subhourly data values are missing from the USCRN data for year: \"{}\" and station: \"{}\"".format(year, station))
	subhourly_processed_data = extract_data(first_valid_row, last_valid_row, subhourly_rows, data_types, is_subhourly_data=True)
	# Merge the hourly and subhourly data
	all_data = merge_hourly_subhourly(hourly_processed_data, subhourly_processed_data, 1)
	# Write the CSV
	with open(csv_path, 'w') as f:
		writer = csv.writer(f)
		writer.writerows(all_data)


def get_USCRN_data(year, station, frequency):
	"""Get a .txt file from the USCRN server and return the data as a list of lists."""
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


def get_hourly_USCRNDataTypes():
	"""Return a list of the USCRNDataTypes that we want to extract from a USCRN .txt file of hourly data."""
	temperature = USCRNDataType(8, -9999.0, flag_index=None, transformation_function=lambda x: round(celsius_to_fahrenheit(x), 1))
	humidity = USCRNDataType(26, -9999, flag_index=27, transformation_function=lambda x: round((x / float(100)), 2))
	solar_dir = USCRNDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.75, 0)))
	solar_diff = USCRNDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.25, 0)))
	solar_global = USCRNDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(watts_per_meter_sq_to_watts_per_ft_sq(x), 0)))
	return [temperature, humidity, solar_dir, solar_diff, solar_global]


def get_subhourly_USCRNDataTypes():
	"""Return the USCRNDataTypes that we want to extract from a USCRN .txt file of subhourly data."""
	wind_speed = USCRNDataType(21, -99.00, flag_index=22, transformation_function=lambda x: round(x, 2))
	return [wind_speed]


def str_to_num(data):
	"""Convert a string to its int or float equivalent."""
	if type(data) is str or type(data) is unicode:
		if get_precision(data) == 0:
			return int(data)
		return float(data)
	return data


def get_precision(data):
	"""Get the decimal precision of a number as an int."""
	if type(data) is not str and type(data) is not unicode:
		data = str(data)
	if data.find(".") == -1:
		return 0
	return len(re.split("[.]", data)[1])


def get_processed_row(data_types, row):
	"""
	Extract the datum for each USCRNDataType from the row of raw data into a new row.

	The ordering of the USCRNDataTypes in the data_types array determines the final ordering in the written CSV.

	:param data_types: a list of USCRNDataType objects
	:type data_types: list
	:param row: a row of raw data from the USCRN .txt file
	:type row: list
	:returns: a subset of the raw data from the USCRN .txt file
	:rtype: list
	"""
	processed_row = []
	for d_type in data_types:
		processed_row.append(d_type.get_value(row))
	return processed_row


def add_row_to_hourly_avg(row, hourly_avg):
	"""
	Add the values from a row of subhourly data into the row that represents the hourly average of the subhourly measurements.

	We need this function because not all data is represented as numbers, so we have to try-except the adding operation.

	:param row: a row of data that contains subhourly measurements. There are 12 subhourly measurements taken per hour
	:type row: list
	:param hourly_avg: a row of data that contains the sum of 12 subhourly measurements for an hour
	:type hourly_avg: list
	"""
	for j in range(len(row)):
		val = row[j]
		try:
			val = str_to_num(val)
			hourly_avg[j] += val
		except:
			hourly_avg[j] = val


def get_first_valid_row(rows, data_types, reverse=False):
	"""
	Iterate over the USCRN .txt file represented as a list of lists and return the first row that has all valid data for the given USCRNDataTypes.

	:param rows: a list of lists that represents the USCRN .txt file
	:type rows: list
	:param data_types: the USCRNDataTypes to use to validate each row
	:type data_types: list
	:param reverse: determines whether to parse from the beginning to end of the .txt file or from the end to beginning
	:type reverse: bool
	:return: a row of data that has all valid values for the given USCRNDataTypes
	:rtype: list
	"""
	#  Don't return a composite row because it's possible that a composite row would have values that don't make any sense together (e.g. 0 relative
	#  humidity and 12 inches of precipitation, each pulled from different datetimes and merged into a single row)
	if reverse:
		rows = reversed(rows)
	for row in rows:
		valid = True
		for d_type in data_types:
			if not d_type.is_valid(row):
				valid = False	
		if valid:
			return row


def extract_data(first_valid_row, last_valid_row, rows, data_types, is_subhourly_data=False):
	"""
	Extract the desired columns of data from the USCRN .txt file that is represented as a list of lists.

	:param first_valid_row: a row of that contains all valid data values. May or may not be a row from the .txt file that is being parsed
	:type first_valid_row: list
	:param last_valid_row: a row that contains all valid data values. May or may not be a row from the .txt file that is being parsed
	:type last_valid_row: list
	:param rows: the USCRN .txt file represented as a list of lists
	:type rows: list
	:param data_types: a list of USCRNDataTypes that will be used to parse the the USCRN .txt file
	:type data_types: list
	:param is_subhourly_data: whether or not the .txt file that is being parsed is hourly or subhourly data.
	:type is_subhourly_data: bool
	:return: a subset of the data from the original USCRN .txt file that has had erronous data values corrected
	:rtype: list
	"""
	most_recent_valid_row = first_valid_row
	processed_data = []
	if is_subhourly_data:
		hourly_avg = [0] * len(rows[0])
	for i in range(len(rows)):
		row = rows[i]
		for d_type in data_types:
			if not d_type.is_valid(row):
				end_row_index, next_valid_value = d_type.get_next_valid_value(rows, i)
				if end_row_index is None:
					end_row_index = len(rows) - 1
					next_valid_value = str_to_num(last_valid_row[d_type.data_index])
				d_type.correct_data(rows, i, end_row_index - 1, str_to_num(most_recent_valid_row[d_type.data_index]), next_valid_value)
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


def watts_per_meter_sq_to_watts_per_ft_sq(w_m_sq):
	"""Convert a W/m^2 measurements to a W/ft^2 measurement."""
	if type(w_m_sq) is str or type(w_m_sq) is unicode:
		w_m_sq = str_to_num(w_m_sq)
	return (w_m_sq / ((1 / .3048) ** 2))


def celsius_to_fahrenheit(c):
	"""Convert a celsius measurement to a fahrenheit measurement."""
	if type(c) is str or type(c) is unicode:
		c = str_to_num(c)
	return c * 9 / float(5) + 32


def merge_hourly_subhourly(hourly, subhourly, insert_idx):
	"""
	Merge the hourly and subhourly USCRN data into a single list of lists and add datetimes and add a header row for GridLAB-D. 

	:param hourly: the list of lists of hourly data
	:type hourly: list
	:param subhourly: the list of lists of averaged subhourly data
	:type subhourly: list
	:param insert_idx: the column index of the hourly data within which to insert the subhourly data
	:type insert_idx: int
	:return: a single merged list of lists
	:rtype: list
	"""
	assert len(hourly) == len(subhourly)
	assert len(hourly[0]) > 0 and len(subhourly[0]) > 0
	# Add headers
	merged_rows = [
		["temperature", "wind_speed", "humidity", "solar_dir", "solar_diff", "solar_global"]
	]
	start_date = datetime(2000, 1, 1, 0, 0, 0) # arbitrary datetime, this could be any year
	hour = timedelta(hours=1)
	for i in range(len(hourly)):
		dt = start_date + hour * i
		gridlabd_date = '{}:{}:{}:{}:{}'.format(dt.month, dt.day, dt.hour, dt.minute, dt.second)
		row = [gridlabd_date]
		for j in range(len(hourly[i])):
			if insert_idx == j:
				row.extend(subhourly[i])
			row.append(hourly[i][j])			
		merged_rows.append(row)
	return merged_rows


class USCRNDataType(object):
	"""
	Each instance of this class represents a particular column of data that we want to parse, validate, and retrieve from the .txt file. The
	programmer need only create instances of this class, append them to a list, and pass that list to the extract_data() function that is in this
	module. The programmer shouldn't need to use any of the methods in the class directly. Due to the behavior of get_processed_rows() that is called
	within extract_data(), the ordering of the USCRNDataTypes inside of the list that is passed to extract_data() will determine the ordering of the CSV
	columns.
	"""


	def __init__(self, data_index, missing_data_value, flag_index=None, transformation_function=None):
		"""
		Set up an object that encapsulates the validation and data retrieval logic that is needed to parse a .txt file from USCRN into a usable CSV for
		GridLAB-D.
		
		:param data_index: the 0-indexed column in the USCRN .txt file where the data for this data type is written
		:type data_index: int
		:param missing_data_value: the int or float used by USCRN to indicate that a value is missing and was not propery recorded in the .txt file
		:type missing_data_value: int or float
		:flag_index: the 0-indexed column in the USCRN .txt file where the quality control flag for this data type is recorded. Not all data types
			have a quality control flag
		:type flag_index: int
		:param transformation_function: a function that should be applied to each datum that is parsed from the .txt file before it is written to the
			CSV file
		:type transformation_function: function
		"""
		self.data_index = int(data_index)
		if type(missing_data_value) is str or type(missing_data_value) is unicode:
			missing_data_value = str_to_num(missing_data_value)
		self.missing_data_value = missing_data_value
		if flag_index is not None:
			flag_index = int(flag_index)
		self.flag_index = flag_index
		self.transformation_function = transformation_function


	def is_valid(self, row):
		"""
		Return True if the row has a valid datum value for this USCRNDataType, otherwise False.

		:param row: a row of data from the USCRN .txt file
		:rtype: bool
		"""
		if str_to_num(row[self.data_index]) == self.missing_data_value:
			return False
		if self.flag_index is not None and str_to_num(row[self.flag_index]) != 0:
			return False
		return True


	def get_next_valid_value(self, rows, start_row_idx):
		"""
		Return the next valid value for this USCRNDataType and the row index at which is was found.

		Parse the list of rows and find the closest row after or including the current row that contains a valid datum for this USCRNDataType, then
		return that datum and its row index.

		:param rows: the USCRN .txt file represented as a list of lists
		:param start_row_idx: the index of the row that we want to start looking for a valid value for this USCRNDataType.
		:rtype: tuple
		"""
		for i in range(start_row_idx, len(rows)):
			row = rows[i]
			if self.is_valid(row):
				return (i, str_to_num(row[self.data_index]))
		return (None, None)


	def correct_data(self, rows, start_row_idx, end_row_idx, initial_val, final_val):
		"""
		Parse the rows specified by the starting and ending row indexes, and modify the datum corresponding to this USCRNDataType in each row.

		The datum in each row is modified according to a linear interpolation between the initial_val and final_val. start_row_idx and end_row_idx are
		both inclusive of modification.

		:param rows: a list of lists that represents the USCRN .txt file
		:param start_row_idx: the index of the first row to start modifying data
		:type start_row_idx: int
		:param end_row_idx: the index of the last row to modify data
		:type end_row_idx: int
		:param initial_val: the starting value of the linear interpolation
		:param final_val: the final value of the linear interpolation
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
		"""
		Return the datum stored in the USCRN .txt file for this USCRNDataType at the specified row.

		:param row: a list of data
		:rtype: int or float
		"""
		value = row[self.data_index]
		if type(value) is str or type(value) is unicode:
			value = str_to_num(value)
		if self.transformation_function is not None:
			return self.transformation_function(value)
		return value


def get_omd_path(glm_path):
	"""Get a .omd from a .glm and return the path."""
	tree = feeder.parse(glm_path)
	omd = {}
	omd["tree"] = tree
	omd_name = os.path.basename(glm_path).split(".")[0] + ".omd"
	omd_path = os.path.join(os.path.dirname(__file__), omd_name)
	with open(omd_path, 'w') as f:
		json.dump(omd, f, indent=4)
	return omd_path


def test_gridlabd_weather_sim(year, station, omd_path):
	"""
	runInFileSystem(
		feederTree: The value stored at the "tree" key of the .omd file.
	    attachments: The value stored at the "attachments" key of the .omd file. Each attachment will be rewritten as a file inside of the working
			directory of the GridLAB-D operation. I do want to specify this.
	    keepFiles: whether or not to preserve all of the files in the workDir. Only has an effect if an explicit workDir was not set.
		workDir: the working directory to run the GridLAB-D operation. If not specified, a temporary directory will be used.
	    glmName: the basename of the .glm file (e.g. "something.glm") where the glmString (which is the result of omf.feeder.sortedWrite(<feederTree>) will
			be written in the workDir. If not specified a .glm file is created with a timestamp as the filename. GridLAB-D operates on the .glm
			corresponding to the glmName, NOT directly on the feederTree.
	)
	"""
	attachHistoricalWeather(omd_path, year, station)
	with open(omd_path) as f:
		omd = json.load(f)
	calibrated_tree = omd["tree"]
	attachments = omd["attachments"]
	# Run here to test GridLAB_D
	# The output is NOT a feeder. It's some data in JSON format. This function call does NOT modify myTree.
	rawOut = runInFilesystem(feederTree=calibrated_tree, attachments=attachments, keepFiles=True, workDir=os.path.join(os.path.dirname(__file__), "gridlabd-work-dir"), glmName='outFile.glm')
	print(rawOut)


def _test_USCRN_with_gridlabd():
	"""
	I cannot tell whether or not GridLAB-D is using the most recently written USCRN data when it runs the simulation. It seems very inconsistent.
	- Running the same existing .omd file with new data 5 times:
		- Did not change gridlabd.xml at all
		- Did not change any of the xout files at all
	- Running the same existing .omd file with the same data 5 times:
		- Did not change gridlabd.xml at all
		- Did not change any of the xout files at all 
	- Running the newly created .omd file with new data 5 times ...
		- 1 run did not change gridlabd.xml but DID change the xout files
		- 1 run did not change gridlabd.xml but DID change the xout files (again)
		- 1 run did change gridlabd.xml but did not change the xout files
		- 1 run did change gridlabd.xml but did not change the xout files (again)
		- 1 run did change gridlabd.xml but did not change the xout files (again)
	- Running the newly created .omd file with the same data 5 times ...
		- 1 run changed gridlabd.xml but not not change any xout files
		- 1 run changed gridlabd.xml AND changed all of the xout files
		- 1 run changed gridlabd.xml but not not change any xout files (again)
		- 1 run changed gridlabd.xml but not not change any xout files (again)
		- 1 run changed gridlabd.xml AND changed all of the xout files (again)
	"""
	year = 2017
	station = "CO_Dinosaur_2_E"
	omd_path = get_omd_path(os.path.join(os.path.dirname(__file__), "IEEE_quickhouse.glm"))
	#omd_path = os.path.join(os.path.dirname(__file__), "OlinBarreGHW.omd")
	test_gridlabd_weather_sim(year, station, omd_path)


def _test_get_USCRN_data_with_multiprocessing():
	"""
	The child process crashes at some point. Thus, using the requests module with Flask is fine, but using the requests module INSIDE of a forked
	child process that was created with the multiprocessing module causes problems. To solve this, we have to use threads instead of processes. See
	https://bugs.python.org/issue31818
	"""
	filepath = os.path.join(os.path.dirname(__file__), "test-uscrn-output.csv")
	def write_USCRN_output():
		"""Write the USCRN data to a CSV to prove the process completed successfully."""
		data = get_USCRN_data(2017, "CO_Dinosaur_2_E", "hourly")
		with open(filepath, 'w') as f:
			writer = csv.writer(f)
			writer.writerows(data)
	t = threading.Thread(target=write_USCRN_output)
	t.start()
	t.join()
	#p = multiprocessing.Process(target=write_USCRN_output)
	#p.start()
	#p.join()
	#write_USCRN_output()
	if os.path.isfile(filepath):
		print("Test ended successfully")
	else:
		print("Background process crashed")


if __name__ == "__main__":
	_test_USCRN_with_gridlabd()
	#_test_get_USCRN_data_with_multiprocessing()
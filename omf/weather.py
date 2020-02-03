'''
Pull weather data from various sources.
Source options include NOAA's USCRN, Iowa State University's METAR, and Weather Underground (currently deprecated).
'''


import os, csv, re, json
from math import sqrt, exp
from os.path import join as pJoin
from datetime import timedelta, datetime
from urllib.request import Request, urlopen
import requests
from dateutil.parser import parse as parse_dt
from omf import feeder

def pullAsos(year, station, datatype):
	'''This model pulls hourly data for a specified year and ASOS station. 
	* ASOS is the Automated Surface Observing System, a network of about 900 
		weater stations, they collect data at hourly intervals, they're run by 
		NWS, FAA, and DOD, and there is data going back to 1901 in some sites.
	* AKA METAR data, which is the name of the format its stored in.
	* For ASOS station code see https://www.faa.gov/air_traffic/weather/asos/
	* For datatypes see bottom of https://mesonet.agron.iastate.edu/request/download.phtml
	* Note for USA stations (beginning with a K) you must NOT include the 'K' 
	'''
	url = ('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?'
		'station={}&data={}&year1={}&month1=1&day1=1&year2={}&month2=1&day2=1'
		'&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=1'
		'&report_type=2').format(station, datatype, year, int(year)+1)
	r = requests.get(url)
	assert r.status_code != 404, "Dataset URL does not exist. " + url
	data = [x.split(',') for x in r.text.splitlines()[1:]]
	verifiedData = [-9999.0] * 8760
	firstDT = datetime(int(year), 1, 1)
	for r in data:
		if 'M' not in r:
			deltatime = parse_dt(r[1]) - firstDT
			verifiedData[int(deltatime.total_seconds()/3600)] = float(r[2])	
	return verifiedData


def pullAsosStations(filePath):
	"""Build a station list for the ASOS data. Put them in filePath with their details. """
	stations = []
	states = """AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME
	 MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT
	 WA WI WV WY"""
	networks = []
	for state in states.split():
		networks.append("%s_ASOS" % (state,))
	with open(filePath, 'w',  newline='') as csvfile:
		fieldnames = ['Station Id', 'Station Name', 'County', 'State', 'Latitude', 'Longitude', 'Elevation', 'Time Zone']
		csvwriter = csv.DictWriter(csvfile, delimiter=',', fieldnames=fieldnames)
		for network in networks:
			current = []
			current.append(network)
			uri = ("https://mesonet.agron.iastate.edu/"
			"geojson/network/%s.geojson") % (network,)
			with urlopen(uri) as f:
				jdict = json.load(f)
			#map attribute to entry in csv
			csvwriter.writeheader()
			for site in jdict['features']:
				currentSite = {}
				currentSite['Station Id'] = site['properties']['sid']
				currentSite['Station Name'] = site['properties']['sname']
				currentSite['County'] = site['properties']['county']
				currentSite['State'] = site['properties']['state']
				currentSite['Latitude'] = site['geometry']['coordinates'][0]
				currentSite['Longitude'] = site['geometry']['coordinates'][1]
				currentSite['Elevation'] = site['properties']['elevation']
				currentSite['Time Zone'] = site['properties']['tzname']
				csvwriter.writerow(currentSite)


def pullDarksky(year, lat, lon, datatype, units='si', api_key=os.environ.get('DARKSKY',''), path = None):
	'''Returns hourly weather data from the DarkSky API as array.

	* For more on the DarkSky API: https://darksky.net/dev/docs#overview
	* List of available datatypes: https://darksky.net/dev/docs#data-point
	
	* year, lat, lon: may be numerical or string
	* datatype: string, must be one of the available datatypes (case-sensitive)
	* api_key: string
	* units: string, either 'us' or 'si'
	* path: string, must be a path to a folder if provided.
		* if a path is provided, the data for all datatypes for the given year and location will be cached there as a csv.'''
	from pandas import date_range
	lat, lon = float(lat), float(lon)
	int(year) # if year isn't castable... something's up
	coords = '%0.2f,%0.2f' % (lat, lon) # this gets us 11.1 km unc <https://gis.stackexchange.com/questions/8650/measuring-accuracy-of-latitude-and-longitude>
	if path:
		assert os.path.isdir(path), 'Path does not exist'
		filename = coords + "_" + str(year) + ".csv"
		filename = pJoin(path, filename)
		try:
			with open(filename, 'r', newline='') as csvfile:
				reader = csv.reader(csvfile)
				in_csv = [row for row in reader]
			index = in_csv[0].index(datatype)
		except IndexError:
			print('Requested datatype not present in cache, an attempt will be made to fetch from the API')
		except IOError:
			print('Cache not found, data will be fetched from the API')	
	# Now we begin the actual scraping. Behold: a convoluted way to get a list of days in a year
	times = list(date_range('{}-01-01'.format(year), '{}-12-31'.format(year)))
	#time.isoformat() has no tzinfo in this case, so darksky parses it as local time
	urls = ['https://api.darksky.net/forecast/%s/%s,%s?exclude=daily&units=%s' % ( api_key, coords, time.isoformat(), units ) for time in times]
	data = [requests.get(url).json() for url in urls] # all requests return 400 and "Poorly formatted request" probably because I don't have the API key
	#a fun little annoyance: let's de-unicode those strings
	#def ascii_me(obj):
	#	if isinstance(obj, unicode):
	#		return obj.encode('ascii','ignore')
	#	if isinstance(obj, list):
	#		return map(ascii_me, obj)
	#	if isinstance(obj, dict):
	#		new_dict = dict()
	#		for k, v in obj.iteritems():
	#			k = k.encode('ascii','ignore') if type(k) is type(u'') else k
	#			new_dict[k] = ascii_me(v)
	#		return new_dict
	#	else:
	#		return obj
	#data = ascii_me(data)
	out = []
	if path:
			# determine the columns from the first day of data
			columns = list(data[0]['hourly']['data'][0].keys())
			out_csv = [columns]
	# parse our json-dict
	for day in data:
		for hour in day['hourly']['data']:
			if path:
				out_csv.append( [hour.get(key) for key in columns] )
			out.append(hour.get(datatype))
	if path:
		with open(filename, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			for row in out_csv:
				writer.writerow(row)
	return out


def pullUscrn(year, station, datatype):
	'''Returns hourly weather data from NOAA's quality-controlled USCRN dataset as array.
	* Documentation: https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/README.txt
	* List of available stations: https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02'''
	url = ('https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/{0}/'
		'CRNH0203-{0}-{1}.txt'.format(year, station))
	r = requests.get(url)
	assert r.status_code != 404, "Dataset URL does not exist. " + url 
	# Columns name and index (subtracted 1 from readme's Field #)
	datatypeDict = {
		"T_CALC": 8,
		"T_HR_AVG": 9,
		"T_MAX": 10,
		"T_MIN": 11,
		"P_CALC": 12,
		"SOLARAD": 13,
		"SOLARAD_MAX": 15,
		"SOLARAD_MIN": 17,
		"SUR_TEMP": 20,
		"SUR_TEMP_MAX": 22,
		"SUR_TEMP_MIN": 24,
		"RH_HR_AVG": 26,
		"SOIL_MOISTURE_5": 28,
		"SOIL_MOISTURE_10": 29,
		"SOIL_MOISTURE_20": 30,
		"SOIL_MOISTURE_50": 31,
		"SOIL_MOISTURE_100": 32,
		"SOIL_TEMP_5": 33,
		"SOIL_TEMP_10": 34,
		"SOIL_TEMP_20": 35,
		"SOIL_TEMP_50": 36,
		"SOIL_TEMP_100": 37,
		"IRRADIENCE_DIFFUSE":13 }
	#IF datatype is "irradiance estimate", then run the diffuse/direct_seperator method 
	assert datatype in datatypeDict, "This datatype isn't listed in options!"
	datatypeID = datatypeDict[datatype]
	rawData = [float(x.split()[datatypeID]) for x in r.text.splitlines() if len(x) != 0]
	if datatype == "IRRADIENCE_DIFFUSE":
		#Now get diffuse component, write in place in data array
		diffuse = list(map(get_diffuse_solar_component, rawData))
		# #Subtract diffuse from raw to get direct component
		direct = list(map(lambda x, y: x-y,rawData, diffuse))
		direct_diffuse = list(zip(direct, diffuse))
		raw_diffuse = list(zip(rawData, diffuse))
		return raw_diffuse #direct_diffuse
	return rawData


def _pullWeatherWunderground(start, end, airport, workDir):
	'''	NOTE: WeatherUnderground moved behind a paywall but we'll keep this in case we get a license. 
	Download weather CSV data to workDir. 1 file for each day between start and 
	end (YYYY-MM-DD format). Location is set by airport (three letter airport code, e.g. DCA). '''
	# Parse start and end dates.
	start_dt = datetime.strptime(start, "%Y-%m-%d")
	end_dt = datetime.strptime(end, "%Y-%m-%d")
	# Calculate the number of days to fetch.
	num_days = (end_dt - start_dt).days
	work_day = start_dt
	# HACK: urllib proxy auto-detection crashes hard in Mac OS X, so force a dummy proxy that will then cause fallback to direct request.
	os.environ["dummy_proxy"] = "NONE"
	# Generate URLs and get data.
	for i in range(num_days):
		year = work_day.year
		month = work_day.month
		day = work_day.day
		address = "http://www.wunderground.com/history/airport/{}/{:d}/{:d}/{:d}/DailyHistory.html?format=1".format(airport, year, month, day)
		filename = pJoin(workDir,"weather_{}_{:d}_{:d}_{:d}.csv".format(airport, year, month, day))
		if os.path.isfile(filename):
			continue # We have the file already, don't re-download it.
		try:
			with urlopen(address) as f:
				data = str(f.read(), 'utf-8')
			with open(filename) as f:
				f.write(data)
			#f = urlretrieve(address, filename)
		except:
			print("ERROR: unable to get data from URL " + address)
			continue # Just try to grab the next one.
		work_day = work_day + timedelta(days = 1) # Advance one day


def airportCodeToLatLon(airport):
	''' Airport three letter code -> lat/lon of that location. 
		Dataset: https://opendata.socrata.com/dataset/Airport-Codes-mapped-
			to-Latitude-Longitude-in-the-/rxrh-4cxm '''
	omfDir = os.path.dirname(os.path.abspath(__file__))
	with open(pJoin(omfDir, 'static/Airports.csv'), newline='') as f:
		for m in list(csv.reader(f))[1:]:
			if m[0] == airport:
				return (m[1], m[2])
	print('Airport not found: ', airport)
	lat = float(input('Please enter latitude manually:'))
	lon = float(input('Please enter longitude manually:'))
	return (lat, lon)


def zipCodeToClimateName(zipCode):
	''' Given a zipcode, return the closest city for which there's weather data. 
	* This will give nearest data within state. If zip code is in NJ on
		border of NYC, Hoboken (07030) for example, it will return Newark
		instead of NYC.
	* Zip code lat/lon/city/state data taken from https://www.gaslampmedia.com
		/download-zip-code-latitude-longitude-city-state-county-csv/ '''
	assert isinstance(zipCode, str), "To prevent leading zero errors, input zipcode as string"
	omfDir = os.path.dirname(os.path.abspath(__file__))
	zipCsvPath = pJoin(omfDir, "static", "zip_codes_altered.csv")
	# Find the state, city, lat, lon for given zipcode
	with open(zipCsvPath, 'r', newline='') as f:
		try:
			'''All zipcodes are unique. len(row) will be either 1 or 0. Error 
				would be raised by calling the zero index on an empty array.'''
			row = [r for r in list(csv.reader(f))[1:] if r[0] == zipCode][0]
		except:
			raise Exception("Data not available: " + zipCode)
		zipState = row[4]
		ziplatlon = row[1], row[2]
	# Collect data from every zipcode in state
	with open(zipCsvPath, 'r', newline='') as f:
		cityData = [r for r in csv.reader(f) if r[4] == zipState]
	# Collect all names of cities with data from state. Remove the state abbr. from beginning and '.tmy2' from end.
	citiesInState = [cn[3:-5] for cn in os.listdir(pJoin(omfDir, 'data', 'Climate')) if zipState == cn[:2]]
	# Approximate closest city with data to given zipcode
	foundCity, lowestDistance = None, float('inf')
	for cCity in citiesInState:
		for row in cityData:
			city = row[3].replace(' ', '_')
			if row[4].lower() == zipState.lower() and city.lower() == cCity.lower():
				# Using pyth on globe is not accurate. Consider updating w spherical distance function
				# E.g. Brick, NJ (08724) is closer to Newark, but this function recommends AC.
				climatelatlon = row[1], row[2]
				differenceLat = float(climatelatlon[0]) - float(ziplatlon[0])
				differenceLon = float(climatelatlon[1]) - float(ziplatlon[1])
				distance = differenceLat ** 2 + differenceLon ** 2
				if distance < lowestDistance: 
					lowestDistance = distance
					foundCity = cCity
	assert foundCity != None, "A city is spelled differently between two datasets. Please notify the OMF team."
	return '{}-{}'.format(zipState, foundCity)





########################
### aGosedWeather.py ###
########################


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
	temperature = USCRNDataType(8, -9999.0, flag_index=None, transformation_function=lambda x: round(_celsius_to_fahrenheit(x), 1))
	humidity = USCRNDataType(26, -9999, flag_index=27, transformation_function=lambda x: round(x / 100, 2))
	solar_dir = USCRNDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(_watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.75, 0)))
	solar_diff = USCRNDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(_watts_per_meter_sq_to_watts_per_ft_sq(x) * 0.25, 0)))
	solar_global = USCRNDataType(13, -99999, flag_index=14, transformation_function=lambda x: int(round(_watts_per_meter_sq_to_watts_per_ft_sq(x), 0)))
	hourly_data_types = [temperature, humidity, solar_dir, solar_diff, solar_global]
	wind_speed = USCRNDataType(21, -99.00, flag_index=22, transformation_function=lambda x: round(x, 2))
	subhourly_data_types = [wind_speed]
	_write_USCRN_csv(csv_path, year, station, hourly_data_types, subhourly_data_types)
	start_date = datetime(year, 1, 1)
	_calibrate_omd(start_date, omd_path, csv_path)


def _calibrate_omd(start_date, omd_path, csv_path):
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
	for key in list(tree.keys()):
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


def _write_USCRN_csv(csv_path, year, station, hourly_data_types, subhourly_data_types):
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
	hourly_rows = _get_USCRN_data(year, station, "hourly")
	if hourly_rows is None:
		raise Exception("Failed to get USCRN data for year \"{}\" and station \"{}\"".format(year, station))
	if hourly_data_types is not None:
		first_valid_row = _get_first_valid_row(hourly_rows, hourly_data_types)
		last_valid_row = _get_first_valid_row(hourly_rows, hourly_data_types, reverse=True)
		if first_valid_row is None or last_valid_row is None:
			raise ValueError("Relevant hourly data values are missing from the USCRN data for year: \"{}\" and station: \"{}\"".format(year, station))
		hourly_processed_data = _extract_data(first_valid_row, last_valid_row, hourly_rows, hourly_data_types, is_subhourly_data=False)
	else:
		hourly_processed_data = None
	# Get subhourly data and process it
	subhourly_rows = _get_USCRN_data(year, station, "subhourly")
	if subhourly_rows is None:
		raise ValueError("Failed to get USCRN data for year \"{}\" and station \"{}\"".format(year, station))
	if subhourly_data_types is not None:
		first_valid_row = _get_first_valid_row(subhourly_rows, subhourly_data_types)
		last_valid_row = _get_first_valid_row(subhourly_rows, subhourly_data_types, reverse=True)
		if first_valid_row is None or last_valid_row is None:
			raise ValueError("Relevant subhourly data values are missing from the USCRN data for year: \"{}\" and station: \"{}\"".format(year, station))
		subhourly_processed_data = _extract_data(first_valid_row, last_valid_row, subhourly_rows, subhourly_data_types, is_subhourly_data=True)
	else:
		subhourly_processed_data = None
	# Merge the hourly and subhourly data
	if hourly_processed_data is not None and subhourly_processed_data is not None:
		all_data = _merge_hourly_subhourly(hourly_processed_data, subhourly_processed_data, 1)
	else:
		if hourly_processed_data is not None:
			all_data = hourly_processed_data
		elif subhourly_processed_data is not None:
			all_data = subhourly_processed_data
		else:
			raise ValueError('There was no processed data to write to the CSV')
	# Write the CSV
	with open(csv_path, 'w', newline='') as f:
		writer = csv.writer(f)
		writer.writerows(all_data)


def _get_USCRN_data(year, station, frequency):
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


def _str_to_num(data):
	"""Convert a string to its int or float equivalent."""
	if isinstance(data, str):
		if _get_precision(data) == 0:
			return int(data)
		return float(data)
	return data


def _get_precision(data):
	"""Get the decimal precision of a number as an int."""
	if not isinstance(data, str):
		data = str(data)
	if data.find(".") == -1:
		return 0
	return len(re.split("[.]", data)[1])


def _get_processed_row(data_types, row):
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
		processed_row.append(d_type._get_value(row))
	return processed_row


def _add_row_to_hourly_avg(row, hourly_avg):
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
			val = _str_to_num(val)
			hourly_avg[j] += val
		except:
			hourly_avg[j] = val


def _get_first_valid_row(rows, data_types, reverse=False):
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
			if not d_type._is_valid(row):
				valid = False	
		if valid:
			return row


def _extract_data(first_valid_row, last_valid_row, rows, data_types, is_subhourly_data=False):
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
			if not d_type._is_valid(row):
				end_row_index, next_valid_value = d_type._get_next_valid_value(rows, i)
				if end_row_index is None:
					end_row_index = len(rows) - 1
					next_valid_value = _str_to_num(last_valid_row[d_type.data_index])
				d_type._correct_data(rows, i, end_row_index - 1, _str_to_num(most_recent_valid_row[d_type.data_index]), next_valid_value)
		most_recent_valid_row = row
		if is_subhourly_data:
			_add_row_to_hourly_avg(row, hourly_avg)
			if (i + 1) % 12 == 0:
				for j in range(len(row)):
					try:
						hourly_avg[j] = hourly_avg[j] / 12
					except:
						pass
				processed_data.append(_get_processed_row(data_types, hourly_avg))
				hourly_avg = [0] * len(row)
		else:
			processed_data.append(_get_processed_row(data_types, row))
	return processed_data


def _watts_per_meter_sq_to_watts_per_ft_sq(w_m_sq):
	"""Convert a W/m^2 measurements to a W/ft^2 measurement."""
	if isinstance(w_m_sq, str):
		w_m_sq = _str_to_num(w_m_sq)
	return (w_m_sq / ((1 / .3048) ** 2))


def _celsius_to_fahrenheit(c):
	"""Convert a celsius measurement to a fahrenheit measurement."""
	if isinstance(c, str):
		c = _str_to_num(c)
	return c * 9 / 5 + 32


def _merge_hourly_subhourly(hourly, subhourly, insert_idx):
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
	programmer need only create instances of this class, append them to a list, and pass that list to the _extract_data() function that is in this
	module. The programmer shouldn't need to use any of the methods in the class directly. Due to the behavior of _get_processed_rows() that is called
	within _extract_data(), the ordering of the USCRNDataTypes inside of the list that is passed to _extract_data() will determine the ordering of the CSV
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
		if isinstance(missing_data_value, str):
			missing_data_value = _str_to_num(missing_data_value)
		self.missing_data_value = missing_data_value
		if flag_index is not None:
			flag_index = int(flag_index)
		self.flag_index = flag_index
		self.transformation_function = transformation_function

	def _is_valid(self, row):
		"""
		Return True if the row has a valid datum value for this USCRNDataType, otherwise False.

		:param row: a row of data from the USCRN .txt file
		:rtype: bool
		"""
		if _str_to_num(row[self.data_index]) == self.missing_data_value:
			return False
		if self.flag_index is not None and _str_to_num(row[self.flag_index]) != 0:
			return False
		return True

	def _get_next_valid_value(self, rows, start_row_idx):
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
			if self._is_valid(row):
				return (i, _str_to_num(row[self.data_index]))
		return (None, None)

	def _correct_data(self, rows, start_row_idx, end_row_idx, initial_val, final_val):
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
			initial_val = _str_to_num(initial_val)
		if type(final_val) is str:
			final_val = _str_to_num(final_val)
		precision = _get_precision(initial_val)
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

	def _get_value(self, row):
		"""
		Return the datum stored in the USCRN .txt file for this USCRNDataType at the specified row.

		:param row: a list of data
		:rtype: int or float
		"""
		value = row[self.data_index]
		if isinstance(value, str):
			value = _str_to_num(value)
		if self.transformation_function is not None:
			return self.transformation_function(value)
		return value


def tmy3_pull(usafn_number, out_file=None):
	'''Pull TMY3 data based on usafn. Use nearest_tmy3_station function to get a close by tmy3 station based on latitude/longitude coordinates '''
	url = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3'
	file_name = '{}TYA.CSV'.format(usafn_number)
	file_path = os.path.join(url, file_name)
	data = requests.get(file_path)
	if out_file is not None:
		csv_lines = [line.decode() for line in data.iter_lines()]
		reader = csv.reader(csv_lines, delimiter=',')
		if out_file is not None:
			with open(out_file, 'w', newline='') as csvfile:
				#can use following to skip first line to line up headers
				#reader.next()
				for i in reader:
					csvwriter = csv.writer(csvfile, delimiter=',')
					csvwriter.writerow(i)
	else:
		return data

def nearest_tmy3_station(latitude, longitude):
	'''Return nearest USAFN stattion based on latlon'''
	url = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3'
	file_name = 'TMY3_StationsMeta.csv'
	file_path = os.path.join(url, file_name)
	data = requests.get(file_path)
	csv_lines = [line.decode() for line in data.iter_lines()]
	reader = csv.DictReader(csv_lines, delimiter=',')
	#SHould file be local?
	#with open('TMY3_StationsMeta.csv', 'r') as metafile:
	#reader = csv.DictReader(metafile, delimiter=',')
	tmy3_stations = [station for station in reader]
	nearest = min(tmy3_stations, key=lambda station: lat_lon_diff(latitude, station['Latitude'], longitude, station['Longitude']))
	return nearest['USAF']

def lat_lon_diff(lat1, lat2, lon1, lon2):
	'''Get the euclidean distance between two sets of latlon coordinates'''
	dist = sqrt((float(lat1) - float(lat2))**2 + (float(lon1) - float(lon2))**2)
	return dist

class NSRDB():
	'''Data pull factory for nsrdb data sets '''
	def __init__(self, data_set, longitude, latitude, year, api_key, utc='true', leap_day='false', email='admin@omf.coop', interval=None):
		self.base_url = 'https://developer.nrel.gov'
		self.data_set = data_set
		self.params = {}
		self.params['api_key'] = api_key
		#wkt will be one point to use csv option - may need another call to get correct wkt value: https://developer.nrel.gov/docs/solar/nsrdb/nsrdb_data_query/
		self.params['wkt'] = self.latlon_to_wkt(longitude, latitude)
		#names will be one value to use csv option
		self.params['names'] = str(year)
		#note utc must be either 'true' or 'false' as a string, not True or False Boolean value
		self.params['utc'] = utc
		self.params['leap_day'] = leap_day
		self.params['email'] = email
		self.interval = interval

	def latlon_to_wkt(self, longitude, latitude):
		if latitude < -90 or latitude > 90:
			raise('invalid latitude')
		elif longitude < -180 or longitude > 180:
			raise('invalid longitude')  
		return 'POINT({} {})'.format(longitude, latitude)

	def create_url(self, route):
		return os.path.join(self.base_url, route)

	#physical solar model
	def psm(self):
		self.params['interval'] = self.interval
		route = 'api/solar/nsrdb_psm3_download.csv'
		self.request_url = self.create_url(route)

	#physical solar model v3 tsm
	def psm_tmy(self):
		route = 'api/nsrdb_api/solar/nsrdb_psm3_tmy_download.csv'
		self.request_url = self.create_url(route)

	#SUNY international
	def suny(self):
		route = 'api/solar/suny_india_download.csv'
		self.request_url = self.create_url(route)

	#spectral tmy
	def spectral_tmy(self):
		route = 'api/nsrdb_api/solar/spectral_tmy_india_download.csv'
		self.request_url = self.create_url(route)

	#makes api request based on inputs and returns the response object
	def execute_query(self):
		set_query = getattr(self, self.data_set)
		set_query()
		resp = requests.get(self.request_url, params=self.params)
		return resp

def get_nrsdb_data(data_set, longitude, latitude, year, api_key, utc='true', leap_day='false', email='admin@omf.coop', interval=None, filename=None):
	'''Create nrsdb factory and execute query. Optional output to file or return the response object.'''
	nrsdb_factory = NSRDB(data_set, longitude, latitude, year, api_key, utc=utc, leap_day=leap_day, email=email, interval=interval)
	data = nrsdb_factory.execute_query()
	csv_lines = [line.decode() for line in data.iter_lines()]
	reader = csv.reader(csv_lines, delimiter=',')
	if filename is not None:
		with open(filename, 'w', newline='') as csvfile:
			for i in reader:
				csvwriter = csv.writer(csvfile, delimiter=',')
				csvwriter.writerow(i)
	else:
		#Maybe change depending on what's easy/flexible but this gives good display
		return data.text

def getRadiationYears(radiation_type, site, year):
	'''Pull solard or surfrad data and aggregate into a year'''
	URL = 'ftp://aftp.cmdl.noaa.gov/data/radiation/{}/{}/{}/'.format(radiation_type, site, year)
	#FILE = 'tbl19001.dat' - example
	# Get directory contents.
	dirReq = Request(URL)
	with urlopen(dirReq) as f:
		text = f.read()
	dirLines = [bytes_.decode() for bytes_ in text.split(b'\r\n')]
	allFileNames = [x[56:] for x in dirLines if x!='']
	accum = []
	for fName in allFileNames:
		req = Request(URL + fName)
		with urlopen(req) as f:
			page = f.read()
		lines = [bytes_.decode() for bytes_ in page.split(b'\n')]
		siteName = lines[0]
		latLonVersion = lines[1].split()
		data = [x.split() for x in lines[2:]]
		minuteIntervals = ['0']
		hourlyReads = [x for x in data if len(x) >= 5 and x[5] in minuteIntervals]
		hourlyReadsSub = [{'col{}'.format(c): row[c] for c in range(len(row))} for row in hourlyReads]
		accum.extend(hourlyReadsSub)
		print('processed file {}'.format(fName))
	return accum

def create_tsv(data, radiation_type, site, year):
	'''Create tsv file from dict '''
	column_count = len(data[0])
	with open('{}-{}-{}.tsv'.format(radiation_type, site, year), 'w', newline='') as f:
		output = csv.DictWriter(f, fieldnames=['col{}'.format(x) for x in range(column_count)], delimiter='\t')
		for item in data:
			output.writerow(item)

def get_radiation_data(radiation_type, site, year, out_file=None):
	'''Get solard or surfrad data. Optional export to csv with out_file option'''
	allYears = getRadiationYears(radiation_type, site, year)
	if out_file is not None:
		create_tsv(allYears, radiation_type, site, year)
	else:
		return allYears

def get_diffuse_solar_component(solarTotalTransmission):
	"""
	Td = TT [1 -- exp {0.6 (1 --B/TT)/(B -- 0.4)}] 
	Where Td = Diffuse solar component
	"""
	#If no solar detected, return 0
	if solarTotalTransmission <= 0:
		return 0
	#B constant at 0.76 per paper
	B = 0.76
	#Multipy solar measurements by 0.0864
	#Because measurements are in in W/second, equation uses MJ/day
	solarTotalTransmission = solarTotalTransmission * 0.0864
	exponent = 0.6 * (1-(B/solarTotalTransmission))/(B-0.4)
	brackets = 1 - exp(exponent)
	T_diffuse = solarTotalTransmission * brackets
	# if T_diffuse < 0:
		#Problem is when brackets is negative
		#Brackets becomes negative becayse exp is greater
		#than 1
		# print(exponent, brackets)
	#Convert from  MJ to J
	T_diffuse = T_diffuse * (10**6)
	#Convert from J/day to W
	T_diffuse = T_diffuse * 0.000012
	return abs(T_diffuse)


def _tests():
	print('weather.py tests currently disabled to keep them from sending too many HTTP requests.')
	from tempfile import mkdtemp
	tmpdir = mkdtemp()
	print("Beginning to test weather.py in", tmpdir)
	# Testing zipCodeToClimateName (Certain cases fail)
	print(zipCodeToClimateName('75001'))
	# print(zipCodeToClimateName('07030')) # Doesn't work
	print(zipCodeToClimateName('64735'))
	# assert ('MO-KANSAS_CITY', 30) == zipCodeToClimateName('64735') # Assertion Fails
	print(airportCodeToLatLon("IAD"))
	# Testing USCRN (Works)
	print('USCRN (NOAA) data pulled to ' + tmpdir)
	data = pullUscrn('2017', 'KY_Versailles_3_NNW', "IRRADIENCE_DIFFUSE") # Does not write to a file by itself
	# print(data)
	# import matplotlib.pyplot as plt
	# plt.plot(data)
	# plt.show()
	# Testing ASOS (Works)
	pullAsos('2017','CHO', 'tmpc') # Does not write to a file by itself
	print('ASOS (Iowa) data pulled to ' + tmpdir)
	pullAsosStations(os.path.join(tmpdir, 'asosStationTable.csv'))
	# Testing DarkSky (Works as long as you have an API key)
	# pullDarksky(2018, 36.64, -93.30, 'temperature', path=tmpdir)
	# print('Darksky data pulled to ' + tmpdir)
	# Testing tmy3 (Works)
	tmy3_pull(nearest_tmy3_station(41, -78), out_file=os.path.join(tmpdir, 'tmy3_test.csv'))
	# Testing getRadiationYears (Works, but not used anywhere)
	# get_radiation_data('surfrad', 'Boulder_CO', 2019, True)
	# get_radiation_data('solrad', 'bis', 2019)
	# Testing NSRDB (Works, but not used anywhere)
	nsrdbkey = 'rnvNJxNENljf60SBKGxkGVwkXls4IAKs1M8uZl56'
	get_nrsdb_data('psm',-99.49218,43.83452,'2017', nsrdbkey, interval=60, filename=os.path.join(tmpdir, 'psm.csv'))
	# print(get_nrsdb_data('psm',-99.49218,43.83452,'2017', nsrdbkey, interval=60))
	# get_nrsdb_data('psm_tmy',-99.49218,43.83452,'tdy-2017', nsrdbkey, filename='psm_tmy.csv')
	# print(get_nrsdb_data('psm_tmy',-99.49218,43.83452,'tdy-2017', nsrdbkey))
	# get_nrsdb_data('suny',77.1679,22.1059,'2014', nsrdbkey, filename='suny.csv')
	# get_nrsdb_data('spectral_tmy',77.08007,20.79720,'tmy', nsrdbkey, filename='spectral_tmy.csv')

if __name__ == "__main__":
	_tests()
'''
Pull weather data from various sources.
Source options include NOAA's USCRN, Iowa State University's METAR, and Weather Underground (currently deprecated).
'''

import os, urllib, urllib2, requests, csv, re, json
from os.path import join as pJoin
from datetime import timedelta
from dateutil.parser import parse as parse_dt
from datetime import datetime as dt
from urllib2 import urlopen

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
	firstDT = dt(int(year), 1, 1)
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
    with open(filePath, 'wb') as csvfile:
    	fieldnames = ['Station Id', 'Station Name', 'County', 'State', 'Latitude', 'Longitude', 'Elevation', 'Time Zone']
    	csvwriter = csv.DictWriter(csvfile, delimiter=',', fieldnames=fieldnames)
    	for network in networks:
			current = []
			current.append(network)
			uri = ("https://mesonet.agron.iastate.edu/"
			"geojson/network/%s.geojson") % (network,)
			data = urlopen(uri)
			jdict = json.load(data)
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

def pullDarksky(year, lat, lon, datatype, units='si', api_key = os.environ.get('DARKSKY',''), path = None):
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
			with open(filename, 'rb') as csvfile:
				reader = csv.reader(csvfile)
				in_csv = [row for row in reader]
			index = in_csv[0].index(datatype)
		except IndexError:
			print 'Requested datatype not present in cache, an attempt will be made to fetch from the API'
		except IOError:
			print 'Cache not found, data will be fetched from the API'	
	#now we begin the actual scraping

	#behold: a convoluted way to get a list of days in a year
	times = list(date_range('{}-01-01'.format(year), '{}-12-31'.format(year)))
	#time.isoformat() has no tzinfo in this case, so darksky parses it as local time
	urls = ['https://api.darksky.net/forecast/%s/%s,%s?exclude=daily&units=%s' % ( api_key, coords, time.isoformat(), units ) for time in times]
	data = [requests.get(url).json() for url in urls]

	#a fun little annoyance: let's de-unicode those strings
	def ascii_me(obj):
		if isinstance(obj, unicode):
			return obj.encode('ascii','ignore')
		if isinstance(obj, list):
			return map(ascii_me, obj)
		if isinstance(obj, dict):
			new_dict = dict()
			for k, v in obj.iteritems():
				k = k.encode('ascii','ignore') if type(k) is type(u'') else k
				new_dict[k] = ascii_me(v)
			return new_dict
		else:
			return obj

	data = ascii_me(data)
	out = []
	
	if path:
			# determine the columns from the first day of data
			columns = data[0]['hourly']['data'][0].keys()
			out_csv = [columns]
	# parse our json-dict
	for day in data:
		for hour in day['hourly']['data']:
			if path:
				out_csv.append( [hour.get(key) for key in columns] )
			out.append(hour.get(datatype))

	if path:
		with open(filename, 'wb') as csvfile:
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
		"SOIL_TEMP_100": 37 }
	assert datatype in datatypeDict, "This datatype isn't listed in options!"
	datatypeID = datatypeDict[datatype]
	return [float(x.split()[datatypeID]) for x in r.text.splitlines() if len(x) != 0]

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
			f = urllib.urlretrieve(address, filename)
		except:
			print("ERROR: unable to get data from URL " + address)
			continue # Just try to grab the next one.
		work_day = work_day + timedelta(days = 1) # Advance one day

def airportCodeToLatLon(airport):
	''' Airport three letter code -> lat/lon of that location. 
		Dataset: https://opendata.socrata.com/dataset/Airport-Codes-mapped-
			to-Latitude-Longitude-in-the-/rxrh-4cxm '''
	omfDir = os.path.dirname(os.path.abspath(__file__))
	with open(pJoin(omfDir, 'static/Airports.csv')) as f:
		for m in list(csv.reader(f))[1:]:
			if m[0] == airport:
				return (m[1], m[2])
	print 'Airport not found: ', airport
	lat = float(raw_input('Please enter latitude manually:'))
	lon = float(raw_input('Please enter longitude manually:'))
	return (lat, lon)

def zipCodeToClimateName(zipCode):
	''' Given a zipcode, return the closest city for which there's weather data. 
	* This will give nearest data within state. If zip code is in NJ on
		border of NYC, Hoboken (07030) for example, it will return Newark
		instead of NYC.
	* Zip code lat/lon/city/state data taken from https://www.gaslampmedia.com
		/download-zip-code-latitude-longitude-city-state-county-csv/ '''
	assert isinstance(zipCode, basestring), "To prevent leading zero errors, input zipcode as string"
	omfDir = os.path.dirname(os.path.abspath(__file__))
	zipCsvPath = pJoin(omfDir, "static", "zip_codes_altered.csv")
	# Find the state, city, lat, lon for given zipcode
	with open(zipCsvPath, 'rt') as f:
		try:
			'''All zipcodes are unique. len(row) will be either 1 or 0. Error 
				would be raised by calling the zero index on an empty array.'''
			row = [r for r in list(csv.reader(f))[1:] if r[0] == zipCode][0]
		except:
			raise Exception("Data not available: " + zipCode)
		zipState = row[4]
		ziplatlon = row[1], row[2]
	# Collect data from every zipcode in state
	with open(zipCsvPath, 'rt') as f:
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

def _tests():
	print 'weather.py tests currently disabled to keep them from sending too many HTTP requests.'
	# tmpdir .mkdtemp()
	# print "Beginning to test weather.py in", tmpdir
	# print zipCodeToClimateName('75001')
	# print zipCodeToClimateName('07030')
	# print zipCodeToClimateName('64735')
	# assert ('MO-KANSAS_CITY', 30) == zipCodeToClimateName('64735')
	# print airportCodeToLatLon("IAD")
	# # Testing USCRN
	# pullUscrn('2017', 'KY_Versailles_3_NNW', 'T_CALC')
	# print 'USCRN (NOAA) data pulled to ' + tmpdir
	# # Testing ASOS
	# pullAsos('2017','CHO', 'tmpc')
	# print 'ASOS (Iowa) data pulled to ' + tmpdir
	# pullAsosStations('./asosStationTable.csv')

if __name__ == "__main__":
	_tests()

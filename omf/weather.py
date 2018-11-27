'''
Pull weather data from various sources.
Source options include NOAA's USCRN, Iowa State University's METAR, and Weather Underground (currently deprecated).
'''

import os, urllib, urllib2, requests, csv, re
from os.path import join as pJoin
from datetime import timedelta, datetime
from dateutil.parser import parse as parse_dt
from datetime import datetime as dt
from bs4 import BeautifulSoup

def pullAsos(year, station, datatype):
	'''This model pulls hourly data for a specified year and ASOS station. 
	* ASOS is the Automated Surface Observing System, a network of about 900 
		weater stations, they collect data at hourly intervals, they're run by 
		NWS, FAA, and DOD, and there is data going back to 1901 in some sites.
	* AKA METAR data, which is the name of the format its stored in.
	* For ASOS station code: https://www.faa.gov/air_traffic/weather/asos/
	* Note for USA stations (beginning with a K) you must NOT include the 'K' '''
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
	''' Download weather CSV data to workDir. 1 file for each day between start and 
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
	''' Airport three letter code -> lat/lon of that location. '''
	# https://opendata.socrata.com/dataset/Airport-Codes-mapped-to-Latitude-Longitude-in-the-/rxrh-4cxm
	# ^^^ If this function is ever used, consider adding this csv! it'll definitely be faster
	try:
		url2 = urllib2.urlopen('http://www.airport-data.com/airport/'+airport+'/#location')
		# print 'http://www.airport-data.com/airport/'+airport+'/#location'
		soup = BeautifulSoup(url2, "html.parser")
		latlon_str = str(soup.find('td', class_='tc0', text='Longitude/Latitude:').next_sibling.contents[2])
		p = re.compile('([0-9\.\-\/])+')
		latlon_val = p.search(latlon_str)
		latlon_val = latlon_val.group()
		latlon_split=latlon_val.split('/') #latlon_split[0] is longitude; latlon_split[1] is latitude
		lat = float(latlon_split[1])
		lon = float(latlon_split[0])
	except urllib2.URLError, e:
		print 'Requested URL generated error code:', e.code
		lat = float(raw_input('Please enter latitude manually:'))
		lon = float(raw_input('Please enter longitude manually:'))
	return (lat,lon)

def zipCodeToClimateName(zipCode):
	''' Given a zipcode, return the closest city for which there's weather data. 
	* This will give nearest data within state. If zip code is in NJ on
		border of NYC, Hoboken (07030) for example, it will return Newark
		instead of NYC.
	* Zip code lat/lon/city/state data taken from https://www.gaslampmedia.com
		/download-zip-code-latitude-longitude-city-state-county-csv/ '''
	assert isinstance(zipCode, basestring), "To prevent leading zero errors, input zipcode as string"
	
	omfDir = os.path.dirname(os.path.abspath(__file__))
	zipCsvPath = pJoin(omfDir, "static", "zip_codes_states.csv")

	# Find the state, city, lat, lon for given zipcode
	with open(zipCsvPath, 'rt') as f:
		try:
			row = [r for r in csv.reader(f) if r[0] == zipCode][0]
			assert float(row[1]), float(row[2])
			'''
			All zipcodes are unique. len(row) will be either 1 or 0. Error 
				would be raised by calling the zero index on an empty array.
			HACK: if there are empty columns, they can't convert to floats.
				Consider removing rows w empty columns from csv. '''
		except:
			raise Exception("Invalid Zipcode entered: " + zipCode)
		zipState = row[4]
		ziplatlon = row[1], row[2]

	# Collect data from every zipcode in state
	with open(zipCsvPath, 'rt') as f:
		cityData = [r for r in csv.reader(f) if r[4] == zipState and r[1] != ''] # HACK: again, remove empty rows from CSV
	# Collect all names of cities with data from state. Remove the state abbr. from beginning and '.tmy2' from end.
	citiesInState = [cn[3:-5] for cn in os.listdir(pJoin(omfDir, 'data', 'Climate')) if zipState == cn[:2]]

	# Approximate closest city with data to given zipcode
	foundCity = None
	lowestDistance = float('inf')
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

	# int(round((float(foundCity[1])-10)/5.0)*5.0) was 'latforpvwatts' listed as 30 below.
	# It is never used in codebase. Removal pending.
	assert foundCity != None, "A city is spelled differently between two datasets. Please notify the OMF team."
	return '{}-{}'.format(zipState, foundCity), 30

def _tests():
	print 'weather.py tests currently disabled to keep them from sending too many HTTP requests.'
	# tmpdir .mkdtemp()
	# print "Beginning to test weather.py in", tmpdir
	# print zipCodeToClimateName('75001')
	# print zipCodeToClimateName('07030')
	# print zipCodeToClimateName('64735')
	# assert ('MO-KANSAS_CITY', 30) == zipCodeToClimateName('64735')
	# assert (38.947444, -77.459944) == airportCodeToLatLon("IAD"), "airportCode lookup failed."
	# # Testing USCRN
	# pullUscrn('2017', 'KY_Versailles_3_NNW', 'T_CALC')
	# print 'USCRN (NOAA) data pulled to ' + tmpdir
	# # Testing ASOS
	# pullAsos('2017','CHO', 'tmpc')
	# print 'ASOS (Iowa) data pulled to ' + tmpdir

if __name__ == "__main__":
	_tests()
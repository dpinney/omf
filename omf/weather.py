'''
Pull weather data from various sources.
Source options include NOAA's USCRN, Iowa State University's METAR, and Weather Underground (currently deprecated).
'''

import os, urllib, urllib2, requests, csv, math, re, tempfile
from os.path import join as pJoin
from datetime import timedelta, datetime
from bs4 import BeautifulSoup


def pullAsos(year, station, datatype):
	'''This model pulls the hourly temperature for the specified year and ASOS station
	ASOS is the Automated Surface Observing System, a network of about 900 weater stations, they collect data at hourly intervals, they're run by NWS + FAA + DOD, and there is data going back to 1901 for at least some sites.
	This data is also known as METAR data, which is the name of the format its stored in.
	The year cannot be the current year.
	For ASOS station code: https://www.faa.gov/air_traffic/weather/asos/
	Note for USA stations (beginning with a K) you must NOT include the 'K'
	This model will output a folder path, open that path and you will find a csv file containing your data
	For years before 1998 there may or may not be any data, as such the datapull can fail for some years'''
	url = ('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=' + station + '&data=' + datatype + '&year1=' + year + 
		'&month1=1&day1=1&year2=' + str(int(year)+1) + '&month2=1&day2=1&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=1&report_type=2')
	r = requests.get(url)
	data = r.text
	return data

def pullUscrn(year, station, datatype):
	'''Pulls hourly weather data from NOAA's quality controlled USCRN dataset.
	Documentation is at https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/README.txt
	For a given year, weather station, and datatype, write 8760 hourly weather data (temp, humidity, etc.) to outputPath.
	for list of available stations go to: https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02'''
	datatypeDict = {
		"T_CALC":9,
		"T_HR_AVG":10,
		"T_MAX":11,
		"T_MIN":12,
		"P_CALC":13,
		"SOLARAD":14,
		"SOLARAD_MAX":16,
		"SOLARAD_MIN":18,
		"SUR_TEMP":21,
		"SUR_TEMP_MAX":23,
		"SUR_TEMP_MIN":25,
		"RH_HR_AVG":27,
		"SOIL_MOISTURE_5":29,
		"SOIL_MOISTURE_10":30,
		"SOIL_MOISTURE_20":31,
		"SOIL_MOISTURE_50":32,
		"SOIL_MOISTURE_100":33,
		"SOIL_TEMP_5":34,
		"SOIL_TEMP_10":35,
		"SOIL_TEMP_20":36,
		"SOIL_TEMP_50":37,
		"SOIL_TEMP_100":38}
	try:
		datatypeID = datatypeDict[datatype]
	except:
		datatypeID = 1
	#need to have handling for stupid inputs #REPLACE WITH A DICTIONARY
	url = 'https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/' + year + '/CRNH0203-' + year + '-' + station + '.txt'
	r = requests.get(url)
	data = r.text
	matrix = [x.split() for x in data.split('\n')]
	tempData = []
	for i in range(8760):
		tempData.append(matrix[i][datatypeID])
	return tempData

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
	''' Maps zipcode from excel data to city, state, lat/lon. '''
	# From excel file at: https://www.gaslampmedia.com/download-zip-code-latitude-longitude-city-state-county-csv/
	def compareLatLon(LatLon, LatLon2):
		differenceLat = float(LatLon[0]) - float(LatLon2[0])
		differenceLon = float(LatLon[1]) - float(LatLon2[1])
		distance = math.sqrt(math.pow(differenceLat, 2) + math.pow(differenceLon,2))
		return distance
	def safeListdir(path):
		try: return os.listdir(path)
		except:	return []
	###
	omfDir = os.path.dirname(os.path.abspath(__file__))
	path = pJoin(omfDir,"data","Climate")
	zipCodeStr = str(zipCode)
	climateNames = [x[:-5] for x in safeListdir(path)]
	climateCity = []
	lowestDistance = 1000
	# Parse .csv file with city/state zip codes and lat/lon
	zipCsvPath = pJoin(omfDir,"static","zip_codes_states.csv")
	with open(zipCsvPath, 'rt') as f:
		reader = csv.reader(f, delimiter=',')
		for row in reader:
			for field in row:
				if field == zipCodeStr:
					zipState = row[4]
					zipCity = row[3]
					ziplatlon  = row[1], row[2]
	# Looks for climate data by looking at all cities in that state.
	# TODO: check other states too.
	# Filter only the cities in that state:
	try:
		for x in range(0, len(climateNames)):
			if (zipState+"-" in climateNames[x]):
				climateCity.append(climateNames[x])
	except:
		raise ValueError('Invalid Zipcode entered:', zipCodeStr)
	climateCity = [w.replace(zipState+"-", '') for w in climateCity]
	# Parse the cities distances to zipcode city to determine closest climate:
	for x in range (0,len(climateCity)):
		with open(zipCsvPath, 'rt') as f:
			reader = csv.reader(f, delimiter=',')
			for row in reader:
				city = row[3].replace (" ", "_")
				if ((row[4].lower() == zipState.lower()) and (city.lower() == str(climateCity[x]).lower())):
					climatelatlon  = row[1], row[2]
					try:
						distance = compareLatLon(ziplatlon, climatelatlon)
						if (distance < lowestDistance):
							latforpvwatts = int(round((float(climatelatlon[0])-10)/5.0)*5.0)
							lowestDistance = distance
							found = x
					except:
						pass
	climateName = zipState + "-" + climateCity[found]
	return climateName, latforpvwatts

def _tests():
	print 'weather.py tests currently disabled to keep them from sending too many HTTP requests.'
	# tmpdir = tempfile.mkdtemp()
	# print "Beginning to test weather.py in", tmpdir
	# assert ('MO-KANSAS_CITY',30) == zipCodeToClimateName(64735)
	# assert (38.947444, -77.459944) == airportCodeToLatLon("IAD"), "airportCode lookup failed."
	# # Testing USCRN
	# pullUscrn('2017', 'KY_Versailles_3_NNW', 'T_CALC')
	# print 'USCRN (NOAA) data pulled to ' + tmpdir
	# # Testing ASOS
	# pullAsos('2017','CHO', 'tmpc')
	# print 'ASOS (Iowa) data pulled to ' + tmpdir

if __name__ == "__main__":
	_tests()
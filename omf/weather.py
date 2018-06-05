''' weather.py pulls weather data from various sources.


'''

import os, urllib, json, csv, math, re, tempfile, shutil, urllib2, sys
from os.path import join as pJoin
from datetime import timedelta, datetime
from math import modf
from bs4 import BeautifulSoup

def _downloadWeatherWunderground(start, end, airport, workDir):
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

def _airportCodeToLatLon(airport):
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
	print "weather.py tests disabled to stop sending too many API requests to airport-data.com, nrel.gov, etc."
	# print "Beginning to test weather.py"
	# workDir = tempfile.mkdtemp()
	# print "IAD lat/lon =", _airportCodeToLatLon("IAD")
	# assert (38.947444, -77.459944)==_airportCodeToLatLon("IAD"), "airportCode lookup failed."
	# print "Weather downloading to", workDir
	# assert None==_downloadWeather("2010-03-01", "2010-04-01", "PDX", workDir)
	# print "Peak solar extraction in", workDir
	# assert None==_getPeakSolar("PDX", workDir, dniScale=1.0, dhiScale=1.0, ghiScale=1.0)
	# print "Pull weather and solar data together in", workDir
	# assert None==_processWeather("2010-03-01", "2010-04-01", "PDX", workDir)
	# print "Testing the full process together."
	# assert None==makeClimateCsv("2010-07-01", "2010-08-01", "IAD", pJoin(tempfile.mkdtemp(),"weatherDCA.csv"), cleanup=True)
	# print "Testing the zip code to climate name conversion"
	# assert ('MO-KANSAS_CITY',30)==zipCodeToClimateName(64735)

if __name__ == "__main__":
	_tests()
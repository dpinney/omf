''' Pulls hourly weather data from NOAA's quality controlled USCRN dataset.
Documentation is at https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/README.txt
'''

import requests, csv, tempfile, os

def pullWeather(year, station, parameter, outputPath):
	'''
	For a given year and weather station, write 8760 hourly weather data (temp, humidity, etc.) to outputPath.
	for list of available stations go to: https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02
	'''
	if parameter == "T_CALC":
		parameter = 9
	elif parameter == "T_HR_AVG":
		parameter = 10
	elif parameter == "T_MAX":
		parameter = 11
	elif parameter == "T_MIN":
		parameter = 12
	elif parameter == "P_CALC":
		parameter = 13
	elif parameter == "SOLARAD":
		parameter = 14
	elif parameter == "SOLARAD_FLAG":
		parameter = 15
	elif parameter == "SOLARAD_MAX":
		parameter = 16
	elif parameter == "SOLARAD_MAX_FLAG":
		parameter = 17
	elif parameter == "SOLARAD_MIN":
		parameter = 18
	elif parameter == "SOLARAD_MIN_FLAG":
		parameter = 19
	elif parameter == "SUR_TEMP_TYPE":
		parameter = 20
	elif parameter == "SUR_TEMP":
		parameter = 21
	elif parameter == "SUR_TEMP_FLAG":
		parameter = 22
	elif parameter == "SUR_TEMP_MAX":
		parameter = 23
	elif parameter == "SUR_TEMP_MAX_FLAG":
		parameter = 24
	elif parameter == "SUR_TEMP_MIN":
		parameter = 25
	elif parameter == "SUR_TEMP_MIN_FLAG":
		parameter = 26
	elif parameter == "RH_HR_AVG":
		parameter = 27
	elif parameter == "RH_HR_AVG_FLAG":
		parameter = 28
	elif parameter == "SOIL_MOISTURE_5":
		parameter = 29
	elif parameter == "SOIL_MOISTURE_10":
		parameter = 30
	elif parameter == "SOIL_MOISTURE_20":
		parameter = 31
	elif parameter == "SOIL_MOISTURE_50":
		parameter = 32
	elif parameter == "SOIL_MOISTURE_100":
		parameter = 33
	elif parameter == "SOIL_TEMP_5":
		parameter = 34
	elif parameter == "SOIL_TEMP_10":
		parameter = 35
	elif parameter == "SOIL_TEMP_20":
		parameter = 36
	elif parameter == "SOIL_TEMP_50":
		parameter = 37
	elif parameter == "SOIL_TEMP_100":
		parameter = 38

	url = 'https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/' + year + '/CRNH0203-' + year + '-' + station + '.txt'
	r = requests.get(url)
	data = r.text
	matrix = [x.split() for x in data.split('\n')]
	tempData = []
	for i in range(8760):
		tempData.append(matrix[i][parameter])
	with open(outputPath, 'wb') as file:
		writer = csv.writer(file)
		writer.writerows([[x] for x in tempData])

def _tests():
	tmpdir = tempfile.mkdtemp()
	pullWeather('2017', 'KY_Versailles_3_NNW', "T_CALC", os.path.join(tmpdir, 'weatherNoaaTemp.csv'))
	print 'Weather testing complete in ' + tmpdir

if __name__ == '__main__':
	_tests()
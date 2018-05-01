''' Pulls hourly weather data from NOAA's quality controlled USCRN dataset.
Documentation is at https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/README.txt
'''

import requests, csv, tempfile, os

def pullWeather(year, station, outputPath):
	'''
	For a given year and weather station, write 8760 hourly weather data (temp, humidity, etc.) to outputPath.
	for list of available stations go to: https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02
	'''
	url = 'https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/' + year + '/CRNH0203-' + year + '-' + station + '.txt'
	r = requests.get(url)
	data = r.text
	matrix = [x.split() for x in data.split('\n')]
	#TODO: use matrix to pull out an arbitrary attribute.
	tempData = []
	for x in range(0,8760):
		temp = ''
		for y in range(x*244+59,x*244+64):
			temp+=data[y]
		tempData.append(float(temp))
	with open(outputPath, 'wb') as myfile:
		wr = csv.writer(myfile,lineterminator = '\n')
		for x in range(0,8760): 
			wr.writerow([tempData[x]])

def _tests():
	tmpdir = tempfile.mkdtemp()
	pullWeather('2017', 'KY_Versailles_3_NNW', os.path.join(tmpdir, 'weatherNoaaTemp.csv'))
	print 'Weather testing complete in ' + tmpdir

if __name__ == '__main__':
	_tests()
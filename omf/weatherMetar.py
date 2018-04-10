'''This model pulls the hourly temperature for the specified year and ASOS station
ASOS is the Automated Surface Observing System, a network of about 900 weater stations, they collect data at hourly intervals, they're run by NWS + FAA + DOD, and there is data going back to 1901 for at least some sites.
This data is also known as METAR data, which is the name of the format its stored in.
The year cannot be the current year.
For ASOS station code: https://www.faa.gov/air_traffic/weather/asos/
This model will output a folder path, open that path and you will find a csv file containing your data
For years before 1998 there may or may not be any data, as such the datapull can fail for some years
'''

import requests, csv, tempfile, os

def pullWeather(year, station, datatype, outputDir):
	url = ('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=' + station + '&data=' + datatype + '&year1=' + year + 
		'&month1=1&day1=1&year2=' + year + '&month2=12&day2=31&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=1&report_type=2')
	r = requests.get(url)
	data = r.text
	tempData = []
	for x in range(8760):
		tempData.append(((data.partition(station + ',')[2]).partition('\n')[0]).partition(',')[2])
		data = data.partition(tempData[x])[2]
	with open(outputDir, 'wb') as myfile:
		wr = csv.writer(myfile,lineterminator = '\n')
		for x in range(0,8760): 
			wr.writerow([tempData[x]])

'''datatype options: 
	'relh' for relative humidity
	'tmpc' for temperature in celsius
'''
def _tests():
	tmpdir = tempfile.mkdtemp()
	pullWeather('2017','CGS', 'relh', os.path.join(tmpdir, 'weatherMetar.csv'))
	print tmpdir

if __name__ == '__main__':
	_tests()
import requests, csv, json, time, collections

DEFAULT_TOKEN = 'JkyCcxgvGhNUdDCvHCeBeaZQdDNQEJtw'

def checkDatasets(token, zipCode):
	# Returns the list of datasets and dates available for a given zipcode.
	url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets?locationid=ZIP:' + zipCode + '&limit=1000')
	r = requests.get(url, headers={'token':DEFAULT_TOKEN})
	return r.json()

def pullOneDayHourly(token, zipCode, year, month, day):
	'''Return all metrics at hourly level for the given day.'''
	url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=NORMAL_HLY&datatype=HLY-TEMP-NORMAL&locationid=ZIP:' + zipCode + \
		'&units=metric&startdate=' + year + '-' + month + '-' + day + 'T00:00:00&enddate=' + \
		year + '-' + month + '-' + day + 'T23:00:00&limit=1000')
	r = requests.get(url, headers={'token':token})
	return r.json()

def annualDataHourlyToCsv(token, zipCode, dataTypeList, csvPath):
	'''Write a CSV at csvPath with a year of hourly data with columns of each datatype in the dataTypeList.'''
	#TODO: implement dataTypeList
	url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets?locationid=ZIP:' + zipCode + '&limit=1000')
	# This checks if data is available for the Zip entered and returns the dates it is available
	r = requests.get(url, headers={'token':DEFAULT_TOKEN})
	x = str(r.text)
	print x
	txt = 'empty'
	dataAvailable = 0
	#TODO: use json.loads(x) to parse JSON from a string.
	while txt != '':
		txt = x.partition('{')[2]
		x = txt.partition('}')[2]
		txt = txt.partition('}')[0]
		if len((txt.partition('NORMAL_HLY')[0]).partition('Normals Hourly')[2]) > 0:
			dataAvailable = 1
			startDate = (txt.partition('mindate":"')[2]).partition('",')[0]
			endDate = (txt.partition('maxdate":"')[2]).partition('",')[0]
	if dataAvailable == 0:
		print 'No temperature data is available for this zip code'
	else:
		print 'We have found temperature data for the zip code: ' + str(zipCode) + '\nWith start date: ' + str(startDate) + '\nAnd end date: ' + str(endDate)
	# Stores the number of days in each month
	calendar = collections.OrderedDict()
	calendar['01'] = 31
	calendar['02'] = 28
	calendar['03'] = 31
	calendar['04'] = 30
	calendar['05'] = 31
	calendar['06'] = 30
	calendar['07'] = 31
	calendar['08'] = 31
	calendar['09'] = 30
	calendar['10'] = 31
	calendar['11'] = 30
	calendar['12'] = 31
	year = startDate.partition('-')[0]
	# Pull the full dataset and write it.
	if dataAvailable == 1:
		with open(csvPath,'w') as file:
			writer = csv.writer(file,lineterminator = '\n')
			for month in calendar:
				for day in range(calendar[month]):
					day = day+1
					if len(str(day)) == 1:
						day = '0' + str(day)
					else:
						day = str(day)
					url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=NORMAL_HLY&datatype=HLY-TEMP-NORMAL&locationid=ZIP:' + zipCode + 
						'&units=metric&startdate=' + year + '-' + month + '-' + day + 'T00:00:00&enddate=' + year + '-' + month + '-' + day + 'T23:00:00&limit=1000')
					#time.sleep(0.1) #SET TO 0.2 WHEN NOT TESTING
					r = requests.get(url, headers={'token':DEFAULT_TOKEN})
					text = r.text
					for hour in range(24):
						if len(str(hour)) == 1:
							hour = '0' + str(hour)
						else:
							hour = str(hour)
						x = text.partition('HLY-TEMP-NORMAL')[2]
						text = x.partition('}')[2]
						x = x.partition('}')[0]
						x = x.partition('value":')[2]
						timeStamp = month + '/' + day + '/' + year + ' ' + str(hour) + ':00:00'
						writer.writerow([timeStamp,str(x)])
						#writer.writerow([str(x)])

def _tests():
	#checkDatasets(DEFAULT_TOKEN, '22202')
	#pullOneDayHourly(DEFAULT_TOKEN, '22202', '2010','01','01')
	annualDataHourlyToCsv(DEFAULT_TOKEN, '11430', [], 'weatherNoaaTemp.csv')

_tests()
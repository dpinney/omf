import requests, csv, json, time, collections

DEFAULT_TOKEN = 'JkyCcxgvGhNUdDCvHCeBeaZQdDNQEJtw'

def checkDatasets(token, zipCode):
	# Returns the list of datasets and dates available for a given zipcode.
	url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets?locationid=ZIP:' + zipCode + '&limit=1000')
	r = requests.get(url, headers={'token':DEFAULT_TOKEN})
	# jsonData = json.loads(str(r.text))
	# size =jsonData['metadata']['resultset']['count']
	# for x in range(size):
	# 	print jsonData['results'][x]['id']
	return r.json()

def pullOneDayHourly(token, zipCode, year, month, day):
	'''Return all metrics at hourly level for the given day.'''
	url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=NORMAL_HLY&datatype=HLY-TEMP-NORMAL&locationid=ZIP:' + zipCode + \
		'&units=metric&startdate=' + year + '-' + month + '-' + day + 'T00:00:00&enddate=' + \
		year + '-' + month + '-' + day + 'T23:00:00&limit=1000')
	r = requests.get(url, headers={'token':token})
	return r.json()

def annualDataHourlyToCsv(token, zipCode, dataSet, dataTypeList, csvPath):
	'''Write a CSV at csvPath with a year of hourly data with columns of each datatype in the dataTypeList.'''
	#TODO: implement dataTypeList
	# print 'Starting annualDataHourlyToCsv'
	url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets?locationid=ZIP:' + zipCode + '&limit=1000')
	#for x in range(numDataTypes):

	# This checks if data is available for the Zip entered and returns the dates it is available
	r = requests.get(url, headers={'token':DEFAULT_TOKEN})
	x = str(r.text)
	jsonData = json.loads(str(r.text))
	size =jsonData['metadata']['resultset']['count']
	for x in range(size):
		if jsonData['results'][x]['id'] == dataSet:
			startDate = jsonData['results'][x]['mindate']
			endDate = jsonData['results'][x]['maxdate']
			dataAvailable = 1
			# print 'Data Found'
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
	try:
		year = startDate.partition('-')[0]
	except:
		raise Exception('No Data Available for that zipcode')
	# Pull the full dataset and write it.
	if type(dataTypeList) is str:
		numDataTypes = 1
	elif type(dataTypeList) is list:
		numDataTypes = len(dataTypeList)
	#print type(dataTypeList)
	if dataAvailable == 1:
		if numDataTypes == 1:
			data = []
		elif numDataTypes == 2:
			data = []
			data1 = []
		elif numDataTypes == 3:
			data = []
			data1 = []
			data2 = []
		elif numDataTypes == 4:
			data = []
			data1 = []
			data2 = []
			data3 = []
		elif numDataTypes == 5:
			data = []
			data1 = []
			data2 = []
			data3 = []
			data4 = []			
		with open(csvPath,'w', newline='') as file:
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
					time.sleep(0.2) #SET TO 0.2 WHEN NOT TESTING
					r = requests.get(url, headers={'token':DEFAULT_TOKEN})
					text = r.text
					jsonData = json.loads(str(r.text))
					size = jsonData['metadata']['resultset']['count']
					if numDataTypes == 1:
						for x in range(size):
							if jsonData['results'][x]['datatype'] == dataTypeList:
									data.append(str(jsonData['results'][x]['value']))
					else:
						for y in dataTypeList:
							for x in range(size):
								if jsonData['results'][x]['datatype'] == y:
									if dataTypeList.index(y) == 0:
										data.append(str(jsonData['results'][x]['value']))
									elif dataTypeList.index(y) == 1:
										data1.append(str(jsonData['results'][x]['value']))
									elif dataTypeList.index(y) == 2:
										data2.append(str(jsonData['results'][x]['value']))
									elif dataTypeList.index(y) == 3:
										data3.append(str(jsonData['results'][x]['value']))
									elif dataTypeList.index(y) == 4:
										data4.append(str(jsonData['results'][x]['value']))
								# if dataTypeList.index(y) == 0:
								# 	data[0].append([str(jsonData['results'][x]['value'])])
								# else:
								# 	data[1].append([str(jsonData['results'][x]['value'])])
								#data[dataTypeList.index(y)].append([str(jsonData['results'][x]['value'])])
								#data.append([str(jsonData['results'][x]['value'])])

								#writer.writerow([str(jsonData['results'][x]['value'])])
			if numDataTypes == 1:
				for x in range(8760):
					writer.writerow([data[x]])
			elif numDataTypes == 2:
				for x in range(8760):
					writer.writerow([data[x],data1[x]])
			elif numDataTypes == 3:
				for x in range(8760):
					writer.writerow([data[x],data1[x],data2[x]])
			elif numDataTypes == 4:
				for x in range(8760):
					writer.writerow([data[x],data1[x],data2[x],data3[x]])
			elif numDataTypes == 5:
				for x in range(8760):
					writer.writerow([data[x],data1[x],data2[x],data3[x],data4[x]])							
			#writer.writerows(data)


def _tests():
	print(checkDatasets(DEFAULT_TOKEN, '40510')) #Lexington, KY (LEX airport)
	print(pullOneDayHourly(DEFAULT_TOKEN, '22202', '2010','01','01'))
	#annualDataHourlyToCsv(DEFAULT_TOKEN, '11430', [], 'weatherNoaaTemp.csv')
	#annualDataHourlyToCsv(DEFAULT_TOKEN, '40510', 'NORMAL_HLY', 'HLY-TEMP-NORMAL', 'weatherNoaaTemp.csv')
	#annualDataHourlyToCsv(DEFAULT_TOKEN, '40510', 'NORMAL_HLY', ['HLY-TEMP-NORMAL','HLY-WIND-1STPCT'], 'weatherNoaaTemp.csv')

if __name__ == '__main__':
	_tests()
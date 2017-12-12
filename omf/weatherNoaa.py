import os, urllib, json, csv, math, re, tempfile, shutil, urllib2, sys
from os.path import join as pJoin
from datetime import timedelta, datetime
from math import modf
import requests
import time
import collections

headers = {'token':'JkyCcxgvGhNUdDCvHCeBeaZQdDNQEJtw'} #token I requested from NOAA

def noaaWeather(token, zipCode, year, month, day):
	pass


############### Trying to pull only u'datatype': u'HLY-TEMP-NORMAL'
# Query Parameters
zipCode = '22202'
year = '2010'
month = '01'
day = '01'

# Build the URL
url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=NORMAL_HLY&datatype=HLY-TEMP-NORMAL&locationid=ZIP:' + zipCode + 
		'&units=metric&startdate=' + year + '-' + month + '-' + day + 'T00:00:00&enddate=' + year + '-' + month + '-' + day + 'T23:00:00&limit=1000')

# Test the query
r = requests.get(url, headers=headers)
print r.json()

########## This checks if data is available for the Zip entered and returns the dates it is available
r = requests.get(url, headers=headers)
x = str(r.text)
txt = 'empty'
dataAvailable = 0
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

####### Stores the number of days in each month
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
##########################
year = startDate.partition('-')[0]
#print year
if dataAvailable == 1:
	with open('weatherNoaaTemp.csv','w') as file:
		writer = csv.writer(file)
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
				r = requests.get(url, headers=headers)
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
					writer.writerow([str(x)])

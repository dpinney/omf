import os, urllib, json, csv, math, re, tempfile, shutil, urllib2, sys
from os.path import join as pJoin
from datetime import timedelta, datetime
from math import modf
from bs4 import BeautifulSoup
import requests
import time
import collections

#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/'
#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/locations?locationcategoryid=CITY&sortfield=name&sortorder=desc'
#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/locations?locationcategoryid=zip&sortfield=name&sortorder=desc'

#https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&locationid=ZIP:28801&startdate=2010-05-01&enddate=2010-05-01
#zipcode = '94501'#'28801'
#startdate = '1945-04-01'#'2010-05-01'
#enddate = '1945-05-01'#'2010-05-01'
#url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&locationid=ZIP:' + zipcode + 
#	'&units=metric&startdate=' + startdate + '&enddate=' + enddate)

#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&stationid=WBAN:23239&startdate=1946-01-01&enddate=1946-12-31&limit=1000'
#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=LCD&locationid=ZIP:94501'
#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=LCD&locationid=WBAN:23239&startdate=1946-01-01&enddate=1946-02-02'

headers = {'token':'JkyCcxgvGhNUdDCvHCeBeaZQdDNQEJtw'} #token I requested from NOAA

###### This search works by taking WBAN inputs and checks if data is available
#url = 'https://www.ncdc.noaa.gov/access-data-service/api/v1/data?dataset=daily-summaries&dataTypes=WT03&stations=WBAN23239&startDate=1952-01-01&endDate=1970-12-31&includeAttributes=true&format=json&limit=1000'
#url = 'https://www.ncdc.noaa.gov/access-data-service/api/v1/data?dataset=global-marine&dataTypes=WIND_DIR,WIND_SPEED&stations=AUCE&startDate=2016-01-01&endDate=2016-01-02'
#url = 'https://www.ncdc.noaa.gov/access-data-service/api/v1/data?dataset=normal-hly&locationid=ZIP:22202'
#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=NORMAL_HLY&locationid=ZIP:22202&startdate=1900-01-01&enddate=2016-01-02'
#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets?NORMAL_HLY/locations/ZIP:22202'

#url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=NORMAL_HLY&datatype=HLY-TEMP-NORMAL&locationid=ZIP:22202&units=metric&startdate=2010-01-01T00:00:00&enddate=2010-12-31T23:00:00&limit=1000'
#HLY-TEMP-NORMAL

'''
zipCode = '22202'
year = '2010'
day = '01'
month = '02'
	#writer.writerows([weather])
#print weather
#weather = []
for hour in range(1):
	if len(str(hour)) == 1:
		hour = '0' + str(hour)
	else:
		hour = str(hour)
	url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=NORMAL_HLY&datatype=HLY-TEMP-NORMAL&locationid=ZIP:' + zipCode + 
		'&units=metric&startdate=' + year + '-01-01T' + hour + ':00:00&enddate=' + year + '-01-01T' + hour + ':00:00&limit=1000')
	time.sleep(0.075) #it says that no more than 5 requests per second can be done but a 0.1 delay is enough
	r = requests.get(url, headers=headers)
	x = r.text
	print x
	#weather.append(x)
	#print x
'''

'''for x in weather:
	x = int(x)#x.encode('utf-8')'''


#print weather
#x = r.json()


'''x = r.text
x = x.partition('HLY-TEMP-NORMAL')[2]
x = x.partition('}')[0]
x = x.partition('value":')[2]
print x'''

############### Trying to pull only u'datatype': u'HLY-TEMP-NORMAL'
zipCode = '11430'#'22202'

######################### this returns the databases that contain data for a given zip code
url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/datasets?locationid=ZIP:' + zipCode + '&limit=1000')
year = '2010'
month = '01'
day = '01'

url = ('https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=NORMAL_HLY&datatype=HLY-TEMP-NORMAL&locationid=ZIP:' + zipCode + 
		'&units=metric&startdate=' + year + '-' + month + '-' + day + 'T00:00:00&enddate=' + year + '-' + month + '-' + day + 'T23:00:00&limit=1000')
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

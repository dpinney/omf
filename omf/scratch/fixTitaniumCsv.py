
import csv
from collections import defaultdict
from operator import itemgetter
from datetime import datetime
from math import sqrt

amiData = []
amiKeys = []
csvFile = '../static/testFiles/TitaniumAMI.csv'
csvDict = csv.DictReader(open(csvFile,'r'))
for row in csvDict:
	for value in row:
		if value != 'Date':
			try:
				datetime_object = datetime.strptime(row['Date'], "%m/%d/%y %I:%M %p")
			except:
				if len(row['Date'])<10:
					row['Date']+=' 0:00'
				datetime_object = datetime.strptime(row['Date'], '%m/%d/%y %H:%M')
			rowObj = {'readDateTime':datetime_object,
					'meterName':'ntpn'+value+'A',
					'wh':row[value],
					# FIX: Pull phase from object; loadModelingAmi code only recognizes one phase from the meter, phase S
					'phase':'S',
					'var': 0.5}
			amiData.append(rowObj)
			if value not in amiKeys:
				amiKeys.append(value)
newlist = sorted(amiData, key=itemgetter('meterName'))

tempList = []
hourlyObj = {}
hourlyList = []
count = 0
for row in newlist:
	if count ==0:
		tempList.append(row)
	meter = row['meterName']
	year = row['readDateTime'].year
	month = row['readDateTime'].month
	day = row['readDateTime'].day
	hour = row['readDateTime'].hour
	if tempList[0]['meterName'] == meter and tempList[0]['readDateTime'].year == year and tempList[0]['readDateTime'].month == month and tempList[0]['readDateTime'].day == day and tempList[0]['readDateTime'].hour == hour and count != 0:
		tempList.append(row)
		count = count + 1
	elif count == 0:
		count = count + 1
	else:
		count = 0
		wh = sum(float(item['wh']) for item in tempList)
		tempList[0]['wh'] = wh
		# VARs = srqt((W/0.98)^2 - W^2)
		tempList[0]['var'] = sqrt((wh/0.98)**2 - wh**2)
		hourlyObj = tempList[0]
		hourlyList.append(hourlyObj)
		length = len(tempList)
		tempList = []
		tempList.append(row)

with open('../static/testFiles/newAmi.csv', 'wb') as csv_file:
    	writer = csv.DictWriter(csv_file, fieldnames=['meterName','phase','readDateTime','wh','var'] ,extrasaction='ignore', delimiter = ',')
    	writer.writeheader()
    	writer.writerows(hourlyList)
		

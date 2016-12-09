''' Convert meter data from EU format to our anomly detection input format. '''
'''A script to read data from inCSV, and write it to outCSV'''
import csv, json
import os
from os.path import join as pJoin
import matplotlib.pyplot as plt
import datetime as datetime
import time 
import pprint as pprint
import operator
import random
import numpy as np 

# Path variables
workDir = os.getcwd()
# Reading the AMI data from .csv file
#inCSV = pJoin(workDir, 'Xample Input - real AMI measurements.csv')
inCSV = pJoin(workDir, 'Xample SMALLER Input - real AMI measurements.csv')

# Other Inputs
MinDetRunTime = 2 # Minimum time (in hours)to detect anomalies 
MinDevFromAve = 5 # The minimum deviation as (percentage %) from the the average power

# The following function puts the datetime on the standerd format
def dateFormatter(dateStr):
	# Try to format a date string to a datetime object.
	toTry = ["%m/%d/%Y %H:%M:%S %p", "%m/%d/%y %H:%M", "%m/%d/%y", "%m/%d/%Y"]
	for dateFormat in toTry:
		try:
			readDateTime = datetime.datetime.strptime(dateStr, dateFormat).isoformat()
			return readDateTime
		except:
			continue
	error = "We don't have a test case for our date: "+dateStr+" :("
	print error
	return error

def readToArr(inCSV):
	# Read data into dict.
	subStationData = []
	with open(inCSV,"r") as amiFile:
			amiReader = csv.DictReader(amiFile, delimiter=',')
			for row in amiReader:
				subStation = row['SUBSTATION']
				meterName = row['METER_ID']
				readDateTime = dateFormatter(row['READ_DTM'])
				kWh = row['READ_VALUE']
				subStationData.append([subStation, meterName, readDateTime, kWh])
	return subStationData

# This sorts the data by Sub--Meter--Time
def sortData(inCSV):
	# Sort data.
	subData = readToArr(inCSV)
	# print "Read in:\n"
	# pprint.pprint(subData[:25])
	# random.shuffle(subData)
	# print "Randomized:\n"
	# pprint.pprint(subData[:25])
	subData = sorted(subData, key=operator.itemgetter(0,1,2), reverse=False)
	# print "Sorted:\n"
	#pprint.pprint(subData[295:310])
	return subData

# Run operationg here:
outArr = sortData(inCSV)
outData = {}
for row in outArr:
        meterName = row[1]
        energyCons = row[3]
        date = row[2]
        if True: # this where you'll check if the meter is in the list
                if outData.get(meterName,'') == '':
                        outData[meterName] = {'energyCons': [energyCons], 'dates' : [date]}
                else:
                        outData[meterName]['energyCons'].append(energyCons)
                        outData[meterName]['dates'].append(date)
i = 0
for key in outData.keys():
	print outData[key]
	i = i+1
	if i == 10:
		break


# output = []
# power = []
# meanPower = []
# for meterName in outData.keys():
# 	energyCons = [int(x) for x in outData[meterName]['energyCons']]
# 	power = np.diff(energyCons)
# 	pMean = [np.mean(power)]* (len(outData[meterName]['energyCons'])-1)
# 	outData[meterName] ['power'] = power
# 	outData[meterName] ['meanPower'] = pMean
# 	outData[meterName] ['dates'] = date
# 	index = [i for i, j in enumerate(outData[meterName]['power']) if j <= MinDevFromAve*0.01*pMean[0]]
# 	Test= np.split(index, np.where(np.diff(index) !=1)[0]+1)
# 	print Test
# 	# for i in range(Test):
# 	# 	if Test[i] >= 5:
# 	# 		print meterName

# # 	if count >= (MinDetRunTime-1):
# # 		print meterName
# # 		print index
# # 		#plt.plot (outData[113560340] ['meanPower'])
# # 		#plt.plot(outData[113560340] ['power'])
# # 		#plt.show()
# # 		eDiv = [0 if y==0 else x/y for x, y in zip(power, pMean)]
# output.append([meterName, date, power])
# # # Write the output.
# # with open(pJoin(workDir,"allOutputData.json"),"w") as outFile:
# # 	json.dump(output, outFile, indent=4)
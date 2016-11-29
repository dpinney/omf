''' Convert meter data from EU format to our anomly detection input format. '''
'''A script to read data from inCSV, and write it to outCSV'''
import csv
import os
from os.path import join as pJoin
import numpy as np 
import matplotlib.pyplot as plt
from datetime import datetime

# Path variables
workDir = os.getcwd()
inCSV = pJoin(workDir, 'Xample SMALLER Input - real AMI measurements.csv')
outCSV = pJoin(workDir, 'AMI Data- Std Format.csv')

# Read and write while reading.
rowNames = ["subStation","meterName", "readDateTime", "kWh"]
balanceCSV = open(pJoin(workDir,outCSV),'wb')
wr = csv.writer(balanceCSV, dialect='excel')
wr.writerow(rowNames)
subStations = []
meterNames = []
readDateTimes = []
kWhs = []
outDataOut =[]
with open(inCSV,"r") as amiFile:
		amiReader = csv.DictReader(amiFile, delimiter=',')
		for i,row in enumerate(amiReader):
			subStation = row ['SUBSTATION']
			meterName = row['METER_ID']
			readDateTime = row['READ_DTM']

			readDateTime.isoformat()
			kWh = row['READ_VALUE']
			outData = [subStation, meterName,readDateTime, kWh]
			meterNames.append(meterName)
			subStations.append(subStation)
			readDateTimes.append(readDateTime)
			kWhs.append(kWh)
			outDataOut.append(outData)

outDataOut.sort(key=lambda x: (x[0], x[1], x[2]))
for row in outDataOut[0:50]: print row

# plotting an example for one meter 


	


#print "Counted %s meters for metername: %s (total :%s)"%(sorted(meterNames).count('103953088'), '103953088', len(meterNames))
#print "Read data from:\n   %s \nWrote it to:\n   %s"%(inCSV, outCSV)
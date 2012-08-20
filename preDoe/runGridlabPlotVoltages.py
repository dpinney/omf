#!/usr/bin/env python
# encoding: utf-8

import sys
import os
from subprocess import call
import csv
import matplotlib.pyplot as p

##################
# Run GridLabD.
##################

os.chdir('C:\\Users\\dwp0\\Dropbox\\OMF\\13 Node CVR\\original 13 node cvr\\')

call(['gridlabd.exe','C:\\Users\\dwp0\\Dropbox\\OMF\\13 Node CVR\\original 13 node cvr\\IEEE_13_house_vvc_2hrDuration.glm'])

##################
# Get the output
##################

# Files we wanna grab.
fileList = ['Voltage_630.csv','Voltage_652.csv','Voltage_671.csv','Voltage_675.csv']
voltMatrix = []


# Function for grabbing some voltages from the output csv.
def file2VoltLists(inFile):
	voltA = []
	voltB = []
	voltC = []

	# function to turn strings like '+23' into positive floats.
	def strClean(x):
		return float(x[1:])

	voltReader = csv.reader(open(inFile))
	for row in voltReader:
		if len(row) > 1 and row[1]!='voltage_A.real':
			voltA.append(strClean(row[1]))
			voltB.append(strClean(row[3]))
			voltC.append(strClean(row[5]))

	return [voltA, voltB, voltC]

# Actually grab voltages.
for fileName in fileList:
	voltMatrix.append(file2VoltLists(fileName))

##################
# Graph the output
##################

for x in xrange(len(voltMatrix)):
	# Choose a subplot.
	p.subplot(220 + x)
	# Set up the axes.
	p.title(fileList[x])
	p.ylabel('Real Voltage')
	#p.xlabel('Minutes After Start')
	# Plot data and show.
	for series in voltMatrix[x]:
		p.plot(series)

#p.savefig('test.png')
p.show()
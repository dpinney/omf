#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import matplotlib.pyplot as p
import matplotlib as m
import math
import Image
from subprocess import call

# Helper function that translates csv values to reasonable floats (or header values to strings):
def strClean(x):
	if x == 'OPEN':
		return 1.0
	elif x == 'CLOSED':
		return 0.0
	elif x[0] == '+':
		return float(x[1:])
	elif x[0] == '-':
		return float(x)
	else:
		return x

# Take a filename to a list of timeseries vectors.
def csvToTimeseries(fileName):
	openfile = open(fileName)
	data = openfile.read()
	lines = data.splitlines()
	array = map(lambda x:x.split(','), lines)
	cleanArray = [map(strClean, x) for x in array]
	# Magic number 8 is the number of header rows in each csv.
	arrayNoHeaders = cleanArray[8:]
	# Drop the timestamp column:
	trimmedArray = [line[1:] for line in arrayNoHeaders]
	timeSeriesList = zip(*trimmedArray)
	return timeSeriesList

def crossProd(realVec,imVec):
	return map(lambda x:math.sqrt(x[0]*x[0]+x[1]*x[1]), zip(realVec, imVec))

def graphVoltFile(voltFile):
	voltTSL = csvToTimeseries(voltFile)
	p.plot(crossProd(voltTSL[0][1:],voltTSL[1][1:]))
	p.plot(crossProd(voltTSL[2][1:],voltTSL[3][1:]))
	p.plot(crossProd(voltTSL[4][1:],voltTSL[5][1:]))

def buildGraph():
	# Get into our working directory.
	print os.getcwd()
	os.chdir('static')

	# RUN GRIDLABD
	call(['gridlabd.exe','IEEE_13_house_vvc_2hrDuration.glm'])

	# Files we'll use.
	voltageCSVs = ['Voltage_630.csv', 'Voltage_652.csv', 'Voltage_671.csv', 'Voltage_675.csv', 'Voltage_680.csv']
	cap1CSV = 'capacitor1_output.csv'
	cap2CSV = 'capacitor2_output.csv'
	regCSV = 'reg1_output.csv'

	# ARG! Subplot indices start at 1!

	# Graphing defaults.
	m.rcParams.update({'font.size': 4})
	# Graph the regulator variables.
	regSeriesList = csvToTimeseries(regCSV)
	p.subplot(3,6,1)
	p.title('Regulator Tap Positions')
	p.plot(regSeriesList[0][1:])
	p.plot(regSeriesList[1][1:])
	p.plot(regSeriesList[2][1:])
	p.subplot(3,6,2)
	p.title('Regulator Real Power')
	p.plot(regSeriesList[3][1:])
	p.plot(regSeriesList[5][1:])
	p.plot(regSeriesList[7][1:])
	p.subplot(3,6,3)
	p.title('Regulator Reactive Power')
	p.plot(regSeriesList[4][1:])
	p.plot(regSeriesList[6][1:])
	p.plot(regSeriesList[8][1:])
	p.subplot(3,6,4)
	p.title('Regulator Apparent Power')
	p.plot(crossProd(regSeriesList[3][1:],regSeriesList[4][1:]))
	p.plot(crossProd(regSeriesList[5][1:],regSeriesList[6][1:]))
	p.plot(crossProd(regSeriesList[7][1:],regSeriesList[8][1:]))
	p.subplot(3,6,5)
	p.title('Regulator Power Factor')
	TotalRealPower = map(sum, zip(regSeriesList[3][1:],regSeriesList[5][1:],regSeriesList[7][1:]))
	TotalReactivePower = map(sum, zip(regSeriesList[4][1:],regSeriesList[6][1:],regSeriesList[8][1:]))
	TotalPowerFactor = map(lambda x:math.cos(math.atan(x[0]/x[1])), zip(TotalReactivePower,TotalRealPower))
	p.plot(TotalPowerFactor)
	# Graph the voltages.
	for x in xrange(5):
		p.subplot(3,6,x+6)
		p.title(voltageCSVs[x])
		graphVoltFile(voltageCSVs[x])
	# Graph the image.
	p.subplot(3,6,(11,12))
	p.imshow(Image.open('map.png'), origin='lower')
	p.xticks([])
	p.yticks([])
	# Graph the caps.
	cap1SeriesList = csvToTimeseries(cap1CSV)
	for x in xrange(3):
		p.subplot(3,6,x+13)
		p.title('Cap1' + ' ' + cap1SeriesList[x][0])
		p.plot(cap1SeriesList[x][1:])
	cap2SeriesList = csvToTimeseries(cap2CSV)
	for x in xrange(3):
		p.subplot(3,6,x+16)
		p.title('Cap2' + ' ' + cap2SeriesList[x][0])
		p.plot(cap2SeriesList[x][1:])

	#p.show()
	p.savefig('test.png', dpi=200)

def main():
	buildGraph()

if __name__ == '__main__':
	main()
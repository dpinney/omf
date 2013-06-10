#!/usr/bin/env python

''' Take a bunch of gridlab objects, figure out how their properties are distributed. '''

with open('variableDistribution.txt', 'r') as vDist:
	rawData = vDist.read()

bigDict = {}

for x in rawData.split('\n'):
	splitArray = x.split()
	if len(splitArray) < 2:
		continue
	if splitArray[0] in bigDict:
		bigDict[splitArray[0]].append(splitArray[1])
	else:
		bigDict[splitArray[0]] = [splitArray[1]]

del bigDict['location']
del bigDict['temperature']

print '{'
for key in bigDict:
	fixedArray = map(float,bigDict[key])
	print '"' + key + '":' + str(fixedArray) + ','
print '}'

'''
Okay, here are the derived rules.

REMEMBER: only 2/3 of houses have electric water heaters.

* schedule_skew: gaussian*2000
* temperature: 135
* tank_volume: 50
* heating_element_capacity: uniform between 3.7 and 5.3 kW
* thermostat_deadband: uniform between 2.0 and 6.0.
* location: INSIDE
* demand: waterX*1 for X uniform on ints [1,...,20]
* tank_setpoint: gaussian really tight around 130.
* tank_UA: uniform between 2.0 and 4.0.

'''
import pandas as pd
import numpy as np
from omf import geo, feeder
import re
import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import datetime

def heatMap(pathToCsv):
	'create a heat map based on input csv file with location, component type, fault type, and cause'
	mc = pd.read_csv(pathToCsv)
	compType = {}
	location = {}
	cause = {}
	faultType = {}
	row_count_mc = mc.shape[0]
	row = 0
	while row < row_count_mc:
		# component type will store which causes and fault types can occur for a given line type
		if mc.loc[row, 'Object type'] in compType.keys():
			if mc.loc[row, 'Cause'] not in compType[mc.loc[row, 'Object type']]['causes']:
				compType[mc.loc[row, 'Object type']]['causes'].append(mc.loc[row, 'Cause'])
			if mc.loc[row, 'Implemented Fault Type'] not in compType[mc.loc[row, 'Object type']]['fault_types']:
				compType[mc.loc[row, 'Object type']]['fault_types'].append(mc.loc[row, 'Implemented Fault Type'])
		else:
			compType[mc.loc[row, 'Object type']] = {}
			compType[mc.loc[row, 'Object type']]['causes'] = []
			compType[mc.loc[row, 'Object type']]['fault_types'] = []
			compType[mc.loc[row, 'Object type']]['causes'].append(mc.loc[row, 'Cause'])
			compType[mc.loc[row, 'Object type']]['fault_types'].append(mc.loc[row, 'Implemented Fault Type'])
		# location of the faults as well as the component type, since the latter is completely dependent on the former (if we have no locations for the components)
		if (mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']) in location.keys():
			location[mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']] += 1
		else:
			location[mc.loc[row, 'Location'] + ' ' + mc.loc[row, 'Object type']] = 1
		# causes for the faults
		if mc.loc[row, 'Cause'] in cause.keys():
			cause[mc.loc[row, 'Cause']] += 1
		else:
			cause[mc.loc[row, 'Cause']] = 1
		# fault types for the faults
		if mc.loc[row, 'Implemented Fault Type'] in faultType.keys():
			faultType[mc.loc[row, 'Implemented Fault Type']] += 1
		else:
			faultType[mc.loc[row, 'Implemented Fault Type']] = 1
		row += 1
	# find the total number of faults that occur in each dictionary
	totalCause = sum(cause.itervalues(), 0.0)
	totalFaultType = sum(faultType.itervalues(), 0.0)
	totalLocation = sum(location.itervalues(), 0.0)

	# create a heat map by dividing the number of each individual item by the total number found
	location = {k: v / totalLocation for k, v in location.iteritems()}
	cause = {k: v / totalCause for k, v in cause.iteritems()}
	faultType = {k: v / totalFaultType for k, v in faultType.iteritems()}
	# create a single dictionary to store heat map data
	heatMap = {}
	heatMap['compType'] = compType
	heatMap['location'] = location
	heatMap['cause'] = cause
	heatMap['faultType'] = faultType
	return heatMap

def randomFault(heatMap):
	'using a heat map object, generate a random fault'
	# choose a random location
	chooseLocationString = np.random.choice(heatMap['location'].keys(), 1, heatMap['location'].values())[0]
	chooseLocation = chooseLocationString.split()
	location = str(chooseLocation[0]) + ' ' + str(chooseLocation[1])
	# Note: for this method, component type is completely dependent on location
	compType = str(chooseLocation[2])
	# choose a cause that is possible, given the component type
	causeChosen = False
	while causeChosen == False:
		chooseCause = np.random.choice(heatMap['cause'].keys(), 1, heatMap['cause'].values())[0]
		if chooseCause in heatMap['compType'][compType]['causes']:
			cause = chooseCause
			causeChosen = True
	# choose a fault type that is possible, given the componenty type
	faultChosen = False
	while faultChosen == False:
		chooseFault = np.random.choice(heatMap['faultType'].keys(), 1, heatMap['faultType'].values())[0]
		if chooseFault in heatMap['compType'][compType]['fault_types']:
			faultType = chooseFault
			faultChosen = True

	return {'compType': compType, 'location': location, 'cause': cause, 'faultType': faultType}

print(heatMap('C:/Users/granb/omf/omf/scratch/smartSwitching/outagesNew3.csv'))
print(randomFault(heatMap('C:/Users/granb/omf/omf/scratch/smartSwitching/outagesNew3.csv')))
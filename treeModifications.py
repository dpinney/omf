#!/usr/bin/env python

import datetime
import treeParser as tp

def adjustTime(tree, simLength, simLengthUnits):
	# translate LengthUnits to minutes.
	if simLengthUnits == 'minutes':
		lengthInSeconds = simLength * 60
		interval = 60
	elif simLengthUnits == 'hours':
		lengthInSeconds = 1440 * simLength
		interval = 1440
	elif simLengthUnits == 'days':
		lengthInSeconds = 86400 * simLength
		interval = 86400

	starttime = datetime.datetime(2000,1,1)
	stoptime = starttime + datetime.timedelta(seconds=lengthInSeconds)

	# alter the clocks and recorders:
	for x in tree:
		leaf = tree[x]
		if 'clock' in leaf:
			# Ick, Gridlabd wants time values wrapped in single quotes:
			leaf['starttime'] = "'" + str(starttime) + "'"
			leaf['stoptime'] = "'" + str(stoptime) + "'"
		if 'object' in leaf and leaf['object'] == 'recorder':
			leaf['interval'] = str(interval)
			leaf['limit'] = str(simLength)

def main(): #tests!
	adjustTime(simLength=30, simLengthUnits='days', tree=tp.parse('../testglms/13_SYNTH.glm'))
#!/usr/bin/env python

import json
import os
import shutil
import solvers
from datetime import datetime

with open('./studies/pvwatts.html','r') as configFile: configHtmlTemplate = configFile.read()

def create(analysisName, simLength, simLengthUnits, simStartDate, studyConfig):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyConfig['studyName']
	# make the study folder:
	os.mkdir(studyPath)
	# copy over tmy2 and replace the dummy climate.tmy2.
	shutil.copyfile('tmy2s/' + studyConfig['tmy2name'], studyPath + '/climate.tmy2')
	# write all the other variables:
	with open(studyPath + '/samInput.json','w') as samInputFile:
		json.dump(studyConfig, samInputFile, indent=4)
	# add the metadata:
	md = {'climate':str(studyConfig['tmy2name']), 'studyType':str(studyConfig['studyType']), 'sourceFeeder':'N/A'}
	with open(studyPath + '/metadata.json','w') as mdFile:
		json.dump(md, mdFile)
	return

def run(analysisName, studyName):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyName
	# gather input and metadata.
	with open(studyPath + '/samInput.json','r') as inputFile, open('analyses/' + analysisName + '/metadata.json','r') as mdFile:
		inputs = json.load(inputFile)
		md = json.load(mdFile)
	# setup data structures
	ssc = solvers.nrelsam.SSCAPI()
	dat = ssc.ssc_data_create()
	# required inputs
	ssc.ssc_data_set_string(dat, "file_name", studyPath + "/climate.tmy2")
	ssc.ssc_data_set_number(dat, "system_size", float(inputs['systemSize']))
	ssc.ssc_data_set_number(dat, "derate", float(inputs['derate']))
	ssc.ssc_data_set_number(dat, "track_mode", float(inputs['trackingMode']))
	ssc.ssc_data_set_number(dat, "azimuth", float(inputs['azimuth']))
	# default inputs exposed
	ssc.ssc_data_set_number(dat, 'rotlim', float(inputs['rotlim']))
	ssc.ssc_data_set_number(dat, 't_noct', float(inputs['t_noct']))
	ssc.ssc_data_set_number(dat, 't_ref', float(inputs['t_ref']))
	ssc.ssc_data_set_number(dat, 'gamma', float(inputs['gamma']))
	ssc.ssc_data_set_number(dat, 'inv_eff', float(inputs['inv_eff']))
	ssc.ssc_data_set_number(dat, 'fd', float(inputs['fd']))
	ssc.ssc_data_set_number(dat, 'i_ref', float(inputs['i_ref']))
	ssc.ssc_data_set_number(dat, 'poa_cutin', float(inputs['poa_cutin']))
	ssc.ssc_data_set_number(dat, 'w_stow', float(inputs['w_stow']))
	# complicated optional inputs
	ssc.ssc_data_set_number(dat, 'tilt_eq_lat', 1)
	# ssc.ssc_data_set_array(dat, 'shading_hourly', ...) 	# Hourly beam shading factors
	# ssc.ssc_data_set_matrix(dat, 'shading_mxh', ...) 		# Month x Hour beam shading factors
	# ssc.ssc_data_set_matrix(dat, 'shading_azal', ...) 	# Azimuth x altitude beam shading factors
	# ssc.ssc_data_set_number(dat, 'shading_diff', ...) 	# Diffuse shading factor
	# ssc.ssc_data_set_number(dat, 'enable_user_poa', ...)	# Enable user-defined POA irradiance input = 0 or 1
	# ssc.ssc_data_set_array(dat, 'user_poa', ...) 			# User-defined POA irradiance in W/m2
	# ssc.ssc_data_set_number(dat, 'tilt', 999)

	# run PV system simulation
	mod = ssc.ssc_module_create("pvwattsv1")
	ssc.ssc_module_exec(mod, dat)

	# MD calc.
	if md['simLengthUnits'] == 'days':
		startDateTime = md['simStartDate']
	else:
		startDateTime = md['simStartDate'] + ' 00:00:00 PDT'

	def aggData(key, aggFun):
		u = md['simStartDate']
		dt = datetime(int(u[0:4]),int(u[5:7]),int(u[8:10]))
		v = dt.isocalendar()
		initHour = int(8760*(v[1]+v[2]/7)/52.0)
		fullData = ssc.ssc_data_get_array(dat, key)
		if md['simLengthUnits'] == 'days':
			multiplier = 24
		else:
			multiplier = 1
		hourData = [fullData[(initHour+i)%8760] for i in xrange(md['simLength']*multiplier)]
		if md['simLengthUnits'] == 'minutes':
			pass
		elif md['simLengthUnits'] == 'hours':
			return hourData
		elif md['simLengthUnits'] == 'days':
			split = [hourData[x:x+24] for x in xrange(md['simLength'])]
			return map(aggFun, split)

	def avg(x):
		return sum(x)/len(x)
	
	# Extract data.
	# Timestamps.
	outData = {}
	outData['timeStamps'] = [startDateTime for x in range(md['simLength'])]
	# Geodata.
	outData['city'] = ssc.ssc_data_get_string(dat, 'city')
	outData['state'] = ssc.ssc_data_get_string(dat, 'state')
	outData['lat'] = ssc.ssc_data_get_number(dat, 'lat')
	outData['lon'] = ssc.ssc_data_get_number(dat, 'lon')
	outData['elev'] = ssc.ssc_data_get_number(dat, 'elev')
	# Weather
	outData['climate'] = {}
	outData['climate']['irrad'] = aggData('dn', avg)
	outData['climate']['diffIrrad'] = aggData('df', avg)
	outData['climate']['temp'] = aggData('tamb', avg)
	outData['climate']['cellTemp'] = aggData('tcell', avg)
	outData['climate']['wind'] = aggData('wspd', avg)
	# Power generation.
	outData['Consumption'] = {}
	outData['Consumption']['Power'] = [-1*x for x in aggData('ac', avg)]
	outData['Consumption']['Losses'] = [0 for x in aggData('ac', avg)]
	outData['Consumption']['DG'] = aggData('ac', avg)
	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ''
	# componentNames.
	outData['componentNames'] = []

	# Write some results.
	with open(studyPath + '/cleanOutput.json','w') as outFile:
		json.dump(outData, outFile, indent=4)
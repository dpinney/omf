#!/usr/bin/env python

import json
import os
import shutil
import solvers

with open('./studies/pvwatts.html','r') as configFile: configHtmlTemplate = configFile.read()

def create(analysisName, simLength, simLengthUnits, simStartDate, studyConfig):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyConfig['studyName']
	# make the study folder:
	os.mkdir(studyPath)
	# copy over tmy2 and replace the dummy climate.tmy2.
	shutil.copyfile('tmy2s/' + studyConfig['tmy2name'], studyPath + '/climate.tmy2')
	# write all the other variables:
	with open(studyPath + '/samInput.json','w') as samInputFile:
		json.dump(studyConfig, samInputFile)
	# add the metadata:
	md = {'climate':str(studyConfig['tmy2name']), 'studyType':str(studyConfig['studyType'])}
	with open(studyPath + '/metadata.json','w') as mdFile:
		json.dump(md, mdFile)
	return

def run(analysisName, studyName):
	studyPath = 'analyses/' + analysisName + '/studies/' + studyName
	# gather input.
	with open(studyPath + '/samInput.json','r') as inputFile:
		inputs = json.load(inputFile)
	# setup data structures
	ssc = solvers.nrelsam.PySSC()
	dat = ssc.data_create()
	# required inputs
	ssc.data_set_string(dat, "file_name", studyPath + "/climate.tmy2")
	ssc.data_set_number(dat, "system_size", float(inputs['systemSize']))
	ssc.data_set_number(dat, "derate", float(inputs['derate']))
	ssc.data_set_number(dat, "track_mode", float(inputs['trackingMode']))
	ssc.data_set_number(dat, "azimuth", float(inputs['azimuth']))
	# default inputs exposed
	ssc.data_set_number(dat, 'rotlim', 45.0)
	ssc.data_set_number(dat, 't_noct', 45.0)
	ssc.data_set_number(dat, 't_ref', 25.0)
	ssc.data_set_number(dat, 'gamma', -0.5)
	ssc.data_set_number(dat, 'inv_eff', 0.92)
	ssc.data_set_number(dat, 'fd', 1.0)
	ssc.data_set_number(dat, 'i_ref', 1000)
	ssc.data_set_number(dat, 'poa_cutin', 0)
	ssc.data_set_number(dat, 'w_stow', 0)
	ssc.data_set_number(dat, "tilt_eq_lat", 1)
	# complicated optional inputs
	# ssc.data_set_array(dat, 'shading_hourly', ...) 	Hourly beam shading factors
	# ssc.data_set_matrix(dat, 'shading_mxh', ...) 		Month x Hour beam shading factors
	# ssc.data_set_matrix(dat, 'shading_azal', ...) 	Azimuth x altitude beam shading factors
	# ssc.data_set_number(dat, 'shading_diff', ...) 	Diffuse shading factor
	# ssc.data_set_number(dat, 'enable_user_poa', ...)	Enable user-defined POA irradiance input = 0 or 1
	# ssc.data_set_array(dat, 'user_poa', ...) 			User-defined POA irradiance in W/m2
	# ssc.data_set_number(dat, "tilt", 999)

	# run PV system simulation
	mod = ssc.module_create("pvwattsv1")
	ssc.module_exec(mod, dat)

	# Extract data.
	# Geodata.
	outData = {}
	outData['city'] = ssc.data_get_string(dat, 'city')
	outData['state'] = ssc.data_get_string(dat, 'state')
	outData['lat'] = ssc.data_get_number(dat, 'lat')
	outData['lon'] = ssc.data_get_number(dat, 'lon')
	outData['elev'] = ssc.data_get_number(dat, 'elev')
	# Weather
	outData['irrad'] = ssc.data_get_array(dat, 'dn')
	outData['diffIrrad'] = ssc.data_get_array(dat, 'df')
	outData['temp'] = ssc.data_get_array(dat, 'tamb')
	outData['cellTemp'] = ssc.data_get_array(dat, 'tcell')
	outData['wind'] = ssc.data_get_array(dat, 'wspd')
	# Power generation.
	outData['dcOut'] = ssc.data_get_array(dat, 'dc')
	outData['acOut'] = ssc.data_get_array(dat, 'ac')

	# Write some results.
	with open(studyPath + '/output.json','w') as outFile:
		json.dump(outData, outFile, indent=4)
'''
GOAL
Pull down historical weather data, put it on a SCADA-calibrated feeder.

TODO
XXX Move scapeAsos.py in to weather.py.
XXX Get aGosedWeather.py running its tests.
XXX Pull the weather data from the new weather.py, ASOS, instead of oldWeather.py.
XXX Figure out how to map new data from ASOS or USCRN to insolation. Decent USCRN done.
XXX Why isn't the weather playing in to the simulation correctly? It needs a tymfile argument. Pure insanity.
OOO Update climateChange function in web.py.
'''

from matplotlib import pyplot as plt
import sys, json, csv
from omf import feeder, weather
from omf.solvers.gridlabd import runInFilesystem
from datetime import datetime, timedelta

def historicalWeatherAttach(inputOmdPath, omdOutputPath, initDateTime, location):
	# Make a weather file.
	data_temp = weather.pullUscrn(str(initDateTime.year), location, 'T_CALC')
	data_hum = weather.pullUscrn(str(initDateTime.year), location, 'RH_HR_AVG')
	data_solar = weather.pullUscrn(str(initDateTime.year), location, 'SOLARAD')
	data_full = []
	for i in range(8760):
		step_time = initDateTime + timedelta(hours=i)
		row = [
			'{}:{}:{}:{}:{}'.format(step_time.month, step_time.day, step_time.hour, step_time.minute, step_time.second),
			# str(step_time), 
			data_temp[i],
			0.0, # TODO: get a windspeed
			data_hum[i],
			data_solar[i] * 0.75, # TODO: better solar direct
			data_solar[i] * 0.25, # TODO: better solar diffuse
			data_solar[i]
		]
		data_full.append(row)
	# Write out the weather file.
	csvName = location + str(initDateTime).replace(' ', 'T').replace(':', '-') + '.csv'
	with open(csvName,'w') as wFile:
		weather_writer = csv.writer(wFile)
		weather_writer.writerow(['temperature','wind_speed','humidity','solar_dir','solar_diff','solar_global'])
		for row in data_full:
			weather_writer.writerow(row)
	# Add stuff to the feeder.
	myOmd = json.load(open(inputOmdPath))
	myTree = myOmd['tree']
	# Delete all climate then reinsert.
	reader_name = 'weatherReader'
	climate_name = 'MyClimate'
	for key in myTree.keys():
		obName = myTree[key].get('name','')
		obType = myTree[key].get('object','')
		if obName in [reader_name, climate_name] or obType == 'climate':
			del myTree[key]
	oldMax = feeder.getMaxKey(myTree)
	myTree[oldMax + 1] = {'omftype':'module', 'argument':'tape'}
	myTree[oldMax + 2] = {'omftype':'module', 'argument':'climate'}
	myTree[oldMax + 3] = {'object':'csv_reader', 'name':reader_name, 'filename':csvName}
	myTree[oldMax + 4] = {'object':'climate', 'name':climate_name, 'reader': reader_name, 'tmyfile':csvName}
	# Set the time correctly.
	feeder.adjustTime(myTree, 240, 'hours', '{}-{}-{}'.format(initDateTime.year, initDateTime.month, initDateTime.day))
	# Write back the full feeder.
	with open(csvName,'r') as weatherFile:
		weatherString = weatherFile.read()
	myOmd['attachments'][csvName] = weatherString
	with open(omdOutputPath, 'w') as outFile:
		json.dump(myOmd, outFile, indent=4)

# Run here to test.
OUT_PATH = 'outFile.omd'
historicalWeatherAttach('OlinBarreGHW.omd', OUT_PATH, datetime(2017,1,1,0,0,0), 'KY_Versailles_3_NNW')
feed = json.load(open(OUT_PATH))
rawOut = runInFilesystem(feed['tree'], attachments=feed['attachments'], keepFiles=True, workDir='./testDir/', glmName='./outFile.glm')
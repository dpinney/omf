''' Pull down historical weather data, put it on a SCADA-calibrated feeder. '''


from matplotlib import pyplot as plt
import sys, json, csv, os
from omf import feeder, weather
from omf.solvers.gridlabd import runInFilesystem
from datetime import datetime, timedelta


def historicalWeatherAttach(omdPath, initDateTime, location):
	#TODO: implement.
	# What should the initDateTime be? Whatever the user decides. We only deal in years apparently.
	# What should the location be? Whatever the user decides. How will the user know the location?
	# What hourly measurements do we want? Just 1) air temperature, 2) windspeed, 3) relative humidity, and 4) solar
	return None #Output is mutation of the OMD? Or new OMD?


def run_example():
	# Globals
	INIT_TIME = datetime(2017,1,1,0,0,0)
	CSV_NAME = 'weatherNewKy.csv'
	LOCATION = 'KY_Versailles_3_NNW'
	GLM_PATH = 'IEEE_quickhouse.glm'
	# Make a weather file.
	data_temp = weather.pullUscrn(str(INIT_TIME.year), LOCATION, 'T_CALC')
	data_hum = weather.pullUscrn(str(INIT_TIME.year), LOCATION, 'RH_HR_AVG')
	data_solar = weather.pullUscrn(str(INIT_TIME.year), LOCATION, 'SOLARAD')
	data_full = []
	for i in range(8760): # 24 hours per day * 365 days per year = 8760 measurements for a USCRN station
		step_time = INIT_TIME + timedelta(hours=i)
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
	# Write USCRN data to CSV
	with open(CSV_NAME,'w') as wFile:
		weather_writer = csv.writer(wFile)
		weather_writer.writerow(['temperature','wind_speed','humidity','solar_dir','solar_diff','solar_global'])
		for row in data_full:
			weather_writer.writerow(row)

	# Get an uncalibrated feeder from a .glm file
	myTree = feeder.parse(GLM_PATH) # get a tree, not a feeder

	# Delete all climate objects from the feeder, then reinsert new climate objects
	reader_name = 'weatherReader'
	climate_name = 'MyClimate'
	for key in myTree.keys():
		obName = myTree[key].get('name','')
		obType = myTree[key].get('object','')
		if obName in [reader_name, climate_name] or obType is 'climate':
			del myTree[key]
	oldMax = feeder.getMaxKey(myTree)
	myTree[oldMax + 1] = {'omftype':'module', 'argument':'tape'}
	myTree[oldMax + 2] = {'omftype':'module', 'argument':'climate'}
	myTree[oldMax + 3] = {'object':'csv_reader', 'name':reader_name, 'filename':CSV_NAME}
	myTree[oldMax + 4] = {'object':'climate', 'name':climate_name, 'reader': reader_name, 'tmyfile':CSV_NAME}
	# Set the time correctly. Modify certain objects in the feeder (e.g. recorder and clock)
	feeder.adjustTime(myTree, 240, 'hours', '{}-{}-{}'.format(INIT_TIME.year, INIT_TIME.month, INIT_TIME.day)) 
	create_omd(myTree, CSV_NAME)
	# Run here to test GridLAB_D
	# The output is NOT a feeder. It's some data in JSON format. This function call does NOT modify myTree.
	#rawOut = runInFilesystem(myTree, attachments=[], keepFiles=True, workDir='.', glmName='./outFile.glm') # Use the modified tree to run a simulation in gridlabd
	#print(rawOut)


def create_omd(tree, CSV_NAME):
	""" An .omd is more than just a tree. It has attachments """
	omd = {}
	omd["tree"] = tree
	with open(CSV_NAME,'r') as weatherFile:
		weatherString = weatherFile.read()
	omd['attachments']['weatheryearDCA.csv'] = weatherString
	filepath = os.path.join(os.path.dirname(__file__), "new-calibrated-feeder.omd")
	with open(filepath, 'w') as f:
		f.write(str(omd))
	#try: os.remove('./Orville Tree Pond Calibrated With Weather.json')
	#except: pass
	#with open('./Orville Tree Pond Calibrated With Weather.json', 'w') as outFile:
	#	json.dump(outJson, outFile, indent=4)


if __name__ == "__main__":
	run_example()
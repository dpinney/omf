''' Pull down historical weather data, put it on a SCADA-calibrated feeder. '''

from matplotlib import pyplot as plt
import sys, json, csv
from omf import feeder, weather
from omf.solvers.gridlabd import runInFilesystem
from datetime import datetime, timedelta

# Globals
INIT_TIME = datetime(2017,1,1,0,0,0)
CSV_NAME = 'weatherNewKy.csv'

# Make a weather file.
data_temp = weather.pullUscrn('2017', 'KY_Versailles_3_NNW', 'T_CALC')
data_hum = weather.pullUscrn('2017', 'KY_Versailles_3_NNW', 'RH_HR_AVG')
data_solar = weather.pullUscrn('2017', 'KY_Versailles_3_NNW', 'SOLARAD')
init_time = datetime(2017,1,1,0,0,0)
data_full = []
for i in range(8760):
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

with open(CSV_NAME,'w') as wFile:
	weather_writer = csv.writer(wFile)
	weather_writer.writerow(['temperature','wind_speed','humidity','solar_dir','solar_diff','solar_global'])
	for row in data_full:
		weather_writer.writerow(row)

# Add stuff to the feeder.
myTree = feeder.parse('IEEE_quickhouse.glm')

# HACK: delete all climate then reinsert.
reader_name = 'weatherReader'
climate_name = 'MyClimate'
for key in myTree.keys():
	if myTree[key].get('name','') in [reader_name, climate_name]:
		del myTree[key]
oldMax = feeder.getMaxKey(myTree)
myTree[oldMax + 1] = {'omftype':'module', 'argument':'tape'}
myTree[oldMax + 2] = {'omftype':'module', 'argument':'climate'}
myTree[oldMax + 3] = {'object':'csv_reader', 'name':reader_name, 'filename':CSV_NAME}
myTree[oldMax + 4] = {'object':'climate', 'name':climate_name, 'reader': reader_name}

# Add a few panels too to test.
# myTree[oldMax + 5] = {'name':'solEngInverter', 
# 	'parent':'node19 23CC 01001447022_A', 
# 	'generator_status':'ONLINE', 
# 	'inverter_type':'PWM',
# 	'object':'inverter',
# 	'generator_mode':'CONSTANT_PF' }
# myTree[oldMax + 6] = {'generator_mode':'SUPPLY_DRIVEN', 
# 	'name':'solar172879', 
# 	'parent':'solEngInverter', 
# 	'area':'30000 sf', 
# 	'generator_status':'ONLINE', 
# 	'object':'solar', 
# 	'efficiency':'0.14', 
# 	'panel_type':'SINGLE_CRYSTAL_SILICON' }
# myTree[oldMax + 7] = { 'interval':'3600',
# 	'parent':'solEngInverter',
# 	'limit':'0',
# 	'file':'Inverter_solEngInverter.csv',
# 	'property':'power_A,power_B,power_C',
# 	'object': 'recorder'}

# Set the time correctly.
feeder.adjustTime(myTree, 240, 'hours', '2017-01-01')

# Run here to test.
rawOut = runInFilesystem(myTree, attachments=[], keepFiles=True, workDir='.', glmName='./outFile.glm')

# # Show some output.
print 'Output Keys:', rawOut.keys()
# plt.plot([abs(complex(x)) for x in rawOut['Inverter_solEngInverter.csv']['power_A']])
# plt.show()

# Write back the full feeder.
# outJson = dict(myFeed)
# with open('weatheryearDCA.csv','r') as weatherFile:
# 	weatherString = weatherFile.read()
# outJson['attachments']['weatheryearDCA.csv'] = weatherString
# outJson['tree'] = myTree
# try: os.remove('./Orville Tree Pond Calibrated With Weather.json')
# except: pass
# with open('./Orville Tree Pond Calibrated With Weather.json', 'w') as outFile:
# 	json.dump(outJson, outFile, indent=4)

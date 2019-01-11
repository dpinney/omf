''' Pull down historical weather data, put it on a SCADA-calibrated feeder. '''

from matplotlib import pyplot as plt
import sys, json
from omf import feeder, weather
from omf.solvers.gridlabd import runInFilesystem

# Make a weather file.
# weather.makeClimateCsv('2014-01-01', '2014-01-11', 'MSP', './mspWeather.csv')
with open('@newWeather.csv','w') as wFile:
	# data = weather.pullUscrn('2017', 'KY_Versailles_3_NNW', 'T_CALC')
	data = weather.pullAsos('2017', 'CHO', 'tmpc')
	print data
raise Exception

# Add stuff to the feeder.
myTree = feeder.parse('IEEE_quickhouse.glm')

# HACK:doesn't matter if we import modules twice, so just stick everything on the end.
oldMax = feeder.getMaxKey(myTree)
myTree[oldMax + 1] = {'omftype':'module', 'argument':'tape'}
myTree[oldMax + 2] = {'omftype':'module', 'argument':'climate'}
myTree[oldMax + 3] = {'object':'csv_reader', 'name':'weatherReader', 'filename':'weatheryearDCA.csv'}
myTree[oldMax + 4] = {'object':'climate', 'name':'MyClimate', 'tmyfile':'weatheryearDCA.csv', 'reader':'weatherReader'}

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

feeder.adjustTime(myTree, 24, 'hours', '2014-01-01')

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

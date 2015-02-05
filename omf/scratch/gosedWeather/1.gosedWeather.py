import sys, json
sys.path.append('../..')
import feeder, weather
from solvers.gridlabd import runInFilesystem

# Make a weather file.
weather.makeClimateCsv('2014-01-01', '2014-01-11', 'MSP', './mspWeather.csv')

# Add stuff to the feeder.
with open('./Orville Tree Pond Calibrated.json','r') as inFile:
	myFeed = json.load(inFile)
	myTree = myFeed['tree']
# HACK: doesn't matter if we import modules twice, so just stick everything on the end.
maxKey = feeder.getMaxKey(myTree)
myTree[maxKey + 1] = {'omftype':'module', 'argument':'tape'}
myTree[maxKey + 2] = {'omftype':'module', 'argument':'climate'}
myTree[maxKey + 3] = {'object':'csv_reader', 'name':'weatherReader', 'filename':'mspWeather.csv'}
myTree[maxKey + 4] = {'object':'climate', 'name':'exampleClimate', 'tmyfile':'mspWeather.csv', 'reader':'weatherReader'}
# myTree[maxKey + 5] = {'object':'recorder', name}
feeder.adjustTime(myTree, 240, 'hours', '2014-01-01')

# Run here.
runInFilesystem(myTree, attachments=myFeed['attachments'], keepFiles=True, workDir='.', glmName='Orville Tree Pond Calibrated.glm')
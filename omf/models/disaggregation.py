import subprocess, matplotlib, pickle, warnings
from os.path import join as pJoin
from matplotlib import pyplot as plt
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

warnings.filterwarnings('ignore')

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "The Disaggregation model performs analysis to appliance level power consumption given a site meter."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. '''

	#print(inputDict);
	
	# initialize variables
	outData = {}
	trainBuilding =  str(inputDict['trainBuilding']);
	testBuilding = str(inputDict['testBuilding']);
	algorithm = str(inputDict['disaggAlgo'])

	# convert train data csv into nilmtk format or load nilmtk data
	if (inputDict['trainSet'] == 'CSV'): 
		trainPath = convertTrainData(modelDir,inputDict['trainingData'])
	else:
		trainPath = getPath(inputDict['trainSet'])

	# convert test data csv into nilmtk format or load nilmtk data
	if (inputDict['testSet'] == 'CSV'): 
		testPath = convertTestData(modelDir, inputDict['testingData'])
	else:
		testPath = getPath(inputDict['testSet'])

	# run the dissag script using python 3 because nilmtk requires it
	dissagScript = '../nilmtk/dissagScript.py'
	python3Script = 'python3 ' + dissagScript + ' ' + algorithm + ' ' + \
		trainPath + ' ' + testPath   + ' ' + \
		trainBuilding  + ' ' + testBuilding + ' ' +\
		modelDir
	process = subprocess.Popen(python3Script.split(), stdout=subprocess.PIPE)
	process.wait()
	output, error = process.communicate()
	
#	print('*************disagg output*******************')
#	print(output)


	# open image outputs and add them to the dictionary used by the html page
	with open(pJoin(modelDir,"trainPlot.png"),"rb") as inFile:
		outData["trainPlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"testPlot.png"),"rb") as inFile:
		outData["testPlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"disaggPlot.png"),"rb") as inFile:
		outData["disaggPlot"] = inFile.read().encode("base64")
	with open(pJoin(modelDir,"disaggPie.png"),"rb") as inFile:
		outData["disaggPie"] = inFile.read().encode("base64")

	return outData

def getPath(dataSet):
	'''logic for returning the data file associated with the specified dataset'''
	path = ''
	if (dataSet == 'REDD'):
		path = '../nilmtk/data/REDD/redd.h5'
	return path

def convertTestData(modelDir, data):

	watts = []
	timeStamps = []
	samplePeriod = ''

	# parse provided csv files
	data = data.split('\r\n')
	firstRow = True
	for row in data:
		if str(row) != '':
			dataPoint = row.split(',')
			if firstRow:
				samplePeriod = dataPoint[0]
				firstRow = False
			else:
				timeStamps.append(dataPoint[0])
				watts.append(dataPoint[1])

	# save parsed and reformatted data as files so that nilmtk scripts can use it
	wattsFile = pJoin(modelDir, 'watts.pkl')  
	pickle.dump(watts, open(wattsFile, 'wb'))
	timeStampsFile = pJoin(modelDir, 'timeStamps.pkl')  
	pickle.dump(timeStamps, open(timeStampsFile, 'wb'))
	
	# run the python 3 scripts to convert the csv data to nilmtks format
	outputFilename = pJoin(modelDir,'testData.h5')
	convScript = '../nilmtk/convTestPython3.py'
	python3Script = 'python3 ' + convScript + ' ' + samplePeriod + ' ' + \
		wattsFile + ' ' + timeStampsFile + ' ' + \
		outputFilename + ' ' + modelDir
	process = subprocess.Popen(python3Script.split(), stdout=subprocess.PIPE)
	process.wait()
	output, error = process.communicate()
	
	return outputFilename

def convertTrainData(modelDir, data):

	watts = []
	timeStamps = []
	appliances = []
	samplePeriod = ''

	# parse provided csv files
	data = data.split('\r\n')
	firstRow = True
	for row in data:
		if str(row) != '':
			dataPoint = row.split(',')
			if firstRow:
				samplePeriod = dataPoint[0]
				firstRow = False
			else:
				timeStamps.append(dataPoint[0])
				watts.append(dataPoint[1])
				appliances.append(dataPoint[2])

	# save parsed and reformatted data as files so that nilmtk scripts can use it
	wattsFile = pJoin(modelDir, 'watts.pkl')  
	pickle.dump(watts, open(wattsFile, 'wb'))
	timeStampsFile = pJoin(modelDir, 'timeStamps.pkl')  
	pickle.dump(timeStamps, open(timeStampsFile, 'wb'))
	appliancesFile = pJoin(modelDir, 'appliances.pkl')  
	pickle.dump(appliances, open(appliancesFile, 'wb'))

	# run the python 3 scripts to convert the csv data to nilmtks format
	outputFilename = pJoin(modelDir,'trainData.h5')
	convScript = '../nilmtk/convTrainPython3.py'
	python3Script = 'python3 ' + convScript + ' ' + samplePeriod + ' ' + \
		wattsFile + ' ' + timeStampsFile + ' ' + \
		appliancesFile + ' ' + outputFilename + ' ' + modelDir
	process = subprocess.Popen(python3Script.split(), stdout=subprocess.PIPE)
	process.wait()
	output, error = process.communicate()
	
	return outputFilename


def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		'modelType': modelName,
		'created': '', 
		'runTime': '', 
		'disaggAlgo': 'combOpt', 
		'testFileName': '', 
		'trainFileName': '', 
		'trainingData': '', 
		'testingData': '', 
		'testSet': 'REDD', 
		'trainSet': 'REDD', 
		'testBuilding': '1', 
		'trainBuilding': '1'
	}
	
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _debugging():
	pass

if __name__ == '__main__':
	_debugging()
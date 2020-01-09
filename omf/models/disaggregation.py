import subprocess, pickle, warnings, os, base64, pathlib
from os.path import join as pJoin
from omf.models import __neoMetaModel__

warnings.filterwarnings('ignore')

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "The Disaggregation model performs analysis to appliance level power consumption given a site meter."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. '''

	#print(inputDict)
	
	# initialize variables
	outData = {}
	trainBuilding =  str(inputDict['trainBuilding'])
	testBuilding = str(inputDict['testBuilding'])
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

	# if nilmtk is not installed, install it
	#if not(os.path.isdir('./solvers/nilmtk/nilmtk')):
	#	installNilm()

	# run the dissag script using python 3 because nilmtk requires it
	#dissagScript = './solvers/nilmtk/nilmtk/dissagScript.py'
	disagg_script_path = str(pathlib.Path(__file__).parent.parent / 'solvers/nilmtk/dissagScript.py')
	print(disagg_script_path)

	#python3Script = 'python3 ' + dissagScript + ' ' + algorithm + ' ' + \
	python3Script = 'python3 ' + disagg_script_path + ' ' + algorithm + ' ' + \
		trainPath + ' ' + testPath   + ' ' + \
		trainBuilding  + ' ' + testBuilding + ' ' +\
		modelDir
	process = subprocess.Popen(python3Script.split(), stdout=subprocess.PIPE)
	process.wait()
	output, error = process.communicate()
	print('*************disagg output*******************')
	print(f'output: {output}')
	print(f'error: {error}')


	# open image outputs and add them to the dictionary used by the html page
	with open(pJoin(modelDir,"trainPlot.png"),"rb") as inFile:
		outData["trainPlot"] = base64.standard_b64encode(inFile.read()).decode('ascii')
	with open(pJoin(modelDir,"testPlot.png"),"rb") as inFile:
		outData["testPlot"] = base64.standard_b64encode(inFile.read()).decode('ascii')
	with open(pJoin(modelDir,"disaggPlot.png"),"rb") as inFile:
		outData["disaggPlot"] = base64.standard_b64encode(inFile.read()).decode('ascii')
	with open(pJoin(modelDir,"disaggPie.png"),"rb") as inFile:
		outData["disaggPie"] = base64.standard_b64encode(inFile.read()).decode('ascii')
	return outData

def getPath(dataSet):
	'''logic for returning the data file associated with the specified dataset'''
	path = ''
	if (dataSet == 'REDD'):
		path = './solvers/nilmtk/nilmtk/data/REDD/redd.h5'
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
	
	# if nilmtk is not installed, install it
	#if not(os.path.isdir('./solvers/nilmtk/nilmtk')):
	#	installNilm()

	# run the python 3 scripts to convert the csv data to nilmtks format
	outputFilename = pJoin(modelDir,'testData.h5')
	convScript = './solvers/nilmtk/nilmtk/convTestPython3.py'
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

	# if nilmtk is not installed, install it
	#if not(os.path.isdir('./solvers/nilmtk/nilmtk')):
	#	installNilm()

	# run the python 3 scripts to convert the csv data to nilmtks format
	outputFilename = pJoin(modelDir,'trainData.h5')
	convScript = './solvers/nilmtk/nilmtk/convTrainPython3.py'
	python3Script = 'python3 ' + convScript + ' ' + samplePeriod + ' ' + \
		wattsFile + ' ' + timeStampsFile + ' ' + \
		appliancesFile + ' ' + outputFilename + ' ' + modelDir
	process = subprocess.Popen(python3Script.split(), stdout=subprocess.PIPE)
	process.wait()
	output, error = process.communicate()
	
	return outputFilename

def installNilm():
	print('------------------------------------------------------------------')
	print('------------------------------------------------------------------')
	print('------------------------------------------------------------------')
	print('------------------------------------------------------------------')


	# install nilmtk
	os.chdir("./solvers/nilmtk/")
	os.system("yes | sudo apt-get install python3-tk git libhdf5-serial-dev python-dev postgresql postgresql-contrib postgresql-server-dev-all python3-pip")
	os.system("sudo pip3 install numpy scipy==0.19.1 six scikit-learn==0.19.2 pandas numexpr tables matplotlib networkx future psycopg2 nose coveralls coverage git+https://github.com/hmmlearn/hmmlearn.git@ae1a41e4d03ea61b7a25cba68698e8e2e52880ad#egg=hmmlearn")
	os.system("git clone https://github.com/nilmtk/nilm_metadata/")
	os.chdir("nilm_metadata")
	os.system("yes | rm -r .git*")
	os.system("sudo python3 setup.py develop")
	os.chdir("..")
	os.system("git clone https://github.com/nilmtk/nilmtk.git")
	os.chdir("nilmtk")
	os.system("yes | rm -r .git*")
	os.system("sudo python3 setup.py develop")
	print('------------------------------------------------------------------')
	print(os.getcwd())
	print('------------------------------------------------------------------')
	os.rename('../convTrainPython3.py','./convTrainPython3.py')
	os.rename('../convTestPython3.py','./convTestPython3.py')
	os.rename('../dissagScript.py','./dissagScript.py')
	os.chdir('../../../')


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
	## Location
	#modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	## Blow away old test results if necessary.
	#try:
	#	shutil.rmtree(modelLoc)
	#except:
	#	# No previous test results.
	#	pass
	## Create New.
	#new(modelLoc)
	## Pre-run.
	## renderAndShow(modelLoc)
	## Run the model.
	#__neoMetaModel__.runForeground(modelLoc)
	## Show the output.
	#__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

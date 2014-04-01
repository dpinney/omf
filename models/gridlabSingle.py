import json, os, sys, tempfile, webbrowser, time, shutil
from jinja2 import Template

_myDir = os.path.dirname(__file__)
_omfDir = os.path.dirname(_myDir)
# TODO: import feeder.py, etc.
# sys.path.append(os.path.dirname(_myDir))

# Speed of model execution so our web server knows whether to wait for results on run:
fastModel = False

with open(_myDir + "/gridlabSingle.html","r") as tempFile:
	template = Template(tempFile.read())

# userInput = {
# 	"modelName": "Single Gridlab Run",
# 	"simLength": "2048",
# 	"simLengthUnits": "hours",
# 	"simStartDate": "2014-01-01"
# }
# userInputNeedsTranslation = {
# 	"feederName": "Test Feeder",
# 	"climateName": "Test Climate"
# }
# machineInput = {
# 	"user": "admin",
# 	"status": None, 
# 	"created": None,
# 	"modelType": "gridlabSingle",
# 	"runTime": None
# }

def renderTemplate(modelDirectory="", absolutePaths=False, datastoreNames={}):
	''' Render the model template. By default render a blank one for new input.
	If modelDirectory is valid, render results post-model-run.
	If absolutePaths, the HTML can be opened without a server. '''
	try:
		allInputData = open(modelDirectory + '/allInputData.json').read()
	except IOError:
		allInputData = None
	try:
		allOutputData = open(modelDirectory + '/allOutputData.json').read()
	except IOError:
		allOutputData = None
	if absolutePaths:
		# Parent of current folder.
		pathPrefix = _omfDir
	else:
		pathPrefix = ""
	return template.render(allInputData=allInputData,
		allOutputData=allOutputData, pathPrefix=pathPrefix,
		datastoreNames=datastoreNames)

def renderAndShow(modelDirectory="", datastoreNames={}):
	''' Render and open a template in a local browser. '''
	with tempfile.NamedTemporaryFile() as temp:
		temp.write(renderTemplate(modelDirectory=modelDirectory, absolutePaths=True))
		temp.flush()
		os.rename(temp.name, temp.name + '.html')
		fullArg = 'file://' + temp.name + '.html'
		webbrowser.open(fullArg)
		# It's going to SPACE! Could you give it a SECOND to get back from SPACE?!
		time.sleep(1)

def create(parentDirectory, inData):
	''' Make a directory for the model to live in, and put the input data into it. '''
	modelDirName = parentDirectory + "/" + inData["user"] + "_" + inData["modelName"] + "/"
	os.mkdir(modelDirName)
	with open(modelDirName + "allInputData.json","w") as inputFile:
		json.dump(inData, inputFile, indent=4)
	# Copy datastore data.
	shutil.copy(os.path.join(_omfDir,"data","Feeder",inData["feederName"] + ".json"),
		modelDirName)
	shutil.copy(os.path.join(_omfDir,"data","Weather",inData["climateName"] + ".json"),
		modelDirName)

def run(modelDirectory):
	''' Run the model in its directory. '''
	with open(modelDirectory + "allInputData.json","r") as inputFile:
		allInputData = json.load(inputFile)
	# TODO: Do stuff in the background here...
	with open(modelDirectory + "allInputData.json","w") as inputFile:
		allInputData = json.load(inputFile)
	# Translate files to needed format. Run Gridlab.

def _tests():
	# Render a no-input template.
	renderAndShow()
	# Render running template.
	testDir = os.path.dirname(_myDir) + "/data/Model/admin_Running Example"
	renderAndShow(modelDirectory=testDir)
	# Render completed template.
	testDir = os.path.dirname(_myDir) + "/data/Model/admin_Single Gridlab Run"
	renderAndShow(modelDirectory=testDir)

if __name__ == '__main__':
	_tests()
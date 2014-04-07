import json, os, sys, tempfile, webbrowser, time, shutil, datetime
from os.path import join as pJoin
from jinja2 import Template

_myDir = os.path.dirname(__file__)
_omfDir = os.path.dirname(_myDir)
# TODO: import feeder.py, etc.
sys.path.append(_omfDir)
import feeder

# Speed of model execution so our web server knows whether to wait for results on run:
fastModel = False

with open(pJoin(_myDir,"gridlabSingle.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(modelDir="", absolutePaths=False, datastoreNames={}):
	''' Render the model template to an HTML string.
	By default render a blank one for new input.
	If modelDir is valid, render results post-model-run.
	If absolutePaths, the HTML can be opened without a server. '''
	try:
		allInputData = open(pJoin(modelDir,"allInputData.json")).read()
	except IOError:
		allInputData = None
	try:
		allOutputData = open(pJoin(modelDir,"allOutputData.json")).read()
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

def renderAndShow(modelDir="", datastoreNames={}):
	''' Render and open a template (blank or with output) in a local browser. '''
	with tempfile.NamedTemporaryFile() as temp:
		temp.write(renderTemplate(modelDir=modelDir, absolutePaths=True))
		temp.flush()
		os.rename(temp.name, temp.name + '.html')
		fullArg = 'file://' + temp.name + '.html'
		webbrowser.open(fullArg)
		# It's going to SPACE! Could you give it a SECOND to get back from SPACE?!
		time.sleep(1)

def create(parentDirectory, inData):
	''' Make a directory for the model to live in, and put the input data into it. '''
	modelDir = pJoin(parentDirectory,inData["user"],inData["modelName"])
	os.mkdir(modelDir)
	inData["created"] = str(datetime.datetime.now())
	with open(pJoin(modelDir,"allInputData.json"),"w") as inputFile:
		json.dump(inData, inputFile, indent=4)
	# Copy datastore data.
	feederDir, feederName = inData["feederName"].split("___")
	shutil.copy(pJoin(_omfDir,"data","Feeder",feederDir,feederName+".json"),
		pJoin(modelDir,"feeder.json"))
	shutil.copy(pJoin(_omfDir,"data","Climate",inData["climateName"] + ".tmy2"),
		pJoin(modelDir,"climate.tmy2"))

def run(modelDir):
	''' Run the model in its directory. '''
	allInputData = json.load(open(pJoin(modelDir,"allInputData.json")))
	# Write the GLM and its associated files.
	feederJson = json.load(open(pJoin(modelDir,"feeder.json")))
	with open(pJoin(modelDir,"feeder.glm"),"w") as glmFile:
		glmFile.write(feeder.sortedWrite(feederJson["tree"]))
	for fName in feederJson["attachments"]:
		with open(pJoin(modelDir,fName),"w") as attachFile:
			attachFile.write(feederJson["attachments"][fName])
	# TODO: Do stuff here...
	
	print "RUNNING"
	# Translate files to needed format. Run Gridlab.
	print "OKAY we're in", modelDir

def cancel(modelDir):
	''' Try to cancel a currently running model. '''
	#TODO: implement me.
	pass

def _oldTests():
	''' REMOVE ME '''
	# Render a no-input template.
	renderAndShow()
	# Render running template.
	testDir = pJoin(_omfDir,"data","Model","admin","Running Example")
	renderAndShow(modelDir=testDir)
	# Render completed template.
	testDir = pJoin(_omfDir,"data","Model","admin","Single Gridlab Run")
	renderAndShow(modelDir=testDir)

def _tests():
	# Variables
	workDir = pJoin(_omfDir,"data","Model")
	# No-input template.
	renderAndShow()
	# If we were actually inputting stuff:
	inData = { "modelName": "Automated Testing",
		"simStartDate": "2012-04-01",
		"simLengthUnits": "hours",
		"feederName": "public___Simple Market System",
		"modelType": "gridlabSingle",
		"climateName": "AL-HUNTSVILLE",
		"simLength": "100",
		"user": "admin", # Only set by web.py
		"runTime": ""}
	# create a model.
	create(workDir, inData)
	modelLoc = pJoin(workDir,inData["user"],inData["modelName"])
	# Show a thing.
	renderAndShow(modelDir=modelLoc)
	# run a thing.
	run(modelLoc)
	# cancel a thing.
	# run a thing again.
	# delete a thing.
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
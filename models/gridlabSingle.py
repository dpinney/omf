import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess, datetime as dt
from os.path import join as pJoin
from jinja2 import Template

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(__file__)
_omfDir = os.path.dirname(_myDir)

# OMF imports
sys.path.append(_omfDir)
import feeder
from omf.solvers import gridlabd

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
	''' Run the model in its directory. WARNING: GRIDLAB CAN TAKE HOURS TO COMPLETE. '''
	print "STARTING TO RUN", modelDir
	startTime = dt.datetime.now()
	allInputData = json.load(open(pJoin(modelDir,"allInputData.json")))
	feederJson = json.load(open(pJoin(modelDir,"feeder.json")))
	tree = feederJson["tree"]
	# Set up GLM with correct time and recorders:
	feeder.attachRecorders(tree, "Regulator", "object", "regulator")
	feeder.attachRecorders(tree, "Capacitor", "object", "capacitor")
	feeder.attachRecorders(tree, "Inverter", "object", "inverter")
	feeder.attachRecorders(tree, "Windmill", "object", "windturb_dg")
	feeder.attachRecorders(tree, "CollectorVoltage", None, None)
	feeder.attachRecorders(tree, "Climate", "object", "climate")
	feeder.attachRecorders(tree, "OverheadLosses", None, None)
	feeder.attachRecorders(tree, "UndergroundLosses", None, None)
	feeder.attachRecorders(tree, "TriplexLosses", None, None)
	feeder.attachRecorders(tree, "TransformerLosses", None, None)
	feeder.groupSwingKids(tree)
	feeder.adjustTime(tree=tree, simLength=float(allInputData["simLength"]),
		simLengthUnits=allInputData["simLengthUnits"], simStartDate=allInputData["simStartDate"])
	# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
	rawOutput = gridlabd.runInFilesystem(tree, attachments=feederJson["attachments"], 
		keepFiles=True, workDir=modelDir)
	# Write the output.
	with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
		json.dump(rawOutput, outFile, indent=4)
	endTime = dt.datetime.now()
	allInputData["runTime"] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
	# Update the runTime in the input file.
	with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
		json.dump(allInputData, inFile, indent=4)
	# Clean up the PID file.
	os.remove(pJoin(modelDir,"PID.txt"))
	print "DONE RUNNING", modelDir

def runBackground(modelDir):
	''' Run the model in a separate process. '''
	pass

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
	inData = { "modelName": "Automated Testing",
		"simStartDate": "2012-04-01",
		"simLengthUnits": "hours",
		"feederName": "public___Simple Market System",
		"modelType": "gridlabSingle",
		"climateName": "AL-HUNTSVILLE",
		"simLength": "100",
		"user": "admin", # Only set by web.py.
		"runTime": ""}
	modelLoc = pJoin(workDir,inData["user"],inData["modelName"])
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow()
	# As if we were actually inputting stuff:
	# create a model.
	create(workDir, inData)
	# Show the model.
	renderAndShow(modelDir=modelLoc)
	# run the model.
	run(modelLoc)
	# cancel the model.
	# run the model again.
	# Show the output.
	renderAndShow(modelDir=modelLoc)
	# delete the model.
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
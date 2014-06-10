''' Graph the voltage drop on a feeder. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt
from os.path import join as pJoin
from jinja2 import Template

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(_myDir)

# OMF imports
sys.path.append(_omfDir)
import feeder
from solvers import gridlabd

# Our HTML template for the interface:
with open(pJoin(_myDir,"voltageDrop.html"),"r") as tempFile:
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
		allOutputData=allOutputData, modelStatus=getStatus(modelDir), pathPrefix=pathPrefix,
		datastoreNames=datastoreNames)

def renderAndShow(modelDir="", datastoreNames={}):
	''' Render and open a template (blank or with output) in a local browser. '''
	with tempfile.NamedTemporaryFile() as temp:
		temp.write(renderTemplate(modelDir=modelDir, absolutePaths=True))
		temp.flush()
		os.rename(temp.name, temp.name + ".html")
		fullArg = "file://" + temp.name + ".html"
		webbrowser.open(fullArg)
		# It's going to SPACE! Could you give it a SECOND to get back from SPACE?!
		time.sleep(1)

def getStatus(modelDir):
	''' Is the model stopped, running or finished? '''
	try:
		modFiles = os.listdir(modelDir)
	except:
		modFiles = []
	hasInput = "allInputData.json" in modFiles
	hasPID = "PID.txt" in modFiles
	hasOutput = "allOutputData.json" in modFiles
	if hasInput and not hasOutput and not hasPID:
		return "stopped"
	elif hasInput and not hasOutput and hasPID:
		return "running"
	elif hasInput and hasOutput and not hasPID:
		return "finished"
	else:
		# Broken! Make the safest choice:
		return "stopped"

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(dt.datetime.now())
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	# Copy spcific climate data into model directory
	shutil.copy(pJoin(_omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"), 
		pJoin(modelDir, "climate.tmy2"))
	# Ready to run
	startTime = dt.datetime.now()
	### TODO:DO SOMETHING HERE.
	# Setting options for start time.
	simLengthUnits = inputDict.get("simLengthUnits","")
	simStartDate = inputDict.get("simStartDate","")
	# Set the timezone to be UTC, it won't affect calculation and display, relative offset handled in pvWatts.html 
	startDateTime = simStartDate + " 00:00:00 UTC"
	# Timestamp output.
	outData = {}
	### TODO:DO SOMETHING HERE.
	# Write the output.
	with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
		json.dump(outData, outFile, indent=4)
	# Update the runTime in the input file.
	endTime = dt.datetime.now()
	inputDict["runTime"] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
	with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
		json.dump(inputDict, inFile, indent=4)

def cancel(modelDir):
	''' Voltage drop runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# Variables
	workDir = pJoin(_omfDir,"data","Model")
	inData = { "modelName": "Automated voltageDrop Testing",
		"modelType": "voltageDrop",
		"user": "admin",
		"runTime": "" }
	modelLoc = pJoin(workDir,inData["user"],inData["modelName"])
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow()
	# Show the model (should look like it's running).
	renderAndShow(modelDir=modelLoc)
	# Run the model.
	run(modelLoc, inData)
	# Show the output.
	renderAndShow(modelDir=modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
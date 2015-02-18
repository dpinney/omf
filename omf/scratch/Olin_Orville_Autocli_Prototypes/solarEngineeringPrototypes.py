import sys, os
sys.path.append('../..')
from models import __metaModel__, solarEngineering
from __metaModel__ import *
from solarEngineering import *

inputs = {
	"Prototype Olin solarEngineering": {
		"simStartDate": "2013-01-01",
		"simLengthUnits": "hours",
		"feederName": "admin___Olin Beckenham Calibrated",
		"modelType": "solarEngineering",
		"climateName": "KY-LEXINGTON",
		"simLength": "168",
		"runTime": "" },
	"Prototype Autocli solarEngineering": {
		"simStartDate": "2013-01-01",
		"simLengthUnits": "hours",
		"feederName": "admin___Autocli Alberich Calibrated",
		"modelType": "solarEngineering",
		"climateName": "TX-ABILENE",
		"simLength": "168",
		"runTime": "" },
	"Prototype Orville solarEngineering": {
		"simStartDate": "2014-01-01",
		"simLengthUnits": "hours",
		"feederName": "admin___Orville Tree Pond Calibrated",
		"modelType": "solarEngineering",
		"climateName": "MN-SAINT_CLOUD",
		"simLength": "168",
		"runTime": ""} }

def test(modelName, inData):
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	modelLoc = pJoin(workDir,"admin", modelName)
	# Blow away old test results if necessary.
	try: shutil.rmtree(modelLoc)
	except: pass
	# Run the model.
	runForeground(modelLoc, inData)

def openAllOutputs():
	#TODO: make all the outputs show up in the server.
	pass

if __name__ == '__main__':
	for name, inData in inputs.items():
		test(name, inData)
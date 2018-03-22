''' TODO: Description TBD '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "Generate timeseries powerflow scenarios from a distribution feeder."

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName+".html"),"r") as tempFile:
	#print(tempFile)
	template = Template(tempFile.read())

#Get scenario Generator
omfDir=os.path.dirname(os.path.dirname(__file__))
scenGen_path=pJoin(omfDir,'scratch','parapopulation_tool','modifyGLMs')
sys.path.append(scenGen_path)
import coSimExperimentMetal1 as scenGen

def work(modelDir, inputDict):
	print(modelDir)
	''' Run the model in its directory. '''
	outData = {}
	# Get feeder name.
	feederName = [x for x in os.listdir(modelDir) if x.endswith(".omd")][0][:-4]
	inputDict["feederName1"] = feederName
	# Modify parapulation tool inputs.
	recStart = dt.datetime.strptime(inputDict['startTime'], '%Y-%m-%d %H:%M:%S')
	startdate = recStart - dt.timedelta(days=1)
	paraInput = {
		"rootpath": None,
		"experimentFilePath": modelDir,
		"numoffeeders": int(inputDict['numoffeeders']),
		"testfolder": "parapopulation_feeders",
		"startdate": str(startdate),
		"enddate": inputDict['endTime'],
		"recordstart": inputDict['startTime'],
		"recordend": inputDict['endTime'],
		"inputGLM": {
			"R1-12.47-1.glm": [0.12, 6.5, 1, 1],
			"R1-12.47-2.glm": [0.11, 6.5, 1, 1],
			"R1-12.47-3.glm": [0.11, 6.5, 1, 1],
			"R2-12.47-1.glm": [0.11, 6.5, 2, 1],
			"R2-12.47-2.glm": [0.11, 6.5, 2, 1],
			"R2-12.47-3.glm": [0.11, 6.5, 2, 1],
			"R3-12.47-1.glm": [0.11, 6.5, 3, 1],
			"R3-12.47-2.glm": [0.11, 6.5, 3, 1],
			"R3-12.47-3.glm": [0.11, 6.5, 3, 1],
		}
	}
	paraInput['rootpath'] = omfDir + '/scratch/parapopulation_tool'
	# Get the feeder data and write to .glm.
	with open(pJoin(modelDir,feederName + ".omd"),"r") as inFile:
		feederData = json.load(inFile)
	with open(pJoin(modelDir,"scenarioSeed.glm"), "w") as outFile:
		outFile.write(omf.feeder.sortedWrite(feederData["tree"]))
	# Put the data in to the PNNL parapulation tool.
	scenGen.main(paraInput)
	direc = pJoin(modelDir, paraInput['testfolder'])
	# Run gridlabd simulations.
	print(direc)
	for filename in os.listdir(direc):
		if filename != 'include':
			for name in os.listdir(pJoin(direc, filename)):
				if name.endswith('.glm'):
					proc = subprocess.Popen('gridlabd ' + name, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=pJoin(direc, filename))
					(out, err) = proc.communicate()
					#code = proc.wait()
	#parse through gridlabd csv files
	 # counter to create dictionary
	for filename in os.listdir(direc):
		if filename != 'include':
			for name in os.listdir(pJoin(direc, filename)):
				if name == 'output':
					for file in os.listdir(pJoin(direc, filename, name)):
						if 'swing_node' in file:
							feeder_name = str(file)
							#Make an output.
							outputFile = pJoin(direc, filename, name, file)
							outData[file] = {}
							outData[file]["dates"] =  graphify(outputFile)["dates"]
							outData[file]["measured_real_power"] = graphify(outputFile)["measured_real_power"]
							outData[file]["measured_reactive_power"] = graphify(outputFile)["measured_reactive_power"]
						
	return outData
	
def graphify(outputFile):
	''' parses through a gridlabd csv file and pulls out relevant information, writes to python dictionary. '''
	new_dict = {}
	dates=[]
	measured_real_power=[]
	measured_reactive_power=[]
	with open(outputFile, 'r') as csvfile:
		swingnode = csv.reader(csvfile, dialect='excel', delimiter=',')
		for i in range(9):
			swingnode.next()
		for row in (swingnode):
			dates.append(row[0][0:19])
			measured_real_power.append(float(row[13]))
			measured_reactive_power.append(float(row[14]))
			new_dict["dates"]=dates
			new_dict["measured_real_power"]=measured_real_power
			new_dict["measured_reactive_power"]=measured_reactive_power
		return new_dict

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "Olin Barre Geo",
		"modelType": modelName,
		"runTime": "",
		"numoffeeders":"1",
		"startTime": "2013-08-01 00:00:00",
		"endTime": "2013-08-02 00:00:00",
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+".omd"), pJoin(modelDir, defaultInputs["feederName1"]+".omd"))
	except:
		return False
	return creationCode

def _debugging():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass 
	# Create New.
	new(modelLoc)
	# Pre-run.
	renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()
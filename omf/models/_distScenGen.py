''' Description TBD '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

#Import json package
import json
import csv
#Import gridlabd to run simulations
import subprocess

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
	# Get the feeder data and write to .glm.
	with open(pJoin(modelDir,feederName + ".omd"),"r") as inFile:
		feederData = json.load(inFile)
	with open(pJoin(modelDir,"scenarioSeed.glm"), "w") as outFile:
		outFile.write(omf.feeder.sortedWrite(feederData["tree"]))

	#Write inputted data (input dict) to a json file for scenGen (input_data_dict)

	#Below should work, assuming files are always written exactly the same in model
	input_data_dict_Path=os.path.dirname(os.path.dirname(scenGen.__file__))
	#somehow pull variable from html so that inputdatadict is name of what is inputted
	with open(pJoin(input_data_dict_Path, 'input_data_dict.json'), 'r') as d:
		data=json.load(d)
	scenGen.main(data)
	direc=pJoin(modelDir, 'testjson_folder') #somehow make testjson_folder a user input
	#run gridlabd simulations
	print(direc)
	for filename in os.listdir(direc):
		if filename != 'include':
			for name in os.listdir(pJoin(direc, filename)):
				if name.endswith('.glm'):
					proc = subprocess.Popen(['gridlabd', name], stdout=subprocess.PIPE, shell=True, cwd=pJoin(direc, filename))
					(out, err) = proc.communicate()
	#parse through gridlabd csv files
	for filename in os.listdir(direc):
		if filename != 'include':
			for name in os.listdir(pJoin(direc, filename)):
				if name == 'output':
					for file in os.listdir(pJoin(direc, filename, name)):
						if 'swing_node' in file:
							#Make an output.
							outputFile=pJoin(direc, filename, name, file)
							outData[file] = graphify(outputFile)  #charts of some sort
	return outData
	
def graphify(outputFile):
	#parses through a gridlabd csv file and pulls out relevant information, writes to python dictionary
	names=('#timestamp', 'measured_current_A.real','measured_current_A.imag'	,'measured_current_B.real'	,'measured_current_B.imag'	,'measured_current_C.real',	'measured_current_C.imag',	'measured_voltage_A.real',	'measured_voltage_A.imag',	'measured_voltage_B.real',	'measured_voltage_B.imag','measured_voltage_C.real','measured_voltage_C.imag,','measured_real_power','measured_reactive_power')
	new_dict = {}
	with open(outputFile, 'r') as csvfile:
		swingnode = csv.DictReader(csvfile, dialect='excel', fieldnames= names, delimiter=',')
		for i in range(9):
			swingnode.next()
		for row in swingnode:
			new_dict[row['#timestamp']] = (row['measured_real_power'], row['measured_reactive_power'])
		return new_dict
def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	# TODO: add inputs needed based on spec.
	defaultInputs = {
		"feederName1": "Olin Barre Geo",
		"modelType": modelName,
		"runTime": "",
		"Start Time": "2013-08-01 0:00:00",
		"End Time": "2013-08-02 0:00:00",
		"Feeder Number": "1",
		"Folder Name": "test_Folder",

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
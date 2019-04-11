''' Calculate phase unbalance and determine mitigation options. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import matplotlib
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
plt.switch_backend('Agg')
from omf.models.voltageDrop import drawPlot

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf.weather import zipCodeToClimateName

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Calculate phase unbalance and determine mitigation options."
hidden = True

def _addCollectors(tree):
	for x in tree.values():
		if 'object' in x and 'load' in x['object'] and 'A' in x['phases'] and 'B' in x['phases'] and 'C' in x['phases']:
			x['groupid'] = 'threePhase'
	max_key = int(max(tree, key=int))
	tree[str(max_key+1)] = {'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)', 'object': 'collector', 'group': 'class=transformer', 'limit': '0', 'file': 'ZlossesTransformer.csv'}
	tree[str(max_key+2)] = {'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)', 'object': 'collector', 'group': 'class=underground_line', 'limit': '0', 'file': 'ZlossesUnderground.csv'}
	tree[str(max_key+3)] = {'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)', 'object': 'collector', 'group': 'class=overhead_line', 'limit': '0', 'file': 'ZlossesOverhead.csv'}
	tree[str(max_key+4)] = {'property': 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)', 'object': 'collector', 'group': 'class=triplex_line', 'limit': '0', 'file': 'ZlossesTriplex.csv'}
	tree[str(max_key+5)] = {'property': 'sum(power_A.real),sum(power_A.imag),sum(power_B.real),sum(power_B.imag),sum(power_C.real),sum(power_C.imag)', 'object': 'collector', 'group': 'class=inverter', 'limit': '0', 'file': 'distributedGen.csv'}
	tree[str(max_key+6)] = {'property': 'sum(power_A.real),sum(power_A.imag),sum(power_B.real),sum(power_B.imag),sum(power_C.real),sum(power_C.imag)', 'object': 'collector', 'group': 'class=load', 'limit': '0', 'file': 'loads.csv'}
	tree[str(max_key+7)] = {'property': 'sum(power_A.real),sum(power_A.imag),sum(power_B.real),sum(power_B.imag),sum(power_C.real),sum(power_C.imag)', 'object': 'collector', 'group': 'class=load AND groupid=threePhase', 'limit': '0', 'file': 'threephaseloads.csv'}
	return tree

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	# feederName = inputDict["feederName1"]
	print(os.listdir(modelDir))
	# Copy spcific climate data into model directory
	inputDict["climateName"] = zipCodeToClimateName(inputDict["zipCode"])
	shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"), 
		pJoin(modelDir, "climate.tmy2"))
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	# Create voltage drop plot.
	# print "*DEBUG: feederName:", feederName
	omd = json.load(open(pJoin(modelDir,feederName + '.omd')))
	tree = omd['tree']
	tree = _addCollectors(tree)
	with open(modelDir + '/withCollectors.glm', 'w') as collFile:
		treeString = feeder.sortedWrite(tree)
		collFile.write(treeString)
		# json.dump(tree, f1, indent=4)
	if inputDict.get("layoutAlgorithm", "geospatial") == "geospatial":
		neato = False
	else:
		neato = True
	# None cheack for edgeCol
	if inputDict.get("edgeCol", "None") == "None":
		edgeColValue = None
	else:
		edgeColValue = inputDict["edgeCol"]
	# None check for nodeCol
	if inputDict.get("nodeCol", "None") == "None":
		nodeColValue = None
	else:
		nodeColValue = inputDict["nodeCol"]
	# None check for edgeLabs
	if inputDict.get("edgeLabs", "None") == "None":
		edgeLabsValue = None
	else:
		edgeLabsValue = inputDict["edgeLabs"]
	# None check for nodeLabs
	if inputDict.get("nodeLabs", "None") == "None":
		nodeLabsValue = None
	else:
		nodeLabsValue = inputDict["nodeLabs"]
	# Type correction for colormap input
	if inputDict.get("customColormap", "True") == "True":
		customColormapValue = True
	else:
		customColormapValue = False
	# chart = voltPlot(omd, workDir=modelDir, neatoLayout=neato)
	chart = drawPlot(
		pJoin(modelDir, "withCollectors.glm"),
		workDir = modelDir,
		neatoLayout = False, #neato,
		edgeCol = edgeColValue,
		nodeCol = nodeColValue,
		nodeLabs = nodeLabsValue,
		edgeLabs = edgeLabsValue,
		customColormap = customColormapValue,
		rezSqIn = int(inputDict["rezSqIn"]))
	chart.savefig(pJoin(modelDir,"output.png"))
	with open(pJoin(modelDir,"output.png"),"rb") as inFile:
		outData["voltageDrop"] = inFile.read().encode("base64")
	outData['threePhase'] = _readCollectorCSV(modelDir+'/threephaseloads.csv')
	#outData['overheadLosses'] = _readCollectorCSV(modelDir+'/ZlossesOverhead.csv')
	return outData

def _readGroupRecorderCSV( filename ):
	dataDictionary = {}
	with open(filename,'r') as csvFile:
		reader = csv.reader(csvFile)
		# loop past the header, 
		[keys,vals] = [[],[]]
		for row in reader:
			if '# timestamp' in row:
				keys = row
				i = keys.index('# timestamp')
				keys.pop(i)
				vals = reader.next()
				vals.pop(i)
		for pos,key in enumerate(keys):
			dataDictionary[key] = vals[pos]
	return dataDictionary

def _readCollectorCSV(filename):
	dataDictionary = {}
	with open(filename, 'r') as csvFile:
		reader = csv.reader(csvFile)
		for row in reader:
			if '# property.. timestamp' in row:
				key_row = row
				value_row = reader.next()
				for pos, key in enumerate(key_row):
					if key == '# property.. timestamp':
						continue
					dataDictionary[key] = value_row[pos]
	return dataDictionary

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "Taxonomic Feeder Rooftop Solar",
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "forceDirected",
		"zipCode": "64735",
		"retailCost": "0.05",
		"discountRate": "7",
		"edgeCol" : "None",
		"nodeCol" : "VoltageImbalance",
		"nodeLabs" : "None",
		"edgeLabs" : "None",
		"customColormap" : "False",
		"rezSqIn" : "225",
		"parameterOne": "42",
		"parameterTwo": "42"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
		# shutil.copyfile(pJoin(__neoMetaModel__._omfDir, 'scratch', 'MPUPV', 'testResult.omd'), pJoin(modelDir, 'R1-12.47-1-solar_collectors.omd'))
		#temp_omd = json.load(open(pJoin(modelDir, defaultInputs["feederName1"]+'.omd')))
		#temp_omd['tree'] = _addCollectors(temp_omd['tree'])
		#with open(pJoin(modelDir, defaultInputs["feederName1"]+'.omd', 'w+')) as outfile:
		#	json.dump(temp_omd, outfile)
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
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()
	# _testingPlot()
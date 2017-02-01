''' Graph the voltage drop on a feeder. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import networkx as nx
from omf.models import __metaModel__
from __metaModel__ import *

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "The voltageDrop model runs loadflow to show system voltages at all nodes."

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,modelName+".html"),"r") as tempFile:
	template = Template(tempFile.read())

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	startTime = dt.datetime.now()
	allOutput = {}
	with open(pJoin(modelDir,'allInputData.json')) as inputFile:    
	    feederName = json.load(inputFile).get('feederName1','feeder')
	inputDict["feederName1"] = feederName
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(dt.datetime.now())
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	try:
		# Create voltage drop plot.
		# print "*DEBUG: feederName:", feederName
		omd = json.load(open(pJoin(modelDir,feederName+'.omd')))
		if inputDict.get("layoutAlgorithm", "geospatial") == "geospatial":
			neato = False
		else:
			neato = True 
		chart = voltPlot(omd, workDir=modelDir, neatoLayout=neato)
		chart.savefig(pJoin(modelDir,"output.png"))
		with open(pJoin(modelDir,"output.png"),"rb") as inFile:
			allOutput["voltageDrop"] = inFile.read().encode("base64")
		with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
			json.dump(allOutput, outFile, indent=4)
		# Update the runTime in the input file.
		endTime = dt.datetime.now()
		inputDict["runTime"] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
	except:
		# If input range wasn't valid delete output, write error to disk.
		cancel(modelDir)	
		thisErr = traceback.format_exc()
		print 'ERROR IN MODEL', modelDir, thisErr
		inputDict['stderr'] = thisErr
		with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
		
def voltPlot(omd, workDir=None, neatoLayout=False):
	''' Draw a color-coded map of the voltage drop on a feeder.
	Returns a matplotlib object. '''
	tree = omd.get('tree',{})
	# # Get rid of schedules and climate:
	for key in tree.keys():
		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
			del tree[key]
	# Make sure we have a voltDump:
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	tree[str(biggestKey*10)] = {"object":"voltdump","filename":"voltDump.csv"}
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
		print "gridlabD runInFilesystem with no specified workDir. Working in", workDir
	gridlabOut = gridlabd.runInFilesystem(tree, attachments=omd.get('attachments',{}), workDir=workDir)
	with open(pJoin(workDir,'voltDump.csv'),'r') as dumpFile:
		reader = csv.reader(dumpFile)
		reader.next() # Burn the header.
		keys = reader.next()
		voltTable = []
		for row in reader:
			rowDict = {}
			for pos,key in enumerate(keys):
				rowDict[key] = row[pos]
			voltTable.append(rowDict)
	# Calculate average node voltage deviation. First, helper functions.
	def pythag(x,y):
		''' For right triangle with sides a and b, return the hypotenuse. '''
		return math.sqrt(x**2+y**2)
	def digits(x):
		''' Returns number of digits before the decimal in the float x. '''
		return math.ceil(math.log10(x+1))
	def avg(l):
		''' Average of a list of ints or floats. '''
		return sum(l)/len(l)
	# Detect the feeder nominal voltage:
	for key in tree:
		ob = tree[key]
		if type(ob)==dict and ob.get('bustype','')=='SWING':
			feedVoltage = float(ob.get('nominal_voltage',1))
	# Tot it all up.
	nodeVolts = {}
	for row in voltTable:
		allVolts = []
		for phase in ['A','B','C']:
			phaseVolt = pythag(float(row['volt'+phase+'_real']),
							   float(row['volt'+phase+'_imag']))
			if phaseVolt != 0.0:
				if digits(phaseVolt)>3:
					# Normalize to 120 V standard
					phaseVolt = phaseVolt*(120/feedVoltage)
				allVolts.append(phaseVolt)
		nodeVolts[row.get('node_name','')] = avg(allVolts)
	# Color nodes by VOLTAGE.
	fGraph = feeder.treeToNxGraph(tree)
	voltChart = plt.figure(figsize=(15,15))
	plt.axes(frameon = 0)
	plt.axis('off')
	#set axes step equal
	voltChart.gca().set_aspect('equal')
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = nx.graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
	edgeIm = nx.draw_networkx_edges(fGraph, positions)
	nodeIm = nx.draw_networkx_nodes(fGraph,
		pos = positions,
		node_color = [nodeVolts.get(n,0) for n in fGraph.nodes()],
		linewidths = 0,
		node_size = 30,
		cmap = plt.cm.jet)
	plt.sci(nodeIm)
	plt.clim(110,130)
	plt.colorbar()
	return voltChart

def cancel(modelDir):
	''' Voltage drop runs so fast it's pointless to cancel a run. '''
	pass

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "Olin Barre Geo",
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "geospatial"
	}
	creationCode = __metaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__metaModel__._omfDir, "scratch", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _debugging():
	# Location
	modelLoc = pJoin(__metaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass 
	# Create New.
	new(modelLoc)
	# Pre-run.
	renderAndShow(template, modelName, modelDir=modelLoc)
	# Run the model.
	run(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(template, modelName, modelDir=modelLoc)

if __name__ == '__main__':
	_debugging()
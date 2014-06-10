''' Graph the voltage drop on a feeder. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import networkx as nx

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
	# # Copy spcific climate data into model directory
	# shutil.copy(pJoin(_omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"), 
	# 	pJoin(modelDir, "climate.tmy2"))
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

def voltPlot(tree, workDir=None):
	''' Draw a color-coded map of the voltage drop on a feeder.
	Returns a matplotlib object. '''
	# Get rid of schedules and climate:
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
	gridlabOut = gridlabd.runInFilesystem(tree, attachments=[], workDir=workDir)
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
	# Examples.
	# print 'Example Deviations:'
	# for key in nodeVolts.keys()[0:5]:
	# 	print key, nodeVolts[key]
	# Color nodes by VOLTAGE.
	fGraph = feeder.treeToNxGraph(tree)
	voltChart = plt.figure(figsize=(12,10))
	plt.axes(frameon = 0)
	plt.axis('off')
	for x in fGraph:
		print fGraph.node[x]
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
	plt.show()
	return voltChart

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

def _newTest():
	#TODO: delete me and change main back.
	import json
	tree = json.load(open("../data/Feeder/public/Olin Barre Geo.json")).get("tree",{})
	voltPlot(tree)

if __name__ == '__main__':
	_newTest()
	#_tests()
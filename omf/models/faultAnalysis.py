''' Graph the voltage drop on a feeder. '''

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
from omf.models.voltageDrop import drawPlot
plt.switch_backend('Agg')

# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *
# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Injects faults in to circuits and measures fault currents, voltages, and protective device response."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	outData = {}
	# feederName = inputDict["feederName1"]
	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict["feederName1"] = feederName
	# Create voltage drop plot.
	# print "*DEBUG: feederName:", feederName
	omd = json.load(open(pJoin(modelDir,feederName + '.omd')))
	if inputDict.get("layoutAlgorithm", "geospatial") == "geospatial":
		neato = False
	else:
		neato = True
	# None check for edgeCol
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
	# None check for scaleMin
	if inputDict.get("scaleMin", "None") == "None":
		scaleMinValue = None
	else:
		scaleMinValue = inputDict["scaleMin"]
	# None check for scaleMax
	if inputDict.get("scaleMax", "None") == "None":
		scaleMaxValue = None
	else:
		scaleMaxValue = inputDict["scaleMax"]
	if inputDict.get("simTime", "") == "":
		simTimeValue = '2000-01-01 0:00:00'
	else:
		simTimeValue = inputDict["simTime"]
	if inputDict.get("faultType", "None") == "None":
		faultTypeValue = None
	else:
		faultTypeValue = inputDict["faultType"]

	chart = drawPlot(
		pJoin(modelDir,feederName + ".omd"),
		neatoLayout = neato,
		edgeCol = edgeColValue,
		nodeCol = nodeColValue,
		nodeLabs = nodeLabsValue,
		edgeLabs = edgeLabsValue,
		customColormap = customColormapValue,
		scaleMin = scaleMinValue,
		scaleMax = scaleMaxValue,
		faultLoc = inputDict["faultLoc"],
		faultType = faultTypeValue,
		rezSqIn = int(inputDict["rezSqIn"]),
		simTime = simTimeValue,
		workDir = modelDir)
	chart.savefig(pJoin(modelDir, "output.png"))
	with open(pJoin(modelDir, "output.png"),"rb") as inFile:
		outData["voltageDrop"] = inFile.read().encode("base64")

	table = drawTable(
		pJoin(modelDir,feederName + ".omd"),
		workDir = modelDir)
	with open(pJoin(modelDir, "statusTable.html"), "w") as tabFile:
		tabFile.write(table)
	outData['tableHtml'] = table
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "Olin Barre Fault",
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "geospatial",
		"edgeCol" : "Current",
		"nodeCol" : "Voltage",
		"nodeLabs" : "None",
		"edgeLabs" : "None",
		"faultLoc" : "17720",
		"faultType" : "SLG-A",
		"customColormap" : "False",
		"scaleMin" : "None",
		"scaleMax" : "None",
		"rezSqIn" : "400",
		"simTime" : '2000-01-01 0:00:00'
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _testingPlot():
	PREFIX = omf.omfDir + '/scratch/CIGAR/'
	# FNAME = 'test_base_R4-25.00-1.glm_CLEAN.glm'
	# FNAME = 'test_Exercise_4_2_1.glm'
	# FNAME = 'test_ieee37node.glm'
	FNAME = 'test_ieee37nodeFaultTester.glm'
	# FNAME = 'test_ieee123nodeBetter.glm'
	# FNAME = 'test_large-R5-35.00-1.glm_CLEAN.glm'
	# FNAME = 'test_medium-R4-12.47-1.glm_CLEAN.glm'
	# FNAME = 'test_smsSingle.glm'
	# Hack: Agg backend doesn't work for interactivity. Switch to something we can use:
	# plt.switch_backend('MacOSX')
	chart = drawPlot(PREFIX + FNAME, neatoLayout=True, edgeCol="Current", nodeCol=None, nodeLabs="Name", edgeLabs=None, faultLoc="node713-704", faultType="TLG", customColormap=False, scaleMin=None, scaleMax=None, rezSqIn=225, simTime='2000-01-01 0:00:00')
	chart.savefig(PREFIX + "YO_WHATS_GOING_ON.png")
	# plt.show()

def drawTable(path, workDir=None):
	#return self.log
	
	warnings.filterwarnings("ignore")
	if path.endswith('.glm'):
		tree = omf.feeder.parse(path)
		attachments = []
	elif path.endswith('.omd'):
		omd = json.load(open(path))
		tree = omd.get('tree', {})
		attachments = omd.get('attachments',[])
	else:
		raise Exception('Invalid input file type. We require a .glm or .omd.')

	# Reminder: fuse objects have 'phase_X_status' instead of 'phase_X_state'
	protDevices = dict.fromkeys(['fuse', 'recloser', 'switch', 'sectionalizer'], False)
	#dictionary of protective device initial states for each phase
	protDevInitStatus = {}
	#dictionary of protective devices final states for each phase after running Gridlab-D
	protDevFinalStatus = {}
	#dictionary of protective device types to help the testing and debugging process
	protDevTypes = {}
	protDevOpModes = {}
	for key in tree:
		obj = tree[key]
		obType = obj.get('object')
		if obType in protDevices.keys():
			obName = obj.get('name', '')
			protDevTypes[obName] = obType
			if obType != 'fuse':
				protDevOpModes[obName] = obj.get('operating_mode', 'INDIVIDUAL')
			protDevices[obType] = True
			protDevInitStatus[obName] = {}
			protDevFinalStatus[obName] = {}
			for phase in ['A', 'B', 'C']:
				if obType != 'fuse':
					phaseState = obj.get('phase_' + phase + '_state','CLOSED')
				else:
					phaseState = obj.get('phase_' + phase + '_status','GOOD')
				if phase in obj.get('phases', ''):
					protDevInitStatus[obName][phase] = phaseState

	for key in protDevices.keys():
		if protDevices[key]:
			for phase in ['A', 'B', 'C']:
				with open(pJoin(workDir,key+'_phase_'+phase+'_state.csv'),'r') as statusFile:
					reader = csv.reader(statusFile)
					# loop past the header, 
					keys = []
					vals = []
					for row in reader:
						if '# timestamp' in row:
							keys = row
							i = keys.index('# timestamp')
							keys.pop(i)
							vals = reader.next()
							vals.pop(i)
					for pos,key2 in enumerate(keys):
						protDevFinalStatus[key2][phase] = vals[pos]

	html_str = """
		<table cellpadding="0" cellspacing="0">
			<thead>
				<tr>
					<th>Protective Device Name</th>
					<th>Device Type</th>
					<th>Initial States</th>
					<th>Final States</th>
					<th>Changes</th>
				</tr>
			</thead>
			<tbody>"""
	for device in protDevInitStatus.keys():
		row_str = "<tr><td>"+device+"</td><td>"
		devType = protDevTypes[device]
		if devType == 'fuse':
			row_str += "Fuse (F)</td><td>"
		elif devType == 'switch':
			row_str += "Switch (S)</td><td>"
		elif devType == 'recloser':
			row_str += "Recloser (R)</td><td>"
		elif devType == 'sectionalizer':
			row_str += "Sectionalizer (X)</td><td>"
		else:
			row_str += "Unknown</td><td>"
		for phase in protDevInitStatus[device].keys():
			row_str += "Phase " + phase + " = " + protDevInitStatus[device][phase] + "</br>"
		row_str += "</td><td>"
		for phase in protDevFinalStatus[device].keys():
			row_str += "Phase " + phase + " = " + protDevFinalStatus[device][phase] + "</br>"
		row_str += "</td>"
		noChange = True
		change_str = ""
		for phase in protDevFinalStatus[device].keys():
			try:
				if protDevInitStatus[device][phase] != protDevFinalStatus[device][phase]:
					change_str += "Phase " + phase + " : " + protDevInitStatus[device][phase] + " -> " + protDevFinalStatus[device][phase] + "</br>"
					noChange = False
			except:
				pass #key error...
		if noChange:
			row_str += "<td>No Change"
		else:
			row_str += "<td style=\"color: red;\">"
			row_str += change_str
		row_str += "</td></tr>"
		html_str += row_str
	html_str += """</tbody></table>"""
	return html_str

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
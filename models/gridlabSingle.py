''' Powerflow results for one Gridlab instance. '''

import json, os, sys, tempfile, webbrowser, time, shutil, datetime, subprocess, datetime as dt
import multiprocessing
from os.path import join as pJoin
from jinja2 import Template
import __util__ as util

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(_myDir)

# OMF imports
sys.path.append(_omfDir)
import feeder
from solvers import gridlabd

# Our HTML template for the interface:
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
		allOutputData=allOutputData, modelStatus=getStatus(modelDir), pathPrefix=pathPrefix,
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
	os.makedirs(modelDir)
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
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	# Touch the PID to indicate the run has started.
	with open(pJoin(modelDir,"PID.txt"), 'a'):
		os.utime(pJoin(modelDir,"PID.txt"), None)
	# If we are re-running, remove output:
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
	except:
		pass
	# Start the computation.
	backProc = multiprocessing.Process(target=runForeground, args=(modelDir,))
	backProc.start()
	print "SENT TO BACKGROUND", modelDir

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

def runForeground(modelDir):
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
	rawOut = gridlabd.runInFilesystem(tree, attachments=feederJson["attachments"], 
		keepFiles=True, workDir=modelDir)
	cleanOut = {}
	# Std Err and Std Out
	cleanOut['stderr'] = rawOut['stderr']
	cleanOut['stdout'] = rawOut['stdout']
	# Time Stamps
	for key in rawOut:
		if '# timestamp' in rawOut[key]:
			cleanOut['timeStamps'] = rawOut[key]['# timestamp']
			break
		elif '# property.. timestamp' in rawOut[key]:
			cleanOut['timeStamps'] = rawOut[key]['# property.. timestamp']
		else:
			cleanOut['timeStamps'] = []
	# Day/Month Aggregation Setup:
	stamps = cleanOut.get('timeStamps',[])
	level = allInputData.get('simLengthUnits','hours')
	# Climate
	for key in rawOut:
		if key.startswith('Climate_') and key.endswith('.csv'):
			cleanOut['climate'] = {}
			cleanOut['climate']['Rain Fall (in/h)'] = util.hdmAgg(rawOut[key].get('rainfall'), sum, level)
			cleanOut['climate']['Wind Speed (m/s)'] = util.hdmAgg(rawOut[key].get('wind_speed'), util.avg, level)
			cleanOut['climate']['Temperature (F)'] = util.hdmAgg(rawOut[key].get('temperature'), max, level)
			cleanOut['climate']['Snow Depth (in)'] = util.hdmAgg(rawOut[key].get('snowdepth'), max, level)
			cleanOut['climate']['Direct Insolation (W/m^2)'] = util.hdmAgg(rawOut[key].get('solar_direct'), sum, level)
	# Voltage Band
	if 'VoltageJiggle.csv' in rawOut:
		cleanOut['allMeterVoltages'] = {}
		cleanOut['allMeterVoltages']['Min'] = util.hdmAgg(rawOut['VoltageJiggle.csv']['min(voltage_12.mag)'], min, level)
		cleanOut['allMeterVoltages']['Mean'] = util.hdmAgg(rawOut['VoltageJiggle.csv']['mean(voltage_12.mag)'], util.avg, level)
		cleanOut['allMeterVoltages']['StdDev'] = util.hdmAgg(rawOut['VoltageJiggle.csv']['std(voltage_12.mag)'], util.avg, level)
		cleanOut['allMeterVoltages']['Max'] = util.hdmAgg(rawOut['VoltageJiggle.csv']['max(voltage_12.mag)'], max, level)
	# Power Consumption
	cleanOut['Consumption'] = {}
	for key in rawOut:
		if key.startswith('SwingKids_') and key.endswith('.csv'):
			oneSwingPower = util.hdmAgg(util.vecPyth(rawOut[key]['sum(power_in.real)'],rawOut[key]['sum(power_in.imag)']), util.avg, level)
			if 'Power' not in cleanOut['Consumption']:
				cleanOut['Consumption']['Power'] = oneSwingPower
			else:
				cleanOut['Consumption']['Power'] = util.vecSum(oneSwingPower,cleanOut['Consumption']['Power'])
		elif key.startswith('Inverter_') and key.endswith('.csv'): 	
			realA = rawOut[key]['power_A.real']
			realB = rawOut[key]['power_B.real']
			realC = rawOut[key]['power_C.real']
			imagA = rawOut[key]['power_A.imag']
			imagB = rawOut[key]['power_B.imag']
			imagC = rawOut[key]['power_C.imag']
			oneDgPower = util.hdmAgg(util.vecSum(util.vecPyth(realA,imagA),util.vecPyth(realB,imagB),util.vecPyth(realC,imagC)), util.avg, level)
			if 'DG' not in cleanOut['Consumption']:
				cleanOut['Consumption']['DG'] = oneDgPower
			else:
				cleanOut['Consumption']['DG'] = util.vecSum(oneDgPower,cleanOut['Consumption']['DG'])
		elif key.startswith('Windmill_') and key.endswith('.csv'):
			vrA = rawOut[key]['voltage_A.real']
			vrB = rawOut[key]['voltage_B.real']
			vrC = rawOut[key]['voltage_C.real']
			viA = rawOut[key]['voltage_A.imag']
			viB = rawOut[key]['voltage_B.imag']
			viC = rawOut[key]['voltage_C.imag']
			crB = rawOut[key]['current_B.real']
			crA = rawOut[key]['current_A.real']
			crC = rawOut[key]['current_C.real']
			ciA = rawOut[key]['current_A.imag']
			ciB = rawOut[key]['current_B.imag']
			ciC = rawOut[key]['current_C.imag']
			powerA = util.vecProd(util.vecPyth(vrA,viA),util.vecPyth(crA,ciA))
			powerB = util.vecProd(util.vecPyth(vrB,viB),util.vecPyth(crB,ciB))
			powerC = util.vecProd(util.vecPyth(vrC,viC),util.vecPyth(crC,ciC))
			oneDgPower = util.hdmAgg(util.vecSum(powerA,powerB,powerC), util.avg, level)
			if 'DG' not in cleanOut['Consumption']:
				cleanOut['Consumption']['DG'] = oneDgPower
			else:
				cleanOut['Consumption']['DG'] = util.vecSum(oneDgPower,cleanOut['Consumption']['DG'])
		elif key in ['OverheadLosses.csv', 'UndergroundLosses.csv', 'TriplexLosses.csv', 'TransformerLosses.csv']:
			realA = rawOut[key]['sum(power_losses_A.real)']
			imagA = rawOut[key]['sum(power_losses_A.imag)']
			realB = rawOut[key]['sum(power_losses_B.real)']
			imagB = rawOut[key]['sum(power_losses_B.imag)']
			realC = rawOut[key]['sum(power_losses_C.real)']
			imagC = rawOut[key]['sum(power_losses_C.imag)']
			oneLoss = util.hdmAgg(util.vecSum(util.vecPyth(realA,imagA),util.vecPyth(realB,imagB),util.vecPyth(realC,imagC)), util.avg, level)
			if 'Losses' not in cleanOut['Consumption']:
				cleanOut['Consumption']['Losses'] = oneLoss
			else:
				cleanOut['Consumption']['Losses'] = util.vecSum(oneLoss,cleanOut['Consumption']['Losses'])
	# Aggregate up the timestamps:
	if level=='days':
		cleanOut['timeStamps'] = util.aggSeries(stamps, stamps, lambda x:x[0][0:10], 'days')
	elif level=='months':
		cleanOut['timeStamps'] = util.aggSeries(stamps, stamps, lambda x:x[0][0:7], 'months')
	# Write the output.
	with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
		json.dump(cleanOut, outFile, indent=4)
	# Update the runTime in the input file.
	endTime = dt.datetime.now()
	allInputData["runTime"] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
	with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
		json.dump(allInputData, inFile, indent=4)
	# Clean up the PID file.
	os.remove(pJoin(modelDir,"PID.txt"))
	print "DONE RUNNING", modelDir

def cancel(modelDir):
	''' Try to cancel a currently running model. '''
	try:
		with open(pJoin(modelDir,"PID.txt"),"r") as pidFile:
			pid = int(pidFile.read())
			os.kill(pid, 15)
		print "CANCELED", modelDir
		os.remove(pJoin(modelDir, "PID.txt"))
	except:
		print "ATTEMPTED AND FAILED TO CANCEL", modelDir
		for fName in os.listdir(modelDir):
			if fName in ["PID.txt","allOutputData.json"]:
				os.remove(pJoin(modelDir,fName))

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
		"user": "admin", # Really only used with web.py.
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
	# Create a model.
	create(workDir, inData)
	# Show the model (should look like it's running).
	renderAndShow(modelDir=modelLoc)
	# Run the model.
	runForeground(modelLoc)
	## Cancel the model.
	# time.sleep(2)
	# cancel(modelLoc)
	# Show the output.
	renderAndShow(modelDir=modelLoc)
	# Delete the model.
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()

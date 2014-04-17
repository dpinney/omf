''' Calculate solar photovoltaic system output using PVWatts. '''

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
from solvers import nrelsam

# Our HTML template for the interface:
with open(pJoin(_myDir,"pvWatts.html"),"r") as tempFile:
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
		os.rename(temp.name, temp.name + ".html")
		fullArg = "file://" + temp.name + ".html"
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
	shutil.copy(pJoin(_omfDir,"data","Climate",inData["climateName"] + ".tmy2"),
		pJoin(modelDir,"climate.tmy2"))

def run(modelDir):
	''' Run the model in its directory. '''
	# TODO: test implementation.
	startTime = dt.datetime.now()
	allInputData = json.load(open(pJoin(modelDir,"allInputData.json")))
	# Set up SAM data structures.
	ssc = nrelsam.SSCAPI()
	dat = ssc.ssc_data_create()
	# Required user inputs.
	ssc.ssc_data_set_string(dat, "file_name", modelDir + "/climate.tmy2")
	ssc.ssc_data_set_number(dat, "system_size", float(allInputData["systemSize"]))
	ssc.ssc_data_set_number(dat, "derate", float(allInputData["derate"]))
	ssc.ssc_data_set_number(dat, "track_mode", float(allInputData["trackingMode"]))
	ssc.ssc_data_set_number(dat, "azimuth", float(allInputData["azimuth"]))
	# Advanced inputs with defaults.
	ssc.ssc_data_set_number(dat, "rotlim", float(allInputData["rotlim"]))
	ssc.ssc_data_set_number(dat, "t_noct", float(allInputData["t_noct"]))
	ssc.ssc_data_set_number(dat, "t_ref", float(allInputData["t_ref"]))
	ssc.ssc_data_set_number(dat, "gamma", float(allInputData["gamma"]))
	ssc.ssc_data_set_number(dat, "inv_eff", float(allInputData["inv_eff"]))
	ssc.ssc_data_set_number(dat, "fd", float(allInputData["fd"]))
	ssc.ssc_data_set_number(dat, "i_ref", float(allInputData["i_ref"]))
	ssc.ssc_data_set_number(dat, "poa_cutin", float(allInputData["poa_cutin"]))
	ssc.ssc_data_set_number(dat, "w_stow", float(allInputData["w_stow"]))
	# Complicated optional inputs.
	ssc.ssc_data_set_number(dat, "tilt_eq_lat", 1)
	# ssc.ssc_data_set_array(dat, 'shading_hourly', ...) 	# Hourly beam shading factors
	# ssc.ssc_data_set_matrix(dat, 'shading_mxh', ...) 		# Month x Hour beam shading factors
	# ssc.ssc_data_set_matrix(dat, 'shading_azal', ...) 	# Azimuth x altitude beam shading factors
	# ssc.ssc_data_set_number(dat, 'shading_diff', ...) 	# Diffuse shading factor
	# ssc.ssc_data_set_number(dat, 'enable_user_poa', ...)	# Enable user-defined POA irradiance input = 0 or 1
	# ssc.ssc_data_set_array(dat, 'user_poa', ...) 			# User-defined POA irradiance in W/m2
	# ssc.ssc_data_set_number(dat, 'tilt', 999)
	# Run PV system simulation.
	mod = ssc.ssc_module_create("pvwattsv1")
	ssc.ssc_module_exec(mod, dat)
	# Setting options for start time.
	startDateTime = allInputData.get("simLengthUnits","")
	simStartDate = allInputData["simStartDate"]
	if startDateTime != "days":
		startDateTime = simStartDate + " 00:00:00 PDT"
	# Set aggregation function constants.
	agg = lambda x,y:_aggData(x,y,allInputData["simStartDate"],
		int(allInputData["simLength"]), allInputData["simLengthUnits"], ssc, dat)
	# Timestamp output.
	outData = {}
	outData["timeStamps"] = [startDateTime for x in range(int(allInputData["simLength"]))]
	# Geodata output.
	outData["city"] = ssc.ssc_data_get_string(dat, "city")
	outData["state"] = ssc.ssc_data_get_string(dat, "state")
	outData["lat"] = ssc.ssc_data_get_number(dat, "lat")
	outData["lon"] = ssc.ssc_data_get_number(dat, "lon")
	outData["elev"] = ssc.ssc_data_get_number(dat, "elev")
	# Weather output.
	outData["climate"] = {}
	outData["climate"]["Direct Irradiance (W/m^2)"] = agg("dn", util.avg)
	outData["climate"]["Difuse Irradiance (W/m^2)"] = agg("df", util.avg)
	outData["climate"]["Ambient Temperature (F)"] = agg("tamb", util.avg)
	outData["climate"]["Cell Temperature (F)"] = agg("tcell", util.avg)
	outData["climate"]["Wind Speed (m/s)"] = agg("wspd", util.avg)
	# Power generation.
	outData["Consumption"] = {}
	outData["Consumption"]["Power"] = [x for x in agg("ac", util.avg)]
	outData["Consumption"]["Losses"] = [0 for x in agg("ac", util.avg)]
	outData["Consumption"]["DG"] = agg("ac", util.avg)
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	# Write the output.
	with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
		json.dump(outData, outFile, indent=4)
	# Update the runTime in the input file.
	endTime = dt.datetime.now()
	allInputData["runTime"] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
	with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
		json.dump(allInputData, inFile, indent=4)

def _aggData(key, aggFun, simStartDate, simLength, simLengthUnits, ssc, dat):
	''' Function to aggregate output if we need something other than hour level. '''
	u = simStartDate
	d = dt.datetime(int(u[0:4]),int(u[5:7]),int(u[8:10]))
	v = d.isocalendar()
	initHour = int(8760*(v[1]+v[2]/7)/52.0)
	fullData = ssc.ssc_data_get_array(dat, key)
	if simLengthUnits == "days":
		multiplier = 24
	else:
		multiplier = 1
	hourData = [fullData[(initHour+i)%8760] for i in xrange(simLength*multiplier)]
	if simLengthUnits == "minutes":
		pass
	elif simLengthUnits == "hours":
		return hourData
	elif simLengthUnits == "days":
		split = [hourData[x:x+24] for x in xrange(simLength)]
		return map(aggFun, split)

def cancel(modelDir):
	''' PV Watts runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# Variables
	workDir = pJoin(_omfDir,"data","Model")
	inData = { "modelName": "Automated Testing",
		"simStartDate": "2012-04-01",
		"simLengthUnits": "hours",
		"modelType": "pvWatts",
		"climateName": "AL-HUNTSVILLE",
		"simLength": "100",
		"systemSize":"10",
		"derate":"0.97",
		"trackingMode":"0",
		"azimuth":"180",
		"user": "admin", # Really only used with web.py.
		"runTime": "",
		"rotlim":"45.0",
		"t_noct":"45.0",
		"t_ref":"25.0",
		"gamma":"-0.5",
		"inv_eff":"0.92",
		"fd":"1.0",
		"i_ref":"1000",
		"poa_cutin":"0",
		"w_stow":"0"}
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
	run(modelLoc)
	# Show the output.
	renderAndShow(modelDir=modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
''' Calculate solar photovoltaic system output using our special financial model. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, math, datetime as dt
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *
from random import random
import xlwt, traceback
# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import nrelsam

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"solarSunda.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))	
	except Exception, e:
		pass
	try:
		# Check whether model exist or not
		if not os.path.isdir(modelDir):
			os.makedirs(modelDir)
			inputDict["created"] = str(dt.datetime.now())
		# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
		with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
			json.dump(inputDict, inputFile, indent = 4)
		#Set static input data
		inputDict["simStartDate"] = "2013-01-01"
		inputDict["simLengthUnits"] = "hours"
		inputDict["modelType"] = "solarSunda"
		inputDict["climateName"] = "VA-STERLING"
		inputDict["simLength"] = "350"
		inputDict["degradation"] = "0.5"         #*paul: 0.8?
		inputDict["derate"] = "87"		
		inputDict["inverterEfficiency"] = "96"		
		inputDict["tilt"] = "True"	
		inputDict["manualTilt"] = "39"		
		inputDict["trackingMode"] = "0"
		inputDict["azimuth"] = "180"		
		inputDict["runTime"] = ""				
		inputDict["rotlim"] = "45.0"
		inputDict["gamma"] = "-0.45"
		inputDict["omCost"] = "1000"	
		if (float(inputDict["systemSize"]) > 250):
			inputDict["inverterCost"] = float(107000)
		# Copy spcific climate data into model directory
		shutil.copy(pJoin(__metaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"), 
			pJoin(modelDir, "climate.tmy2"))
		# Ready to run
		startTime = dt.datetime.now()
		# Set up SAM data structures.
		ssc = nrelsam.SSCAPI()
		dat = ssc.ssc_data_create()
		# Required user inputs.
		ssc.ssc_data_set_string(dat, "file_name", modelDir + "/climate.tmy2")
		ssc.ssc_data_set_number(dat, "system_size", float(inputDict.get("systemSize", 100)))
		derate = float(inputDict.get("derate", 100))/100 * float(inputDict.get("inverterEfficiency", 92))/100
		ssc.ssc_data_set_number(dat, "derate", derate)
		ssc.ssc_data_set_number(dat, "track_mode", float(inputDict.get("trackingMode", 0)))
		ssc.ssc_data_set_number(dat, "azimuth", float(inputDict.get("azimuth", 180)))
		# Advanced inputs with defaults.
		ssc.ssc_data_set_number(dat, "rotlim", float(inputDict.get("rotlim", 45)))
		ssc.ssc_data_set_number(dat, "gamma", float(inputDict.get("gamma", 0.5))/100)
		# Complicated optional inputs.
		ssc.ssc_data_set_number(dat, "tilt_eq_lat", 1)
		# Run PV system simulation.
		mod = ssc.ssc_module_create("pvwattsv1")
		ssc.ssc_module_exec(mod, dat)
		# Setting options for start time.
		simLengthUnits = inputDict.get("simLengthUnits","hours")
		simStartDate = inputDict.get("simStartDate", "2014-01-01")
		# Set the timezone to be UTC, it won't affect calculation and display, relative offset handled in pvWatts.html 
		startDateTime = simStartDate + " 00:00:00 UTC"
		# Timestamp output.
		outData = {}
		outData["timeStamps"] = [dt.datetime.strftime(
			dt.datetime.strptime(startDateTime[0:19],"%Y-%m-%d %H:%M:%S") + 
			dt.timedelta(**{simLengthUnits:x}),"%Y-%m-%d %H:%M:%S") + " UTC" for x in range(int(inputDict.get("simLength", 8760)))]
		# Geodata output.
		outData["city"] = ssc.ssc_data_get_string(dat, "city")
		outData["state"] = ssc.ssc_data_get_string(dat, "state")
		outData["lat"] = ssc.ssc_data_get_number(dat, "lat")
		outData["lon"] = ssc.ssc_data_get_number(dat, "lon")
		outData["elev"] = ssc.ssc_data_get_number(dat, "elev")
		# Weather output.
		outData["climate"] = {}
		outData["climate"]["Global Horizontal Radiation (W/m^2)"] = ssc.ssc_data_get_array(dat, "gh")
		outData["climate"]["Plane of Array Irradiance (W/m^2)"] = ssc.ssc_data_get_array(dat, "poa")
		outData["climate"]["Ambient Temperature (F)"] = ssc.ssc_data_get_array(dat, "tamb")
		outData["climate"]["Cell Temperature (F)"] = ssc.ssc_data_get_array(dat, "tcell")
		outData["climate"]["Wind Speed (m/s)"] = ssc.ssc_data_get_array(dat, "wspd")		
		# Power generation.
		outData["powerOutputAc"] = ssc.ssc_data_get_array(dat, "ac")	
		# Cashflow outputs.
		arraySize = float(inputDict.get("systemSize",0))*1.3908
		pvModules = arraySize * float(inputDict.get("moduleCost",0))*1000 #off by 4000
		racking = arraySize * float(inputDict.get("rackCost",0))*1000
		inverters = math.ceil(float(inputDict.get("systemSize",0))/1000/0.5) * float(inputDict.get("inverterCost",0))
		gear = 22000		
		balance = float(inputDict.get("systemSize",0))*1.3908 * 134
		numberPanels = (arraySize*1000/305)
		combiners = math.ceil(numberPanels/19/24) * float(1800)  #*
		hardwareCosts = (pvModules + racking + inverters + 22000 + balance + combiners + arraySize*1.0 + 1.0*28000 + 1.0*12500)*1.02
		#hardware = pvModules + racking + inverters + disconnectGear + balance + combiners + wireManagement + transformer + weatherMonitor + shipping
		EPCmarkup = float(inputDict.get("EPCRate",0))/100 * hardwareCosts
		laborCosts = float(inputDict.get("mechLabor",0))*160 + float(inputDict.get("elecLabor",0))*75 + float(inputDict.get("pmCost",0)) + EPCmarkup	
		#sitePrep = 60395 #material + labor
		sitePrep = 56834
		constrEquip = 48000
		installCosts = numberPanels * (15.00 + 12.50 + 1.50) +  arraySize * (20.00 + 100) + 72*50.0 + 60 * 50.0 + 70 * 50.0 + 10 * 50 + 5 * 50.0 + 30 * 50.0 + 70 * 50.0 
		minLandSize = float(inputDict.get("systemSize",0))/1000*5 + 1
		land = float(inputDict.get("costAcre",0))*minLandSize
		totalCosts = hardwareCosts + laborCosts + sitePrep + constrEquip + installCosts + land
		totalFees= float(inputDict.get("devCost",0))/100 * totalCosts
		outData["totalCost"] = totalCosts + totalFees + float(inputDict.get("interCost",0))
		#One year generation
		outData["oneYearGenerationWh"] = sum(outData["powerOutputAc"])
		# Monthly aggregation outputs.
		# Stdout/stderr.
		outData["stdout"] = "Success"
		outData["stderr"] = ""
		# Write the output.
		with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
			json.dump(outData, outFile, indent=4)
		# Update the runTime in the input file.
		endTime = dt.datetime.now()
		inputDict["runTime"] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
	except:
		# If input range wasn't valid delete output, write error to disk.
		thisErr = traceback.format_exc()
		inputDict['stderr'] = thisErr
		with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
		try:
			os.remove(pJoin(modelDir,"allOutputData.json"))
		except Exception, e:
			pass

def _runningSum(inList):
	''' Give a list of running sums of inList. '''
	return [sum(inList[:i+1]) for (i,val) in enumerate(inList)]

def cancel(modelDir):
	''' solarSunda runs so fast it's pointless to cancel a run. '''
	pass

def _tests():	
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	# TODO: Fix inData because it's out of date.
	inData = {"simStartDate": "2013-01-01",
		"simLengthUnits": "hours",
		"modelType": "solarSunda",
		"climateName": "VA-STERLING",
		"simLength": "8760",
		"costAcre": "10000",
		"systemSize":"250",
		"moduleCost": "0.720",
		"rackCost": "0.137",
		"inverterCost": "61963",		
		"mechLabor": "50",
		"elecLabor": "75",
		"pmCost": "15000",
		"interCost": "25000",
		"devCost": "2",
		"EPCRate": "10",
		"distAdder": "2",
		"discRate": "2.32",
		"loanRate": "2.00",
		"NCREBRate": "4.31",
		"taxEquityReturn": "8.50",
		"lifeSpan": "30",
		"degradation": "0.5",
		"derate": "87",
		"inverterEfficiency": "96",
		"tilt": "True",
		"manualTilt":"34.65",	
		"trackingMode":"0",
		"azimuth":"180",
		"runTime": "",
		"rotlim":"45.0",
		"gamma":"-0.45",}
	modelLoc = pJoin(workDir,"admin","Automated solarSunda Testing")	
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow(template)
	# Run the model.
	run(modelLoc, inData)
	# Show the output.
	renderAndShow(template, modelDir = modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()

	'''		'''
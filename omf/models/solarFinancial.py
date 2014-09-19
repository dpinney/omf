''' Calculate solar photovoltaic system output using our special financial model. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, math, datetime as dt
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import nrelsam

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"solarFinancial.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(dt.datetime.now())
	# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
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
	ssc.ssc_data_set_number(dat, "derate", float(inputDict.get("derate", 0.77)))
	ssc.ssc_data_set_number(dat, "track_mode", float(inputDict.get("trackingMode", 0)))
	ssc.ssc_data_set_number(dat, "azimuth", float(inputDict.get("azimuth", 180)))
	# Advanced inputs with defaults.
	ssc.ssc_data_set_number(dat, "rotlim", float(inputDict.get("rotlim", 45)))
	ssc.ssc_data_set_number(dat, "t_noct", float(inputDict.get("t_noct", 45)))
	ssc.ssc_data_set_number(dat, "t_ref", float(inputDict.get("t_ref", 25)))
	ssc.ssc_data_set_number(dat, "gamma", float(inputDict.get("gamma", 0.5)))
	ssc.ssc_data_set_number(dat, "inv_eff", float(inputDict.get("inv_eff", 0.92)))
	ssc.ssc_data_set_number(dat, "fd", float(inputDict.get("fd", 1)))
	ssc.ssc_data_set_number(dat, "i_ref", float(inputDict.get("i_ref", 1000)))
	ssc.ssc_data_set_number(dat, "poa_cutin", float(inputDict.get("poa_cutin", 0)))
	ssc.ssc_data_set_number(dat, "w_stow", float(inputDict.get("w_stow", 0)))
	# Complicated optional inputs.
	ssc.ssc_data_set_number(dat, "tilt_eq_lat", 1)
	# ssc.ssc_data_set_array(dat, 'shading_hourly', ...) 	# Hourly beam shading factors
	# ssc.ssc_data_set_matrix(dat, 'shading_mxh', ...) 		# Month x Hour beam shading factors
	# ssc.ssc_data_set_matrix(dat, ' shading_azal', ...) 	# Azimuth x altitude beam shading factors
	# ssc.ssc_data_set_number(dat, 'shading_diff', ...) 	# Diffuse shading factor
	# ssc.ssc_data_set_number(dat, 'enable_user_poa', ...)	# Enable user-defined POA irradiance input = 0 or 1
	# ssc.ssc_data_set_array(dat, 'user_poa', ...) 			# User-defined POA irradiance in W/m2
	# ssc.ssc_data_set_number(dat, 'tilt', 999)
	# Run PV system simulation.
	mod = ssc.ssc_module_create("pvwattsv1")
	ssc.ssc_module_exec(mod, dat)
	# Setting options for start time.
	simLengthUnits = inputDict.get("simLengthUnits","hours")
	simStartDate = inputDict.get("simStartDate", "2014-01-01")
	# Set the timezone to be UTC, it won't affect calculation and display, relative offset handled in pvWatts.html 
	startDateTime = simStartDate + " 00:00:00 UTC"
	# Set aggregation function constants.
	agg = lambda x,y:_aggData(x,y,inputDict["simStartDate"],
		int(inputDict["simLength"]), inputDict.get("simLengthUnits","hours"), ssc, dat)
	avg = lambda x:sum(x)/len(x)
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
	outData["climate"]["Direct Irradiance (W/m^2)"] = agg("dn", avg)
	outData["climate"]["Difuse Irradiance (W/m^2)"] = agg("df", avg)
	outData["climate"]["Ambient Temperature (F)"] = agg("tamb", avg)
	outData["climate"]["Cell Temperature (F)"] = agg("tcell", avg)
	outData["climate"]["Wind Speed (m/s)"] = agg("wspd", avg)
	# Power generation.
	outData["powerOutputAc"] = [x for x in agg("ac", avg)]
	# Cashflow outputs.
	lifeSpan = int(inputDict.get("lifeSpan",30))
	lifeYears = range(1, 1 + lifeSpan)
	retailCost = float(inputDict.get("retailCost",0.0))
	degradation = float(inputDict.get("degradation",0.5))/100
	installCost = float(inputDict.get("installCost",0.0))
	outData["oneYearGenerationWh"] = sum(outData["powerOutputAc"])
	outData["lifeGenerationDollars"] = [roundSig(retailCost*(1.0/1000.0)*outData["oneYearGenerationWh"]*(1.0-(x*degradation)),2) for x in lifeYears]
	outData["lifeOmCosts"] = [-1.0*float(inputDict["omCost"]) for x in lifeYears]
	outData["lifePurchaseCosts"] = [-1.0 * installCost] + [0 for x in lifeYears[1:]]
	outData["netCashFlow"] = [roundSig(x+y+z,2) for (x,y,z) in zip(outData["lifeGenerationDollars"], outData["lifeOmCosts"], outData["lifePurchaseCosts"])]
	outData["cumCashFlow"] = map(lambda x:roundSig(x,2), _runningSum(outData["netCashFlow"]))
	outData["ROI"] = roundSig(sum(outData["netCashFlow"]), 2)
	#TODO: implement these two.
	outData["NPV"] = "TBD"
	outData["IRR"] = "TBD"
	# Monthly aggregation outputs.
	months = {"Jan":0,"Feb":1,"Mar":2,"Apr":3,"May":4,"Jun":5,"Jul":6,"Aug":7,"Sep":8,"Oct":9,"Nov":10,"Dec":11}
	totMonNum = lambda x:sum([z for (y,z) in zip(outData["timeStamps"], outData["powerOutputAc"]) if y.startswith(simStartDate[0:4] + "-{0:02d}".format(x+1))])
	outData["monthlyGeneration"] = [[a, roundSig(totMonNum(b),2)] for (a,b) in sorted(months.items(), key=lambda x:x[1])]
	# Heatmaped hour+month outputs.
	hours = range(24)
	from random import random
	totHourMon = lambda h,m:sum([z for (y,z) in zip(outData["timeStamps"], outData["powerOutputAc"]) if y[5:7]=="{0:02d}".format(m+1) and y[11:13]=="{0:02d}".format(h+1)])
	outData["seasonalPerformance"] = [[x,y,totHourMon(x,y)] for x in hours for y in months.values()]
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

def _runningSum(inList):
	''' Give a list of running sums of inList. '''
	return [sum(inList[:i+1]) for (i,val) in enumerate(inList)]

def _aggData(key, aggFun, simStartDate, simLength, simLengthUnits, ssc, dat):
	''' Function to aggregate output if we need something other than hour level. '''
	u = simStartDate
	# pick a common year, ignoring the leap year, it won't affect to calculate the initHour
	d = dt.datetime(2013, int(u[5:7]),int(u[8:10])) 
	# first day of the year	
	sd = dt.datetime(2013, 01, 01) 
	# convert difference of datedelta object to number of hours 
	initHour = int((d-sd).total_seconds()/3600)
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
	''' solarFinancial runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	# TODO: Fix inData because it's out of date.
	inData = {"simStartDate": "2013-01-01",
		"simLengthUnits": "hours",
		"modelType": "solarFinancial",
		"climateName": "AL-HUNTSVILLE",
		"simLength": "8760",
		"systemSize":"100",
		"installCost":"100000",
		"derate":"0.77",
		"trackingMode":"0",
		"azimuth":"180",
		"runTime": "",
		"rotlim":"45.0",
		"t_noct":"45.0",
		"t_ref":"25.0",
		"gamma":"-0.5",
		"inv_eff":"0.92",
		"fd":"1.0",
		"i_ref":"1000",
		"poa_cutin":"0",
		"omCost": "1000",
		"w_stow":"0"}
	modelLoc = pJoin(workDir,"admin","Automated solarFinancial Testing")
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
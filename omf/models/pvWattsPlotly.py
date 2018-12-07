''' Calculate solar photovoltaic system output using PVWatts. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback
from os.path import join as pJoin
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# OMF imports
import omf.feeder as feeder
from omf.solvers import nrelsam2013
from omf.weather import zipCodeToClimateName

# Model metadata:
tooltip = "The pvWatts model runs the NREL pvWatts tool for quick estimation of solar panel output."
modelName, template = metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	#plotly imports. Here for now so web server starts.
	import plotly
	# from plotly import __version__
	# from plotly.offline import download_plotlyjs, plot
	# from plotly import tools
	import plotly.graph_objs as go
	# Copy specific climate data into model directory
	inputDict["climateName"] = zipCodeToClimateName(inputDict["zipCode"])
	shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"), 
		pJoin(modelDir, "climate.tmy2"))
	# Set up SAM data structures.
	ssc = nrelsam2013.SSCAPI()
	dat = ssc.ssc_data_create()
	# Required user inputs.
	ssc.ssc_data_set_string(dat, "file_name", modelDir + "/climate.tmy2")
	ssc.ssc_data_set_number(dat, "system_size", float(inputDict["systemSize"]))
	ssc.ssc_data_set_number(dat, "derate", 0.01 * float(inputDict["nonInverterEfficiency"]))
	ssc.ssc_data_set_number(dat, "track_mode", float(inputDict["trackingMode"]))
	ssc.ssc_data_set_number(dat, "azimuth", float(inputDict["azimuth"]))
	# Advanced inputs with defaults.
	if (inputDict.get("tilt",0) == "-"):
		tilt_eq_lat = 1.0
		manualTilt = 0.0
	else:
		tilt_eq_lat = 0.0
		manualTilt = float(inputDict.get("tilt",0))
	ssc.ssc_data_set_number(dat, "tilt_eq_lat", tilt_eq_lat)
	ssc.ssc_data_set_number(dat, "tilt", manualTilt)
	ssc.ssc_data_set_number(dat, "rotlim", float(inputDict["rotlim"]))
	ssc.ssc_data_set_number(dat, "gamma", -1 * float(inputDict["gamma"]))
	ssc.ssc_data_set_number(dat, "inv_eff", 0.01 * float(inputDict["inverterEfficiency"]))
	ssc.ssc_data_set_number(dat, "w_stow", float(inputDict["w_stow"]))
	# Complicated optional inputs that we could enable later.
	# ssc.ssc_data_set_array(dat, 'shading_hourly', ...) 	# Hourly beam shading factors
	# ssc.ssc_data_set_matrix(dat, 'shading_mxh', ...) 		# Month x Hour beam shading factors
	# ssc.ssc_data_set_matrix(dat, 'shading_azal', ...) 	# Azimuth x altitude beam shading factors
	# ssc.ssc_data_set_number(dat, 'shading_diff', ...) 	# Diffuse shading factor
	# ssc.ssc_data_set_number(dat, 'enable_user_poa', ...)	# Enable user-defined POA irradiance input = 0 or 1
	# ssc.ssc_data_set_array(dat, 'user_poa', ...) 			# User-defined POA irradiance in W/m2
	# ssc.ssc_data_set_number(dat, 'tilt', 999)
	# ssc.ssc_data_set_number(dat, "t_noct", float(inputDict["t_noct"]))
	# ssc.ssc_data_set_number(dat, "t_ref", float(inputDict["t_ref"]))
	# ssc.ssc_data_set_number(dat, "fd", float(inputDict["fd"]))
	# ssc.ssc_data_set_number(dat, "i_ref", float(inputDict["i_ref"]))
	# ssc.ssc_data_set_number(dat, "poa_cutin", float(inputDict["poa_cutin"]))
	# Run PV system simulation.
	mod = ssc.ssc_module_create("pvwattsv1")
	ssc.ssc_module_exec(mod, dat)
	# Setting options for start time.
	simLengthUnits = inputDict.get("simLengthUnits","")
	simStartDate = inputDict["simStartDate"]
	# Set the timezone to be UTC, it won't affect calculation and display, relative offset handled in pvWatts.html 
	startDateTime = simStartDate + " 00:00:00 UTC"
	# Set aggregation function constants.
	agg = lambda x,y:_aggData(x,y,inputDict["simStartDate"],
		int(inputDict["simLength"]), inputDict["simLengthUnits"], ssc, dat)
	avg = lambda x:sum(x)/len(x)
	# Timestamp output.
	outData = {}
	outData["timeStamps"] = [datetime.datetime.strftime(
		datetime.datetime.strptime(startDateTime[0:19],"%Y-%m-%d %H:%M:%S") + 
		datetime.timedelta(**{simLengthUnits:x}),"%Y-%m-%d %H:%M:%S") + " UTC" for x in range(int(inputDict["simLength"]))]
	# Geodata output.
	outData["city"] = ssc.ssc_data_get_string(dat, "city")
	outData["state"] = ssc.ssc_data_get_string(dat, "state")
	outData["lat"] = ssc.ssc_data_get_number(dat, "lat")
	outData["lon"] = ssc.ssc_data_get_number(dat, "lon")
	outData["elev"] = ssc.ssc_data_get_number(dat, "elev")
	# Weather output.
	outData["climate"] = {}
	outData["climate"]["Plane of Array Irradiance (W/m^2)"] = agg("poa", avg)
	outData["climate"]["Beam Normal Irradiance (W/m^2)"] = agg("dn", avg)
	outData["climate"]["Diffuse Irradiance (W/m^2)"] = agg("df", avg)
	outData["climate"]["Ambient Temperature (F)"] = agg("tamb", avg)
	outData["climate"]["Cell Temperature (F)"] = agg("tcell", avg)
	outData["climate"]["Wind Speed (m/s)"] = agg("wspd", avg)
	# Power generation.
	outData["Consumption"] = {}
	outData["Consumption"]["Power"] = [x for x in agg("ac", avg)]
	outData["Consumption"]["Losses"] = [0 for x in agg("ac", avg)]
	outData["Consumption"]["DG"] = agg("ac", avg)

	#Plotly data sets for power generation graphs
	convertedDateStrings = [datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S %Z") for x in outData["timeStamps"]]
	powerGeneration = go.Scatter(
		x=convertedDateStrings,
		y=outData["Consumption"]["Power"],
		line=dict(
			color=('red')
			),
		name="Power Generated")

	chartInverter = None
	if float(inputDict["inverterSize"]) == 0:
		chartInverter = float(inputDict["systemSize"])
	else:
		chartInverter = float(inputDict["inverterSize"])

	panelsNameplate = go.Scatter(
		x=convertedDateStrings,
		y=[float(inputDict['systemSize'])*1000 for x in range(len(convertedDateStrings))],
		line=dict(
			dash = 'dash',
			color='orange'
			),
		name="Panels Nameplate")
	inverterNameplate = go.Scatter(
		x=convertedDateStrings,
		y=[chartInverter*1000 for x in range(len(convertedDateStrings))],
		line=dict(
			dash = 'dash',
			color='orange'
			),
		name="inverter Nameplate")

	#Set Power generation plotly layout
	powerGenerationLayout = go.Layout(
		width=1000,
		height=375,
		xaxis=dict(
			showgrid=False,
			),
		legend=dict(
			x=0,
			y=1.25,
			orientation="h")
		)
	#Combine all datasets for plotly graph
	powerGenerationData = [powerGeneration, panelsNameplate, inverterNameplate]
	#Example updating go object
	powerGenerationLayout['yaxis'].update(title='Power (W-AC)')
	#fig = go.Figure(data=powerGenerationData, layout=powerGenerationLayout)
	#inlinePlot = plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')
	#outData["plotlyDiv"] = html.escape(json.dumps(inlinePlot, cls=plotly.utils.PlotlyJSONEncoder))

	#Plotly power generation outputs
	outData["powerGenerationData"] = json.dumps(powerGenerationData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["powerGenerationLayout"] = json.dumps(powerGenerationLayout, cls=plotly.utils.PlotlyJSONEncoder)

	#Irradiance plotly data
	poaIrradiance = go.Scatter(
		x=convertedDateStrings,
		y=outData["climate"]["Plane of Array Irradiance (W/m^2)"],
		line=dict(
			color='yellow'
			),
		name="Plane of Array Irradiance (W/m^2)") 
	beamNormalIrradiance = go.Scatter(
		x=convertedDateStrings,
		y=outData["climate"]["Beam Normal Irradiance (W/m^2)"],
		line=dict(
			color='gold'
			),
		name="Beam Normal Irradiance (W/m^2)") 
	diffuseIrradiance = go.Scatter(
		x=convertedDateStrings,
		y=outData["climate"]["Diffuse Irradiance (W/m^2)"],
		line=dict(
			color='lemonchiffon'
			),
		name="Diffuse Irradiance (W/m^2)")
	irradianceData = [poaIrradiance, beamNormalIrradiance, diffuseIrradiance]

	#Set Power generation plotly layout
	irradianceLayout = go.Layout(
		width=1000,
		height=375,
		xaxis=dict(
			showgrid=False,
			),
		yaxis=dict(
			title="Climate Units",
			),
		legend=dict(
			x=0,
			y=1.25,
			orientation="h")
		)
	outData["irradianceData"] = json.dumps(irradianceData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["irradianceLayout"] = json.dumps(irradianceLayout, cls=plotly.utils.PlotlyJSONEncoder)

	#Other Climate Variables plotly data
	ambientTemperature = go.Scatter(
		x=convertedDateStrings,
		y=	outData["climate"]["Ambient Temperature (F)"],
		line=dict(
			color='dimgray'
			),
		name="Ambient Temperature (F)") 
	cellTemperature = go.Scatter(
		x=convertedDateStrings,
		y=outData["climate"]["Cell Temperature (F)"],
		line=dict(
			color='gainsboro'
			),
		name="Cell Temperature (F)") 
	windSpeed = go.Scatter(
		x=convertedDateStrings,
		y=outData["climate"]["Wind Speed (m/s)"],
		line=dict(
			color='darkgray'
			),
		name="Wind Speed (m/s)")
	otherClimateData = [ambientTemperature, cellTemperature, windSpeed]

	#Set Power generation plotly layout
	otherClimateLayout = go.Layout(
		width=1000,
		height=375,
		xaxis=dict(
			showgrid=False,
			),
		yaxis=dict(
			title="Climate Units",
			),
		legend=dict(
			x=0,
			y=1.25,
			orientation="h")
		)
	outData["otherClimateData"] = json.dumps(otherClimateData, cls=plotly.utils.PlotlyJSONEncoder)
	outData["otherClimateLayout"] = json.dumps(otherClimateLayout, cls=plotly.utils.PlotlyJSONEncoder)
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def _aggData(key, aggFun, simStartDate, simLength, simLengthUnits, ssc, dat):
	''' Function to aggregate output if we need something other than hour level. '''
	u = simStartDate
	# pick a common year, ignoring the leap year, it won't affect to calculate the initHour
	d = datetime.datetime(2013, int(u[5:7]),int(u[8:10])) 
	# first day of the year	
	sd = datetime.datetime(2013, 01, 01) 
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

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"simStartDate": "2012-04-01",
		"simLengthUnits": "hours",
		"modelType": modelName,
		"zipCode": "64735",
		"simLength": "100",
		"systemSize":"10",
		"nonInverterEfficiency":"77",
		"trackingMode":"0",
		"azimuth":"180",
		"runTime": "",
		"rotlim":"45.0",
		"gamma":"0.45",
		"inverterEfficiency":"92",
		"tilt":"45",
		"w_stow":"0",
		"inverterSize":"8",
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
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
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
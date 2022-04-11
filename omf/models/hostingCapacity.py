''' Calculate solar photovoltaic system output using PVWatts. '''

import shutil, datetime
from os.path import join as pJoin

# OMF imports
from omf import weather
from omf.solvers import nrelsam2013
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
tooltip = "The hostingCapacity model calculates the kW hosting capacity available at each meter in the provided AMI data."
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	# Copy specific climate data into model directory
	inputDict["climateName"] = weather.zipCodeToClimateName(inputDict["zipCode"])
	shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"), 
		pJoin(modelDir, "climate.tmy2"))
	# Set up SAM data structures.
	ssc = nrelsam2013.SSCAPI()
	dat = ssc.ssc_data_create()
	# Required user inputs.
	ssc.ssc_data_set_string(dat, b'file_name', bytes(modelDir + '/climate.tmy2', 'ascii'))
	ssc.ssc_data_set_number(dat, b'system_size', float(inputDict['systemSize']))
	ssc.ssc_data_set_number(dat, b'derate', 0.01 * float(inputDict['nonInverterEfficiency']))
	ssc.ssc_data_set_number(dat, b'track_mode', float(inputDict['trackingMode']))
	ssc.ssc_data_set_number(dat, b'azimuth', float(inputDict['azimuth']))
	# Advanced inputs with defaults.
	if (inputDict.get("tilt",0) == "-"):
		tilt_eq_lat = 1.0
		manualTilt = 0.0
	else:
		tilt_eq_lat = 0.0
		manualTilt = float(inputDict.get("tilt",0))
	ssc.ssc_data_set_number(dat, b'tilt_eq_lat', tilt_eq_lat)
	ssc.ssc_data_set_number(dat, b'tilt', manualTilt)
	ssc.ssc_data_set_number(dat, b'rotlim', float(inputDict['rotlim']))
	ssc.ssc_data_set_number(dat, b'gamma', -1 * float(inputDict['gamma']))
	ssc.ssc_data_set_number(dat, b'inv_eff', 0.01 * float(inputDict['inverterEfficiency']))
	ssc.ssc_data_set_number(dat, b'w_stow', float(inputDict['w_stow']))
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
	mod = ssc.ssc_module_create(b'pvwattsv1')
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
	outData['city'] = ssc.ssc_data_get_string(dat, b'city').decode()
	outData['state'] = ssc.ssc_data_get_string(dat, b'state').decode()
	outData['lat'] = ssc.ssc_data_get_number(dat, b'lat')
	outData['lon'] = ssc.ssc_data_get_number(dat, b'lon')
	outData['elev'] = ssc.ssc_data_get_number(dat, b'elev')
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
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def runtimeEstimate(modelDir):
	''' Estimated runtime of model in minutes. '''
	return 0.5

def _aggData(key, aggFun, simStartDate, simLength, simLengthUnits, ssc, dat):
	''' Function to aggregate output if we need something other than hour level. '''
	u = simStartDate
	# pick a common year, ignoring the leap year, it won't affect to calculate the initHour
	d = datetime.datetime(2013, int(u[5:7]),int(u[8:10])) 
	# first day of the year	
	sd = datetime.datetime(2013, 1, 1)
	# convert difference of datedelta object to number of hours 
	initHour = int((d-sd).total_seconds()/3600)
	fullData = ssc.ssc_data_get_array(dat, bytes(key, 'ascii'))
	if simLengthUnits == "days":
		multiplier = 24
	else:
		multiplier = 1
	hourData = [fullData[(initHour+i)%8760] for i in range(simLength*multiplier)]
	if simLengthUnits == "minutes":
		pass
	elif simLengthUnits == "hours":
		return hourData
	elif simLengthUnits == "days":
		split = [hourData[x:x+24] for x in range(simLength)]
		return list(map(aggFun, split))

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
		"trackingMode":"2",
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

@neoMetaModel_test_setup
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
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()

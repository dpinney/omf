''' Get power and energy limits from PNNL VirtualBatteries (VBAT) load model.'''

import json, os, shutil, subprocess, platform, math
from os.path import join as pJoin
from jinja2 import Template
import __neoMetaModel__
from __neoMetaModel__ import *
import requests, csv, tempfile
from dateutil.parser import parse as parseDt
import datetime as dt

# Model metadata:
fileName = os.path.basename(__file__)
modelName = fileName[0:fileName.rfind('.')]
tooltip = "Download historical weather data for a given location for use in other models."
hidden = True

# Our HTML template for the interface:
with open(pJoin(__neoMetaModel__._myDir,modelName + ".html"),"r") as file:
	template = Template(file.read())

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	outData = {}
	# Run VBAT code.
	source = inputDict["source"]
	year = inputDict["year"]
	if source == "METAR":
		station = inputDict["stationMETAR"]
		parameter = inputDict["weatherParameterMETAR"]
	elif source == "USCRN":
		station = inputDict["stationUSCRN"]
		parameter = inputDict["weatherParameterUSCRN"]
	verifiedData = []
	errorCount = 0
	#check the source using and use the appropriate function
	if source == "METAR":
		data = pullMETAR(year,station,parameter)
		with open(pJoin(modelDir,"weather.csv"),"w") as file:
			file.write(data)
	elif source == "USCRN":
		data = pullUSCRN(year,station,parameter)
		with open(pJoin(modelDir,"weather.csv"),"w") as file:
			writer = csv.writer(file)
			writer.writerows([[x] for x in data])
	#writing raw data
	if parameter != "metar" and source == "METAR":#raw metar should not be formated as it is already in its own format and difficult to handle
		verifiedData = [999.9]*8760
		firstDT = dt.datetime(int(year),1,1,0)
		with open(pJoin(modelDir,"weather.csv"),"r") as file:
			reader = csv.reader(file)
			for row in reader:
				if row[1] != "valid" and row[2] != "M":
					d = parseDt(row[1])
					deltatime = d - firstDT
					verifiedData[int(math.floor((deltatime.total_seconds())/(60*60)))] = row[2]
		#storing good data to allOutputData.json and weather.csv
		outData["data"] = verifiedData
		with open(pJoin(modelDir,"weather.csv"),"wb") as file:
			writer = csv.writer(file)
			writer.writerows([[x] for x in verifiedData])
	elif source == "USCRN":
		verifiedData = []
		with open(pJoin(modelDir,"weather.csv"),"r") as file:
			reader = csv.reader(file)
			for row in reader:
				verifiedData.append(row[0])	
			outData["data"] = verifiedData
	with open(pJoin(modelDir,"weather.csv"),"wb") as file:
		writer = csv.writer(file)
		writer.writerows([[x] for x in verifiedData])
	#checking how many wrong values there are
	if source == "METAR":
		for each in verifiedData:
			if each == 999.9:
				errorCount += 1
	elif source == "USCRN":
		for each in verifiedData:
			if str(each) == str(-9999.0):
				errorCount += 1
	outData["errorCount"] = errorCount
	outData["stdout"] = "Success"
	return outData

def pullMETAR(year, station, datatype):
	url = ('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=' + station + '&data=' + datatype + '&year1=' + year + 
		'&month1=1&day1=1&year2=' + str(int(year)+1) + '&month2=1&day2=1&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=1&report_type=2')
	r = requests.get(url)
	data = r.text
	return data

def pullUSCRN(year, station, datatype):
	'''	For a given year and weather station, write 8760 hourly weather data (temp, humidity, etc.) to outputPath.
	for list of available stations go to: https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02'''
	if datatype == "T_CALC":
		datatypeID = 9
	elif datatype == "T_HR_AVG":
		datatypeID = 10
	elif datatype == "T_MAX":
		datatypeID = 11
	elif datatype == "T_MIN":
		datatypeID = 12
	elif datatype == "P_CALC":
		datatypeID = 13
	elif datatype == "SOLARAD":
		datatypeID = 14
	elif datatype == "SOLARAD_MAX":
		datatypeID = 16
	elif datatype == "SOLARAD_MIN":
		datatypeID = 18
	elif datatype == "SUR_TEMP":
		datatypeID = 21
	elif datatype == "SUR_TEMP_MAX":
		datatypeID = 23
	elif datatype == "SUR_TEMP_MIN":
		datatypeID = 25
	elif datatype == "RH_HR_AVG":
		datatypeID = 27
	elif datatype == "SOIL_MOISTURE_5":
		datatypeID = 29
	elif datatype == "SOIL_MOISTURE_10":
		datatypeID = 30
	elif datatype == "SOIL_MOISTURE_20":
		datatypeID = 31
	elif datatype == "SOIL_MOISTURE_50":
		datatypeID = 32
	elif datatype == "SOIL_MOISTURE_100":
		datatypeID = 33
	elif datatype == "SOIL_TEMP_5":
		datatypeID = 34
	elif datatype == "SOIL_TEMP_10":
		datatypeID = 35
	elif datatype == "SOIL_TEMP_20":
		datatypeID = 36
	elif datatype == "SOIL_TEMP_50":
		datatypeID = 37
	elif datatype == "SOIL_TEMP_100":
		datatypeID = 38
	else:
		datatypeID = 1
	#need to have handling for stupid inputs #REPLACE WITH A DICTIONARY
	url = 'https://www1.ncdc.noaa.gov/pub/data/uscrn/products/hourly02/' + year + '/CRNH0203-' + year + '-' + station + '.txt'
	r = requests.get(url)
	data = r.text
	matrix = [x.split() for x in data.split('\n')]
	tempData = []
	for i in range(8760):
		tempData.append(matrix[i][datatypeID])
	return tempData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"source":"USCRN",#"source":"METAR", #
		"year":"2017",
		"stationMETAR":"CHO",
		"stationUSCRN":"AK_Barrow_4_ENE",
		"weatherParameterUSCRN":"T_CALC",
		"weatherParameterMETAR":"tmpc",
		"modelType":modelName}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

def _simpleTest():
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
	runForeground(modelLoc, json.load(open(modelLoc + "/allInputData.json")))
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_simpleTest ()
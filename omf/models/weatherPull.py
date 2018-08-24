''' Get power and energy limits from PNNL VirtualBatteries (VBAT) load model.'''
import json, os, shutil, math, requests, csv, __neoMetaModel__
from os.path import join as pJoin
from jinja2 import Template
from __neoMetaModel__ import *
from dateutil.parser import parse as parseDt
import datetime as dt
from omf import weather

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Download historical weather data for a given location for use in other models."
hidden = True

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	outData = {}
	source = inputDict["source"]
	year = inputDict["year"]
	if source == "ASOS":
		station = inputDict["stationASOS"]
		parameter = inputDict["weatherParameterASOS"]
	elif source == "USCRN":
		station = inputDict["stationUSCRN"]
		parameter = inputDict["weatherParameterUSCRN"]
	verifiedData = []
	errorCount = 0
	#check the source using and use the appropriate function
	if source == "ASOS":
		data = weather.pullAsos(year,station,parameter)
		with open(pJoin(modelDir,"weather.csv"),"w") as file:
			file.write(data)
	elif source == "USCRN":
		data = weather.pullUscrn(year,station,parameter)
		with open(pJoin(modelDir,"weather.csv"),"w") as file:
			writer = csv.writer(file)
			writer.writerows([[x] for x in data])
	#writing raw data
	if parameter != "asos" and source == "ASOS":#raw ASOS should not be formated as it is already in its own format and difficult to handle
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
		outData["rawData"] = [float(x) for x in verifiedData]
		with open(pJoin(modelDir,"weather.csv"),"wb") as file:
			writer = csv.writer(file)
			writer.writerows([[x] for x in verifiedData])
	elif source == "USCRN":
		verifiedData = []
		with open(pJoin(modelDir,"weather.csv"),"r") as file:
			reader = csv.reader(file)
			for row in reader:
				verifiedData.append(row[0])	
			outData["rawData"] = [float(x) for x in verifiedData]
	with open(pJoin(modelDir,"weather.csv"),"wb") as file:
		writer = csv.writer(file)
		writer.writerows([[x] for x in verifiedData])
	#checking how many wrong values there are
	if source == "ASOS":
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

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"source":"ASOS", #"source":"USCRN",#
		"year":"2017",
		"stationASOS":"CHO",
		"stationUSCRN":"AK_Barrow_4_ENE",
		"weatherParameterUSCRN":"T_CALC",
		"weatherParameterASOS":"tmpc",
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
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_simpleTest ()
''' Anomaly Detection Model '''

import json, os, tempfile, shutil, datetime, traceback, csv, operator
from os.path import join as pJoin
from pprint import pprint
from jinja2 import Template
import numpy as np

import omf
from omf.models import __neoMetaModel__

# Our HTML template for the interface:
with open(pJoin("./Anomaly.html"),"r") as tempFile:
	template = Template(tempFile.read())
# HACK: this file is reallly old, so add the Anomaly template
import omf.models
from types import SimpleNamespace
o = SimpleNamespace()
o.template = template
setattr(omf.models, 'Anomaly', o)

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __neoMetaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def quickRender(template, modelDir="", absolutePaths=False, datastoreNames={}):
	''' Presence of this function indicates we can run the model quickly via a public interface. '''
	return __neoMetaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames, quickRender=True)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))
	except Exception as e:
		pass
	# Check whether model exist or not
	try:
		if not os.path.isdir(modelDir):
			os.makedirs(modelDir)
			inputDict["created"] = str(datetime.datetime.now())
		with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
			json.dump(inputDict, inputFile, indent = 4)
		startTime = datetime.datetime.now()
		# Inputs.
		MinDetRunTime = int(inputDict.get('MinDetectionRunTime',4))
		devFromAve = 1-float(inputDict.get('MinDeviationFromAverage', 95))/100
		workDir = os.getcwd()
		# Run.
		outData = {}
		computeAMIResults(pJoin(workDir,inputDict.get('fileName','')),  devFromAve,  MinDetRunTime, outData)
		# Save output.
		with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
			json.dump(outData, outFile, indent=4)
		# Update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
	except:
		# If input range wasn't valid delete output, write error to disk.
		cancel(modelDir)
		thisErr = traceback.format_exc()
		print('ERROR IN MODEL', modelDir, thisErr)
		inputDict['stderr'] = thisErr
		with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)

def dateFormatter(dateStr):
	# Try to format a date string to a datetime object.
	toTry = ["%m/%d/%Y %H:%M:%S %p", "%m/%d/%y %H:%M", "%m/%d/%y", "%m/%d/%Y"]
	for dateFormat in toTry:
		try:
			readDateTime = datetime.datetime.strptime(dateStr, dateFormat).isoformat()
			return readDateTime
		except:
			continue
	error = "We don't have a test case for our date: "+dateStr+" :("
	print(error)
	return error

def getAMIData(inCSV):
	# This gets the data and returns a sorted array of data by Sub--Meter--Time
	subStationData = []
	with open(inCSV, newline='') as amiFile:
			amiReader = csv.DictReader(amiFile, delimiter=',')
			for row in amiReader:
				subStation = row['SUBSTATION']
				meterName = row['METER_ID']
				readDateTime = dateFormatter(row['READ_DTM'])
				kWh = row['READ_VALUE']
				subStationData.append([subStation, meterName, readDateTime, kWh])
	subData = sorted(subStationData, key=operator.itemgetter(0,1,2), reverse=False)
	return subData

def computeAMIResults(inCSV, devFromAve,  MinDetRunTime, outData):
	# Take in AMI data and compute anamolies.
	amiArr = getAMIData(inCSV)
	tempDict = {}
	# Put into dict.
	for row in amiArr:
			meterName = row[1]
			energyCons = row[3]
			date = row[2]
			if tempDict.get(meterName,'') == '':
					tempDict[meterName] = {'energyCons': [energyCons], 'dates' : [date]}
			else:
					tempDict[meterName]['energyCons'].append(energyCons)
					tempDict[meterName]['dates'].append(date)
	numMeters = 1000
	# Print input.
	# toShow = 60
	# print "\nTemp dict:"
	# for i,meterID in enumerate(tempDict.keys()):
	# 	print "\nmeterID:", meterID
	# 	for subkey in tempDict[meterID]: print "(%s: %s values)"%(subkey, len(tempDict[meterID][subkey])), tempDict[meterID][subkey]
	# 	if i>=(numMeters-1): break
	output, startIndex = [], 0
	powerArr = []
	for i,key in enumerate(tempDict.keys()):
		meterid = key
		powerArr.append([])
		for j in range(len(tempDict[key]['dates'])-1):
			dateTimes = tempDict[key]['dates'][j+1]
			power = float(tempDict[key]['energyCons'][j+1])-float(tempDict[key]['energyCons'][j])
			output.append([meterid, dateTimes, power])
			powerArr[i].append(power)
		if i>(numMeters-1): break
	# Compute avg power.
	start = 0
	for powers in powerArr:
		powerAvg = np.mean(powers)
		for i in range(0,len(powers)):
			output[start+i].append(round(powerAvg,3))
		start+=(i+1)
	# Print results.
	# print "\Results of getting energy and avg energy:"
	# for i, row in enumerate(output):
	# 	print row
	# 	if i>toShow: break
	# Get energy deviation.
	tempDict['outputDeviateds'] = []
	metersToKeep = []
	devValues = []
	index, endPoint = -1, 0
	#print "Anamoly results:"
	for i,row in enumerate(output):
		coDevFromAve = 1-devFromAve
		if (row[2])<=(devFromAve*row[3]) or (row[2])>=((1+coDevFromAve)*row[3]):
			if index == -1:
				index = i
				devValues = [row[2]]
				average = [row[3]]*len(devValues)
				# print "---------------------------------"
			else:
				endPoint = i
				devValues.append(row[2])
			# print "Reading data: Power %s that is less than: %s (index %s) "%(row[2], devFromAve*row[3], i)
			# print "Row %s "%(row)
		else:
			if (index!= -1) and (endPoint-index) >= MinDetRunTime:
				meter = output[index][0]
				time1 = datetime.datetime.strptime(output[index][1], "%Y-%m-%dT%H:%M:%S")
				time2 = datetime.datetime.strptime(output[endPoint][1], "%Y-%m-%dT%H:%M:%S")
				duration = round(abs((time2-time1)).total_seconds()/3600,2)
				dev = [(a-b)*100/b if b else 0 for a,b in zip(devValues,average)] #zero division is handeled by setting the dev=0
				if np.mean(dev) == 0:
					deviation = "Zero Demand"
				elif np.mean(dev)<0:
					deviation = round(min(dev),2)
				else:
					deviation = round(max(dev),2)
				#print devValues
				tempDict['outputDeviateds'].append([meter,str(time1),duration,str(deviation)])
				metersToKeep.append(meter)
				#print "FOUND %s consecutive values at index, endpoint: (%s,%s) for %s duration (%s)"%(endPoint-index+1, index, endPoint, duration, devValues)
				#print "Deviation is:", abs(deviation), "\n"
			index = -1
	# Send back relevant outputs.
	for meter in tempDict:
		pass
	outData['outputDeviateds'] = tempDict['outputDeviateds']
	outData['outputDeviateds'] = sorted(outData['outputDeviateds'], key=operator.itemgetter(0))
	# Return only those meters energy/dates.
	outData['anomalyMeters'] = {}
	for row in output:
		meterID = row[0]
		if meterID in metersToKeep:
			if outData['anomalyMeters'].get(meterID,'') == '':
				outData['anomalyMeters'][meterID] = {'energy':[], 'time':[], 'avg':[row[3]]}
				startDate = row[1]
			outData['anomalyMeters'][meterID]['time'].append(row[1])
			outData['anomalyMeters'][meterID]['energy'].append(row[2])

def _tests():
	# Variables
	workDir = pJoin(__neoMetaModel__._omfDir,"data","Model")
	inData = {"simStartDate": "2012-04-01",
		"simLengthUnits": "hours",
		"modelType": "Anomaly",
		"simLength": "100",
		"runTime": "",
		"MinDetectionRunTime":"4",
		"MinDeviationFromAverage":"95",
		"fileName": "Input - synthetic AMI measurements.csv"}
	modelLoc = pJoin(workDir,"admin","Anomaly Detection")
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Run the model and show the input only.
	# renderAndShow(template)
	# Run the model and show the output.
	run(modelLoc, inData)
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()

#Hourly Day Of Week Forecasting
# This code using an hourly day of week forecasting technique that linearizes the relationship between temperature and demand for the 4 previous
# days same days of the week at the same hour. Take the 4 mondays at 14:00 to predict the next based on the forecasted temperature.

#model specific imports
import csv,math
import numpy as np
import matplotlib.pyplot as plt
import  __neoMetaModel__, json
from __neoMetaModel__ import *
from omf import loadForecast

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Download historical weather data for a given location for use in other models."
hidden = True

def work(modelDir, inputDict):
	''' Run the model in its directory.'''
	outData = {}
	rawData = []
	forecasted = []
	actual = []
	with open(pJoin(modelDir,"demandTemp.csv"),"w") as demandTempFile:
		demandTempFile.write(inputDict['demandTemp'].replace('\r',''))
	try:
		with open(pJoin(modelDir,"demandTemp.csv")) as inFile:
			reader = csv.reader(inFile)
			for row in reader:
				rawData.append(row)
	except:
		errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href = 'https://github.com/dpinney/omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>\nOMF Wiki storagePeakShave - Demand File CSV Format</a>"
		raise Exception(errorMessage)
	rawData = list(np.float_(rawData)) #converts all data from float to string
	(forecasted, MAE) = loadForecast.pullHourlyDayOfWeekForecast(rawData,(inputDict["upBound"]),float(inputDict["lowBound"]))
	for x in range(len(rawData)):
		actual.append(float(rawData[x][0]))
	outData["actual"] = actual
	outData["forecasted"] = forecasted
	outData["MAE"] = MAE
	return outData

# def pullHourlyDayOfWeekForecast(rawData,upBound,lowBound):	#pullHourlyDayOfWeekForecast(rawData,inputDict["upBound"],inputDict["lowBound"])
# 	forecasted = []
# 	actual = []
# 	for w in range(8760):
# 		# need to start at 4 weeks+1 hour to get enough data to train so 4*7*24 = 672, the +1 is not necessary due to indexing starting at 0
# 		actual.append((rawData[w][0]))
# 		if w>=672:
# 			x = np.array([rawData[w-168][1],rawData[w-336][1],rawData[w-504][1],rawData[w-672][1]]) #training temp
# 			y = np.array([rawData[w-168][0],rawData[w-336][0],rawData[w-504][0],rawData[w-672][0]]) #training demand
# 			z = np.polyfit(x, y, 1)
# 			p = np.poly1d(z)
# 			forecasted.append(float((p(rawData[w][1]))))
# 		else:
# 			forecasted.append(None)
# 	for i in range(len(forecasted)):
# 		if forecasted[i]>float(upBound):
# 			forecasted[i] = None
# 		elif forecasted[i] <float(lowBound):
# 			forecasted[i] = None
# 	MAE = 0		#Mean Average Error calculation
# 	for i in range(len(forecasted)):
# 		if forecasted[i]!=None:
# 			MAE = MAE + abs(forecasted[i]-actual[i])
# 	MAE = math.trunc(MAE/len(forecasted)) 
# 	return (forecasted,MAE)


def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"demandTemp": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","loadForecastDefault.csv")).read(),
		"lowBound":500,
		"upBound":3550,
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
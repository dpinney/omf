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
	for x in range(len(rawData)):
		actual.append(float(rawData[x][0]))
	minInput = min(actual)*0.5
	maxInput = max(actual)*1.5
	# (forecasted, MAE) = loadForecast.pullHourlyDayOfWeekForecast(rawData,maxInput,minInput) #uncomment to use a 50% of min max training set limits
	(forecasted, MAE) = loadForecast.pullHourlyDayOfWeekForecast(rawData,(inputDict["upBound"]),float(inputDict["lowBound"])) #uses a user entered limit for min/max of results
	outData["startDate"] = inputDict["simStartDate"]
	outData["actual"] = actual
	outData["forecasted"] = forecasted
	outData["MAE"] = MAE
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user": "admin",
		"demandTemp": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","loadForecastDefault.csv")).read(),
		"lowBound":500,
		"upBound":3550,
		"simStartDate": "2012-04-01",
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
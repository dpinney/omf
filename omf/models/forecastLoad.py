import csv, math
import numpy as np
import matplotlib.pyplot as plt
import __neoMetaModel__, json
from __neoMetaModel__ import *
from omf import loadForecast

# Model metadata:
modelName, template = metadata(__file__)
tooltip = ("Forecasts hourly load day-ahead using multiple methods")
hidden = False


def work(modelDir, inputDict):
	""" Run the model in its directory."""
	outData = {}
	rawData = []
	forecasted = []
	actual = []
	with open(pJoin(modelDir, "demandTemp.csv"), "w") as demandTempFile:
		demandTempFile.write(inputDict["demandTemp"].replace("\r", ""))
	try:
		with open(pJoin(modelDir, "demandTemp.csv")) as inFile:
			reader = csv.reader(inFile)
			for row in reader:
				rawData.append(row)
	except:
		errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href = 'https://github.com/dpinney/omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>\nOMF Wiki storagePeakShave - Demand File CSV Format</a>"
		raise Exception(errorMessage)
	for i in range(len(rawData)):
		rawData[i] = [a if a else 0 for a in rawData[i]]
	rawData = list(np.float_(rawData))  # converts all data from float to string
	for x in range(len(rawData)):
		actual.append(float(rawData[x][0]))
	(forecasted, MAE) = loadForecast.rollingDylanForecast(
		rawData, float(inputDict["upBound"]), float(inputDict["lowBound"])
	)

	# parse json params
	try:
		params = json.loads(inputDict.get("katSpec", "{}"))
	except ValueError:
		params = {}

	pred_demand = loadForecast.nextDayPeakKatrinaForecast(
		rawData, inputDict["simStartDate"], modelDir, params
	)
	pred_demand = np.transpose(np.array(pred_demand)).tolist()

	# zucc it up
	prophet_partitions = int(inputDict.get("prophet", 0))
	if prophet_partitions > 1:
		prophet, prophet_low, prophet_high = loadForecast.prophetForecast(
			rawData, inputDict["simStartDate"], modelDir, inputDict["prophet"]
		)
	outData["startDate"] = inputDict["simStartDate"]
	outData["actual"] = actual
	outData["forecasted"] = forecasted
	outData["MAE"] = MAE
	outData["peakDemand"] = pred_demand
	if prophet_partitions > 1:
		outData["prophet"] = prophet
		outData["prophetLow"] = prophet_low
		outData["prophetHigh"] = prophet_high
	return outData


def new(modelDir):
	""" Create a new instance of this model. Returns true on success, false on failure. """
	defaultInputs = {
		"user": "admin",
		"demandTemp": open(
			pJoin(
				__neoMetaModel__._omfDir,
				"static",
				"testFiles",
				"ERCOT_south_shortened.csv",
			)
		).read(),
		"fileName": "ERCOT_south_shortened.csv",
		"lowBound": 500,
		"upBound": 3550,
		"simStartDate": "2002-01-01",
		"modelType": modelName,
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode


def _simpleTest():
	# Location
	modelLoc = pJoin(
		__neoMetaModel__._omfDir,
		"data",
		"Model",
		"admin",
		"Automated Testing of " + modelName,
	)
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


if __name__ == "__main__":
	_simpleTest()

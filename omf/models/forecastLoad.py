import csv, math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import __neoMetaModel__, json
from __neoMetaModel__ import *
from omf import loadForecast

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Forecasts hourly load day-ahead using multiple methods"
hidden = False


def work(modelDir, inputDict):
	""" Run the model in its directory."""
	outData = {}
	rawData = []
	actual = []

	# write input file to modelDir sans carriage returns
	with open(pJoin(modelDir, "demandTemp.csv"), "w") as demandTempFile:
		demandTempFile.write(inputDict["demandTemp"].replace("\r", ""))

		# read it in as a list of lists
	try:
		with open(pJoin(modelDir, "demandTemp.csv")) as inFile:
			df = pd.read_csv(inFile, header=None)
			df.columns = ["load", "tempc"]
			df["dates"] = pd.date_range(
				start=inputDict["simStartDate"], freq="H", periods=df.shape[0]
			)
			print df.shape[0]
	except ZeroDivisionError:
		errorMessage = "CSV file is incorrect format. Please see valid format definition at <a target='_blank' href = 'https://github.com/dpinney/omf/wiki/Models-~-storagePeakShave#demand-file-csv-format'>\nOMF Wiki storagePeakShave - Demand File CSV Format</a>"
		raise Exception(errorMessage)

		# neural net time
	all_X = loadForecast.makeUsefulDf(df)
	all_y = df["load"]
	all_X.to_csv(pJoin(modelDir, "usefulDf.csv"))
	rawData = df[["load", "tempc"]].fillna(0).values.tolist()
	del df

	nn_pred, nn_accuracy = loadForecast.neural_net_predictions(all_X, all_y)
	while len(nn_pred) < len(rawData):
		nn_pred.insert(0, None)

	"""
	# None -> 0, float-> string
	for i in range(len(rawData)):
		rawData[i] = [a if a else 0 for a in rawData[i]]
	rawData = list(np.float_(rawData))
	"""

	# populate actual list
	for x in range(len(rawData)):
		actual.append(float(rawData[x][0]))

	(forecasted, MAPE) = loadForecast.rollingDylanForecast(
		rawData, float(inputDict["upBound"]), float(inputDict["lowBound"])
	)

	(exp, exp_MAPE) = loadForecast.exponentiallySmoothedForecast(
		rawData, float(inputDict["alpha"]), float(inputDict["beta"])
	)

	# parse json params for nextDayPeakKatrina
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

		# write our outData
	outData["startDate"] = inputDict["simStartDate"]
	outData["actual"] = actual
	outData["forecasted"] = forecasted
	outData["doubleExp"] = exp
	outData["neuralNet"] = nn_pred
	outData["MAPE"] = "%0.2f%%" % (MAPE*100)
	outData["MAPE_exp"] = "%0.2f%%" % (exp_MAPE*100)
	outData["MAPE_nn"] = "%0.2f%%" % nn_accuracy["test"]
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
		"rollingWindow": 4,
		"alpha": 0.95,
		"beta": 0.05,
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

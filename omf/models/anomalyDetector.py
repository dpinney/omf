""" Calculate the costs and benefits of energy storage from a distribution utility perspective. """

import os, sys, shutil, csv, StringIO
import omf.anomalyDetection
import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta
from os.path import isdir, join as pJoin
from numpy import npv
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# Model metadata:
modelName, template = metadata(__file__)
tooltip = (
	"The storagePeakShave model calculates the value of a distribution utility "
	"deploying energy storage based on three possible battery dispatch strategies."
)


def work(modelDir, inputDict):
	""" Model processing done here. """
	from scipy.stats import t

	cached_file_name = "input_data_{}.csv".format(inputDict["confidence"])
	cached_file_path = pJoin(modelDir, cached_file_name)

	# try to get our cached input
	try:
		with open(cached_file_path, "r") as f:
			cached_str = f.read()
	except IOError:
		cached_str = ""

	confidence = float(inputDict["confidence"]) if inputDict.get("confidence") else 0.99
	if confidence >= 1:
		raise Exception(
			"Value for Confidence Level Out of Bounds (must be less than 1)"
		)

		# do we have a cached forecast?
	cached = (
		"forecasted_{}.csv".format(confidence)
		if cached_str == inputDict["file"]
		else None
	)

	with open(cached_file_path, "w") as f:
		f.write(inputDict["file"])

	out = {}

	# load our csv to df
	f = StringIO.StringIO(inputDict["file"])
	df = pd.read_csv(f)

	# try to use user input to remap column
	df = df.rename(columns={inputDict["yLabel"]: "y"})
	if "y" not in df.columns:
		df = df.rename(columns={df.columns[0]: "y"})

		# add our boy for prophet
	df["ds"] = pd.date_range(
		start=inputDict["startDate"], freq="H", periods=df.shape[0]
	)

	prophet_df = omf.anomalyDetection.prophet(
		df[["ds", "y"]], modelDir, confidence=confidence, cached=cached
	)

	elliptic_df = omf.anomalyDetection.elliptic_envelope(df, modelDir)

	peak_time, peak_demand, act_time, act_demand = omf.loadForecast.nextDayPeakKatrinaForecast(
		df.values, inputDict["startDate"], modelDir, {}, returnActuals=True
	)

	diff = [p - a for p, a in zip(peak_demand, act_demand)]
	diff = np.asarray(diff)
	alpha = 1 - confidence
	twosigma = t.ppf(alpha / 2, len(diff)) * np.std(diff)
	diff = np.abs(diff)

	diff = diff > twosigma

	katrina_outliers = [
		(time, demand) if out_bool else None
		for time, out_bool, demand in zip(act_time, diff, act_demand)
	]
	katrina_outliers = [a for a in katrina_outliers if a]

	out["y"] = list(prophet_df.y.values)
	out["yhat"] = list(prophet_df.yhat.values)
	out["yhat_upper"] = list(prophet_df.yhat_upper.values)
	out["yhat_lower"] = list(prophet_df.yhat_lower.values)
	out["prophet_outlier"] = list(prophet_df.outlier.values.astype(int))
	if elliptic_df:
		out["elliptic_outlier"] = list(elliptic_df.outlier.astype(int))
	if True:
		out["pred_demand"] = peak_demand
		out["peak_time"] = act_time
		out["act_demand"] = act_demand
		out["katrina_outlier"] = katrina_outliers
	out["startDate"] = inputDict["startDate"]
	return out


def new(modelDir):
	""" Create a new instance of this model. Returns true on success, false on failure. """
	defaultInputs = {
		"created": "2015-06-12 17:20:39.308239",
		"modelType": modelName,
		"file": open(
			pJoin(
				__neoMetaModel__._omfDir,
				"static",
				"testFiles",
				"ERCOT_south_shortened.csv",
			)
		).read(),
		"fileName": "ERCOT_south_shortened.csv",
		"confidence": "0.99",
		"startDate": "2002-01-01",
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)


def _tests():
	modelLoc = pJoin(
		__neoMetaModel__._omfDir,
		"data",
		"Model",
		"admin",
		"Automated Testing of " + modelName,
	)
	# Blow away old test results if necessary.
	if isdir(modelLoc):
		shutil.rmtree(modelLoc)
	new(modelLoc)  # Create New.
	renderAndShow(modelLoc)  # Pre-run.
	runForeground(modelLoc)  # Run the model.
	renderAndShow(modelLoc)  # Show the output.


if __name__ == "__main__":
	_tests()

"""
outDic {
	startdate: str
	stdout: "Success"
	batteryDischargekWMax: float
	batteryDischargekw: [8760] float
	monthlyDemandRed: [12] float
	ps: [12] float
	demandAfterBattery: [8760] float
	SPP: float
	kwhtoRecharge [12] float
	LCOE: float
	batteryLife: float
	cumulativeCashflow: [12] float
	batterySoc: [8760] float
	demand: [8760] float
	benefitMonthly: [12] float
	netCashflow: [12] float
	costtoRecharge: [12] float
	months: [12] (strings)
	monthlyDemand: [12] float
	cycleEquivalents: float
	stderr: ""
	NPV: float
	benefitNet: 12
}

# insert into work()
	# ------------------------ DEBUGGING TOOLS ----------------------- #
	# import matplotlib.pyplot as plt 
	# dcThroughTheMonth = [[t for t in iter(dc) if t['month']<=x] for x in range(12)]
	# hoursThroughTheMonth = [len(dcThroughTheMonth[month]) for month in range(12)]
	# # Output some matplotlib results as well.
	# plt.plot([t['power'] for t in dc])
	# plt.plot([t['netpower'] for t in dc])
	# plt.plot([t['battSoC'] for t in dc])
	# for month in range(12):
	#   plt.axvline(hoursThroughTheMonth[month])
	# plt.savefig(pJoin(modelDir,"plot.png"))

"""

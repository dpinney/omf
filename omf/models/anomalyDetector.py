""" Anomaly detection. """
import os, sys, shutil, csv, StringIO, hashlib
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
tooltip = ('Detect anomalies in meter data.')
hidden = True

def work(modelDir, inputDict):
	""" Model processing done here. """

	cached_file_name = "input_data_{}.csv".format(inputDict["confidence"])
	cached_file_path = pJoin(modelDir, cached_file_name)

	# try to get our cached input
	try:
		with open(cached_file_path, "r") as f:
			cached_hash = f.read()
	except IOError:
		cached_hash = ""

	confidence = float(inputDict["confidence"]) if inputDict.get("confidence") else 0.99
	if confidence >= 1:
		raise Exception(
			"Value for Confidence Level Out of Bounds (must be less than 1)"
		)

		# do we have a cached forecast?
	input_hasher = hashlib.md5()
	input_hasher.update(inputDict["file"].encode())
	cached = (
		"forecasted_{}.csv".format(confidence)
		if cached_hash == input_hasher.hexdigest()
		else None
	)

	with open(cached_file_path, "w") as f:
		f.write(input_hasher.hexdigest())

	out = {}

	# load our csv to df
	f = StringIO.StringIO(inputDict["file"])
	header = csv.Sniffer().has_header(f.read(1024))
	header = 0 if header else None
	f.seek(0)
	df = pd.read_csv(f, header = header)

	if inputDict.get("demandTempBool"):
		nn_bool, nn_actual, nn_pred, nn_lower, nn_upper = omf.anomalyDetection.t_test(df, modelDir, inputDict["startDate"], confidence)
		pk_bool, pk_actual, pk_time = omf.anomalyDetection.t_test(df, modelDir, inputDict["startDate"], confidence, model="nextDayPeakKatrina")
		katrina_outliers = [
			(time, demand) if out_bool else None
			for time, out_bool, demand in zip(pk_time, pk_bool, pk_actual)
		]
		katrina_outliers = [a for a in katrina_outliers if a]

	# try to use user input to remap columns for prophet
	df = df.rename(columns={inputDict.get("yLabel",""): "y"})
	if "y" not in df.columns:
		df = df.rename(columns={df.columns[0]: "y"})

		# add our boy for prophet
	df["ds"] = pd.date_range(
		start=inputDict["startDate"], freq="H", periods=df.shape[0]
	)

	prophet_df = omf.anomalyDetection.prophet(
		df[["ds", "y"]], modelDir, confidence=confidence, cached=cached
	)

	elliptic_df = omf.anomalyDetection.elliptic_envelope(df, modelDir, float(inputDict["norm_confidence"]))

	out["y"] = list(prophet_df.y.values)
	out["yhat"] = list(prophet_df.yhat.values)
	out["yhat_upper"] = list(prophet_df.yhat_upper.values)
	out["yhat_lower"] = list(prophet_df.yhat_lower.values)
	out["prophet_outlier"] = list(prophet_df.outlier.values.astype(int))
	if elliptic_df is not None:
		out["elliptic_outlier"] = list(elliptic_df.outlier.astype(int))
	if inputDict.get("demandTempBool"):
		out["nn_outlier"] = list(nn_bool.astype(int))
		out["nn_actual"] = list(nn_actual)
		out["nn_pred"] = list(nn_pred)
		out["nn_lower"] = list(nn_lower)
		out["nn_upper"] = list(nn_upper)
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
		"norm_confidence": "0.90",
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
	runForeground(modelLoc)  # Run the model.
	renderAndShow(modelLoc)  # Show the output.


if __name__ == "__main__":
	_tests()

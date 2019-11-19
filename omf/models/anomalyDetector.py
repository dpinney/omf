""" Anomaly detection. """
import os, sys, shutil, csv, StringIO, hashlib, plotly
import omf.anomalyDetection
import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta
from os.path import isdir, join as pJoin
from numpy import npv
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
import matplotlib.pyplot as plt
from sklearn.neighbors import LocalOutlierFactor
from sklearn.ensemble import IsolationForest
import plotly.graph_objs as go


# Model metadata:
modelName, template = metadata(__file__)
tooltip = ('Detect anomalies in meter data.')
hidden = False

def workProphet(modelDir, inputDict):
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
		# nn_bool, nn_actual, nn_pred, nn_lower, nn_upper = omf.anomalyDetection.t_test(df, modelDir, inputDict["startDate"], confidence)
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
		"""
		out["nn_outlier"] = list(nn_bool.astype(int))
		out["nn_actual"] = list(nn_actual)
		out["nn_pred"] = list(nn_pred)
		out["nn_lower"] = list(nn_lower)
		out["nn_upper"] = list(nn_upper)
		"""
		out["katrina_outlier"] = katrina_outliers
	out["startDate"] = inputDict["startDate"]
	return out

def workLof(modelDir, inputDict):
	
	neighbors = int(inputDict['neighbors'])
	contamination = float(inputDict['contaminationLof'])
	if contamination == 0:
		contamination = 'auto'
	clf = LocalOutlierFactor(n_neighbors=neighbors, contamination=contamination)
	
	# load our csv to df
	f = StringIO.StringIO(inputDict["file"])
	df = pd.read_csv(f)
	datapoints = df.to_numpy()

	maxVals = np.max(datapoints, axis=0)
	maxVals = np.tile( maxVals, (datapoints.shape[0],1) )
	normalizedDatapoints = np.divide(datapoints,maxVals)

	labels = clf.fit_predict(normalizedDatapoints)
	scores = clf.negative_outlier_factor_

	plotData = []
	x = np.arange(0,datapoints.shape[0])
	data = go.Scatter( x=x, y=datapoints[:,0], name='data', mode='lines+markers' ) 
	plotData.append(data)
	outliers = go.Scatter( x=x[labels!=1], y=datapoints[labels!=1, 0], name='outliers', 
		mode='markers' ) 
	plotData.append(outliers)

	return plotData

def workIso(modelDir, inputDict):

	samples = float(inputDict['samples'])
	estimators = int(inputDict['estimators'])
	contamination = float(inputDict['contaminationIso'])
	if contamination == 0:
		contamination = 'auto'
	clf =  IsolationForest(max_samples=samples,	n_estimators=estimators, 
		contamination=contamination, behaviour='new', random_state=42)

	# load our csv to df
	f = StringIO.StringIO(inputDict["file"])
	df = pd.read_csv(f)
	datapoints = df.to_numpy()

	maxVals = np.max(datapoints, axis=0)
	maxVals = np.tile( maxVals, (datapoints.shape[0],1) )
	normalizedDatapoints = np.divide(datapoints,maxVals)

	labels = clf.fit_predict(normalizedDatapoints)
	scores = clf.score_samples(normalizedDatapoints)

	plotData = []
	x = np.arange(0,datapoints.shape[0])
	data = go.Scatter( x=x, y=datapoints[:,0], name='data', mode='lines+markers' ) 
	plotData.append(data)
	outliers = go.Scatter( x=x[labels!=1], y=datapoints[labels!=1, 0], name='outliers',
		mode='markers' ) 
	plotData.append(outliers)

	return plotData

def workSAX(modelDir, inputDict):
	pass


def work(modelDir, inputDict):
	""" Model processing done here. """

	"""if inputDict['algorithm'] == 'prophet':
		outData = workProphet(modelDir, inputDict)
	elif inputDict['algorithm'] == 'lof':
		outData = workLOF(modelDir, inputDict)
	elif inputDict['algorithm'] == 'isoForest':
		outData = workIsoForest(modelDir, inputDict)
	elif inputDict['algorithm'] == 'sax':
		outData = workSAX(modelDir, inputDict)
	"""

	outData = workProphet(modelDir, inputDict)
	plotData = workLof(modelDir, inputDict)
	outData['plotLof'] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	plotData = workIso(modelDir, inputDict)
	outData['plotIso'] = json.dumps(plotData, cls=plotly.utils.PlotlyJSONEncoder)
	
	return outData


def new(modelDir):
	""" Create a new instance of this model. Returns true on success, false on failure. """
	fName = "ERCOT_south_shortened.csv";
	defaultInputs = {
		"created": "2015-06-12 17:20:39.308239",
		"modelType": modelName,
		"file": open(
			pJoin(
				__neoMetaModel__._omfDir,
				"static",
				"testFiles",
				fName,
			)
		).read(),
		"fileName": fName,
		"confidence": "0.99",
		"norm_confidence": "0.90",
		"startDate": "2002-01-01",
		"contaminationLof": "0",
		"contaminationIso": "0",
		"neighbors": "20",
		"estimators": "100",
		"samples":"0.1"
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

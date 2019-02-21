''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import os, sys, shutil, csv, StringIO
import omf.anomalyDetection
import pandas as pd
from datetime import datetime as dt, timedelta
from os.path import isdir, join as pJoin
from numpy import npv
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# Model metadata:
modelName, template = metadata(__file__)
tooltip = ("The storagePeakShave model calculates the value of a distribution utility " 
	"deploying energy storage based on three possible battery dispatch strategies.")

def work(modelDir, inputDict):
	''' Model processing done here. '''
	out = {}  # See bottom of file for out's structure
	f = StringIO.StringIO(inputDict['file'])
	df = pd.read_csv(f)
	df.columns = ['y']
	df['ds'] = pd.date_range(start = inputDict['startDate'], freq = "H", periods = df.shape[0])
	forecast = omf.anomalyDetection.detect_outliers(df, modelDir)	
	out['y'] = list(forecast.y.values)
	out['yhat'] = list(forecast.yhat.values)
	out['yhat_upper'] = list(forecast.yhat_upper.values)
	out['yhat_lower'] = list(forecast.yhat_lower.values)
	out['outlier'] = list(forecast.outlier.values.astype(int))
	out['startDate'] = inputDict['startDate']
	return out

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		'created': '2015-06-12 17:20:39.308239',
		'modelType': modelName,
		'file': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','ERCOT_south_shortened_no_temp.csv')).read(),
		'fileName': 'ERCOT_south_shortened_no_weather.csv',
		'startDate': '2002-01-01',
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	modelLoc = pJoin(__neoMetaModel__._omfDir,'data','Model','admin','Automated Testing of ' + modelName)
	# Blow away old test results if necessary.
	if isdir(modelLoc):
		shutil.rmtree(modelLoc)	
	new(modelLoc)  # Create New.
	renderAndShow(modelLoc)  # Pre-run.
	runForeground(modelLoc)  # Run the model.
	renderAndShow(modelLoc)  # Show the output.

if __name__ == '__main__':
	_tests()

'''
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

'''

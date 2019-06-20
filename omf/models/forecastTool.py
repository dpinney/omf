''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import os, sys, shutil, csv
from datetime import datetime as dt, timedelta
from os.path import isdir, join as pJoin
import pandas as pd
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf import loadForecast as lf
import numpy as np
from scipy.stats import norm
import re

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "This model predicts whether the following day will be a monthly peak."
hidden = True

def peak_likelihood(hist=None, tomorrow=None, tomorrow_std=None, two_day=None, two_day_std=None, three_day=None, three_day_std=None):
    A = norm(tomorrow, tomorrow_std).cdf(hist)
    B = norm(0, 1).cdf(-(tomorrow - two_day) / ((tomorrow_std**2 + two_day_std**2)**.5))
    C = norm(0, 1).cdf(-(tomorrow - three_day) / ((tomorrow_std**2 + three_day_std**2)**.5))
    return round((1 - A)*(1 - B)*(1 - C)*100, 2)

def highest_peak_this_month(df, predicted_day):
	y = predicted_day.year
	m = predicted_day.month
	d = predicted_day.day
	return_v = df[(df['year'] == y) & (df['month'] == m) & (df['day'] != d)]['load'].max()
	return 0 if np.isnan(return_v) else return_v

def work(modelDir, ind):
	''' Model processing done here. '''
	epochs = int(ind['epochs'])
	o = {}  # See bottom of file for out's structure

	# # serialize model to JSON
	# model_json = model.to_json()
	# with open("model.json", "w") as json_file:
	#     json_file.write(model_json)
	# # serialize weights to HDF5
	# model.save_weights("model.h5")
	# print("Saved model to disk")
	 
	# # later...
	# if not (ind.get('model') is None):
	# 	# load json and create model
	# 	json_file = open('model.json', 'r')
	# 	loaded_model_json = json_file.read()
	# 	json_file.close()
	# 	loaded_model = model_from_json(loaded_model_json)
	# # load weights into new model
	# loaded_model.load_weights("model.h5")
	# print("Loaded model from disk")

	try:
	 	with open(pJoin(modelDir, 'hist.csv'), 'w') as f:
	 		f.write(ind['histCurve'].replace('\r', ''))
		df = pd.read_csv(pJoin(modelDir, 'hist.csv'))
		assert df.shape[0] >= 26280 # must be longer than 3 years
	 	if 'dates' not in df.columns:
		 	df['dates'] = df.apply(
				lambda x: dt(
					int(x['year']), 
					int(x['month']), 
					int(x['day']), 
					int(x['hour'])), 
				axis=1
			)
	except:
		raise Exception("Load CSV file is incorrect format.")

	try:
		weather = [float(i) for i in ind['tempCurve'].split('\n')]
		assert len(weather) == 72, "weather csv in wrong format"
	except:
		raise Exception(ind['tempCurve'])

	# ---------------------- MAKE PREDICTIONS ------------------------------- #
	df, tomorrow = lf.add_day(df, weather[:24])
	all_X = lf.makeUsefulDf(df)
	all_y = df['load']

	#load prediction
	tomorrow_load, model, tomorrow_accuracy = lf.neural_net_next_day(all_X, all_y, epochs=epochs)
	# tomorrow_load = [13044.3369140625, 12692.4453125, 11894.0712890625, 13391.0185546875, 13378.373046875, 14098.5048828125, 14984.5, 15746.6845703125, 14677.6064453125, 14869.6953125, 14324.302734375, 13727.908203125, 13537.51171875, 12671.90234375, 13390.9970703125, 12111.166015625, 13539.05078125, 15298.7939453125, 14620.8369140625, 15381.9404296875, 15116.42578125, 13652.3974609375, 13599.5986328125, 12882.5185546875]
	# tomorrow_accuracy = {'test': 4, 'train': 3}
	o['tomorrow_load'] = tomorrow_load
	o['startDate'] = "{}-{}-{}".format(tomorrow.year, tomorrow.month, tomorrow.day)
	o['startDate_s'] = tomorrow.strftime("%A, %B %-m, %Y")
	
	# second day
	df, second_day = lf.add_day(df, weather[24:48])
	if second_day.month == tomorrow.month:
		all_X = lf.makeUsefulDf(df, hours_prior=48, noise=5)
		all_y = df['load']
		two_day_predicted_load, two_day_model, two_day_load_accuracy = lf.neural_net_next_day(all_X, all_y, epochs=epochs, hours_prior=48)
		two_day_peak = max(two_day_predicted_load)

		# third day
		df, third_day = lf.add_day(df, weather[48:72])
		if third_day.month == tomorrow.month:
			all_X = lf.makeUsefulDf(df, hours_prior=72, noise=15)
			all_y = df['load']
			three_day_predicted_load, three_day_model, three_day_load_accuracy = lf.neural_net_next_day(all_X, all_y, epochs=epochs, hours_prior=72)
			three_day_peak = max(three_day_predicted_load)
		else:
			three_day_peak = 0
			three_day_load_accuracy = {'test': np.nan, 'train': np.nan}
			
	else:
		two_day_peak = 0
		two_day_load_accuracy = {'test': np.nan, 'train': np.nan}
		three_day_peak = 0
		three_day_load_accuracy = {'test': np.nan, 'train': np.nan}

	tomorrow_peak = max(tomorrow_load)
	o['predicted_peak'] = [highest_peak_this_month(df, tomorrow), tomorrow_peak, two_day_peak, three_day_peak]
	o['predicted_peak_limits'] = [
		[0, 0],
		[tomorrow_peak*(1 + tomorrow_accuracy['test']*.01), tomorrow_peak*(1 - tomorrow_accuracy['test']*.01)],
		[two_day_peak*(1 + two_day_load_accuracy['test']*.01), two_day_peak*(1 - two_day_load_accuracy['test']*.01)],
		[three_day_peak*(1 + three_day_load_accuracy['test']*.01), three_day_peak*(1 - three_day_load_accuracy['test']*.01)]
	]

	o['load_test_accuracy'] = round(tomorrow_accuracy['test'], 2)
	o['load_train_accuracy'] = round(tomorrow_accuracy['train'], 2)
	o['tomorrow_test_accuracy'] = round(tomorrow_accuracy['test'], 2)
	o['tomorrow_train_accuracy'] = round(tomorrow_accuracy['train'], 2)
	o['two_day_peak_train_accuracy'] = round(two_day_load_accuracy['train'], 2)
	o['two_day_peak_test_accuracy'] = round(two_day_load_accuracy['test'], 2)
	o['three_day_peak_train_accuracy'] = round(three_day_load_accuracy['train'], 2)
	o['three_day_peak_test_accuracy'] = round(three_day_load_accuracy['test'], 2)


	o['peak_percent_chance'] = peak_likelihood(
		hist=highest_peak_this_month(df[:-48], tomorrow), 
		tomorrow=tomorrow_peak,
		tomorrow_std=tomorrow_peak*tomorrow_accuracy['test']*.01,
		two_day=two_day_peak,
		two_day_std=two_day_peak*two_day_load_accuracy['test']*.01,
		three_day=three_day_peak,
		three_day_std=three_day_peak*three_day_load_accuracy['test']*.01
	)

	o['stderr'] = ''

	return o

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		'created': '2015-06-12 17:20:39.308239',
		'modelType': modelName,
		'runTime': '0:01:03',
		'epochs': '1',
		'autoFill': "off",
		'histFileName': 'd_Texas_17yr_TempAndLoad.csv',
		"histCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","d_Texas_17yr_TempAndLoad.csv"), 'rU').read(),
		'tempFileName': '72hr_TexasTemp.csv',
		'tempCurve': open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","72hr_TexasTemp.csv"), 'rU').read()
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

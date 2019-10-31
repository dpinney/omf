''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import os, sys, shutil, csv
from datetime import datetime as dt, timedelta
from os.path import isdir, join as pJoin
import pandas as pd
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf import forecast as lf
try:
	import tensorflow as tf
except:
	pass
import numpy as np
from scipy.stats import norm
import re

# test

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "This model predicts whether the following day will be a monthly peak."
# hidden = True

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

def autofill(df):
	def estimate(df, last_dt, hour, item):
		prev_d = last_dt - datetime.timedelta(days=1)
		prev_w = last_dt - datetime.timedelta(days=7)

		df_pd = df[df.dates.dt.date == prev_d.date()]
		df_pw = df[df.dates.dt.date == prev_w.date()]

		est_pd = float(df_pd[df_pd['hour'] == hour][item])
		est_pw = float(df_pw[df_pw['hour'] == hour][item])

		return (est_pd + est_pw)/2

	
	last_dt = df.dates.max()
	if last_dt.hour != 23:
		ds_to_add = []
		for hour in range(last_dt.hour+1, 24):
			load = estimate(df, last_dt, hour, 'load')
			weather = estimate(df, last_dt, hour, 'tempc')
			d = {
				'load': load, 
				'tempc': weather, 
				'year': last_dt.year,
				'day': last_dt.day, 
				'hour': hour, 
				'month': last_dt.month, 
				'dates': dt(last_dt.year, last_dt.month, last_dt.day, hour)
			}
			ds_to_add.append(d)

		return df.append(ds_to_add, ignore_index=True)
	else:
		return df

def work(modelDir, ind):
	''' Model processing done here. '''
	epochs = int(ind['epochs'])
	o = {}  # See bottom of file for out's structure

	try:
		with open(pJoin(modelDir, 'hist.csv'), 'w') as f:
			f.write(ind['histCurve'].replace('\r', ''))
		df = pd.read_csv(pJoin(modelDir, 'hist.csv'))
		assert df.shape[0] >= 26280, 'At least 3 years of data is required'

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
		weather = [float(i) for i in ind['tempCurve'].split('\n') if i != '']
		assert len(weather) == 72, "weather csv in wrong format"
	except:
		raise Exception(ind['tempCurve'])

	# ---------------------- MAKE PREDICTIONS ------------------------------- #

	df = df.sort_values('dates')
	d = dict(df.groupby(df.dates.dt.date)['dates'].count())
	df = autofill(df)
	df = df[df['dates'].dt.date.apply(lambda x: d[x] == 24)] # find all non-24

	df, tomorrow = lf.add_day(df, weather[:24])
	all_X = lf.makeUsefulDf(df)
	all_y = df['load']

	if ind['newModel'] == 'False':
		for day in ['one_day_model', 'two_day_model', 'three_day_model']:
			with open(pJoin(modelDir, ind[day+'_filename']), 'wb') as f:
					f.write(ind[day].decode('base64'))

	#load prediction
	tomorrow_load, model, tomorrow_accuracy = lf.neural_net_next_day(
		all_X, all_y, 
		epochs=epochs, save_file=pJoin(modelDir, 'one_day_model.h5'),
		model=(None if ind['newModel'] == 'True' else tf.keras.models.load_model(pJoin(modelDir, ind['one_day_model_filename'])))
	)

	o['tomorrow_load'] = tomorrow_load
	o['month_start'] = dt(tomorrow.year, tomorrow.month, 1).strftime("%A, %B %-d, %Y")
	o['forecast_start'] = tomorrow.strftime("%A, %B %-d, %Y")
	
	# second day
	df, second_day = lf.add_day(df, weather[24:48])
	if second_day.month == tomorrow.month:
		all_X = lf.makeUsefulDf(df, hours_prior=48, noise=5)
		all_y = df['load']
		two_day_predicted_load, two_day_model, two_day_load_accuracy = lf.neural_net_next_day(
			all_X, all_y, 
			epochs=epochs, hours_prior=48, 
			save_file=pJoin(modelDir, 'two_day_model.h5'),
			model=(None if ind['newModel'] == 'True' else tf.keras.models.load_model(pJoin(modelDir, ind['two_day_model_filename'])))
		)
		two_day_peak = max(two_day_predicted_load)

		# third day
		df, third_day = lf.add_day(df, weather[48:72])
		if third_day.month == tomorrow.month:
			all_X = lf.makeUsefulDf(df, hours_prior=72, noise=15)
			all_y = df['load']
			three_day_predicted_load, three_day_model, three_day_load_accuracy = lf.neural_net_next_day(
				all_X, all_y, 
				epochs=epochs, hours_prior=72, 
				save_file=pJoin(modelDir, 'three_day_model.h5'),
				model=(None if ind['newModel'] == 'True' else tf.keras.models.load_model(pJoin(modelDir, ind['three_day_model_filename'])))
			)
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
	m = df[(df['month'] == tomorrow.month) & (df['year'] != tomorrow.year) ]
	hourly = m
	m = m.groupby(m.dates.dt.date)['load'].max()
	o['quantile'] = round(m[m < tomorrow_peak].shape[0]/float(m.shape[0])*100, 2)
	o['predicted_peak'] = [m.median(), highest_peak_this_month(df, tomorrow), tomorrow_peak, two_day_peak, three_day_peak]
	o['predicted_peak_limits'] = [
		[m.min(), m.max()],
		[0, 0],
		[tomorrow_peak*(1 + tomorrow_accuracy['test']*.01), tomorrow_peak*(1 - tomorrow_accuracy['test']*.01)],
		[two_day_peak*(1 + two_day_load_accuracy['test']*.01), two_day_peak*(1 - two_day_load_accuracy['test']*.01)],
		[three_day_peak*(1 + three_day_load_accuracy['test']*.01), three_day_peak*(1 - three_day_load_accuracy['test']*.01)]
	]
	m = hourly
	previous_months = [{
		'year': y,
		'load': m[m['year'] == y]['load'].tolist()
	} for y in m.year.unique()]

	# hard-code the input for highcharts
	o['cats_pred'] = list(range(744)) ### FIX THIS

	l = []
	for d in previous_months:
		l.append({
			'name': d['year'],
			'color': 'lightgrey',
			'data': d['load'],
			'type': 'line',
			'opacity': .05,
			'enableMouseTracking': False
		})

	load_leading_up = df[(df['month'] == tomorrow.month) & (df['year'] == tomorrow.year)]['load'].tolist()
	l.append({'name': tomorrow.year, 'color': 'black', 'data': load_leading_up[:-72], 'type': 'line'})
	l.append({'name':'forecast','color':'blue','data': [None]*(len(load_leading_up) - 72) + o['tomorrow_load'],'type': 'line'})

	o['previous_months'] = l

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

	# re-input values
	ind['newModel'] = 'False',
	ind['one_day_model'] = open(pJoin(modelDir,'one_day_model.h5')).read().encode("base64"),
	ind['one_day_model_filename'] = 'one_day_model.h5',
	ind['two_day_model'] = open(pJoin(modelDir,'two_day_model.h5')).read().encode("base64"),
	ind['two_day_model_filename'] = 'two_day_model.h5',
	ind['three_day_model'] = open(pJoin(modelDir,'three_day_model.h5')).read().encode("base64"),
	ind['three_day_model_filename'] = 'three_day_model.h5',

	return o

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		'created': '2015-06-12 17:20:39.308239',
		'modelType': modelName,
		'runTime': '0:01:03',
		'epochs': '1',
		# 'autoFill': "off",
		# 'histFileName': 'd_Texas_17yr_TempAndLoad_Dec.csv',
		# "histCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","d_Texas_17yr_TempAndLoad_Dec.csv"), 'rU').read(),
		'tempFileName': '72hr_TexasTemp.csv',
		'tempCurve': open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","72hr_TexasTemp.csv"), 'rU').read(),
		
		# autofill
		'histFileName': 'Texas_1pm.csv',
		"histCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_1pm.csv"), 'rU').read(),		

		# upload models
		'newModel': 'False',
		'one_day_model': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','one_day_model.h5')).read().encode("base64"),
		'one_day_model_filename': 'one_day_model.h5',
		'two_day_model': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','two_day_model.h5')).read().encode("base64"),
		'two_day_model_filename': 'two_day_model.h5',
		'three_day_model': open(pJoin(__neoMetaModel__._omfDir,'static','testFiles','three_day_model.h5')).read().encode("base64"),
		'three_day_model_filename': 'three_day_model.h5',
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

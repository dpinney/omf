''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import os, sys, shutil, csv
from datetime import datetime as dt, timedelta
from os.path import isdir, join as pJoin
import pandas as pd
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf import forecast as lf
from omf import peakForecast as pf

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "This model predicts whether the following day will be a monthly peak."
hidden = True
def work(modelDir, ind):
	''' Model processing done here. '''
	epochs = int(ind['epochs'])
	o = {}  # See bottom of file for out's structure
	o['max_c'] = float(ind['max_c'])

	try:
	 	with open(pJoin(modelDir, 'hist.csv'), 'w') as f:
	 		f.write(ind['histCurve'].replace('\r', ''))
		df = pd.read_csv(pJoin(modelDir, 'hist.csv'))
		assert df.shape[0] >= 26280 # must be longer than 3 years
	 	df['dates'] = df.apply(
			lambda x: dt(
				int(x['year']), 
				int(x['month']), 
				int(x['day']), 
				int(x['hour'])), 
			axis=1
		)
		df['dayOfYear'] = df['dates'].dt.dayofyear
	except:
		raise Exception("CSV file is incorrect format.")

	this_year = max(list(df.year.unique()))
	o['startDate'] = "{}-01-01".format(this_year)

	# ---------------------- MAKE PREDICTIONS ------------------------------- #
	d_dict = pf.dispatch_strategy(df, EPOCHS=epochs)
	df_dispatch = d_dict['df_dispatch']
	
	# -------------------- MODEL ACCURACY ANALYSIS -------------------------- #
	# load forecasting accuracy
	demand = df_dispatch['load']
	o['demand'] = list(demand)
	o['one_day'] = list(df_dispatch['1-day'])
	o['two_day'] = list(df_dispatch['2-day'])
	o['one_day_train'] = 100 - round(d_dict['1-day_accuracy']['train'], 2)
	o['one_day_test'] = 100 - round(d_dict['1-day_accuracy']['test'], 2)
	o['two_day_train'] = 100 - round(d_dict['2-day_accuracy']['train'], 2)
	o['two_day_test'] = 100 - round(d_dict['2-day_accuracy']['test'], 2)


	# peak forecasting accuracy
	df_conf = pf.confidence_dispatch(df_dispatch, max_c=o['max_c'])
	# o['precision_g'] = list(df_conf['precision'])
	# o['recall_g'] = list(df_conf['recall'])
	# o['peaks_missed_g'] = list(df_conf['peaks_missed'])
	# o['unnecessary_dispatches_g'] = list(df_conf['unnecessary_dispatches'])
	
	ans = df_dispatch['should_dispatch']
	pre = df_dispatch['dispatch']
	days = [(dt(this_year, 1, 1)+timedelta(days=1)*i) for i, _ in enumerate(pre)]
	tp = list((ans & pre)*demand)
	fp = list(((~ans) & pre)*demand)
	fn = list((ans & (~pre)*demand))
	o['true_positive'] = [[str(i)[:-9] + "T20:15:00.441844", j] for i, j in zip(days, tp)]
	o['false_positive'] = [[str(i)[:-9] + "T20:15:00.441844", j] for i, j in zip(days,fp)]
	o['false_negative'] = [[str(i)[:-9] + "T20:15:00.441844", j] for i, j in zip(days, fn)]

	# recommended confidence
	d = pf.find_lowest_confidence(df_conf)
	o['lowest_confidence'] = d['confidence']
	o['lowest_dispatch'] = d['unnecessary_dispatches']

	print(len(o['true_positive']), o['true_positive'])
	
	o['stderr'] = ''

	return o

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		'created': '2015-06-12 17:20:39.308239',
		'modelType': modelName,
		'runTime': '0:01:03',
		'epochs': '1',
		'max_c': '0.1',
		'histFileName': 'd_Texas_17yr_TempAndLoad.csv',
		"histCurve": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","d_Texas_17yr_TempAndLoad.csv"), 'rU').read(),
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

''' Calculate the costs and benefits of energy storage from a distribution utility perspective. '''

import os, sys, shutil, csv
from datetime import datetime as dt, timedelta
from os.path import isdir, join as pJoin
import pandas as pd
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf import loadForecast as lf

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "This model predicts whether the following day will be a monthly peak."
hidden = True

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
		raise Exception("CSV file is incorrect format.")

	# ---------------------- MAKE PREDICTIONS ------------------------------- #
	weather = [2.5]*24
	df, predicted_day = lf.add_day(df, weather)
	all_X = lf.makeUsefulDf(df)
	all_y = df['load']
	# predictions, model = lf.neural_net_next_day(all_X, all_y, EPOCHS=1)
	predictions = [13044.3369140625, 12692.4453125, 11894.0712890625, 13391.0185546875, 13378.373046875, 14098.5048828125, 14984.5, 15746.6845703125, 14677.6064453125, 14869.6953125, 14324.302734375, 13727.908203125, 13537.51171875, 12671.90234375, 13390.9970703125, 12111.166015625, 13539.05078125, 15298.7939453125, 14620.8369140625, 15381.9404296875, 15116.42578125, 13652.3974609375, 13599.5986328125, 12882.5185546875]
	o['predictions'] = predictions
	o['startDate'] = "{}-{}-{}".format(predicted_day.year, predicted_day.month, predicted_day.day)
	print o['startDate']
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

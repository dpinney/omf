# break out of code on keyboard interrupt -------------------------------------

import os, signal
def signalHandler(signal, frame):
    os._exit(1)

signal.signal(signal.SIGINT, signalHandler)

# imports ---------------------------------------------------------------------

import pathlib, time, csv
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import IncrementalPCA
from sklearn.linear_model import SGDRegressor
from joblib import Parallel, delayed, Memory, load, dump
from glob import glob

# constants -------------------------------------------------------------------

# define analysis params
NUM_HOUSE_TYPES = 48
NUM_INSTANCES_OF_EACH_HOUSE_TYPE = 2
TIME_CHUNK_IN_SECS = 0
NUM_EPOCHS = 1000
PCA_VAR = 0.95
DELIMITER = ','

# input file params; path defined relative to the code file location
DATA_DIR = str( pathlib.Path(__file__).parent.absolute() ) + '/../data/'
DATA_SUBFOLDER = DATA_DIR + str(NUM_HOUSE_TYPES) + 'house' + \
	str(NUM_INSTANCES_OF_EACH_HOUSE_TYPE) + 'typesInputChunking'

# joblib sometimes writes data out to share among processors
JOBLIB_DIR = str( pathlib.Path(__file__).parent.absolute() ) + 
	'/../workingDir/'

# functions -------------------------------------------------------------------

def train(regressor, data, labels, appIndex):

	# if isinstance(data, np.memmap):
	# 	data = np.asarray(data)
	# if isinstance(labels, np.memmap):
	# 	labels = np.asarray(labels)

	timerStart = time.time()
	labelsSingleApp = labels[:,appIndex]
	regressor.partial_fit(data, labelsSingleApp)
	# score = regressor.score(data, labelsSingleApp)
	timerEnd = time.time()
	
	# print(appIndex, score, timerEnd-timerStart)
	
	return regressor

def test(regressor, data, labels, appIndex):

	# if isinstance(data, np.memmap):
	# 	data = np.asarray(data)
	# if isinstance(labels, np.memmap):
	# 	labels = np.asarray(labels)

	timerStart = time.time()
	labelsSingleApp = labels[:,appIndex]
	prediction = regressor.predict(data)
	# score = regressor.score(prediction, labelsSingleApp)
	timerEnd = time.time()
	
	# print(appIndex, score, timerEnd-timerStart)
	
	return prediction

# initialize vars -------------------------------------------------------------

# define scaler for normalization
scaler = StandardScaler()

# define PCA for dimentionality reduction
pca = IncrementalPCA()

# define regression model
regressor = SGDRegressor(random_state=42, max_iter=1, tol=None)
regressors = None

# load training data one batch at a time
trainFiles = glob(DATA_SUBFOLDER+'/trainBatch*')
timerStartLocal  = time.time()
for fileNum, file in enumerate(trainFiles):
	
	# load batch
	timerStartLocal2  = time.time()
	data,labels = load(file)
	timerEnd = time.time()

	#init scaler and pca
	scaler.partial_fit(data)
	# pca.partial_fit(data)

# determine how many pca components to retain based on provided variance
# numComponentsToRetain = \
# 	np.argmax(pca.explained_variance_ratio_.cumsum() >= PCA_VAR)
# if numComponentsToRetain == 0:
# 	numComponentsToRetain = 1
# print(numComponentsToRetain, pca.explained_variance_ratio_.cumsum())


# train -----------------------------------------------------------------------

with Parallel(n_jobs=2, temp_folder=CACHE_DIR) as parallel:

	# load training data one batch at a time
	trainFiles = glob(DATA_SUBFOLDER+'/trainBatch*')
	timerStartLocal  = time.time()
	for epochNum in range(NUM_EPOCHS):
		for fileNum, file in enumerate(trainFiles):
			
			# load batch
			timerStartLocal2  = time.time()
			data, labels = load(file)
			timerEnd = time.time()


			# normalize and reduce dimentionality
			data = scaler.transform(data)
			# data = pca.transform(data)[:,numComponentsToRetain]
			
			# init regressors
			if regressors == None:
				regressors = [regressor]*labels.shape[1]

			# train models for each app in parallel
			regressors = parallel( delayed(train) ( \
					regressor=regressors[appIndex], \
					data=data, \
					labels=labels, \
					appIndex = appIndex
				) for appIndex in range(labels.shape[1])
			)

			# timerEnd = time.time()
			# print(fileNum, timerEnd-timerStartLocal2)	

		timerEnd = time.time()
		print('epoch', epochNum, timerEnd-timerStartLocal)	

# test -----------------------------------------------------------------------

hour = int(TIME_CHUNK_IN_SECS/3600)
resultsFile = DATA_SUBFOLDER+'/results'+str(hour)+'timeChunk.csv'
with Parallel(n_jobs=2, temp_folder=CACHE_DIR) as parallel:

	# load training data one batch at a time
	testFiles = glob(DATA_SUBFOLDER+'/testBatch*')
	timerStartLocal  = time.time()
	for fileNum, file in enumerate(testFiles):
		
		# load batch
		# timerStartLocal  = time.time()
		data,labels = load(file)
		# timerEnd = time.time()
		# print(file,timerEnd-timerStartLocal)

		print(fileNum, data.shape,labels.shape)

		# normalize and reduce dimentionality
		data = scaler.transform(data)
		# data = pca.transform(data)[:,numComponentsToRetain]

		# make predictions for each app in parallel
		predictions = parallel( delayed(test) ( \
				regressor=regressors[appIndex], \
				data=data, \
				labels=labels, \
				appIndex = appIndex
			) for appIndex in range(labels.shape[1])
		)
		

	# write to file -----------------------------------------------------------

		pred = np.array(predictions).transpose()

		print(pred.shape,labels.shape)
		
		with open(resultsFile, 'a') as file:
			writer = csv.writer( file, delimiter=DELIMITER )

			for rowNum in range(labels.shape[0]):
				
				predRow = pred[rowNum,:]
				trueRow = labels[rowNum,:]
				toWrite = list(predRow) + [''] + list(trueRow)
				writer.writerow(toWrite)
				
				# if ( (rowNum+1) % NUM_ROWS_PER_FILE) == 0:
				# 	end = time.time()
				# 	print('house',int(rowNum/NUM_ROWS_PER_FILE),'/', \
				# 		NUM_INSTANCES*NUM_HOUSE_TYPES, \
				# 		'\ntotal time elapsed ', end-START, 'secs')

	# compute and display progress --------------------------------------------

	timerEnd = time.time()
	print(fileNum, timerEnd-timerStartLocal)
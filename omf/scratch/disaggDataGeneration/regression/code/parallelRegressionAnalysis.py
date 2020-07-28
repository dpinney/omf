# break out of code on keyboard interrupt -------------------------------------

import os, signal
def signalHandler(signal, frame):
    os._exit(1)

signal.signal(signal.SIGINT, signalHandler)

# imports ---------------------------------------------------------------------

from joblib import Parallel, delayed
import multiprocessing as mp
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import MaxAbsScaler
from scipy.sparse import coo_matrix, hstack, lil_matrix
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import Ridge
from datetime import date

import pathlib, math, time, csv
import plotly.express as px
import numpy as np
import scipy

import plotly.graph_objs as go
# comment this out to let plotly pick the default renderer
# mine defaulted to "browser" and printed out a bunch of stuff to 
# the terminal so i use firefox specifically to avoid that
import plotly.io as pio
pio.renderers.default = "firefox"


# constants -------------------------------------------------------------------

# define analysis params
NUM_HOUSE_TYPES = 48
NUM_INSTANCES = 4
DESIRED_TRAIN_FRACTION = 0.5
RAND_SEED = 42
START = time.time();

# define input file params 
# path relative to the code file location
DATA_DIR = str( pathlib.Path(__file__).parent.absolute() ) + '/../data/'
DATA_SUBFOLDER = DATA_DIR + str(NUM_HOUSE_TYPES) + 'Types' + \
	str(NUM_INSTANCES) + 'HousesPerType'
INPUT_FILE = DATA_SUBFOLDER+'/dataTest.csv'

# define file structure params
DELIMITER = ','
TIMESTEP = 15*60
TEST_DATA_COL_START = 10
NUM_ROWS_PER_FILE = 35136
CATEGORICAL_FEATURE_INDEXES = [0,1,2,3]
CATEGORICAL_FEATURE_INT_MAPPING = {
	0:{'True':0, 'False':1},
	1:{'GASHEAT':0,'ELECTRIC':1},
	2:{'HEAT_PUMP':0,'ELECTRIC':1,'NONE':2},
	3:{'HEAT_PUMP':0,'GAS':1,'RESISTANCE':2,'NONE':3}
}

# functions -------------------------------------------------------------------

def loadData(filename):
	
	print('\nloading file')
	
	rowNum = 0
	xNumCols, yNumCols = 0, 0
	x, xNonZeroRows, yNonZeroRows = [], [], []
	y, xNonZeroCols, yNonZeroCols = [], [], []

	with open(INPUT_FILE, 'r') as file:

		# read header and get list of appliance from it
		appliances=file.readline()
		appliances=appliances.replace('\n','')
		appliances=appliances.split(DELIMITER)
		appliances=appliances[TEST_DATA_COL_START:]
		appliances=np.array(appliances)

		# separate each line into x and y and save in sparse matrix
		for line in file:
			data = line.split(DELIMITER)

			# break timestamp into its components
			timestamp = data[0].split(' ')
			dataDate = timestamp[0].split('-')
			dataTime = timestamp[1].split(':')

			# compute time features from timestamp
			hourOfDay = int(dataTime[0])
			dayOfWeek = date( int(dataDate[0]),
				int(dataDate[1]), int(dataDate[2]) ).weekday()
			isWeekend = 0
			if (dayOfWeek == 5) or (dayOfWeek == 5):
				isWeekend = 1

			# create xRow and yRow 
			xRow = data[1:TEST_DATA_COL_START] + [isWeekend, hourOfDay]
			yRow = data[TEST_DATA_COL_START:]

			if rowNum == 0:
				xNumCols = len(xRow)
				yNumCols = len(yRow)

			# convert categorical variables to ints
			for colNum in CATEGORICAL_FEATURE_INDEXES:
				xRow[colNum] = \
					CATEGORICAL_FEATURE_INT_MAPPING[colNum][xRow[colNum]]

			# keep track of non-zero values for sparse matrix creation
			trackNonZeros( xRow, rowNum, xNonZeroRows, xNonZeroCols, x)
			trackNonZeros( yRow, rowNum, yNonZeroRows, yNonZeroCols, y)

			rowNum+=1
			if (rowNum % NUM_ROWS_PER_FILE) == 0:
				end = time.time()
				print('house',int(rowNum/NUM_ROWS_PER_FILE),'/', \
					NUM_INSTANCES*NUM_HOUSE_TYPES, \
					'total time elapsed', end-START, 'secs')

	# create sparse matrices --------------------------------------------------
	
	localStart = time.time()
	print('\nconverting to sparse representation')
	
	# calculate toltal number of houses and do some error checking
	numHouses = NUM_HOUSE_TYPES*NUM_INSTANCES
	if numHouses == 1:
		raise Exception('input data must have at least 2 houses')
	
	# calculate toltal number of rows and do some error checking
	numRows = numHouses*NUM_ROWS_PER_FILE
	if numRows != rowNum:
		raise Exception( 'numRows: '+ numRows + \
			' != num rows read from file: ' + rowNum + \
			' provided NUM_ROWS_PER_FILE: ' + NUM_ROWS_PER_FILE + \
			' is likely incorrect' )

	# calculate nuber of houses to use for training 
	# ensure theres at least one test house
	numTrainHouses = math.ceil(numHouses*DESIRED_TRAIN_FRACTION)
	numTestHouses = numHouses - numTrainHouses
	if numTestHouses == 0:
		numTrainHouses -= 1
		numTestHouses += 1
	numTrainRows = numTrainHouses*NUM_ROWS_PER_FILE
	numTestRows = numTestHouses*NUM_ROWS_PER_FILE

	# convert index arrays into numpy array
	x = np.array(x)
	y = np.array(y)
	xNonZeroRows = np.array(xNonZeroRows)
	yNonZeroRows = np.array(yNonZeroRows)
	xNonZeroCols = np.array(xNonZeroCols)
	yNonZeroCols = np.array(yNonZeroCols)
	# compute training and testing indexes
	xTrainingMask = (xNonZeroRows<numTrainRows)
	xTestingMask = np.invert(xTrainingMask)
	yTrainingMask = (yNonZeroRows<numTrainRows)
	yTestingMask = np.invert(yTrainingMask)

	# create sparse arrays
	xTrain = coo_matrix( \
		(x[xTrainingMask], \
			(xNonZeroRows[xTrainingMask], \
				xNonZeroCols[xTrainingMask])), \
		shape=[numTrainRows,xNumCols])
	yTrain = coo_matrix( \
		(y[yTrainingMask], \
			(yNonZeroRows[yTrainingMask], \
				yNonZeroCols[yTrainingMask])), \
		shape=[numTrainRows,yNumCols])
	xTest = coo_matrix( \
		(x[xTestingMask], \
			(xNonZeroRows[xTestingMask]-numTrainRows, \
				xNonZeroCols[xTestingMask])), \
		shape=[numTestRows,xNumCols])
	yTest = coo_matrix( \
		(y[yTestingMask], \
			(yNonZeroRows[yTestingMask]-numTrainRows, \
				yNonZeroCols[yTestingMask])), \
		shape=[numTestRows,yNumCols])
	
	# compute and display progress
	end = time.time()
	print('completed in', end-localStart, 'secs')
	print('xTrain shape',xTrain.shape,'yTrain shape',yTrain.shape)
	print('xTest shape',xTest.shape,'yTest shape',yTest.shape)
	print('\ntotal time elapsed', end-START, 'secs')	

	# convert categorical features to one-hot ---------------------------------
	
	localStart = time.time()
	print('\nperforming one-hot encoding')
	print('original xTrain shape', xTrain.shape)
	print('original xTest shape', xTest.shape)
	
	# perform encoding
	xTrain = performOneHotEncoding( xTrain )
	xTest = performOneHotEncoding( xTest )
	
	# compute and display progress
	end = time.time()
	print('completed in', end-localStart, 'secs')
	print('converted xTrain shape', xTrain.shape, \
		' yTrain shape', yTrain.shape)
	print('converted xTest shape', xTest.shape, \
		' yTest shape', yTest.shape)
	print('appliances shape', appliances.shape)
	print('\ntotal time elapsed', end-START, 'secs')	

	return xTrain, yTrain, xTest, yTest, appliances

def reshapeByTimeChunk( data, timeChunk ):

	# get sparse matrix defining params
	numHouses = (data.shape[0]/NUM_ROWS_PER_FILE)
	numFeatures = data.shape[1]
	dataRows = data.row
	dataCols = data.col
	dataVals = data.data

	#determine new array shape given timeChunk and TIMESTEP
	numExamplesToCombine = int(timeChunk/TIMESTEP)
	if numExamplesToCombine < 1:
		numExamplesToCombine = 1
	numRowsToKeep = numExamplesToCombine * \
			int(NUM_ROWS_PER_FILE/numExamplesToCombine)
	numRows = numHouses*numRowsToKeep
	numDesiredRows = int(numRows/numExamplesToCombine)
	numDesiredFeatures = numFeatures*numExamplesToCombine

	# recalculate dataRows and dataCols to reshape the matrix
	rowOffset = (dataRows%numExamplesToCombine)
	reshapedDataRows = (dataRows/numExamplesToCombine).astype(int)
	reshapedDataCols = (dataCols*numExamplesToCombine)+\
		(dataRows%numExamplesToCombine)

	# delete leftover row that dont form a complete chunk
	toKeep =  reshapedDataRows < numDesiredRows
	chunkedDataRows = reshapedDataRows[toKeep]
	chunkedDataCols = reshapedDataCols[toKeep]
	chunkedDataVals = dataVals[toKeep]

	# print('-----------------------------')
	# dataRows = dataRows[toKeep]
	# for i, ii in enumerate(chunkedDataRows):
	# 	print(dataRows[i],ii)
	# print('-----------------------------')

	# create new sparse matrix
	data = coo_matrix( (chunkedDataVals, (chunkedDataRows, chunkedDataCols)), \
		shape=[numDesiredRows,numDesiredFeatures])
	
	return data

def predict(regressor, xTrain, yTrain, xTest, yTest, appIndex):

	# get the column we want to train on 
	trainLabels = yTrain.getcol(appIndex).toarray().reshape(-1)

	# train model and make predictions
	localStart = time.time()
	# print('\ntraining model for column ', appIndex)
	regressor.fit(xTrain,trainLabels)
	end = time.time()
	print('completed model training for column ', appIndex, ' in ', end-localStart, 'secs')
	print('total time elapsed ', end-START, 'secs')
	
	localStart = time.time()
	# print('making predictions')
	predictions = regressor.predict(xTest)
	print('completed predictions for column ', appIndex, ' in ', end-localStart, 'secs')
	print('total time elapsed ', end-START, 'secs')

	return predictions
	
# helper functions ------------------------------------------------------------

def trackNonZeros( inputArray, rowNum, rowTrack, colTrack, dataTrack):

	for colNum, item in enumerate(inputArray):
		item = float(item)
		if item != 0:
			colTrack.append(colNum)
			rowTrack.append(rowNum)
			dataTrack.append(item)

def performOneHotEncoding( x ):

	xConverted = None
	oh = OneHotEncoder()
	for colNum in range(x.shape[1]):
		
		# encode categorical columns
		xCol = x.getcol(colNum)
		if colNum in CATEGORICAL_FEATURE_INDEXES:
			xCol = oh.fit_transform(xCol.toarray())

			# remove one of the cols for binary features
			if xCol.shape[1] == 2:
				xCol = xCol[:,0]

		# if this is the first column replace xConverted
		if xConverted is None:
			xConverted = xCol
		else: # otherwise append xConverted as a 32 bit float
			xConverted = hstack((xConverted,xCol), dtype=np.float32)

	return xConverted

# main ------------------------------------------------------------------------

START = time.time()

# define regression model
# regressor = Ridge(random_state=RAND_SEED, max_iter=2000)
regressor = SGDRegressor(random_state=RAND_SEED, max_iter=2000, tol=1e-3)

# load data
xTrainOrig, yTrainOrig, xTestOrig, yTestOrig, appliances = \
	loadData( INPUT_FILE )

scaler = MaxAbsScaler()
xTrainOrig = scaler.fit_transform(xTrainOrig)
xTestOrig = scaler.transform(xTestOrig)
xTrainOrig = xTrainOrig.tocoo()
xTestOrig = xTestOrig.tocoo()

TIME_CHUNKS = [24]#[0,24,2,12,48,24*7]
for iterNum, hour in enumerate(TIME_CHUNKS):
	timeChunk = hour*3600

	# perform regression 
	localStart = time.time()
	print('\nperforming regression with',hour,'hour chunks')

	# reshape data in time chunks
	xTrain = reshapeByTimeChunk( xTrainOrig, timeChunk )
	yTrain = reshapeByTimeChunk( yTrainOrig, timeChunk )
	xTest = reshapeByTimeChunk( xTestOrig, timeChunk )
	yTest = reshapeByTimeChunk( yTestOrig, timeChunk )

	# print reshaped data shape
	print('xTrain', xTrain.shape, 'yTrain', yTrain.shape)
	print('xTest', xTest.shape, 'yTest', yTest.shape) 
	print('appliances', appliances.shape)

	# perform predictions for each appliance in parallel
	# results = [ pool.apply( predict, \
	# 	args=(regressor, xTrain, yTrain, xTest, yTest, appIndex) ) \
	# 	for appIndex in np.arange(yTest.shape[1]) ]
	predictions = Parallel(n_jobs=2)( delayed(predict) \
		(regressor, xTrain, yTrain, xTest, yTest, appIndex) \
		for appIndex in range(yTest.shape[1]) )

	# for appIndex in range(yTest.shape[1]):
	# 	predict(regressor, xTrain, yTrain, xTest, yTest, appIndex)

	# pool.close() 

	# write to file ---------------------------------------------------------

	pred = np.array(predictions).transpose()
	print(pred.shape)

	true = yTest.toarray()

	resultsFile = DATA_SUBFOLDER+'/results'+str(hour)+'timeChunk.csv'
	with open(resultsFile, 'w') as file:
		writer = csv.writer( file, delimiter=DELIMITER )

		for rowNum in range(yTest.shape[0]):
			
			predRow = pred[rowNum,:]
			trueRow = true[rowNum,:]
			toWrite = list(predRow) + [''] + list(trueRow)
			writer.writerow(toWrite)
			
			# if ( (rowNum+1) % NUM_ROWS_PER_FILE) == 0:
			# 	end = time.time()
			# 	print('house',int(rowNum/NUM_ROWS_PER_FILE),'/', \
			# 		NUM_INSTANCES*NUM_HOUSE_TYPES, \
			# 		'\ntotal time elapsed ', end-START, 'secs')

	# compute and display progress
	end = time.time()
	print('completed iteration', iterNum, 'in', end-localStart, 'secs')
	print('\ntotal time elapsed ', end-START, 'secs')

# close multiprocessing pool
# pool.close()    
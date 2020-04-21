# imports ---------------------------------------------------------------------

from sklearn.linear_model import LinearRegression
from sklearn.linear_model import RANSACRegressor
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
from sklearn.svm import LinearSVR
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.isotonic import IsotonicRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler

import numpy as np
import time

# constants -------------------------------------------------------------------

TRAIN_FILE = 'disaggData.csv' 
TEST_FILE = 'disaggData.csv'
TRAIN_FRACTION = 0.9
TEST_FRACTION = 0.1

SEED = 42

# helper functions ------------------------------------------------------------

def loadData(filename):

	x, y, appliances= [],[],[]
	dayOfWeek, previousDay = -1,0
	with open(filename, 'r') as file:
		appliances=file.readline()
		appliances=appliances.split(',')
		appliances=appliances[2:]
		for line in file:

			data = line.split(',')
			timestamp = data[0].split(' ')
			date = timestamp[0].split('-')
			time = timestamp[1].split(':')

			if date[1] != previousDay:
				previousDay = date[1]
				dayOfWeek += 1
				if dayOfWeek == 7:
					dayOfWeek = 0

			x.append([ date[1],date[2],dayOfWeek,time[0],time[1],data[1] ])
			y.append(data[2:])

	x = StandardScaler().fit_transform(x)
	return x,y,appliances

# load data and split into train and test -------------------------------------

trainX, trainY, appliances = loadData(TRAIN_FILE)
testX, testY,  = loadData(TEST_FILE)[0:2]

trainX = np.array(trainX,dtype='float64')
trainY = np.array(trainY,dtype='float64')
testX = np.array(testX,dtype='float64')
testY = np.array(testY,dtype='float64')

numTrainPoints = int(trainX.shape[0] * TRAIN_FRACTION)
numTestPoints = int(testX.shape[0] * TEST_FRACTION)

trainX = trainX[:numTrainPoints,:]
trainY = trainY[:numTrainPoints,:]
testX = testX[-numTestPoints:,:]
testY = testY[-numTestPoints:,:]

# build regressors ------------------------------------------------------------

regressors = [
	LinearRegression(),
	# RANSACRegressor(random_state=SEED),
	Ridge(random_state=SEED),
	Lasso(random_state=SEED),
	LinearSVR(random_state=SEED),
	SVR(),
	IsotonicRegression(),
	DecisionTreeRegressor(random_state=SEED),
	AdaBoostRegressor(random_state=SEED),
	KNeighborsRegressor(),
	MLPRegressor(random_state=SEED, hidden_layer_sizes=(5,), max_iter=1000)
]

names = [
	'LinearRegression',
	# 'RANSACRegressor',
	'Ridge',
	'Lasso',
	'LinearSVR',
	'SVR',
	'IsotonicRegression',
	'DecisionTreeRegressor',
	'AdaBoostRegressor',
	'KNeighborsRegressor',
	'MLPRegressor'
]

regressorsWith1dOutput = [
	'LinearSVR',
	'SVR',
	'IsotonicRegression',
	'AdaBoostRegressor'
]

# make predictions ------------------------------------------------------------

print(appliances)
for regressorName,regressor in zip(names,regressors):
	print('\n'+regressorName+'------------------------')

	if regressorName in regressorsWith1dOutput:

		predictions = np.zeros( testY.shape )
		for applianceNum in range(trainY.shape[1]):

			trainY2 = trainY[:,applianceNum]
			if regressorName == 'IsotonicRegression':
				trainX2 = trainX[:,-1]
				testX2 = testX[:,-1]
			else:
				trainX2 = trainX.copy()
				testX2 = testX.copy()

			model = regressor.fit(trainX2,trainY2)
			prediction = model.predict(testX2)
			predictions[:,applianceNum] = \
				prediction.reshape( (prediction.shape[0],) )

	else:

		model = regressor.fit(trainX,trainY)
		predictions = model.predict(testX)

	error = predictions-testY
	errorMean = error.mean()
	errorStd = error.std()
	errorMeanByApp = error.mean(axis=0)
	errorStdByApp = error.std(axis=0)

	print(errorMean)
	print(errorStd)
	print(errorMeanByApp)
	print(errorStdByApp)

	# raise Exception('')
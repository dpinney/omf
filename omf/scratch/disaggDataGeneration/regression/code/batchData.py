# break out of code on keyboard interrupt -------------------------------------

import os, signal
def signalHandler(signal, frame):
    os._exit(1)

signal.signal(signal.SIGINT, signalHandler)

# imports ---------------------------------------------------------------------

import pathlib, time, csv
import numpy as np
from datetime import date
from joblib import load, dump

# constants -------------------------------------------------------------------

# define analysis params
NUM_HOUSE_TYPES = 48
NUM_INSTANCES_OF_EACH_HOUSE_TYPE = 2
APPLIANCE_DATA_START_COL = 10
NUM_ROWS_PER_HOUSE = 35136
DESIRED_TRAIN_FRAC = 0.5
TIME_CHUNK_IN_SECS = 0
FILE_TIMESTEP_IN_SECS = 15*60
DELIMITER = ','

# define the maximum number of houses to load and train on at one time
# loading a few houses at a time prevents us from running out of memory
BATCH_SIZE_IN_HOUSES = 1

# constants for converting categorical features to one-hot encoding
CATEGORICAL_FEATURE_INDEXES = [0,1,2,3]
CATEGORICAL_FEATURE_MAPPING = {
	0:{'True':[0], 'False':[1]},
	1:{'GASHEAT':[0],'ELECTRIC':[1]},
	2:{'HEAT_PUMP':[1,0,0],'ELECTRIC':[0,1,0],'NONE':[0,0,1]},
	3:{'HEAT_PUMP':[1,0,0,0],'GAS':[0,1,0,0],
		'RESISTANCE':[0,0,1,0],'NONE':[0,0,0,1]}
}

# input file params; path defined relative to the code file location
DATA_DIR = str( pathlib.Path(__file__).parent.absolute() ) + '/../data/'
DATA_SUBFOLDER = DATA_DIR + str(NUM_HOUSE_TYPES) + 'Types' + \
	str(NUM_INSTANCES_OF_EACH_HOUSE_TYPE) + 'HousesPerType'
INPUT_FILE = DATA_SUBFOLDER+'/dataTest.csv'

# constants computed from other constants, improves readibility
NUM_TOTAL_HOUSES = NUM_HOUSE_TYPES*NUM_INSTANCES_OF_EACH_HOUSE_TYPE
NUM_TRAIN_HOUSES = int(NUM_TOTAL_HOUSES*DESIRED_TRAIN_FRAC)
NUM_ROWS_PER_BATCH = NUM_ROWS_PER_HOUSE*BATCH_SIZE_IN_HOUSES
NUM_TOTAL_ROWS = NUM_TOTAL_HOUSES*NUM_ROWS_PER_HOUSE
NUM_TRAIN_ROWS = NUM_TRAIN_HOUSES*NUM_ROWS_PER_HOUSE
NUM_ROWS_TO_CHUNK = int(TIME_CHUNK_IN_SECS/FILE_TIMESTEP_IN_SECS)

# input error checking
if NUM_TRAIN_HOUSES == 0:
	raise Exception('the given training fraction results in 0 training houses')
if NUM_ROWS_TO_CHUNK == 0:
	NUM_ROWS_TO_CHUNK = 1

# cache deifnition
CACHE_DIR = str( pathlib.Path(__file__).parent.absolute() ) + '/../workingDir/'

# functions -------------------------------------------------------------------

def getModelInputAndOutputFromFileRow(rowFromFile):
	''' takes a single line from the input csv and converts it into
	input features and output labels '''

	data = rowFromFile.split(DELIMITER)

	# break timestamp into its components
	timestamp = data[0].split(' ')
	dataDate = timestamp[0].split('-')
	dataTime = timestamp[1].split(':')

	# determine whether current sample occurred on a weekend
	isWeekend = 0
	dayOfWeek = date( int(dataDate[0]),
		int(dataDate[1]), int(dataDate[2]) ).weekday()
	if (dayOfWeek == 5) or (dayOfWeek == 6):
		isWeekend = 1

	# determine hour of day for current sample
	hourOfDay = int(dataTime[0])

	# create dataRow and labelsRow 
	dataRow = data[1:APPLIANCE_DATA_START_COL] + [isWeekend, hourOfDay]
	labelsRow = data[APPLIANCE_DATA_START_COL:]

	# convert categorical variables to one-hot encoding
	dataRowEncoded = []
	for colNum, colVal in enumerate(dataRow):
		toAppend = [colVal]
		if colNum in CATEGORICAL_FEATURE_INDEXES:
			toAppend = CATEGORICAL_FEATURE_MAPPING[colNum][colVal]
		dataRowEncoded += toAppend
		
	return dataRowEncoded, labelsRow

def reshapeDataByTimeChunkInputsOnly(modelInput, modelOutput):
	''' reshape data such that each output sample is associated
	with the inputs of all the samples in the previous TIME_CHUNK '''
				
	# group train data by house, such that the structure is 
	# houses by rows by columns
	numRowsInCurrentBatch = modelInput.shape[0]
	numHousesInCurrentBatch = int(numRowsInCurrentBatch/NUM_ROWS_PER_HOUSE)
	modelInput = np.reshape( modelInput, \
		(numHousesInCurrentBatch, -1, modelInput.shape[1]) )
	modelOutput = np.reshape( modelOutput, \
		(numHousesInCurrentBatch, -1, modelOutput.shape[1]) )
	
	# reshape each house based on desired TIME_CHUNK for analysis
	chunkedShape = ( modelInput.shape[0], \
		modelInput.shape[1]-NUM_ROWS_TO_CHUNK+1, \
		modelInput.shape[2]*NUM_ROWS_TO_CHUNK )
	modelInputChunked = np.zeros(chunkedShape)
	# each row will have the rows after it, that are 
	# part of the same time chunk, added to its columns 
	# this way each input sample (each row) has all the data within
	# a TIME_CHUNK included as features
	for chunkRowNum in range(NUM_ROWS_TO_CHUNK):
		rowStartIndex = chunkRowNum
		rowEndIndex = rowStartIndex + chunkedShape[1]
		colStartIndex = chunkRowNum*modelInput.shape[2]
		colEndIndex = colStartIndex+modelInput.shape[2]
		modelInputChunked[:,:,colStartIndex:colEndIndex] = \
			modelInput[:,rowStartIndex:rowEndIndex,:]

	# resize the output to match the input appropriately; 
	modelOutputChunked = modelOutput[:, NUM_ROWS_TO_CHUNK-1:, :]
	# each chunked row will have the appliance outputs of the last
	# sample in the time chunk; so effectively we are trying to 
	# predict each sample based on the previous time chunk worth 
	# of inputs 

	# reshape data back to num examples by features
	modelInputChunked = np.reshape( modelInputChunked, \
		(-1,modelInputChunked.shape[2]) )
	modelOutputChunked = np.reshape( modelOutputChunked, \
		(-1,modelOutputChunked.shape[2]) )

	return modelInputChunked, modelOutputChunked

def reshapeDataByTimeChunkNoOverlap(modelInput, modelOutput):
	''' reshape data such that each output sample is associated
	with the inputs of all the samples in the previous TIME_CHUNK '''
				
	# group train data by house, such that the structure is 
	# houses by rows by columns
	numRowsInCurrentBatch = modelInput.shape[0]
	numHousesInCurrentBatch = int(numRowsInCurrentBatch/NUM_ROWS_PER_HOUSE)
	modelInput = np.reshape( modelInput, \
		(numHousesInCurrentBatch, -1, modelInput.shape[1]) )
	modelOutput = np.reshape( modelOutput, \
		(numHousesInCurrentBatch, -1, modelOutput.shape[1]) )
	
	# reshape each house based on desired TIME_CHUNK for analysis
	numChunks = int(modelInput.shape[1]/NUM_ROWS_TO_CHUNK)
	numRowsToKeep = numChunks*NUM_ROWS_TO_CHUNK
	chunkedShape = ( modelInput.shape[0], \
		numChunks, modelInput.shape[2]*NUM_ROWS_TO_CHUNK )
	modelInputChunked = np.reshape(modelInput[:,:numRowsToKeep,:],chunkedShape)
	
	# resize the output to match the input appropriately; 
	chunkedShape = ( modelOutput.shape[0], \
		int(modelOutput.shape[1]/NUM_ROWS_TO_CHUNK), \
		modelOutput.shape[2]*NUM_ROWS_TO_CHUNK )
	modelOutputChunked = np.reshape(modelOutput[:,:numRowsToKeep,:], \
		chunkedShape)
	
	# reshape data back to num examples by features
	modelInputChunked = np.reshape( modelInputChunked, \
		(-1,modelInputChunked.shape[2]) )
	modelOutputChunked = np.reshape( modelOutputChunked, \
		(-1,modelOutputChunked.shape[2]) )

	return modelInputChunked, modelOutputChunked

# load data split it into batches and save batches to file --------------------

timerStart = time.time()
with open(INPUT_FILE, 'r') as file:

	# read header and get the list of appliances from it
	appliances=file.readline()
	appliances=appliances.replace('\n','')
	appliances=appliances.split(DELIMITER)
	appliances=appliances[APPLIANCE_DATA_START_COL:]
	appliances=np.array(appliances)

	# loop through each line in the file
	batchNum = 0
	for rowNum, row in enumerate(file):

		# get model input and outputs
		dataRow, labelsRow = getModelInputAndOutputFromFileRow(row)
		
		# reset variables at the start of each batch
		rowIndex = rowNum % NUM_ROWS_PER_BATCH
		if rowIndex == 0:
			dataSize = ( NUM_ROWS_PER_BATCH, len(dataRow) )
			labelsSize = ( NUM_ROWS_PER_BATCH, len(labelsRow) )
			data = np.zeros( dataSize )
			labels = np.zeros( labelsSize )
			numRowsInCurrentBatch = 0
		
		# add rows to data
		data[rowIndex,:] = dataRow
		labels[rowIndex,:] = labelsRow
		numRowsInCurrentBatch += 1

		# if we're at the end of a batch
		if ( rowIndex==(NUM_ROWS_PER_BATCH-1) ) or \
			( rowNum==NUM_TOTAL_ROWS-1 ):

			# size the batch appropriately; 
			# we always initialize the vars to be the size of 
			# a full batch, but the last batch can be smaller so 
			# remove any rows that dont have actual data
			data = data[:numRowsInCurrentBatch,:]
			labels = labels[:numRowsInCurrentBatch,:]

			# reshape data such that each output sample is associated
			# with all inputs of all the samples in the previous 
			# TIME_CHUNK
			# timerStartLocal  = time.time()
			data, labels = reshapeDataByTimeChunkNoOverlap(data, labels)
			# timerEnd = time.time()

			# name batch based on if it training or test
			filename = 'testBatch' + str(batchNum) + '.joblib'
			if rowNum < (NUM_TRAIN_HOUSES*NUM_ROWS_PER_HOUSE):
				filename = 'trainBatch' + str(batchNum) + '.joblib'				

			#save batch to file
			timerStartLocal  = time.time()
			dump((data,labels),CACHE_DIR+filename)
			timerEnd = time.time()
			print('write batch to file', timerEnd-timerStartLocal, 'secs')
			batchNum += 1

		# print progress
		if (rowNum % NUM_ROWS_PER_HOUSE) == (NUM_ROWS_PER_HOUSE-1):
			timerEnd = time.time()
			print('house',int(rowNum/NUM_ROWS_PER_HOUSE)+1,'/', \
				NUM_INSTANCES_OF_EACH_HOUSE_TYPE*NUM_HOUSE_TYPES, \
				'total time elapsed', timerEnd-timerStart, 'secs')
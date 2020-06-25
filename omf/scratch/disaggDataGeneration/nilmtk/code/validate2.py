import os, time
from os.path import join as pJoin
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from omf.solvers.nilmtk.nilm_metadata.nilm_metadata import save_yaml_to_datastore
from omf.solvers.nilmtk.nilmtk.nilmtk import DataSet, TimeFrame, MeterGroup, HDFDataStore
from omf.solvers.nilmtk.nilmtk.nilmtk.disaggregate import FHMMExact
from omf.solvers.nilmtk.nilmtk.nilmtk.disaggregate import CO
from omf.solvers.nilmtk.nilmtk.nilmtk.disaggregate import Hart85
from omf.solvers.nilmtk.nilmtk.nilmtk.disaggregate import Mean
from omf.solvers.nilmtk.nilmtk.nilmtk.datastore import Key
from omf.solvers.nilmtk.nilmtk.nilmtk.measurement import LEVEL_NAMES
from omf.solvers.nilmtk.nilmtk.nilmtk.utils import get_datastore

# constants -------------------------------------------------------------------

trainFile = '../disaggTraining.csv' 
truthFile = '../disaggTestingTruth.csv'
testFile = '../disaggTesting.csv'

trainBuilding =  1
truthBuilding =  1
testBuilding = 1

algorithm = 'mean'
modelDir = './'

# helper functions ------------------------------------------------------------

def convertTestData(modelDir, data, outputFilename):

	watts = []
	timeStamps = []
	samplePeriod = ''

	# parse provided csv files
	data = data.split('\n')
	firstRow = True
	for row in data:
		if str(row) != '':
			dataPoint = row.split(',')
			if firstRow:
				samplePeriod = dataPoint[0]
				firstRow = False
			else:
				timeStamps.append(dataPoint[0])
				watts.append(dataPoint[1])

	# format dataframe data structure and save in nilmtk format
	store = get_datastore(outputFilename, 'HDF', mode='w')
	df = pd.DataFrame({('power', 'apparent'): watts}, dtype=float)
	df.columns.set_names(LEVEL_NAMES, inplace=True)
	df.index = pd.to_datetime(timeStamps, format='%Y-%m-%d %H:%M:%S', exact=False, utc=True)
	df = df.tz_convert('US/Eastern')
	df = df.sort_index()
	key = Key(building=1, meter=1)
	store.put(str(key), df)

	## create the metadata files in accordance with nilmtk guidelines

	# building metatdata
	if not os.path.exists(pJoin(modelDir,'test')):
	    os.makedirs(pJoin(modelDir,'test'))
	f = open(pJoin(modelDir,'test','building1.yaml'), 'w')
	f.write('instance: 1\n')
	f.write('elec_meters:\n')
	f.write( '  ' + '1: &generic\n')
	f.write( '    ' + 'site_meter: true\n')
	f.write( '    ' + 'device_model: generic\n')
	f.write('\nappliances: []')
	f.close()

	# dataset metadata
	f = open(pJoin(modelDir,'test','dataset.yaml'), 'w')
	f.write('name: testData\n')
	f.close()

	# meter device metadata
	f = open(pJoin(modelDir,'test','meter_devices.yaml'), 'w')
	f.write('generic:\n')
	f.write('  ' + 'model: generic\n')
	f.write('  ' + 'sample_period: ' + samplePeriod + '\n')
	f.write('  ' + 'max_sample_period: ' + samplePeriod + '\n')
	f.write('  ' + 'measurements:\n')
	f.write('  ' + '- physical_quantity: power\n')
	f.write('    ' + 'type: apparent\n')
	f.write('    ' + 'upper_limit: 1000000000\n')
	f.write('    ' + 'lower_limit: -100000000\n')
	f.close()

	# save data and metadata
	save_yaml_to_datastore(pJoin(modelDir,'test'), store)
	store.close()
	
	return outputFilename

def convertTrainData(modelDir, data, outputFilename):

	watts = []
	timeStamps = []
	appliances = []
	samplePeriod = ''

	# parse provided csv files
	data = data.split('\n')
	firstRow = True
	for row in data:
		if str(row) != '':
			dataPoint = row.split(',')
			if firstRow:
				samplePeriod = dataPoint[0]
				firstRow = False
			else:
				timeStamps.append(dataPoint[0])
				watts.append(dataPoint[1])
				appliances.append(dataPoint[2])


	watts = np.array(watts)
	appliances = np.array(appliances)
	timeStamps = np.array(timeStamps)

	store = get_datastore(outputFilename, 'HDF', mode='w')

	# breakdown the data by appliance and set every time point where
	# the appliance wasnt used to 0
	
	uniqueAppliances = list(np.unique(appliances))
	meterIndex = uniqueAppliances.index('meter')

	for index, app in enumerate(uniqueAppliances):
		
		# get the time points where a given appliance is on and 
		# also where it is off
		appIndices = np.where(appliances == app)[0]
		nonAppIndices = np.where(appliances != app)[0]
		
		# keep only the data for when the appliance is on
		wattsFiltered = np.delete(np.copy(watts),nonAppIndices)
		timeFiltered = np.delete(np.copy(timeStamps),nonAppIndices)

		# create zeroed data when the appliance is off
		timeFiller = np.setdiff1d(np.copy(timeStamps),timeFiltered)
		wattsFiller = np.zeros(timeFiller.shape)

		# combine the on and off data
		timeAll = np.append(timeFiller,timeFiltered)
		wattsAll = np.append(wattsFiller,wattsFiltered)

		# format dataframe data structure and save in nilmtk format
		df = pd.DataFrame({('power', 'apparent'): wattsAll}, dtype=float)
		df.index = pd.to_datetime(timeAll, format='%Y-%m-%d %H:%M:%S', exact=False, utc=True)
		df.columns.set_names(LEVEL_NAMES, inplace=True)
		df = df.tz_convert('US/Eastern')
		df = df.sort_index()

		if index == meterIndex:
			key = Key(building=1, meter=1)
		elif index < meterIndex:
			key = Key(building=1, meter=index+2)
		else:
			key = Key(building=1, meter=index+1)			
		
		store.put(str(key), df)

	## create the metadata files in accordance with nilmtk guidelines
	del(uniqueAppliances[meterIndex])

	# building metatdata
	if not os.path.exists(pJoin(modelDir,'train')):
	    os.makedirs(pJoin(modelDir,'train'))
	f = open(pJoin(modelDir,'train', 'building1.yaml'), 'w')
	f.write('instance: 1\n')
	f.write('elec_meters:\n')
	f.write('  ' + '1: &mainMeter\n')
	f.write('    ' + 'site_meter: true\n')
	f.write('    ' + 'device_model: generic\n')
	for index, app in enumerate(uniqueAppliances):
		if index == 0:
			f.write('  ' + '2: &generic\n')
			f.write('    ' + 'submeter_of: 0\n')
			f.write('    ' + 'device_model: generic\n')
		else:
			f.write('  ' + str(index +2) + ': *generic\n')	
	f.write('\nappliances:')
	for index, app in enumerate(uniqueAppliances):
		f.write('\n- ' + 'original_name: ' + app + '\n')
		f.write('  ' + 'type: unknown\n')
		f.write('  ' + 'instance: ' + str(index + 1) + '\n')
		f.write('  ' + 'meters: ['  + str(index + 2) + ']\n')
	f.close()

	# dataset metadata
	f = open(pJoin(modelDir,'train', 'dataset.yaml'), 'w')
	f.write('name: trainData\n')
	f.close()

	# meterdevices metadata
	f = open(pJoin(modelDir,'train', 'meter_devices.yaml'), 'w')
	f.write('generic:\n')
	f.write('  ' + 'model: generic\n')
	f.write('  ' + 'sample_period: ' + samplePeriod + '\n')
	f.write('  ' + 'max_sample_period: ' + samplePeriod + '\n')
	f.write('  ' + 'measurements:\n')
	f.write('  ' + '- physical_quantity: power\n')
	f.write('    ' + 'type: apparent\n')
	f.write('    ' + 'upper_limit: 1000000000\n')
	f.write('    ' + 'lower_limit: -100000000\n')
	f.close()

	# save data and metadata
	save_yaml_to_datastore(pJoin(modelDir,'train'), store)
	store.close()
	
	return outputFilename

def convertTruthData(modelDir, data, outputFilename):

	watts = []
	timeStamps = []
	appliances = []
	samplePeriod = ''

	# parse provided csv files
	data = data.split('\n')
	firstRow = True
	for row in data:
		if str(row) != '':
			dataPoint = row.split(',')
			if firstRow:
				samplePeriod = dataPoint[0]
				firstRow = False
			else:
				timeStamps.append(dataPoint[0])
				watts.append(dataPoint[1])
				appliances.append(dataPoint[2])


	watts = np.array(watts)
	appliances = np.array(appliances)
	timeStamps = np.array(timeStamps)

	store = get_datastore(outputFilename, 'HDF', mode='w')

	# breakdown the data by appliance and set every time point where
	# the appliance wasnt used to 0
	
	uniqueAppliances = list(np.unique(appliances))

	for index, app in enumerate(uniqueAppliances):
		
		# get the time points where a given appliance is on and 
		# also where it is off
		appIndices = np.where(appliances == app)[0]
		nonAppIndices = np.where(appliances != app)[0]
		
		# keep only the data for when the appliance is on
		wattsFiltered = np.delete(np.copy(watts),nonAppIndices)
		timeFiltered = np.delete(np.copy(timeStamps),nonAppIndices)

		# create zeroed data when the appliance is off
		timeFiller = np.setdiff1d(np.copy(timeStamps),timeFiltered)
		wattsFiller = np.zeros(timeFiller.shape)

		# combine the on and off data
		timeAll = np.append(timeFiller,timeFiltered)
		wattsAll = np.append(wattsFiller,wattsFiltered)

		# format dataframe data structure and save in nilmtk format
		df = pd.DataFrame({('power', 'apparent'): wattsAll}, dtype=float)
		df.index = pd.to_datetime(timeAll, format='%Y-%m-%d %H:%M:%S', exact=False, utc=True)
		df.columns.set_names(LEVEL_NAMES, inplace=True)
		df = df.tz_convert('US/Eastern')
		df = df.sort_index()

		key = Key(building=1, meter=index+1)			
		
		store.put(str(key), df)

	## create the metadata files in accordance with nilmtk guidelines

	# building metatdata
	if not os.path.exists(pJoin(modelDir,'truth')):
	    os.makedirs(pJoin(modelDir,'truth'))
	f = open(pJoin(modelDir,'truth', 'building1.yaml'), 'w')
	f.write('instance: 1\n')
	f.write('elec_meters:\n')
	for index, app in enumerate(uniqueAppliances):
		if index == 0:
			f.write('  ' + '1: &generic\n')
			f.write('    ' + 'submeter_of: 0\n')
			f.write('    ' + 'device_model: generic\n')
		else:
			f.write('  ' + str(index + 1) + ': *generic\n')	
	f.write('\nappliances:')
	for index, app in enumerate(uniqueAppliances):
		f.write('\n- ' + 'original_name: ' + app + '\n')
		f.write('  ' + 'type: unknown\n')
		f.write('  ' + 'instance: ' + str(index + 1) + '\n')
		f.write('  ' + 'meters: ['  + str(index + 1) + ']\n')
	f.close()

	# dataset metadata
	f = open(pJoin(modelDir,'truth', 'dataset.yaml'), 'w')
	f.write('name: truthData\n')
	f.close()

	# meterdevices metadata
	f = open(pJoin(modelDir,'truth', 'meter_devices.yaml'), 'w')
	f.write('generic:\n')
	f.write('  ' + 'model: generic\n')
	f.write('  ' + 'sample_period: ' + samplePeriod + '\n')
	f.write('  ' + 'max_sample_period: ' + samplePeriod + '\n')
	f.write('  ' + 'measurements:\n')
	f.write('  ' + '- physical_quantity: power\n')
	f.write('    ' + 'type: apparent\n')
	f.write('    ' + 'upper_limit: 1000000000\n')
	f.write('    ' + 'lower_limit: -100000000\n')
	f.close()

	# save data and metadata
	save_yaml_to_datastore(pJoin(modelDir,'truth'), store)
	store.close()
	
	return outputFilename

# convert csvs into nilmtk format ---------------------------------------------

with open(trainFile, 'r') as file:
    trainData = file.read()
with open(truthFile, 'r') as file:
    truthData = file.read()
with open(testFile, 'r') as file:
    testData = file.read()

truthPath = convertTruthData(modelDir, truthData, 'truthData.h5')
trainPath = convertTrainData(modelDir, trainData, 'trainData.h5')
testPath = convertTestData(modelDir, testData, 'testData.h5')

# load data
train = DataSet(trainPath)
truth = DataSet(truthPath)
test = DataSet(testPath)
trainMetergroup = train.buildings[trainBuilding].elec
truthMetergroup = truth.buildings[truthBuilding].elec
testMetergroup = test.buildings[testBuilding].elec

# select the sampling period 
samplePeriod = next(iter( train.metadata['meter_devices'].values() ))
samplePeriod = samplePeriod['sample_period']


# use appliance names as the labels

appliances = []
trainMainData = []
trainApplianceData = []
trainDataFrames = trainMetergroup.dataframe_of_meters()

for meterNum,meter in enumerate(trainMetergroup.meters):
	
	data = trainDataFrames.iloc[:,meterNum].to_frame()
	data.columns = [('power','apparent')]

	if meter.appliances != []:
		appName = meter.appliances[0].metadata['original_name']
		appName = appName.replace('_',' ')
		appName = appName.capitalize()
		trainApplianceData.append( (appName,[data]) )
		appliances.append(appName)
	else:
		appName = 'Main meter'
		trainMainData.append(data)


# train the appropriate algorithm ---------------------------------------------

clf = ''
params = {}
if algorithm == 'hart85':

	clf = Hart85(params)
	clf. partial_fit(trainMainData, trainApplianceData)

else:

	if algorithm == 'fhmm':
		clf = FHMMExact(params)
	elif algorithm == 'combOpt':
		clf = CO(params)
	elif algorithm == 'mean':
		clf = Mean(params)

	start = time.time()
	clf. partial_fit(trainMainData, trainApplianceData)
	end = time.time()
	print('Training runtime =', end-start, 'seconds.')

# make predicitons ------------------------------------------------------------

testData = [testMetergroup.dataframe_of_meters()]
pred = clf.disaggregate_chunk(testData)
predictedVals = pred[0]
print('---------------------------------')
print('Testing done')
print('---------------------------------')

print()

trueVals = truthMetergroup.dataframe_of_meters()
trueVals.columns=appliances

totalDisagg = predictedVals.sum(1)
totalDisagdByApp = predictedVals.sum()
percentDisagg = 100.*totalDisagdByApp/totalDisagdByApp.sum()

totalTrue = trueVals.sum(1)
totalTrueByApp = trueVals.sum()
percentTrue = 100.*totalTrueByApp/totalTrueByApp.sum()

predictedVals = predictedVals.sort_index(axis=1)
trueVals = trueVals.sort_index(axis=1)

# plot % use by appliance
patches, texts = plt.pie(percentDisagg, startangle=180,  counterclock=False)
labels = ['{0} - {1:1.2f} %'.format(i,j) for i,j in zip(percentDisagg.index, percentDisagg)]
lgd = plt.legend(patches, labels, loc='center left', bbox_to_anchor=(-0.1, 1))
plt.savefig(modelDir + '/predictedDisaggPie.png', 
		bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=600)
plt.clf()

patches, texts = plt.pie(percentTrue, startangle=180,  counterclock=False)
labels = ['{0} - {1:1.2f} %'.format(i,j) for i,j in zip(percentTrue.index, percentTrue)]
lgd = plt.legend(patches, labels, loc='center left', bbox_to_anchor=(-0.1, 1))
plt.savefig(modelDir + '/trueDisaggPie.png', 
		bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=600)
plt.clf()

# error ----------------------------------------------------------------------------

error = predictedVals - trueVals
errorMeanByApp = error.mean()
errorStdByApp = error.std() 
errorMean = error.stack().mean()
errorStd = error.stack().std()

print('\n\n\n')
print('classifier: ' + algorithm)
print('Error mean by appliance------------------------')
print(errorMeanByApp)
print('Error standard deviation by appliance----------')
print(errorStdByApp)
print('Error mean-------------------------------------')
print(errorMean)
print('Error standard deviation-----------------------')
print(errorStd)
print('\n\n\n')
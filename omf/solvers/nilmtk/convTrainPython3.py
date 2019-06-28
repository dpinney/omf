from nilmtk.datastore import Key
from nilmtk.measurement import LEVEL_NAMES
from nilmtk.utils import get_datastore
from nilm_metadata import save_yaml_to_datastore
import os, sys, pickle
import pandas as pd
from os.path import join as pJoin
import numpy as np

samplePeriod = sys.argv[1]
wattsFile = sys.argv[2]
timeStampsFile = sys.argv[3]
appliancesFile = sys.argv[4]
outputFilename = sys.argv[5]
modelDir = sys.argv[6]

f = open(wattsFile, 'rb')
watts = pickle.load(f) 
f.close()
f = open(timeStampsFile, 'rb')
timeStamps = pickle.load(f)  
f.close()
f = open(appliancesFile, 'rb')
appliances = pickle.load(f)  
f.close()

watts = np.array(watts)
appliances = np.array(appliances)
timeStamps = np.array(timeStamps)

store = get_datastore(outputFilename, 'HDF', mode='w')

# breakdown the data by appliance and set every time point where
# the appliance wasnt used to 0
for instance, app in enumerate(np.unique(appliances)):
	
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
	key = Key(building=1, meter=instance+1)
	store.put(str(key), df)

## create the metadata files in accordance with nilmtk guidelines

# building metatdata
if not os.path.exists(pJoin(modelDir,'train')):
    os.makedirs(pJoin(modelDir,'train'))
f = open(pJoin(modelDir,'train', 'building1.yaml'), 'w')
f.write('instance: 1\n')
f.write('elec_meters:\n')
for instance, app in enumerate(np.unique(appliances)):
	if instance == 0:
		f.write('  ' + '1: &generic\n')
		f.write('    ' + 'submeter_of: 0\n')
		f.write('    ' + 'device_model: generic\n')
	else:
		f.write('  ' + str(instance +1) + ': *generic\n')	
f.write('\nappliances:')
for instance, app in enumerate(np.unique(appliances)):
	f.write('\n- ' + 'original_name: ' + app + '\n')
	f.write('  ' + 'type: unknown\n')
	f.write('  ' + 'instance: ' + str(instance +1) + '\n')
	f.write('  ' + 'meters: ['  + str(instance +1) + ']\n')
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
f.write('    ' + 'lower_limit: 0\n')
f.close()

# save data and metadata
save_yaml_to_datastore(pJoin(modelDir,'train'), store)
store.close()
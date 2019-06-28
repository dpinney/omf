from nilmtk.datastore import Key
from nilmtk.measurement import LEVEL_NAMES
from nilmtk.utils import get_datastore
from nilm_metadata import save_yaml_to_datastore
import os, sys, pickle
import pandas as pd
from os.path import join as pJoin

samplePeriod = sys.argv[1]
wattsFile = sys.argv[2]
timeStampsFile = sys.argv[3]
outputFilename = sys.argv[4]
modelDir = sys.argv[5]

f = open(wattsFile, 'rb')
watts = pickle.load(f)  
f.close()
f = open(timeStampsFile, 'rb')
timeStamps = pickle.load(f)  
f.close()

# format dataframe data structure and save in nilmtk format
store = get_datastore(outputFilename, 'HDF', mode='w')
df = pd.DataFrame({('power', 'apparent'): watts}, dtype=float)
df.columns.set_names(LEVEL_NAMES, inplace=True)
df.index = pd.to_datetime(timeStamps, format='%Y-%m-%d %H:%M:%S', exact=False, utc=True)
df = df.tz_convert('US/Eastern')
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
f.write('    ' + 'lower_limit: 0\n')
f.close()

# save data and metadata
save_yaml_to_datastore(pJoin(modelDir,'test'), store)
store.close()
from nilmtk import DataSet, TimeFrame, MeterGroup, HDFDataStore
from nilmtk.disaggregate import fhmm_exact
from nilmtk.disaggregate import CombinatorialOptimisation
import time
import matplotlib.pyplot as plt
import pandas as pd
import warnings
import sys, os

plt.switch_backend('Agg')
warnings.filterwarnings('ignore')

algorithm = sys.argv[1]
trainPath = sys.argv[2]
testPath = sys.argv[3]
trainBuilding = int(sys.argv[4])
testBuilding = int(sys.argv[5])
modelDir = sys.argv[6]

# load data
train = DataSet(trainPath)
test = DataSet(testPath)
train_elec = train.buildings[trainBuilding].elec
test_elec = test.buildings[testBuilding].elec

# select the larger sampling period between the train and the test set
samplePeriod = next(iter(train.metadata['meter_devices'].values()))['sample_period']
testSamples = next(iter(test.metadata['meter_devices'].values()))['sample_period']
if samplePeriod < testSamples:
	samplePeriod = testSamples

# train the appropriate algorithm
clf = ''
if algorithm == 'fhmm':
	clf = fhmm_exact.FHMM()
elif algorithm == 'combOpt':
	print('here')
	clf = CombinatorialOptimisation()
start = time.time()
clf.train(train_elec, sample_period=samplePeriod)
end = time.time()
print('Training runtime =', end-start, 'seconds.')

# make predicitons
pred = {}
testChunks = test_elec.mains().load(sample_period=samplePeriod)
for i, chunk in enumerate(testChunks):
    chunk_drop_na = chunk.dropna()
    pred[i] = clf.disaggregate_chunk(chunk_drop_na)
print('---------------------------------')
print('Testing done')
print('---------------------------------')
# If everything can fit in memory
pred_overall = pd.concat(pred)
pred_overall.index = pred_overall.index.droplevel()

# use appliance names as the labels
appliance_labels = []
for m in pred_overall.columns.values:
    name = m.appliances[0].metadata['original_name']
    name = name.replace('_',' ')
    name = name.capitalize()
    appliance_labels.append(name)
pred_overall.columns = appliance_labels

# compute the total predicted usage as well as the appliance level breakdown
totalDisagg = pred_overall.sum(1)
totalByApp = pred_overall.sum()
totalByApp.sort_values(inplace=True, ascending=False)
percent = 100.*totalByApp/totalByApp.sum()

# plot training data using appliance names as labels
top_k_train_elec = train_elec.submeters().select_top_k(k=5)
appliance_labels = []
for m in top_k_train_elec.meters:
    name = m.appliances[0].metadata['original_name']
    name = name.replace('_',' ')
    name = name.capitalize()
    appliance_labels.append(name)
print('-----------------------------------------')
print(appliance_labels)
print('-------------------------------------------')
top_k_train_elec.plot()
ax = plt.gca()
plt.legend(labels=appliance_labels, bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", 
	mode="expand", borderaxespad=0, ncol=3)
plt.savefig(modelDir + '/trainPlot.png', dpi=600)
plt.clf()

# plot the test data as well as the sum of the disag 
totalDisagg.plot()
test_elec.mains().plot()
ax = plt.gca();
lgd = plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", 
	mode="expand", borderaxespad=0, ncol=3)
lgd.get_texts()[0].set_text('total disaggregation output')
plt.savefig(modelDir + '/testPlot.png', dpi=600)
plt.clf()

# plot disagg time series
pred_overall.plot()
ax = plt.gca();
lgd = plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", 
	mode="expand", borderaxespad=0, ncol=3)
plt.savefig(modelDir + '/disaggPlot.png', 
	bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=600)
plt.clf()

# plot % use by appliance
patches, texts = plt.pie(totalByApp, startangle=180,  counterclock=False)
labels = ['{0} - {1:1.2f} %'.format(i,j) for i,j in zip(totalByApp.index, percent)]
lgd = plt.legend(patches, labels, loc='left center', bbox_to_anchor=(-0.1, 1))
plt.savefig(modelDir + '/disaggPie.png', 
	bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=600)
plt.clf()

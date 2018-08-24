# TODO: see slides.

#import warnings
#warnings.filterwarnings("ignore")

import csv
import matplotlib.pyplot as plt
import numpy as np
import scipy
import StringIO
import datetime
from collections import OrderedDict
import pandas as pd

from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly import tools
import plotly.graph_objs as go

from omf.weather import pullAsos

import CSSS.csss.SolarDisagg as SolarDisagg

#read measured load from csv file
netload_csv = []
with open('load_data.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		netload_csv.append(row)
netload = np.array(netload_csv)

#read the solar proxy from csv file
solarproxy_csv = []
with open('solar_proxy.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		solarproxy_csv.append(row)
solarproxy = np.array(solarproxy_csv)

#Gather weather data from asos and interpolate for 15 minute intervals
timeTemp = OrderedDict()

flike = StringIO.StringIO(pullAsos('2017','CHO', 'tmpf'))
next(csv.reader(flike))
for row in csv.reader(flike):
	if row[2] != 'M':
		timeTemp[datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M")] = float(row[2])
	elif row[1][14:] in ['00','15','30','45'] and row[2] =='M':
		timeTemp[datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M")] = np.nan

#Get the actual data for temperatures 
realTemps = pd.DataFrame(timeTemp.items(), columns=['date', 'temperature'])
realTemps.dropna(inplace=True)
#temporary to get single day of data
realTemps = realTemps[(realTemps['date'] >= '2017-4-15') & (realTemps['date'] < '2017-4-16')]
#print(realTemps)

#interpolate the data to use in model
pdTemps = pd.DataFrame(timeTemp.items(), columns=['date', 'temperature'])
pdTemps.interpolate(inplace=True, limit_direction='both')
#print(pdTemps)

#Filter data set for 15 minute intervals with interpolated data
fifteenMinuteTimestamps = pd.date_range(start='2017-1-1', end='2018-1-1', closed='left', freq='15T')
pdTemps = pdTemps[pdTemps['date'].isin(fifteenMinuteTimestamps)]
#temporary to get single day of data
pdTemps = pdTemps[(pdTemps['date'] >= '2017-4-15') & (pdTemps['date'] < '2017-4-16')]
print(pdTemps)
#pdTemps.set_index('date', inplace=True)

#create load regressor from weather data in correct format as nparray
loadregressors = pdTemps[['temperature']].values


#asosTemps = []
#asosDates = []
#missingTemps = []
#missingDates = []
#for i in timeTemp:
#	if timeTemp[i] == 'M':
#		missingDates.append(((datetime.datetime.strptime(i, "%Y-%m-%d %H:%M"))-datetime.datetime(2017,1,1)).total_seconds())
#	else:
#		asosTemps.append(float(timeTemp[i]))
#		asosDates.append(((datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M"))-datetime.datetime(2017,1,1)).total_seconds())
#missingTemps = np.interp(missingDates, asosDates, asosTemps)
#for i in range(len(missingDates)):
#	timeTemp[(datetime.datetime(2017,1,1)+datetime.timedelta(seconds=missingDates[i])).strftime("%Y-%m-%d %H:%M")] = missingTemps[i]

#limit to one day of weather data for now
#loadregressors=firstDayTemp.reshape(-1,1)

#CSSS run CSSS algo for individual home scenario
sdmod0 = SolarDisagg.SolarDisagg_IndvHome(netloads=netload, solarregressors=solarproxy, loadregressors=loadregressors)
#
sdmod0.constructSolve()

#Create subplots in plotly
fig = tools.make_subplots(rows=5, cols=1, subplot_titles=('Weather', 'Solar Canary', 'House 1', 'House 2', 'House 3' ))
#plot weather and solar canary
fig.append_trace(go.Scatter(y=pdTemps['temperature'], x=pdTemps['date'], name=('interpolated weather ')),1,1)
fig.append_trace(go.Scatter(y=realTemps['temperature'], x=realTemps['date'], name=('real weather data '), mode = 'markers'),1,1)
fig['layout']['yaxis1'].update(title='Temperature')
xaxis = [i for i in range(96)]
fig.append_trace(go.Scatter(y=np.array([item for sublist in solarproxy for item in sublist]), x=pdTemps['date'], name=('Solar Canary ')),2,1)
fig['layout']['yaxis2'].update(title='Watts')

#plot household loads and solar
for i, model in enumerate(sdmod0.models):
	if model != 'AggregateLoad':
		solarArray = np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist])
		disaggLoad = (sdmod0.netloads[str(i)] - solarArray)
		fig.append_trace(go.Scatter(y=sdmod0.netloads[str(i)], x=pdTemps['date'], name=('Measured Load ' + str(i))),i+3,1)
		fig.append_trace(go.Scatter(y=disaggLoad, x=pdTemps['date'], name=('Disaggregated Load (Actual) ' + str(i))),i+3,1)
		fig.append_trace(go.Scatter(y=np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist]), x=pdTemps['date'], name=('Predicted solar ' + str(i))),i+3,1)
		fig['layout']['yaxis' + str(i+3)].update(title='Watts')	

#plot the results
fig['layout'].update(height=1500)
plot(fig)
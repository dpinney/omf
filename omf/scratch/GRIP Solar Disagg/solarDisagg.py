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

#temporary weather data from csv
loadregressors_csv = []
with open('weather_regress.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		loadregressors_csv.append(row)
loadregressors = np.array(loadregressors_csv)

#Gather weather data from asos and interpolate for 15 minute intervals
asosTemps = []
asosDates = []
missingTemps = []
missingDates = []

timeTemp = OrderedDict()

flike = StringIO.StringIO(pullAsos('2017','CHO', 'tmpf'))
next(csv.reader(flike))
for row in csv.reader(flike):
	if row[2] != 'M':
		timeTemp[datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M")] = float(row[2])
	elif row[1][14:] in ['00','15','30','45']:
		#print(row[1])
		#print(row[2])
		timeTemp[datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M")] = np.nan

#Interpolate data 
pdTemps = pd.DataFrame(timeTemp.items(), columns=['date', 'temperature'])
realTemp = pd.DataFrame(timeTemp.items(), columns=['date', 'temperature'])
realTemp.dropna(inplace=True)
print(pdTemps)
pdTemps.interpolate(inplace=True, limit_direction='both')
print(pdTemps)
fifteenMinuteTimestamps = pd.date_range(start='1/1/2017', end='1/1/2018', closed='left', freq='15T')
print(fifteenMinuteTimestamps)
#Filter data set for 15 minute intervals with interpolated data
pdTemps = pdTemps[pdTemps['date'].isin(fifteenMinuteTimestamps)]
#pdTemps.set_index('date', inplace=True)

#Get a one day sample of temperature for testing
temp_regress = pdTemps[['temperature']][0:2976].values
#print((pdTemps.iloc[:,1]))
#print(pdTemps.loc['2017-3-1':'2017-3-2']['temperature'])

#for i in timeTemp:
#	if timeTemp[i] == 'M':
#		missingDates.append(((datetime.datetime.strptime(i, "%Y-%m-%d %H:%M"))-datetime.datetime(2017,1,1)).total_seconds())
#	else:
#		asosTemps.append(float(timeTemp[i]))
#		asosDates.append(((datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M"))-datetime.datetime(2017,1,1)).total_seconds())



#missingTemps = np.interp(missingDates, asosDates, asosTemps)
#for i in range(100):
#	print(missingTemps[1])
#print(len(asosDates))
#print(len(missingDates))
#for i in range(len(missingDates)):
#	timeTemp[(datetime.datetime(2017,1,1)+datetime.timedelta(seconds=missingDates[i])).strftime("%Y-%m-%d %H:%M")] = missingTemps[i]
	#print((datetime.datetime(2017,1,1)+datetime.timedelta(seconds=missingDates[i])).strftime("%Y-%m-%d %H:%M"))
	#print(i)


#limit to one day of weather data for now
firstDayTemp = missingTemps[0:96]
#loadregressors=firstDayTemp.reshape(-1,1)
#print(loadregressors)
#print(list(timeTemp.keys())[96:192])
#print([x[1] for x in list(timeTemp.items())[30000:]])

testfig = tools.make_subplots(rows=1, cols=1)
testfig.append_trace(go.Scatter(y=pdTemps['temperature'], x=pdTemps['date'], name=('interped')),1,1)
testfig.append_trace(go.Scatter(y=realTemp['temperature'], x=realTemp['date'], name=('real'), mode = 'markers'),1,1)
#testfig.append_trace(go.Scatter(y=asosTemps[0:24], x=asosDates[0:24], name=('measured')),1,1)
#print(missingDates[0:96])
#print(asosDates[0:24])
#testfig.append_trace(go.Scatter(y=list(timeTemp.items())[96:192], x=list(timeTemp.keys())[96:192], name=('predicted')),2,1)
#testfig.append_trace(go.Scatter(y=asosTemps[24:48], x=asosDates[24:48], name=('measured')),2,1)
#print(missingDates[96:192])
#print(asosDates[24:48])
#testfig.append_trace(go.Scatter(y=list(timeTemp.items())[192:288], x=list(timeTemp.keys())[192:288], name=('predicted')),3,1)
#testfig.append_trace(go.Scatter(y=asosTemps[48:72], x=asosDates[48:72], name=('measured')),3,1)
#print(missingDates[192:288])
#print(asosDates[48:72])
plot(testfig)

#CSSS run CSSS algo for individual home scenario
sdmod0 = SolarDisagg.SolarDisagg_IndvHome(netloads=netload, solarregressors=solarproxy, loadregressors=loadregressors)
sdmod0.constructSolve()

#Create subplots in plotly
xaxis = [i for i in range(360)]
#fig = tools.make_subplots(rows=5, cols=1)

#plot weather and solar canary
#fig.append_trace(go.Scatter(y=firstDayTemp, x=xaxis, name=('Weather')),1,1)
#fig.append_trace(go.Scatter(y=np.array([item for sublist in solarproxy for item in sublist]), x=xaxis, name=('Solar Canary')),2,1)

#plot household loads and solar
#for i, model in enumerate(sdmod0.models):
#	if model != 'AggregateLoad':
#		solarArray = np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist])
#		print(solarArray)
#		disaggLoad = (sdmod0.netloads[str(i)] - solarArray)
#		fig.append_trace(go.Scatter(y=sdmod0.netloads[str(i)], x=xaxis, name=('Measured Load ' + str(i))),i+3,1)
#		fig.append_trace(go.Scatter(y=disaggLoad, x=xaxis, name=('Disaggregated Load (Actual) ' + str(i))),i+3,1)
#		fig.append_trace(go.Scatter(y=np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist]), x=xaxis, name=('Predicted solar ' + str(i))),i+3,1)

#plot(fig)
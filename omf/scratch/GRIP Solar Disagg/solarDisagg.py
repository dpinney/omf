# TODO: see slides.

#import warnings
#warnings.filterwarnings("ignore")

import csv
import matplotlib.pyplot as plt
import numpy as np
import StringIO
import datetime

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

flike = StringIO.StringIO(pullAsos('2017','CHO', 'tmpf'))
next(csv.reader(flike))
for row in csv.reader(flike):
	if row[2] == 'M' and row[1][14:] in ['00','15','30','45'] :
		missingDates.append(((datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M"))-datetime.datetime(2017,1,1)).total_seconds())
	elif row[2] != 'M':
		asosDates.append(((datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M"))-datetime.datetime(2017,1,1)).total_seconds())
		asosTemps.append(float(row[2]))

missingTemps = np.interp(missingDates, asosDates, asosTemps)

#limit to one day of weather data for now
firstDayTemp = missingTemps[360:720]
loadregressors=firstDayTemp.reshape(-1,1)

#CSSS run CSSS algo for individual home scenario
sdmod0 = SolarDisagg.SolarDisagg_IndvHome(netloads=netload, solarregressors=solarproxy, loadregressors=loadregressors)
sdmod0.constructSolve()

#Create subplots in plotly
xaxis = [i for i in range(360)]
fig = tools.make_subplots(rows=3, cols=1)

for i, model in enumerate(sdmod0.models):
	if model != 'AggregateLoad':
		solarArray = np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist])
		disaggLoad = (sdmod0.netloads[str(i)] - solarArray)
		fig.append_trace(go.Scatter(y=sdmod0.netloads[str(i)], x=xaxis, name=('Measured Load' + str(i))),i+1,1)
		fig.append_trace(go.Scatter(y=disaggLoad, x=xaxis, name=('Disaggregated Load (Actual)' + str(i))),i+1,1)
		fig.append_trace(go.Scatter(y=np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist]), x=xaxis, name=('Predicted solar' + str(i))),i+1,1)

plot(fig)
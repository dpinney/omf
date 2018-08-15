# TODO: see slides.
import csv
import matplotlib.pyplot as plt
import numpy as np

from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly import tools
import plotly.graph_objs as go

#import SolarDisagg
#import newcsss
#import SolarDisagg2

#import etcss
import CSSS.csss.SolarDisagg as SolarDisagg

meterData = []


#csv reader example
netload_csv = []
with open('load_data.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		netload_csv.append(row)
netload = np.array(netload_csv)

solarproxy_csv = []
with open('solar_proxy.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		solarproxy_csv.append(row)
solarproxy = np.array(solarproxy_csv) 

loadregressors_csv = []
with open('weather_regress.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		loadregressors_csv.append(row)
loadregressors = np.array(loadregressors_csv) 

sdmod0 = SolarDisagg.SolarDisagg_IndvHome(netloads=netload, solarregressors=solarproxy, loadregressors=loadregressors)
sdmod0.constructSolve()
print(type(sdmod0.modelcounter))

#Set up plots
f, axes = plt.subplots(3, 1, sharey=True, sharex=True)

#aggregate = []
#for i in range(sdmod0.modelcounter):
#	aggregate.append(sum([x[i] for x in meterData]))

for i, model in enumerate(sdmod0.models):
	if sdmod0.models[model]['name'] != 'AggregateLoad':
		#print(type(sdmod0.models[model]['source'].value))
		#print(type(sdmod0.netloads[str(i)]))
		solarArray = np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist])
		disaggLoad = (sdmod0.netloads[str(i)] - solarArray)
		axes[i].plot(sdmod0.netloads[str(i)], label=('net load' + str(i)))
		axes[i].plot(disaggLoad, label=('meter' + str(i)))
		axes[i].plot(solarArray, label=('solar' + str(i)))
		axes[i].legend()

plt.show()

#plotly testing
#plotlyData = []
xaxis = [i for i in range(360)]
fig = tools.make_subplots(rows=3, cols=1)
fig.print_grid

for i, model in enumerate(sdmod0.models):
	if model != 'AggregateLoad':
		solarArray = np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist])
		disaggLoad = (sdmod0.netloads[str(i)] - solarArray)
		fig.append_trace(go.Scatter(y=sdmod0.netloads[str(i)], x=xaxis, name=('net load' + str(i))),i+1,1)
		fig.append_trace(go.Scatter(y=disaggLoad, x=xaxis, name=('meter' + str(i))),i+1,1)
		fig.append_trace(go.Scatter(y=np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist]), x=xaxis, name=('solar' + str(i))),i+1,1)

plot(fig)
# TODO: see slides.
import csv
import matplotlib.pyplot as plt
import numpy as np

from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly import tools
import plotly.graph_objs as go

#import SolarDisagg
import newcsss
import SolarDisagg2

meterData = []


#csv reader example
netload_csv = []
with open('load_data.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		netload_csv.append(row)
netload = np.array(netload_csv)

solarproxy_csv = []
with open('solar_data.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		solarproxy_csv.append(row)
solarproxy = np.array(solarproxy_csv) 

loadregressors = np.array([55,55,56,57,59,61,63,65,67,70,73,75,75,74,74,72,71,70,68,66,63,61,59,57])

sdmod0 = SolarDisagg2.SolarDisagg_IndvHome(netloads=netload, solarregressors=solarproxy, loadregressors=loadregressors)
sdmod0.constructSolve()
print(type(sdmod0.modelcounter))

#Set up plots
f, axes = plt.subplots(4, 1, sharey=True, sharex=True)

#aggregate = []
#for i in range(sdmod0.modelcounter):
#	aggregate.append(sum([x[i] for x in meterData]))

for i, model in enumerate(sdmod0.models):
	print(sdmod0.models[model]['source'].value)
	axes[i].plot(sdmod0.models[model]['source'].value)

plt.show()

#plotly testing
#plotlyData = []
xaxis = [i for i in range(24)]
fig = tools.make_subplots(rows=4, cols=1)
fig.print_grid

for i, model in enumerate(sdmod0.models):
	if model != 'AggregateLoad':
		fig.append_trace(go.Scatter(y=sdmod0.netloads[str(i)], x=xaxis),i+1,1)
	#print()
	fig.append_trace(go.Scatter(y=[item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist], x=xaxis),i+1,1)

plot(fig)
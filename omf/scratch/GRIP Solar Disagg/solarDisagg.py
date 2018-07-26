# TODO: see slides.
import csv
import matplotlib.pyplot as plt
import numpy as np

from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
from plotly import tools
import plotly.graph_objs as go

meterData = []

#csv reader example
with open('testing.csv', 'rb') as csvfile:
	csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
	for row in csvreader:
		meterData.append(row)

#Set up plots
f, axes = plt.subplots(len(meterData), 1, sharey=True, sharex=True)

aggregate = []
for i in range(len(meterData[0])):
	aggregate.append(sum([x[i] for x in meterData]))

for i in range(len(meterData)):
	axes[i].plot(meterData[i])
	axes[i].plot(aggregate)

plt.show()

#plotly testing
#plotlyData = []
xaxis = [i for i in range(10)]
fig = tools.make_subplots(rows=len(meterData), cols=1)
fig.print_grid

for i in range(len(meterData)):
	#plotlyData.append(go.Scatter(y=meterData[i], x=[i for i in range(10)]))
	print(i)
	fig.append_trace(go.Scatter(y=meterData[i], x=xaxis),i+1,1)

plot(fig)
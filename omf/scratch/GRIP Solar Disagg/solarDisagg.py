# TODO: see slides.
import csv
import matplotlib.pyplot as plt
import numpy as np

from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
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
plot([go.Scatter(x=[1, 2, 3], y=[3, 1, 6])])
# imports ---------------------------------------------------------------------

from datetime import datetime

import pathlib, csv, time
import numpy as np

import plotly.graph_objs as go
# comment this out to let plotly pick
# mine defaulted to browser and printed out 
# a bunch of garbage to the terminal so i use firefox to avoid that
import plotly.io as pio
pio.renderers.default = "firefox"
import matplotlib.pyplot as plt

# constants -------------------------------------------------------------------

DATE_FORMAT = '%Y-%m-%d'
START_DATE = '2012-01-01'
PLOT_DATE = '2012-01-01'
PLOT_HOUSE_INDEX = 1 # set to 'average' to see average error across all houses

TIME_SAMPLES_PER_HOUR = 4
TIME_CHUNK = 24
PLOT_TIME_WINDOW_IN_HOURS = 24

NUM_ROWS_PER_FILE = 35136
NUM_HOUSE_TYPES = 48
NUM_INSTANCES = 2
TEST_FRAC = 0.5

DATA_DIR = str( pathlib.Path(__file__).parent.absolute() ) + '/../data/'
DATA_SUBFOLDER = DATA_DIR + str(NUM_HOUSE_TYPES) + 'Types' + \
	str(NUM_INSTANCES) + 'HousesPerType'
IN_FILENAME = DATA_SUBFOLDER+'/results'+str(TIME_CHUNK)+'timeChunkEasyFeatures.csv'

DELIMITER = ','

APPLIANCES = ['heating_demand',
	'cooling_demand',
	'ev_charger',
	'hvac',
	'responsive',
	'unresponsive',
	'waterheater']

# functions -------------------------------------------------------------------

def plotWithBounds(fig, x, y, upper, lower, color, name='', title='', \
	xAxisLabel='', yAxisLabel=''):
	
	alphaValStart = color.rfind(',')+1
	transparentColor = color[:alphaValStart]+'0.2)'
	transparent = color[:alphaValStart]+'0)'

	trace1 = go.Scatter(
	    x=x,
	    y=upper,
	    fillcolor=transparentColor,
	    line=dict(color=transparent),
	    showlegend=False,
	    name=name,
	    fill='none'
	)

	trace2 = go.Scatter(
	    x=x,
	    y=lower,
	    fillcolor=transparentColor,
	    line=dict(color=transparent),
	    showlegend=False,
	    name=name,
	    fill='tonexty'
	)

	trace3 = go.Scatter(
	    x=x,
	    y=y,
	    line=dict(color=color),
	    mode='lines',
	    name=name,
	)

	layout = go.Layout(
	
		title= title,
	    paper_bgcolor='rgb(255,255,255)',
	    plot_bgcolor='rgb(229,229,229)',
	
	    xaxis=dict(
	        gridcolor='rgb(255,255,255)',
	        showgrid=True,
	        showline=False,
	        showticklabels=True,
	        tickcolor='rgb(127,127,127)',
	        ticks='outside',
	        zeroline=False,
	        title=xAxisLabel
	    ),
	
	    yaxis=dict(
	        gridcolor='rgb(255,255,255)',
	        # range = rangeY,
	        showgrid=True,
	        showline=False,
	        showticklabels=True,
	        tickcolor='rgb(127,127,127)',
	        ticks='outside',
	        zeroline=False,
	        title=yAxisLabel
	    ),
	
	)

	fig.add_trace(trace1)
	fig.add_trace(trace2)
	fig.add_trace(trace3)
	fig.update_layout(layout)

# read file and compute metrics -----------------------------------------------

rowNum = 0
start = time.time()

# read file and populate the truth and predicted arrays
pred,true = [],[]
with open(IN_FILENAME, 'r') as infile:
	
	reader = csv.reader( infile, delimiter=DELIMITER )
	for row in reader:

		if rowNum == 0:
			splitIndex = int( (len(row)-1) / 2 )
			numAppliances = splitIndex
			if TIME_CHUNK > 0:
				numAppliances = int( splitIndex / \
					(TIME_CHUNK*TIME_SAMPLES_PER_HOUR) )
			print('number of appliances', numAppliances)

		currentPred = row[:splitIndex]
		currentTrue = row[splitIndex+1:]

		true.append(currentTrue)
		pred.append(currentPred)

		rowNum+=1
		# if (rowNum % 1000) == 0:
		# 	end = time.time()
		# 	print('loaded till line',rowNum, 'in', end-start, 'secs')

# make sure everything is a numpy array of floats
true = np.array(true,dtype='float64')
pred = np.array(pred,dtype='float64')
pred[pred<0] = 0
print('\ntrue shape', true.shape)

# reshape true and predicted to be (time x houses) by appliance
true = np.reshape(true, (true.shape[0],-1,numAppliances), order='F')
pred = np.reshape(pred, (true.shape[0],-1,numAppliances), order='F')
print('true shape', true.shape)
true = np.transpose(true, (1,0,2))
pred = np.transpose(pred, (1,0,2))
print('true shape', true.shape)
true = np.reshape(true, (-1,numAppliances), order='F')
pred = np.reshape(pred, (-1,numAppliances), order='F')
print('true shape', true.shape)

# compute error
error = pred-true

# # plot data
# hNum = 0
# hIndex = hNum*NUM_ROWS_PER_FILE
# print(hIndex)
# for applianceNum in range(numAppliances):
# 	plotY = true[:96,applianceNum]
# 	plotX = np.arange(len(plotY))
# 	fig = go.Figure(data=go.Scatter(x=plotX, y=plotY))
# 	fig.update_layout( \
# 		title='all test houses, all time points for appliance ' + \
# 		APPLIANCES[applianceNum] )
# 	fig.show()
# raise Exception('')

# compute error as a percent of max load
trueMaxByApp = true.max(axis=0)
trueMaxByApp = np.broadcast_to(trueMaxByApp,error.shape)
# error = 100*np.divide(error,trueMaxByApp) 

# compute metrics
errorMean = error.mean()
errorStd = error.std()
errorMeanIgnoreHVACDemand = error[:,2:].mean()
errorStdIgnoreHVACDemand = error[:,2:].std()
errorMeanByApp = error.mean(axis=0)
errorStdByApp = error.std(axis=0)

print()
print( 'results mean:', \
	list(errorMeanByApp)+list([errorMean])+list([errorMeanIgnoreHVACDemand]) )
print( 'results std:', \
	list(errorStdByApp)+list([errorStd])+list([errorStdIgnoreHVACDemand]) )
print()

# reshape data into houses x time x app
numHouses = int(NUM_HOUSE_TYPES*NUM_INSTANCES*TEST_FRAC)
true = np.reshape(true, (-1,numHouses,numAppliances), order='F')
pred = np.reshape(pred, (-1,numHouses,numAppliances), order='F')
error = np.reshape(error, (-1,numHouses,numAppliances), order='F')
print('true shape', true.shape)

# # plot data
# hNum = 2
# hIndex = hNum*NUM_ROWS_PER_FILE
# print(hIndex)
# for applianceNum in range(numAppliances):
# 	plotY = true[:96,hNum,applianceNum]
# 	plotX = np.arange(len(plotY))
# 	fig = go.Figure(data=go.Scatter(x=plotX, y=plotY))
# 	fig.update_layout( \
# 		title='all test houses, all time points for appliance ' + \
# 		APPLIANCES[applianceNum] )
# 	fig.show()
# raise Exception('')


if PLOT_HOUSE_INDEX =='average':

	# average data across houses
	trueMeanByHouse = true.mean(axis=1)
	predMeanByHouse = pred.mean(axis=1)
	errorMeanByHouse = error.mean(axis=1)
	# get std
	trueStdByHouse = true.std(axis=1)
	predStdByHouse = pred.std(axis=1)
	errorStdByHouse = error.std(axis=1)

else:

	trueMeanByHouse = np.squeeze(true[:,PLOT_HOUSE_INDEX,:])
	predMeanByHouse = np.squeeze(pred[:,PLOT_HOUSE_INDEX,:])
	errorMeanByHouse = np.squeeze(error[:,PLOT_HOUSE_INDEX,:])
	trueStdByHouse = np.zeros(trueMeanByHouse.shape)
	predStdByHouse = np.zeros(predMeanByHouse.shape)
	errorStdByHouse = np.zeros(errorMeanByHouse.shape)

# reshape data into days x time sample x app
timeWindow = TIME_SAMPLES_PER_HOUR*PLOT_TIME_WINDOW_IN_HOURS

trueMeanByHouse = np.reshape(trueMeanByHouse, \
	(timeWindow,-1,numAppliances), order='F')
trueMeanByHouse = np.transpose( trueMeanByHouse, (1,0,2) )

predMeanByHouse = np.reshape(predMeanByHouse, \
	(timeWindow,-1,numAppliances), order='F')
predMeanByHouse = np.transpose( predMeanByHouse, (1,0,2) )

errorMeanByHouse = np.reshape(errorMeanByHouse, \
	(timeWindow,-1,numAppliances), order='F')
errorMeanByHouse = np.transpose( errorMeanByHouse, (1,0,2) )

trueStdByHouse = np.reshape(trueStdByHouse, \
	(timeWindow,-1,numAppliances), order='F')
trueStdByHouse = np.transpose( trueStdByHouse, (1,0,2) )

predStdByHouse = np.reshape(predStdByHouse, \
	(timeWindow,-1,numAppliances), order='F')
predStdByHouse = np.transpose( predStdByHouse, (1,0,2) )

errorStdByHouse = np.reshape(errorStdByHouse, \
	(timeWindow,-1,numAppliances), order='F')
errorStdByHouse = np.transpose( errorStdByHouse, (1,0,2) )

# plot data as stacked bars ---------------------------------------------------

startDate = datetime.strptime(START_DATE, DATE_FORMAT)
plotDate = datetime.strptime(PLOT_DATE, DATE_FORMAT)
plotDayIndex = (plotDate - startDate).days
print('plot data', plotDate, 'plotting day', plotDayIndex)

if PLOT_HOUSE_INDEX !='average':

	barWidth = 1
	legendItems, legendLabels = [],[]
	trueMeansPreviousAppliance = 0
	trueStdPreviousAppliance = 0
	predMeansPreviousAppliance = 0
	predStdPreviousAppliance = 0

	for applianceNum in range(2,numAppliances):

		trueMeansCurrentAppliance = \
			trueMeanByHouse[plotDayIndex,:,applianceNum]
		trueMeansCurrentAppliance = np.reshape( trueMeansCurrentAppliance, \
			(-1,TIME_SAMPLES_PER_HOUR) )
		trueStdCurrentAppliance = trueMeansCurrentAppliance.std(axis=1)
		trueMeansCurrentAppliance = trueMeansCurrentAppliance.mean(axis=1)
		trueInd = np.arange(0,3*len(trueMeansCurrentAppliance),3)

		predMeansCurrentAppliance = \
			predMeanByHouse[plotDayIndex,:,applianceNum]
		predMeansCurrentAppliance = np.reshape( predMeansCurrentAppliance, \
			(-1,TIME_SAMPLES_PER_HOUR) )
		predStdCurrentAppliance = predMeansCurrentAppliance.std(axis=1)
		predMeansCurrentAppliance = predMeansCurrentAppliance.mean(axis=1)
		predInd = np.arange(1,3*len(predMeansCurrentAppliance),3)

		if applianceNum == 2:
			truePlot = plt.bar(trueInd, trueMeansCurrentAppliance, barWidth, \
				yerr=trueStdCurrentAppliance, \
				capsize=5,error_kw={'alpha':0.5})
			predPlot = plt.bar(predInd, predMeansCurrentAppliance, barWidth, \
				yerr=predStdCurrentAppliance, \
				capsize=5,error_kw={'alpha':0.5})

		else:
			truePlot = plt.bar(trueInd, trueMeansCurrentAppliance, barWidth, \
				bottom=trueMeansPreviousAppliance, \
				yerr=trueStdPreviousAppliance, \
				capsize=5,error_kw={'alpha':0.5})
			predPlot = plt.bar(predInd, predMeansCurrentAppliance, barWidth, \
				bottom=predMeansPreviousAppliance, \
				yerr=predStdPreviousAppliance, \
				capsize=5,error_kw={'alpha':0.5})

		trueMeansPreviousAppliance = np.add(trueMeansPreviousAppliance, \
			trueMeansCurrentAppliance)
		trueStdPreviousAppliance = np.add(trueStdPreviousAppliance, \
			trueStdCurrentAppliance)
		predMeansPreviousAppliance = np.add(predMeansPreviousAppliance, \
			predMeansCurrentAppliance)
		predStdPreviousAppliance = np.add(predStdPreviousAppliance, \
			predStdCurrentAppliance)

		legendItems.append(truePlot[0])
		legendItems.append(predPlot[0])
		legendLabels.append('true ' + APPLIANCES[applianceNum])
		legendLabels.append('predicted ' + APPLIANCES[applianceNum])


	plt.legend(legendItems,legendLabels, \
		bbox_to_anchor=(1.05, 1.0), loc='upper left')
	plt.xticks(np.arange(1,len(trueInd)*3,3), np.arange(len(trueInd)) )
	plt.xlabel('Hour of Day')
	plt.ylabel('Watts')
	plt.tight_layout()
	plt.show()

# plot data as individual appliances ------------------------------------------

plotX = np.arange(trueMeanByHouse.shape[1])
for applianceNum in range(numAppliances):
	
	truePlotY = trueMeanByHouse[plotDayIndex,:,applianceNum]
	trueUpper = truePlotY + trueStdByHouse[plotDayIndex,:,applianceNum]
	trueLower = truePlotY - trueStdByHouse[plotDayIndex,:,applianceNum]

	predPlotY = predMeanByHouse[plotDayIndex,:,applianceNum]
	predUpper = predPlotY + predStdByHouse[plotDayIndex,:,applianceNum]
	predLower = predPlotY - predStdByHouse[plotDayIndex,:,applianceNum]

	errorPlotY = errorMeanByHouse[plotDayIndex,:,applianceNum]
	errorUpper = errorPlotY + errorStdByHouse[plotDayIndex,:,applianceNum]
	errorLower = errorPlotY - errorStdByHouse[plotDayIndex,:,applianceNum]

	# plot truth vs prediction by appliance
	fig = go.Figure()
	title = 'truth vs prediction for appliance ' + APPLIANCES[applianceNum]
	plotWithBounds(fig, plotX, truePlotY, trueUpper, trueLower, \
		'rgba(255,0,0,1)', name='truth')
	plotWithBounds(fig, plotX, predPlotY, predUpper, predLower, \
		'rgba(0,0,255,1)', name='predicted', title=title, \
		xAxisLabel = '15 minute sampleNum', yAxisLabel='watts')
	fig.show()

	# plot error by appliance
	fig2 = go.Figure()
	title = 'error for appliance ' + APPLIANCES[applianceNum]
	plotWithBounds(fig2, plotX, errorPlotY, errorUpper, errorLower, \
		'rgba(0,0,255,1)', name='error', title=title, \
		xAxisLabel = '15 minute sampleNum', yAxisLabel='watts')
	fig2.show()

# compute and display progress
end = time.time()
print('total elapsed time', end-start, 'secs')
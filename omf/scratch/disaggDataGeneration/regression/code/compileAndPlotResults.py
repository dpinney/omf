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

# constants -------------------------------------------------------------------

DATE_FORMAT = '%Y-%m-%d'
START_DATE = '2012-01-01'
PLOT_DATE = '2012-01-10'

TIME_SAMPLES_PER_HOUR = 4
TIME_CHUNK = 24

NUM_ROWS_PER_FILE = 35136
NUM_HOUSE_TYPES = 48
NUM_INSTANCES = 2
TEST_FRAC = 0.5

DATA_DIR = str( pathlib.Path(__file__).parent.absolute() ) + '/../data/'
DATA_SUBFOLDER = DATA_DIR + str(NUM_HOUSE_TYPES) + 'Types' + \
	str(NUM_INSTANCES) + 'HousesPerType'
IN_FILENAME = DATA_SUBFOLDER+'/results'+str(TIME_CHUNK)+'timeChunk.csv'

DELIMITER = ','

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
		if (rowNum % 1000) == 0:
			end = time.time()
			print('loaded till line',rowNum, 'in', end-start, 'secs')

# make sure everything is a numpy array of floats
true = np.array(true,dtype='float64')
pred = np.array(pred,dtype='float64')
print('\ntrue shape', true.shape)

# reshape true and predicted to be (time x houses) by appliance
true = np.reshape(true, (-1,numAppliances), order='F')
pred = np.reshape(pred, (-1,numAppliances), order='F')
error = pred-true
print('true shape', true.shape)

# compute error as a percent of max load
trueMaxByApp = true.max(axis=0)
print('trueMax shape', trueMaxByApp.shape)
print('trueMax', trueMaxByApp)
trueMaxByApp = np.broadcast_to(trueMaxByApp,error.shape)
print('trueMax shape', trueMaxByApp.shape)
error = 100*np.divide(error,trueMaxByApp) 
print('error shape', error.shape)
print('error', error)

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
true = np.reshape(true, (NUM_HOUSE_TYPES,-1,numAppliances), order='F')
pred = np.reshape(pred, (NUM_HOUSE_TYPES,-1,numAppliances), order='F')
error = np.reshape(error, (NUM_HOUSE_TYPES,-1,numAppliances), order='F')
print('true shape', true.shape)

# average data across houses
trueMeanByHouse = true.mean(axis=0)
predMeanByHouse = pred.mean(axis=0)
errorMeanByHouse = error.mean(axis=0)
# get std
trueStdByHouse = true.std(axis=0)
predStdByHouse = pred.std(axis=0)
errorStdByHouse = error.std(axis=0)
print('true shape', true.shape)

# reshape data into days x time sample x app
trueMeanByHouse = np.reshape(trueMeanByHouse, \
	(-1,TIME_SAMPLES_PER_HOUR*24,numAppliances), order='F')
predMeanByHouse = np.reshape(predMeanByHouse, \
	(-1,TIME_SAMPLES_PER_HOUR*24,numAppliances), order='F')
errorMeanByHouse = np.reshape(errorMeanByHouse, \
	(-1,TIME_SAMPLES_PER_HOUR*24,numAppliances), order='F')
trueStdByHouse = np.reshape(trueStdByHouse, \
	(-1,TIME_SAMPLES_PER_HOUR*24,numAppliances), order='F')
predStdByHouse = np.reshape(predStdByHouse, \
	(-1,TIME_SAMPLES_PER_HOUR*24,numAppliances), order='F')
errorStdByHouse = np.reshape(errorStdByHouse, \
	(-1,TIME_SAMPLES_PER_HOUR*24,numAppliances), order='F')
print('true shape', trueMeanByHouse.shape)

# plot data ---------------------------------------------------------------

startDate = datetime.strptime(START_DATE, DATE_FORMAT)
plotDate = datetime.strptime(PLOT_DATE, DATE_FORMAT)
plotDayIndex = (plotDate - startDate).days
print(plotDayIndex)

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

	# print truth vs prediction by appliance
	fig = go.Figure()
	title = 'truth vs prediction for appliance' + str(applianceNum)
	plotWithBounds(fig, plotX, truePlotY, trueUpper, trueLower, \
		'rgba(255,0,0,1)', name='truth')
	plotWithBounds(fig, plotX, predPlotY, predUpper, predLower, \
		'rgba(0,0,255,1)', name='predicted', title=title, \
		xAxisLabel = '15 minute sampleNum', yAxisLabel='watts')
	fig.show()

	# print error by appliance
	fig2 = go.Figure()
	title = 'error for appliance' + str(applianceNum)
	plotWithBounds(fig2, plotX, errorPlotY, errorUpper, errorLower, \
		'rgba(0,0,255,1)', name='error', title=title, \
		xAxisLabel = '15 minute sampleNum', yAxisLabel='percent max load')
	fig2.show()

# compute and display progress
end = time.time()
print('total elapsed time', end-start, 'secs')
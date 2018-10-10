''' A model skeleton for future models: Calculates the sum of two integers. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, csv, requests
import multiprocessing
from os.path import join as pJoin
from jinja2 import Template
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

#SolarDisagg imports
import numpy as np
import scipy
import StringIO
import datetime
from collections import OrderedDict

# OMF imports
sys.path.append(__neoMetaModel__._omfDir)
from omf.weather import pullAsos
from omf.solvers import CSSS
import CSSS.csss.SolarDisagg as SolarDisagg
from bs4 import BeautifulSoup

# Model metadata:
modelName, template = metadata(__file__)
hidden = False

def work(modelDir, inputDict):
	import pandas as pd

	#plotly imports
	import plotly
	from plotly import __version__
	from plotly.offline import download_plotlyjs, plot
	from plotly import tools
	import plotly.graph_objs as go
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	outData = {}		
	# Model operations goes here.

	#read measured load from csv file
	meterNames = []
	netload_csv = []
	with open(pJoin(modelDir, inputDict['meterFileName']),'w') as loadTempFile:
		loadTempFile.write(inputDict['meterData'])
	try:
		with open(pJoin(modelDir, inputDict['meterFileName']), 'r') as csvfile:
			csvreader = csv.reader(csvfile, delimiter=',')
			meterNames = next(csvreader)
			csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
			for row in csvreader:
				netload_csv.append(row)
	except:
		errorMessage = 'CSV file is incorrect format.'
		raise Exception(errorMessage)
	netload = np.array(netload_csv)

	#read the solar proxy from csv file
	solarproxy_csv = []
	with open(pJoin(modelDir, inputDict['solarFileName']),'w') as loadTempFile:
		loadTempFile.write(inputDict['solarData'])
	try:
		with open(pJoin(modelDir, inputDict['solarFileName']), 'r') as csvfile:
			csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
			for row in csvreader:
				solarproxy_csv.append(row)
	except:
		errorMessage = "CSV file is incorrect format."
		raise Exception(errorMessage)
	solarproxy = np.array(solarproxy_csv)

	#Gather weather data from asos and interpolate for 15 minute intervals
	timeTemp = OrderedDict()

	#Uses default weather data for testing
	#with open(pJoin(modelDir,'weather_data_uploaded.csv'),'w') as loadTempFile:
	#	loadTempFile.write(inputDict['weatherData'])

	#Pulling data from ASOS
	startDate = datetime.datetime.strptime(inputDict.get("year"), "%Y-%m-%d")
	#Use 90 day interval for now
	endDate = datetime.datetime.strftime(startDate + datetime.timedelta(days=90), "%Y-%m-%d")
	flike = StringIO.StringIO(pullAsosRevised(inputDict.get("year"),inputDict.get("asos"), 'tmpf', end=endDate))
	with open(pJoin(modelDir,inputDict['weatherFileName']),'w') as loadTempFile:
		csvwriter = csv.writer(loadTempFile, delimiter=',')
		next(csv.reader(flike))
		for row in csv.reader(flike):
			csvwriter.writerow(row)
	try:
		with open(pJoin(modelDir,inputDict['weatherFileName']), 'r') as csvfile:
			#next(csv.reader(flike))
			for row in csv.reader(csvfile):
				if row[2] != 'M':
					timeTemp[datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M")] = float(row[2])
	except:
		errorMessage = "CSV file is incorrect format."
		raise Exception(errorMessage)

	#Dataframe of temperature data
	realTemps = pd.DataFrame(timeTemp.items(), columns=['date', 'temperature'])
	realTemps['date'] = pd.to_datetime(realTemps['date'], utc=True)
	realTemps.set_index('date', inplace=True)
	#realTemps.to_csv('output.csv')

	#Filter data set for 15 minute intervals with interpolated data

	#Use this to calculate end date when full year is pulled
	#startDate = datetime.datetime.strptime(inputDict.get("year"), "%Y-%m-%d")
	#Use 90 day interval for now
	#endDate = datetime.datetime.strftime(startDate + datetime.timedelta(days=90), "%Y-%m-%d")
	#endYear = str(int(datetime.datetime.strftime(startDate, "%Y"))+1)
	#endMonth = datetime.datetime.strftime(startDate, "%m")
	#endDay = datetime.datetime.strftime(startDate, "%d")
	#endDate = endYear + '-' + endMonth + '-' + endDay
	
	#end date is manually set for time being before addressing year issue
	fifteenMinuteTimestamps = pd.date_range(start=inputDict.get("year"), end=endDate, closed='left', freq='15T', tz='UTC')
	fifteenMinuteTimestamps = pd.DataFrame(index=fifteenMinuteTimestamps, columns=['temperature']).fillna(np.nan)
	fifteenMinuteTimestamps.index.rename('date', inplace=True)
	#fifteenMinuteTimestamps.to_csv("true.csv")

	#combine asos with 15 minute intervals and interpolate
	pdTemps = realTemps.append(fifteenMinuteTimestamps)
	pdTemps = pdTemps.sort_index()
	pdTemps = pdTemps[~pdTemps.index.duplicated(keep='first')]
	pdTemps.interpolate(inplace=True, limit_direction='both')
	pdTemps = pdTemps[pdTemps.index.isin(fifteenMinuteTimestamps.index)]

	#create load regressor from weather data in correct format as nparray
	loadregressors = pdTemps[['temperature']].values
	def createTempInput(temp, size, minTemp=None, maxTemp=None, intercept = False):
		if (minTemp is None):
			minTemp=min(temp)
		if maxTemp is None:
			maxTemp=max(temp)
		minBound=int(np.floor(minTemp / size)) * size
		maxBound=int(np.floor(maxTemp / size)) * size + size

		rangeCount = int((maxBound-minBound) / size)
		result = np.zeros((len(temp), rangeCount+intercept))
		t = 0
		for elem in temp:
			fullRanges = min( int(np.floor((elem-minBound) / size)), rangeCount-1)
			fullRanges = max(0, fullRanges)
			bound      = (minBound+fullRanges*size)
			lastRange  = elem-bound
			res        = [size for elem in range(fullRanges)]
			res.append(lastRange)
			for var in range(rangeCount-fullRanges-1):
				res.append(0)
			if intercept:
				res.append(1)  ## Include an intercept

			result[t,:] = np.array(res)
			t +=1
		return minTemp, maxTemp,result

	#hod = pd.Series([t for t in pdTemps['date']])
	#hod = pd.get_dummies(hod)
	#print(hod)

	#Waiting on algo update for tempregress 
	Tmin, Tmax, tempregress = createTempInput(pdTemps['temperature'], 20)
	loadregressors = tempregress
	#print(pdTemps['date'].values)
	#print(tempregress)

	#CSSS run CSSS algo for individual home scenario
	sdmod0 = SolarDisagg.SolarDisagg_IndvHome(netloads=netload, solarregressors=solarproxy, loadregressors=loadregressors, names=meterNames)
	#
	sdmod0.constructSolve()
	#sdmod0.fitTuneModels()

	#Create subplots in plotly
	fig = tools.make_subplots(rows=5, cols=1)

	weatherPlotData = []


	#plot weather and solar canary
	fig.append_trace(go.Scatter(y=pdTemps['temperature'], x=pdTemps.index, name=('Interpolated weather '), marker=dict(color='red'), legendgroup='weather'),1,1)

	interpWeatherPlotly = go.Scatter(y=pdTemps['temperature'], x=pdTemps.index, name=('Interpolated weather '), marker=dict(color='red'), legendgroup='weather')
	fig.append_trace(go.Scatter(y=realTemps['temperature'], x=realTemps.index, name=('Real weather data '), mode = 'markers', marker=dict(color='orange'), legendgroup='weather'),1,1)
	realWeatherPlotly = go.Scatter(y=realTemps['temperature'], x=realTemps.index, name=('Real weather data '), mode = 'markers', marker=dict(color='orange'))
	weatherPlotData = [interpWeatherPlotly, realWeatherPlotly]
	weatherPlotLayout = go.Layout(title='Temperature', legend=dict(x=0, y=1.2, orientation="h"), height=400, width=980)
	weatherPlotLayout['yaxis'].update(title='Fahrenheit')
	xaxis = [i for i in range(96)]
	fig.append_trace(go.Scatter(y=np.array([item for sublist in solarproxy for item in sublist]), x=pdTemps.index, name=('Solar Canary '), marker=dict(color='gold') ),2,1)
	solarPlotData = [go.Scatter(y=np.array([item for sublist in solarproxy for item in sublist]), x=pdTemps.index, name=('Solar Proxy'), marker=dict(color='gold'))]
	solarPlotLayout = go.Layout(title='Solar Proxy', showlegend=True, legend=dict(x=0, y=1.2, orientation="h"), height=400, width=980)
	solarPlotLayout['yaxis'].update(title='Watts')

	#plot net aggregate load 
	#print(sdmod0.models['AggregateLoad']['source'].value)
	#fig.append_trace(go.Scatter(y=np.array([item for sublist in sdmod0.models['AggregateLoad']['source'].value.tolist() for item in sublist]), x=pdTemps['date'], name=('Disaggregated Total Load')),3,1)
	#fig.append_trace(go.Scatter(y=sdmod0.aggregateSignal, x=pdTemps['date'], name=('Aggregate Total Load')),3,1)

	#plot household loads and solar
	meterPlot = []
	for i, model in enumerate(sdmod0.models):
		if model != 'AggregateLoad':
			#print(sdmod0.models[model]['source'].value)
			solarArray = np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist])
			disaggLoad = (sdmod0.netloads[model] - solarArray)
			fig.append_trace(go.Scatter(y=sdmod0.netloads[model], x=pdTemps.index, name=(str(model) + ': Measured Load'), marker=dict(color='green'), legendgroup=i),i+3,1)
			measuredLoad = go.Scatter(y=sdmod0.netloads[model], x=pdTemps.index, name=(str(model) + ': Measured Load'), marker=dict(color='green'))
			fig.append_trace(go.Scatter(y=disaggLoad, x=pdTemps.index, name=(str(model) + ': Disagreggated Load'), marker=dict(color='blue'), legendgroup=i),i+3,1)
			disaggregatedLoad = go.Scatter(y=disaggLoad, x=pdTemps.index, name=(str(model) + ': Disagreggated Load'), marker=dict(color='blue'))
			fig.append_trace(go.Scatter(y=np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist]), x=pdTemps.index, name=(str(model) + ': Actual Load'), marker=dict(color='yellow'), legendgroup=i),i+3,1)
			actualLoad = go.Scatter(y=np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist]), x=pdTemps.index, name=(str(model) + ': Actual Load'), marker=dict(color='yellow'))
			meterPlotLayout = go.Layout(title=str(model), legend=dict(x=0, y=1.2, orientation="h"), height=400, width=980)
			meterPlotLayout['yaxis'].update(title='Watts')
			meterPlot.append({'data': json.dumps([measuredLoad, disaggregatedLoad, actualLoad], cls=plotly.utils.PlotlyJSONEncoder), 'layout': json.dumps(meterPlotLayout, cls=plotly.utils.PlotlyJSONEncoder)})
			fig['layout']['yaxis' + str(i+3)].update(title='Watts')

	#plot the results
	fig['layout'].update(height=1500, width=900)
	#inlinePlot = plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')
	graphJSON = json.dumps(fig['data'], cls=plotly.utils.PlotlyJSONEncoder)
	layoutJSON = json.dumps(fig['layout'], cls=plotly.utils.PlotlyJSONEncoder)

	graphWeatherJSON = json.dumps(weatherPlotData, cls=plotly.utils.PlotlyJSONEncoder)
	layoutWeatherJSON = json.dumps(weatherPlotLayout, cls=plotly.utils.PlotlyJSONEncoder)
	graphSolarJSON = json.dumps(solarPlotData, cls=plotly.utils.PlotlyJSONEncoder)
	layoutSolarJSON = json.dumps(solarPlotLayout, cls=plotly.utils.PlotlyJSONEncoder)

	#soup = html.escape(str(BeautifulSoup(inlinePlot).find("div")))
	#soup2 = html.escape(str(BeautifulSoup(inlinePlot).find("script")))
	#print(soup)
	#print(soup2)

	loadLocations=[]
	with open(pJoin(modelDir, inputDict['latLonFileName']),'w') as loadTempFile:
		loadTempFile.write(inputDict['latLonData'])
	with open(pJoin(modelDir, inputDict['latLonFileName']), 'r') as csvfile:
		csvreader = csv.DictReader(csvfile, fieldnames=('netLoadName', 'netLoadLat', 'netLoadLon') , delimiter=',')
		for row in csvreader:
			loadLocations.append({'netLoadName': row['netLoadName'], 'netLoadLat': row['netLoadLat'], 'netLoadLon': row['netLoadLon']})

	outData['loadLocations'] = loadLocations

	#how to pass with escape chars
	outData['graphJSON'] = graphJSON
	outData['layoutJSON'] = layoutJSON
	outData['graphWeatherJSON'] = graphWeatherJSON
	outData['layoutWeatherJSON'] = layoutWeatherJSON
	outData['graphSolarJSON'] = graphSolarJSON
	outData['layoutSolarJSON'] = layoutSolarJSON
	outData['meterJSON'] = meterPlot
	#outData["plotlyOutput"] = html.escape(soup)
	#outData["scriptTag"] = html.escape(soup2)
	outData['year'] = inputDict.get('year')
	outData['meterNames'] = meterNames
	# Model operations typically ends here.
	# Stdout/stderr.
	outData['stdout'] = 'Success'
	outData['stderr'] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	meterDataFile = "load_data_three_month.csv"
	solarDataFile = "solar_proxy_three_month.csv"
	latLonDataFile = "lat_lon_data_plus.csv"
	weatherDataFile = "asos_three_month.csv"
	defaultInputs = {
		"user" : "admin",
		"modelType": modelName,
		"meterData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles",meterDataFile)).read(),
		"meterFileName": meterDataFile,
		"solarData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles",solarDataFile)).read(),
		"solarFileName": solarDataFile,
		"weatherData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles",weatherDataFile)).read(),
		"weatherFileName": weatherDataFile,
		"latLonData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles",latLonDataFile)).read(),
		"latLonFileName": latLonDataFile,
		"asos": "CHO",
		"year": "2017-01-01",
		"created":str(datetime.datetime.now())
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

#Revised asos pulling function to allow entering specific dates
def pullAsosRevised(start, station, datatype, end=None):
	'''This model pulls the hourly temperature for the specified year and ASOS station
	ASOS is the Automated Surface Observing System, a network of about 900 weater stations, they collect data at hourly intervals, they're run by NWS + FAA + DOD, and there is data going back to 1901 for at least some sites.
	This data is also known as METAR data, which is the name of the format its stored in.
	The year cannot be the current year.
	For ASOS station code: https://www.faa.gov/air_traffic/weather/asos/
	Note for USA stations (beginning with a K) you must NOT include the 'K'
	This model will output a folder path, open that path and you will find a csv file containing your data
	For years before 1998 there may or may not be any data, as such the datapull can fail for some years'''
	startDate = datetime.datetime.strptime(start, "%Y-%m-%d")
	startYear = datetime.datetime.strftime(startDate, "%Y")
	startMonth = datetime.datetime.strftime(startDate, "%m")
	startDay = datetime.datetime.strftime(startDate, "%d")
	if end is None:
		endYear = str(int(datetime.datetime.strftime(startDate, "%Y"))+1)
		endMonth = datetime.datetime.strftime(startDate, "%m")
		endDay = datetime.datetime.strftime(startDate, "%d")
	else:
		endDate = datetime.datetime.strptime(end, "%Y-%m-%d")
		endYear = datetime.datetime.strftime(endDate, "%Y")
		endMonth = datetime.datetime.strftime(endDate, "%m")
		endDay = datetime.datetime.strftime(endDate, "%d")
	url = ('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=' + station + '&data=' + datatype + '&year1=' + startYear + 
		'&month1='+ startMonth +'&day1=' + startDay + '&year2=' + endYear + '&month2=' + endMonth +'&day2=' + endDay + '&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=1&report_type=2')
	r = requests.get(url)
	data = r.text
	return data

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	renderAndShow(modelLoc)
	# # Run the model.
	runForeground(modelLoc)
	# # Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
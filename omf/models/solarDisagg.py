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
import pandas as pd

#plotly imports
import plotly
from plotly import __version__
from plotly.offline import download_plotlyjs, plot
from plotly import tools
import plotly.graph_objs as go

#folium imports
import folium
from folium.plugins import MarkerCluster

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
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	outData = {}		
	# Model operations goes here.

	#read measured load from csv file
	#print(inputDict)
	#print(type(inputDict))
	#print(json.dump(pJoin(modelDir,'load_data.csv')))
	print(inputDict.keys())
	meterNames = []
	netload_csv = []
	with open(pJoin(modelDir,'meter_data_uploaded.csv'),'w') as loadTempFile:
		loadTempFile.write(inputDict['meterData'])
	try:
		with open(pJoin(modelDir,'meter_data_uploaded.csv'), 'r') as csvfile:
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
	with open(pJoin(modelDir,'solar_data_uploaded.csv'),'w') as loadTempFile:
		loadTempFile.write(inputDict['solarData'])
	try:
		with open(pJoin(modelDir,'solar_data_uploaded.csv'), 'r') as csvfile:
			csvreader = csv.reader(csvfile, delimiter=',',quoting=csv.QUOTE_NONNUMERIC)
			for row in csvreader:
				solarproxy_csv.append(row)
	except:
		errorMessage = "CSV file is incorrect format."
		raise Exception(errorMessage)
	solarproxy = np.array(solarproxy_csv)

	#Gather weather data from asos and interpolate for 15 minute intervals
	timeTemp = OrderedDict()

	#flike = StringIO.StringIO(pullAsosRevised(inputDict.get("year"),inputDict.get("asos"), 'tmpf'))
	#next(csv.reader(flike))
	#for row in csv.reader(flike):
	#	if row[2] != 'M':
	#		timeTemp[datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M")] = float(row[2])
	#	elif row[1][14:] in ['00','15','30','45'] and row[2] =='M':
	#		timeTemp[datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M")] = np.nan
	#use cached weather data
	with open(pJoin(modelDir,'weather_data_uploaded.csv'),'w') as loadTempFile:
		loadTempFile.write(inputDict['weatherData'])
	try:
		with open(pJoin(modelDir,'weather_data_uploaded.csv'), 'r') as flike:
			#next(csv.reader(flike))
			for row in csv.reader(flike):
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
	fifteenMinuteTimestamps = pd.date_range(start='2017-1-1', end='2018-1-1', closed='left', freq='15T', tz='UTC')
	fifteenMinuteTimestamps = pd.DataFrame(index=fifteenMinuteTimestamps, columns=['temperature']).fillna(np.nan)
	fifteenMinuteTimestamps.index.rename('date', inplace=True)
	#print(fifteenMinuteTimestamps)
	#fifteenMinuteTimestamps.to_csv("true.csv")

	#combine asos with 15 minute intervals and interpolate
	pdTemps = realTemps.append(fifteenMinuteTimestamps)
	pdTemps = pdTemps.sort_index()
	pdTemps = pdTemps[~pdTemps.index.duplicated(keep='first')]
	pdTemps.interpolate(inplace=True, limit_direction='both')
	pdTemps = pdTemps[pdTemps.index.isin(fifteenMinuteTimestamps.index)]

	#create load regressor from weather data in correct format as nparray
	#loadregressors = pdTemps[['temperature']].values
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

	Tmin, Tmax, tempregress = createTempInput(pdTemps['temperature'], 1)
	#print(pdTemps['date'].values)
	#print(tempregress)
	loadregressors = tempregress
	#print(tempregress)

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
	sdmod0 = SolarDisagg.SolarDisagg_IndvHome(netloads=netload, solarregressors=solarproxy, loadregressors=loadregressors, names=meterNames)
	#
	sdmod0.constructSolve()
	#sdmod0.fitTuneModels()

	#Create subplots in plotly
	fig = tools.make_subplots(rows=5, cols=1)
	#plot weather and solar canary
	fig.append_trace(go.Scatter(y=pdTemps['temperature'], x=pdTemps.index, name=('interpolated weather '), marker=dict(color='red'), legendgroup='weather'),1,1)
	fig.append_trace(go.Scatter(y=realTemps['temperature'], x=realTemps.index, name=('real weather data '), mode = 'markers', marker=dict(color='orange'), legendgroup='weather'),1,1)
	fig['layout']['yaxis1'].update(title='Temperature')
	xaxis = [i for i in range(96)]
	fig.append_trace(go.Scatter(y=np.array([item for sublist in solarproxy for item in sublist]), x=pdTemps.index, name=('Solar Canary '), marker=dict(color='gold') ),2,1)
	fig['layout']['yaxis2'].update(title='Watts')

	#plot net aggregate load 
	#print(sdmod0.models['AggregateLoad']['source'].value)
	#fig.append_trace(go.Scatter(y=np.array([item for sublist in sdmod0.models['AggregateLoad']['source'].value.tolist() for item in sublist]), x=pdTemps['date'], name=('Disaggregated Total Load')),3,1)
	#fig.append_trace(go.Scatter(y=sdmod0.aggregateSignal, x=pdTemps['date'], name=('Aggregate Total Load')),3,1)

	#plot household loads and solar
	for i, model in enumerate(sdmod0.models):
		if model != 'AggregateLoad':
			#print(sdmod0.models[model]['source'].value)
			solarArray = np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist])
			disaggLoad = (sdmod0.netloads[model] - solarArray)
			fig.append_trace(go.Scatter(y=sdmod0.netloads[model], x=pdTemps.index, name=(str(model) + ': Measured Load'), marker=dict(color='green'), legendgroup=i),i+3,1)
			fig.append_trace(go.Scatter(y=disaggLoad, x=pdTemps.index, name=(str(model) + ': Disagreggated Load'), marker=dict(color='blue'), legendgroup=i),i+3,1)
			fig.append_trace(go.Scatter(y=np.array([item for sublist in sdmod0.models[model]['source'].value.tolist() for item in sublist]), x=pdTemps.index, name=(str(model) + ': Actual Load'), marker=dict(color='yellow'), legendgroup=i),i+3,1)
			fig['layout']['yaxis' + str(i+3)].update(title='Watts')

	#plot the results
	fig['layout'].update(height=1500, width=900)
	#inlinePlot = plotly.offline.plot(fig, include_plotlyjs=False, output_type='div')
	graphJSON = json.dumps(fig['data'], cls=plotly.utils.PlotlyJSONEncoder)
	layoutJSON = json.dumps(fig['layout'], cls=plotly.utils.PlotlyJSONEncoder)
	#soup = html.escape(str(BeautifulSoup(inlinePlot).find("div")))
	#soup2 = html.escape(str(BeautifulSoup(inlinePlot).find("script")))
	#print(soup)
	#print(soup2)

	folMap = folium.Map()
	marker_cluster = MarkerCluster().add_to(folMap)
	bounds = []
	with open(pJoin(modelDir,'lat_lon_uploaded.csv'),'w') as loadTempFile:
		loadTempFile.write(inputDict['latLonData'])
	with open(pJoin(modelDir,'lat_lon_uploaded.csv'), 'r') as csvfile:
		csvreader = csv.DictReader(csvfile, fieldnames=('netLoadName', 'netLoadLat', 'netLoadLon') , delimiter=',')
		for row in csvreader:
			bounds.append([float(row['netLoadLat']), float(row['netLoadLon'])])
			folium.CircleMarker(
				location=[float(row['netLoadLat']), float(row['netLoadLon'])],
				tooltip=row['netLoadName'],
				color='#FFFF00',
				fill=True,
				fill_opacity=0.9
			).add_to(marker_cluster)
#except:
	#	errorMessage = "CSV file is incorrect format."
	#	raise Exception(errorMessage)


	folMap.fit_bounds(bounds)
	folMap.save(pJoin(modelDir,'folGraph.html'))

	#how to pass with escape chars
	outData['graphJSON'] = graphJSON
	outData['layoutJSON'] = layoutJSON
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
	defaultInputs = {
		"user" : "admin",
		"modelType": modelName,
		"meterData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","load_data_year.csv")).read(),
		"solarData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","solar_proxy_year.csv")).read(),
		"weatherData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","asosweatherall.csv")).read(),
		"latLonData": open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","lat_lon_data.csv")).read(),
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
	print(endDay)
	url = ('https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=' + station + '&data=' + datatype + '&year1=' + startYear + 
		'&month1='+ startMonth +'&day1=' + startDay + '&year2=' + endYear + '&month2=' + endMonth +'&day2=' + endDay + '&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=1&report_type=2')
	r = requests.get(url)
	data = r.text
	return data

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated pvWatts Testing")
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
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
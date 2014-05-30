from datetime import datetime, timedelta
#from datetime import timezone # v3.0
#from datetime import tzinfo #v2.7
import math, os, re

# custom imports
import GetPeakSolar
import ExtractWeather

# [0],    [1],         [2],       [3],     [4],                 [5],          [6],           [7],          [8],          [9],            [10],  [11],      [12],          [13] 
# TimePST,TemperatureF,Dew PointF,Humidity,Sea Level PressureIn,VisibilityMPH,Wind Direction,Wind SpeedMPH,Gust SpeedMPH,PrecipitationIn,Events,Conditions,WindDirDegrees,DateUTC<br />
# 12:53 AM,44.1,43.0,96,29.99,9.0,Calm,Calm,-,N/A,,Overcast,0,2010-03-01 08:53:00<br />

class Weather:
	Time = ""
	Temp = 68.0
	Humi = 10.0
	Wind = 2.5
	Cond = "Sunny"
	Data = 0
	Seas = ""
	Solar = 0
	TzDelta = 0
	def __init__(self):
		pass
	def Build(self, tm, dt, tz, t, h, w, c, d):
		seasonDict = {1 : "Winter", 2 : "Winter", 3 : "Spring", 4 : "Spring", 5 : "Spring", 6 : "Summer", 7 : "Summer", 8 : "Summer", 9 : "Fall", 10 : "Fall", 11 : "Fall", 12 : "Winter"}
		self.Temp = float(t)
		self.Humi = float(h)
		self.Wind = w
		self.Cond = c # 3-tuple
		self.Data = d # csv-split line as a list
		self.TzDelta = tz
		dt2 = dt.split("<")
		t1 = datetime.strptime(dt2[0], "%Y-%m-%d %H:%M:%S")
		t2 = datetime.strptime(tm, "%I:%M %p")
		#self.Time = datetime(t1.year, t1.month, t1.day, t2.hour, t2.minute, 0)
		self.Time = t1 + tz
		self.Seas = seasonDict[self.Time.month]
		self.Solar = 0
		return self
def ParseWeather(line, hdr):
	rv = Weather()
	rv.Time = datetime.strptime("%Y-%m-%d %H:%M:%S<br />", line)
	rv.Temp = float(line[1])
	

def ProcessWeather(start, end, airport='', wdir='.', interpolate="linear"):
	# sanity checks
	startDate = datetime.strptime(start, "%m-%d-%Y")
	endDate = datetime.strptime(end, "%m-%d-%Y")
	if (startDate > endDate):
		print("start date is after the end date!")
		return -1

	# condition dictionary
	conditionDict = {"Clear" : (1.0, 1.0, 1.0),
								"Partly Cloudy" : (0.9, 1.1, 0.95),
								"Scattered Clouds" : (0.8, 1.2, 0.9),
								"Light Rain" : (0.8, 1.2, 0.9),
								"Mostly Cloudy" : (0.75, 1.25, 0.85),
								'Rain' : (0.75, 1.25, 0.85),
								'Overcast' : (0.7, 1.3, 0.8),
								'Heavy Rain' : (0.7, 1.3, 0.8),
								'Fog' : (0.7, 1.3, 0.8),
								'Haze' : (0.7, 1.3, 0.8),
								'Thunderstorm' : (0.7, 1.3, 0.8),
								'Heavy Thunderstorm' : (0.8, 1.4, 0.75),
								'Light Drizzle' : (0.75, 1.25, 0.85),
								'Mist' : (0.7, 1.3, 0.8),
								'Light Ice Pellets' : (0.75, 1.25, 0.85),
								'Light Snow' : (0.8, 1.2, 0.9),
								'Squalls' : (0.75, 1.25, 0.85)}
	moreConditionDict = {	"Light Drizzle" : 		(0.8, 1.2, 0.9), 
											"Drizzle" : 			(0.75, 1.25, 0.85),
											"Heavy Drizzle" : 		(0.7, 1.3, 0.8),
											"Light Rain" : 			(0.8, 1.2, 0.9),
											"Rain" : 				(0.75, 1.25, 0.85),
											'Heavy Rain' : 			(0.7, 1.3, 0.8),
											"Light Snow" : 			(0.8, 1.2, 0.9),
											"Snow" :				(0.8, 1.2, 0.9), #
											"Heavy Snow" :			(0.8, 1.2, 0.9), #
											"Light Snow Grains" : 	(0.8, 1.2, 0.9), # from 'light snow'
											"Snow Grains" : 		(0.8, 1.2, 0.9), #
											"Heavy Snow Grains" : 	(0.8, 1.2, 0.9), #
											"Light Ice Crystals" : 	(0.8, 1.2, 0.9), # from 'light snow'
											"Ice Crystals" : 		(0.8, 1.2, 0.9), #
											"Heavy Ice Crystals" : 	(0.8, 1.2, 0.9), #
											"Light Ice Pellets" : 	(0.8, 1.2, 0.9), # from 'light snow'
											"Ice Pellets" : 		(0.8, 1.2, 0.9), #
											"Heavy Ice Pellets" : 	(0.8, 1.2, 0.9), #
											"Light Hail" : 			(0.75, 1.25, 0.85), # from 'light rain'
											"Hail" :  				(0.75, 1.25, 0.85), #
											"Heavy Hail" :  		(0.75, 1.25, 0.85), #
											"LightMist" : 			(0.7, 1.3, 0.8), #
											"Mist" : 				(0.7, 1.3, 0.8),
											"Heavy Mist" : 			(0.7, 1.3, 0.8), #
											"Light Fog" : 			(0.7, 1.3, 0.8), #
											"Fog" : 				(0.7, 1.3, 0.8),
											"Heavy Fog" : 			(0.7, 1.3, 0.8), #
											"Light Fog Patches" : 	(0.7, 1.3, 0.8), #
											"Fog Patches" :			(0.7, 1.3, 0.8), # copied from "Fog"
											"Heavy Fog Patches" : 	(0.7, 1.3, 0.8), #
											"Light Smoke" : 		(1.0, 1.0, 1.0), #
											"Smoke" : 				(1.0, 1.0, 1.0), #
											"Heavy Smoke" : 		(1.0, 1.0, 1.0), #
											"Light Volcanic Ash" : 	(1.0, 1.0, 1.0), # 
											"Volcanic Ash" : (1.0, 1.0, 1.0),  #
											"Heavy Volcanic Ash" : (1.0, 1.0, 1.0), #
											"Light Widespread Dust" : (1.0, 1.0, 1.0), # 
											"Widespread Dust" : (1.0, 1.0, 1.0),  #
											"Heavy Widespread Dust" : (1.0, 1.0, 1.0), #
											"Light Sand" : (1.0, 1.0, 1.0),  #
											"Sand" : (1.0, 1.0, 1.0),  #
											"Heavy Sand" : (1.0, 1.0, 1.0), #
											"Light Haze" : (1.0, 1.0, 1.0),  #
											"Haze" : (1.0, 1.0, 1.0),  #
											"Heavy Haze" : (1.0, 1.0, 1.0), #
											"Light Spray" : (1.0, 1.0, 1.0),  #
											"Spray" : (1.0, 1.0, 1.0),  #
											"Heavy Spray" : (1.0, 1.0, 1.0), #
											"Light Dust Whirls" : (1.0, 1.0, 1.0), # 
											"Dust Whirls" : (1.0, 1.0, 1.0), # 
											"Heavy Dust Whirls" : (1.0, 1.0, 1.0), #
											"Light Sandstorm" : (1.0, 1.0, 1.0),  #
											"Sandstorm" : (1.0, 1.0, 1.0),  #
											"Heavy Sandstorm" : (1.0, 1.0, 1.0), #
											"Light Low Drifting Snow" : (1.0, 1.0, 1.0), # 
											"Low Drifting Snow" : (1.0, 1.0, 1.0),  #
											"Heavy Low Drifting Snow" : (1.0, 1.0, 1.0), #
											"Light Low Drifting Widespread Dust" : (1.0, 1.0, 1.0), # 
											"Low Drifting Widespread Dust" : (1.0, 1.0, 1.0),  #
											"Heavy Low Drifting Widespread Dust" : (1.0, 1.0, 1.0), #
											"Light Low Drifting Sand" : (1.0, 1.0, 1.0),  #
											"Low Drifting Sand" : (1.0, 1.0, 1.0),  #
											"Heavy Low Drifting Sand" : (1.0, 1.0, 1.0), #
											"Light Blowing Snow" : (1.0, 1.0, 1.0),  #
											"Blowing Snow" : (1.0, 1.0, 1.0),  #
											"Heavy Blowing Snow" : (1.0, 1.0, 1.0), #
											"Light Blowing Widespread Dust" : (1.0, 1.0, 1.0), # 
											"Blowing Widespread Dust" : (1.0, 1.0, 1.0), # 
											"Heavy Blowing Widespread Dust" : (1.0, 1.0, 1.0), #
											"Light Blowing Sand" : (1.0, 1.0, 1.0),  #
											"Blowing Sand" : (1.0, 1.0, 1.0),  #
											"Heavy Blowing Sand" : (1.0, 1.0, 1.0), #
											"Light Rain Mist" : (1.0, 1.0, 1.0), # 
											"Rain Mist" : (1.0, 1.0, 1.0),  #
											"Heavy Rain Mist" : (1.0, 1.0, 1.0), #
											"Light Rain Showers" : (1.0, 1.0, 1.0), # 
											"Rain Showers" : (1.0, 1.0, 1.0), # 
											"Heavy Rain Showers" : (1.0, 1.0, 1.0), #
											"Light Snow Showers" : (1.0, 1.0, 1.0), # 
											"Snow Showers" : (1.0, 1.0, 1.0), # 
											"Heavy Snow Showers" : (1.0, 1.0, 1.0), #
											"Light Snow Blowing Snow Mist" : (1.0, 1.0, 1.0), #
											"Snow Blowing Snow Mist" : (1.0, 1.0, 1.0),  #
											"Heavy Snow Blowing Snow Mist" : (1.0, 1.0, 1.0), #
											"Light Ice Pellet Showers" : (1.0, 1.0, 1.0), #
											"Ice Pellet Showers" : (1.0, 1.0, 1.0), #
											"Heavy Ice Pellet Showers" : (1.0, 1.0, 1.0), #
											"Light Hail Showers" : (1.0, 1.0, 1.0), #
											"Hail Showers" : (1.0, 1.0, 1.0), #
											"Heavy Hail Showers" : (1.0, 1.0, 1.0), #
											"Light Small Hail Showers" : (1.0, 1.0, 1.0), #
											"Small Hail Showers" : (1.0, 1.0, 1.0), #
											"Heavy Small Hail Showers" : (1.0, 1.0, 1.0), #
											"Light Thunderstorm" : (1.0, 1.0, 1.0), #
											"Thunderstorm" : (1.0, 1.0, 1.0), # 
											"Heavy Thunderstorm" : (1.0, 1.0, 1.0), #
											"Light Thunderstorms and Rain" : (1.0, 1.0, 1.0), # 
											"Thunderstorms and Rain" : (1.0, 1.0, 1.0), # 
											"Heavy Thunderstorms and Rain" : (1.0, 1.0, 1.0), #
											"Light Thunderstorms and Snow" : (1.0, 1.0, 1.0), # 
											"Thunderstorms and Snow" : (1.0, 1.0, 1.0), # 
											"Heavy Thunderstorms and Snow" : (1.0, 1.0, 1.0), #
											"Light Thunderstorms and Ice Pellets" : (1.0, 1.0, 1.0), # 
											"Thunderstorms and Ice Pellets" : (1.0, 1.0, 1.0), # 
											"Heavy Thunderstorms and Ice Pellets" : (1.0, 1.0, 1.0), #
											"Light Thunderstorms with Hail" : (1.0, 1.0, 1.0), # 
											"Thunderstorms with Hail" : (1.0, 1.0, 1.0), # 
											"Heavy Thunderstorms with Hail" : (1.0, 1.0, 1.0), #
											"Light Thunderstorms with Small Hail" : (1.0, 1.0, 1.0), # 
											"Thunderstorms with Small Hail" : (1.0, 1.0, 1.0), # 
											"Heavy Thunderstorms with Small Hail" : (1.0, 1.0, 1.0), #
											"Light Freezing Drizzle" : (1.0, 1.0, 1.0), # 
											"Freezing Drizzle" : (1.0, 1.0, 1.0), # 
											"Heavy Freezing Drizzle" : (1.0, 1.0, 1.0), #
											"Light Freezing Rain" : (1.0, 1.0, 1.0), # 
											"Freezing Rain" : (1.0, 1.0, 1.0), # 
											"Heavy Freezing Rain" : (1.0, 1.0, 1.0), #
											"Light Freezing Fog" : (1.0, 1.0, 1.0), # 
											"Freezing Fog" : (1.0, 1.0, 1.0), # 
											"Heavy Freezing Fog" : (1.0, 1.0, 1.0), #
											"Patches of Fog" : (1.0, 1.0, 1.0), #
											"Shallow Fog" : (1.0, 1.0, 1.0), #
											"Partial Fog" : (1.0, 1.0, 1.0), #
											"Overcast" : (1.0, 1.0, 1.0), #
											"Clear" : (1.0, 1.0, 1.0),
											"Partly Cloudy" : (0.9, 1.1, 0.95),
											"Mostly Cloudy" : (1.0, 1.0, 1.0), #
											"Scattered Clouds" : (1.0, 1.0, 1.0), #
											"Small Hail" : (1.0, 1.0, 1.0), #
											"Squalls" : (1.0, 1.0, 1.0), #
											"Funnel Cloud" : (1.0, 1.0, 1.0), #
											"Unknown Precipitation" : (1.0, 1.0, 1.0), #
											"Unknown" : (1.0, 1.0, 1.0) #
											}

	#for item in moreConditionDict:
	#	a, b, c = moreConditionDict[item]
	#	print("{}: {}, {}, {}".format(item, str(a), str(b), str(c))) 
	seasonDict = {1 : "Winter", 2 : "Winter", 3 : "Spring", 4 : "Spring", 5 : "Spring", 6 : "Summer", 7 : "Summer", 8 : "Summer", 9 : "Fall", 10 : "Fall", 11 : "Fall", 12 : "Winter"}
	# interpolation options
	interpolateList = ["none", "linear", "quadratic"]
	# scan for files
	fileList = os.listdir(wdir)
	filePtrn = re.compile("weather_(?P<loc>[A-Z]+)_(?P<raw_date>[0-9]+_[0-9]+_[0-9]+).csv")
	matchedFiles = list(filter(filePtrn.match, fileList))
	if len(matchedFiles) is 0:
		print("no weather files found in {}".format(wdir))
		return -1
	# identify desired files
	matchedList = [filePtrn.match(x) for x in matchedFiles]
	fileParts = [m.groupdict() for m in matchedList]
	filteredParts = list(filter(lambda x: x["loc"] == airport, fileParts))
	if len(filteredParts) is 0:
		print("no weather files found in {} that match airport {}".format(wdir, airport))
		return -1
	# filteredParts now contains a list of dictionaries where "loc" == airport
	# process dates into datetime objects
	#for part in filteredParts:
		#part["date"] = datetime.strptime(part["raw_date"], "%Y_%m_%d")
	fileDict = {}
	for part in filteredParts:
	#for part in filterDict:
		part["date"] = datetime.strptime(part["raw_date"], "%Y_%m_%d")
		part["file"] = "weather_{}_{}.csv".format(part["loc"], part["raw_date"])
		fileDict[part["date"]] = part
	# get timedelta
	timeDiff = endDate - startDate
	timeRange = [startDate + timedelta(days=n) for n in range(0, timeDiff.days)]
	useFiles = []
	for eachDay in timeRange:
		if eachDay in fileDict:
			useFiles.append(fileDict[eachDay])
	# useFiles now has a list of all the files in the range that we want to use
	myData = []
	weatherData = []
	
	currDir = os.getcwd()
	os.chdir(wdir)
	for eachFile in useFiles:
		myFile = open(eachFile["file"], "r")
		myLines = myFile.readlines()
		#myLines = [line+","+eachFile["file"] for line in myLinesPre]
		myData.extend(myLines)
	os.chdir(currDir)
	weatherDataInt = list(filter(lambda x: len(x) > 1, myData))						# remove all "<br />" lines
	weatherHeader = list(filter(lambda x: "Time" in x, weatherDataInt))			# capture all header lines
	weatherDataTrim = list(filter(lambda x: "Time" not in x, weatherDataInt))	# remove all header lines
	weatherSplit = [str.split(line, ",") for line in weatherDataTrim]				# split into a list of lists
	weatherKeys = str.split(weatherHeader[0], ",")
	#weatherData = [dict(zip(weatherKeys, thisSplit)) for thisSplit in weatherSplit] # makes a dictionary out of things, to make it complicated...
	weatherData = weatherSplit
	# TimePST,     TemperatureF, Dew PointF, Humidity, Sea Level PressureIn, VisibilityMPH, Wind Direction, Wind SpeedMPH,
	# ['1:53 AM', '43.0',        '42.1',    '97',      '29.99',              '9.0',        'Calm',          'Calm',
	# (cont'd)
	# Gust SpeedMPH, PrecipitationIn, Events,  Conditions,    WindDirDegrees, DateUTC<br />
	# '-',           'N/A',           'Fog',   'Shallow Fog', '0',            '2010-03-01 09:53:00<br />\n']
	
	# record the time, temp, humidity, wind, conditions, and date.

	#get time & date indices
	timeIndex = 0
	utcIndex = 0
	for index,key in enumerate(weatherKeys): # works to this point
		if "Time" in key:
			timeIndex = index
		if "Date" in key:
			utcIndex = index
	# slice timezone from keys
	tz = weatherKeys[timeIndex][4:7]
	
	# use the first sample to determine TZ offset
	firstDt = datetime.strptime(weatherData[0][timeIndex], "%I:%M %p")
	t1 = datetime(year=startDate.year, month=startDate.month, day=startDate.day, hour=firstDt.hour, minute=firstDt.minute) # local
	t2 = datetime.strptime(weatherData[0][utcIndex].split("<")[0], "%Y-%m-%d %H:%M:%S") # GMT
	tzDelta = t1 - t2
	
	# replace "Calm" wind with 0
	windIndex = 0
	windKey = "Wind SpeedMPH"
	if windKey in weatherKeys:
		windIndex = weatherKeys.index(windKey)
		windDataList = [sample[windIndex] for sample in weatherData]
		#print(windDataList)
		for index,entry in enumerate(windDataList): 
			if entry == "Calm":
				weatherData[index][windIndex] = 0.0
				#print("replacing 'Calm' at time "+str(weatherData[index][utcIndex]))
			else:
				#print("not replacing '"+str(entry)+"' at time "+str(weatherData[index][utcIndex]))
				weatherData[index][windIndex] = float(weatherData[index][windIndex])
			
	else:
		windIndex = -1
		# error and explode
	
	# replace "N/A" humidity with 0
	humidKey = "Humidity"
	humidIndex = 0
	if humidKey in weatherKeys:
		humidIndex = weatherKeys.index(humidKey)
		for index,entry in enumerate(sample[humidIndex] for sample in weatherData): 
			if entry == "N/A":
				weatherData[index][humidIndex] = 0.0
	else:
		humidIndex = -1
		# error and explode
	
	# replace 'Conditions" with dictionary value
	condKey = "Conditions"
	condIndex = 0
	if condKey in weatherKeys:
		condIndex = weatherKeys.index(condKey)
		for index,entry in enumerate(sample[condIndex] for sample in weatherData):
			if entry in moreConditionDict.keys():
				#weatherData[index][condIndex] = conditionDict[entry]
				weatherData[index][condIndex] = moreConditionDict[entry]
				#print("index {:d} to ".format(index)+str(weatherData[index][condIndex]))
			else:
				print("index {:d} invalid conditions '{}'".format(index, entry))
	else:
		condIndex = -1
		# error and explode
	
	# get temperature index
	heatKey = "TemperatureF"
	heatIndex = 0
	if heatKey in weatherKeys:
		heatIndex = weatherKeys.index(heatKey)
	else:
		heatIndex = -1
	
	
	
	# convert to useful values
	weatherList = []
	# def Weather(self, tm, dt, tz, t, h, w, c, d):
	for entry in weatherData:
		sample = Weather().Build(entry[timeIndex], entry[utcIndex], tzDelta, entry[heatIndex], entry[humidIndex], entry[windIndex], entry[condIndex], entry)
		weatherList.append(sample)
	
	# sanity-check numbers
	for index,entry in enumerate(weatherList):
		# * temperature
		if entry.Temp > 150.0 or entry.Temp < -20:
			if index > 0:
				entry.Temp = weatherList[index-1].Temp
			else:
				# if first value is bad, snag the first good value
				n = 1
				while (weatherList[n].Temp > 150.0 or weatherList[n].Temp < -20) and n < len(weatherList):
					n += 1
				entry.Temp = weatherList[n].Temp
		# * humidity
		if entry.Humi > 100.0 or entry.Humi < 0.0:
			if index > 0:
				entry.Humi = weatherList[index-1].Temp
			else:
				# if first value is bad, snag the first good value
				n = 1
				while (weatherList[n].Humi > 100.0 or weatherList[n].Humi < 0) and n < len(weatherList):
					n += 1
				entry.Humi = weatherList[n].Humi 
		# * wind speed
		if entry.Wind > 200.0 or entry.Wind < -1.0:
			if index > 0:
				entry.Wind = weatherList[index-1].Wind
			else:
				# if first value is bad, snag the first good value
				n = 1
				while (n < len(weatherList)):
					if weatherList[n].Wind > 200.0:
						print("wind speed "+str(weatherList[n].Wind)+" at "+str(n)+" out of range (above)")
						n += 1
					if weatherList[n].Wind < -1.0:
						print("wind speed "+str(weatherList[n].Wind)+" at "+str(n)+" out of range (below)")
						n += 1
					else:
						break
				#try:
				if n < len(weatherList):
					entry.Wind = weatherList[n].Wind
				else:
					print("error getting wind value for sample at "+str(entry.Time))
				#except IndexError:
				#	print("error getting wind value from sample at "+str(entry.Time)) 
				#	return
		# * conditions
		if entry.Cond == "Unknown":
			if index > 0:
				entry.Cond = weatherList[index-1].Cond
			else:
				# if first value is bad, snag the first good value
				n = 1
				while n < len(weatherList) and (weatherList[n].Cond == "Unknown"):
					n += 1
				#try:
				#entry.Cond = conditionDict[weatherList[n].Cond]
				entry.Cond = moreConditionDict[weatherList[n].Cond]
				#except IndexError:
				#	print("error getting condition value from sample at "+str(entry.Time))
				#	return
				
	# add 00:00:00 to each day
	
	seasons = {	"Winter" : ([], "solar_{}_winter_csv".format(airport)),
						"Spring" : ([], "solar_{}_spring.csv".format(airport)),
						"Summer" : ([], "solar_{}_summer.csv".format(airport)),
						"Fall" : ([], "solar_{}_fall.csv".format(airport))}
	
	# look for the solar files
	if os.path.isdir(wdir):
		os.chdir(wdir)
	if not os.path.isfile(seasons["Winter"][1]):
		os.chdir(currDir)
		rv = GetPeakSolar.GetPeakSolar(airport, wdir)
		os.chdir(currDir) # in case it's left dirty
		if rv is None:
			print("ERROR: unable to retrieve solar information")
			return -1

	# load and parse these files for key in seasons.keys():
	seasonCount = {	"Winter" : 0,
								"Spring" : 0,
								"Summer" : 0,
								"Fall" : 0}
	for line in weatherList:
		seasonCount[line.Seas] += 1
		
	for season in seasonCount:
		if seasonCount[season] == 0:
			continue
		# Time(HH:MM), GHI_Normal, DNI_Normal and DHI_Normal
		#  * {2-4} used for 'real data'.
		seasonData, seasonFileName = seasons[season]
		if os.path.isdir(wdir):
			os.chdir(wdir)
		seasonFile = open(seasonFileName, "r")
		os.chdir(currDir)
		seasonFileLines = seasonFile.readlines()
		seasonFileLines.pop(0) # header
		seasonDataStr = [str.split(line, ",") for line in seasonFileLines]
		#print(seasonDataStr)
		seasonData.extend([(float(data[2]), float(data[3]), float(data[1])) for data in seasonDataStr]) # skip time in index 0
	pass
	
	# find solar data per-season, interpolate from hourly to the sample time, add into weather dictionary
	for sample in weatherList:
		wdir, dif, glo = sample.Cond
		sampleHour = sample.Time.hour
		seasonData, Season = seasons[sample.Seas]
		dirMod, difMod, gloMod = seasonData[sampleHour]
		sample.Solar = (wdir*dirMod, dif*difMod, glo*gloMod)
		#print(str(sample.Time)+": "+str(sample.Cond)+" * "+str(seasonData[sampleHour])+" = "+str(sample.Solar))
	
	# interpolate downloaded data into 
	outData = []
	interval = timedelta(minutes = 5)
	lerp = lambda x, y, r: x + (y-x)*r
	def qerp(x, y0, y1, y2, x0, x1, x2):
		if x == x0:
			return y0
		if x == x1:
			return y1
		if x == x2:
			return y2
		if(x0 == x1):
			print("QERP ERROR: x0 == x1")
			return 0.0
		if(x1 == x2):
			print("QERP ERROR: x1 == x2")
			return 0.0
		if x0 == x2:
			print("QERP ERROR: x0 == x2")
			return 0.0
		return (x-x1)*(x-x2)/(x0-x1)/(x0-x2)*y0 + (x-x0)*(x-x2)/(x1-x0)/(x1-x2)*y1 + (x-x0)*(x-x1)/(x2-x0)/(x2-x1)*y2 
	epoch = datetime(1970, 1, 1)
	for index,entry in enumerate(weatherList):
		# write sample
		outData.append(entry)
		# if next step is more than 5 minutes ahead,
		if index + 1 >= len(weatherList):
			# we've run out of samples
			break
		#  * count number of 5 minute steps
		steps = 0
		timeStep = weatherList[index+1].Time - weatherList[index].Time
		if "linear" in interpolate:
			if timeStep > interval:
				steps = int(math.floor(timeStep.seconds / interval.seconds))
				nxEntry = weatherList[index+1]
				#  * for each step, write an interpolated value.
				for n in range(1, steps):
					ratio = n * float(interval.seconds) / float(timeStep.seconds) # @todo verify this works and doesn't break on 'unit conversion'
					sample = Weather()
					sample.Temp = lerp(entry.Temp, nxEntry.Temp, ratio)
					sample.Humi = lerp(entry.Humi, nxEntry.Humi, ratio)
					sample.Wind = lerp(entry.Wind, nxEntry.Wind, ratio)
					sDir, sDif, sGlo = entry.Solar
					nDir, nDif, nGlo = nxEntry.Solar
					sample.Solar = (lerp(sDir, nDir, ratio), lerp(sDif, nDif, ratio), lerp(sGlo, nGlo, ratio))
					sample.Time = entry.Time + n * interval
					sample.Seas = seasonDict[sample.Time.month]
					outData.append(sample)
		elif "quadratic" in interpolate:
			if timeStep > interval:
				steps = int(math.floor(timeStep.seconds / interval.seconds))
				p0 = 0
				p1 = 0
				p2 = 0
				if index + 2 > len(weatherList):
					# last sample, don't interpolate forward
					break
				elif index + 2 == len(weatherList):
					# need to use i-1, i, i+1 for reference points
					p0 = weatherList[index-1]
					p1 = entry
					p2 = weatherList[index+1]
				else:
					# full interpolation
					p0 = entry
					p1 = weatherList[index+1]
					p2 = weatherList[index+2]
				for n in range(1, steps):
					#t = float(n) * float(interval.seconds) + float(timeStep.seconds)
					t = (n * interval + timeStep).total_seconds()
					t1 = (p0.Time - epoch).total_seconds()
					t2 = (p1.Time - epoch).total_seconds()
					t3 = (p2.Time - epoch).total_seconds()
					sample = Weather()
					sample.Temp = qerp(t, p0.Temp, p1.Temp, p2.Temp, t1, t2, t3)
					sample.Humi = qerp(t, p0.Humi, p1.Humi, p2.Humi, t1, t2, t3)
					sample.Wind = qerp(t, p0.Wind, p1.Wind, p2.Wind, t1, t2, t3)
					aDir, aDif, aGlo = p0.Solar
					bDir, bDif, bGlo = p1.Solar
					cDir, cDif, cGlo = p2.Solar
					sample.Solar = (qerp(t, aDir, bDir, cDir, t1, t2, t3), qerp(t, aDif, bDif, cDif, t1, t2, t3), qerp(t, aGlo, bGlo, cGlo, t1, t2, t3))
					sample.Time = entry.Time + n * interval
					sample.Seas = seasonDict[sample.Time.month]
					if sample.Wind < 0:
						sample.Wind = 0 # clip, since qerp can take values below zero
					outData.append(sample)
			pass
		
		pass
	
	### @todo: check that the timestamps make sense
	
	
	
	# open and write the output file
	outFile = open("SCADA_weather_"+airport+"_gld.csv", "w")
	# write header
	outFile.write('#DUKE weather file\n');
	outFile.write('$state_name=North Carolina\n');
	outFile.write('$city_name=Charlotte\n');
	outFile.write('$lat_deg=35\n');
	outFile.write('$lat_min=13\n');
	outFile.write('$long_deg=-80\n');
	outFile.write('$long_min=56\n');
	outFile.write('$timezone_offset=-4\n');
	outFile.write('temperature,wind_speed,humidity,solar_dir,solar_diff,solar_global\n');
	outFile.write('#month:day:hour:minute:second\n');
	# write samples per-line
	for line in outData:
		# write each line
		#fprintf(fidfin, '%s, %.1f, %.1f, %.2f, %.2f, %.2f, %.2f\n', TimeC, finaldata(ii,2:7));
		outFile.write("{}:{}:{}:{}:{},{},{},{},{},{},{}\n".format(line.Time.month, line.Time.day, line.Time.hour, line.Time.minute, line.Time.second,
																line.Temp, line.Wind, line.Humi, line.Solar[0], line.Solar[1], line.Solar[2]))
		pass
	# clean up and exit
	outFile.close()
	
	return 0

def GenerateWeatherFiles(start, end, airport, wdir=''):
	rv = ExtractWeather.GetWeather(start, end, airport, wdir)
	if rv != None:
		rv2 = ProcessWeather(start, end, airport, wdir)
		if rv2 == None:
			print("ERROR: ProcessWeather({}, {}, {}, {}) failed!".format(start, end, airport, wdir))
			return None
		return 0
	else:
		print("ERROR: ExtractWeather.GetWeather({}, {}, {}, {}) failed!".format(start, end, airport, wdir))
		return None
	
if __name__ is '__main__':
	ProcessWeather('06-01-2010', '07-01-2010', airport="PDX")

#
# EOF
#
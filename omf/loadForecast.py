'''
This contains the loadForecast algorithms

'''

import math
import numpy as np
from datetime import datetime as dt

# source: https://www.energygps.com/HomeTools/PowerCalendar
nercHolidays = {
	dt(2019, 1, 1): 'New Years',
	dt(2019, 5, 27): 'Memorial',
	dt(2019, 7, 4): 'Independence',
	dt(2019, 9, 2): 'Labor',
	dt(2019, 11, 28): 'Thanksgiving',
	dt(2019, 12, 25): 'Christmas',
	dt(2020, 1, 1): 'New Years',
	dt(2020, 5, 25): 'Memorial',
	dt(2020, 7, 4): 'Independence',
	dt(2020, 9, 7): 'Labor',
	dt(2020, 11, 26): 'Thanksgiving',
	dt(2020, 12, 25): 'Christmas',
	dt(2021, 1, 1): 'New Years',
	dt(2021, 5, 31): 'Memorial',
	dt(2021, 7, 5): 'Independence',
	dt(2021, 9, 6): 'Labor',
	dt(2021, 11, 25): 'Thanksgiving',
	dt(2021, 12, 25): 'Christmas'
}

def pullHourlyDayOfWeekForecast(rawData,upBound,lowBound):
	'''
	This model takes the inputs rawData, a dataset that holds 8760 values in two columns with no indexes
	The first column rawData[:][0] holds the hourly demand for one year
	The second column rawData[:][1] holds the hourly temperature for one year
	upBound is the upper limit for forecasted data to not exceed as sometimes the forecasting is wonky
	lowBound is the lower limit for forecasted data to not exceed as sometimes the forecasting is wonky
	when values exceed upBound or go below lowBound they are set to None
	'''
	forecasted = []
	actual = []
	for w in range(8760):
		# need to start at 4 weeks+1 hour to get enough data to train so 4*7*24 = 672, the +1 is not necessary due to indexing starting at 0
		actual.append((rawData[w][0]))
		if w>=672:
			x = np.array([rawData[w-168][1],rawData[w-336][1],rawData[w-504][1],rawData[w-672][1]]) #training temp
			y = np.array([rawData[w-168][0],rawData[w-336][0],rawData[w-504][0],rawData[w-672][0]]) #training demand
			z = np.polyfit(x, y, 1)
			p = np.poly1d(z)
			forecasted.append(float((p(rawData[w][1]))))
		else:
			forecasted.append(None)
	for i in range(len(forecasted)):
		if forecasted[i]>float(upBound):
			forecasted[i] = None
		elif forecasted[i] <float(lowBound):
			forecasted[i] = None
	MAE = 0		#Mean Average Error calculation
	for i in range(len(forecasted)):
		if forecasted[i]!=None:
			MAE = MAE + abs(forecasted[i]-actual[i])
	MAE = math.trunc(MAE/len(forecasted)) 
	return (forecasted,MAE)
	'''
	forecasted is an 8760 list of demand values
	MAE is an int and is the mean average error of the forecasted/actual data correlation
	'''
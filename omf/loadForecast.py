'''
This contains the loadForecast algorithms

'''

import math
import numpy as np

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
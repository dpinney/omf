import csv
import random
import numpy as np
from math import sqrt

tempMu = 65
sigma = sqrt(1)

#meter data
tempRaw = np.linspace(tempMu - 0*sigma, tempMu + 0*sigma, 180)
#print(meterRaw[::-1])
tempRaw = np.append(tempRaw, tempRaw[::-1])

#randomized meters
tempRaw = np.array([tempRaw + np.random.normal(0,.5,360)]).transpose()

with open('weather_regress.csv', 'wb') as csvfile:
	csvwriter = csv.writer(csvfile, delimiter=',',
							quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for i in tempRaw:
		csvwriter.writerow(i)
print("Weather generated")
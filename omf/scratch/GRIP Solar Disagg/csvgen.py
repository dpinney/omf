import csv
import random
import numpy as np
from math import sqrt

meterMu = 4
sigma = sqrt(1)

#meter data
#0-5
meterRaw1 = np.ones(24)
#6-11
meterRaw2 = np.linspace(1 + 1*sigma, meterMu + 6*sigma, 24)
#12-17
meterRaw3 = np.linspace(meterMu + 6*sigma, meterMu + 6*sigma, 24)
#18-23
meterRaw4 = np.linspace(meterMu + 9*sigma, 1 + 1*sigma, 24)
#print(meterRaw[::-1])
meterRaw = np.concatenate((meterRaw1, meterRaw2, meterRaw3, meterRaw4))

#randomized meters
meter1 = meterRaw + np.random.normal(0,.5,96)
meter2 = meterRaw + np.random.normal(0,.5,96)
meter3 = meterRaw + np.random.normal(0,.5,96)

#solar for house
sigma = sqrt(1)
solarMu = -5
solarDay =  np.linspace(solarMu + 5*sigma, solarMu - 20*sigma, 24)
solarDay = np.append(solarDay, solarDay[::-1])
#print(solarDay)
solarRaw = np.concatenate((np.zeros(24), solarDay, np.zeros(24)))

meter3 = meter3 + solarRaw

meters = np.array([meter1, meter2, meter3]).transpose()
#print(meters)
#print(meter1)
#print(meter2)
#print(meter3)

with open('load_data.csv', 'wb') as csvfile:
	csvwriter = csv.writer(csvfile, delimiter=',',
							quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for i in meters:
		csvwriter.writerow(i)

print("Meters generated")
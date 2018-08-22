import csv
import random
import numpy as np
from math import sqrt

meterMu = 4
sigma = sqrt(1)

#meter data
meterRaw = np.linspace(meterMu - 3*sigma, meterMu + 3*sigma, 48)
#print(meterRaw[::-1])
meterRaw = np.append(meterRaw, meterRaw[::-1])

#randomized meters
meter1 = meterRaw + np.random.normal(0,.5,96)
meter2 = meterRaw + np.random.normal(0,.5,96)
meter3 = meterRaw + np.random.normal(0,.5,96)

#solar for house
sigma = sqrt(1)
solarMu = -5
solarDay =  np.linspace(solarMu + 4*sigma, solarMu - 4*sigma, 32)
solarDay = np.append(solarDay, solarDay[::-1])
#print(solarDay)
solarRaw = np.concatenate((np.zeros(16), solarDay, np.zeros(16)))

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
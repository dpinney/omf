import csv
import random
import numpy as np
from math import sqrt

#solar proxy
sigma = sqrt(1)
solarMu = 5
solarDay =  np.linspace(solarMu - 5*sigma, solarMu + 20*sigma, 24)
solarDay = np.append(solarDay, solarDay[::-1])
#solarDay = solarDay + np.random.normal(0,.5,240) 
solarRaw = np.concatenate((np.zeros(24), solarDay, np.zeros(24)))

randSolar = np.array([solarRaw]).transpose()
#print(randSolar)

#meters = np.array([meter1, meter2, meter3]).transpose()
#print(meters)



with open('solar_proxy.csv', 'wb') as csvfile:
	csvwriter = csv.writer(csvfile, delimiter=',',
							quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for i in randSolar:
		csvwriter.writerow(i)
print("Solar generated")
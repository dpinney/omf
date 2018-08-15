import csv
import random
import numpy as np
from math import sqrt

#solar proxy
sigma = sqrt(1)
solarMu = 5
solarDay =  np.linspace(solarMu - 4*sigma, solarMu + 4*sigma, 120)
solarDay = np.append(solarDay, solarDay[::-1])
#solarDay = solarDay + np.random.normal(0,.5,240) 
solarRaw = np.concatenate((np.zeros(60), solarDay, np.zeros(60)))

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
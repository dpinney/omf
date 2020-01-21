import csv
import numpy as np
import matplotlib.pyplot as plt

X = []
with open( 'faultyPowerAndLabels.csv','r' ) as faultyFile:
    faultyReader = csv.reader(faultyFile, delimiter=',')

    for faultyRow in faultyReader:
    	X.append( float(faultyRow[0]) )

count = 0
with open( 'faultFreePowerAndLabels.csv','r' ) as faultFreeFile:
    faultFreeReader = csv.reader(faultFreeFile, delimiter=',')
    for faultFreeRow in faultFreeReader:
    	X[count] -= float(faultFreeRow[0]) 
    	count += 1

print(np.mean(X),np.std(X))
plt.scatter(range(len(X)),X)
plt.tight_layout()
plt.show()
import opendssdirect as dss
import pandas as pd
import matplotlib.pyplot as plt
import math

dss.run_command('Redirect IEEE37.dss')
voltage = pd.read_csv('volts.csv')
volt_coord_cols = ['Bus', 'X', 'Y']
coord = pd.read_csv('IEEE37_BusXY.csv', names=volt_coord_cols)
hyp = []
for index, row in coord.iterrows():
	hyp.append(math.sqrt(row['X']**2 + row['Y']**2))
coord['radius'] = hyp
voltageDF = pd.merge(coord, voltage, on='Bus')
plt.scatter(voltageDF['radius'], voltageDF[' pu1'])
plt.xlabel('RADIUS')
plt.ylabel('VOLTS')
plt.show()

dss.run_command('Redirect short_circuit.dss')

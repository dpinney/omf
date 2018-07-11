import opendssdirect as dss
import pandas as pd
import matplotlib.pyplot as plt
import math


dss.run_command('Redirect ieee37.dss')
voltage = pd.read_csv('volts.csv')
volt_coord_cols = ['Bus', 'X', 'Y']
volt_coord = pd.read_csv('IEEE37_BusXY.csv', names=volt_coord_cols)
volt_hyp = []
for index, row in volt_coord.iterrows():
	volt_hyp.append(math.sqrt(row['X']**2 + row['Y']**2))
volt_coord['radius'] = volt_hyp
voltageDF = pd.merge(volt_coord, voltage, on='Bus')
for i in range(1, 4):
	volt_ind = ' pu' + str(i)
	plt.scatter(voltageDF['radius'], voltageDF[volt_ind])
	plt.xlabel('RADIUS')
	plt.ylabel('VOLTS')
	plt.title('FOR ' + volt_ind)
	plt.show()



dss.run_command('Redirect short_circuit.dss')
current = pd.read_csv('short_currents.csv')
curr_coord_cols = ['Index', 'X', 'Y']
curr_coord = pd.read_csv('short_circuit_coords.csv', names=curr_coord_cols)
curr_hyp = []
for index, row in curr_coord.iterrows():
	curr_hyp.append(math.sqrt(row['X']**2 + row['Y']**2))
curr_coord['radius'] = curr_hyp
currentDF = pd.concat([curr_coord, current], axis=1)
for i in range(1, 3):
	for j in range(1, 4):
		cur_ind = ' I' + str(i) + '_' + str(j)
		plt.scatter(currentDF['radius'], currentDF[cur_ind])
		plt.xlabel('RADIUS')
		plt.ylabel('CURRENT')
		plt.title('FOR ' +  cur_ind)
		plt.show()



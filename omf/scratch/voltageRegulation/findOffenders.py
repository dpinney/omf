#Find Offenders


import json, math, os, argparse
from omf import feeder
from os.path import join as pJoin
import pandas as pd
import numpy as np
import csv

# omfDIR = '/Users/tuomastalvitie/omf/omf'

data = pd.read_csv(('voltDump.csv'), skiprows=[0])
for i, row in data['voltA_real'].iteritems():
	voltA_real = data.loc[i,'voltA_real']
	voltA_imag = data.loc[i,'voltA_imag']
	voltA_mag = np.sqrt(np.add((voltA_real*voltA_real), (voltA_imag*voltA_imag)))
	name_volt_dict[data.loc[i, 'node_name']].update({'Volt_A':voltA_mag})
	voltB_real = data.loc[i,'voltB_real']
	voltB_imag = data.loc[i,'voltB_imag']
	voltB_mag = np.sqrt(np.add((voltB_real*voltB_real), (voltB_imag*voltB_imag)))
	name_volt_dict[data.loc[i, 'node_name']].update({'Volt_B':voltB_mag})
	voltC_real = data.loc[i,'voltC_real']
	voltC_imag = data.loc[i,'voltC_imag']
	voltC_mag = np.sqrt(np.add((voltC_real*voltC_real), (voltC_imag*voltC_imag)))
	name_volt_dict[data.loc[i, 'node_name']].update({'Volt_C':voltC_mag})

offenders = []
for name, volt in name_volt_dict.iteritems():
	if (float(volt['Volt_A'])/float(volt['Nominal_Voltage'])) > 1.05:
		print name
		offenders.append(name)
	if (float(volt['Volt_B'])/float(volt['Nominal_Voltage'])) > 1.05:
		print name
		offenders.append(name)
	if (float(volt['Volt_C'])/float(volt['Nominal_Voltage'])) > 1.05:
		print name
		offenders.append(name)
print offenders
print len(offenders)
offenders = list(set(offenders))
with open('offenders.csv', 'w') as f:
	wr = csv.writer(f, quoting=csv.QUOTE_ALL)
	wr.writerow(offenders)

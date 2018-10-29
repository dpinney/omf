
import json, math, os, argparse
from omf import feeder
from os.path import join as pJoin
import pandas as pd
import numpy as np
import csv
import omf

#Parse Command Line
# parser = argparse.ArgumentParser(description='Converts an OMD to GLM and runs it on gridlabd')
# parser.add_argument('file_path', metavar='base', type=str,
#                     help='Path to OMD.')
# args = parser.parse_args()
# filePath = args.file_path

# omfDIR = '/Users/tuomastalvitie/omf/omf'
# #Import OMD, add in frequency and gridballast control properties
# filePath = '/Users/tuomastalvitie/Desktop/UCS_Egan_Housed_Solar.omd'
# with open(filePath, 'r') as inFile:
# 	inFeeder = json.load(inFile)
# 	# inFeeder['tree']['8'].update({'module residential':'implicit_enduses NONE;'})
# 	# inFeeder['tree']['8'].update({'class player': 'double value;'})
# 	# inFeeder['tree']['8'].update({'object player':'name frequency_values; file frequency.PLAYER1;'})
# 	name_volt_dict ={}
# 	for key, value in inFeeder['tree'].iteritems():
# 		try:
# 			# if value['object'] == 'waterheater':
# 			# 	inFeeder['tree'][key].update({'enable_freq_control':True})
# 			# 	inFeeder['tree'][key].update({'freq_lowlimit':59.99})
# 			# 	inFeeder['tree'][key].update({'freq_uplimit':60.01})
# 			# 	inFeeder['tree'][key].update({'heat_mode':'ELECTRIC'})
# 			# 	inFeeder['tree'][key].update({'measured_frequency':'frequency_values.value'}) 
# 			name_volt_dict[value['name']] = {'Nominal_Voltage': value['nominal_voltage']}
# 		except KeyError:
# 				pass
# with open('outGLM.glm', "w") as outFile:
# 	outFile.write(feeder.sortedWrite(inFeeder['tree']))

# os.system('/Users/tuomastalvitie/omf/omf/solvers/gridlabd_gridballast/local_gd/bin/gridlabd outGLM.glm')

# data = pd.read_csv(('voltDump.csv'), skiprows=[0])
# for i, row in data['voltA_real'].iteritems():
# 	voltA_real = data.loc[i,'voltA_real']
# 	voltA_imag = data.loc[i,'voltA_imag']
# 	voltA_mag = np.sqrt(np.add((voltA_real*voltA_real), (voltA_imag*voltA_imag)))
# 	name_volt_dict[data.loc[i, 'node_name']].update({'Volt_A':voltA_mag})
# 	voltB_real = data.loc[i,'voltB_real']
# 	voltB_imag = data.loc[i,'voltB_imag']
# 	voltB_mag = np.sqrt(np.add((voltB_real*voltB_real), (voltB_imag*voltB_imag)))
# 	name_volt_dict[data.loc[i, 'node_name']].update({'Volt_B':voltB_mag})
# 	voltC_real = data.loc[i,'voltC_real']
# 	voltC_imag = data.loc[i,'voltC_imag']
# 	voltC_mag = np.sqrt(np.add((voltC_real*voltC_real), (voltC_imag*voltC_imag)))
# 	name_volt_dict[data.loc[i, 'node_name']].update({'Volt_C':voltC_mag})

# offenders = []
# for name, volt in name_volt_dict.iteritems():
# 	if (float(volt['Volt_A'])/float(volt['Nominal_Voltage'])) > 1.05:
# 		offenders.append(name)
# 	if (float(volt['Volt_B'])/float(volt['Nominal_Voltage'])) > 1.05:
# 		offenders.append(name)
# 	if (float(volt['Volt_C'])/float(volt['Nominal_Voltage'])) > 1.05:
# 		offenders.append(name)

# offenders = list(set(offenders))
# offenders = "object offenders {" + str(offenders) + "};"

# print offenders

# with open('outGLM.glm','wr') as glmFile:
# 			newfile = glmFile.read()
# 			newfile = newfile + offenders
# 			print data
# 			print type(data)



# with open('offenders.csv', 'w') as f:
# 	wr = csv.writer(f, quoting=csv.QUOTE_ALL)
# 	wr.writerow(offenders)


omf.distNetViz.viz('outGLM.glm') #or model.omd






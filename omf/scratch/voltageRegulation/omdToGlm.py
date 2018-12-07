
import json, math, os, argparse
from omf import feeder
from os.path import join as pJoin
import pandas as pd
import numpy as np
import csv
import omf
import voltageViz



# filePath = '/Users/tuomastalvitie/Desktop/UCS_Egan_Housed_Solar.omd'

#Parse Command Line
parser = argparse.ArgumentParser(description='Converts an OMD to GLM and runs it on gridlabd')
parser.add_argument('file_path', metavar='base', type=str,
                    help='Path to OMD. Put in quotes.')
args = parser.parse_args()
filePath = args.file_path

# filePath = pJoin(os.path.dirname(os.path.realpath(__file__)), 'UCS_Egan_Housed_Solar.omd')
# #Import OMD, add in frequency and gridballast control properties
with open(filePath, 'r') as inFile:
	inFeeder = json.load(inFile)
	inFeeder['tree'][u'01'] = {u'omftype': u'#include', u'argument': u'"hot_water_demand1.glm"'}
	inFeeder['tree'][u'011'] = {u'class': u'player', u'double': u'value'}# add in manually for now
	name_volt_dict ={}
	for key, value in inFeeder['tree'].iteritems():
		try:#disable freq control
			if (value['object'] == 'waterheater'):
				inFeeder['tree'][key].update({'heat_mode':'ELECTRIC'})
				inFeeder['tree'][key].update({'enable_volt_control':'true'})
				inFeeder['tree'][key].update({'volt_lowlimit':'113.99'})
				inFeeder['tree'][key].update({'volt_uplimit':'126.99'}) 
			elif (value['object']== 'ZIPload'):
				inFeeder['tree'][key].update({'enable_volt_control':'true'})
				inFeeder['tree'][key].update({'volt_lowlimit':'113.99'})
				inFeeder['tree'][key].update({'volt_uplimit':'126.99'})
			name_volt_dict[value['name']] = {'Nominal_Voltage': value['nominal_voltage']}
		except KeyError:
				pass
with open('outGLMtest.glm', "w") as outFile:
	outFile.write(feeder.sortedWrite(inFeeder['tree']))
os.system(omf.omfDir +'/solvers/gridlabd_gridballast/local_gd/bin/gridlabd outGLMtest.glm')


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
		offenders.append(tuple([name, float(volt['Volt_A'])/float(volt['Nominal_Voltage'])]))
	if (float(volt['Volt_B'])/float(volt['Nominal_Voltage'])) > 1.05:
		offenders.append(tuple([name, float(volt['Volt_B'])/float(volt['Nominal_Voltage'])]))
	if (float(volt['Volt_C'])/float(volt['Nominal_Voltage'])) > 1.05:
		offenders.append(tuple([name, float(volt['Volt_C'])/float(volt['Nominal_Voltage'])]))

# #Old Code for name recording only
# offenders = []
# for name, volt in name_volt_dict.iteritems():
# 	if (float(volt['Volt_A'])/float(volt['Nominal_Voltage'])) > 1.05:
# 		offenders.append(name)
# 	if (float(volt['Volt_B'])/float(volt['Nominal_Voltage'])) > 1.05:
# 		offenders.append(name)
# 	if (float(volt['Volt_C'])/float(volt['Nominal_Voltage'])) > 1.05:
# 		offenders.append(name)

#Print General information about offending nodes
offenders = list(set(offenders))
# print len(offenders)
isum = 0
offendersNames = []
for i in range(len(offenders)):
	isum = isum + offenders[i][1]
	offendersNames.append(offenders[i][0])
print ("average voltage overdose is by a factor of", isum/(len(offenders)))
print len(offendersNames)

# Write out file
with open('offenders.csv', 'w') as f:
	wr = csv.writer(f, quoting=csv.QUOTE_ALL)
	wr.writerow(offenders)


substation = pd.read_csv('measured_substation_power', comment='#', names=['timestamp', 'measured_real_power'])
substation_power = substation['measured_real_power'][0]
solar1 =  pd.read_csv('measured_solar_1', comment='#', names=['timestamp', 'measured_real_power'])
solar1_power = solar1['measured_real_power'][0]
solar2 =  pd.read_csv('measured_solar_2', comment='#', names=['timestamp', 'measured_real_power'])
solar2_power = solar2['measured_real_power'][0]
ziploads =  pd.read_csv('measured_load_ziploads', comment='#', names=['timestamp', 'measured_real_power'])
zipload_power = ziploads['measured_real_power'][0]
waterheaters = pd.read_csv('measured_load_waterheaters', comment='#', names=['timestamp', 'measured_real_power'])
waterheater_power = waterheaters['measured_real_power'][0]
HVAC = pd.read_csv('measured_HVAC', comment='#', names=['timestamp', 'heating_power', 'cooling_power'])
HVAC_power = HVAC['heating_power'][0], HVAC['cooling_power'][0]


print "substation power", substation_power
print "Solar1 Power", solar1_power
print "Solar2 Power", solar2_power
print "Zipload power", zipload_power+1000
print "waterheater power", waterheater_power*1000
print "HVAC Power", (HVAC_power[0]+HVAC_power[1])*1000


#Open Distnetviz
omf.distNetViz.viz('outGLMtest.glm') #or model.omd

#Remove Feeder
os.remove('outGLMtest.glm')

#Visualize Voltage Regulation
voltageRegVisual.voltRegViz(filePath)








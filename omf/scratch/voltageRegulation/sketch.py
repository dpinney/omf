#sketch
import json
import numpy as np 
import pandas as pd 
import csv
import json, math, os, argparse
from os.path import join as pJoin
import pandas as pd
import numpy as np
import csv
import re
from datetime import datetime 
import os
import omf


#good thing is that you can add everything in at end of feeder
#General approach, loop through homes, get name of home and meter it attached to.
# create solar object and inverter pair and attach to nreca synthetic meter
#add in at end of feeder

filePath = '/Users/tuomastalvitie/Desktop/gridballast_gld_simulations/Feeders/UCS_Egan_Housed_Solar.omd'

with open(filePath, 'r') as inFile:
		inFeeder = json.load(inFile)
		inFeeder['tree'][u'01'] = {u'omftype': u'#include', u'argument': u'"hot_water_demand1.glm"'}
		inFeeder['tree'][u'011'] = {u'class': u'player', u'double': u'value'}# add in manually for now
		name_volt_dict ={}
		solar_meters=[]
		wind_obs=[]
		substation = None 
		rooftopSolars = []
		rooftopInverters =[]
		for key, value in inFeeder['tree'].iteritems():
			if 'name' in value and 'solar' in value['name']:
				inverter_ob = value['parent']
				for key, value in inFeeder['tree'].iteritems():
					if 'name' in value and value['name']==inverter_ob:
						solar_meters.append(value['parent'])
			if 'name' in value and 'wind' in value['name']:
				wind_obs.append(value['name'])
			if 'name' in value and 'nominal_voltage' in value:
				name_volt_dict[value['name']] = {'Nominal_Voltage': value['nominal_voltage']}
			if 'object' in value and (value['object'] == 'waterheater'):
				inFeeder['tree'][key].update({'heat_mode':'ELECTRIC'})
				inFeeder['tree'][key].update({'enable_volt_control':'true'})
				inFeeder['tree'][key].update({'volt_lowlimit':'113.99'})
				inFeeder['tree'][key].update({'volt_uplimit':'126.99'}) 
			if'object' in value and (value['object']== 'ZIPload'):
				inFeeder['tree'][key].update({'enable_volt_control':'true'})
				inFeeder['tree'][key].update({'volt_lowlimit':'113.99'})
				inFeeder['tree'][key].update({'volt_uplimit':'126.99'})
			if 'object' in value and (value['object']== 'house'):
				houseMeter = value['parent']
				houseName = value['name']
				houseLon = value['longitude']
				houseLat = value['latitude']
				rooftopSolar_inverter = houseName+"_rooftop_inverter;"
				rooftopSolars.append("object solar {\n\tname "+houseName+"_rooftopSolar;\n\tparent "+rooftopSolar_inverter+"\n\tgenerator status ONLINE;\n\tefficiency 0.2;\n\tlongitude "+houseLon+";\n\tgenerator_mode SUPPLY_DRIVEN;\n\tpanel_type SINGLE_CRYSTAL_SILICON;\n\tlatitude "+houseLat+";\n\tarea 2;\n\t};\n")
				rooftopInverters.append("object inverter {\n\tphases AS;\n\tpower_factor 1.0;\n\tname "+rooftopSolar_inverter+"\n\tparent "+houseMeter+"\n\tinverter_type PWM;\n\tlongitude "+houseLon+";\n\tgenerator_mode CONSTANT_PF;\n\tlatitude "+houseLat+";\n\t};\n")
			if 'argument' in value and ('minimum_timestep' in value['argument']):
					interval = int(re.search(r'\d+', value['argument']).group())
			if 'bustype' in value and 'SWING' in value['bustype']:
				substation = value['name']
				value['object'] = 'meter'
			

print rooftopSolars
print rooftopInverters


# os.system(omf.omfDir +'/solvers/gridlabd_gridballast/local_gd/bin/gridlabd testGLM.glm')







# arrr = np.zeros((3,3))
# path = 'np.'
# path2 = 'append(arrr, (1,2,3))'


# gldBinary=omf.omfDir + '/solvers/gridlabd_gridballast/local_gd/bin/gridabd'



# gldbinary='omf.solvers.gridlabd_gridballast'

# join = lambda *args: pJoin(*args).replace("/","")
# chunk=".runInFilesystem(tree, attachments=attachments, workDir=workDir)"
# exec('gridlabOut =' + join(gldbinary, chunk)) in globals(), locals()

# join = lambda *args: pJoin(*args).replace("/","")
# a3 = join(path, path2)
# exec('a3=' + join(path, path2))
# print a3

#1 try simple pjoin with string first. 
#2 try the lambda function as specified above




# print datetime.today()


# filePath = '/Users/tuomastalvitie/Desktop/UCS_Egan_Housed_Solar.omd'



# with open(filePath, 'r') as inFile:
# 	inFeeder = json.load(inFile)
# 	# inFeeder['tree'][u'01'] = {u'omftype': u'#include', u'argument': u'"hot_water_demand1.glm"'}
# 	# inFeeder['tree'][u'011'] = {u'class': u'player', u'double': u'value'}# add in manually for now
# 	name_volt_dict ={}
# 	solar_meters=[]
# 	wind_obs=[]
# 	substation = None 
# 	for key, value in inFeeder['tree'].iteritems():
# 		if 'name' in value and 'solar' in value['name']:
# 			inverter_ob = value['parent']
# 			for key, value in inFeeder['tree'].iteritems():
# 				if 'name' in value and value['name']==inverter_ob:
# 					solar_meters.append(value['parent'])
# 		if 'name' in value and 'wind' in value['name']:
# 			wind_obs.append(value['name'])
# 		if 'name' in value and 'nominal_voltage' in value:
# 			name_volt_dict[value['name']] = {'Nominal_Voltage': value['nominal_voltage']}
# # 		if 'object' in value and (value['object'] == 'waterheater'):
# 			inFeeder['tree'][key].update({'heat_mode':'ELECTRIC'})
# 			inFeeder['tree'][key].update({'enable_volt_control':'true'})
# 			inFeeder['tree'][key].update({'volt_lowlimit':'113.99'})
# 			inFeeder['tree'][key].update({'volt_uplimit':'126.99'}) 
# 		if'object' in value and (value['object']== 'ZIPload'):
# 			inFeeder['tree'][key].update({'enable_volt_control':'true'})
# 			inFeeder['tree'][key].update({'volt_lowlimit':'113.99'})
# 			inFeeder['tree'][key].update({'volt_uplimit':'126.99'})
# 		if 'argument' in value and ('minimum_timestep' in value['argument']):
# 				interval = int(re.search(r'\d+', value['argument']).group())
# 		if 'bustype' in value and 'SWING' in value['bustype']:
# 			substation = value['name']
# 			print value['object']

	# collectorw=("object collector {\n\tname collector_Waterheater;\n\tgroup class=waterheater;\n\tproperty sum(actual_load);\n\tinterval "+str(interval)+";\n\tfile 'measured_load_waterheaters.csv';\n};\n")
	# collectorz=("object collector {\n\tname collector_ZIPloads;\n\tgroup class=ZIPload;\n\tproperty sum(base_power);\n\tinterval "+str(interval)+";\n\tfile 'measured_load_ziploads.csv';\n};\n")
	# collectorw=("object collector {\n\tname collector_HVAC;\n\tgroup class=house;\n\tproperty sum(heating_demand), sum(cooling_demand);\n\tinterval "+str(interval)+";\n\tfile 'measured_HVAC.csv';\n};\n")
	# recordersub=("object recorder {\n\tinterval "+str(interval)+";\n\tproperty measured_real_power;\n\tfile 'measured_substation_power.csv';\n\tparent "+str(substation)+";\n\t};\n")
	# recorders = []
	# recorderw=[]
	# for i in range(len(solar_meters)):
	# 	print i
	# 	recorders.append(("object recorder {\n\tinterval "+str(interval)+";\n\tproperty measured_real_power;\n\tfile 'measured_solar_"+str(i)+".csv';\n\tparent "+str(solar_meters[i])+";\n\t};\n"))
	# for i in range(len(wind_obs)):
	# 	recorderw.append(("object recorder {\n\tinterval "+str(interval)+";\n\tproperty Pconv;\n\tfile 'measured_wind_"+str(i)+".csv';\n\tparent "+str(wind_obs[i])+";\n\t};\n"))


# os.remove('outGLMtest.glm')



'''power across swing bus = total load + system losses - distributed generation 



-2.7478e+07 [W] = (+9813.18[kW from waterheaters] + +3240.81[kW from ZIPloads] + (+18725.9 ++8373.37) [kW] from HVAC) + (systems losses) - (+13555.7[W from wind] + 4.74729e+07 [W from solar] + 4.74729e+07 [W from solar2])


-27478000 [W] = (9813180 [W] + 3240810 [W] + 18725900[W] + 8373370 [W]) + (system losses) - (13555.7 [W] + 2*4747290 [W])


'''

# a = ((9813180+3240810+18725900+8373370)-(13555.7 + 2*4747290))
# b = -27478000
# print a 
# print a - b

# c = 9813180+3240810+18725900+8373370
# print c
# d = 13555.7 + 2*4747290
# print d
# e=27478000

# # -27478000 [W] = (9813180 [W] + 3240810 [W] + 18725900[W] + 8373370 [W]) + (system losses) - (13555.7 [W] + 2*4747290 [W])


# print c-d

# f= c-d

# print e-f


# data = pd.read_csv(('measured_solar_1.csv'), skiprows=[0], error_bad_lines=False)
# for i in data:
# 	print i



''' 
DG.               					  9,508,135.7 X
Load.  								 40,153,260.0 Y
Load-DG							     30,645,124.3 
	+13555.7[W from wind] + 4.74729e+07 [W from solar] + 4.74729e+07 [W from solar2]
powerflow across substation			 27,478,000.0
system losses						  3,167,124.3
Gridballlast devices on 				100% of WH ZL Z
Total number of GB devices				6420
Total number of residential objects		8560
Offenders ===  774	(1041)					774/3798 aka 20.4% of NODE objects are breaking the law 

basically when total system power is around 60,000,000 W or +30% of total load, GB can help all but 30% of loads. also gridballast only causes
46 node decrease. however after lower power it goes friom 1041 to 774

Basically, the difference is negligible


Average violation by offenders is aound 11% over limit. When lower power on solar objects, violation is about 8%
 Homes would need to be able to absorb that much.
'''
#LOOK AT CASE WHERE THERE ARE NO RENEWABLES



'''
3,545,854.3 [W]
-27,478,000 [W]
'''

# filePath = '/Users/tuomastalvitie/Desktop/UCS_Egan_Housed_Solar.omd'
# with open(filePath, 'r') as inFile:
# 	inFeeder = json.load(inFile)
# # 	inFeeder['tree']['8'].update({'module residential':'implicit_enduses NONE;'})
# # 	inFeeder['tree']['8'].update({'class player': 'double value;'})
# # 	inFeeder['tree']['8'].update({'object player':'name frequency_values; file frequency.PLAYER1;'})
# 	name_volt_dict ={}
# 	for key, value in inFeeder['tree'].iteritems():
# 		try:
# # 			if value['object'] == 'waterheater':
# # 				inFeeder['tree'][key].update({'enable_freq_control':True})
# # 				inFeeder['tree'][key].update({'freq_lowlimit':59.99})
# # 				inFeeder['tree'][key].update({'freq_uplimit':60.01})
# # 				inFeeder['tree'][key].update({'heat_mode':'ELECTRIC'})
# # 				inFeeder['tree'][key].update({'measured_frequency':'frequency_values.value'}) 
# 			name_volt_dict[value['name']] = {'Nominal_Voltage': value['nominal_voltage']}
# 		except KeyError:
# 				pass

# with open('outGLMnorm.glm', "w") as outFile:	
#  	outFile.write(feeder.sortedWrite(inFeeder['tree']))

# with open('outGLMnorm.glm', "r") as inFile:
# 	for row in inFile:
# # 		print row
# os.system(omf.omfDir +'/solvers/gridlabd_gridballast/local_gd/bin/gridlabd /Users/tuomastalvitie/Desktop/gridballast_gld_simulations/Feeders/outGLM.glm')



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
# print len(offenders)

# with open('offenders.csv', 'w') as f:
# 	wr = csv.writer(f, quoting=csv.QUOTE_ALL)
# 	wr.writerow(offenders)

# substation = pd.read_csv(('measured_substation_power.csv'), comment='#', names=['timestamp', 'measured_real_power'])
# substation_power = substation['measured_real_power'][0]
# solar1 =  pd.read_csv(('measured_solar_0.csv'), comment='#', names=['timestamp', 'measured_real_power'])
# solar1_power = solar1['measured_real_power'][0]
# solar2 =  pd.read_csv(('measured_solar_1.csv'), comment='#', names=['timestamp', 'measured_real_power'])
# solar2_power = solar2['measured_real_power'][0]
# ziploads =  pd.read_csv(('measured_load_ziploads.csv'), comment='#', names=['timestamp', 'measured_real_power'])
# zipload_power = ziploads['measured_real_power'][0]
# waterheaters = pd.read_csv(('measured_load_waterheaters.csv'), comment='#', names=['timestamp', 'measured_real_power'])
# waterheater_power = waterheaters['measured_real_power'][0]
# HVAC = pd.read_csv(('measured_HVAC.csv'), comment='#', names=['timestamp', 'heating_power', 'cooling_power'])
# HVAC_power = HVAC['heating_power'][0], HVAC['cooling_power'][0]
# wind = pd.read_csv(('measured_wind_0.csv'), comment='#', names=['timestamp', 'Pconv'])
# wind_power = wind['Pconv'][0]

# #Print Results
# print "substation power", substation_power
# print "Solar1 Power", solar1_power
# print "Solar2 Power", solar2_power
# print "Zipload power", zipload_power*1000
# print "waterheater power", waterheater_power*1000
# print "HVAC Power", (HVAC_power[0]+HVAC_power[1])*1000
# #convert results to watts, write to dataframe
# df=pd.DataFrame(columns=('result', 'value'))
# df.loc[0]=["number of offenders", len(offenders)]
# df.loc[1]=["substation power", substation_power]
# df.loc[2]=["Solar1 Power", solar1_power]
# df.loc[3]=["Solar2 Power", solar2_power]
# df.loc[4]=["Zipload power", zipload_power*1000]
# df.loc[5]=["waterheater power", waterheater_power*1000]
# df.loc[6]=["HVAC Power", (HVAC_power[0]+HVAC_power[1])*1000]
# df.loc[7]=['wind power', wind_power]
# df.loc[8]=['current time', datetime.today()]
# #Write Dataframe to .csv
# df.to_csv('Results.csv')



##################

#Checking the voltdump

# import csv

# substation = pd.read_csv('measured_substation_power', comment='#', names=['timestamp', 'measured_real_power'])
# substation_power = substation['measured_real_power'][0]
# solar1 =  pd.read_csv('measured_solar_1', comment='#', names=['timestamp', 'measured_real_power'])
# solar1_power = solar1['measured_real_power'][0]
# solar2 =  pd.read_csv('measured_solar_2', comment='#', names=['timestamp', 'measured_real_power'])
# solar2_power = solar2['measured_real_power'][0]
# ziploads =  pd.read_csv('measured_load_ziploads', comment='#', names=['timestamp', 'measured_real_power'])
# zipload_power = ziploads['measured_real_power'][0]
# waterheaters = pd.read_csv('measured_load_waterheaters', comment='#', names=['timestamp', 'measured_real_power'])
# waterheater_power = waterheaters['measured_real_power'][0]
# HVAC = pd.read_csv('measured_HVAC', comment='#', names=['timestamp', 'heating_power', 'cooling_power'])
# HVAC_power = HVAC['heating_power'][0], HVAC['cooling_power'][0]


# print substation_power
# print solar1_power
# print solar2_power
# print zipload_power
# print type(waterheater_power)
# print HVAC_power
# print type(HVAC_power[0])


# f1voltareal=f1['voltA_real']
# f2voltareal=f2['voltA_real']

# a = list(zip(f1voltareal, f2voltareal))

# for i in a: 
# 	print i


# if any((f1voltareal == f2voltareal)) == False:
# 	print "oh no"
# else:
# 	print " oh yes"


# print all(f1voltareal==f2voltareal)

# # 	testfile.ix[:,1] = lista

# # 	print testfile
# # testfile.to_csv('frequency.PLAYER1', sep='\t')	

# omf.distNetViz.viz('outGLMnorm.glm') #or model.omd

# omfDIR = '/Users/tuomastalvitie/omf/omf'
# #Import OMD, add in frequency and gridballast control properties
# filePath = '/Users/tuomastalvitie/Desktop/UCS_Egan_Housed_Solar.omd'
# with open(filePath, 'r') as inFile:
# 	inFeeder = json.load(inFile)
# 	inFeeder['tree']['8'].update({'module residential':'implicit_enduses NONE;'})
# 	inFeeder['tree']['8'].update({'class player': 'double value;'})
# 	inFeeder['tree']['8'].update({'object player':'name frequency_values; file frequency.PLAYER1;'})
# 	print inFeeder['tree']['8']
# 	name_volt_dict ={}
# 	for key, value in inFeeder['tree'].iteritems():
# 		try:
# 			if value['object'] == 'waterheater':
# 				inFeeder['tree'][key].update({'enable_freq_control':True})
# 				inFeeder['tree'][key].update({'freq_lowlimit':59.99})
# 				inFeeder['tree'][key].update({'freq_uplimit':60.01})
# 				inFeeder['tree'][key].update({'heat_mode':'ELECTRIC'})
# 				inFeeder['tree'][key].update({'measured_frequency':'frequency_values.value'}) 
# 			name_volt_dict[value['name']] = {'Nominal_Voltage': value['nominal_voltage']}
# 		except KeyError:
# 				pass

# with open('/Users/tuomastalvitie/Desktop/UCS_Egan_Housed_Solar.omd', "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		inFeeder['tree']['8'].update({'module': 'residential'})
# 		inFeeder['tree']['8'].update({'implicit_enduses' : 'NONE'})
# 		name_volt_dict ={}
# 		for key, value in inFeeder['tree'].iteritems():
# 			try:
# 				if value['object'] == 'waterheater':
# 					inFeeder['tree'][key].update({'enable_freq_control':True})
# 					inFeeder['tree'][key].update({'freq_lowlimit':59.97})
# 					inFeeder['tree'][key].update({'freq_uplimit':60.03})
# 					inFeeder['tree'][key].update({'heat_mode':'ELECTRIC'})
# 					inFeeder['tree'][key].update({'measured_frequency':'frequency_values.value'})
# 					# print key, value
# 				name_volt_dict[value['name']] = {'Nominal_Voltage': value['nominal_voltage']}
# 			except KeyError:
# 				pass
# # print name_volt_dict

# # with open('glmTEST.glm', "w") as outFile:
# # 	outFile.write(feeder.sortedWrite(inFeeder['tree']))



# data = pd.read_csv('voltDump.csv', skiprows=[0])

# # # print data.head()
# # # print list(data)

# # #check for transformers, must be within 5%
# # #GB enabled offenders len == 562
# # #Non gb enabled offenders len == 537

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
# 		print name
# 		offenders.append(name)
# 	if (float(volt['Volt_B'])/float(volt['Nominal_Voltage'])) > 1.05:
# 		print name
# 		offenders.append(name)
# 	if (float(volt['Volt_C'])/float(volt['Nominal_Voltage'])) > 1.05:
# 		print name
# 		offenders.append(name)
# print offenders
# print len(offenders)
	

# offenders = list(set(offenders))
# print offenders
# with open('offenders.csv', 'w') as f:
# 	wr = csv.writer(f, quoting=csv.QUOTE_ALL)
# 	wr.writerow(offenders)

# print offenders


# with open('offenders.csv', 'r') as f:
# 	csv_reader1 = csv.reader(f, delimiter=',')
# 	offenders1 = []
# 	for row in csv_reader1:
# 		for line in row:
# 			offenders1.append(line)

	
# with open('offendersVoltReg.csv', 'r') as f:
# 	csv_reader2 = csv.reader(f, delimiter=',')
# 	offenders2 = []
# 	for row in csv_reader2:
# 		for line in row:
# 			offenders2.append(line)

# # for i, j in [(offenders1, offenders2) for i in offenders1 for j in offenders2] :
# # 	print i, j

# for i, j in map(None, offenders1, offenders2):
# 	print i, j

# print len(offenders1)
# print len(offenders2)





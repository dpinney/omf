
import json, math, os, argparse
from omf import feeder
from os.path import join as pJoin
import pandas as pd
import numpy as np
import csv
import omf
import voltageRegVisual
import re
from datetime import datetime
from voltageDropVoltageViz import drawPlot

#Run 11-1, stop results at noon, run at hour resolution

def ConvertAndwork(filePath, gb_on_off='on'):
	"""
	Converts omd to glm, adds in necessary recorder, collector, and
	attributes+parameters for gridballast gld to run on waterheaters and
	ziploads
	"""
	with open(filePath, 'r') as inFile:
		if gb_on_off == 'on':
			gb_status = 'true'
		else:
			gb_status = 'false'
		inFeeder = json.load(inFile)
		inFeeder['tree'][u'01'] = {u'omftype': u'#include', u'argument': u'"hot_water_demand1.glm"'}
		inFeeder['tree'][u'011'] = {u'class': u'player', u'double': u'value'}# add in manually for now
		name_volt_dict ={}
		solar_meters=[]
		wind_obs=[]
		substation = None 
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
				inFeeder['tree'][key].update({'enable_volt_control':gb_status})
				inFeeder['tree'][key].update({'volt_lowlimit':'113.99'})
				inFeeder['tree'][key].update({'volt_uplimit':'126.99'}) 
			if'object' in value and (value['object']== 'ZIPload'):
				inFeeder['tree'][key].update({'enable_volt_control':gb_status})
				inFeeder['tree'][key].update({'volt_lowlimit':'113.99'})
				inFeeder['tree'][key].update({'volt_uplimit':'126.99'})
			if 'object' in value and (value['object']== 'house'):
				houseMeter = value['parent']
			if 'argument' in value and ('minimum_timestep' in value['argument']):
					interval = int(re.search(r'\d+', value['argument']).group())
			if 'bustype' in value and 'SWING' in value['bustype']:
				substation = value['name']
				value['object'] = 'meter'


		collectorwat=("object collector {\n\tname collector_Waterheater;\n\tgroup class=waterheater;\n\tproperty sum(actual_load);\n\tinterval "+str(interval)+";\n\tfile out_load_waterheaters.csv;\n};\n")
		collectorz=("object collector {\n\tname collector_ZIPloads;\n\tgroup class=ZIPload;\n\tproperty sum(base_power);\n\tinterval "+str(interval)+";\n\tfile out_load_ziploads.csv;\n};\n")
		collectorh=("object collector {\n\tname collector_HVAC;\n\tgroup class=house;\n\tproperty sum(heating_demand), sum(cooling_demand);\n\tinterval "+str(interval)+";\n\tfile out_HVAC.csv;\n};\n")
		recordersub=("object recorder {\n\tinterval "+str(interval)+";\n\tproperty measured_real_power;\n\tfile out_substation_power.csv;\n\tparent "+str(substation)+";\n\t};\n")
		recorders = []
		recorderw=[]
		for i in range(len(solar_meters)):
			recorders.append(("object recorder {\n\tinterval "+str(interval)+";\n\tproperty measured_real_power;\n\tfile out_solar_gen_"+str(i)+".csv;\n\tparent "+str(solar_meters[i])+";\n\t};\n"))
		for i in range(len(wind_obs)):
			recorderw.append(("object recorder {\n\tinterval "+str(interval)+";\n\tproperty Pconv;\n\tfile out_wind_gen"+str(i)+".csv;\n\tparent "+str(wind_obs[i])+";\n\t};\n"))

	with open('outGLM.glm', "w") as outFile:
		addedString = collectorwat+collectorz+collectorh+recordersub
		for i in recorders:
			addedString = addedString+i
		for i in recorderw:
			addedString = addedString + i
		outFile.write(feeder.sortedWrite(inFeeder['tree'])+addedString)

	os.system(omf.omfDir +'/solvers/gridlabd_gridballast/local_gd/bin/gridlabd outGLM.glm')

	return name_volt_dict

def ListOffenders(name_volt_dict):
	#Finds objects that carry too much voltage, these are called 'Offenders', write to disk
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
	offendersGen = []
	for name, volt in name_volt_dict.iteritems():
		if (float(volt['Volt_A'])/float(volt['Nominal_Voltage'])) > 1.05:
			offenders.append(tuple([name, float(volt['Volt_A'])/float(volt['Nominal_Voltage'])]))
			offendersGen.append(name)
		if (float(volt['Volt_B'])/float(volt['Nominal_Voltage'])) > 1.05:
			offenders.append(tuple([name, float(volt['Volt_B'])/float(volt['Nominal_Voltage'])]))
			offendersGen.append(name)
		if (float(volt['Volt_C'])/float(volt['Nominal_Voltage'])) > 1.05:
			offenders.append(tuple([name, float(volt['Volt_C'])/float(volt['Nominal_Voltage'])]))
			offendersGen.append(name)



	#Print General information about offending nodes
	offenders = list(set(offenders))
	# print len(offenders)
	isum = 0
	offendersNames = []
	for i in range(len(offenders)):
		isum = isum + offenders[i][1]
		offendersNames.append(offenders[i][0])
	offendersGen = list(set(offendersGen))
	#print ("average voltage overdose is by a factor of", isum/(len(offenders)))
	print ("Number of offenders is", len(offendersGen))
	# Write out file
	voltSum = data['voltA_real'].sum() + data['voltB_real'].sum() + data['voltC_real'].sum()
	print "volt total", voltSum
	with open('offenders.csv', 'w') as f:
		wr = csv.writer(f, quoting=csv.QUOTE_ALL)
		wr.writerow(offenders)
	return offendersGen

def writeResults(offendersGen):
	#Write powerflow results for generation and waterheater, zipload, and hvac (house) load objects
	#need to fix up testing for if file exsists based upon name written
	dir_path = os.path.dirname(os.path.realpath(__file__))
	substation = pd.read_csv(('out_substation_power.csv'), comment='#', names=['timestamp', 'measured_real_power'])
	substation_power = substation['measured_real_power'][0]
	ziploads =  pd.read_csv(('out_load_ziploads.csv'), comment='#', names=['timestamp', 'measured_real_power'])
	zipload_power = ziploads['measured_real_power'][0]
	waterheaters = pd.read_csv(('out_load_waterheaters.csv'), comment='#', names=['timestamp', 'measured_real_power'])
	waterheater_power = waterheaters['measured_real_power'][0]
	HVAC = pd.read_csv(('out_HVAC.csv'), comment='#', names=['timestamp', 'heating_power', 'cooling_power'])
	HVAC_power = HVAC['heating_power'][0], HVAC['cooling_power'][0]
	wind_power = []
	solar_power = []
	for file in os.listdir(dir_path):
		if 'out_wind' in file:
			wind = pd.read_csv((file), comment='#', names=['timestamp', 'Pconv'])['Pconv'][0]
			wind_power.append(wind)
	for file in os.listdir(dir_path):
		if 'out_solar' in file:
			solar = pd.read_csv((file), comment='#', names=['timestamp', 'measured_real_power'])['measured_real_power'][0]
			solar_power.append(solar)
	#Print Results
	print "Substation power", substation_power
	print "Zipload Power Use", zipload_power*1000
	print "Waterheater Power Use", waterheater_power*1000
	print "HVAC Power Use", (HVAC_power[0]+HVAC_power[1])*1000
	#convert results to watts, write to dataframe
	df=pd.DataFrame(columns=('result', 'value'))
	df.loc[1]=['current time', datetime.today()]
	df.loc[2]=["Number of offenders", len(offendersGen)]
	df.loc[3]=["Substation Power", substation_power]
	df.loc[4]=["Zipload Power Use", zipload_power*1000]
	df.loc[5]=["Waterheater Power Use", waterheater_power*1000]
	df.loc[6]=["HVAC Power Use", (HVAC_power[0]+HVAC_power[1])*1000]
	for i, j in enumerate(solar_power):
		df.loc[len(df)+1]=["Solar Power" +str(i), j]
		print ("Solar Power" +str(i), j)
	for i, j in enumerate(wind_power):
		df.loc[len(df)+1]=["Wind Power"+str(i), j]
		print ("Wind Power"+str(i), j)
	# if os.path.isfile('measured_wind_0'): 
	# 	#temporary test
	# 	df.loc[7]=['wind power', wind_power]
	
	#Write Dataframe to .csv


	df.to_csv('Results.csv')



def _debugging(filePath, gb_on_off='on'):
	#Begin Main Function
	name_volt_dict = ConvertAndwork(filePath, gb_on_off)
	offendersGen = ListOffenders(name_volt_dict)
	writeResults(offendersGen)
	# Open Distnetviz on glm
	omf.distNetViz.viz('outGLM.glm') #or model.omd
	# Visualize Voltage Regulation
	voltRegViz('outGLM_rooftop.glm')
	# Remove Feeder
	os.remove('outGLM.glm')


def voltRegViz(FNAME):
	chart = drawPlot(FNAME, neatoLayout=True, edgeCol=False, nodeLabs=None, edgeLabs=None, nodeCol = "perUnitVoltage", customColormap=True, rezSqIn=400)
	chart.savefig("./VOLTOUT.png")
	validFiles = ['_minutes.PLAYER', 'climate.tmy2', 'frequency.PLAYER1', "hot_water_demand1.glm", 'schedulesResponsiveLoads.glm']
	for file in os.listdir(pJoin(dir_path, '_voltViz')):
		if file not in validFiles : 
			os.remove(pJoin('_voltViz', file))
	
if __name__ == '__main__':
	# no try except, instead do if argument missing, then 
	try: 
		#Parse Command Line
		parser = argparse.ArgumentParser(description='Converts an OMD to GLM and runs it on gridlabd')
		parser.add_argument('file_path', metavar='base', type=str,
		                    help='Path to OMD. Put in quotes.')
		parser.add_argument('gridballast_on_off', metavar='gb', type=str, help='turn gb on or off, type on or off')
		args = parser.parse_args()
		filePath = args.file_path
		gb_on_off = args.gridballast_on_off
		_debugging(filePath, gb_on_off)
	except:
		# _myDir = os.path.dirname(os.path.realpath(__file__))
		# _omfDir = os.path.dirname(os.path.dirname(_myDir))
		# _feederDir = pJoin(_omfDir, 'static/publicFeeders/Olin Barre GH EOL Solar.omd')
		_debugging('/Users/tuomastalvitie/Desktop/gridballast_gld_simulations/Feeders/UCS_Egan_Housed_Solar.omd', gb_on_off='off')








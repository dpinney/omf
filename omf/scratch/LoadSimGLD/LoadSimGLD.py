import os, omf, csv
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import argparse
import sys
import pvlib


_parameters = ["GasHeat", "HeatPump", "Resistance", "AC_electric", "AC_HeatPump", "Waterheater", "EV", "Refrigerator",  "Clotheswasher", "Dryer", "Freezer"]
_myDir = os.path.dirname(os.path.realpath(__file__))

def runGld(modelType):
	# Run GridLAB-D on the GLM.
	if modelType == 'GasHeat':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'GAS'
		graphType = 'out_super_house_heat'
		system_type_name = 'Gas Heating'
	elif modelType == 'HeatPump':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'HEAT_PUMP'
		graphType = 'out_super_house_heat'
		system_type_name = 'Heat Pump'
	elif modelType == 'Resistance':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'RESISTANCE'
		graphType = 'out_super_house_heat'
		system_type_name = 'Resistance'
	elif modelType == 'AC_electric':
		cooling_system_type = "ELECTRIC"
		heating_system_type = '' 
		graphType = 'out_super_house_cool'
		system_type_name = 'Electric'
	elif modelType == 'AC_HeatPump':
		cooling_system_type = "HEAT_PUMP"
		heating_system_type = ''
		graphType = 'out_super_house_cool'
		system_type_name = 'Heat Pump'
	elif modelType == 'Waterheater':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'RESISTANCE'
		graphType = 'waterheater'
	elif modelType == 'EV':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'RESISTANCE'
		graphType = 'EV'
	elif modelType =='Refrigerator':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'RESISTANCE'
		graphType = 'Refrigerator'
	elif modelType == 'Clotheswasher':
		cooling_system_type= "ELECTRIC"
		heating_system_type = "RESISTANCE"
		graphType = 'clotheswasher'
	elif modelType == 'Dryer':
		cooling_system_type = "ELECTRIC"
		heating_system_type = "RESISTANCE"
		graphType = 'dryer'
	elif modelType == 'Freezer':
		cooling_system_type = "ELECTRIC"
		heating_system_type = "RESISTANCE"
		graphType = 'freezer'




	with open('in_super_house.glm', 'r') as myfile:
	    data=myfile.read()


	    """ 
	    SUPER HOUSE OBJECT BELOW
	    The following is the house model, it is inserted into the .glm that is run in any situation. 
	    If you would like to edit the properties of the house, please edit the text below.
	    	
	    """
	    data = data + ("""\nobject house {\n\tglass_type 2;\n\tcooling_COP 3.8;\n\thvac_breaker_rating 1000;\t
		cooling_system_type """+cooling_system_type+""";\t
		total_thermal_mass_per_floor_area 3.504;\t
		cooling_setpoint cooling6*2.89+69.19;\t
		air_temperature 71.22;\t
		ceiling_height 8;\t
		Rdoors 10.51;\t
		heating_system_type """+heating_system_type+""";\t
		glazing_layers 3;\t
		glazing_treatment 2;\t
		heating_setpoint heating6*0.19+59.01;\t
		groupid Residential;\t
		schedule_skew -57.2977315002;\t
		window_frame 4;\t
		parent R4-25-00-1_tm_1;\t
		floor_area 8000.0;\t
		number_of_stories 1;\t
		mass_temperature 71.22;\t
		name house0;\t
		Rfloor 35.59;\t
		airchange_per_hour 0.23;\t
		Rroof 50.34;\t
		Rwall 27.33;\t
		breaker_amps 1000;\t
		over_sizing_factor 0.1;
	};""")

	with open('temp_super_house.glm', 'w') as outFile:
		outFile.write(data)

	os.system('gridlabd '+'temp_super_house.glm')
	os.remove('temp_super_house.glm')
	return graphHandler(graphType, heating_system_type, cooling_system_type, system_type_name)

def graphHandler(graphType, heating_system_type = None, cooling_system_type = None, system_type_name = None):
	location = getCity()
	if graphType == 'out_super_house_heat':
		plotLoadHouseHeat(heating_system_type, system_type_name, location)
		plotTemp()
	if graphType == 'out_super_house_cool':
		plotLoadHouseCool(cooling_system_type, system_type_name, location)
		plotTemp()
	elif graphType == 'waterheater':
		plotLoadWaterheater(location)
	elif graphType == 'EV':
		plotLoadEV(location)
	elif graphType == 'Refrigerator':
		plotFridge(location)
	elif graphType == 'clotheswasher':
		plotClotheswasher(location)
	elif graphType =='dryer':
		plotDryer(location)
	elif graphType == 'freezer':
		plotFreezer(location)


def plotLoadHouseHeat(heating_system_type, system_type_name, location):
	# Get the data
	fileOb = open('out_super_house.csv')
	for x in range(8):
	# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	# Plot Heat and AC load
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [float(x.get('heating_demand', 0.0)) for x in data], '-', label="Heating")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.suptitle(location +' ' + system_type_name +' Heating System')
	plt.title('Path to raw data is in '+ _myDir, fontsize =10 )
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (kW)')
	plt.show()

def plotLoadHouseCool(cooling_system_type, system_type_name, location):
		# Get the data
	fileOb = open('out_super_house.csv')
	for x in range(8):
	# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	# Plot Heat and AC load
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [float(x.get(' cooling_demand', 0.0)) for x in data], '-', label="Cooling")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.suptitle(location +' ' + system_type_name +' Cooling System')
	plt.title('Path to raw data is in '+ _myDir, fontsize =10 )
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (kW)')
	plt.show()

def plotLoadWaterheater(location):
	fileOb = open('out_super_house_waterheater.csv')
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [float(x.get('actual_load', 0.0)) for x in data], '-', label="Load")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.suptitle(location +' waterheater load in (kW)')
	plt.title('Path to raw data is in '+ _myDir, fontsize =10 )
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (kW)')
	plt.show()

def plotLoadEV(location):
	fileOb = open('out_super_house_EV.csv')
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [float(x.get('charge_rate', 0.0)) for x in data], '-', label="Load")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.suptitle(location +' EV load in (W)')
	plt.title('Path to raw data is in '+ _myDir, fontsize =10 )
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (W)')
	plt.show()

def plotFridge(location):
	fileOb = open('out_load_fridge.csv')
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [complex(x.get('base_power', 0.0)).real for x in data], '-', label="Load")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.suptitle(location + ' Fridge load in (kW)')
	plt.title('Path to raw data is in '+ _myDir, fontsize =10 )
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (kW)')
	plt.show()

def plotFreezer(location):
	fileOb = open('out_load_freezer.csv')
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [complex(x.get('base_power', 0.0)).real for x in data], '-', label="Load")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.suptitle(location + ' Freezer load in (kW)')
	plt.title('Path to raw data is in '+ _myDir, fontsize =10 )
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (kW)')
	plt.show()

def plotClotheswasher(location):
	fileOb = open('out_load_clotheswasher.csv')
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [complex(x.get('base_power', 0.0)).real for x in data], '-', label="Load")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.suptitle(location + ' Clotheswasher load in (kW)')
	plt.title('Path to raw data is in '+ _myDir, fontsize =10 )
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (kW)')
	plt.show()

def plotDryer(location):
	fileOb = open('out_load_dryer.csv')
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [complex(x.get('base_power', 0.0)).real for x in data], '-', label="Load")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.suptitle(location + ' Dryer load in (kW)')
	plt.title('Path to raw data is in '+ _myDir, fontsize =10 )
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (kW)')
	plt.show()



def plotTemp():
	# Get the data
	fileOb = open('out_super_house.csv')
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	plt.title('New Years Day, Huntsville, AL, Temperatures')
	formatter = mdates.DateFormatter('%Y-%m-%d')
	dates = mdates.datestr2num([''.join(x.get('# timestamp')) for x in data])
	plt.plot_date(dates, [float(x.get(' air_temperature', 0.0)) for x in data], '-', label="Indoor")
	plt.plot_date(dates, [float(x.get(' outdoor_temperature', 0.0)) for x in data], '-', label="Outdoors")
	plt.plot_date(dates, [float(x.get(' heating_setpoint', 0.0)) for x in data], '-', label="heating_setpoint")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Temperature (degF)')
	plt.show()


def getCity():
	df = pvlib.tmy.readtmy2('inc_climate.tmy2')
	city = df[1]['City']
	state = df[1]['State']
	return (city + ", " + state)



if __name__ == '__main__':
	#TODO: warning text 'Illegal input. Usage: "python LoadSimGLD <load_type>" where load_type is one of ...
	#Parse Command Line
	if len(sys.argv) == 1:
		modelType = 'AC_HeatPump'
	else:
		parser = argparse.ArgumentParser(description='Simulates heat/cool power use on a canonical .glm single house model')
		parser.add_argument(
		'model_type',
		metavar = 'base',
		type = str,
		help = 'Please specify type of model :"GasHeat", "HeatPump", "Resistance", "AC_electric", "AC_HeatPump", "Waterheater", "EV", "Refrigerator",  "Clotheswasher", "Dryer", "Freezer" ') 
		args = parser.parse_args()
		modelType = args.model_type
	runGld(modelType)

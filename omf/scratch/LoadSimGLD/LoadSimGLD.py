import os, omf, csv
from matplotlib import pyplot as plt
from pprint import pprint as pp
from dateutil.parser import parse as parse_dt
import matplotlib.dates as mdates


''' TODOS
XXX A little bit of plotting.
XXX Additional devices? See superHouse.glm.
OOO Parse and display datetimes correctly. {'# timestamp': '2012-01-01 23:53:00 EST'}
OOO Other variables to watch? Studies to do?
OOO Switch to superHouse.glm?
'''

def workAndGraph(modelType):
	# Run GridLAB-D on the GLM.
	if modelType == 'Gas':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'GAS'
	elif modelType == 'HeatPump':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'HEAT_PUMP'
	elif modelType == 'Resistance':
		cooling_system_type = "ELECTRIC"
		heating_system_type = 'RESISTANCE'

	with open('in_super_house.glm', 'r') as myfile:
	    data=myfile.read()
	    # .replace('\n', '')
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

	# Get the data
	fileOb = open('out_super_house.csv')
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data = list(csv.DictReader(fileOb))
	# pp(data)

	# Do something about datetimes.
	# dt = parse_dt("Aug 28 1999 12:00AM")
	# print dt

	# Plot something.
	plt.switch_backend('MacOSX')
	plt.figure()
	formatter = mdates.DateFormatter('%H-%m-%S')
	dates = mdates.datestr2num([x.get('# timestamp').split(' ')[1] for x in data])
	plt.plot_date(dates, [float(x.get('heating_demand', 0.0)) for x in data], '-', label="Heating")
	plt.plot_date(dates, [float(x.get(' cooling_demand', 0.0)) for x in data], '-', label="Cooling")
	ax = plt.gcf().axes[0]
	ax.xaxis.set_major_formatter(formatter)
	plt.gcf().autofmt_xdate(rotation=45)
	plt.title('New Years Day, Huntsville, AL, '+modelType+' Heating System')
	plt.legend()
	plt.xlabel('Time Stamp')
	plt.ylabel('Demand (kW)')
	plt.figure()
	plt.title('New Years Day, Huntsville, AL, Temperatures')
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

if __name__ == '__main__':
	try: 
		#Parse Command Line
		parser = argparse.ArgumentParser(description='Simulates heat/cool power use on a canonical .glm single house model')
		parser.add_argument('model_type', metavar='base', type=str,
		                    help='Please specify type of model, being Gas, Resistance, or HeatPump')
		args = parser.parse_args()
		modelType = args.model_type
		workAndGraph(modelType)
	except:
		workAndGraph('HeatPump')
import os, csv
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
plt.style.use('ggplot')

# Run GridLAB-D
glmName = 'in_superHouse.glm'
os.system('gridlabd ' + glmName)

# Get the data
fileNames = [
	# 'out_house.csv',
	'out_responsive.csv',
	'out_unresponsive.csv',
	'out_waterheater.csv',
	'out_ev_charger.csv',
	# 'out_solar_inv.csv',
	'out_meter.csv'
]
data = {}
for fname in fileNames:
	fileOb = open(fname)
	for x in range(8):
		# Burn the headers.
		fileOb.readline()
	data[fname] = list(csv.DictReader(fileOb))

# # Plot the demands and generations
# plt.switch_backend('MacOSX')
# plt.figure(figsize=(16,10))
# plt.subplots_adjust(left=0.07, right=0.97, bottom=0.10, top=0.95, wspace=0.12, hspace=0.12)
# plt.subplot(2, 1, 1)
# formatter = mdates.DateFormatter('%H-%m-%S')
# dates = mdates.datestr2num([x.get('# timestamp') for x in data['out_house.csv']])
# plt.plot_date(dates, [float(x.get('heating_demand[kW]', 0.0)) for x in data['out_house.csv']], '-', label="Heating", alpha=0.6)
# plt.plot_date(dates, [float(x.get('cooling_demand[kW]', 0.0)) for x in data['out_house.csv']], '-', label="Cooling", alpha=0.6)
# plt.plot_date(dates, [float(x.get('power.real[kW]', 0.0)) for x in data['out_waterheater.csv']], '-', label="Water Heating", alpha=0.6)
# plt.plot_date(dates, [float(x.get('power.real[kW]', 0.0)) for x in data['out_responsive.csv']], '-', label="Responsive Loads", alpha=0.6)
# plt.plot_date(dates, [float(x.get('power.real[kW]', 0.0)) for x in data['out_unresponsive.csv']], '-', label="Unresponsive Loads", alpha=0.6)
# plt.plot_date(dates, [float(x.get('power.real[kW]', 0.0)) for x in data['out_ev_charger.csv']], '-', label="EV Charger", alpha=0.6)
# plt.plot_date(dates, [-1.0 * float(x.get('VA_Out.real[kW]', 0.0)) for x in data['out_solar_inv.csv']], '-', label="Solar", alpha=0.6)
# ax = plt.gcf().axes[0]
# ax.xaxis.set_major_formatter(formatter)
# plt.gcf().autofmt_xdate(rotation=45)
# bill = 0.10 * float(data['out_meter.csv'][-1].get('measured_real_energy[kWh]', 0.0))
# plt.title('House Simulation. Total bill: $' + str(bill))
# plt.legend()
# plt.xlabel('Time Stamp')
# plt.ylabel('Demand (kW)')
# plt.subplot(4, 1, 3)
# # Plot the Temperatures
# plt.plot_date(dates, [float(x.get('air_temperature[degF]', 0.0)) for x in data['out_house.csv']], '-', label="Indoor")
# plt.plot_date(dates, [float(x.get('outdoor_temperature[degF]', 0.0)) for x in data['out_house.csv']], '-', label="Outdoors")
# plt.plot_date(dates, [float(x.get('heating_setpoint[degF]', 0.0)) for x in data['out_house.csv']], '-', label="Heating Setpoint")
# plt.plot_date(dates, [float(x.get('temperature[degF]', 0.0)) for x in data['out_waterheater.csv']], '-', label="Waterheater")
# ax = plt.gcf().axes[0]
# ax.xaxis.set_major_formatter(formatter)
# plt.gcf().autofmt_xdate(rotation=45)
# plt.legend()
# plt.xlabel('Time Stamp')
# plt.ylabel('Temperature (degF)')
# # Plot the net load and energy.
# plt.subplot(4, 1, 4)
# plt.plot_date(dates, [float(x.get('measured_power.real[kW]', 0.0)) for x in data['out_meter.csv']], '-', label="Net Load (kW)")
# plt.plot_date(dates, [float(x.get('measured_real_energy[kWh]', 0.0)) for x in data['out_meter.csv']], '-', label="Energy (kWh)")
# ax = plt.gcf().axes[0]
# ax.xaxis.set_major_formatter(formatter)
# plt.gcf().autofmt_xdate(rotation=45)
# plt.legend()
# plt.xlabel('Time Stamp')
# plt.ylabel('Units')
# # plt.show()
# plt.savefig('out_all_charts.png', dpi = 350)
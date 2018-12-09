import os, omf, csv
from matplotlib import pyplot as plt
from pprint import pprint as pp
from dateutil.parser import parse as parse_dt

''' TODOS
XXX A little bit of plotting.
XXX Additional devices? See superHouse.glm.
OOO Parse and display datetimes correctly. {'# timestamp': '2012-01-01 23:53:00 EST'}
OOO Other variables to watch? Studies to do?
OOO Switch to superHouse.glm?
'''

# Run GridLAB-D on the GLM.
os.system('gridlabd hvac_gridlabd_sim.glm')

# Get the data
fileOb = open('measured_house_power.csv')
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
plt.title('New Years Day, Huntsville, AL, Heat Pump Heating System')
plt.plot([float(x.get('heating_demand', 0.0)) for x in data], label="Heating")
plt.plot([float(x.get(' cooling_demand', 0.0)) for x in data], label="Cooling")
plt.legend()
plt.xlabel('Time Step (minute)')
plt.ylabel('Demand (kW)')
plt.figure()
plt.title('New Years Day, Huntsville, AL, Temperatures')
plt.plot([float(x.get(' air_temperature', 0.0)) for x in data], label="Indoor")
plt.plot([float(x.get(' outdoor_temperature', 0.0)) for x in data], label="Outdoors")
plt.plot([float(x.get(' heating_setpoint', 0.0)) for x in data], label="Heating Setpoint")
plt.legend()
plt.xlabel('Time Step (minute)')
plt.ylabel('Temperature (degF)')
plt.show()
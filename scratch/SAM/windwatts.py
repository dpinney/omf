from sscapi import PySSC


''' This does not work because of API failures as of 3/22/2013 '''

ssc = PySSC()
data = ssc.data_create()

# Test windwatts with skystream 2.4/3.7 hybrid
ssc.data_set_string(data, 'file_name', 'WY Southern-Flat Lands.srw')
ssc.data_set_number(data, 'ctl_mode', 2)
ssc.data_set_number(data, 'cutin', 4)
ssc.data_set_number(data, 'hub_ht', 50)
ssc.data_set_number(data, 'lossc', 0)
ssc.data_set_number(data, 'lossp', 0)
pc_wind = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39]
ssc.data_set_array(data, 'pc_wind', pc_wind)
pc_power = [0,0,0,0,0.08,0.02,0.35,0.6,1,1.6,2,2.25,2.35,2.4,2.4,2.37,2.3,2.09,2,2,2,2,2,1.98,1.95,1.8,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
ssc.data_set_array(data, 'pc_power', pc_power)
ssc.data_set_number(data, 'rotor_di', 3.7)
ssc.data_set_number(data, 'shear', 0.14)
ssc.data_set_number(data, 'turbul', 0.1)
ssc.data_set_array(data, 'wt_x', [0])
ssc.data_set_array(data, 'wt_y', [0])
ssc.data_set_number(data, 'wake_model', 0)
ssc.data_set_number(data, 'model_choice', 0)
# Took wind model Weibull parameter from here: http://www.wind-power-program.com/wind_statistics.htm
ssc.data_set_number(data, 'weibullK', 2)
ssc.data_set_number(data, 'max_cp', 0.45)
ssc.data_set_number(data, 'resource_class', 0.45)
hub_efficiency = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
ssc.data_set_array(data, 'hub_efficiency', hub_efficiency)


# run wind system simulation
mod = ssc.module_create("windpower")
ssc.module_exec(mod, data)
ann = 0
ac = ssc.data_get_array(data, "farmpwr")
for i in range(len(ac)):
	ann += ac[i]
print 'WindWatts Simulation ok, e_net (annual kW)=', ann

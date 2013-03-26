from sscapi import PySSC

# setup inputs
ssc = PySSC()
dat = ssc.data_create()
ssc.data_set_string(dat, "file_name", "daggett.tm2")
ssc.data_set_number(dat, "system_size", 4)
ssc.data_set_number(dat, "derate", 0.77)
ssc.data_set_number(dat, "track_mode", 0)
ssc.data_set_number(dat, "azimuth", 180)
ssc.data_set_number(dat, "tilt_eq_lat", 1)

# run PV system simulation
mod = ssc.module_create("pvwattsv1")
ssc.module_exec(mod, dat)

# print results
ann = 0
ac = ssc.data_get_array(dat, "ac")
for i in range(len(ac)):
	ac[i] = ac[i]/1000
	ann += ac[i]
print "PVWatts V1 Simulation ok, e_net (annual kW)=", ann
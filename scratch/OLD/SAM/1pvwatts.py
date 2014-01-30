from sscapi import PySSC
import matplotlib.pyplot as plot

# setup data structures
ssc = PySSC()
dat = ssc.data_create()
# required inputs
ssc.data_set_string(dat, "file_name", "daggett.tm2")
ssc.data_set_number(dat, "system_size", 4)
ssc.data_set_number(dat, "derate", 0.77)
ssc.data_set_number(dat, "track_mode", 2)
ssc.data_set_number(dat, "azimuth", 180)
ssc.data_set_number(dat, "tilt_eq_lat", 1)
# default inputs exposed
ssc.data_set_number(dat, 'rotlim', 45.0)
ssc.data_set_number(dat, 't_noct', 45.0)
ssc.data_set_number(dat, 't_ref', 25.0)
ssc.data_set_number(dat, 'gamma', -0.5)
ssc.data_set_number(dat, 'inv_eff', 0.92)
ssc.data_set_number(dat, 'fd', 1.0)
ssc.data_set_number(dat, 'i_ref', 1000)
ssc.data_set_number(dat, 'poa_cutin', 0)
ssc.data_set_number(dat, 'w_stow', 0)
# complicated optional inputs
# ssc.data_set_array(dat, 'shading_hourly', ...) 	Hourly beam shading factors
# ssc.data_set_matrix(dat, 'shading_mxh', ...) 		Month x Hour beam shading factors
# ssc.data_set_matrix(dat, 'shading_azal', ...) 	Azimuth x altitude beam shading factors
# ssc.data_set_number(dat, 'shading_diff', ...) 	Diffuse shading factor
# ssc.data_set_number(dat, 'enable_user_poa', ...)	Enable user-defined POA irradiance input = 0 or 1
# ssc.data_set_array(dat, 'user_poa', ...) 			User-defined POA irradiance in W/m2


# run PV system simulation
mod = ssc.module_create("pvwattsv1")
ssc.module_exec(mod, dat)

# OLD print results
# ac = ssc.data_get_array(dat, "ac")
# ann = sum([x/1000 for x in ac])
# print "PVWatts V1 Simulation ok, e_net (annual kW)=", ann

# Extract data.
# Geodata.
city = ssc.data_get_string(dat, 'city')
state = ssc.data_get_string(dat, 'state')
lat = ssc.data_get_number(dat, 'lat')
lon = ssc.data_get_number(dat, 'lon')
elev = ssc.data_get_number(dat, 'elev')
# Weather
irrad = ssc.data_get_array(dat, 'dn')
diffIrrad = ssc.data_get_array(dat, 'df')
temp = ssc.data_get_array(dat, 'tamb')
cellTemp = ssc.data_get_array(dat, 'tcell')
wind = ssc.data_get_array(dat, 'wspd')
# Power generation.
dcOut = ssc.data_get_array(dat, 'dc')
acOut = ssc.data_get_array(dat, 'ac')

# Show some results.
def printSumm(name):
	values = eval(name)
	print name, len(values), values[1:24]
print city, state, lat, lon, elev
printSumm('irrad')
printSumm('diffIrrad')
printSumm('temp')
printSumm('cellTemp')
printSumm('wind')
printSumm('dcOut')
printSumm('acOut')

# Graph some results.
def addPlot(name):
	values = eval(name)
	plot.plot(values, label=name)
plot.figure('pvwatts annual output')
plot.subplots_adjust(left=0.03, bottom=0.05, right=0.98, top=0.98)
plot.subplot(311)
addPlot('irrad')
addPlot('diffIrrad')
plot.legend()
plot.subplot(312)
addPlot('temp')
addPlot('cellTemp')
addPlot('wind')
plot.legend()
plot.subplot(313)
addPlot('dcOut')
addPlot('acOut')
plot.xlabel('Hour of the Year')
plot.legend()
plot.show()


'''
====================== OUTPUT VARIABLES ============================
TYPE				NAME				DESC								UNITS			CONSTRAINT
-------------------------------------------------------------------------------------------------------------
SSC_ARRAY			gh					Global horizontal irradiance		W/m2			LENGTH=8760
SSC_ARRAY			dn					Beam irradiance						W/m2			LENGTH=8760
SSC_ARRAY			df					Diffuse irradiance					W/m2			LENGTH=8760
SSC_ARRAY			tamb				Ambient temperature					C				LENGTH=8760
SSC_ARRAY			tdew				Dew point temperature				C				LENGTH=8760
SSC_ARRAY			wspd				Wind speed							m/s				LENGTH=8760
SSC_ARRAY			poa					Plane of array irradiance			W/m2			LENGTH=8760
SSC_ARRAY			tcell				Module temperature					C				LENGTH=8760
SSC_ARRAY			dc					DC array output						Wdc				LENGTH=8760
SSC_ARRAY			ac					AC system output					Wac				LENGTH=8760
SSC_ARRAY			shad_beam_factor	Shading factor for beam radiation					LENGTH=8760
SSC_ARRAY			poa_monthly			Plane of array irradiance			kWh/m2			LENGTH=12
SSC_ARRAY			solrad_monthly		Daily average solar irradiance		kWh/m2/day		LENGTH=12
SSC_ARRAY			dc_monthly			DC array output						kWhdc			LENGTH=12
SSC_ARRAY			ac_monthly			AC system output					kWhac			LENGTH=12
SSC_NUMBER			solrad_annual		Daily average solar irradiance		kWh/m2/day						
SSC_NUMBER			ac_annual			Annual AC system output				kWhac						
SSC_STRING			location			Location ID
SSC_STRING			city				City									
SSC_STRING			state				State									
SSC_NUMBER			lat					Latitude							deg						
SSC_NUMBER			lon					Longitude							deg						
SSC_NUMBER			tz					Time zone							hr						
SSC_NUMBER			elev				Site elevation						m						



====================== INPUT VARIABLES ============================

TYPE		NAME			DESC										UNITS								REQUIRED			CONSTRAINT
----------------------------------------------------------------------------------------------------------------------------------------------------
SSC_STRING	file_name		local weather file path															Y					LOCAL_FILE
SSC_NUMBER	system_size		Nameplate capacity							kW									Y					MIN=0.05,MAX=500000
SSC_NUMBER	derate			System derate value	frac														Y					MIN=0,MAX=1
SSC_NUMBER	track_mode		Tracking mode								0/1/2/3=Fixed,1Axis,2Axis,AziAxis	Y					MIN=0,MAX=3,INTEGER
SSC_NUMBER	azimuth			Azimuth angle								deg: E=90,S=180,W=270				Y					MIN=0,MAX=360
SSC_NUMBER	tilt			Tilt angle									deg: H=0,V=90						Y or tilt_eq_lat	MIN=0,MAX=90
SSC_NUMBER	tilt_eq_lat		Tilt=latitude override						0/1									Y or tilt			BOOLEAN
SSC_ARRAY	shading_hourly	Hourly beam shading factors														?					LENGTH=???
SSC_MATRIX	shading_mxh		Month x Hour beam shading factors												?					LENGTH=???
SSC_MATRIX	shading_azal	Azimuth x altitude beam shading factors											?					LENGTH=???
SSC_NUMBER	shading_diff	Diffuse shading factor															?					
SSC_NUMBER	enable_user_poa	Enable user-defined POA irradiance input	0/1									?=0					BOOLEAN
SSC_ARRAY	user_poa		User-defined POA irradiance					W/m2								enable_user_poa=1	LENGTH=8760
SSC_NUMBER	rotlim			Tracker rotation limit (+/- 1 axis)			deg									?=45.0				MIN=1,MAX=90
SSC_NUMBER	t_noct			Nominal operating cell temperature			C									?=45.0				POSITIVE
SSC_NUMBER	t_ref			Reference cell temperature					C									?=25.0				POSITIVE
SSC_NUMBER	gamma			Max power temperature coefficient			%/C									?=-0.5				
SSC_NUMBER	inv_eff			Inverter efficiency at rated power			frac								?=0.92				MIN=0,MAX=1
SSC_NUMBER	fd				Diffuse fraction							0..1								?=1.0				MIN=0,MAX=1
SSC_NUMBER	i_ref			Rating condition irradiance					W/m2								?=1000				POSITIVE
SSC_NUMBER	poa_cutin		Min reqd irradiance for operation			W/m2								?=0					MIN=0
SSC_NUMBER	w_stow			Wind stow speed								m/s									?=0					MIN=0


'''
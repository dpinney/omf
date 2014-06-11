from sscapi import PySSC

''' Runs but returns nonsense data. '''

# setup inputs
ssc = PySSC()
dat = ssc.data_create()
ssc.data_set_string(dat, "file_name", "daggett.tm2")
ssc.data_set_number(dat, "resource_potential", 910)				#Resource Potential	MW
ssc.data_set_number(dat, "resource_type", 0)					#Type of Resource			INTEGER
ssc.data_set_number(dat, "resource_temp", 200)					#Resource Temperature	C
ssc.data_set_number(dat, "resource_depth", 2000)				#Resource Depth	m
ssc.data_set_number(dat, "analysis_period", 25)					#Analysis Lifetime	years		INTEGER
ssc.data_set_number(dat, "model_choice", 0)						#Which model to run (0,1,2)			INTEGER
ssc.data_set_number(dat, "nameplate", 15000)					#Desired plant output	kW
ssc.data_set_number(dat, "analysis_type", 0)					#Analysis Type			INTEGER
ssc.data_set_number(dat, "num_wells", 3)						#Number of Wells
ssc.data_set_number(dat, "num_wells_getem", 3)					#Number of Wells GETEM calc'd
ssc.data_set_number(dat, "conversion_type", 0)					#Conversion Type			INTEGER
ssc.data_set_number(dat, "plant_efficiency_input", 11.28)		#Plant efficiency
ssc.data_set_number(dat, "conversion_subtype", 0)				#Conversion Subtype			INTEGER
ssc.data_set_number(dat, "decline_type", 0)						#Temp decline Type			INTEGER
ssc.data_set_number(dat, "temp_decline_rate", 0.03)				#Temperature decline rate	%/yr
ssc.data_set_number(dat, "temp_decline_max", 30)				#Maximum temperature decline	C
ssc.data_set_number(dat, "wet_bulb_temp", 15)					#Wet Bulb Temperature	C
ssc.data_set_number(dat, "ambient_pressure", 14.7)				#Ambient pressure	psi
ssc.data_set_number(dat, "well_flow_rate", 70)					#Production flow rate per well	kg/s
ssc.data_set_number(dat, "pump_efficiency", 0.60)				#Pump efficiency	%
ssc.data_set_number(dat, "delta_pressure_equip", 25)			#Delta pressure across surface equipment	psi
ssc.data_set_number(dat, "excess_pressure_pump", 50.76)			#Excess pressure @ pump suction	psi
ssc.data_set_number(dat, "well_diameter", 10)					#Production well diameter	in
ssc.data_set_number(dat, "casing_size", 9.625)					#Production pump casing size	in
ssc.data_set_number(dat, "inj_well_diam", 10)					#Injection well diameter	in
ssc.data_set_number(dat, "design_temp", 200)					#Power block design temperature	C
ssc.data_set_number(dat, "specify_pump_work", 0)				#Did user specify pump work?	0 or 1		INTEGER
ssc.data_set_number(dat, "specified_pump_work_amount", 1)		#Pump work specified by user	MW
# Source for thermal conductivity data: http://www.ems.psu.edu/~elsworth/courses/egee580/2010/Final%20Presentations/Finalppt_580_EGS_SP2010.pdf
ssc.data_set_number(dat, "rock_thermal_conductivity", 192900)	#Rock thermal conductivity	J/m-day-C
# Specific heat source: http://www.alanpedia.com/physics_specific_heat_capacity/specific_heat_capacity_questions_and_equation.html 
ssc.data_set_number(dat, "rock_specific_heat", 796)				#Rock specific heat	J/kg-C
# Density source (Granite): http://geology.about.com/cs/rock_types/a/aarockspecgrav.htm
ssc.data_set_number(dat, "rock_density", 2600)					#Rock density	kg/m^3
ssc.data_set_number(dat, "reservoir_pressure_change_type", 0)	#Reservoir pressure change type			INTEGER
ssc.data_set_number(dat, "reservoir_pressure_change", 951)		#Pressure change	psi-h/1000lb
ssc.data_set_number(dat, "reservoir_width", 500)				#Reservoir width	m
ssc.data_set_number(dat, "reservoir_height", 100)				#Reservoir height	m
ssc.data_set_number(dat, "reservoir_permeability", 0.05)		#Reservoir Permeability	darcys
ssc.data_set_number(dat, "inj_prod_well_distance", 1500)		#Distance from injection to production wells	m
ssc.data_set_number(dat, "subsurface_water_loss", 0.02)			#Subsurface water loss	%
ssc.data_set_number(dat, "fracture_aperature", 0.0004)			#Fracture aperature	m
ssc.data_set_number(dat, "fracture_width", 175)					#Fracture width	m
ssc.data_set_number(dat, "num_fractures", 6)					#Number of fractures			INTEGER
ssc.data_set_number(dat, "fracture_angle", 15)					#Fracture angle	deg
ssc.data_set_number(dat, "tech_type", 1)						#Technology type ID	(1-4)		INTEGER
ssc.data_set_number(dat, "T_htf_cold_ref", 90)					#Outlet design temp	C
ssc.data_set_number(dat, "T_htf_hot_ref", 200)					#Inlet design temp	C
ssc.data_set_number(dat, "HTF", 3)								#Heat trans fluid type ID	(1-27)		INTEGER
ssc.data_set_number(dat, "P_boil", 2)							#Design Boiler Pressure	bar
ssc.data_set_number(dat, "eta_ref", 0.17)						#Desgin conversion efficiency	%
ssc.data_set_number(dat, "q_sby_frac", 0.2)						#% thermal power for standby mode	%
ssc.data_set_number(dat, "startup_frac", 0.2)					#% thermal power for startup	%
ssc.data_set_number(dat, "startup_time", 1)						#Hours to start power block	hours
ssc.data_set_number(dat, "pb_bd_frac", 0.1)						#Blowdown steam fraction	%
ssc.data_set_number(dat, "T_amb_des", 15)						#Design ambient temperature	C
ssc.data_set_number(dat, "CT", 1)								#Condenser type (Wet, Dry,Hybrid)	(1-3)		INTEGER
ssc.data_set_number(dat, "dT_cw_ref", 10)						#Design condenser cooling water inlet/outlet T diff	C
ssc.data_set_number(dat, "T_approach", 5)						#Approach Temperature	C
ssc.data_set_number(dat, "T_ITD_des", 16)						#Design ITD for dry system	C
ssc.data_set_number(dat, "P_cond_ratio", 1.0028)				#Condenser pressure ratio
ssc.data_set_number(dat, "P_cond_min", 1.25)					#Minimum condenser pressure	in Hg
ssc.data_set_number(dat, "hr_pl_nlev", 0)						## part-load increments	(0-9)		INTEGER
ssc.data_set_number(dat, "hc_ctl1", 0)							#HC Control 1
ssc.data_set_number(dat, "hc_ctl2", 0)							#HC Control 2
ssc.data_set_number(dat, "hc_ctl3", 0)							#HC Control 3
ssc.data_set_number(dat, "hc_ctl4", 0)							#HC Control 4
ssc.data_set_number(dat, "hc_ctl5", 0)							#HC Control 5
ssc.data_set_number(dat, "hc_ctl6", 0)							#HC Control 6
ssc.data_set_number(dat, "hc_ctl7", 0)							#HC Control 7
ssc.data_set_number(dat, "hc_ctl8", 0)							#HC Control 8
ssc.data_set_number(dat, "hc_ctl9", 0)							#HC Control 9
ssc.data_set_string(dat, "hybrid_dispatch_schedule", '1'*288)	#Daily dispatch schedule	TOUSCHED

# run PV system simulation
mod = ssc.module_create("geothermal")
ssc.module_exec(mod, dat)

# print results
ac = ssc.data_get_array(dat, "monthly_power")
print "Monthly Power", ac
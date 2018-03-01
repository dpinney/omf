"""
This file contains functions to define user specifications for glm models

	technologyFunction(case_flag):
		This function creates the use flags dictionary
	feederDefinition(feederName):
		Creates the specific settings for each feeder needed to populate the feeder
	feederConfiguration(config_file, classification):
		Creates the complete configuration dictionary needed to populate the feeder

Created December 20, 2016 by Jacob Hansen (jacob.hansen@pnnl.gov)

Copyright (c) 2016 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
Government, including the right to distribute to other Government contractors.
"""

from __future__ import division

def technologyFunction(case_flag):
	"""
	Creates the use flags dictionary

	Inputs
		case_flag - an integer indicating which technology case to tack on to the GridLAB-D model
			 case_flag : technology
			 0 : Load shape case
			 1 : House case
	Outputs
		use_flags - dictionary that contains flags for what technology case to tack on to the GridLAB-D model
	"""
	valid = [0, 1]

	if case_flag not in valid:
		raise Exception('case flag "{:s}" is not defined'.format(case_flag))

	use_flags = {'use_normalized_loadshapes' : 0,
				 'use_homes' : 0,
				 'use_commercial' : 0,}

	# standard settings that apply to all feeders

	# quick case. Use load shapes instead of house objects.
	if case_flag is 0:
		use_flags["use_normalized_loadshapes"] = 1
		use_flags["use_homes"] = 1
		use_flags["use_commercial"] = 0

	# base case. Use house objects.
	if case_flag is 1:
		use_flags["use_normalized_loadshapes"] = 0
		use_flags["use_homes"] = 1
		use_flags["use_commercial"] = 0

	return use_flags

def feederConfiguration(feederName, date_list):
	"""
	Creates the specific settings for each feeder needed to populate the feeder

	Inputs
		feederName - name of the specific feeder we are working on
	Outputs
		data - dictionary with full configuration specifications
		use_flags - dictionary that contains flags for what technology case to tack on to the GridLAB-D model
	"""
	data = dict()
	use_flags = dict()

	# Specific flags for what technology you want implemented
	# use_flags["use_normalized_loadshapes"] = 0
	use_flags["use_homes"] = 1			# 0= no homes, 1= individual homes, 2= normalized load shapes
	use_flags["use_commercial"] = 1		# 0= no commercial, 1= individual commercial, 2= normalized load shapes
	use_flags["use_EVs"] = 0			# add Electric vehicles to the simulation
	use_flags["use_residential_storage"] = 0	# add battery storage at the residential level
	use_flags["use_utility_storage"] = 0	# add battery storage at the residential level
	use_flags["use_schedules"] = 1 				# ALWAYS keep at 1 unless you know what you are doing!!
	use_flags['useFNCS'] = 0 					# if true the connection module will be added
	use_flags['addTSEControllers'] = 0 			# add Transactive Energy Controllers
	use_flags['addTSEAggregators'] = 0 			# add Transactive Energy Controllers so they are paticipating in wholesale
	use_flags['houseThermostatMode'] = 'AUTO'  	# setting to specify how house thermostats should behave, 'COOL', 'HEAT', 'AUTO'
	use_flags['addSubstation'] = 1 				# if true a substation will be added with a transformer according to the feeder details below (for CCSI we can't use this configuration!)

	# path to the include folder
	data['includePath'] = '../include'

	# settings for Transactive Energy Controllers
	data['TSEmarketName'] = 'retailMarket'
	data['TSEmarketUnit'] = 'W'
	data['TSEmarketPeriod'] = 300
	data['TSEcontrolTechnology'] = 'DOUBLE_PRICE'  # at the moment we only support modes that does either cooling or heating
	data['TSEresolveMode'] = 'DEADBAND'
	data['TSEbidMode'] = 'ON'
	data['TSEbidDelay'] = 30
	data['TSEsliderSetting'] = 1
	data['TSEauctionStatistics'] = 24
	data['TSEinitPrice'] = 40
	data['TSEinitStdev'] = 12
	data['TSEpriceCap'] = 1000
	data['TSEuseFutureMeanPrice'] = 'FALSE'
	data['TSEwarmUp'] = 0

	# standard settings that apply to all feeders
	data["timezone"] = 'PST8'
	
	#print 'date_list in module feederConfiguration.py'
	
	#print (date_list)
	data['startdate'] = date_list[0] # '2013-08-01 0:00:00'
	data['stopdate'] = date_list[1] #'2013-08-02 0:00:00'
	data['record_in'] = date_list[2] #'2013-08-01 0:00:00'
	data['record_out'] = date_list[3] #'2013-08-02 0:00:00'

	data['minimum_timestep'] = 30

	data['measure_interval'] = 300

	data["load_shape_norm"] = 'load_shape_player.player'

	# recorders {key : True/False}
	data["recorders"] = {'water_heaters': 	  	False,  # record properties from the electric water heaters
						 'responsive_load':   	False,  # record power drawn by responsive zip loads
						 'unresponsive_load': 	False,  # record power drawn by non responsive loads
						 'HVAC': 				False,  # record power drawn by HVAC systems
						 'swing_node': 			True,  # record power drawn at the swing node
						 'climate': 			True,  # record properties from the climate object
						 'load_composition': 	False,   # record load composition by groupid's
						 'customer_meter':		False,   # record power and voltage from customer meters
						 'voltage_regulators':	False,	# record secondary side of voltage regulators along with tab operation
						 'market':				False,	# record properties from the market
						 'TSEControllers':		False,	# record bid price and quantiy of controllers
						 'EVChargers':		    False,	# record properties from EV chargers
						 'residentialStorage':	False,	# record properties from the residential battery storage
						 'utilityStorage': 		False}	# record properties from the utility battery storage

	# residential zip fractions for loadshapes
	data["r_heat_fraction"] = 0.9
	data["r_z_pf"] = 0.97
	data["r_i_pf"] = 0.97
	data["r_p_pf"] = 0.97
	data["r_zfrac"] = 0.2
	data["r_ifrac"] = 0.4
	data["r_pfrac"] = 1 - data["r_zfrac"] - data["r_ifrac"]

	# commercial zip fractions for loadshapes
	data["c_z_pf"] = 0.97
	data["c_i_pf"] = 0.97
	data["c_p_pf"] = 0.97
	data["c_zfrac"] = 0.2
	data["c_ifrac"] = 0.4
	data["c_pfrac"] = 1 - data["c_zfrac"] - data["c_ifrac"]

	# --------------------- Feeder specific settings -------------------------------------------
	# -- data["nom_volt"] 						# Nominal voltage of the trunk of the feeder
	# -- data["feeder_rating"] 					# substation rating in MVA - add'l 15% gives rated kW & pf = 0.87
	# -- data["normalized_loadshape_scalar"] 	# Scale the load shape
	# -- data["region"]							# Region Identifier (1:West Coast (temperate), 2:North Central/Northeast (cold/cold), 3:Southwest (hot/arid), 4:Southeast/Central (hot/cold), 5:Southeast Coastal (hot/humid), 6: Hawaii (sub-tropical))
	# -- data["weather"] 						# Please specify what weather file you would like to use (either .csv or .tmy). If not specified, region weather file will be used!
	# -- data["avg_house"] 						# Determines how many houses to populate (bigger avg_house = less houses)
	# -- data["base_load_scalar"] 				# Scale the responsive and unresponsive loads (percentage)
	# -- data["residential_skew_shift"] 		# variable to shift the residential schedule skew (seconds)
	# -- data["residential_skew_max"] 			# maximum schedule skew (seconds) [-residential_skew_max, residential_skew_max]
	# -- data["residential_skew_std"] 			# widen schedule skew (seconds)
	# -- data["perc_gas"] 						# percentage of house that use Gas for heating. If not set default will be pulled from region specific values
	# -- data["perc_pump"]						# percentage of house that use Heat pumps. If not set default will be pulled from region specific values
	# -- data["perc_AC"] 						# percentage of house that use AC systems. If not set default will be pulled from region specific values
	# -- data["wh_electric"] 					# percentage of house that have an electric water heater. If not set default will be pulled from region specific values
	# -- data["perc_poolpumps"] 				# percentage of house that have a pool pump. Will only affect SFH. If not set default will be pulled from region specific values
	# -- data["perc_EV"] 						# percentage of house that have a EV charger. Will only be used if the corresponding use flag for EVs is set
	# -- data["avg_commercial"] 				# Determines sizing of commercial loads (bigger avg_commercial = less houses)
	# -- data["commercial_load_cut"] 			# Determines the point at which a commercial load will only be converted to street light
	# -- data["commercial_skew_max"] 			# maximum schedule skew (seconds) [-commercial_skew_max, commercial_skew_max]
	# -- data["commercial_skew_std"] 			# widen schedule skew (seconds)
	# -- data["cooling_COP"] 					# commercial cooling COP
	# -- data["light_scalar_comm"] 				# commercial street light scalar
	# -- data["perc_EB"]						# percentage of house that have battery storage. Will only be used if the corresponding use flag for battery storage is set
	# -- data["utility_EB"]						# number of utility scale batteries to attach to the feeder. They will be placed at the substation
	# --------------------------------------------------------------------------------------------------
	# ------------------------------ Feeders available -------------------------------------------------
	# -- 4BusSystem
	# -- GC-12.47-1
	# -- R1-12.47-1
	# -- R1-12.47-2
	# -- R1-12.47-3
	# -- R1-12.47-4
	# -- R1-25.00-1
	# -- R2-12.47-1
	# -- R2-12.47-2
	# -- R2-12.47-3
	# -- R2-25.00-1
	# -- R2-35.00-1
	# -- R3-12.47-1
	# -- R3-12.47-2
	# -- R3-12.47-3
	# -- R4-12.47-1
	# -- R4-12.47-2
	# -- R4-25.00-1
	# -- R5-12.47-1
	# -- R5-12.47-2
	# -- R5-12.47-3
	# -- R5-12.47-4
	# -- R5-12.47-5
	# -- R5-25.00-1
	# -- R5-35.00-1

	# feeder specific settings
	if feederName == '4BusSystem':
		data["nom_volt"] = 14400
		data["feeder_rating"] = 1.15 * 14.0
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 4
		data["weather"] = ''
		data["avg_house"] = 3000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["perc_gas"] = 1
		data["perc_pump"] = 0
		data["perc_AC"] = 1
		data["wh_electric"] = 1
		data["perc_poolpumps"] = 0
		data["perc_EV"] = 0
		data["avg_commercial"] = 35000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'GC-12.47-1':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 5.38
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 1
		data["weather"] = ''
		data["avg_house"] = 8000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 13000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R1-12.47-1':
		data["nom_volt"] = 12500
		data["feeder_rating"] = 1.15 * 7.272
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 1
		data["weather"] = ''
		data["avg_house"] = 4000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 20000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0.1
		data["perc_EB"] = 0.05
		data["utility_EB"] = 0

	elif feederName == 'R1-12.47-2':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 2.733
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 1
		data["weather"] = ''
		data["avg_house"] = 4500
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 30000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R1-12.47-3':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 1.255
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 1
		data["weather"] = ''
		data["avg_house"] = 8000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 15000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R1-12.47-4':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 4.960
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 1
		data["weather"] = ''
		data["avg_house"] = 4000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 15000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R1-25.00-1':
		data["nom_volt"] = 24900
		data["feeder_rating"] = 1.15 * 2.398
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 1
		data["weather"] = ''
		data["avg_house"] = 6000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 25000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R2-12.47-1':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 6.256
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 2
		data["weather"] = ''
		data["avg_house"] = 7000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 20000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R2-12.47-2':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 5.747
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 2
		data["weather"] = ''
		data["avg_house"] = 7500
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 25000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0.1
		data["perc_EB"] = 0.05
		data["utility_EB"] = 1

	elif feederName == 'R2-12.47-3':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 3.435
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 2
		data["weather"] = ''
		data["avg_house"] = 5000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 30000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0.1
		data["perc_EB"] = 0.05
		data["utility_EB"] = 0

	elif feederName == 'R2-25.00-1':
		data["nom_volt"] = 24900
		data["feeder_rating"] = 1.15 * 16.825
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 2
		data["weather"] = ''
		data["avg_house"] = 6000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 15000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R2-35.00-1':
		data["nom_volt"] = 34500
		data["feeder_rating"] = 1.15 * 12.638
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 2
		data["weather"] = ''
		data["avg_house"] = 15000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 30000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R3-12.47-1':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 9.366
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 3
		data["weather"] = ''
		data["avg_house"] = 12000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 40000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R3-12.47-2':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 4.462
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 3
		data["weather"] = ''
		data["avg_house"] = 14000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 30000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R3-12.47-3':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 8.620
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 3
		data["weather"] = ''
		data["avg_house"] = 7000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 15000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R4-12.47-1':
		data["nom_volt"] = 13800
		data["feeder_rating"] = 1.15 * 5.55
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 4
		data["weather"] = ''
		data["avg_house"] = 9000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 30000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R4-12.47-2':
		data["nom_volt"] = 12500
		data["feeder_rating"] = 1.15 * 2.249
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 4
		data["weather"] = ''
		data["avg_house"] = 6000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 20000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R4-25.00-1':
		data["nom_volt"] = 24900
		data["feeder_rating"] = 1.15 * 0.934
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 4
		data["weather"] = ''
		data["avg_house"] = 6000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 20000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R5-12.47-1':
		data["nom_volt"] = 13800
		data["feeder_rating"] = 1.15 * 9.473
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 5
		data["weather"] = ''
		data["avg_house"] = 6500
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 20000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R5-12.47-2':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 4.878
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 5
		data["weather"] = ''
		data["avg_house"] = 4500
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 15000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R5-12.47-3':
		data["nom_volt"] = 13800
		data["feeder_rating"] = 1.15 * 9.924
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 5
		data["weather"] = ''
		data["avg_house"] = 4000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 15000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R5-12.47-4':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 7.612
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 5
		data["weather"] = ''
		data["avg_house"] = 6000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 30000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R5-12.47-5':
		data["nom_volt"] = 12470
		data["feeder_rating"] = 1.15 * 9.125
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 5
		data["weather"] = ''
		data["avg_house"] = 4500
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 25000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R5-25.00-1':
		data["nom_volt"] = 22900
		data["feeder_rating"] = 1.15 * 12.346
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 5
		data["weather"] = ''
		data["avg_house"] = 3000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 20000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == 'R5-35.00-1':
		data["nom_volt"] = 34500
		data["feeder_rating"] = 1.15 * 12.819
		data["normalized_loadshape_scalar"] = 1
		data["region"] = 5
		data["weather"] = ''
		data["avg_house"] = 6000
		data["base_load_scalar"] = 1.0
		data["residential_skew_shift"] = 0
		data["residential_skew_max"] = 8100
		data["residential_skew_std"] = 2700
		data["avg_commercial"] = 25000
		data["commercial_load_cut"] = 5000
		data["commercial_skew_max"] = 5400
		data["commercial_skew_std"] = 1800
		data["cooling_COP"] = 3
		data["light_scalar_comm"] = 1
		data["perc_EV"] = 0
		data["perc_EB"] = 0
		data["utility_EB"] = 0

	elif feederName == '':
		# if no feeder is specified all we return are setting flags
		return data, use_flags
	else:
		raise Exception('"{:s}" is not a known feeder!'.format(feederName))

	# ------------- external control options --------------------------

	# respect local control -> 0 = false, 1 = true
	data["respect_local_control"] = 0

	# control HVACs
	data["control_HVAC"] = 0

	# control water heaters
	data["control_WH"] = 0

	# control EVs
	data["control_EV"] = 0

	#---------------------------------------------------------------------
	#--------------- no modification beyond this point! ------------------
	#---------------------------------------------------------------------

	# Regional building data
	# thermal_percentage integrity percentages
	# {region}(level, sf / apart / mh)
	# 	single family homes
	#	apartments
	#	mobile homes
	# level corresponds to age of home from "Building Reccs"
	# 	1:pre - 1940, 2:1940 - 1949, 3:1950 - 1959, 4:1960 - 1969, 5:1970 - 1979, 6:1980 - 1989, 7:1990 - 2005
	# 	1:pre - 1960, 2:1960 - 1989, 3:1990 - 2005
	# 	1:pre - 1960, 2:1960 - 1989, 3:1990 - 2005

	if data["region"] == 1:
		thermal_percentages = [[0.0805,0.0724,0.1090,0.0867,0.1384,0.1264,0.1297], # sf
                               [0.0356,0.1223,0.0256,0.0000,0.0000,0.0000,0.0000], # apart
                               [0.0000,0.0554,0.0181,0.0000,0.0000,0.0000,0.0000]] # mh

		floor_area_scalar = [[0.4620,0.4988,0.5047,0.6724,0.7495,0.8271,1.0000], # sf
					  		 [1.0000,1.1000,1.2000,0.0000,0.0000,0.0000,0.0000], # apart
							 [1.0000,1.0000,1.0000,0.0000,0.0000,0.0000,0.0000]] # mh
		floor_area = [2209,820,1054] # SFH, MOBILE, APT
		one_story = 0.6887
		window_wall_ratio = 0.15
		perc_gas = 0.7051
		perc_pump = 0.0321
		perc_res = 1 - perc_pump - perc_gas
		perc_AC = 0.4348
		perc_pool_pumps = 0.0904
		wh_electric = 0.7455
		wh_size = [0.0000, 0.3333, 0.6667]
		over_sizing_factor = 0.1

	elif data["region"] == 2:
		thermal_percentages = [[0.1574, 0.0702, 0.1290, 0.0971, 0.0941, 0.0744, 0.1532],  # sf
							   [0.0481, 0.0887, 0.0303, 0.0000, 0.0000, 0.0000, 0.0000],  # apart
							   [0.0000, 0.0372, 0.0202, 0.0000, 0.0000, 0.0000, 0.0000]]  # mh

		floor_area_scalar = [[0.4620,0.4988,0.5047,0.6724,0.7495,0.8271,1.0000], # sf
					  		 [1.0000,1.1000,1.2000,0.0000,0.0000,0.0000,0.0000], # apart
							 [1.0000,1.0000,1.0000,0.0000,0.0000,0.0000,0.0000]] # mh
		floor_area = [2951,798,1035]  # SFH, MOBILE, APT
		one_story = 0.5210
		window_wall_ratio = 0.15
		perc_gas = 0.8927
		perc_pump = 0.0177
		perc_res = 1 - perc_pump - perc_gas
		perc_AC = 0.7528
		perc_pool_pumps = 0.0591
		wh_electric = 0.7485
		wh_size = [0.1459,0.5836,0.2706] # size of units - [<30, 31-49, >50]
		over_sizing_factor = 0.2

	elif data["region"] == 3:
		thermal_percentages = [[0.0448, 0.0252, 0.0883, 0.0843, 0.1185, 0.1315, 0.2411],  # sf
							   [0.0198, 0.1159, 0.0478, 0.0000, 0.0000, 0.0000, 0.0000],  # apart
							   [0.0000, 0.0524, 0.0302, 0.0000, 0.0000, 0.0000, 0.0000]]  # mh

		floor_area_scalar = [[0.4620,0.4988,0.5047,0.6724,0.7495,0.8271,1.0000], # sf
					  		 [1.0000,1.1000,1.2000,0.0000,0.0000,0.0000,0.0000], # apart
							 [1.0000,1.0000,1.0000,0.0000,0.0000,0.0000,0.0000]] # mh
		floor_area = [2370,764,1093]  # SFH, MOBILE, APT
		one_story = 0.7745
		window_wall_ratio = 0.15
		perc_gas = 0.6723
		perc_pump = 0.0559
		perc_res = 1 - perc_pump - perc_gas
		perc_AC = 0.5259
		perc_pool_pumps = 0.0818
		wh_electric = 0.6520
		wh_size = [0.2072,0.5135,0.2793]
		over_sizing_factor = 0.2

	elif data["region"] == 4:
		thermal_percentages = [[0.0526, 0.0337, 0.0806, 0.0827, 0.1081, 0.1249, 0.2539],  # sf
							   [0.0217, 0.1091, 0.0502, 0.0000, 0.0000, 0.0000, 0.0000],  # apart
							   [0.0000, 0.0491, 0.0333, 0.0000, 0.0000, 0.0000, 0.0000]]  # mh

		floor_area_scalar = [[0.4620,0.4988,0.5047,0.6724,0.7495,0.8271,1.0000], # sf
					  		 [1.0000,1.1000,1.2000,0.0000,0.0000,0.0000,0.0000], # apart
							 [1.0000,1.0000,1.0000,0.0000,0.0000,0.0000,0.0000]] # mh
		floor_area = [2655,901,1069]  # SFH, MOBILE, APT
		one_story = 0.7043
		window_wall_ratio = 0.15
		perc_gas = 0.4425
		perc_pump = 0.1983
		perc_res = 1 - perc_pump - perc_gas
		perc_AC = 0.9673
		perc_pool_pumps = 0.0657
		wh_electric = 0.3572
		wh_size = [0.2259,0.5267,0.2475]
		over_sizing_factor = 0.3

	elif data["region"] == 5:
		thermal_percentages = [[0.0526, 0.0337, 0.0806, 0.0827, 0.1081, 0.1249, 0.2539],  # sf
							   [0.0217, 0.1091, 0.0502, 0.0000, 0.0000, 0.0000, 0.0000],  # apart
							   [0.0000, 0.0491, 0.0333, 0.0000, 0.0000, 0.0000, 0.0000]]  # mh

		floor_area_scalar = [[0.4620,0.4988,0.5047,0.6724,0.7495,0.8271,1.0000], # sf
					  		 [1.0000,1.1000,1.2000,0.0000,0.0000,0.0000,0.0000], # apart
							 [1.0000,1.0000,1.0000,0.0000,0.0000,0.0000,0.0000]] # mh
		floor_area = [2655,901,1069]  # SFH, MOBILE, APT
		one_story = 0.7043
		window_wall_ratio = 0.15
		perc_gas = 0.4425
		perc_pump = 0.1983
		perc_res = 1 - perc_pump - perc_gas
		perc_AC = 0.9673
		perc_pool_pumps = 0.0657
		wh_electric = 0.3572
		wh_size = [0.2259,0.5267,0.2475]
		over_sizing_factor = 0.3

	elif data["region"] == 6:
		# Warning, this region is almost a copy of region 5!!!!
		thermal_percentages = [[0.0526, 0.0337, 0.0806, 0.0827, 0.1081, 0.1249, 0.2539],  # sf
							   [0.0217, 0.1091, 0.0502, 0.0000, 0.0000, 0.0000, 0.0000],  # apart
							   [0.0000, 0.0491, 0.0333, 0.0000, 0.0000, 0.0000, 0.0000]]  # mh

		floor_area_scalar = [[0.4620,0.4988,0.5047,0.6724,0.7495,0.8271,1.0000], # sf
					  		 [1.0000,1.1000,1.2000,0.0000,0.0000,0.0000,0.0000], # apart
							 [1.0000,1.0000,1.0000,0.0000,0.0000,0.0000,0.0000]] # mh
		floor_area = [2655,901,1069]  # SFH, MOBILE, APT
		one_story = 0.7043
		window_wall_ratio = 0.15
		perc_gas = 0.4425
		perc_pump = 0.1983
		perc_res = 1 - perc_pump - perc_gas
		perc_AC = 0.9673
		perc_pool_pumps = 0.0657
		wh_electric = 0.3572
		wh_size = [0.2259,0.5267,0.2475]
		over_sizing_factor = 0.3

	else:
		raise Exception('region "{:d}" is not defined'.format(data["region"]))

	# thermal properties for each level
	#   [sf/apart/mh][level](R-roof,R-wall,R-floor,window layers,window glass, glazing treatment, window frame, R-door, Air infiltration, COP high, COP low)
	#   Single family homes
	thermal_properties = [None]*3
	for i in xrange(3):
		thermal_properties[i] = [None] * 7

	thermal_properties[0][0] = [16.0, 10.0, 10.0, 1, 1, 1, 1, 3, .75, 2.8, 2.4]
	thermal_properties[0][1] = [19.0, 11.0, 12.0, 2, 1, 1, 1, 3, .75, 3.0, 2.5]
	thermal_properties[0][2] = [19.0, 14.0, 16.0, 2, 1, 1, 1, 3, .5, 3.2, 2.6]
	thermal_properties[0][3] = [30.0, 17.0, 19.0, 2, 1, 1, 2, 3, .5, 3.4, 2.8]
	thermal_properties[0][4] = [34.0, 19.0, 20.0, 2, 1, 1, 2, 3, .5, 3.6, 3.0]
	thermal_properties[0][5] = [36.0, 22.0, 22.0, 2, 2, 1, 2, 5, 0.25, 3.8, 3.0]
	thermal_properties[0][6] = [48.0, 28.0, 30.0, 3, 2, 2, 4, 11, 0.25, 4.0, 3.0]
	#   Apartments
	thermal_properties[1][0] = [13.4, 11.7, 9.4, 1, 1, 1, 1, 2.2, .75, 2.8, 1.9]
	thermal_properties[1][1] = [20.3, 11.7, 12.7, 2, 1, 2, 2, 2.7, 0.25, 3.0, 2.0]
	thermal_properties[1][2] = [28.7, 14.3, 12.7, 2, 2, 3, 4, 6.3, .125, 3.2, 2.1]
	#   Mobile Homes
	thermal_properties[2][0] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	thermal_properties[2][1] = [13.4, 9.2, 11.7, 1, 1, 1, 1, 2.2, .75, 2.8, 1.9]
	thermal_properties[2][2] = [24.1, 11.7, 18.1, 2, 2, 1, 2, 3, .75, 3.5, 2.2]

	# Average heating and cooling setpoints
	#  by thermal integrity type [0=sf, 1=apart, 2=mh]
	# 		[nighttime percentage,
	#		 nighttime average difference (+ indicates nightime is cooler)
	#		 high bin value
	#		 low bin value]
	cooling_setpoint = [None]*3
	heating_setpoint = [None] * 3
	cooling_setpoint[0] = [[0.098, 0.140, 0.166, 0.306, 0.206, 0.084],
						   [0.96, 0.96, 0.96, 0.96, 0.96, 0.96],
						   [69, 70, 73, 76, 79, 85],
						   [65, 70, 71, 74, 77, 80]]

	cooling_setpoint[1] = [[0.155, 0.207, 0.103, 0.310, 0.155, 0.069],
						   [0.49, 0.49, 0.49, 0.49, 0.49, 0.49],
						   [69, 70, 73, 76, 79, 85],
						   [65, 70, 71, 74, 77, 80]]

	cooling_setpoint[2] = [[0.138, 0.172, 0.172, 0.276, 0.138, 0.103],
						   [0.97, 0.97, 0.97, 0.97, 0.97, 0.97],
						   [69, 70, 73, 76, 79, 85],
						   [65, 70, 71, 74, 77, 80]]

	heating_setpoint[0] = [[0.141, 0.204, 0.231, 0.163, 0.120, 0.141],
						   [0.80, 0.80, 0.80, 0.80, 0.80, 0.80],
						   [63, 66, 69, 70, 73, 79],
						   [59, 64, 67, 70, 71, 74]]

	heating_setpoint[1] = [[0.085, 0.132, 0.147, 0.279, 0.109, 0.248],
						   [0.20, 0.20, 0.20, 0.20, 0.20, 0.20],
						   [63, 66, 69, 70, 73, 79],
						   [59, 64, 67, 70, 71, 74]]

	heating_setpoint[2] = [[0.129, 0.177, 0.161, 0.274, 0.081, 0.1770],
						   [0.88, 0.88, 0.88, 0.88, 0.88, 0.88],
						   [63, 66, 69, 70, 73, 79],
						   [59, 64, 67, 70, 71, 74]]

	# Weather data [region]
	regionWeatherFiles = ['CA-San_francisco.tmy3',
						  'IL-Chicago.tmy3',
						  'AZ-Phoenix.tmy3',
						  'TN-Nashville.tmy3',
						  'FL-Miami.tmy3',
						  'HI-Honolulu.tmy3']

	if 'thermal_percentages' not in data:
		data["thermal_percentages"] = thermal_percentages
	if 'floor_area_scalar' not in data:
		data["floor_area_scalar"] = floor_area_scalar
	if 'floor_area' not in data:
		data["floor_area"] = floor_area
	if 'one_story' not in data:
		data["one_story"] = one_story
	if 'window_wall_ratio' not in data:
		data["window_wall_ratio"] = window_wall_ratio
	if 'perc_gas' not in data:
		data["perc_gas"] = perc_gas
	if 'perc_pump' not in data:
		data["perc_pump"] = perc_pump
	if 'perc_res' not in data:
		data["perc_res"] = perc_res
	if 'perc_AC' not in data:
		data["perc_AC"] = perc_AC
	if 'perc_poolpumps' not in data:
		data["perc_poolpumps"] = perc_pool_pumps
	if 'wh_electric' not in data:
		data["wh_electric"] = wh_electric
	if 'wh_size' not in data:
		data["wh_size"] = wh_size
	if 'over_sizing_factor' not in data:
		data["over_sizing_factor"] = over_sizing_factor
	if data["weather"] is '':
		data["weather"] = regionWeatherFiles[data["region"]-1]
	if 'thermal_properties' not in data:
		data["thermal_properties"] = thermal_properties
	if 'cooling_setpoint' not in data:
		data["cooling_setpoint"] = cooling_setpoint
	if 'heating_setpoint' not in data:
		data["heating_setpoint"] = heating_setpoint

	data["no_cool_sch"] = 8
	data["no_heat_sch"] = 6
	data["no_water_sch"] = 6

	# check to see if the data is valid
	if abs(sum(sum(thermal_percentages, [])) - 1) > 0.001:
		raise Exception('Thermal percentage data is not valid!')

	if abs(perc_gas+perc_pump+perc_res - 1) > 0.001:
		raise Exception('house heat distribution is not valid!')

	if perc_pool_pumps < 0 or perc_pool_pumps > 1:
		raise Exception('Pool pump distribution is not valid!')

	if wh_electric < 0 or wh_electric > 1:
		raise Exception('Water heater distribution is not valid!')

	return data, use_flags

if __name__ == '__main__':
	pass

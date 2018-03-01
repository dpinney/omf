"""
This file contains four fuctions to add load types to a feeder based on the use flags and cofiguration defined

	append_residential(ResTechDict, use_flags, residential_dict, last_object_key, configuration_file):
		Adds residential houses to a feeder based on existing triplex loads
	append_commercial(glmCaseDict, use_flags, commercial_dict, last_object_key, use_config_file):
		Adds commercial houses to a feeder based on existing loads
	add_normalized_residential_ziploads(loadshape_dict, residenntial_dict, config_data, last_key):
		Adds residential zip load to a feeder based on existing triplex loads
	add_normalized_commercial_ziploads(loadshape_dict, commercial_dict, config_data, last_key):
		Adds commercial zip load to a feeder based on existing loads
	add_residential_EVs(glmCaseDict, config_file, last_key):
		Adds residential EVs to a feeder

Modified December 21, 2016 by Jacob Hansen (jacob.hansen@pnnl.gov)
Created April 13, 2013 by Andy Fisher (andy.fisher@pnnl.gov)

Copyright (c) 2013 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
Government, including the right to distribute to other Government contractors.
"""
from __future__ import division
import math, random

def append_residential(ResTechDict, use_flags, residential_dict, last_object_key, config_data):
	"""
	This fucntion appends residential houses to a feeder based on existing triplex loads

	Inputs
		ResTechDict - dictionary containing the full feeder
		use_flags - dictionary that contains the use flags
		residential_dict - dictionary that contains information about residential loads spots
		last_object_key - Last object key
		configuration_file - dictionary that contains the configurations of the feeder

	Outputs
		ResTechDict -  dictionary containing the full feeder
		last_object_key - Last object key
	"""

	# Initialize psuedo-random seed
	# random.seed(3)

	# Check if last_object_key exists in glmCaseDict
	if last_object_key in ResTechDict:
		while last_object_key in ResTechDict:
			last_object_key += 1
	
	# Begin adding residential house dictionaries
	if use_flags['use_homes'] == 1 and len(residential_dict) > 0:
		count_house = 0
		fl_area = []

		# In order to ensure we follow the thermal integrity distribution we will need to base it off the total populations of houses to be attached
		total_no_houses = 0
		for x in residential_dict:
			total_no_houses += residential_dict[x]['number_of_houses']

		# Create a histogram of what the thermal integrity of the houses should be
		thermal_integrity = [[math.ceil(x * total_no_houses) for x in config_data['thermal_percentages'][y]] for y in xrange(0,len(config_data['thermal_percentages']))]

		# list of how many house per type
		total_houses_by_type = [sum(x) for x in thermal_integrity] #[sum(x) for x in zip(*thermal_integrity)]

		# only allow pool pumps on single family homes
		no_pool_pumps = total_houses_by_type[0]

		# number of water heater to implement
		no_water_heaters = math.ceil(total_no_houses * config_data['wh_electric'])

		# Create a histogram of what the heating and cooling schedules of the houses should be
		cool_sp = [[math.ceil(x * total_houses_by_type[y]) for x in config_data['cooling_setpoint'][y][0]] for y in xrange(0,len(config_data['cooling_setpoint']))]
		heat_sp = [[math.ceil(x * total_houses_by_type[y]) for x in config_data['heating_setpoint'][y][0]] for y in xrange(0, len(config_data['heating_setpoint']))]

		# Create a histogram of what the water heater sizes should be
		wh_sp = [math.ceil(x * no_water_heaters) for x in config_data['wh_size'] ]

		#print('iterating over residential_dict')
		# Begin attaching houses to designated triplex_meters
		for x in residential_dict:
			if residential_dict[x]['number_of_houses'] > 0:
				if residential_dict[x]['parent'] != 'None':
					my_name = residential_dict[x]['parent'] #+ '_' + residential_dict[x]['name']
					my_parent = residential_dict[x]['parent']
				else:
					my_name = residential_dict[x]['name']
					my_parent = residential_dict[x]['name']

				no_houses = residential_dict[x]['number_of_houses']
				phase = residential_dict[x]['phases']
				lg_vs_sm = residential_dict[x]['large_vs_small']

				#print('iterating over number of houses')
				# Start adding house dictionaries
				for y in xrange(no_houses):
					ResTechDict[last_object_key] = {'object' : 'triplex_meter',
													'phases' : '{:s}'.format(phase),
													'name' : 'tpm{:d}_{:s}'.format(y,my_name),
													'parent' : '{:s}'.format(my_parent),
													'groupid' : 'Residential_Meter',
													'nominal_voltage' : '120'}
					last_object_key += 1

					# Create the house dictionary
					ResTechDict[last_object_key] = {'object' : 'house',
													'name' : 'house{:d}_{:s}'.format(y,my_name),
													'parent' : 'tpm{:d}_{:s}'.format(y,my_name),
													'groupid' : 'Residential'}

					# Calculate the  residential schedule skew value
					skew_value = config_data['residential_skew_std']*random.normalvariate(0,1)

					if skew_value < -1*config_data['residential_skew_max']:
						skew_value = -1*config_data['residential_skew_max']
					elif skew_value > config_data['residential_skew_max']:
						skew_value = config_data['residential_skew_max']

					# Additional skew outside the residential skew max
					skew_value = skew_value + config_data['residential_skew_shift']

					# Calculate the waterheater schedule skew
					wh_skew_value = 3*config_data['residential_skew_std']*random.normalvariate(0,1)

					if wh_skew_value < -6*config_data['residential_skew_max']:
						wh_skew_value = -6*config_data['residential_skew_max']
					elif wh_skew_value > 6*config_data['residential_skew_max']:
						wh_skew_value = 6*config_data['residential_skew_max']

					# Scale this skew up to weeks
					pp_skew_value = 128*config_data['residential_skew_std']*random.normalvariate(0,1)

					if pp_skew_value < -128*config_data['residential_skew_max']:
						pp_skew_value = -128*config_data['residential_skew_max']
					elif pp_skew_value > 128*config_data['residential_skew_max']:
						pp_skew_value = 128*config_data['residential_skew_max']

					ResTechDict[last_object_key]['schedule_skew'] = '{:.0f}'.format(skew_value)

					# Choose what type of building we are going to use
					# and set the thermal integrity of said building
					size_a = len(thermal_integrity)
					size_b = len(thermal_integrity[0])

					therm_int = int(math.ceil(size_a * size_b * random.random()))

					row_ti = therm_int % size_a
					col_ti = therm_int % size_b

					# print thermal_integrity

					while thermal_integrity[row_ti][col_ti] < 1:
						therm_int = int(math.ceil(size_a * size_b * random.random()))
						row_ti = therm_int % size_a
						col_ti = therm_int % size_b

					thermal_integrity[row_ti][col_ti] -= 1
					thermal_temp = config_data['thermal_properties'][row_ti][col_ti]

					f_area_base = config_data['floor_area'][row_ti]
					f_area_dist = config_data['floor_area_scalar'][row_ti]
					story_rand = random.random()
					height_rand = random.randint(0,2) # add aither 0, 1, or 2 feet to the base heigth
					fa_rand = random.random()

					# Manipulate the floor area based on age
					floor_area = (f_area_base*f_area_dist[col_ti]) + ((f_area_base*f_area_dist[col_ti]) / 2.) * (0.5 - fa_rand) # +- 25%

					# Determine one story vs. two story house along with ceiling height
					if row_ti == 0:
						# single family home
						if story_rand < config_data['one_story']:
							stories = 1
						else:
							stories = 2
					else:
						# apartment of mobile home
						stories = 1
						height_rand = 0

					# Now also adjust square footage as a factor of whether
					# the load modifier (avg_house) rounded up or down
					floor_area *= (1 + lg_vs_sm)

					if floor_area > 4000:
						floor_area = 3800 + fa_rand*200
					elif floor_area < 300:
						floor_area = 300 + fa_rand*100

					fl_area.append(floor_area)
					count_house += 1

					ResTechDict[last_object_key]['floor_area'] = '{:.0f}'.format(floor_area)
					ResTechDict[last_object_key]['number_of_stories'] = '{:.0f}'.format(stories)

					ceiling_height = 8 + height_rand
					ResTechDict[last_object_key]['ceiling_height'] = '{:.0f}'.format(ceiling_height)

					building_type = ['Single Family','Apartment','Mobile Home']
					ResTechDict[last_object_key]['comment'] = '//Thermal integrity -> {:s} {:d}'.format(building_type[row_ti],col_ti)

					rroof = thermal_temp[0] * (0.8 + (0.4 * random.random()))
					ResTechDict[last_object_key]['Rroof'] = '{:.2f}'.format(rroof)

					rwall =  thermal_temp[1] * (0.8 + (0.4 * random.random()))
					ResTechDict[last_object_key]['Rwall'] = '{:.2f}'.format(rwall)

					rfloor =  thermal_temp[2] * (0.8 + (0.4 * random.random()))
					ResTechDict[last_object_key]['Rfloor'] = '{:.2f}'.format(rfloor)
					ResTechDict[last_object_key]['glazing_layers'] = '{:.0f}'.format(thermal_temp[3])
					ResTechDict[last_object_key]['glass_type'] = '{:.0f}'.format(thermal_temp[4])
					ResTechDict[last_object_key]['glazing_treatment'] = '{:.0f}'.format(thermal_temp[5])
					ResTechDict[last_object_key]['window_frame'] = '{:.0f}'.format(thermal_temp[6])

					rdoor =  thermal_temp[7] * (0.8 + (0.4 * random.random()))
					ResTechDict[last_object_key]['Rdoors'] = '{:.2f}'.format(rdoor)

					airchange =  thermal_temp[8] * (0.8 + (0.4 * random.random()))
					ResTechDict[last_object_key]['airchange_per_hour'] = '{:.2f}'.format(airchange)

					c_COP =  thermal_temp[10] + (random.random() * (thermal_temp[9] - thermal_temp[10]))
					ResTechDict[last_object_key]['cooling_COP'] = '{:.2f}'.format(c_COP)

					init_temp = 68. + (4. * random.random())
					ResTechDict[last_object_key]['air_temperature'] = '{:.2f}'.format(init_temp)
					ResTechDict[last_object_key]['mass_temperature'] = '{:.2f}'.format(init_temp)

					ResTechDict[last_object_key]['window_wall_ratio'] = '{:.2f}'.format(config_data['window_wall_ratio'])

					# This is a bit of a guess from Rob's estimates
					mass_floor = 2.5 + (1.5 * random.random())
					ResTechDict[last_object_key]['total_thermal_mass_per_floor_area'] = '{:.3f}'.format(mass_floor)

					heat_type = random.random()
					cool_type = random.random()
					h_COP = c_COP

					# ct = 'NONE'
					if heat_type <= config_data['perc_gas']:
						ResTechDict[last_object_key]['heating_system_type'] = 'GAS'

						if cool_type <= config_data['perc_AC']:
							ResTechDict[last_object_key]['cooling_system_type'] = 'ELECTRIC'
							ResTechDict[last_object_key]['motor_model'] = 'BASIC'
							ResTechDict[last_object_key]['motor_efficiency'] = 'GOOD'
							# ct = 'ELEC'
						else:
							ResTechDict[last_object_key]['cooling_system_type'] = 'NONE'

						# ht = 'GAS'
					elif heat_type <= (config_data['perc_gas'] + config_data['perc_pump']):
						ResTechDict[last_object_key]['heating_system_type'] = 'HEAT_PUMP'
						ResTechDict[last_object_key]['heating_COP'] = '{:.1f}'.format(h_COP)
						ResTechDict[last_object_key]['cooling_system_type'] = 'ELECTRIC'
						ResTechDict[last_object_key]['auxiliary_strategy'] = 'DEADBAND'
						ResTechDict[last_object_key]['auxiliary_system_type'] = 'ELECTRIC'
						ResTechDict[last_object_key]['motor_model'] = 'BASIC'
						ResTechDict[last_object_key]['motor_efficiency'] = 'AVERAGE'
						# ht = 'HP'
						# ct = 'ELEC'
					elif (floor_area * ceiling_height) > 12000: # No resistive homes with large volumes
						ResTechDict[last_object_key]['heating_system_type'] = 'GAS'

						if cool_type <= config_data['perc_AC']:
							ResTechDict[last_object_key]['cooling_system_type'] = 'ELECTRIC'
							ResTechDict[last_object_key]['motor_model'] = 'BASIC'
							ResTechDict[last_object_key]['motor_efficiency'] = 'GOOD'
							# ct = 'ELEC'
						else:
							ResTechDict[last_object_key]['cooling_system_type'] = 'NONE'

						# ht = 'GAS'
					else:
						ResTechDict[last_object_key]['heating_system_type'] = 'RESISTANCE'

						if cool_type <= config_data['perc_AC']:
							ResTechDict[last_object_key]['cooling_system_type'] = 'ELECTRIC'
							ResTechDict[last_object_key]['motor_model'] = 'BASIC'
							ResTechDict[last_object_key]['motor_efficiency'] = 'GOOD'
							# ct = 'ELEC'
						else:
							ResTechDict[last_object_key]['cooling_system_type'] = 'NONE'

						# ht = 'ELEC'

					os_rand = config_data['over_sizing_factor'] * (0.8 + (0.4 * random.random()))
					ResTechDict[last_object_key]['over_sizing_factor'] = '{:.1f}'.format(os_rand)

					ResTechDict[last_object_key]['breaker_amps'] = '1000'
					ResTechDict[last_object_key]['hvac_breaker_rating'] = '1000'

					# Choose a cooling and heating schedule
					cooling_set = int(math.ceil(config_data['no_cool_sch'] * random.random()))
					heating_set = int(math.ceil(config_data['no_heat_sch'] * random.random()))

					# Choose a cooling bin
					coolsp = config_data['cooling_setpoint'][row_ti]
					no_cool_bins = len(coolsp[0])

					# See if we have that bin left
					cool_bin = random.randint(0,no_cool_bins - 1)

					while cool_sp[row_ti][cool_bin] < 1:
						cool_bin = random.randint(0,no_cool_bins - 1)

					cool_sp[row_ti][cool_bin] -= 1

					# Choose a heating bin
					heatsp = config_data['heating_setpoint'][row_ti]
					no_heat_bins = len(heatsp[0])
					find = False

					# we have already choosen a cool bing and since they allign with the heating bins we will first check to see if the coresponding heat bin is available
					heat_bin = cool_bin
					while heat_sp[row_ti][heat_bin] < 1 or heatsp[2][heat_bin] >= coolsp[3][cool_bin]:
						if heat_bin <= 0:
							# we ended up with the lowest bin. We make one more attempt to find another bin by random search
							heat_bin = random.randint(0,no_heat_bins - 1)
							heat_count = 1

							while heat_sp[row_ti][heat_bin] < 1 or heatsp[2][heat_bin] >= coolsp[3][cool_bin]:
								heat_bin = random.randint(0,no_heat_bins - 1)

								# if we tried a few times, give up and take an extra
								# draw from the lowest bin
								if heat_count > 20:
									heat_bin = 0
									find = True
									break

								heat_count += 1

						if find:
							break
						heat_bin -= 1

					heat_sp[row_ti][heat_bin] -= 1

					# Randomly choose within the bin, then +/- one
					# degree to seperate the deadbands
					cool_night = (coolsp[2][cool_bin] - coolsp[3][cool_bin]) * random.random() + coolsp[3][cool_bin] + 1
					heat_night = (heatsp[2][heat_bin] - heatsp[3][heat_bin]) * random.random() + heatsp[3][heat_bin] - 1

					# 1-15-2013: made a change so that cool and heat
					# diff's are based off same random value -JLH
					diff_rand = random.random()
					cool_night_diff = coolsp[1][cool_bin] * 2. * diff_rand
					heat_night_diff = heatsp[1][heat_bin] * 2. * diff_rand

					#heat_night += config_data['addtl_heat_degrees']

					if use_flags['use_schedules'] == 1:
						if use_flags['houseThermostatMode'] == 'COOL': # cooling only
							ResTechDict[last_object_key]['cooling_setpoint'] = 'cooling{:d}*{:.2f}+{:.2f}'.format(cooling_set,cool_night_diff,cool_night)
							ResTechDict[last_object_key]['heating_setpoint'] = '40'
						elif use_flags['houseThermostatMode'] == 'HEAT': # heating only
							ResTechDict[last_object_key]['cooling_setpoint'] = '110'
							ResTechDict[last_object_key]['heating_setpoint'] = 'heating{:d}*{:.2f}+{:.2f}'.format(heating_set,heat_night_diff,heat_night)
						else: # auto so both cooling and heating
							ResTechDict[last_object_key]['cooling_setpoint'] = 'cooling{:d}*{:.2f}+{:.2f}'.format(cooling_set,cool_night_diff,cool_night)
							ResTechDict[last_object_key]['heating_setpoint'] = 'heating{:d}*{:.2f}+{:.2f}'.format(heating_set,heat_night_diff,heat_night)
					else:
						ResTechDict[last_object_key]['cooling_setpoint'] = '{:.2f}'.format(cool_night)
						ResTechDict[last_object_key]['heating_setpoint'] = '{:.2f}'.format(heat_night)


					# add some randomness to the compressor lock time, range will be 1-3 minutes
					onLock = random.randint(30,90)
					offLock = random.randint(30,90)

					ResTechDict[last_object_key]['thermostat_off_cycle_time'] = '{:d}'.format(offLock)
					ResTechDict[last_object_key]['thermostat_on_cycle_time'] = '{:d}'.format(onLock)


					last_object_key += 1

					# Add the end-use ZIPload objects to the house
					# Scale all of the end-use loads
					scalar_base = config_data['base_load_scalar']
					scalar1 = ((324.9 / 8907.) * pow(floor_area,0.442)) * scalar_base
					scalar2 = 0.8 + 0.4 * random.random()
					scalar3 = 0.8 + 0.4 * random.random()
					resp_scalar = scalar1 * scalar2
					unresp_scalar = scalar1 * scalar3

					# average size is 1.36 kW
					# Energy Savings through Automatic Seasonal Run-Time Adjustment of Pool Filter Pumps
					# Stephen D Allen, B.S. Electrical Engineering
					pool_pump_power = 1.36 + .36*random.random()
					pool_pump_perc = random.random()

					# average 4-12 hours / day -> 1/6-1/2 duty cycle
					# typically run for 2 - 4 hours at a time
					pp_dutycycle = 1./6. + (1./2. - 1./6.)*random.random()
					pp_period = 4. + 4.*random.random()
					pp_init_phase = random.random()

					# Add responsive ZIPload

					ResTechDict[last_object_key] = {'object' : 'ZIPload',
													'name' : 'house{:d}_resp_{:s}'.format(y,my_name),
													'parent' : 'house{:d}_{:s}'.format(y,my_name),
													'comment' : '// Responsive load',
													'groupid' : 'Responsive_load',
													# 'groupid': 'Residential_zip',
													'schedule_skew' : '{:.0f}'.format(skew_value),
													'base_power' : 'responsive_loads*{:.2f}'.format(resp_scalar),
													'heatgain_fraction' : '{:.3f}'.format(config_data['r_heat_fraction']),
													'power_pf' : '{:.3f}'.format(config_data['r_p_pf']),
													'current_pf' : '{:.3f}'.format(config_data['r_i_pf']),
													'impedance_pf' : '{:.3f}'.format(config_data['r_z_pf']),
													'impedance_fraction' : '{:f}'.format(config_data['r_zfrac']),
													'current_fraction' : '{:f}'.format(config_data['r_ifrac']),
													'power_fraction' : '{:f}'.format(config_data['r_pfrac'])}

					# if we do not use schedules we will assume resp_scalar is the fixed value
					if use_flags['use_schedules'] == 0:
						ResTechDict[last_object_key]['base_power'] = '{:.2f}'.format(resp_scalar)

					last_object_key += 1

					# Add unresponsive ZIPload object
					ResTechDict[last_object_key] = {'object' : 'ZIPload',
													'name' : 'house{:d}_unresp_{:s}'.format(y,my_name),
													'parent' : 'house{:d}_{:s}'.format(y,my_name),
													'comment' : '// Unresponsive load',
													'groupid' : 'Unresponsive_load',
													# 'groupid': 'Residential_zip',
													'schedule_skew' : '{:.0f}'.format(skew_value),
													'base_power' : 'unresponsive_loads*{:.2f}'.format(unresp_scalar),
													'heatgain_fraction' : '{:.3f}'.format(config_data['r_heat_fraction']),
													'power_pf' : '{:.3f}'.format(config_data['r_p_pf']),
													'current_pf' : '{:.3f}'.format(config_data['r_i_pf']),
													'impedance_pf' : '{:.3f}'.format(config_data['r_z_pf']),
													'impedance_fraction' : '{:f}'.format(config_data['r_zfrac']),
													'current_fraction' : '{:f}'.format(config_data['r_ifrac']),
													'power_fraction' : '{:f}'.format(config_data['r_pfrac'])}

					# if we do not use schedules we will assume unresp_scalar is the fixed value
					if use_flags['use_schedules'] == 0:
						ResTechDict[last_object_key]['base_power'] = '{:.2f}'.format(unresp_scalar)

					last_object_key += 1
					#print('finished unresponsive zipload')
					# Add pool pumps only on single-family homes
					if pool_pump_perc < (2.*config_data['perc_poolpumps']) and no_pool_pumps >= 1 and row_ti == 0:
						ResTechDict[last_object_key] = {'object' : 'ZIPload',
														'name' : 'house{:d}_ppump_{:s}'.format(y,my_name),
														'parent' : 'house{:d}_{:s}'.format(y,my_name),
														'comment' : '// Pool Pump',
														'groupid' : 'Pool_Pump',
														# 'groupid': 'Residential_zip',
														'schedule_skew' : '{:.0f}'.format(pp_skew_value),
														'base_power' : 'pool_pump_season*{:.2f}'.format(pool_pump_power),
														'duty_cycle' : '{:.2f}'.format(pp_dutycycle),
														'phase' : '{:.2f}'.format(pp_init_phase),
														'period' : '{:.2f}'.format(pp_period),
														'heatgain_fraction' : '0.0',
														'power_pf' : '{:.3f}'.format(config_data['r_p_pf']),
														'current_pf' : '{:.3f}'.format(config_data['r_i_pf']),
														'impedance_pf' : '{:.3f}'.format(config_data['r_z_pf']),
														'impedance_fraction' : '{:f}'.format(config_data['r_zfrac']),
														'current_fraction' : '{:f}'.format(config_data['r_ifrac']),
														'power_fraction' : '{:f}'.format(config_data['r_pfrac']),
														'is_240' : 'TRUE'}

						# if we do not use schedules we will assume the pool pump never running
						if use_flags['use_schedules'] == 0:
							ResTechDict[last_object_key]['base_power'] = '0'

						no_pool_pumps -= 1
						last_object_key += 1

					# Add Water heater objects
					heat_element = 3.0 + (0.5 * random.randint(1,5))
					tank_height = 3.78
					tank_set = 120. + (16 * random.random())
					tank_temp = 130. + (12 * random.random())
					therm_dead = 4. + (4. * random.random())
					tank_UA = 2. + (2. * random.random())
					water_sch = math.ceil(config_data['no_water_sch'] * random.random())
					water_var = 0.95 + (random.random() * 0.1)
					wh_size_test = random.random()
					wh_size_rand = random.randint(0,2)

					# waterDemandScale = 0.245 * (1 + 0.331555 * random.random())
					# waterEnergy = 2 + (0.25 * random.random())
					# waterPeriod = 160 + (30 * random.random())
					# waterCount = 5 + (3 * random.random())
					# waterDemandScale = 0.245 * (1 + 0.331555 * random.random())
					# waterEnergy = 2 + (0.25 * random.random())
					# waterCount = 5 + (3 * random.random())
					# waterDuration = 160 #+ (30 * random.random())
					# waterQOFF = 2
					# waterQON = 4

					if heat_type <= config_data['wh_electric']:
						ResTechDict[last_object_key] = {'object' : 'waterheater',
														'groupid': 'water_heater',
														'name' : 'house{:d}_wh_{:s}'.format(y,my_name),
														'parent' : 'house{:d}_{:s}'.format(y,my_name),
														'schedule_skew' : '{:.0f}'.format(wh_skew_value),
														'heating_element_capacity' : '{:.1f} kW'.format(heat_element),
														'tank_setpoint' : '{:.1f}'.format(tank_set),
														'temperature': '{:.1f}'.format(tank_temp),
														'thermostat_deadband' : '{:.1f}'.format(therm_dead),
														'location' : 'INSIDE',
														'tank_UA' : '{:.1f}'.format(tank_UA),
														'tank_height': '{:.2f}'.format(tank_height)}#,
														#'water_demand' : 'this.myshape*{:.3f}'.format(waterDemandScale),
														#'myshape' : '"type: modulated; schedule: WATERHEATER; energy: {:.3f} kWh; period: {:.3f} s; count: {:.3f}; modulation: amplitude"'.format(waterEnergy, waterPeriod, waterCount)}
														#'myshape' : '"type: queued; schedule: WATERHEATER; energy: {:.3f} kWh; count: {:.3f}; duration: {:.3f} s; q_on: {:.3f}; q_off: {:.3f}";'.format(waterEnergy, waterCount, waterDuration, waterQON, waterQOFF)}
														#'myshape': '"type: pulsed; schedule: WATERHEATER; energy: {:.3f} kWh; count: {:.3f}; duration: {:.3f} s;"'.format(waterEnergy, waterCount, waterDuration)}

						# determine tank size and schedule to use
						if wh_size_test < config_data['wh_size'][0]:
							ResTechDict[last_object_key]['water_demand'] = 'small_{:.0f}*{:.02f}'.format(water_sch,water_var)
							whsize = 20. + (5. * wh_size_rand)
							wh_sp[0] -= 1
						elif wh_size_test < (config_data['wh_size'][0] + config_data['wh_size'][1]):
							if floor_area < 2000:
								ResTechDict[last_object_key]['water_demand'] = 'small_{:.0f}*{:.02f}'.format(water_sch,water_var)
							else:
								ResTechDict[last_object_key]['water_demand'] = 'large_{:.0f}*{:.02f}'.format(water_sch,water_var)
							whsize = 30. + (10. * wh_size_rand)
							wh_sp[1] -= 1
						else:
							ResTechDict[last_object_key]['water_demand'] = 'large_{:.0f}*{:.02f}'.format(water_sch,water_var)
							whsize = 50. + (10. * wh_size_rand)
							wh_sp[2] -= 1

						ResTechDict[last_object_key]['tank_volume'] = '{:.0f}'.format(whsize)

						# if we do not use schedules we will assume the water heater is just a storage tank
						if use_flags['use_schedules'] == 0:
							ResTechDict[last_object_key]['water_demand'] = '0'

						last_object_key += 1

				#print('finished water heater')
			#print('finished iterating over number of houses')
		#print('finished iterating over residential dict')
	return ResTechDict, last_object_key

def add_normalized_residential_ziploads(loadshape_dict, residenntial_dict, config_data, last_key):
	"""
	This fucntion appends residential zip loads to a feeder based on existing triplex loads

	Inputs
		loadshape_dict - dictionary containing the full feeder
		residenntial_dict - dictionary that contains information about residential loads spots
		last_key - Last object key
		config_data - dictionary that contains the configurations of the feeder

	Outputs
		loadshape_dict -  dictionary containing the full feeder
		last_key - Last object key
	"""

	for x in residenntial_dict.keys():
		tpload_name = residenntial_dict[x]['name']
		tpload_parent = residenntial_dict[x].get('parent', 'None')
		tpphases = residenntial_dict[x]['phases']
		tpnom_volt = '120.0'
		bp = residenntial_dict[x]['load'] * config_data['normalized_loadshape_scalar']

		loadshape_dict[last_key] = {'object': 'triplex_load',
									'name': '{:s}_loadshape'.format(tpload_name),
									'phases': tpphases,
									'nominal_voltage': tpnom_volt}
		if tpload_parent != 'None':
			loadshape_dict[last_key]['parent'] = tpload_parent
		else:
			loadshape_dict[last_key]['parent'] = tpload_name

		if bp > 0.0:
			loadshape_dict[last_key]['base_power_12'] = 'norm_feeder_loadshape.value*{:f}'.format(bp)
			loadshape_dict[last_key]['power_pf_12'] = '{:f}'.format(config_data['r_p_pf'])
			loadshape_dict[last_key]['current_pf_12'] = '{:f}'.format(config_data['r_i_pf'])
			loadshape_dict[last_key]['impedance_pf_12'] = '{:f}'.format(config_data['r_z_pf'])
			loadshape_dict[last_key]['power_fraction_12'] = '{:f}'.format(config_data['r_pfrac'])
			loadshape_dict[last_key]['current_fraction_12'] = '{:f}'.format(config_data['r_ifrac'])
			loadshape_dict[last_key]['impedance_fraction_12'] = '{:f}'.format(config_data['r_zfrac'])

		last_key += last_key

	return loadshape_dict, last_key


def append_commercial(glmCaseDict, use_flags, commercial_dict, last_object_key, config_data):
	"""
	This fucntion appends commercial houses to a feeder based on existing loads

	Inputs
		glmCaseDict - dictionary containing the full feeder
		use_flags - dictionary that contains the use flags
		commercial_dict - dictionary that contains information about commercial loads spots
		last_object_key - Last object key
		use_config_file - dictionary that contains the configurations of the feeder

	Outputs
		glmCaseDict -  dictionary containing the full feeder
		last_object_key - Last object key
	"""

	# Initialize psuedo-random seed
	# random.seed(4)

	# Phase ABC - convert to "commercial buildings"
	#  if number of "houses" > 15, then create a large office
	#  if number of "houses" < 15 but > 6, create a big box commercial
	#  else, create a residential strip mall

	# If using Configuration.m and load classifications,
	#  building type is chosen according to classification
	#  regardless of number of "houses"


	# Check if last_object_key exists in glmCaseDict
	if last_object_key in glmCaseDict:
		while last_object_key in glmCaseDict:
			last_object_key += 1

	if len(commercial_dict) > 0 and use_flags["use_commercial"] == 1:
		# setup all of the line configurations we may need
		glmCaseDict[last_object_key] = {"object": "triplex_line_conductor",
										"name": "comm_line_cfg_cnd1",
										"resistance": "0.48",
										"geometric_mean_radius": "0.0158"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "triplex_line_conductor",
										"name": "comm_line_cfg_cnd2",
										"resistance": "0.48",
										"geometric_mean_radius": "0.0158"}

		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "triplex_line_conductor",
										"name": "comm_line_cfg_cndN",
										"resistance": "0.48",
										"geometric_mean_radius": "0.0158"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "triplex_line_configuration",
										"name": "commercial_line_config",
										"conductor_1": "comm_line_cfg_cnd1",
										"conductor_2": "comm_line_cfg_cnd2",
										"conductor_N": "comm_line_cfg_cndN",
										"insulation_thickness": "0.08",
										"diameter": "0.522"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "line_spacing",
										"name": "line_spacing_commABC",
										"distance_AB": "53.19999999996 in",
										"distance_BC": "53.19999999996 in",
										"distance_AC": "53.19999999996 in",
										"distance_AN": "69.80000000004 in",
										"distance_BN": "69.80000000004 in",
										"distance_CN": "69.80000000004 in"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "overhead_line_conductor",
										"name": "overhead_line_conductor_comm",
										"rating.summer.continuous": "443.0",
										"geometric_mean_radius": "0.02270 ft",
										"resistance": "0.05230"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "line_configuration",
										"name": "line_configuration_commABC",
										"conductor_A": "overhead_line_conductor_comm",
										"conductor_B": "overhead_line_conductor_comm",
										"conductor_C": "overhead_line_conductor_comm",
										"conductor_N": "overhead_line_conductor_comm",
										"spacing": "line_spacing_commABC"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "line_configuration",
										"name": "line_configuration_commAB",
										"conductor_A": "overhead_line_conductor_comm",
										"conductor_B": "overhead_line_conductor_comm",
										"conductor_N": "overhead_line_conductor_comm",
										"spacing": "line_spacing_commABC"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "line_configuration",
										"name": "line_configuration_commAC",
										"conductor_A": "overhead_line_conductor_comm",
										"conductor_C": "overhead_line_conductor_comm",
										"conductor_N": "overhead_line_conductor_comm",
										"spacing": "line_spacing_commABC"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "line_configuration",
										"name": "line_configuration_commBC",
										"conductor_B": "overhead_line_conductor_comm",
										"conductor_C": "overhead_line_conductor_comm",
										"conductor_N": "overhead_line_conductor_comm",
										"spacing": "line_spacing_commABC"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "line_configuration",
										"name": "line_configuration_commA",
										"conductor_A": "overhead_line_conductor_comm",
										"conductor_N": "overhead_line_conductor_comm",
										"spacing": "line_spacing_commABC"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "line_configuration",
										"name": "line_configuration_commB",
										"conductor_B": "overhead_line_conductor_comm",
										"conductor_N": "overhead_line_conductor_comm",
										"spacing": "line_spacing_commABC"}
		last_object_key += 1

		glmCaseDict[last_object_key] = {"object": "line_configuration",
										"name": "line_configuration_commC",
										"conductor_C": "overhead_line_conductor_comm",
										"conductor_N": "overhead_line_conductor_comm",
										"spacing": "line_spacing_commABC"}
		last_object_key += 1

		# initializations for the commercial "house" list

		# print('iterating over commercial_dict')
		for iii in commercial_dict:
			total_comm_houses = commercial_dict[iii]['number_of_houses'][0] + commercial_dict[iii]['number_of_houses'][1] + commercial_dict[iii]['number_of_houses'][2]

			my_phases = 'ABC'

			# read through the phases and do some bit-wise math
			has_phase_A = 0
			has_phase_B = 0
			has_phase_C = 0
			ph = ''
			if "A" in commercial_dict[iii]['phases']:
				has_phase_A = 1
				ph += 'A'
			if "B" in commercial_dict[iii]['phases']:
				has_phase_B = 1
				ph += 'B'
			if "C" in commercial_dict[iii]['phases']:
				has_phase_C = 1
				ph += 'C'

			no_of_phases = has_phase_A + has_phase_B + has_phase_C

			if no_of_phases == 0:
				raise Exception('The phases in commercial buildings did not add up right.')

			# name of original load object
			if commercial_dict[iii]['parent'] != 'None':
				my_name = commercial_dict[iii]['parent'] #+ '_' + commercial_dict[iii]['name']
				my_parent = commercial_dict[iii]['parent']
			else:
				my_name = commercial_dict[iii]['name']
				my_parent = commercial_dict[iii]['name']

			nom_volt = int(float(commercial_dict[iii]['nom_volt']))

			# Same for everyone
			# air_heat_fraction = 0
			# mass_solar_gain_fraction = 0.5
			# mass_internal_gain_fraction = 0.5
			fan_type = 'ONE_SPEED'
			heat_type = 'GAS'
			cool_type = 'ELECTRIC'
			aux_type = 'NONE'
			# cooling_design_temperature = 100
			# heating_design_temperature = 1
			# over_sizing_factor = 0.3
			no_of_stories = 1
			surface_heat_trans_coeff = 0.59

			# Office building - must have all three phases and enough load for 15 zones
			#                     *or* load is classified to be office buildings
			if total_comm_houses > 15 and no_of_phases == 3:
				no_of_offices = int(round(total_comm_houses / 15))

				glmCaseDict[last_object_key] = {"object": "transformer_configuration",
												"name": "CTTF_config_A_{:s}".format(my_name),
												"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
												"install_type": "POLETOP",
												"impedance": "0.00033+0.0022j",
												"shunt_impedance": "10000+10000j",
												"primary_voltage": "{:.3f}".format(nom_volt),
												# might have to change to 7200/sqrt(3)
												"secondary_voltage": "{:.3f}".format(120*math.sqrt(3)),
												"powerA_rating": "50 kVA"}
				last_object_key += 1

				glmCaseDict[last_object_key] = {"object": "transformer_configuration",
												"name": "CTTF_config_B_{:s}".format(my_name),
												"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
												"install_type": "POLETOP",
												"impedance": "0.00033+0.0022j",
												"shunt_impedance": "10000+10000j",
												"primary_voltage": "{:.3f}".format(nom_volt),
												# might have to change to 7200/sqrt(3)
												"secondary_voltage": "{:.3f}".format(120*math.sqrt(3)),
												"powerB_rating": "50 kVA"}
				last_object_key += 1

				glmCaseDict[last_object_key] = {"object": "transformer_configuration",
												"name": "CTTF_config_C_{:s}".format(my_name),
												"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
												"install_type": "POLETOP",
												"impedance": "0.00033+0.0022j",
												"shunt_impedance": "10000+10000j",
												"primary_voltage": "{:.3f}".format(nom_volt),
												# might have to change to 7200/sqrt(3)
												"secondary_voltage": "{:.3f}".format(120*math.sqrt(3)),
												"powerC_rating": "50 kVA"}
				last_object_key += 1
				# print('iterating over number of offices')
				for jjj in xrange(no_of_offices):
					floor_area_choose = 40000. * (0.5 * random.random() + 0.5)  # up to -50# #config_data.floor_area
					ceiling_height = 13.
					airchange_per_hour = 0.69
					Rroof = 19.
					Rwall = 18.3
					Rfloor = 46.
					Rdoors = 3.
					glazing_layers = 'TWO'
					glass_type = 'GLASS'
					glazing_treatment = 'LOW_S'
					window_frame = 'NONE'
					int_gains = 3.24  # W/sf

					glmCaseDict[last_object_key] = {"object": "overhead_line",
													"from": "{:s}".format(my_parent),
													"to": "{:s}_office_meter{:.0f}".format(my_name, jjj),
													"phases": "{:s}".format(commercial_dict[iii]['phases']),
													"length": "50ft",
													"configuration": "line_configuration_comm{:s}".format(ph)}
					last_object_key += 1

					glmCaseDict[last_object_key] = {"object": "meter",
													"phases": "{:s}".format(commercial_dict[iii]['phases']),
													"name": "{:s}_office_meter{:.0f}".format(my_name, jjj),
													"groupid": "Commercial_Meter",
													"nominal_voltage": "{:f}".format(nom_volt)}
					last_object_key += 1

					# for phind = 1:3 #for each of three floors (5 zones each)
					# for phind = 1:no_of_phases #jlh
					for phind in xrange(1,4):
						glmCaseDict[last_object_key] = {"object": "transformer",
														"name": "{:s}_CTTF_{:s}_{:.0f}".format(my_name, ph[phind-1], jjj),
														"phases": "{:s}S".format(ph[phind-1]),
														"from": "{:s}_office_meter{:.0f}".format(my_name, jjj),
														"to": "{:s}_tm_{:s}_{:.0f}".format(my_name, ph[phind-1], jjj),
														"groupid": "Distribution_Trans",
														"configuration": "CTTF_config_{:s}_{:s}".format(ph[phind-1], my_name)}
						last_object_key += 1

						glmCaseDict[last_object_key] = {"object": "triplex_meter",
														"name": "{:s}_tm_{:s}_{:.0f}".format(my_name, ph[phind-1], jjj),
														"phases": "{:s}S".format(ph[phind-1]),
														"nominal_voltage": "120"}
						last_object_key += 1

						# skew each office zone identically per floor
						sk = round(2 * random.normalvariate(0, 1))
						skew_value = config_data["commercial_skew_std"] * sk
						if skew_value < -config_data["commercial_skew_max"]:
							skew_value = -config_data["commercial_skew_max"]
						elif skew_value > config_data["commercial_skew_max"]:
							skew_value = config_data["commercial_skew_max"]

						for zoneind in xrange(1, 6):
							total_depth = math.sqrt(floor_area_choose / (3. * 1.5))
							total_width = 1.5 * total_depth

							if phind < 3:
								exterior_ceiling_fraction = 0
							else:
								exterior_ceiling_fraction = 1

							if zoneind == 5:
								exterior_wall_fraction = 0
								w = total_depth - 30.
								d = total_width - 30.
								floor_area = w * d
								aspect_ratio = w / d
							else:
								window_wall_ratio = 0.33

								if zoneind == 1 or zoneind == 3:
									w = total_width - 15.
									d = 15.
									floor_area = w * d
									exterior_wall_fraction = w / (2. * (w + d))
									aspect_ratio = w / d
								else:
									w = total_depth - 15.
									d = 15.
									floor_area = w * d
									exterior_wall_fraction = w / (2. * (w + d))
									aspect_ratio = w / d

							if phind > 1:
								exterior_floor_fraction = 0
							else:
								exterior_floor_fraction = w / (2. * (w + d)) / (floor_area / (floor_area_choose / 3.))

							thermal_mass_per_floor_area = 3.9 * (0.5 + 1. * random.random())  # +/- 50#
							interior_exterior_wall_ratio = (floor_area * (2. - 1.) + 0. * 20.) / (no_of_stories * ceiling_height * 2. * (w + d)) - 1. + window_wall_ratio * exterior_wall_fraction
							no_of_doors = 0.1  # will round to zero

							init_temp = 68. + 4. * random.random()
							os_rand = config_data["over_sizing_factor"] * (0.8 + 0.4 * random.random())
							COP_A = config_data["cooling_COP"] * (0.8 + 0.4 * random.random())
							glmCaseDict[last_object_key] = {"object": "house",
															"name": "office{:s}_{:s}{:.0f}_zone{:.0f}".format(my_name, my_phases[phind-1], jjj, zoneind),
															"parent": "{:s}_tm_{:s}_{:.0f}".format(my_name, my_phases[phind-1], jjj),
															"groupid": "Commercial",
															"motor_model" : "BASIC",
															"schedule_skew": "{:.0f}".format(skew_value),
															"floor_area": "{:.0f}".format(floor_area),
															"design_internal_gains": "{:.0f}".format(int_gains * floor_area * 3.413),
															"number_of_doors": "{:.0f}".format(no_of_doors),
															"aspect_ratio": "{:.2f}".format(aspect_ratio),
															"total_thermal_mass_per_floor_area": "{:1.2f}".format(thermal_mass_per_floor_area),
															"interior_surface_heat_transfer_coeff": "{:1.2f}".format(surface_heat_trans_coeff),
															"interior_exterior_wall_ratio": "{:2.1f}".format(interior_exterior_wall_ratio),
															"exterior_floor_fraction": "{:.3f}".format(exterior_floor_fraction),
															"exterior_ceiling_fraction": "{:.3f}".format(exterior_ceiling_fraction),
															"Rwall": "{:2.1f}".format(Rwall),
															"Rroof": "{:2.1f}".format(Rroof),
															"Rfloor": "{:.2f}".format(Rfloor),
															"Rdoors": "{:2.1f}".format(Rdoors),
															"exterior_wall_fraction": "{:.2f}".format(exterior_wall_fraction),
															"glazing_layers": "{:s}".format(glazing_layers),
															"glass_type": "{:s}".format(glass_type),
															"glazing_treatment": "{:s}".format(glazing_treatment),
															"window_frame": "{:s}".format(window_frame),
															"airchange_per_hour": "{:.2f}".format(airchange_per_hour),
															"window_wall_ratio": "{:0.3f}".format(window_wall_ratio),
															"heating_system_type": "{:s}".format(heat_type),
															"auxiliary_system_type": "{:s}".format(aux_type),
															"fan_type": "{:s}".format(fan_type),
															"cooling_system_type": "{:s}".format(cool_type),
															"air_temperature": "{:.2f}".format(init_temp),
															"mass_temperature": "{:.2f}".format(init_temp),
															"over_sizing_factor": "{:.1f}".format(os_rand),
															"cooling_COP": "{:2.2f}".format(COP_A),
															"cooling_setpoint" : "office_cooling",
															"heating_setpoint" : "office_heating"}
							parent_house = glmCaseDict[last_object_key]

							# if we do not use schedules we will assume the initial temp is the setpoint
							if use_flags['use_schedules'] == 0:
								del glmCaseDict[last_object_key]['cooling_setpoint']
								del glmCaseDict[last_object_key]['heating_setpoint']

							last_object_key += 1

							# Need all of the "appliances"
							# Lights
							adj_lights = (0.9 + 0.1 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "lights_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, my_phases[phind-1], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Lights",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "1.0",
															"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
															"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
															"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
															"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
															"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
															"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
															"base_power": "office_lights*{:.2f}".format(adj_lights)}

							# if we do not use schedules we will assume adj_lights is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_lights)

							last_object_key += 1

							# Plugs
							adj_plugs = (0.9 + 0.2 * random.random()) * floor_area / 1000.  # randomize 20# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "plugs_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, my_phases[phind-1], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Plugs",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "1.0",
															"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
															"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
															"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
															"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
															"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
															"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
															"base_power": "office_plugs*{:.2f}".format(adj_plugs)}

							# if we do not use schedules we will assume adj_plugs is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_plugs)

							last_object_key += 1

							# Gas Waterheater
							adj_gas = (0.9 + 0.2 * random.random()) * floor_area / 1000. # randomize 20# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "wh_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, my_phases[phind-1], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Gas_waterheater",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "1.0",
															"power_fraction": "0.0",
															"impedance_fraction": "0.0",
															"current_fraction": "0.0",
															"power_pf": "1.0",
															"base_power": "office_gas*{:.2f}".format(adj_gas)}

							# if we do not use schedules we will assume adj_gas is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_gas)

							last_object_key += 1

							# Exterior Lighting
							adj_ext = (0.9 + 0.1 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "ext_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, my_phases[phind-1], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Exterior_lighting",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "0.0",
															"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
															"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
															"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
															"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
															"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
															"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
															"base_power": "office_exterior*{:.2f}".format(adj_ext)}

							# if we do not use schedules we will assume adj_ext is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_ext)

							last_object_key += 1

							# Occupancy
							adj_occ = (0.9 + 0.1 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "occ_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, my_phases[phind-1], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Occupancy",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "1.0",
															"power_fraction": "0.0",
															"impedance_fraction": "0.0",
															"current_fraction": "0.0",
															"power_pf": "1.0",
															"base_power": "office_occupancy*{:.2f}".format(adj_occ)}

							# if we do not use schedules we will assume adj_occ is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_occ)

							last_object_key += 1

						# end of house object
						# end # office zones (1-5)
						# end  #office floors (1-3)
						# end # total offices needed
						# print('finished iterating over number of offices')
			# Big box - has at least 2 phases and enough load for 6 zones
			#            *or* load is classified to be big boxes
			elif total_comm_houses > 6 and no_of_phases >= 2:
				no_of_bigboxes = int(round(total_comm_houses / 6.))

				if has_phase_A == 1:
					glmCaseDict[last_object_key] = {"object": "transformer_configuration",
													"name": "CTTF_config_A_{:s}".format(my_name),
													"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
													"install_type": "POLETOP",
													"impedance": "0.00033+0.0022j",
													"shunt_impedance": "10000+10000j",
													"primary_voltage": "{:.3f}".format(nom_volt),
													# might have to change to 7200/sqrt(3)
													"secondary_voltage": "{:.3f}".format(120.*math.sqrt(3)),
													"powerA_rating": "50 kVA"}
					last_object_key += 1

				if has_phase_B == 1:
					glmCaseDict[last_object_key] = {"object": "transformer_configuration",
													"name": "CTTF_config_B_{:s}".format(my_name),
													"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
													"install_type": "POLETOP",
													"impedance": "0.00033+0.0022j",
													"shunt_impedance": "10000+10000j",
													"primary_voltage": "{:.3f}".format(nom_volt),
													# might have to change to 7200/sqrt(3)
													"secondary_voltage": "{:.3f}".format(120.*math.sqrt(3)),
													"powerB_rating": "50 kVA"}
					last_object_key += 1

				if has_phase_C == 1:
					glmCaseDict[last_object_key] = {"object": "transformer_configuration",
													"name": "CTTF_config_C_{:s}".format(my_name),
													"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
													"install_type": "POLETOP",
													"impedance": "0.00033+0.0022j",
													"shunt_impedance": "10000+10000j",
													"primary_voltage": "{:.3f}".format(nom_volt),
													# might have to change to 7200/sqrt(3)
													"secondary_voltage": "{:.3f}".format(120.*math.sqrt(3)),
													"powerC_rating": "50 kVA"}
					last_object_key += 1
				# print('iterating over number of big boxes')
				for jjj in xrange(no_of_bigboxes):
					floor_area_choose = 20000. * (0.5 + 1. * random.random())  # +/- 50#
					ceiling_height = 14.
					airchange_per_hour = 1.5
					Rroof = 19.
					Rwall = 18.3
					Rfloor = 46.
					Rdoors = 3.
					glazing_layers = 'TWO'
					glass_type = 'GLASS'
					glazing_treatment = 'LOW_S'
					window_frame = 'NONE'
					int_gains = 3.6  # W/sf

					glmCaseDict[last_object_key] = {"object": "overhead_line",
													"from": "{:s}".format(my_parent),
													"to": "{:s}_bigbox_meter{:.0f}".format(my_name, jjj),
													"phases": "{:s}".format(commercial_dict[iii]["phases"]),
													"length": "50ft",
													"configuration": "line_configuration_comm{:s}".format(ph)}
					last_object_key += 1

					glmCaseDict[last_object_key] = {"object": "meter",
													"phases": "{:s}".format(commercial_dict[iii]["phases"]),
													"name": "{:s}_bigbox_meter{:.0f}".format(my_name, jjj),
													"groupid": "Commercial_Meter",
													"nominal_voltage": "{:f}".format(nom_volt)}

					last_object_key += 1

					# skew each big box zone identically
					sk = round(2 * random.normalvariate(0, 1))
					skew_value = config_data["commercial_skew_std"] * sk
					if skew_value < -config_data["commercial_skew_max"]:
						skew_value = -config_data["commercial_skew_max"]
					elif skew_value > config_data["commercial_skew_max"]:
						skew_value = config_data["commercial_skew_max"]

					total_index = 0

					for phind in xrange(no_of_phases):
						glmCaseDict[last_object_key] = {"object": "transformer",
														"name": "{:s}_CTTF_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"phases": "{:s}S".format(ph[phind]),
														"from": "{:s}_bigbox_meter{:.0f}".format(my_name, jjj),
														"to": "{:s}_tm_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"groupid": "Distribution_Trans",
														"configuration": "CTTF_config_{:s}_{:s}".format(ph[phind],
																										my_name)}
						last_object_key += 1

						glmCaseDict[last_object_key] = {"object": "triplex_meter",
														"name": "{:s}_tm_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"phases": "{:s}S".format(ph[phind]),
														"nominal_voltage": "120"}
						last_object_key += 1

						zones_per_phase = int(6. / no_of_phases)
						for zoneind in xrange(1,zones_per_phase+1):
							total_index += 1
							thermal_mass_per_floor_area = 3.9 * (0.8 + 0.4 * random.random())  # +/- 20#
							floor_area = floor_area_choose / 6.
							exterior_ceiling_fraction = 1.
							aspect_ratio = 1.28301275561855

							total_depth = math.sqrt(floor_area_choose / aspect_ratio)
							total_width = aspect_ratio * total_depth
							d = total_width / 3.
							w = total_depth / 2.
							if total_index == 2 or total_index == 5:
								exterior_wall_fraction = d / (2. * (d + w))
								exterior_floor_fraction = (0. + d) / (2. * (total_width + total_depth)) / (floor_area / floor_area_choose)
							else:
								exterior_wall_fraction = 0.5
								exterior_floor_fraction = (w + d) / (2. * (total_width + total_depth)) / (floor_area / floor_area_choose)

							if total_index == 2:
								window_wall_ratio = 0.76
							else:
								window_wall_ratio = 0.

							if total_index < 4:
								no_of_doors = 0.1  # this will round to 0
							elif total_index == 4 or total_index == 6:
								no_of_doors = 1.
							else:
								no_of_doors = 24.

							interior_exterior_wall_ratio = (floor_area * (2. - 1.) + no_of_doors * 20.) / (no_of_stories * ceiling_height * 2. * (w + d)) - 1. + window_wall_ratio * exterior_wall_fraction

							if total_index > 6:
								raise Exception('Something wrong in the indexing of the retail strip.')

							init_temp = 68. + 4. * random.random()
							os_rand = config_data["over_sizing_factor"] * (0.8 + 0.4 * random.random())
							COP_A = config_data["cooling_COP"] * (0.8 + 0.4 * random.random())
							glmCaseDict[last_object_key] = {"object": "house",
															"name": "bigbox{:s}_{:s}{:.0f}_zone{:.0f}".format(my_name, ph[phind], jjj, zoneind),
															"groupid": "Commercial",
															"motor_model": "BASIC",
															"schedule_skew": "{:.0f}".format(skew_value),
															"parent": "{:s}_tm_{:s}_{:.0f}".format(my_name, ph[phind],jjj),
															"floor_area": "{:.0f}".format(floor_area),
															"design_internal_gains": "{:.0f}".format(int_gains * floor_area * 3.413),
															"number_of_doors": "{:.0f}".format(no_of_doors),
															"aspect_ratio": "{:.2f}".format(aspect_ratio),
															"total_thermal_mass_per_floor_area": "{:1.2f}".format(thermal_mass_per_floor_area),
															"interior_surface_heat_transfer_coeff": "{:1.2f}".format(surface_heat_trans_coeff),
															"interior_exterior_wall_ratio": "{:2.1f}".format(interior_exterior_wall_ratio),
															"exterior_floor_fraction": "{:.3f}".format(exterior_floor_fraction),
															"exterior_ceiling_fraction": "{:.3f}".format(exterior_ceiling_fraction),
															"Rwall": "{:2.1f}".format(Rwall),
															"Rroof": "{:2.1f}".format(Rroof),
															"Rfloor": "{:.2f}".format(Rfloor),
															"Rdoors": "{:2.1f}".format(Rdoors),
															"exterior_wall_fraction": "{:.2f}".format(exterior_wall_fraction),
															"glazing_layers": "{:s}".format(glazing_layers),
															"glass_type": "{:s}".format(glass_type),
															"glazing_treatment": "{:s}".format(glazing_treatment),
															"window_frame": "{:s}".format(window_frame),
															"airchange_per_hour": "{:.2f}".format(airchange_per_hour),
															"window_wall_ratio": "{:0.3f}".format(window_wall_ratio),
															"heating_system_type": "{:s}".format(heat_type),
															"auxiliary_system_type": "{:s}".format(aux_type),
															"fan_type": "{:s}".format(fan_type),
															"cooling_system_type": "{:s}".format(cool_type),
															"air_temperature": "{:.2f}".format(init_temp),
															"mass_temperature": "{:.2f}".format(init_temp),
															"over_sizing_factor": "{:.1f}".format(os_rand),
															"cooling_COP": "{:2.2f}".format(COP_A),
															"cooling_setpoint": "bigbox_cooling",
															"heating_setpoint": "bigbox_heating"}
							parent_house = glmCaseDict[last_object_key]  # cache this for a second...

							# if we do not use schedules we will assume the initial temp is the setpoint
							if use_flags['use_schedules'] == 0:
								del glmCaseDict[last_object_key]['cooling_setpoint']
								del glmCaseDict[last_object_key]['heating_setpoint']

							last_object_key += 1

							# Need all of the "appliances"
							# Lights
							adj_lights = 1.2 * (0.9 + 0.1 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "lights_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, ph[phind], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Lights",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "1.0",
															"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
															"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
															"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
															"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
															"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
															"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
															"base_power": "bigbox_lights*{:.2f}".format(adj_lights)}

							# if we do not use schedules we will assume adj_lights is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_lights)

							last_object_key += 1

							# Plugs
							adj_plugs = (0.9 + 0.2 * random.random()) * floor_area / 1000.  # randomize 20# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "plugs_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, ph[phind], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Plugs",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "1.0",
															"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
															"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
															"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
															"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
															"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
															"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
															"base_power": "bigbox_plugs*{:.2f}".format(adj_plugs)}

							# if we do not use schedules we will assume adj_plugs is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_plugs)

							last_object_key += 1

							# Gas Waterheater
							adj_gas = (0.9 + 0.2 * random.random()) * floor_area / 1000.  # randomize 20# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "wh_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, ph[phind], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Gas_waterheater",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "1.0",
															"power_fraction": "0.0",
															"impedance_fraction": "0.0",
															"current_fraction": "0.0",
															"power_pf": "1.0",
															"base_power": "bigbox_gas*{:.2f}".format(adj_gas)}

							# if we do not use schedules we will assume adj_gas is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_gas)

							last_object_key += 1

							# Exterior Lighting
							adj_ext = (0.9 + 0.1 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "ext_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, ph[phind], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Exterior_lighting",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "0.0",
															"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
															"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
															"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
															"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
															"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
															"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
															"base_power": "bigbox_exterior*{:.2f}".format(adj_ext)}

							# if we do not use schedules we will assume adj_ext is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_ext)

							last_object_key += 1

							# Occupancy
							adj_occ = (0.9 + 0.1 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
							glmCaseDict[last_object_key] = {"object": "ZIPload",
															"name": "occ_{:s}_{:s}_{:.0f}_zone{:.0f}".format(my_name, ph[phind], jjj, zoneind),
															"parent": parent_house["name"],
															"groupid": "Occupancy",
															# "groupid": "Commercial_zip",
															"schedule_skew": "{:.0f}".format(skew_value),
															"heatgain_fraction": "1.0",
															"power_fraction": "0.0",
															"impedance_fraction": "0.0",
															"current_fraction": "0.0",
															"power_pf": "1.0",
															"base_power": "bigbox_occupancy*{:.2f}".format(adj_occ)}

							# if we do not use schedules we will assume adj_occ is the fixed value
							if use_flags['use_schedules'] == 0:
								glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_occ)

							last_object_key += 1

						# end #zone index
						# end #phase index
						# end #number of big boxes
						# print('finished iterating over number of big boxes')
			# Strip mall
			elif total_comm_houses > 0:  # unlike for big boxes and offices, if total house number = 0, just don't populate anything.
				no_of_strip = total_comm_houses
				strip_per_phase = int(math.ceil(no_of_strip / no_of_phases))

				if has_phase_A == 1:
					glmCaseDict[last_object_key] = {"object": "transformer_configuration",
													"name": "CTTF_config_A_{:s}".format(my_name),
													"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
													"install_type": "POLETOP",
													"impedance": "0.00033+0.0022j",
													"shunt_impedance": "100000+100000j",
													"primary_voltage": "{:.3f}".format(nom_volt),
													# might have to change to 7200/sqrt(3)
													"secondary_voltage": "{:.3f}".format(120.*math.sqrt(3)),
													"powerA_rating": "{:.0f} kVA".format(50. * strip_per_phase)}

					last_object_key += 1

				if has_phase_B == 1:
					glmCaseDict[last_object_key] = {"object": "transformer_configuration",
													"name": "CTTF_config_B_{:s}".format(my_name),
													"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
													"install_type": "POLETOP",
													"impedance": "0.00033+0.0022j",
													"shunt_impedance": "100000+100000j",
													"primary_voltage": "{:.3f}".format(nom_volt),
													# might have to change to 7200/sqrt(3)
													"secondary_voltage": "{:.3f}".format(120.*math.sqrt(3)),
													"powerB_rating": "{:.0f} kVA".format(50. * strip_per_phase)}

					last_object_key += 1

				if has_phase_C == 1:
					glmCaseDict[last_object_key] = {"object": "transformer_configuration",
													"name": "CTTF_config_C_{:s}".format(my_name),
													"connect_type": "SINGLE_PHASE_CENTER_TAPPED",
													"install_type": "POLETOP",
													"impedance": "0.00033+0.0022j",
													"shunt_impedance": "100000+100000j",
													"primary_voltage": "{:.3f}".format(nom_volt),
													# might have to change to 7200/sqrt(3)
													"secondary_voltage": "{:.3f}".format(120.*math.sqrt(3)),
													"powerC_rating": "{:.0f} kVA".format(50. * strip_per_phase)}

					last_object_key += 1

				glmCaseDict[last_object_key] = {"object": "overhead_line",
												"from": "{:s}".format(my_parent),
												"to": "{:s}_strip_node".format(my_name),
												"phases": "{:s}".format(commercial_dict[iii]["phases"]),
												"length": "50ft",
												"configuration": "line_configuration_comm{:s}".format(ph)}
				last_object_key += 1

				glmCaseDict[last_object_key] = {"object": "node",
												"phases": "{:s}".format(commercial_dict[iii]["phases"]),
												"name": "{:s}_strip_node".format(my_name),
												"nominal_voltage": "{:f}".format(nom_volt)}
				last_object_key += 1

				# print('iterating over number of stripmalls')
				for phind in xrange(no_of_phases):
					floor_area_choose = 2400. * (0.7 + 0.6 * random.random())  # +/- 30#
					# ceiling_height = 12
					airchange_per_hour = 1.76
					Rroof = 19.
					Rwall = 18.3
					Rfloor = 40.
					Rdoors = 3.
					glazing_layers = 'TWO'
					glass_type = 'GLASS'
					glazing_treatment = 'LOW_S'
					window_frame = 'NONE'
					int_gains = 3.6  # W/sf
					thermal_mass_per_floor_area = 3.9 * (0.5 + 1. * random.random())  # +/- 50#
					exterior_ceiling_fraction = 1.

					for jjj in xrange(1, strip_per_phase+1):
						# skew each office zone identically per floor
						sk = round(2 * random.normalvariate(0, 1))
						skew_value = config_data["commercial_skew_std"] * sk
						if skew_value < -config_data["commercial_skew_max"]:
							skew_value = -config_data["commercial_skew_max"]
						elif skew_value > config_data["commercial_skew_max"]:
							skew_value = config_data["commercial_skew_max"]

						if jjj == 1 or jjj == (math.floor(strip_per_phase / 2.) + 1.):
							floor_area = floor_area_choose
							aspect_ratio = 1.5
							window_wall_ratio = 0.05

							# if (j == jjj):
							#    exterior_wall_fraction = 0.7;
							#    exterior_floor_fraction = 1.4;
							# else:
							exterior_wall_fraction = 0.4
							exterior_floor_fraction = 0.8

							interior_exterior_wall_ratio = -0.05
						else:
							floor_area = floor_area_choose / 2.
							aspect_ratio = 3.0
							window_wall_ratio = 0.03

							if jjj == strip_per_phase:
								exterior_wall_fraction = 0.63
								exterior_floor_fraction = 2.
							else:
								exterior_wall_fraction = 0.25
								exterior_floor_fraction = 0.8

							interior_exterior_wall_ratio = -0.40

						no_of_doors = 1

						glmCaseDict[last_object_key] = {"object": "transformer",
														"name": "{:s}_CTTF_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"phases": "{:s}S".format(ph[phind]),
														"from": "{:s}_strip_node".format(my_name),
														"to": "{:s}_tn_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"groupid": "Distribution_Trans'",
														"configuration": "CTTF_config_{:s}_{:s}".format(ph[phind], my_name)}
						last_object_key += 1

						glmCaseDict[last_object_key] = {"object": "triplex_node",
														"name": "{:s}_tn_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"phases": "{:s}S".format(ph[phind]),
														"nominal_voltage": "120"}
						last_object_key += 1

						glmCaseDict[last_object_key] = {"object": "triplex_meter",
														"parent": "{:s}_tn_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"name": "{:s}_tm_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"phases": "{:s}S".format(ph[phind]),
														"groupid": "Commercial_Meter",
														# was 'real(my_var), imag(my_var), but it's an int above
														"nominal_voltage": "120"}
						last_object_key += 1

						init_temp = 68. + 4. * random.random()
						os_rand = config_data["over_sizing_factor"] * (0.8 + 0.4 * random.random())
						COP_A = config_data["cooling_COP"] * (0.8 + 0.4 * random.random())
						glmCaseDict[last_object_key] = {"object": "house",
														"name": "stripmall{:s}_{:s}{:.0f}".format(my_name, ph[phind], jjj),
														"groupid": "Commercial",
														"motor_model": "BASIC",
														"schedule_skew": "{:.0f}".format(skew_value),
														"parent": "{:s}_tm_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"floor_area": "{:.0f}".format(floor_area),
														"design_internal_gains": "{:.0f}".format(int_gains * floor_area * 3.413),
														"number_of_doors": "{:.0f}".format(no_of_doors),
														"aspect_ratio": "{:.2f}".format(aspect_ratio),
														"total_thermal_mass_per_floor_area": "{:1.2f}".format(thermal_mass_per_floor_area),
														"interior_surface_heat_transfer_coeff": "{:1.2f}".format(surface_heat_trans_coeff),
														"interior_exterior_wall_ratio": "{:2.1f}".format(interior_exterior_wall_ratio),
														"exterior_floor_fraction": "{:.3f}".format(exterior_floor_fraction),
														"exterior_ceiling_fraction": "{:.3f}".format(exterior_ceiling_fraction),
														"Rwall": "{:2.1f}".format(Rwall),
														"Rroof": "{:2.1f}".format(Rroof),
														"Rfloor": "{:.2f}".format(Rfloor),
														"Rdoors": "{:2.1f}".format(Rdoors),
														"exterior_wall_fraction": "{:.2f}".format(exterior_wall_fraction),
														"glazing_layers": "{:s}".format(glazing_layers),
														"glass_type": "{:s}".format(glass_type),
														"glazing_treatment": "{:s}".format(glazing_treatment),
														"window_frame": "{:s}".format(window_frame),
														"airchange_per_hour": "{:.2f}".format(airchange_per_hour),
														"window_wall_ratio": "{:0.3f}".format(window_wall_ratio),
														"heating_system_type": "{:s}".format(heat_type),
														"auxiliary_system_type": "{:s}".format(aux_type),
														"fan_type": "{:s}".format(fan_type),
														"cooling_system_type": "{:s}".format(cool_type),
														"air_temperature": "{:.2f}".format(init_temp),
														"mass_temperature": "{:.2f}".format(init_temp),
														"over_sizing_factor": "{:.1f}".format(os_rand),
														"cooling_COP": "{:2.2f}".format(COP_A),
														"cooling_setpoint": "stripmall_cooling",
														"heating_setpoint": "stripmall_heating"}
						parent_house = glmCaseDict[last_object_key]

						# if we do not use schedules we will assume the initial temp is the setpoint
						if use_flags['use_schedules'] == 0:
							del glmCaseDict[last_object_key]['cooling_setpoint']
							del glmCaseDict[last_object_key]['heating_setpoint']

						last_object_key += 1

						# Need all of the "appliances"
						# Lights
						adj_lights = (0.8 + 0.4 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
						glmCaseDict[last_object_key] = {"object": "ZIPload",
														"name": "lights_{:s}_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"parent": parent_house["name"],
														"groupid": "Lights",
														# "groupid": "Commercial_zip",
														"schedule_skew": "{:.0f}".format(skew_value),
														"heatgain_fraction": "1.0",
														"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
														"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
														"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
														"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
														"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
														"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
														"base_power": "stripmall_lights*{:.2f}".format(adj_lights)}

						# if we do not use schedules we will assume adj_lights is the fixed value
						if use_flags['use_schedules'] == 0:
							glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_lights)

						last_object_key += 1

						# Plugs
						adj_plugs = (0.8 + 0.4 * random.random()) * floor_area / 1000.  # randomize 20# then convert W/sf -> kW
						glmCaseDict[last_object_key] = {"object": "ZIPload",
														"name": "plugs_{:s}_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"parent": parent_house["name"],
														"groupid": "Plugs",
														# "groupid": "Commercial_zip",
														"schedule_skew": "{:.0f}".format(skew_value),
														"heatgain_fraction": "1.0",
														"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
														"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
														"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
														"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
														"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
														"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
														"base_power": "stripmall_plugs*{:.2f}".format(adj_plugs)}

						# if we do not use schedules we will assume adj_plugs is the fixed value
						if use_flags['use_schedules'] == 0:
							glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_plugs)

						last_object_key += 1

						# Gas Waterheater
						adj_gas = (0.8 + 0.4 * random.random()) * floor_area / 1000.  # randomize 20# then convert W/sf -> kW
						glmCaseDict[last_object_key] = {"object": "ZIPload",
														"name": "wh_{:s}_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"parent": parent_house["name"],
														"groupid": "Gas_waterheater",
														# "groupid": "Commercial_zip",
														"schedule_skew": "{:.0f}".format(skew_value),
														"heatgain_fraction": "1.0",
														"power_fraction": "0.0",
														"impedance_fraction": "0.0",
														"current_fraction": "0.0",
														"power_pf": "1.0",
														"base_power": "stripmall_gas*{:.2f}".format(adj_gas)}

						# if we do not use schedules we will assume adj_gas is the fixed value
						if use_flags['use_schedules'] == 0:
							glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_gas)

						last_object_key += 1

						# Exterior Lighting
						adj_ext = (0.8 + 0.4 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
						glmCaseDict[last_object_key] = {"object": "ZIPload",
														"name": "ext_{:s}_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"parent": parent_house["name"],
														"groupid": "Exterior_lighting",
														# "groupid": "Commercial_zip",
														"schedule_skew": "{:.0f}".format(skew_value),
														"heatgain_fraction": "0.0",
														"power_fraction": "{:.2f}".format(config_data["c_pfrac"]),
														"impedance_fraction": "{:.2f}".format(config_data["c_zfrac"]),
														"current_fraction": "{:.2f}".format(config_data["c_ifrac"]),
														"power_pf": "{:.2f}".format(config_data["c_p_pf"]),
														"current_pf": "{:.2f}".format(config_data["c_i_pf"]),
														"impedance_pf": "{:.2f}".format(config_data["c_z_pf"]),
														"base_power": "stripmall_exterior*{:.2f}".format(adj_ext)}

						# if we do not use schedules we will assume adj_ext is the fixed value
						if use_flags['use_schedules'] == 0:
							glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_ext)

						last_object_key += 1

						# Occupancy
						adj_occ = (0.8 + 0.4 * random.random()) * floor_area / 1000.  # randomize 10# then convert W/sf -> kW
						glmCaseDict[last_object_key] = {"object": "ZIPload",
														"name": "occ_{:s}_{:s}_{:.0f}".format(my_name, ph[phind], jjj),
														"parent": parent_house["name"],
														"groupid": "Occupancy",
														# "groupid": "Commercial_zip",
														"schedule_skew": "{:.0f}".format(skew_value),
														"heatgain_fraction": "1.0",
														"power_fraction": "0.0",
														"impedance_fraction": "0.0",
														"current_fraction": "0.0",
														"power_pf": "1.0",
														"base_power": "stripmall_occupancy*{:.2f}".format(adj_occ)}

						# if we do not use schedules we will assume adj_occ is the fixed value
						if use_flags['use_schedules'] == 0:
							glmCaseDict[last_object_key]['base_power'] = "{:.2f}".format(adj_occ)

						last_object_key += 1
					# end
					# end #number of strip zones
					# end #phase index
					# end #commercial selection
					# print('finished iterating over number of stripmalls')
			# add the "street light" loads
			# parent them to the METER as opposed to the node, so we don't
			# have any "grandchildren"
			elif total_comm_houses == 0 and sum(commercial_dict[iii]['load']) > 0:
				# print('writing street_light')
				glmCaseDict[last_object_key] = {"object": "load",
												"parent": "{:s}".format(my_parent),
												"name": "str_light_{:s}{:s}".format(ph, commercial_dict[iii]['name']),
												"nominal_voltage": "{:.2f}".format(nom_volt),
												"phases": "{:s}".format(ph)
												}
				if has_phase_A == 1 and commercial_dict[iii]['load'][0] > 0:
					if use_flags['use_schedules'] == 1:
						glmCaseDict[last_object_key]["base_power_A"] = "street_lighting*{:f}".format(config_data["light_scalar_comm"] * commercial_dict[iii]['load'][0])
					else:
						glmCaseDict[last_object_key]["base_power_A"] = "{:f}".format(config_data["light_scalar_comm"] * commercial_dict[iii]['load'][0])
					glmCaseDict[last_object_key]["power_pf_A"] = "{:f}".format(config_data["c_p_pf"])
					glmCaseDict[last_object_key]["current_pf_A"] = "{:f}".format(config_data["c_i_pf"])
					glmCaseDict[last_object_key]["impedance_pf_A"] = "{:f}".format(config_data["c_z_pf"])
					glmCaseDict[last_object_key]["power_fraction_A"] = "{:f}".format(config_data["c_pfrac"])
					glmCaseDict[last_object_key]["current_fraction_A"] = "{:f}".format(config_data["c_ifrac"])
					glmCaseDict[last_object_key]["impedance_fraction_A"] = "{:f}".format(config_data["c_zfrac"])

				if has_phase_B == 1 and commercial_dict[iii]['load'][1] > 0:
					if use_flags['use_schedules'] == 1:
						glmCaseDict[last_object_key]["base_power_B"] = "street_lighting*{:f}".format(config_data["light_scalar_comm"] * commercial_dict[iii]['load'][1])
					else:
						glmCaseDict[last_object_key]["base_power_B"] = "{:f}".format(config_data["light_scalar_comm"] * commercial_dict[iii]['load'][1])
					glmCaseDict[last_object_key]["power_pf_B"] = "{:f}".format(config_data["c_p_pf"])
					glmCaseDict[last_object_key]["current_pf_B"] = "{:f}".format(config_data["c_i_pf"])
					glmCaseDict[last_object_key]["impedance_pf_B"] = "{:f}".format(config_data["c_z_pf"])
					glmCaseDict[last_object_key]["power_fraction_B"] = "{:f}".format(config_data["c_pfrac"])
					glmCaseDict[last_object_key]["current_fraction_B"] = "{:f}".format(config_data["c_ifrac"])
					glmCaseDict[last_object_key]["impedance_fraction_B"] = "{:f}".format(config_data["c_zfrac"])

				if has_phase_C == 1 and commercial_dict[iii]['load'][2] > 0:
					if use_flags['use_schedules'] == 1:
						glmCaseDict[last_object_key]["base_power_C"] = "street_lighting*{:f}".format(config_data["light_scalar_comm"] * commercial_dict[iii]['load'][2])
					else:
						glmCaseDict[last_object_key]["base_power_C"] = "{:f}".format(config_data["light_scalar_comm"] * commercial_dict[iii]['load'][2])
					glmCaseDict[last_object_key]["power_pf_C"] = "{:f}".format(config_data["c_p_pf"])
					glmCaseDict[last_object_key]["current_pf_C"] = "{:f}".format(config_data["c_i_pf"])
					glmCaseDict[last_object_key]["impedance_pf_C"] = "{:f}".format(config_data["c_z_pf"])
					glmCaseDict[last_object_key]["power_fraction_C"] = "{:f}".format(config_data["c_pfrac"])
					glmCaseDict[last_object_key]["current_fraction_C"] = "{:f}".format(config_data["c_ifrac"])
					glmCaseDict[last_object_key]["impedance_fraction_C"] = "{:f}".format(config_data["c_zfrac"])

				last_object_key += 1
			# end 'for each load'

	return glmCaseDict, last_object_key


def add_normalized_commercial_ziploads(loadshape_dict, commercial_dict, config_data, last_key):
	"""
	This fucntion appends commercial zip loads to a feeder based on existing loads

	Inputs
		loadshape_dict - dictionary containing the full feeder
		commercial_dict - dictionary that contains information about commercial loads spots
		last_key - Last object key
		config_data - dictionary that contains the configurations of the feeder

	Outputs
		loadshape_dict -  dictionary containing the full feeder
		last_key - Last object key
	"""

	for x in commercial_dict.keys():
		load_name = commercial_dict[x]['name']
		load_parent = commercial_dict[x].get('parent', 'None')
		phases = commercial_dict[x]['phases']
		nom_volt = commercial_dict[x]['nom_volt']
		bp_A = commercial_dict[x]['load'][0] * config_data['normalized_loadshape_scalar']
		bp_B = commercial_dict[x]['load'][1] * config_data['normalized_loadshape_scalar']
		bp_C = commercial_dict[x]['load'][2] * config_data['normalized_loadshape_scalar']

		loadshape_dict[last_key] = {'object': 'load',
									'name': '{:s}_loadshape'.format(load_name),
									'phases': phases,
									'nominal_voltage': nom_volt}
		if load_parent != 'None':
			loadshape_dict[last_key]['parent'] = load_parent
		else:
			loadshape_dict[last_key]['parent'] = load_parent

		if 'A' in phases and bp_A > 0.0:
			loadshape_dict[last_key]['base_power_A'] = 'norm_feeder_loadshape.value*{:f}'.format(bp_A)
			loadshape_dict[last_key]['power_pf_A'] = '{:f}'.format(config_data['c_p_pf'])
			loadshape_dict[last_key]['current_pf_A'] = '{:f}'.format(config_data['c_i_pf'])
			loadshape_dict[last_key]['impedance_pf_A'] = '{:f}'.format(config_data['c_z_pf'])
			loadshape_dict[last_key]['power_fraction_A'] = '{:f}'.format(config_data['c_pfrac'])
			loadshape_dict[last_key]['current_fraction_A'] = '{:f}'.format(config_data['c_ifrac'])
			loadshape_dict[last_key]['impedance_fraction_A'] = '{:f}'.format(config_data['c_zfrac'])

		if 'B' in phases and bp_B > 0.0:
			loadshape_dict[last_key]['base_power_B'] = 'norm_feeder_loadshape.value*{:f}'.format(bp_B)
			loadshape_dict[last_key]['power_pf_B'] = '{:f}'.format(config_data['c_p_pf'])
			loadshape_dict[last_key]['current_pf_B'] = '{:f}'.format(config_data['c_i_pf'])
			loadshape_dict[last_key]['impedance_pf_B'] = '{:f}'.format(config_data['c_z_pf'])
			loadshape_dict[last_key]['power_fraction_B'] = '{:f}'.format(config_data['c_pfrac'])
			loadshape_dict[last_key]['current_fraction_B'] = '{:f}'.format(config_data['c_ifrac'])
			loadshape_dict[last_key]['impedance_fraction_B'] = '{:f}'.format(config_data['c_zfrac'])

		if 'C' in phases and bp_C > 0.0:
			loadshape_dict[last_key]['base_power_C'] = 'norm_feeder_loadshape.value*{:f}'.format(bp_C)
			loadshape_dict[last_key]['power_pf_C'] = '{:f}'.format(config_data['c_p_pf'])
			loadshape_dict[last_key]['current_pf_C'] = '{:f}'.format(config_data['c_i_pf'])
			loadshape_dict[last_key]['impedance_pf_C'] = '{:f}'.format(config_data['c_z_pf'])
			loadshape_dict[last_key]['power_fraction_C'] = '{:f}'.format(config_data['c_pfrac'])
			loadshape_dict[last_key]['current_fraction_C'] = '{:f}'.format(config_data['c_ifrac'])
			loadshape_dict[last_key]['impedance_fraction_C'] = '{:f}'.format(config_data['c_zfrac'])

		last_key += last_key

	return loadshape_dict, last_key


def add_residential_EVs(glmCaseDict, config_file, use_flags, last_key=0):
	"""
	This fucntion appends residential EVs to a feeder

	Inputs
		glmCaseDict - dictionary containing the full feeder
		config_file - dictionary that contains the configurations of the feeder
		use_flags - dictionary that contains the use flags
		file_path - file path for the experiment. Used to get the EV trip log
		last_key - Last object key


	Outputs
		glmCaseDict -  dictionary containing the full feeder
	"""

	# Initialize psuedo-random seed
	# random.seed(4)

	if use_flags['use_EVs'] != 0 and use_flags['use_homes'] != 0:

		# Check if last_key is already in glm dictionary
		def unused_key(key):
			if key in glmCaseDict:
				while key in glmCaseDict:
					key += 1
			return key

		# let's determine the next available key
		last_key = unused_key(last_key)

		# determine the total number of homes in the feeder
		control_dict = []
		for x in glmCaseDict:
			if 'object' in glmCaseDict[x] and glmCaseDict[x]['object'] == 'house' and glmCaseDict[x]['groupid'] == 'Residential':
				control_dict.append(glmCaseDict[x]['name'])

		# determine how many EVs to implement
		total_num_EVs = round(float(config_file["perc_EV"])*len(control_dict))

		# adjust the house list with the appropiate number to be implemented at random
		control_dict = random.sample(control_dict, int(total_num_EVs))

		for controlObject in control_dict:
			# random variables for each EV
			mileageClassification = 50 + random.randint(0, 200)  # between 50-250
			mileageEfficiency = 3.35 + 0.5 * random.random()  # between 3.35-3.85
			maximumChargeRate = math.floor(1500 + 200 * random.random())  # between 1500-1700
			chargingEfficiency = 0.85 + 0.1 * random.random()  # between 0.85-0.95
			vehicleIndex = random.randint(1, 35200)  # we have 35200 entries in the trip log

			# adding the EV charger
			glmCaseDict[last_key] = {'object': 'evcharger_det',
									 'parent': '{:s}'.format(controlObject),
									 'name': '{:s}_ev_charger'.format(controlObject),
									 'variation_mean' : '0.0',
									 'variation_std_dev' : '0.0',
									 'variation_trip_mean' : '0.0',
									 'variation_trip_std_dev' : '0.0',
									 'mileage_classification' : '{:.2f}'.format(mileageClassification),
									 'work_charging_available' : 'false',
									 'mileage_efficiency' : '{:.2f}'.format(mileageEfficiency),
									 'maximum_charge_rate' : '{:.2f}'.format(maximumChargeRate),
									 'charging_efficiency' : '{:.2f}'.format(chargingEfficiency),
									 'data_file' : '{:s}/schedules/EV_trips.csv'.format(config_file['includePath']),
									 'vehicle_index' : '{:d}'.format(vehicleIndex)}

			last_key = unused_key(last_key)

	else:
		if use_flags['use_EVs'] != 0:
			print "You asked for EVs but you did not implement residential houses so this setting was ignored"

	return glmCaseDict

def add_residential_storage(glmCaseDict, config_file, use_flags, last_key=0):
	"""
	This fucntion appends residential battery storage to a feeder

	Inputs
		glmCaseDict - dictionary containing the full feeder
		config_file - dictionary that contains the configurations of the feeder
		use_flags - dictionary that contains the use flags
		file_path - file path for the experiment. Used to get the EV trip log
		last_key - Last object key


	Outputs
		glmCaseDict -  dictionary containing the full feeder
	"""
	if use_flags['use_residential_storage'] != 0 and use_flags['use_homes'] != 0:

		# Check if last_key is already in glm dictionary
		def unused_key(key):
			if key in glmCaseDict:
				while key in glmCaseDict:
					key += 1
			return key

		# let's determine the next available key
		last_key = unused_key(last_key)

		# determine the total number of homes in the feeder
		control_dict = []
		for x in glmCaseDict:
			if 'object' in glmCaseDict[x] and glmCaseDict[x]['object'] == 'house' and glmCaseDict[x]['groupid'] == 'Residential':
				control_dict.append([glmCaseDict[x]['name'],glmCaseDict[x]['parent']])

		# determine how many EVs to implement
		total_num_EBs = round(float(config_file["perc_EB"])*len(control_dict))

		# adjust the house list with the appropiate number to be implemented at random
		control_dict = random.sample(control_dict, int(total_num_EBs))

		for controlObject in control_dict:
			# random variables for each EB

			batterySOC = 0.7 + 0.2 * random.random() 

			# adding the external controller
			glmCaseDict[last_key] = {'object': 'inverter',
									'parent': '{:s}'.format(controlObject[1]),
									'name': '{:s}_eb_inveter'.format(controlObject[0]),
								    'inverter_type': 'FOUR_QUADRANT', # Must be in FOUR_QUADRANT to use the load following control scheme.
								    'generator_status': 'ONLINE', # set the status of the inverter to online
								    'charge_lockout_time': '30', # lockout time for charging
								    'discharge_lockout_time': '30', # lockout time for dischargeing
								    'four_quadrant_control_mode': 'LOAD_FOLLOWING', # The only mode that works with the battery object.
								    'sense_object': '{:s}'.format(controlObject[1]), # the sense_object must be a meter, triplex_meter, or transformer.
								    'rated_power': '3000.0', # The per phase power output rating of the inverter in VA.
								    'inverter_efficiency': '0.95',
								    'charge_on_threshold': '1.3 kW', # when the load at the sense_object drops below this value the inverter starts to charge the battery.
								    'charge_off_threshold': '2.7 kW', # when the battery is charging and the load at the sense_object rises above this value the inverter stops charging the battery.
								    'discharge_off_threshold': '3.0 kW', # when the battery is discharging and the load at the sense_object drops below this value the inverter stops discharging the battery.
								    'discharge_on_threshold': '4.5 kW', # when the load at the sense_object rises above this value the inverter starts to discharge the battery.
								    'max_discharge_rate': '1 kW', # The maximum power output to demand from the battery when discharging.
								    'max_charge_rate': '1 kW'} # The maximum power input to the battery when charging.


			last_key = unused_key(last_key)
			
			glmCaseDict[last_key] = {'object': 'battery',
									 'groupid': 'residential_storage',
									 'parent': '{:s}_eb_inveter'.format(controlObject[0]),
									 'name': '{:s}_eb_battery'.format(controlObject[0]),
									 'use_internal_battery_model': 'true',
									 'battery_type': 'LI_ION',
									 'state_of_charge': '{:.2f}'.format(batterySOC),
									 'generator_mode': 'SUPPLY_DRIVEN',
									 'rfb_size': 'HOUSEHOLD'}

			last_key = unused_key(last_key)
	else:
		if use_flags['use_residential_storage'] != 0:
			print "You asked for residential battery storage, but you did not implement residential houses so this setting was ignored"

	return glmCaseDict


def add_utility_storage(glmCaseDict, config_file, use_flags, peakLoad, last_key=0):
	"""
	This fucntion appends utility battery storage to a feeder

	Inputs
		glmCaseDict - dictionary containing the full feeder
		config_file - dictionary that contains the configurations of the feeder
		use_flags - dictionary that contains the use flags
		file_path - file path for the experiment. Used to get the EV trip log
		last_key - Last object key


	Outputs
		glmCaseDict -  dictionary containing the full feeder
	"""

	# Check if last_key is already in glm dictionary
	def unused_key(key):
		if key in glmCaseDict:
			while key in glmCaseDict:
				key += 1
		return key

	# let's determine the next available key
	last_key = unused_key(last_key)

	foundNode = False
	# determine the total number of homes in the feeder
	for x in glmCaseDict:
		if 'object' in glmCaseDict[x] and glmCaseDict[x]['object'] == 'transformer' and glmCaseDict[x]['name'] == 'substation_transformer':
			foundNode = True
			UEBParent = glmCaseDict[x]['to']
			break

	if foundNode:
		for count in xrange(0,int(config_file["utility_EB"])): # we have to create the correct amount of batteries
			# random variables for each EB

			batterySOC = 0.7 + 0.2 * random.random() 

			charge_on_threshold = (peakLoad*1000)*0.65
			charge_off_threshold = (peakLoad*1000)*0.73
			discharge_off_threshold = (peakLoad*1000)*0.77
			discharge_on_threshold = (peakLoad*1000)*0.85

			# adding the external controller
			glmCaseDict[last_key] = {'object': 'inverter',
									'parent': '{:s}'.format(UEBParent),
									'name': 'utility_eb_inveter_{:d}'.format(count),
								    'inverter_type': 'FOUR_QUADRANT', # Must be in FOUR_QUADRANT to use the load following control scheme.
								    'generator_status': 'ONLINE', # set the status of the inverter to online
								    'charge_lockout_time': '30', # lockout time for charging
								    'discharge_lockout_time': '30', # lockout time for dischargeing
								    'four_quadrant_control_mode': 'LOAD_FOLLOWING', # The only mode that works with the battery object.
								    'sense_object': '{:s}'.format(UEBParent), # the sense_object must be a meter, triplex_meter, or transformer.
								    'rated_power': '240000.0', # The per phase power output rating of the inverter in VA.
								    'inverter_efficiency': '0.95',
								    'charge_on_threshold': '{:.2f} kW'.format(charge_on_threshold), # when the load at the sense_object drops below this value the inverter starts to charge the battery.
								    'charge_off_threshold': '{:.2f} kW'.format(charge_off_threshold), # when the battery is charging and the load at the sense_object rises above this value the inverter stops charging the battery.
								    'discharge_off_threshold': '{:.2f} kW'.format(discharge_off_threshold), # when the battery is discharging and the load at the sense_object drops below this value the inverter stops discharging the battery.
								    'discharge_on_threshold': '{:.2f} kW'.format(discharge_on_threshold), # when the load at the sense_object rises above this value the inverter starts to discharge the battery.
								    'max_discharge_rate': '200 kW', # The maximum power output to demand from the battery when discharging.
								    'max_charge_rate': '200 kW'} # The maximum power input to the battery when charging.


			last_key = unused_key(last_key)
			
			glmCaseDict[last_key] = {'object': 'battery',
									 'groupid': 'utility_storage',
									 'parent': 'utility_eb_inveter_{:d}'.format(count),
									 'name': 'utility_eb_battery_{:d}'.format(count),
									 'use_internal_battery_model': 'true',
									 'battery_type': 'LI_ION',
									 'state_of_charge': '{:.2f}'.format(batterySOC),
									 'generator_mode': 'SUPPLY_DRIVEN',
									 'rfb_size': 'LARGE'}

			last_key = unused_key(last_key)

	else:
		print "Unable to find the nodes to connect the utility scale battery storage"
	
	return glmCaseDict

if __name__ == '__main__':
	pass

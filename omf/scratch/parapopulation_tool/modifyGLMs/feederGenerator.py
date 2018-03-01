"""
This file takes in the original GLM dictionary and output the modified GLM dictionary

	modifyFeeder(glmDict, config_data, use_flags, randomSeed=2)
		This fucntion modifies the feeder based on feeder configuration and use flags

	addCCSISubstation(glmDict, config_data, substationkV):
		This function adds a specific substation that is needed for the co-simulation studies


Modified December 20, 2016 by Jacob Hansen (jacob.hansen@pnnl.gov)
Created April 13, 2013 by Andy Fisher (andy.fisher@pnnl.gov)

Copyright (c) 2013 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
Government, including the right to distribute to other Government contractors.
"""

from __future__ import division
import loads
import copy, random, math, time

def modifyFeeder(glmDict, config_data, use_flags, randomSeed=2):
	"""
	This fucntion modifies the feeder based on feeder configuration and use flags

	Inputs
		glmDict - dictionary containing the full feeder unmodified
		configuration_file - dictionary that contains the configurations of the feeder
		use_flags - dictionary that contains flags for what technology case to tack on to the GridLAB-D model
		randomSeed - initialize psuedo-random seed (defaults to 2)
	Outputs
		glmCaseDict -  dictionary containing the full feeder modified
	"""

	# Initialize psuedo-random seed
	random.seed(randomSeed)

	# Create new modified case dictionary
	glmCaseDict = {}
	last_key = len(glmCaseDict)

	# Create clock dictionary
	glmCaseDict[last_key] = {'clock' : '',
							 'timezone' : '{:s}'.format(config_data['timezone']),
							 'starttime' : "'{:s}'".format(config_data['startdate']),
							 'stoptime' : "'{:s}'".format(config_data['stopdate'])}
	last_key += 1

	# Create dictionaries of preprocessor directives
	if use_flags['use_schedules'] == 1:
		if use_flags['use_homes'] != 0:
			glmCaseDict[last_key] = {'#include' : '"{:s}/schedules/appliance_schedules.glm"'.format(config_data['includePath'])}
			last_key += 1
			glmCaseDict[last_key] = {'#include' : '"{:s}/schedules/water_and_setpoint_schedule_v5.glm"'.format(config_data['includePath'])}
			last_key += 1
			# glmCaseDict[last_key] = {'#include': '"include/schedules/waterheater_energy_schedule.glm"'}
			# last_key += 1

		if use_flags['use_commercial'] == 1:
			glmCaseDict[last_key] = {'#include': '"{:s}/schedules/commercial_schedules.glm"'.format(config_data['includePath'])}
			last_key += 1

	glmCaseDict[last_key] = {'#define': 'stylesheet=http://gridlab-d.svn.sourceforge.net/viewvc/gridlab-d/trunk/core/gridlabd-2_0'}
	last_key += 1

	glmCaseDict[last_key] = {'#set': 'minimum_timestep={:f}'.format(config_data['minimum_timestep'])}
	last_key += 1

	glmCaseDict[last_key] = {'#set': 'profiler=1'}
	last_key += 1

	glmCaseDict[last_key] = {'#set': 'relax_naming_rules=1'}
	last_key += 1

	glmCaseDict[last_key] = {'#set': 'randomseed=10'}
	last_key += 1

	glmCaseDict[last_key] = {'#set': 'suppress_repeat_messages=1'}
	last_key += 1

	# Create dictionaries of modules to be used from the case_flag
	glmCaseDict[last_key] = {'module': 'market'}
	last_key += 1

	glmCaseDict[last_key] = {'module': 'tape'}
	last_key += 1

	glmCaseDict[last_key] = {'module': 'climate'}
	last_key += 1

	glmCaseDict[last_key] = {'module': 'residential',
							 'implicit_enduses': 'NONE'}
	last_key += 1

	glmCaseDict[last_key] = {'module': 'powerflow',
							 'solver_method': 'FBS',
							 'default_maximum_voltage_error': '1e-4',
							 #'solver_method': 'NR',
							 # 'NR_iteration_limit': '100'
							 'line_limits' : 'FALSE',}
	last_key += 1

	if use_flags["useFNCS"] == 1:
		glmCaseDict[last_key] = {'module': 'connection',
								 'security': 'STANDARD',
								 'lockout': '1 min'}

		last_key += 1

	if use_flags["use_residential_storage"] == 1 or use_flags["use_utility_storage"] == 1:
		glmCaseDict[last_key] = {'module': 'generators'}

		last_key += 1		
	# # added load shape to the class water heater
	# glmCaseDict[last_key] = {'class': 'waterheater',
	# 						 'loadshape': 'myshape'}
	# last_key += 1

	if use_flags['use_homes'] == 2 or use_flags['use_commercial'] == 2:
		# Add the class player dictionary to glmCaseDict
		glmCaseDict[last_key] = {'class': 'player',
								 'double': 'value'}
		last_key += 1

		glmCaseDict[last_key] = {'object': 'player',
								 'name': 'norm_feeder_loadshape',
								 'property': 'value',
								 'file': '{:s}/players/{:s}'.format(config_data['includePath'], config_data['load_shape_norm']),
								 'loop': '14600',
								 'comment': '// Will loop file for 40 years assuming the file has data for a 24 hour period'}
		last_key += 1

	# Add climate dictionaries
	if '.csv' in config_data["weather"]:
		# Climate file is a cvs file. Need to add csv_reader object
		glmCaseDict[last_key] = {'object': 'csv_reader',
								 'name': 'CsvReader',
								 'filename': '{:s}/weather/{:s}'.format(config_data['includePath'], config_data["weather"])}
		last_key += 1

	glmCaseDict[last_key] = {'object': 'climate',
							 'name': 'ClimateWeather',
							 'tmyfile': '{:s}/weather/{:s}'.format(config_data['includePath'], config_data["weather"])}

	if '.tmy2' in config_data["weather"] or '.tmy3' in config_data["weather"]:
		glmCaseDict[last_key]['interpolate'] = 'QUADRATIC'
	elif '.csv' in config_data["weather"]:
		glmCaseDict[last_key]['reader'] = 'CsvReader'
	else:
		raise Exception('weather name "{:s}" did not contain a valid extension'.format(config_data['weather']))

	last_key += 1

	if use_flags["addSubstation"] == 1:
		#find name of swingbus of static model dictionary
		hit = 0
		swing_bus_name = ''
		nom_volt = 0
		for x in glmDict:
			if hit < 1 and 'bustype' in glmDict[x] and glmDict[x]['bustype'] == 'SWING':
				hit = 1
				swing_bus_name = glmDict[x]['name']
				nom_volt = glmDict[x]['nominal_voltage'] # Nominal voltage in V
		if hit is 0:
			raise Exception('Original feeder model did not contain a swing bus!')

		# Add substation transformer transformer_configuration
		glmCaseDict[last_key] = {'object': 'transformer_configuration',
								 'name': 'trans_config_to_feeder',
								 'connect_type': 'WYE_WYE',
								 'install_type': 'PADMOUNT',
								 'primary_voltage': '{:d}'.format(config_data['nom_volt']),
								 'secondary_voltage': '{:s}'.format(nom_volt),
								 'power_rating': '{:.1f} MVA'.format(config_data['feeder_rating']),
								 'impedance': '0.00033+0.0022j'}
		last_key += 1

		# Add substation swing bus and substation transformer dictionaries
		glmCaseDict[last_key] = {'object': 'meter',
								 'name': 'network_node',
								 'bustype': 'SWING',
								 'nominal_voltage': '{:d}'.format(config_data['nom_volt']),
								 'phases': 'ABCN'}
		# Add transmission voltage players
		# parent_key = last_key
		last_key += 1

		glmCaseDict[last_key] = {'object': 'transformer',
								 'name': 'substation_transformer',
								 'from': 'network_node',
								 'to': '{:s}'.format(swing_bus_name),
								 'phases': 'ABCN',
								 'configuration': 'trans_config_to_feeder'}
		last_key += 1

	# Copy static powerflow model glm dictionary into case dictionary
	for x in glmDict:
		if 'clock' not in glmDict[x].keys() and '#set' not in glmDict[x].keys() and '#define' not in glmDict[x].keys() and 'module' not in glmDict[x].keys() and 'omftype' not in glmDict[x].keys():
			glmCaseDict[last_key] = copy.deepcopy(glmDict[x])
			if use_flags["addSubstation"] == 1:
				# Remove original swing bus from static model
				if 'bustype' in glmCaseDict[last_key].keys() and glmCaseDict[last_key]['bustype'] == 'SWING':
					del glmCaseDict[last_key]['bustype']
					glmCaseDict[last_key]['object'] = 'meter'
			last_key += 1

	# Add groupid's to lines and transformers
	for x in glmCaseDict:
		if 'object' in glmCaseDict[x]:
			if glmCaseDict[x]['object'] == 'triplex_line':
				glmCaseDict[x]['groupid'] = 'Triplex_Line'
			elif glmCaseDict[x]['object'] == 'transformer':
				glmCaseDict[x]['groupid'] = 'Distribution_Trans'
			elif glmCaseDict[x]['object'] == 'overhead_line' or glmCaseDict[x]['object'] == 'underground_line':
				glmCaseDict[x]['groupid'] = 'Distribution_Line'

	# Create dictionary that houses the number of residential 'load' objects where residential house objects will be tacked on.
	total_house_number = 0
	residential_dict = {}
	if use_flags['use_homes'] == 1:
		residential_key = 0
		for x in glmCaseDict:
			if 'object' in glmCaseDict[x] and glmCaseDict[x]['object'] == 'triplex_node':
				if 'power_1' in glmCaseDict[x] or 'power_12' in glmCaseDict[x] or 'number_of_houses' in glmCaseDict[x]:
					residential_dict[residential_key] = {'name': glmCaseDict[x]['name'],
														 'parent': 'None',
														 'number_of_houses': 0,
														 'load': 0,
														 'large_vs_small': 0.0,
														 'phases': glmCaseDict[x]['phases']}

					if 'parent' in glmCaseDict[x]:
						residential_dict[residential_key]['parent'] = glmCaseDict[x]['parent']

					if 'load_class' in glmCaseDict[x]:
						residential_dict[residential_key]['load_classification'] = glmCaseDict[x]['load_class']

					# Figure out how many houses should be attached to this load object
					load = 0
					if 'number_of_houses' in glmCaseDict[x]:
						if 'power_1' in glmCaseDict[x] or 'power_12' in glmCaseDict[x]:
							print 'You specified both number of houses to implement along with a constant load. Constant load is ignored!'
						load = int(glmCaseDict[x]['number_of_houses'])*config_data['avg_house']
						residential_dict[residential_key]['load'] = load
						residential_dict[residential_key]['number_of_houses'] = int(glmCaseDict[x]['number_of_houses'])
						del glmCaseDict[x]['number_of_houses']
					else:
						if 'power_1' in glmCaseDict[x]:
							c_num = complex(glmCaseDict[x]['power_1'])
							load += abs(c_num)
							del glmCaseDict[x]['power_1']

						if 'power_12' in glmCaseDict[x]:
							c_num = complex(glmCaseDict[x]['power_12'])
							load += abs(c_num)
							del glmCaseDict[x]['power_12']

						residential_dict[residential_key]['load'] = load
						residential_dict[residential_key]['number_of_houses'] = int(round(load / config_data['avg_house']))

					total_house_number += residential_dict[residential_key]['number_of_houses']

					# Determine whether we rounded down of up to help determine the square footage (neg. number => small homes)
					large_vs_small = load / config_data['avg_house'] - residential_dict[residential_key]['number_of_houses']
					if large_vs_small > 0.25:
						residential_dict[residential_key]['large_vs_small'] = 0.25
					elif large_vs_small < -0.25:
						residential_dict[residential_key]['large_vs_small'] = -0.25
					else:
						residential_dict[residential_key]['large_vs_small'] = large_vs_small

					residential_key += 1

	# Create dictionary that houses the number of commercial 'load' objects where commercial house objects will be tacked on.
	total_commercial_number = 0  # Variable that stores the total amount of houses that need to be added.
	commercial_dict = {}
	if use_flags['use_commercial'] == 1:
		commercial_key = 0

		for x in glmCaseDict:
			if 'object' in glmCaseDict[x] and glmCaseDict[x]['object'] == 'load':
				commercial_dict[commercial_key] = {'name': glmCaseDict[x]['name'],
												   'parent': 'None',
												   'load': [0, 0, 0],
												   'number_of_houses': [0, 0, 0],
												   # [phase A, phase B, phase C]
												   'nom_volt': glmCaseDict[x]['nominal_voltage'],
												   'phases': glmCaseDict[x]['phases']}

				if 'parent' in glmCaseDict[x]:
					commercial_dict[commercial_key]['parent'] = glmCaseDict[x]['parent']

				# Figure out how many houses should be attached to this load object
				load_A = 0
				load_B = 0
				load_C = 0

				# determine the total ZIP load for each phase
				if 'constant_power_A' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_power_A'])
					load_A += abs(c_num)

				if 'constant_power_B' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_power_B'])
					load_B += abs(c_num)

				if 'constant_power_C' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_power_C'])
					load_C += abs(c_num)

				if 'constant_impedance_A' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_impedance_A'])
					load_A += pow(commercial_dict[commercial_key]['nom_volt'], 2) / (3 * abs(c_num))

				if 'constant_impedance_B' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_impedance_B'])
					load_B += pow(commercial_dict[commercial_key]['nom_volt'], 2) / (3 * abs(c_num))

				if 'constant_impedance_C' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_impedance_C'])
					load_C += pow(commercial_dict[commercial_key]['nom_volt'], 2) / (3 * abs(c_num))

				if 'constant_current_A' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_current_A'])
					load_A += commercial_dict[commercial_key]['nom_volt'] * (abs(c_num))

				if 'constant_current_B' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_current_B'])
					load_B += commercial_dict[commercial_key]['nom_volt'] * (abs(c_num))

				if 'constant_current_C' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_current_C'])
					load_C += commercial_dict[commercial_key]['nom_volt'] * (abs(c_num))

				# if the load is too low we don'w implement any houses
				if load_A < config_data['commercial_load_cut']:
					commercial_dict[commercial_key]['number_of_houses'][0] = 0
				else:
					commercial_dict[commercial_key]['number_of_houses'][0] = int(math.ceil(load_A / config_data['avg_commercial']))

				if load_B < config_data['commercial_load_cut']:
					commercial_dict[commercial_key]['number_of_houses'][1] = 0
				else:
					commercial_dict[commercial_key]['number_of_houses'][1] = int(math.ceil(load_B / config_data['avg_commercial']))

				if load_C < config_data['commercial_load_cut']:
					commercial_dict[commercial_key]['number_of_houses'][2] = 0
				else:
					commercial_dict[commercial_key]['number_of_houses'][2] = int(math.ceil(load_C / config_data['avg_commercial']))

				total_commercial_number += commercial_dict[commercial_key]['number_of_houses'][0]
				total_commercial_number += commercial_dict[commercial_key]['number_of_houses'][1]
				total_commercial_number += commercial_dict[commercial_key]['number_of_houses'][2]

				commercial_dict[commercial_key]['load'][0] = load_A
				commercial_dict[commercial_key]['load'][1] = load_B
				commercial_dict[commercial_key]['load'][2] = load_C

				# Replace load with a node remove constant load keys
				glmCaseDict[x]['object'] = 'node'
				if 'voltage_A' in glmCaseDict[x]:
					del glmCaseDict[x]['voltage_A']

				if 'voltage_B' in glmCaseDict[x]:
					del glmCaseDict[x]['voltage_B']

				if 'voltage_C' in glmCaseDict[x]:
					del glmCaseDict[x]['voltage_C']

				if 'load_class' in glmCaseDict[x]:
					del glmCaseDict[x]['load_class']  # Must remove load_class as it isn't a published property

				if 'constant_power_A' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_power_A']

				if 'constant_power_B' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_power_B']

				if 'constant_power_C' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_power_C']

				if 'constant_impedance_A' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_impedance_A']

				if 'constant_impedance_B' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_impedance_B']

				if 'constant_impedance_C' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_impedance_C']

				if 'constant_current_A' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_current_A']

				if 'constant_current_B' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_current_B']

				if 'constant_current_C' in glmCaseDict[x]:
					del glmCaseDict[x]['constant_current_C']

				commercial_key += 1

	# Tack on residential loads
	if use_flags['use_homes'] == 1:
		glmCaseDict, last_key = loads.append_residential(glmCaseDict, use_flags, residential_dict, last_key, config_data)
	elif use_flags['use_homes'] == 2:
		glmCaseDict, last_key = loads.add_normalized_residential_ziploads(glmCaseDict, residential_dict, config_data, last_key)


	if use_flags['use_commercial'] == 1:
		glmCaseDict, last_key = loads.append_commercial(glmCaseDict, use_flags, commercial_dict, last_key, config_data)
	elif use_flags['use_commercial'] == 2:
		glmCaseDict, last_key = loads.add_normalized_commercial_ziploads(glmCaseDict, commercial_dict, config_data, last_key)

	return glmCaseDict

def addCCSISubstation(glmDict, config_data, use_flags, substationkV):
	"""
	This function adds a specific substation that is needed for the co-simulation studies

	Inputs
		glmDict - dictionary containing the full feeder unmodified
		config_data - dictionary that contains the configurations of the feeder
		substationkV - the substation nominal voltage

	Outputs
		glmDict -  dictionary containing the full feeder modified
	"""

	# a double check to ensure we actually need to add the substation this way!
	if use_flags['addSubstation'] == 1:
		return glmDict

	# Check if last_key is already in glm dictionary
	def unused_key(key):
		if key in glmDict:
			while key in glmDict:
				key += 1
		return key

	# let's determine the next available key
	last_key = unused_key(0)

	#find name of swingbus of static model dictionary
	hit = 0
	swing_bus_name = ''
	nom_volt = 0
	for x in glmDict:
		if hit < 1 and 'bustype' in glmDict[x] and glmDict[x]['bustype'] == 'SWING':
			hit = 1
			swing_bus_name = glmDict[x]['name']
			nom_volt = glmDict[x]['nominal_voltage'] # Nominal voltage in V
			del glmDict[x]['bustype']
			glmDict[x]['object'] = 'meter'
	if hit is 0:
		raise Exception('Original feeder model did not contain a swing bus!')

	# Add substation swing bus and substation transformer dictionaries
	glmDict[last_key] = {'object': 'substation',
							 'name': 'network_node',
							 'bustype': 'SWING',
							 'positive_sequence_voltage': '{:d}'.format(int(substationkV*1000)),
						 	 'base_power': '100',
							 'power_convergence_value': '100',
							 'nominal_voltage': '{:d}'.format(int(substationkV*1000)),
							 'phases': 'ABCN'}
	# Add transmission voltage players
	last_key = unused_key(last_key)

	glmDict[last_key] = {'object': 'transformer',
							 'name': 'substation_transformer',
							 'from': 'network_node',
							 'to': '{:s}'.format(swing_bus_name),
							 'phases': 'ABCN',
							 'configuration': 'trans_config_to_feeder'}
	last_key = unused_key(last_key)

	# Add substation transformer transformer_configuration
	glmDict[last_key] = {'object': 'transformer_configuration',
							 'name': 'trans_config_to_feeder',
							 'connect_type': 'WYE_WYE',
							 'install_type': 'PADMOUNT',
							 'primary_voltage': '{:d}'.format(int(substationkV*1000)),
							 'secondary_voltage': '{:s}'.format(nom_volt),
							 'power_rating': '{:.1f} MVA'.format(config_data['feeder_rating']),
							 'impedance': '0.00033+0.0022j'}
	# last_key = unused_key(last_key)

	return glmDict

if __name__ == '__main__':
	pass

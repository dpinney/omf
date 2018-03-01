"""
This file contains a fuction to add recorders to a feeder based on the use flags defined

	add_recorders(recorder_dict, config_file, file_path, feeder_name, last_key=0):
		This fuction add recorders based on the configuration of the feeder


Created December 20, 2016 by Jacob Hansen (jacob.hansen@pnnl.gov)

Copyright (c) 2016 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
Government, including the right to distribute to other Government contractors.
"""
from __future__ import division
import os

def add_recorders(recorder_dict, config_file, file_path, feeder_name, last_key=0):
	"""
	This fuction adds recorders based on the configuration of the feeder

	Inputs
		recorder_dict - dictionary containing the full feeder
		config_file - dictionary that contains the configurations of the feeder
		file_path - file path to where you created the modified GLM
		feeder_name - name of the feeder we are working with
		last_object_key - Last object key

	Outputs
		recorder_dict -  dictionary containing the full feeder
	"""

	# determine if we need to create an output folder
	if not os.path.isdir(file_path + '/output'):
		os.makedirs(file_path + '/output')

	# Check if last_key is already in glm dictionary
	def unused_key(key):
		if key in recorder_dict:
			while key in recorder_dict:
				key += 1
		return key

	# let's determine the next available key
	last_key = unused_key(last_key)

	# flags to ensure we are not deploying recorders for technology that is not in the dictionary
	have_resp_zips = 0
	have_houses = 0
	have_unresp_zips = 0
	have_waterheaters = 0
	have_auction = 0
	have_EVs = 0
	have_EBs = 0
	have_UEBs = 0
	swing_node = None
	climate_name = None
	regulator_parents = []
	regulator_names = []

	for x in recorder_dict.keys():
		if 'object' in recorder_dict[x].keys():
			if recorder_dict[x]['object'] == 'transformer' and recorder_dict[x]['name'] == 'substation_transformer':
				swing_node = recorder_dict[x]['to']

			if recorder_dict[x]['object'] == 'house':
				have_houses = 1

			if recorder_dict[x]['object'] == 'climate':
				climate_name = recorder_dict[x]['name']

			if recorder_dict[x]['object'] == 'ZIPload':
				if 'groupid' in recorder_dict[x].keys():
					if recorder_dict[x]['groupid'] == 'Responsive_load':
						have_resp_zips = 1

					if recorder_dict[x]['groupid'] == 'Unresponsive_load':
						have_unresp_zips = 1

			if recorder_dict[x]['object'] == 'waterheater':
				have_waterheaters = 1

			if recorder_dict[x]['object'] == 'auction_ccsi':
				have_auction = 1
				
			if recorder_dict[x]['object'] == 'evcharger_det':
				have_EVs = 1	

			if recorder_dict[x]['object'] == 'battery':
				if recorder_dict[x]['groupid'] == 'residential_storage':
					have_EBs = 1
				if recorder_dict[x]['groupid'] == 'utility_storage':
					have_UEBs = 1

			if recorder_dict[x]['object'] == 'regulator':
				regulator_parents.append(recorder_dict[x]['to'])
				regulator_names.append(recorder_dict[x]['name'])

	# time to add those recorders
	if 'responsive_load' in config_file['recorders']:
		if have_resp_zips == 1 and config_file['recorders']['responsive_load']:
			recorder_dict[last_key] = {'object': 'collector',
									   'group': '"class=ZIPload AND groupid=Responsive_load"',
									   'file': 'output/{:s}_residential_responsive_load.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(base_power)'}
			last_key = unused_key(last_key)
		else:
			if config_file['recorders']['responsive_load']:
				print 'You asked to record responsive zip load, however I did not find any in the dictionary'

	if 'unresponsive_load' in config_file['recorders']:
		if have_unresp_zips == 1 and config_file['recorders']['unresponsive_load']:
			recorder_dict[last_key] = {'object': 'collector',
									   'group': '"class=ZIPload AND groupid=Unresponsive_load"',
									   'file': 'output/{:s}_residential_unresponsive_load.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(base_power)'}
			last_key = unused_key(last_key)
		else:
			if config_file['recorders']['unresponsive_load']:
				print 'You asked to record non responsive zip load, however I did not find any in the dictionary'
	if 'water_heaters' in config_file['recorders']:
		if have_waterheaters == 1 and config_file['recorders']['water_heaters']:
			recorder_dict[last_key] = {'object': 'collector',
									   'group': '"class=waterheater"',
									   'file': 'output/{:s}_waterheater_total_load.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(actual_load)'}
			last_key = unused_key(last_key)
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=waterheater"',
									   'file': 'output/{:s}_waterheater_load.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'actual_load'}
			last_key = unused_key(last_key)
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=waterheater"',
									   'file': 'output/{:s}_waterheater_temperature.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'temperature'}
			last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=waterheater"',
			# 						   'file': 'output/{:s}_waterheater_control_temperature.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 'Tcontrol'}
			# last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=waterheater"',
			# 						   'file': 'output/{:s}_waterheater_tank_setpoint.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 'tank_setpoint'}
			# last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=waterheater"',
			# 						   'file': 'output/{:s}_waterheater_thermostat_deadband.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 'thermostat_deadband'}
			# last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=waterheater"',
			# 						   'file': 'output/{:s}_waterheater_override.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 're_override'}
			# last_key = unused_key(last_key)
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=waterheater"',
									   'file': 'output/{:s}_waterheater_water_draw.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'water_demand'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=waterheater"',
									   'file': 'output/{:s}_waterheater_load_state.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'load_state'}
			last_key = unused_key(last_key)
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=waterheater"',
									   'file': 'output/{:s}_waterheater_thermo_height.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'height'}
			last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=waterheater"',
			# 						   'file': 'output/{:s}_waterheater_model.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 'waterheater_model'}
			# last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=waterheater"',
			# 						   'file': 'output/{:s}_waterheater_height.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 'tank_height'}
			# last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=waterheater"',
			# 						   'file': 'output/{:s}_waterheater_tank_state.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 'current_tank_status'}
			# last_key = unused_key(last_key)
		else:
			if config_file['recorders']['water_heaters']:
				print 'You asked to record water heaters, however I did not find any in the dictionary'

	if 'swing_node' in config_file['recorders']:
		if config_file['recorders']['swing_node']:
			if swing_node is not None:
				recorder_dict[last_key] = {'object': 'recorder',
											'parent': '{:s}'.format(swing_node),
											'file': 'output/{:s}_swing_node.csv'.format(feeder_name),
											'interval': '{:d}'.format(config_file['measure_interval']),
											'in': '"{:s}"'.format(config_file['record_in']),
											'out': '"{:s}"'.format(config_file['record_out']),
											#'property': 'measured_current_A,measured_current_B,measured_current_C,measured_voltage_A,measured_voltage_B,measured_voltage_C,measured_power'}
											'property': 'measured_current_A.real,measured_current_A.imag,measured_current_B.real,measured_current_B.imag,measured_current_C.real,measured_current_C.imag,measured_voltage_A.real,measured_voltage_A.imag,measured_voltage_B.real,measured_voltage_B.imag,measured_voltage_C.real,measured_voltage_C.imag,measured_real_power,measured_reactive_power'}

				last_key = unused_key(last_key)
			else:
				print 'You asked to record the swing node, however I did not find any in the dictionary'

	if 'climate' in config_file['recorders']:
		if config_file['recorders']['climate']:
			if climate_name is not None:
				recorder_dict[last_key] = {'object': 'recorder',
										   'parent': '{:s}'.format(climate_name),
										   'file': 'output/{:s}_climate.csv'.format(feeder_name),
										   'interval': '{:d}'.format(config_file['measure_interval']),
										   'in': '"{:s}"'.format(config_file['record_in']),
										   'out': '"{:s}"'.format(config_file['record_out']),
										   'property': 'temperature,humidity'}
				last_key = unused_key(last_key)
			else:
				print 'You asked to record the climate, however I did not find any in the dictionary'

	if 'HVAC' in config_file['recorders']:
		if have_houses == 1 and config_file['recorders']['HVAC']:
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=house"',
									   'file': 'output/{:s}_residential_house_temperature.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'air_temperature'}
			last_key = unused_key(last_key)
			recorder_dict[last_key] = {'object': 'group_recorder',
								   	   'group': '"class=house"',
									   'file': 'output/{:s}_residential_HVAC_load.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'hvac_load'}
			last_key = unused_key(last_key)
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=house"',
									   'file': 'output/{:s}_residential_HVAC_heating_setpoint.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'heating_setpoint'}
			last_key = unused_key(last_key)
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=house"',
									   'file': 'output/{:s}_residential_HVAC_cooling_setpoint.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'cooling_setpoint'}
			last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=house"',
			# 						   'file': 'output/{:s}_residential_HVAC_deadband.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 'thermostat_deadband'}
			# last_key = unused_key(last_key)
			# recorder_dict[last_key] = {'object': 'group_recorder',
			# 						   'group': '"class=house"',
			# 						   'file': 'output/{:s}_residential_HVAC_override.csv'.format(feeder_name),
			# 						   'interval': '{:d}'.format(config_file['measure_interval']),
			# 						   'in': '"{:s}"'.format(config_file['record_in']),
			# 						   'out': '"{:s}"'.format(config_file['record_out']),
			# 						   'property': 're_override'}
			# last_key = unused_key(last_key)

		else:
			if config_file['recorders']['HVAC']:
				print 'You asked to record HVAC, however I did not find any in the dictionary'

	if 'load_composition' in config_file['recorders']:
		if config_file['recorders']['load_composition']:

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=triplex_meter AND groupid=Residential_Meter',
									   'file': 'output/{:s}_Residential_meter.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(measured_real_power)'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=triplex_meter AND groupid=Commercial_Meter',
									   'file': 'output/{:s}_Commercial_meter.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(measured_real_power)'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=house AND groupid=Residential',
									   'file': 'output/{:s}_Residential_building.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(total_load)'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=house AND groupid=Commercial',
									   'file': 'output/{:s}_Commercial_building.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(total_load)'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=house AND groupid=Residential',
									   'file': 'output/{:s}_Residential_hvac.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(hvac_load)'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=house AND groupid=Commercial',
									   'file': 'output/{:s}_Commercial_hvac.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(hvac_load)'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=ZIPload AND groupid=Residential_zip',
									   'file': 'output/{:s}_Residential_zip.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(actual_power.real)'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=ZIPload AND groupid=Commercial_zip',
									   'file': 'output/{:s}_Commercial_zip.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(actual_power.real)'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'collector',
									   'group': 'class=waterheater AND groupid=water_heater',
									   'file': 'output/{:s}_Residential_water_heater.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'sum(actual_load)'}
			last_key = unused_key(last_key)

	if 'customer_meter' in config_file['recorders']:
		if config_file['recorders']['customer_meter']:

			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"groupid=Residential_Meter"',
									   'file': 'output/{:s}_AMI_residential_phase12_power.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'measured_power'}
			last_key = unused_key(last_key)


			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"groupid=Residential_Meter"',
									   'file': 'output/{:s}_AMI_residential_phase12_voltage.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'voltage_12'}
			last_key = unused_key(last_key)

	if 'voltage_regulators' in config_file['recorders']:
		if regulator_parents and config_file['recorders']['voltage_regulators']:
			for idx, regulator in enumerate(regulator_parents):
				recorder_dict[last_key] = {'object': 'recorder',
										   'parent': '{:s}'.format(regulator),
										   'file': 'output/{:s}_regulator_{:d}_output.csv'.format(feeder_name, idx+1),
										   'interval': '{:d}'.format(config_file['measure_interval']),
										   'in': '"{:s}"'.format(config_file['record_in']),
										   'out': '"{:s}"'.format(config_file['record_out']),
										   #'property': 'voltage_A.real,voltage_A.imag,voltage_B.real,voltage_B.imag,voltage_C.real,voltage_C.imag'}
										   'property': 'voltage_A,voltage_B,voltage_C'}
				last_key = unused_key(last_key)

			for idx, regulator in enumerate(regulator_names):
				recorder_dict[last_key] = {'object': 'recorder',
										   'parent': '{:s}'.format(regulator),
										   'file': 'output/{:s}_regulator_{:d}_tab.csv'.format(feeder_name, idx + 1),
										   'interval': '{:d}'.format(config_file['measure_interval']),
										   'in': '"{:s}"'.format(config_file['record_in']),
										   'out': '"{:s}"'.format(config_file['record_out']),
										   'property': 'tap_A,tap_B,tap_C'}
				last_key = unused_key(last_key)
		else:
			if config_file['recorders']['voltage_regulators']:
				print 'You asked to record regulators, however I did not find any in the dictionary'

	if 'market' in config_file['recorders']:
		if have_auction == 1 and config_file['recorders']['market']:
			recorder_dict[last_key] = {'object': 'recorder',
									   'parent': 'retailMarket',
									   'file': 'output/{:s}_retail_market.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'current_price_mean_24h,current_price_stdev_24h,fixed_price,market_id'}
			last_key = unused_key(last_key)
		else:
			if config_file['recorders']['market']:
				print 'You asked to record auction, however I did not find any in the dictionary'

	if 'TSEControllers' in config_file['recorders']:
		if have_auction == 1 and config_file['recorders']['TSEControllers']:
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=controller_ccsi"',
									   'file': 'output/{:s}_controller_bid_price.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'bid_price'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=controller_ccsi"',
									   'file': 'output/{:s}_controller_bid_quantity.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'bid_quantity'}
			last_key = unused_key(last_key)

		else:
			if config_file['recorders']['TSEControllers']:
				print 'You asked to record TSE controllers, however I did not find any in the dictionary'

	if 'EVChargers' in config_file['recorders']:
		if have_EVs == 1 and config_file['recorders']['EVChargers']:
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=evcharger_det"',
									   'file': 'output/{:s}_EV_battery_SOC.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'battery_SOC'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"class=evcharger_det"',
									   'file': 'output/{:s}_EV_charge_rate.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'charge_rate'}
			last_key = unused_key(last_key)
		else:
			if config_file['recorders']['EVChargers']:
				print 'You asked to record EV chargers, however I did not find any in the dictionary'			
	

	if 'residentialStorage' in config_file['recorders']:
		if have_EBs == 1 and config_file['recorders']['residentialStorage']:
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"groupid=residential_storage"',
									   'file': 'output/{:s}_residential_storage_SOC.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'state_of_charge'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"groupid=residential_storage"',
									   'file': 'output/{:s}_residential_storage_power.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'battery_load'}
			last_key = unused_key(last_key)
		else:
			if config_file['recorders']['residentialStorage']:
				print 'You asked to record residential battery storage, however I did not find any in the dictionary'


	if 'utilityStorage' in config_file['recorders']:
		if have_UEBs == 1 and config_file['recorders']['utilityStorage']:
			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"groupid=utility_storage"',
									   'file': 'output/{:s}_utility_storage_SOC.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'state_of_charge'}
			last_key = unused_key(last_key)

			recorder_dict[last_key] = {'object': 'group_recorder',
									   'group': '"groupid=utility_storage"',
									   'file': 'output/{:s}_utility_storage_power.csv'.format(feeder_name),
									   'interval': '{:d}'.format(config_file['measure_interval']),
									   'in': '"{:s}"'.format(config_file['record_in']),
									   'out': '"{:s}"'.format(config_file['record_out']),
									   'property': 'battery_load'}
			last_key = unused_key(last_key)
		else:
			if config_file['recorders']['utilityStorage']:
				print 'You asked to record utility battery storage, however I did not find any in the dictionary'				

	return recorder_dict

if __name__ == '__main__':
	pass

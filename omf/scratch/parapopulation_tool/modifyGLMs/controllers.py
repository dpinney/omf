"""
This file contains functions that help configure residential house controllers



Created April 26, 2017 by Jacob Hansen (jacob.hansen@pnnl.gov)

Copyright (c) 2017 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
Government, including the right to distribute to other Government contractors.
"""

from __future__ import division
import random, time

def add_residential_control(feeder_dict, feederConfig, useFlags, last_key=0):
	"""
	This fuction adds residential controllers based on the configuration of the feeder

	Inputs
		feeder_dict - dictionary containing the full feeder
		config_file - dictionary that contains the configurations of the feeder
		last_object_key - Last object key

	Outputs
		feeder_dict -  dictionary containing the full feeder
	"""

	# let's check that the control mode specified by the user makes sense.
	if not (useFlags['houseThermostatMode'] == 'HEAT' or useFlags['houseThermostatMode'] == 'COOL'):
		print 'WARNING: control mode is ill defined. These controllers will only work with either cooling or heating!'

	# Check if last_key is already in glm dictionary
	def unused_key(key):
		if key in feeder_dict:
			while key in feeder_dict:
				key += 1
		return key

	# let's determine the next available key
	last_key = unused_key(last_key)

	# Add class auction to dictionary
	feeder_dict[last_key] = {'class': 'auction_ccsi',
							 'variable_types': ['double', 'double'],
							 'variable_names': ['current_price_mean_{:.0f}h'.format(feederConfig['TSEauctionStatistics']), 'current_price_stdev_{:.0f}h'.format(feederConfig['TSEauctionStatistics'])]}

	# let's determine the next available key
	last_key = unused_key(last_key)

	# Add object auction to dictionary
	feeder_dict[last_key] = {'object': 'auction_ccsi',
							 'name': "{:s}".format(feederConfig['TSEmarketName']),
							 'unit': "{:s}".format(feederConfig['TSEmarketUnit']),
							 'period': "{:.0f}".format(feederConfig['TSEmarketPeriod']),
							 'special_mode': 'BUYERS_ONLY',
							 'init_price': '{:.2f}'.format(feederConfig['TSEinitPrice']),
							 'init_stdev': '{:.2f}'.format(feederConfig['TSEinitStdev']),
							 'price_cap': '{:.2f}'.format(feederConfig['TSEpriceCap']),
							 'use_future_mean_price': '{:s}'.format(feederConfig['TSEuseFutureMeanPrice']),
							 'warmup': '{:.0f}'.format(feederConfig['TSEwarmUp'])}

	# let's determine the next available key
	last_key = unused_key(last_key)

	# loop through the feeder dictionary to find residential houses that we can attach controllers to
	controllerDict = {}
	counter = 0
	for x in feeder_dict:
		if 'object' in feeder_dict[x] and feeder_dict[x]['object'] == 'house' and feeder_dict[x]['groupid'] == 'Residential':
			# if we are in heating mode we need to ensure that
			if (useFlags['houseThermostatMode'] == 'HEAT' and feeder_dict[x]['heating_system_type'] != 'GAS') or (useFlags['houseThermostatMode'] == 'COOL' and feeder_dict[x]['cooling_system_type'] != 'NONE'):
				controllerDict[counter] = {'parent' : '{:s}'.format(feeder_dict[x]['name']),
										   'name': '{:s}_controller'.format(feeder_dict[x]['name']),
										   'schedule_skew': '{:s}'.format(feeder_dict[x]['schedule_skew']),
										   'heating_setpoint': '{:s}'.format(feeder_dict[x]['heating_setpoint']),
										   'cooling_setpoint': '{:s}'.format(feeder_dict[x]['cooling_setpoint']),}

				if useFlags['houseThermostatMode'] == 'COOL': # very important to remove the cooling setpoint from the house! it will not be handled by the controller
					del feeder_dict[x]['cooling_setpoint']
				elif useFlags['houseThermostatMode'] == 'HEAT': # very important to remove the heating setpoint from the house! it will not be handled by the controller
					del feeder_dict[x]['heating_setpoint']

				counter += 1
			# else:
				# print "we passed on controller -> ", feeder_dict[x]['name']

	# now we just need to add the controllers
	for x in controllerDict:
		# limit slider randomization to Olypen style
		## slider = random.normalvariate(0.45, 0.2)
		slider = random.normalvariate(0.6, 0.2)
		if slider > feederConfig['TSEsliderSetting']:
			slider = feederConfig['TSEsliderSetting']
		if slider < 0:
			#slider = 0
			slider = 0.1

		# set the pre-cool / pre-heat xrange to really small
		# to get rid of it.
		s_rampstat = 2
		s_rangestat = 5
		#s_rampstat = 2.1
		#s_rangestat = 10

		hrh = s_rangestat - s_rangestat * (1 - slider)
		crh = s_rangestat - s_rangestat * (1 - slider)
		hrl = -s_rangestat - s_rangestat * (1 - slider)
		crl = -s_rangestat + s_rangestat * (1 - slider)

		hrh2 = -s_rampstat - (1 - slider)
		crh2 = s_rampstat + (1 - slider)
		hrl2 = -s_rampstat - (1 - slider)
		crl2 = s_rampstat + (1 - slider)

		feeder_dict[last_key] = {'object': 'controller_ccsi',
									'name': '{:s}'.format(controllerDict[x]['name']),
									'parent': '{:s}'.format(controllerDict[x]['parent']),
									'schedule_skew': '{:s}'.format(controllerDict[x]['schedule_skew']),
									'market': '{:s}'.format(feederConfig['TSEmarketName']),
									'bid_mode': '{:s}'.format(feederConfig['TSEbidMode']),
								    'bid_delay': '{:d}'.format(feederConfig['TSEbidDelay']),
									'control_mode': '{:s}'.format(feederConfig['TSEcontrolTechnology']),
									'resolve_mode': '{:s}'.format(feederConfig['TSEresolveMode']),
									'period': '{:.0f}'.format(feederConfig['TSEmarketPeriod']),
									'average_target': 'current_price_mean_{:.0f}h'.format(feederConfig['TSEauctionStatistics']),
									'standard_deviation_target': 'current_price_stdev_{:.0f}h'.format(feederConfig['TSEauctionStatistics']),
									'target': 'air_temperature',
									'deadband': 'thermostat_deadband',
									'total': 'total_load',
									'load': 'hvac_load',
									'state': 'power_state'}

		# if we are in heating mode
		if useFlags['houseThermostatMode'] == 'HEAT':
			feeder_dict[last_key]['range_high'] = hrh
			feeder_dict[last_key]['range_low'] = hrl
			feeder_dict[last_key]['ramp_high'] = hrh2
			feeder_dict[last_key]['ramp_low'] = hrl2
			feeder_dict[last_key]['base_setpoint'] = controllerDict[x]['heating_setpoint']
			feeder_dict[last_key]['setpoint'] = 'heating_setpoint'
			feeder_dict[last_key]['demand'] = 'rated_heating_demand' # could also use last_heating_load

		# if we are in cooling mode
		if useFlags['houseThermostatMode'] == 'COOL':
			feeder_dict[last_key]['range_high'] = crh
			feeder_dict[last_key]['range_low'] = crl
			feeder_dict[last_key]['ramp_high'] = crh2
			feeder_dict[last_key]['ramp_low'] = crl2
			feeder_dict[last_key]['base_setpoint'] = controllerDict[x]['cooling_setpoint']
			feeder_dict[last_key]['setpoint'] = 'cooling_setpoint'
			feeder_dict[last_key]['demand'] = 'rated_cooling_demand'  # could also use last_cooling_load

		# find the next available key
		last_key = unused_key(last_key)

	return feeder_dict

if __name__ == '__main__':
	pass
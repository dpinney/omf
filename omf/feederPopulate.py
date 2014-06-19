'''
This library is used to populate a base feeder tree with different load and technology models and returns a new feeder tree with the desired technology models.
For example, to attach a feeder tree, baseTree, with ziploads run in the terminal

	python -c "import populateFeeder; newTree, key = populateFeeder.startPopulation(loadshape_dict, residenntial_dict, config_data, last_key)"
	
@author: Andrew Fisher
'''
import math
import random
import copy

def _add_normalized_residential_ziploads(loadshape_dict, residenntial_dict, config_data, last_key):
	'''This function adds triplex_load dictionary with load shape information to the population feeder tree.'''
	for x in residenntial_dict.keys():
		tpload_name = residenntial_dict[x]['name']
		tpload_parent = residenntial_dict[x]['parent']
		tpphases = residenntial_dict[x]['phases']
		tpnom_volt = '120.0'
		bp = residenntial_dict[x]['load']*config_data['normalized_loadshape_scalar']
		loadshape_dict[last_key] = {    'object' : 'triplex_load',
														'name' : '{:s}_loadshape'.format(tpload_name),
														'phases' : tpphases,
														'nominal_voltage' : tpnom_volt}
		loadshape_dict[last_key]['parent'] = tpload_parent
		if bp > 0.0:         
			loadshape_dict[last_key]['base_power_12'] = 'norm_feeder_loadshape.value*{:f}'.format(bp)
			loadshape_dict[last_key]['power_pf_12'] = '{:f}'.format(config_data['r_p_pf'])
			loadshape_dict[last_key]['current_pf_12'] = '{:f}'.format(config_data['r_i_pf'])
			loadshape_dict[last_key]['impedance_pf_12'] = '{:f}'.format(config_data['r_z_pf'])
			loadshape_dict[last_key]['power_fraction_12'] = '{:f}'.format(config_data['r_pfrac'])
			loadshape_dict[last_key]['current_fraction_12'] = '{:f}'.format(config_data['r_ifrac'])
			loadshape_dict[last_key]['impedance_fraction_12'] = '{:f}'.format(config_data['r_zfrac'])
		last_key += last_key
	return (loadshape_dict, last_key)

def _add_normalized_commercial_ziploads(loadshape_dict, commercial_dict, config_data, last_key):
	'''This function adds load dictionary with load shape information to the population feeder tree.'''
	for x in commercial_dict.keys():
		load_name = commercial_dict[x]['name']
		load_parent = commercial_dict[x]['parent']
		phases = commercial_dict[x]['phases']
		nom_volt = commercial_dict[x]['nom_volt']
		bp_A = commercial_dict[x]['load'][0]*config_data['normalized_loadshape_scalar']
		bp_B = commercial_dict[x]['load'][1]*config_data['normalized_loadshape_scalar']
		bp_C = commercial_dict[x]['load'][2]*config_data['normalized_loadshape_scalar']
		loadshape_dict[last_key] = {    'object' : 'load',
			'name' : '{:s}_loadshape'.format(load_name),
			'phases' : phases,
			'nominal_voltage' : nom_volt}
		if load_parent != 'None':
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
	return (loadshape_dict, last_key)

def _TechnologyParametersFunc(use_flags, TechToTest):
	'''create parameters necessary for technology use cases'''
	#TODO: Can we get rid of this function and this tech parameters concept?
	data = {'tech_flag' : TechToTest,
		'use_tech' : 0,
		'measure_losses' : 0,
		'dump_bills' : 0,
		'measure_capacitor' : 0,
		'measure_regulators' : 0,
		'collect_setpoints' : 0,
		'measure_EOL_voltage' : 0,
		'measure_loads' : 0,
		'include_stats' : 0,
		'meter_consumption' : 0,
		'dump_voltage' : 0,
		'measure_market' : 0,
		'get_IEEE_stats' : 0,
		'ts_SOC' : 0,
		'k_ts' : 0}
	data["tech_flag"] = TechToTest;
	data["use_tech"] = 0;
	# initialize use_flags
	use_flags = {    'use_normalized_loadshapes' : 0,
		'use_homes' : 0,
		'use_commercial' : 0,
		'use_billing' : 0,
		'use_capacitor_outtages' : 0,
		'use_vvc' : 0,
		'use_emissions' : 0,
		'use_market' : 0,
		'use_ts' : 0,
		'use_solar' : 0,
		'use_solar_res' : 0,
		'use_solar_com' : 0,
		'use_battery' : 0,
		'use_phev' : 0,
		'use_da' : 0,
		'use_wind' : 0}
	# quick case. Use load shapes instead of house objects.
	if TechToTest == -1:
		use_flags["use_normalized_loadshapes"] = 1
		use_flags["use_homes"] = 1
		use_flags["use_commercial"] = 1
		# These will include recorders/collectors/dumps
		data["measure_losses"] = 1;    
		data["collect_setpoints"] = 1;    
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1
		# Adds in meter consumption
		data["meter_consumption"] = 1
		#Set to '1' only for testing
		data["dump_voltage"] = 0; 
		data["measure_market"] = 0
		data["get_IEEE_stats"] = 0
	# base case
	if TechToTest == 0:
		# These will all be '1' for base case
		# homes and commercial are need to include these objects
		use_flags["use_homes"] = 1
		use_flags["use_commercial"] = 1
		# These will include recorders/collectors/dumps
		data["measure_losses"] = 1;    
		data["collect_setpoints"] = 1;    
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1
		# Adds in meter consumption
		data["meter_consumption"] = 1
		#Set to '1' only for testing
		data["dump_voltage"] = 0; 
		data["measure_market"] = 0
		data["get_IEEE_stats"] = 0
	# CVR
	elif data["tech_flag"] == 1:
		#These will all be '1' for base case
		# homes and commercial are need to include these objects
		use_flags["use_homes"] = 1
		use_flags["use_commercial"] = 1
		# These will include recorders/collectors/dumps
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		use_flags["use_vvc"] = 1;
		data["measure_losses"] = 1; 
		data["measure_capacitors"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_EOL_voltage"] = 1;
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1;
		# Adds in meter consumption
		data["meter_consumption"] = 1;
		#Set to '1' only for testing
		data["dump_voltage"] = 0;   
		data["measure_market"] = 0;
		data["get_IEEE_stats"] = 0;
	# Automation
	elif data["tech_flag"] == 2:
		#These will all be '1' for base case
		# homes and commercial are need to include these objects
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		# These will include recorders/collectors/dumps
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["measure_capacitors"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_EOL_voltage"] = 1;
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1;
		# Adds in meter consumption
		data["meter_consumption"] = 1;
		#Set to '1' only for testing
		data["dump_voltage"] = 0;   
		data["measure_market"] = 0;
		data["get_IEEE_stats"] = 0;
	# FDIR
	elif data["tech_flag"] == 3:
		print("FDIR not implemented yet")
		pass
	# TOU/CPP w/ tech
	elif data["tech_flag"] == 4:
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		use_flags["use_billing"] = 3;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_capacitors"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_loads"] = 1;
		# adds in the market
		use_flags["use_market"] = 2;
		# adds in customer/technology interactions
		data["use_tech"] = 1;
		data["include_stats"] = 1;
		data["meter_consumption"] = 2;
		data["dump_voltage"] = 0;   
		data["measure_market"] = 1;
		data["get_IEEE_stats"] = 0;
	# TOU/CPP w/o tech
	elif data["tech_flag"] == 5:
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		use_flags["use_billing"] = 3;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_capacitors"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_loads"] = 1;
		data["include_stats"] = 1;
		use_flags["use_market"] = 2;
		data["meter_consumption"] = 2;
		data["dump_voltage"] = 0;   
		data["measure_market"] = 1;
		data["get_IEEE_stats"] = 0;
	# TOU w/ tech
	elif data["tech_flag"] == 6:
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		use_flags["use_billing"] = 3;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_capacitors"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_loads"] = 1;
		data["include_stats"] = 1;
		use_flags["use_market"] = 1;
		data["use_tech"] = 1;
		data["meter_consumption"] = 2;
		data["dump_voltage"] = 0;   
		data["measure_market"] = 1;
		data["get_IEEE_stats"] = 0;
	# TOU w/o tech
	elif data["tech_flag"] == 7:
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		use_flags["use_billing"] = 3;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_capacitors"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_loads"] = 1;
		data["include_stats"] = 1;
		use_flags["use_market"] = 1;
		data["meter_consumption"] = 2;
		data["dump_voltage"] = 0;   
		data["measure_market"] = 1;
		data["get_IEEE_stats"] = 0;
	# DLC
	elif data["tech_flag"] == 8:
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		use_flags["use_billing"] = 1;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_capacitors"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_loads"] = 1;
		data["include_stats"] = 1;
		use_flags["use_market"] = 1;
		data["meter_consumption"] = 2;
		data["dump_voltage"] = 0;   
		data["measure_market"] = 1;
		data["get_IEEE_stats"] = 0;
	# Thermal
	elif data["tech_flag"] == 9:
		#These will all be '1' for base case
		# homes and commercial are need to include these objects
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		# These will include recorders/collectors/dumps
		use_flags["use_billing"] = 1;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_capacitors"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_EOL_voltage"] = 1;
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1;
		# Adds in meter consumption
		data["meter_consumption"] = 1;
		#Set to '1' only for testing
		data["dump_voltage"] = 0;   
		data["measure_market"] = 0;
		data["get_IEEE_stats"] = 0;
		#Turn on energy storage
		#1 = add thermal storage using the defaults, 2 = add thermal storage with a randomized schedule, 0 = none
		#3 = add thermal storage to all houses using defaults, 4 = add thermal storage to all houses with a randomized schedule
		use_flags["use_ts"] = 2;
		#Set initial state of charge
		data["ts_SOC"] = 100;
		#Set thermal losses - no losses
		data["k_ts"] = 0;
	# PHEV
	elif data["tech_flag"] == 10:
		print("PHEV not implemented yet")
		pass
	# Solar Residential
	elif data["tech_flag"] == 11:
		#These will all be '1' for base case
		# homes and commercial are need to include these objects
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		# These will include recorders/collectors/dumps
		use_flags["use_billing"] = 1;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_EOL_voltage"] = 1;
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1;
		# Adds in meter consumption
		data["meter_consumption"] = 1;
		#Set to '1' only for testing
		data["dump_voltage"] = 0;   
		data["measure_market"] = 0;
		data["get_IEEE_stats"] = 0;
		#Turn on solar residential
		use_flags["use_solar_res"] = 1;
	# Solar Commercial
	elif data["tech_flag"] == 12:
		# These will all be '1' for base case
		# homes and commercial are need to include thse objects
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		# These will include recorders/collectors/dumps
		use_flags["use_billing"] = 1;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_EOL_voltage"] = 1;
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1;
		# Adds in meter consumption
		data["meter_consumption"] = 1;
		#Set to '1' only for testing
		data["dump_voltage"] = 0;   
		data["measure_market"] = 0;
		data["get_IEEE_stats"] = 0;
		#Turn on solar commercial
		use_flags["use_solar_com"] = 1;
	# Combined solar 
	elif data["tech_flag"] == 13:
		#These will all be '1' for base case
		# homes and commercial are need to include these objects
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		# These will include recorders/collectors/dumps
		use_flags["use_billing"] = 1;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_EOL_voltage"] = 1;
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1;
		# Adds in meter consumption
		data["meter_consumption"] = 1;
		#Set to '1' only for testing
		data["dump_voltage"] = 0;   
		data["measure_market"] = 0;
		data["get_IEEE_stats"] = 0;
		#Turn on solar combined (both comm & residential)
		use_flags["use_solar"] = 1; 
	# Wind Commercial
	elif data["tech_flag"] == 14:
		#These will all be '1' for base case
		# commercial are need to include thse objects
		use_flags["use_homes"] = 1;
		use_flags["use_commercial"] = 1;
		# These will include recorders/collectors/dumps
		use_flags["use_billing"] = 1;
		use_flags["use_emissions"] = 1;
		use_flags["use_capacitor_outtages"] = 1;
		data["measure_losses"] = 1; 
		data["dump_bills"] = 1;
		data["measure_regulators"] = 1;   
		data["collect_setpoints"] = 1;    
		data["measure_loads"] = 1;
		#Prints stats at bottom of GLM
		data["include_stats"] = 1;
		# Adds in meter consumption
		data["meter_consumption"] = 1;
		#Set to '1' only for testing
		data["dump_voltage"] = 0;   
		data["measure_market"] = 0;
		data["get_IEEE_stats"] = 0;
		#Turn on commercial wind
		use_flags["use_wind"] = 1;  
	## Use flags structure
	# 1. Use homes
	# 2. Use battery storage ~ has {0, 1, 2} by the looks of it
	# 3. Use markets
	# 4. Use commercial buildings
	# 5. Use vvc
	# 6. Use customer billing
	# 7. Use solar
	# 8. Use PHEV
	# 9. Use distribution automation
	#10. Use wind
	#11. Other parameters
	## Home parameters
	if use_flags["use_homes"] == 1:
		# ZIP fractions and their power factors - Residential
		#data["z_pf"] = 1;
		#data["i_pf"] = 1;
		#data["p_pf"] = 1;
		data["z_pf"] = 0.97;
		data["i_pf"] = 0.97;
		data["p_pf"] = 0.97;
		data["zfrac"] = 0.2;
		data["ifrac"] = 0.4;
		data["pfrac"] = 1 - data["zfrac"] - data["ifrac"];
		data["heat_fraction"] = 0.9;
		# waterheaters 1 = yes, 0 = no
		data["use_wh"] = 1; 
		# Meter data is from Itron type meters (Centrution vs. OpenWay)
		if (data["meter_consumption"] == 1):
			data["res_meter_cons"] = '1+7j'; # Electromechanical (VAr)
		elif (data["meter_consumption"] == 2):
			data["res_meter_cons"] = '2+11j';# AMI (VAr)
		else:
			data["res_meter_cons"] = 0;
		# There is no ZIP fraction assosciated with this variable
		data["light_scalar_res"] = 1;
	## Battery Parameters
	if (use_flags["use_battery"] == 2 or use_flags["use_battery"] == 1):
		data["battery_energy"] = 1000000; # 10 MWh
		data["battery_power"] = 250000; # 1.5 MW
		data["efficiency"] = 0.86;   #percent
		data["parasitic_draw"] = 10; #Watts
	## Market Parameters -- @todo
	# 1 - TOU
	# 2 - TOU/CPP
	# 3 - DLC
	if (use_flags["use_market"] != 0):
		# market name, 
		# period, 
		# mean, 
		# stdev, 
		# max slider setting (xrange: 0.001 - 1; NOTE: do not use zero;
		# name of the price player/schedule)
		# percent penetration,
		if (use_flags["use_market"] == 1):
			data["two_tier_cpp"] = 'false';     
		elif (use_flags["use_market"] == 2):
			data["two_tier_cpp"] = 'true';
		elif (use_flags["use_market"] == 3):
			pass
		if (data["use_tech"] == 1):
			data["daily_elasticity"] = 'daily_elasticity_wtech';
			data["sub_elas_12"] = -0.152; # TOU substitution elasticity (average)
			data["sub_elas_13"] = -0.222; # CPP substitution elasticity (average)
		else:
			data["daily_elasticity"] = 'daily_elasticity_wotech'; #weekend vs. weekday schedules for daily elasticity
			data["sub_elas_12"] = -0.076; # TOU substitution elasticity (average)
			data["sub_elas_13"] = -0.111; # CPP substitution elasticity (average)
		# A lot of these values aren't used, except in an RTP market
		data["market_info"] = ['Market_1', 900, 'avg24', 'std24', 1.0, 'price_player', 1.0]
	## Commercial building parameters
	if (use_flags["use_commercial"] == 0):
		# zip loads
		#data["c_z_pf"] = 1;
		data["c_z_pf"] = 0.97;
		#data["c_i_pf"] = 1;
		data["c_i_pf"] = 0.97;
		#data["c_p_pf"] = 1;
		data["c_p_pf"] = 0.97;
		data["c_zfrac"] = 0.2;
		data["c_ifrac"] = 0.4;
		data["c_pfrac"] = 1 - data["c_zfrac"] - data["c_ifrac"];
	elif (use_flags["use_commercial"] == 1):
		# buildings
		data["cooling_COP"] = 3;
		#data["c_z_pf"] = 1;
		data["c_z_pf"] = 0.97;
		#data["c_i_pf"] = 1;
		data["c_i_pf"] = 0.97;
		#data["c_p_pf"] = 1;
		data["c_p_pf"] = 0.97;
		data["c_zfrac"] = 0.2;
		data["c_ifrac"] = 0.4;
		data["c_pfrac"] = 1 - data["c_zfrac"] - data["c_ifrac"];
		# Meer data is from Itron type meters (Centrution vs. OpenWay)
		if (data["meter_consumption"] == 1):
			data["comm_meter_cons"] = '1+15j'; # Electromechanical (VAr)
		elif (data["meter_consumption"] == 2):
			data["comm_meter_cons"] = '4+21j';# AMI (VAr)
		else:
			data["comm_meter_cons"] = 0;
		# VA cutoff - loads below this value per phase are made into "light" loads
		data["load_cutoff"] = 5000; 
		# Uses commercial building ZIP fractions
		data["light_scalar_comm"] = 1;
	## VVC parameters
	if (use_flags["use_vvc"] == 1):
		#data["output_volt"] = 2401;  # voltage to regulate to - 2401::120
		print("ERROR: CVR is not implemented yet")
	## Customer billing parameters
	if (use_flags["use_billing"] == 1): #FLAT RATE
		data["monthly_fee"] = 10; # $
		data["comm_monthly_fee"] = 25;
		# Average rate by region from, merged using Viraj spreadsheet
		# EIA: http://www.eia.doe.gov/electricity/epm/table5_6_b.html
		#  Region 6 is HECO 2010 rates for Oahu
		data["flat_price"] = [0.1243, 0.1294, 0.1012, 0.1064, 0.1064, 0.2547]; # $ / kWh
		data["comm_flat_price"] = [0.1142,0.1112,0.0843,0.0923,0.0923,0.2227];
	elif(use_flags["use_billing"] == 2): #TIERED RATE
		data["monthly_fee"] = 10; # $
		data["flat_price"] = 0.1; # $ / kWh - first tier price
		data["tier_energy"] = 500; # kWh - the transition between 1st and 2nd tier
		data["second_tier_price"] = 0.08; # $ / kWh
	elif(use_flags["use_billing"] == 3): #RTP/TOU RATE - market must be activated
		data["monthly_fee"] = 10; # $
		data["comm_monthly_fee"] = 25;
		data["flat_price"] = [0.1243,0.1294,0.1012,0.1064,0.1064,0.2547]; # $ / kWh
		if (use_flags["use_market"] == 0):
			print('Error: Must use markets when applying use_billing == 3');
	## Solar parameters
	if (use_flags["use_solar"] ==1 or use_flags["use_solar_res"] == 1 or use_flags["use_solar_com"] == 1):
		data["Rated_Insolation"] = 92.902; #W/Sf for 1000 W/m2
		data["efficiency_solar"] = 0.2; 
		data["solar_averagepower"] = 4 #For solar residential
		data["solar_averagepower_stripmall"] = 10 #For solar stripmall
		data["solar_averagepower_office"] = 100 #For solar commercial (offices)
		data["solar_averagepower_bigbox"] = 100 #For solar commercial (bigbox)
	## PHEV parameters
	if (use_flags["use_phev"] == 1):
		print("ERROR: PHEV is not implemented yet")
	## DA parameters
	if (use_flags["use_da"] == 1):
		print("ERROR: DA is not implemented yet")
	## Wind parameters
	if (use_flags["use_wind"] == 1):
		print("ERROR: Wind is not implemented yet")
	## Emission parameters
	if (use_flags["use_emissions"]  == 1):
		data["Naturalgas_Conv_Eff"] = 8.16; #MBtu/MWh
		data["Coal_Conv_Eff"] = 10.41;
		data["Biomass_Conv_Eff"] = 12.93;
		data["Geothermal_Conv_Eff"] = 21.02;
		data["Hydroelectric_Conv_Eff"] = 0;
		data["Nuclear_Conv_Eff"] = 10.46;
		data["Wind_Conv_Eff"] = 0;
		data["Petroleum_Conv_Eff"] = 11.00;
		data["Solarthermal_Conv_Eff"] = 0;
		data["Naturalgas_CO2"] = 117.08; #lb/MBtu;
		data["Coal_CO2"] = 205.573;
		data["Biomass_CO2"] = 195;
		data["Geothermal_CO2"] = 120;
		data["Hydroelectric_CO2"] = 0;
		data["Nuclear_CO2"] = 0;
		data["Wind_CO2"] = 0;
		data["Petroleum_CO2"] = 225.13;
		data["Solarthermal_CO2"] = 0;
		data["Naturalgas_SO2"] = 0.001; #lb/MBtu;
		data["Coal_SO2"] = 0.1;
		data["Biomass_SO2"] = 0;
		data["Geothermal_SO2"] = 0.2;
		data["Hydroelectric_SO2"] = 0;
		data["Nuclear_SO2"] = 0;
		data["Wind_SO2"] = 0;
		data["Petroleum_SO2"] = 0.1;
		data["Solarthermal_SO2"] = 0;    
		data["Naturalgas_NOx"] = 0.0075; #lb/MBtu;
		data["Coal_NOx"] = 0.06; 
		data["Biomass_NOx"] = 0.08;
		data["Geothermal_NOx"] = 0;             
		data["Hydroelectric_NOx"] = 0;
		data["Nuclear_NOx"] = 0;                 
		data["Wind_NOx"] = 0;
		data["Petroleum_NOx"] = 0.04;
		data["Solarthermal_NOx"] = 0;
		data["cycle_interval"] = 15; #min
	## Other parameters    
	# simulation start and end times -> please use format: yyyy-mm-dd HH:MM:SS
	data["start_date"] = '2012-06-28 00:00:00'; #summer dates
	data["end_date"] = '2012-06-30 00:00:00';
	data["start_date2"] = '2012-01-03 00:00:00'; #winter dates
	data["end_date2"] = '2012-01-05 00:00:00';
	data["start_date3"] = '2012-04-10 00:00:00'; #spring dates
	data["end_date3"] = '2012-04-12 00:00:00';
	# How often do you want to measure?
	#data["meas_interval"] = 900;  #applies to everything
	data["meas_interval"] = 300; # 5 minute intervals
	# @todo: fix 'datenum'
	#meas = datenum(data["end_date"]) - datenum(data["start_date"]); #days between start and end
	meas = 10000
	meas2 = meas*24*60*60;  #seconds between start and end dates
	data["meas_limit"] = int(20*math.ceil(meas2/data["meas_interval"]));
	# Skews
	data["residential_skew_max"] = 8100; # 2hr 15min
	data["commercial_skew_std"] = 1800; #These are in 30 minute blocks
	data["commercial_skew_max"] = 5400;
	data["tech_number"] = data["tech_flag"];
	# end nasty long copy/paste block
	return (data, use_flags)

def _ConfigurationFunc(wdir, config_file, classification=None):
	'''Create the complete configuration dictionary needed to populate the feeder'''
	data = {}
	if config_file == None:    
		data["timezone"] = 'PST+8PDT'
		data['startdate'] = '2014-01-01 0:00:00'
		data['stopdate'] = '2015-01-01 0:00:00'
		data["region"] = 4
		# Feeder Properties
		# - Substation Rating in MVA (Additional 15% gives rated kW & pf = 0.87)
		# - Nominal Voltage of Feeder Trunk
		# - Secondary (Load Side) of Transformers
		# - Voltage Players Read Into Swing Node
		data["feeder_rating"] = 1.15*14.0
		data["nom_volt"] = 14400
		vA='../schedules/VA.player'
		vB='../schedules/VB.player'
		vC='../schedules/VC.player'
		data["voltage_players"] = ['"{:s}"'.format(vA),'"{:s}"'.format(vB),'"{:s}"'.format(vC)]
		# Voltage Regulation
		# - EOL Measurements (name of node, phases to measure (i.e. ['GC-12-47-1_node_7','ABC',1]))
		# - Voltage Regulationn ( [desired, min, max, high deadband, low deadband] )
		# - Regulators (list of names)
		# - Capacitor Outages ( [name of capacitor, outage player file])
		# - Peak Power of Feeder in kVA 
		data["EOL_points"] = []
		data["voltage_regulation"] = [14400, 12420, 15180, 60, 60]     
		data["regulators"] = []
		data["capacitor_outtage"] = []
		data["emissions_peak"] = 13910 # Peak in kVa base .85 pf of 29 (For emissions)
		# set dictionary values (for default case)
		data["avg_house"] = 15000
		data["avg_commercial"] = 35000
		# normalized load shape scalar
		data["normalized_loadshape_scalar"] = 1
		data["load_shape_norm"] = '../schedules/load_shape_player.player'
		if 'load_shape_norm' in data.keys() and data['load_shape_norm'] is not None:
			# commercial zip fractions for loadshapes
			data["c_z_pf"] = 0.97
			data["c_i_pf"] = 0.97
			data["c_p_pf"] = 0.97
			data["c_zfrac"] = 0.2
			data["c_ifrac"] = 0.4
			data["c_pfrac"] = 1 - data["c_zfrac"] - data["c_ifrac"]
			# residential zip fractions for loadshapes
			data["r_z_pf"] = 0.97
			data["r_i_pf"] = 0.97
			data["r_p_pf"] = 0.97
			data["r_zfrac"] = 0.2
			data["r_ifrac"] = 0.4
			data["r_pfrac"] = 1 - data["r_zfrac"] - data["r_ifrac"]
		data["weather"] = '../schedules/SCADA_weather_NC_gld_shifted.csv'
	else:
		if 'timezone' in config_file.keys():
			data['timezone'] = config_file['timezone']
		else:
			data["timezone"] = 'PST+8PDT'
		if 'startdate' in config_file.keys():
			data['startdate'] = config_file['startdate']
		else:
			data['startdate'] = '2014-01-01 0:00:00'
		if 'stopdate' in config_file.keys():
			data['stopdate'] = config_file['stopdate']
		else:
			data['stopdate'] = '2015-01-01 0:00:00'
		if 'region' in config_file.keys():
			data['region'] = config_file['region']
		else:
			data["region"] = 4
		if 'feeder_rating' in config_file.keys():
			data['feeder_rating'] = config_file['feeder_rating']
		else:
			data["feeder_rating"] = 1.15*14.0
		if 'nom_volt' in config_file.keys():
			data['nom_volt'] = config_file['nom_volt']
		else:
			data["nom_volt"] = 14400
		if 'voltage_players' in config_file.keys():
			data['voltage_players'] = config_file['voltage_players']
		else:
			vA='../schedules/VA.player'
			vB='../schedules/VB.player'
			vC='../schedules/VC.player'
			data["voltage_players"] = ['"{:s}"'.format(vA),'"{:s}"'.format(vB),'"{:s}"'.format(vC)]
		if 'EOL_points' in config_file.keys():
			data['EOL_points'] = config_file['EOL_points']
		else:
			data["EOL_points"] = []
		if 'voltage_regulation' in config_file.keys():
			data['voltage_regulation'] = config_file['voltage_regulation']
		else:
			data["voltage_regulation"] = [14400, 12420, 15180, 60, 60]
		if 'regulators' in config_file.keys():
			data['regulators'] = config_file['regulators']
		else:
			data["capacitor_outtage"] = []
		if 'regulators' in config_file.keys():
			data['capacitor_outtage'] = config_file['capacitor_outtage']
		else:
			data["capacitor_outtage"] = []
		if 'emissions_peak' in config_file.keys():
			data['emissions_peak'] = config_file['emissions_peak']
		else:
			data["emissions_peak"] = 13910 # Peak in kVa base .85 pf of 29 (For emissions)
		if 'avg_house' in config_file.keys():
			data["avg_house"] = config_file['avg_house']
		else:
			data["avg_house"] = 15000
		if 'avg_comm' in config_file.keys():
			data["avg_commercial"] = config_file['avg_comm']
		else:
			data["avg_commercial"] = 35000
		if "load_shape_scalar" in config_file.keys():
			data["normalized_loadshape_scalar"] = config_file['load_shape_scalar']
		else:
			data["normalized_loadshape_scalar"] = 1
		if 'load_shape_player_file' in config_file.keys():
			data['load_shape_norm'] = config_file['load_shape_player_file']
		else:
			data["load_shape_norm"] = '../schedules/load_shape_player.player'
		if 'load_shape_norm' in data.keys() and data['load_shape_norm'] is not None:
			# commercial zip fractions for loadshapes
			data["c_z_pf"] = 0.97
			data["c_i_pf"] = 0.97
			data["c_p_pf"] = 0.97
			data["c_zfrac"] = 0.2
			data["c_ifrac"] = 0.4
			data["c_pfrac"] = 1 - data["c_zfrac"] - data["c_ifrac"]
			# residential zip fractions for loadshapes
			data["r_z_pf"] = 0.97
			data["r_i_pf"] = 0.97
			data["r_p_pf"] = 0.97
			data["r_zfrac"] = 0.2
			data["r_ifrac"] = 0.4
			data["r_pfrac"] = 1 - data["r_zfrac"] - data["r_ifrac"]
		if 'weather_file' in config_file.keys():
			data['weather'] = config_file['weather_file']
		else:
			data["weather"] = '../schedules/SCADA_weather_NC_gld_shifted.csv'
	return data

def startPopulation(glmDict,case_flag,wdir,configuration_file=None):
	'''glmDict is a dictionary containing all the objects in WindMIL model represented as equivalent GridLAB-D objects
	case_flag is an integer indicating which technology case to tack on to the GridLAB-D model
		case_flag : technology
	  -1 : Loadshape Case
		0 : Base Case
		1 : CVR
		2 : Automation
		3 : FDIR
		4 : TOU/CPP w/ tech
		5 : TOU/CPP w/o tech
		6 : TOU w/ tech
		7 : TOU w/o tech
		8 : DLC
		9 : Thermal Storage
	  10 : PHEV
	  11 : Solar Residential
	  12 : Solar Commercial
	  13 : Solar Combined
	configuration_file is the name of the file to use for getting feeder information
	GLD_Feeder returns a dictionary, glmCaseDict, similar to glmDict with additional object dictionaries added according to the case_flag selected.'''
	random.seed(1)
	# Check to make sure we have a valid case flag
	if case_flag < -1:
		case_flag = 0
	if case_flag > 13:
		case_flag = 13
	# Get information about each feeder from Configuration() and  TechnologyParameters()
	config_data = _ConfigurationFunc(wdir,configuration_file,None)
	#set up default flags
	use_flags = {}
	tech_data,use_flags = _TechnologyParametersFunc(use_flags,case_flag)
	tmy = config_data['weather']
	#find name of swingbus of static model dictionary
	hit = 0
	for x in glmDict:
		if hit < 1 and 'bustype' in glmDict[x] and glmDict[x]['bustype'] == 'SWING':
			hit = 1
			swing_bus_name = glmDict[x]['name']
			nom_volt = glmDict[x]['nominal_voltage'] # Nominal voltage in V
	# Create new case dictionary
	glmCaseDict = {}
	last_key = len(glmCaseDict)
	# Create clock dictionary
	glmCaseDict[last_key] = {    'clock' : '',
		'timezone' : '{:s}'.format(config_data['timezone']),
		'starttime' : "'{:s}'".format(config_data['startdate']),
		'stoptime' : "'{:s}'".format(config_data['stopdate'])}
	last_key += 1
	# Create dictionaries of preprocessor directives
	glmCaseDict[last_key] = {'#define' : 'stylesheet=http://gridlab-d.svn.sourceforge.net/viewvc/gridlab-d/trunk/core/gridlabd-2_0'}
	last_key += 1
	glmCaseDict[last_key] = {'#set' : 'minimum_timestep=300'}
	last_key += 1
	glmCaseDict[last_key] = {'#set' : 'profiler=1'}
	last_key += 1
	glmCaseDict[last_key] = {'#set' : 'relax_naming_rules=1'}
	last_key += 1
	# Create dictionaries of modules to be used from the case_flag
	glmCaseDict[last_key] = {'module' : 'tape'}
	last_key += 1
	glmCaseDict[last_key] = {'module' : 'climate'}
	last_key += 1
	glmCaseDict[last_key] = {    'module' : 'powerflow',
		'solver_method' : 'NR',
		'NR_iteration_limit' : '50'}
	last_key += 1
	if use_flags['use_solar'] != 0 or use_flags['use_solar_res'] != 0 or use_flags['use_solar_com'] != 0 or use_flags['use_battery'] == 1 or use_flags['use_battery'] == 2:
		glmCaseDict[last_key] = {'module' : 'generators'}
		last_key += 1
	# Add the class player dictionary to glmCaseDict
	glmCaseDict[last_key] = {    'class' : 'player',
		'variable_types' : ['double'],
		'variable_names' : ['value']}
	last_key += 1
	if use_flags['use_normalized_loadshapes'] == 1:
		glmCaseDict[last_key] = {    'object' : 'player',
			'name' : 'norm_feeder_loadshape',
			'property' : 'value',
			'file' : '{:s}'.format(config_data['load_shape_norm']),
			'loop' : '14600',
			'comment' : '// Will loop file for 40 years assuming the file has data for a 24 hour period'}
		last_key += 1
	# Add climate dictionaries
	if '.csv' in tmy:
		# Climate file is a cvs file. Need to add csv_reader object
		glmCaseDict[last_key] = {    'object' : 'csv_reader',
													'name' : 'CsvReader',
													'filename' : '"{:s}"'.format(tmy)}
		last_key += 1
	elif '.tmy2' in tmy:
		glmCaseDict[last_key] = {    'object' : 'climate',
													'tmyfile' : '"{:s}"'.format(tmy)}
		if '.tmy2' in tmy:
			glmCaseDict[last_key]['interpolate'] = 'QUADRATIC'
		elif '.csv' in tmy:
			glmCaseDict[last_key]['reader'] = 'CsvReader'
		last_key += 1
	# Add substation transformer transformer_configuration
	glmCaseDict[last_key] = {    'object' : 'transformer_configuration',
		'name' : 'trans_config_to_feeder',
		'connect_type' : 'WYE_WYE',
		'install_type' : 'PADMOUNT',
		'primary_voltage' : '{:d}'.format(config_data['nom_volt']),
		'secondary_voltage' : '{:s}'.format(nom_volt),
		'power_rating' : '{:.1f} MVA'.format(config_data['feeder_rating']),
		'impedance' : '0.00033+0.0022j'}
	last_key += 1
	# Add CVR controller
	if use_flags['use_vvc'] == 1:
		# TODO: pull all of these out and put into TechnologyParameters()
		glmCaseDict[last_key] = {    'object' : 'volt_var_control',
			'name' : 'volt_var_control',
			'control_method' : 'ACTIVE',
			'capacitor_delay' : '60.0',
			'regulator_delay' : '60.0',
			'desired_pf' : '0.99',
			'd_max' : '0.8',
			'd_min' : '0.1',
			'substation_link' : 'substation_transfromer',
			'regulator_list' : '"{:s}"'.format(','.join(config_data['regulators'])), # config_data['regulators'] should contain a list of the names of the regulators that use CVR
			'maximum_voltage' : '{:.2f}'.format(config_data['voltage_regulation'][2]),
			'minimum_voltage' : '{:.2f}'.format(config_data['voltage_regulation'][1]),
			'max_vdrop' : '50',
			'high_load_deadband' :'{:.2f}'.format(config_data['voltage_regulation'][4]),
			'desired_voltages' : '{:.2f}'.format(config_data['voltage_regulation'][0]),
			'low_load_deadband' : '{:.2f}'.format(config_data['voltage_regulation'][3])}
		num_caps = len(config_data['capacitor_outage'])
		if num_caps > 0:
			glmCaseDict[last_key]['capacitor_list'] = '"'
			for x in xrange(num_caps):
				if x < (num_caps - 1):
					glmCaseDict[last_key]['capacitor_list'] = glmCaseDict[last_key]['capacitor_list'] + '{:s},'.format(config_data['capacitor_outage'][x][0])
				else:
					glmCaseDict[last_key]['capacitor_list'] = glmCaseDict[last_key]['capacitor_list'] + '{:s}"'.format(config_data['capacitor_outage'][x][0])
		else:
			glmCaseDict[last_key]['capacitor_list'] = '""'
		num_eol = len(config_data['EOL_points'])
		glmCaseDict[last_key]['voltage_measurements'] = '"'
		for x in xrange(num_eol):
			if x < (num_eol - 1):
				glmCaseDict[last_key]['voltage_measurements'] = glmCaseDict[last_key]['voltage_measurements'] + '{:s},{:d},'.format(config_data['EOL_points'][x][0],config_data['EOL_points'][x][2])
			else:
				glmCaseDict[last_key]['voltage_measurements'] = glmCaseDict[last_key]['voltage_measurements'] + '{:s},{:d}"'.format(config_data['EOL_points'][x][0],config_data['EOL_points'][x][2])
		last_key += 1
	# Add substation swing bus and substation transformer dictionaries
	glmCaseDict[last_key] = {    'object' : 'meter',
		'name' : 'network_node',
		'bustype' : 'SWING',
		'nominal_voltage' : '{:d}'.format(config_data['nom_volt']),
		'phases' : 'ABCN'}
	# Add transmission voltage players
	parent_key = last_key
	last_key += 1
	glmCaseDict[last_key] = {    'object' : 'player',
		'property' : 'voltage_A',
		'parent' : '{:s}'.format(glmCaseDict[parent_key]['name']),
		'loop' : '10',
		'file' : '{:s}'.format(config_data["voltage_players"][0])}
	last_key += 1
	glmCaseDict[last_key] = {    'object' : 'player',
		'property' : 'voltage_B',
		'parent' : '{:s}'.format(glmCaseDict[parent_key]['name']),
		'loop' : '10',
		'file' : '{:s}'.format(config_data["voltage_players"][1])}
	last_key += 1
	glmCaseDict[last_key] = {    'object' : 'player',
		'property' : 'voltage_C',
		'parent' : '{:s}'.format(glmCaseDict[parent_key]['name']),
		'loop' : '10',
		'file' : '{:s}'.format(config_data["voltage_players"][2])}
	last_key += 1
	glmCaseDict[last_key] = {    'object' : 'transformer',
		'name' : 'substation_transformer',
		'from' : 'network_node',
		'to' : '{:s}'.format(swing_bus_name),
		'phases' : 'ABCN',
		'configuration' : 'trans_config_to_feeder'}
	last_key += 1
	# Copy static powerflow model glm dictionary into case dictionary
	for x in glmDict:
		if 'clock' not in glmDict[x].keys() and '# set' not in glmDict[x].keys() and '# define' not in glmDict[x].keys() and 'module' not in glmDict[x].keys():
			glmCaseDict[last_key] = copy.deepcopy(glmDict[x])
			# Remove original swing bus from static model
			if 'bustype' in glmCaseDict[last_key] and glmCaseDict[last_key]['bustype'] == 'SWING':
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
	# Create dictionary that houses the number of commercial 'load' objects where commercial house objects will be tacked on.
	total_commercial_number = 0 # Variable that stores the total amount of houses that need to be added.
	commercial_dict = {}
	if use_flags['use_commercial'] == 1:
		commercial_key = 0
		for x in glmCaseDict:
			if 'object' in glmCaseDict[x] and glmCaseDict[x]['object'] == 'load':
				commercial_dict[commercial_key] = {    'name' : glmCaseDict[x]['name'],
					'parent' : 'None',
					'load_classification' : 'None',
					'load' : [0,0,0],
					'number_of_houses' : [0,0,0], #[phase A, phase B, phase C]
					'nom_volt' : glmCaseDict[x]['nominal_voltage'],
					'phases' : glmCaseDict[x]['phases']}
				if 'parent' in glmCaseDict[x]:
					commercial_dict[commercial_key]['parent'] = glmCaseDict[x]['parent']
				else:
					commercial_dict[commercial_key]['parent'] = glmCaseDict[x]['name']
				if 'load_class' in glmCaseDict[x]:
					commercial_dict[commercial_key]['load_classification'] = glmCaseDict[x]['load_class']
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
					load_A += pow(float(commercial_dict[commercial_key]['nom_volt']),2)/(3*abs(c_num))
				if 'constant_impedance_B' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_impedance_B'])
					load_B += pow(float(commercial_dict[commercial_key]['nom_volt']),2)/(3*abs(c_num))
				if 'constant_impedance_C' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_impedance_C'])
					load_C += pow(float(commercial_dict[commercial_key]['nom_volt']),2)/(3*abs(c_num))
				if 'constant_current_A' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_current_A'])
					load_A += float(commercial_dict[commercial_key]['nom_volt'])*(abs(c_num))
				if 'constant_current_B' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_current_B'])
					load_B += float(commercial_dict[commercial_key]['nom_volt'])*(abs(c_num))
				if 'constant_current_C' in glmCaseDict[x]:
					c_num = complex(glmCaseDict[x]['constant_current_C'])
					load_C += float(commercial_dict[commercial_key]['nom_volt'])*(abs(c_num))
				if load_A >= tech_data['load_cutoff']:
					commercial_dict[commercial_key]['number_of_houses'][0] = int(math.ceil(load_A/config_data['avg_commercial']))
					total_commercial_number += commercial_dict[commercial_key]['number_of_houses'][0]
				if load_B >= tech_data['load_cutoff']:
					commercial_dict[commercial_key]['number_of_houses'][1] = int(math.ceil(load_B/config_data['avg_commercial']))
					total_commercial_number += commercial_dict[commercial_key]['number_of_houses'][1]
				if load_C >= tech_data['load_cutoff']:
					commercial_dict[commercial_key]['number_of_houses'][2] = int(math.ceil(load_C/config_data['avg_commercial']))
					total_commercial_number += commercial_dict[commercial_key]['number_of_houses'][2]
				commercial_dict[commercial_key]['load'][0] = load_A
				commercial_dict[commercial_key]['load'][1] = load_B
				commercial_dict[commercial_key]['load'][2] = load_C
				# TODO: Bypass this is load rating is known
				# Determine load_rating
				standard_transformer_rating = [10,15,25,37.5,50,75,100,150,167,250,333.3,500,666.7]
				total_load = (load_A + load_B + load_C)/1000
				load_rating = 0
				for y in standard_transformer_rating:
					if y >= total_load:
						load_rating = y
					elif y == 666.7:
						load_rating = y
				# Deterimine load classification
				if commercial_dict[commercial_key]['load_classification'].isdigit():
					commercial_dict[commercial_key]['load_classification'] = int(commercial_dict[commercial_key]['load_classification'])
				else: # load_classification is unknown determine from no_houses and transformer size
					#TODO: Determine what classID should be from no_houses and transformer size
					commercial_dict[commercial_key]['load_classification'] = None
					random_class_number = random.random()*100
					if load_rating == 10:
						commercial_dict[commercial_key]['load_classification'] = 6
					elif load_rating == 15:
						commercial_dict[commercial_key]['load_classification'] = 6
					elif load_rating == 25:
						if random_class_number <= 5:
							commercial_dict[commercial_key]['load_classification'] = 7
						elif 5 < random_class_number <= 11:
							commercial_dict[commercial_key]['load_classification'] = 8
						elif random_class_number > 11:
							commercial_dict[commercial_key]['load_classification'] = 6
					elif load_rating == 37.5:
						commercial_dict[commercial_key]['load_classification'] = 6
					elif load_rating == 50:
						if random_class_number <= 28:
							commercial_dict[commercial_key]['load_classification'] = 7
						elif 28 < random_class_number <= 61:
							commercial_dict[commercial_key]['load_classification'] = 8
						elif random_class_number > 61:
							commercial_dict[commercial_key]['load_classification'] = 6
					elif load_rating == 75:
						if random_class_number <= 18:
							commercial_dict[commercial_key]['load_classification'] = 6
						elif 18 < random_class_number <= 49:
							commercial_dict[commercial_key]['load_classification'] = 8
						elif random_class_number > 49:
							commercial_dict[commercial_key]['load_classification'] = 7
					elif load_rating == 100:
						if random_class_number <= 15:
							commercial_dict[commercial_key]['load_classification'] = 6
						elif 15 < random_class_number <= 56:
							commercial_dict[commercial_key]['load_classification'] = 7
						elif random_class_number > 56:
							commercial_dict[commercial_key]['load_classification'] = 8
					elif load_rating == 150:
						commercial_dict[commercial_key]['load_classification'] = 6
					elif load_rating == 167:
						if random_class_number <= 11:
							commercial_dict[commercial_key]['load_classification'] = 6
						elif 11 < random_class_number <= 43:
							commercial_dict[commercial_key]['load_classification'] = 8
						elif random_class_number > 43:
							commercial_dict[commercial_key]['load_classification'] = 7
					elif load_rating == 250:
						if random_class_number <= 27:
							commercial_dict[commercial_key]['load_classification'] = 7
						elif random_class_number > 27:
							commercial_dict[commercial_key]['load_classification'] = 8
					elif load_rating == 333.3:
						if random_class_number <= 17:
							commercial_dict[commercial_key]['load_classification'] = 7
						elif random_class_number > 17:
							commercial_dict[commercial_key]['load_classification'] = 8
					elif load_rating == 500:
						commercial_dict[commercial_key]['load_classification'] = 8
					elif load_rating == 666.7:
						if random_class_number <= 50:
							commercial_dict[commercial_key]['load_classification'] = 7
						elif random_class_number > 50:
							commercial_dict[commercial_key]['load_classification'] = 8
					else:
						if sum(commercial_dict[commercial_key]['number_of_houses']) >= 15:
							commercial_dict[commercial_key]['load_classification'] = 8
						elif sum(commercial_dict[commercial_key]['number_of_houses']) >= 6:
							commercial_dict[commercial_key]['load_classification'] = 7
						elif sum(commercial_dict[commercial_key]['number_of_houses']) > 0:
							commercial_dict[commercial_key]['load_classification'] = 6
						else:
							commercial_dict[commercial_key]['load_classification'] = None
				# Replace load with a node remove constant load keys
				glmCaseDict[x]['object'] = 'node'
				if 'load_class' in glmCaseDict[x]:
					del glmCaseDict[x]['load_class'] # Must remove load_class as it isn't a published property
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
	# Create dictionary that houses the number of residential 'load' objects where residential house objects will be tacked on.
	total_house_number = 0
	residential_dict = {}
	if use_flags['use_homes'] == 1:
		residential_key = 0
		for x in glmCaseDict:
			if 'object' in glmCaseDict[x] and glmCaseDict[x]['object'] == 'triplex_node':
				if 'power_1' in glmCaseDict[x] or 'power_12' in glmCaseDict[x]:
					residential_dict[residential_key] = {    'name' : glmCaseDict[x]['name'],
						'parent' : 'None',
						'load_classification' : 'None',
						'number_of_houses' : 0,
						'load' : 0,
						'large_vs_small' : 0.0,
						'phases' : glmCaseDict[x]['phases']}
					if 'parent' in glmCaseDict[x]:
						residential_dict[residential_key]['parent'] = glmCaseDict[x]['parent']
					else:
						residential_dict[residential_key]['parent'] = glmCaseDict[x]['name']
					if 'load_class' in glmCaseDict[x]:
						residential_dict[residential_key]['load_classification'] = glmCaseDict[x]['load_class']
					# Figure out how many houses should be attached to this load object
					load = 0
					# determine the total ZIP load for each phase
					if 'power_1' in glmCaseDict[x]:
						c_num = complex(glmCaseDict[x]['power_1'])
						load += abs(c_num)
					if 'power_12' in glmCaseDict[x]:
						c_num = complex(glmCaseDict[x]['power_12'])
						load += abs(c_num)
					residential_dict[residential_key]['load'] = load    
					residential_dict[residential_key]['number_of_houses'] = int(round(load/config_data['avg_house']))
					total_house_number += residential_dict[residential_key]['number_of_houses']
					# Determine whether we rounded down of up to help determine the square footage (neg. number => small homes)
					residential_dict[residential_key]['large_vs_small'] = load/config_data['avg_house'] - residential_dict[residential_key]['number_of_houses']
					# Determine load_rating
					standard_transformer_rating = [10,15,25,37.5,50,75,100,150,167,250,333.3,500,666.7]
					total_load = load/1000
					load_rating = 0
					for y in standard_transformer_rating:
						if y >= total_load:
							load_rating = y
						elif y == 666.7:
							load_rating = y
					# Deterimine load classification
					if residential_dict[residential_key]['load_classification'].isdigit():
						residential_dict[residential_key]['load_classification'] = int(residential_dict[residential_key]['load_classification'])
					else: # load_classification is unknown determine from no_houses and transformer size
						#TODO: Determine what classID should be from no_houses and transformer size
						residential_dict[residential_key]['load_classification'] = None
						random_class_number = random.random()*100
						if load_rating == 10:
							if random_class_number <= 6:
								residential_dict[residential_key]['load_classification'] = 5
							elif 6 < random_class_number <= 24:
								residential_dict[residential_key]['load_classification'] = 0
							elif random_class_number > 24:
								residential_dict[residential_key]['load_classification'] = 1
						elif load_rating == 15:
							if random_class_number <= 14:
								residential_dict[residential_key]['load_classification'] = 1
							elif 14 < random_class_number <= 57:
								residential_dict[residential_key]['load_classification'] = 0
							elif random_class_number > 57:
								residential_dict[residential_key]['load_classification'] = 5
						elif load_rating == 25:
							if random_class_number <= 1.5:
								residential_dict[residential_key]['load_classification'] = 2
							elif 1.5 < random_class_number <= 3.7:
								residential_dict[residential_key]['load_classification'] = 3
							elif 3.7 < random_class_number <= 16.6:
								residential_dict[residential_key]['load_classification'] = 5
							elif 16.6 < random_class_number <= 38.7:
								residential_dict[residential_key]['load_classification'] = 0
							elif random_class_number > 38.7:
								residential_dict[residential_key]['load_classification'] = 1
						elif load_rating == 37.5:
							residential_dict[residential_key]['load_classification'] = 2
						elif load_rating == 50:
							if random_class_number <= 3.1:
								residential_dict[residential_key]['load_classification'] = 2
							elif 3.1 < random_class_number <= 16.7:
								residential_dict[residential_key]['load_classification'] = 5
							elif 16.7 < random_class_number <= 30.6:
								residential_dict[residential_key]['load_classification'] = 0
							elif 30.6 < random_class_number <= 51.6:
								residential_dict[residential_key]['load_classification'] = 3
							elif random_class_number > 51.6:
								residential_dict[residential_key]['load_classification'] = 1
						elif load_rating == 75:
							if random_class_number <= 7.9:
								residential_dict[residential_key]['load_classification'] = 1
							elif 7.9 < random_class_number <= 15.8:
								residential_dict[residential_key]['load_classification'] = 2
							elif 15.8 < random_class_number <= 26.2:
								residential_dict[residential_key]['load_classification'] = 0
							elif 26.2 < random_class_number <= 56.7:
								residential_dict[residential_key]['load_classification'] = 5
							elif random_class_number > 56.7:
								residential_dict[residential_key]['load_classification'] = 3
						elif load_rating == 100:
							if random_class_number <= 4:
								residential_dict[residential_key]['load_classification'] = 1
							elif 4 < random_class_number <= 12:
								residential_dict[residential_key]['load_classification'] = 0
							elif 12 < random_class_number <= 38:
								residential_dict[residential_key]['load_classification'] = 3
							elif 38 < random_class_number <= 68:
								residential_dict[residential_key]['load_classification'] = 2
							elif random_class_number > 68:
								residential_dict[residential_key]['load_classification'] = 5
						elif load_rating == 167:
							if random_class_number <= 1:
								residential_dict[residential_key]['load_classification'] = 1
							elif 1 < random_class_number <= 2:
								residential_dict[residential_key]['load_classification'] = 2
							elif 2 < random_class_number <= 4:
								residential_dict[residential_key]['load_classification'] = 0
							elif 4 < random_class_number <= 13:
								residential_dict[residential_key]['load_classification'] = 3
							elif random_class_number > 13:
								residential_dict[residential_key]['load_classification'] = 5
						else:
							residential_dict[residential_key]['load_classification'] = random.choice([0, 1, 2, 3, 4, 5]) # randomly pick between the 6 residential classifications
					# Remove constant load keys
					if 'load_class' in glmCaseDict[x]:
						del glmCaseDict[x]['load_class'] # Must remove load_class as it isn't a published property
					if 'power_12' in glmCaseDict[x]:
						del glmCaseDict[x]['power_12']
					if 'power_1' in glmCaseDict[x]:
						del glmCaseDict[x]['power_1']
					if total_house_number == 0 and load > 0 and use_flags['use_normalized_loadshapes'] == 0: # Residential street light
						glmCaseDict[x]['power_12_real'] = 'street_lighting*{:.4f}'.format(c_num.real*tech_data['light_scalar_res'])
						glmCaseDict[x]['power_12_reac'] = 'street_lighting*{:.4f}'.format(c_num.imag*tech_data['light_scalar_res'])
					residential_key += 1
	# Tack on residential loads
	if use_flags['use_homes'] != 0:
		#print('calling ResidentialLoads.py\n')
		if use_flags['use_normalized_loadshapes'] == 1:
			glmCaseDict, last_key = _add_normalized_residential_ziploads(glmCaseDict, residential_dict, config_data, last_key)
	# End addition of residential loads ########################################################################################################################
	if use_flags['use_commercial'] != 0:
		#print('calling CommercialLoads.py\n')
		if use_flags['use_normalized_loadshapes'] == 1:
			glmCaseDict, last_key = _add_normalized_commercial_ziploads(glmCaseDict, commercial_dict, config_data, last_key)
	return glmCaseDict, last_key

def _append_solar():
	# NOTE: deleted, find in git history in Solar_Technology.py.
	pass

def _append_residential():
	# NOTE: deleted, find in git history in ResidentialLoads.py.
	pass

def _append_commercial():
	# NOTE: deleted, find in git history in CommercialLoads.py.
	pass

def _test():
	import sys, os
	sys.path.append('..')
	import feeder
	glmbase = feeder.parse('./uploads/IEEE-13.glm')
	feeder_config = {    'timezone' : 'EST+5EDT',
		'startdate' : '2013-01-01 0:00:00',
		'stopdate' : '2014-01-01 0:00:00',
		'region' : 6,
		'feeder_rating' : 600,
		'nom_volt' : 66395,
		'voltage_players' : ['./uploads/VA.player', './uploads/VB.player', './uploads/VC.player'],
		'loadshape_scalar' : 1.1,
		'load_shape_player_file' : './uploads/load_shape_player.player',
		'weather_file' : './uploads/SCADA_weather_NC_gld_shifted.csv'}
	glmpopulated, last_key = startPopulation(glmbase, -1, feeder_config, None)
	assert 75776==last_key

if __name__ == '__main__':
	_test()
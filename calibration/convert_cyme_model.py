'''
Created on Nov 19, 2013

@author: fish334
'''
import pyodbc
import feeder
import os
import re
import csv
import shutil
import math
import cmath
import copy
import add_glm_object_dictionary
import warnings

    #glm_parameters is a list containing all the user inputs for the object in a certain order as strings
        # node
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'parent'
        #    3 : 'bustype'
        #    4 : 'phases'
        #    5 : 'nominal_voltage'
        #    6 : 'comments'
        
        # meter
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'parent'
        #    3 : 'bustype'
        #    4 : 'phases'
		#	5 : 'voltage_A'
		#	6 : 'voltage_B'
		#	7 : 'voltage_C'
        #    8 : 'nominal_voltage'
        #    9 : 'comments'
        
        # load
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'parent'
        #    3 : 'bustype'
        #    4 : 'phases'
        #    5 : 'nominal_voltage'
        #    6 : 'load_class'
        #    7 : 'constant_power_A'
        #    8 : 'constant_power_B'
        #    9 : 'constant_power_C'
        #    10 : 'constant_current_A'
        #    11 : 'constant_current_B'
        #    12 : 'constant_current_C'
        #    13 : 'constant_impedance_A'
        #    14 : 'constant_impedance_B'
        #    15 : 'constant_impedance_C'
        #    16 : 'base_power_A'
        #    17 : 'base_power_B'
        #    18 : 'base_power_C'
        #    19 : 'power_pf_A'
        #    20 : 'power_pf_B'
        #    21 : 'power_pf_C'
        #    22 : 'current_pf_A'
        #    23 : 'current_pf_B'
        #    24 : 'current_pf_C'
        #    25 : 'impedance_pf_A'
        #    26 : 'impedance_pf_B'
        #    27 : 'impedance_pf_C'
        #    28 : 'power_fraction_A'
        #    29 : 'power_fraction_B'
        #    30 : 'power_fraction_C'
        #    31 : 'current_fraction_A'
        #    32 : 'current_fraction_B'
        #    33 : 'current_fraction_C'
        #    34 : 'impedance_fraction_A'
        #    35 : 'impedance_fraction_B'
        #    36 : 'impedance_fraction_C'
        #    37 : 'comments'
        
        # triplex_node
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'parent'
        #    3 : 'bustype'
        #    4 : 'phases'
        #    5 : 'nominal_voltage'
        #    6 : 'power_12'
        #    7 : 'comments'
        
        # triplex_meter
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'parent'
        #    3 : 'bustype'
        #    4 : 'phases'
        #    5 : 'nominal_voltage'
        #    6 : 'comments'
        
        # triplex_load
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'parent'
        #    3 : 'bustype'
        #    4 : 'phases'
        #    5 : 'nominal_voltage'
        #    6 : 'load_class'
        #    7 : 'constant_power_1'
        #    8 : 'constant_power_2'
        #    9 : 'constant_power_12'
        #    10 : 'constant_current_1'
        #    11 : 'constant_current_2'
        #    12 : 'constant_current_12'
        #    13 : 'constant_impedance_1'
        #    14 : 'constant_impedance_2'
        #    15 : 'constant_impedance_12'
        #    16 : 'base_power_1'
        #    17 : 'base_power_2'
        #    18 : 'base_power_12'
        #    19 : 'power_pf_1'
        #    20 : 'power_pf_2'
        #    21 : 'power_pf_12'
        #    22 : 'current_pf_1'
        #    23 : 'current_pf_2'
        #    24 : 'current_pf_12'
        #    25 : 'impedance_pf_1'
        #    26 : 'impedance_pf_2'
        #    27 : 'impedance_pf_12'
        #    28 : 'power_fraction_1'
        #    29 : 'power_fraction_2'
        #    30 : 'power_fraction_12'
        #    31 : 'current_fraction_1'
        #    32 : 'current_fraction_2'
        #    33 : 'current_fraction_12'
        #    34 : 'impedance_fraction_1'
        #    35 : 'impedance_fraction_2'
        #    36 : 'impedance_fraction_12'
        #    37 : 'comments'
        
        # capacitor
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'parent'
        #    3 : 'phases'
        #    4 : 'nominal_voltage'
        #    5 : 'pt_phase'
        #    6 : 'phases_connected'
        #    7 : 'switchA'
        #    8 : 'switchB'
        #    9 : 'switchC'
        #    10 : 'control'
        #    11 : 'voltage_set_high'
        #    12 : 'voltage_set_low'
        #    13 : 'VAr_set_high'
        #    14 : 'VAr_set_low'
        #    15 : 'current_set_high'
        #    16 : 'current_set_low'
        #    17 : 'capacitor_A'
        #    18 : 'capacitor_B'
        #    19 : 'capacitor_C'
        #    20 : 'cap_nominal_voltage'
        #    21 : 'time_delay'
        #    22 : 'dwell_time'
        #    23 : 'lockout_time'
        #    24 : 'remote_sense'
        #    25 : 'remote_sense_B'
        #    26 : 'control_level'
        #    27 : 'comments'
        
        # fuse
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'phases'
        #    3 : 'from'
        #    4 : 'to'
        #    5 : 'phase_A_status'
        #    6 : 'phase_B_status'
        #    7 : 'phase_C_status'
        #    8 : 'repair_dist_type'
        #    9 : 'current_limit'
        #    10 : 'mean_replacement_time'
        #    11 : 'comments'
		#    12 : 'status'
        
        # switch
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'phases'
        #    3 : 'from'
        #    4 : 'to'
        #    5 : 'phase_A_state'
        #    6 : 'phase_B_state'
        #    7 : 'phase_C_state'
        #    8 : 'operating_mode'
        #    9 : 'comments'
        
        # overhead_line
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'phases'
        #    3 : 'from'
        #    4 : 'to'
        #    5 : 'length'
        #    6 : 'configuration'
        #    7 : 'comments'
        
        # underground_line
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'phases'
        #    3 : 'from'
        #    4 : 'to'
        #    5 : 'length'
        #    6 : 'configuration'
        #    7 : 'comments'
        
        # triplex_line
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'phases'
        #    3 : 'from'
        #    4 : 'to'
        #    5 : 'length'
        #    6 : 'configuration'
        #    7 : 'comments'
        
        # transformer
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'phases'
        #    3 : 'from'
        #    4 : 'to'
        #    5 : 'configuration'
        #    6 : 'climate'
        #    7 : 'aging_constant'
        #    8 : 'use_thermal_model'
        #    9 : 'aging_granularity'
        #    10 : 'comments'
        
        # regulator
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'phases'
        #    3 : 'from'
        #    4 : 'to'
        #    5 : 'configuration'
        #    6 : 'sense_node'
        #    7 : 'comments'
        
        # line_configuration
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'conductor_A'
        #    3 : 'conductor_B'
        #    4 : 'conductor_C'
        #    5 : 'conductor_N'
        #    6 : 'spacing'
        #    7 : 'z11'
        #    8 : 'z12'
        #    9 : 'z13'
        #    10 : 'z21'
        #    11 : 'z22'
        #    12 : 'z23'
        #    13 : 'z31'
        #    14 : 'z32'
        #    15 : 'z33'
        #    16 : 'comments'
        
        # triplex_line_configuration
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'conductor_1'
        #    3 : 'conductor_2'
        #    4 : 'conductor_N'
        #    5 : 'insulation_thickness'
        #    6 : 'diameter'
        #    7 : 'spacing'
        #    8 : 'z11'
        #    9 : 'z12'
        #    10 : 'z21'
        #    11 : 'z22'
        #    12 : 'comments'
        
        # transformer_configuration
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'connect_type'
        #    3 : 'install_type'
        #    4 : 'coolant_type'
        #    5 : 'cooling_type'
        #    6 : 'primary_voltage'
        #    7 : 'secondary_voltage'
        #    8 : 'power_rating'
        #    9 : 'powerA_rating'
        #    10 : 'powerB_rating'
        #    11 : 'powerC_rating'
        #    12 : 'impedance'
        #    13 : 'shunt_impedance'
        #    14 : 'core_coil_weight'
        #    15 : 'tank_fittings_weight'
        #    16 : 'oil_volume'
        #    17 : 'rated_winding_time_constant'
        #    18 : 'rated_winding_hot_spot_rise'
        #    19 : 'rated_top_oil_rice'
        #    20 : 'no_load_loss'
        #    21 : 'full_load_loss'
        #    22 : 'reactance_resistance_ratio'
        #    23 : 'installed_insulation_life'
        #    24 : 'comments'
        
        # regulator_configuration
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'connect_type'
        #    3 : 'band_center'
        #    4 : 'band_width'
        #    5 : 'time_delay'
        #    6 : 'dwell_time'
        #    7 : 'raise_taps'
        #    8 : 'lower_taps'
        #    9 : 'current_transducer_ratio'
        #    10 : 'power_transducer_ratio'
        #    11 : 'compensator_r_setting_A'
        #    12 : 'compensator_x_setting_A'
        #    13 : 'compensator_r_setting_B'
        #    14 : 'compensator_x_setting_B'
        #    15 : 'compensator_r_setting_C'
        #    16 : 'compensator_x_setting_C'
        #    17 : 'CT_phase'
        #    18 : 'PT_phase'
        #    19 : 'regulation'
        #    20 : 'control_level'
        #    21 : 'Control'
        #    22 : 'Type'
        #    23 : 'tap_pos_A'
        #    24 : 'tap_pos_B'
        #    25 : 'tap_pos_C'
        #    26 : 'comments'
        
        # line_spacing
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'distance_AB'
        #    3 : 'distance_AC'
        #    4 : 'distance_AN'
        #    5 : 'distance_AE'
        #    6 : 'distance_BC'
        #    7 : 'distance_BN'
        #    8 : 'distance_BE'
        #    9 : 'distance_CN'
        #    10 : 'distance_CE'
        #    11 : 'distance_NE'
        #    12 : 'comments'
        
        # overhead_line_conductor
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'geometric_mean_radius'
        #    3 : 'resistance'
        #    4 : 'diameter'
        #    5 : 'rating.summer.continuous'
        #    6 : 'rating.summer.emergency'
        #    7 : 'rating.winter.continuous'
        #    8 : 'rating.winter.emergency'
        #    9 : 'comments'
        
        # underground_line_conductor
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'outer_diameter'
        #    3 : 'conductor_gmr'
        #    4 : 'conductor_diameter'
        #    5 : 'conductor_resistance'
        #    6 : 'neutral_gmr'
        #    7 : 'neutral_diameter'
        #    8 : 'neutral_resistance'
        #    9 : 'neutral_strands'
        #    10 : 'insulation_relative_permativitty'
        #    11 : 'shield_gmr'
        #    12 : 'shield_resistance'
        #    13 : 'rating.summer.continuous'
        #    14: 'rating.summer.emergency'
        #    15 : 'rating.winter.continuous'
        #    16 : 'rating.winter.emergency'
        #    17 : 'comments'
        
        # overhead_line_conductor
        #    0 : 'name'
        #    1 : 'groupid'
        #    2 : 'resistance'
        #    3 : 'geometric_mean_radius'
        #    4 : 'rating.summer.continuous'
        #    5 : 'rating.summer.emergency'
        #    6 : 'rating.winter.continuous'
        #    7 : 'rating.winter.emergency'
        #    8 : 'comments'

def convert_cyme_model(network_db, equipment_db, feeder_id, conductor_data_csv=None):
	glmTree = {}    # Dictionary that will hold the feeder model for conversion to .glm format 
    
	node_prop_list = [None]*7                           # the size of the node property list is 7
	meter_prop_list = [None]*10                          # the size of the meter property list is 7
	load_prop_list = [None]*38                          # the size of the load property list is 38
	triplex_node_prop_list = [None]*8                   # the size of the triplex_node property list for nodes 8
	triplex_meter_prop_list = [None]*7                  # the size of the triplex_meter property list for nodes 7
	capacitor_prop_list = [None]*28                     # the size of the capacitor property list is 28
	fuse_prop_list = [None]*13                          # the size of the capacitor property list is 12
	switch_prop_list = [None]*10                        # the size of the switch property list is 10
	overhead_line_prop_list = [None]*8                  # the size of the overhead_line property list is 8
	underground_line_prop_list = [None]*8               # the size of the underground_line property list is 8
	triplex_line_prop_list = [None]*8                   # the size of the triplex_line property list is 8
	transformer_prop_list = [None]*11                   # the size of the transformer property list is 11
	regulator_prop_list = [None]*8                      # the size of the regulator property list is 8
	line_configuration_prop_list = [None]*17            # the size of the line_configuration property list is 17
	triplex_line_configuration_prop_list = [None]*13    # the size of the triplex_line_configuration property list is 13
	transformer_configuration_prop_list = [None]*25     # the size of the transformer_configuration property list is 25
	regulator_configuration_prop_list = [None]*27       # the size of the regulator_configuration property list is 27
	line_spacing_prop_list = [None]*13                  # the size of the line_spacing property list is 13
	overhead_line_conductor_prop_list = [None]*10       # the size of the overhead_line_conductor property list is 10
	underground_line_conductor_prop_list = [None]*18    # the size of the underground_line_conductor property list is 18
	triplex_line_conductor_prop_list = [None]*9         # the size of the triplex_line_conductor property list is 9
	
	OH_conductors = []			# Stores all overhead line conductors as found in the database. 
	UG_conductors = []
	
	nodes = {}                  # Stores all nodes found in the network database
	meters = {}                 # Stores all meters found in the network database
	loads = {}                  # Stores all loads found in the network database
	tp_nodes = {}               # Stores all triplex nodes found in the network database
	tp_meters = {}              # Stores all triplex meters found in the network database
	capacitors = {}             # Stores all capacitors found in the network database
	fuses = {}                  # Stores all fuses found in the network database
	switches = {}               # Stores all switches found in the network database
	oh_lines = {}               # Stores all overhead lines found in the network database
	ug_lines = {}               # Stores all underground lines found in the network database
	tp_lines = {}               # Stores all triplex lines found in the network database
	transformers = {}           # Stores all transformers found in the network database
	regulators = {}             # Stores all regulators found in the network database
	line_configs = {}           # Stores all line configurations found in the network database
	tp_line_configs = {}        # Stores all triplex line configurations found in the network database
	transformer_configs ={}     # Stores all transformer configurations found in the network database
	regulator_configs = {}      # Stores all regulator configurations found in the network database
	line_spacings = {}          # Stores all line spacings found in the network database
	oh_line_conds = {}          # Stores all overhead line conductors found in the network database
	ug_line_conds = {}          # Stores all underground line conductors found in the network database
	tp_line_conds = {}          # Stores all triplex line conductors found in the network database
	
	m2ft = 1/0.3048             # Conversion factor for meters to feet
	V2nd = 120
	
	# Function that creates a connection to a .mdb database file
	def open_database(database_file):
		connect_string = 'Driver={Microsoft Access Driver (*.mdb)};Dbq=' + database_file + ';Uid=Admin;Pwd='
		#print(connect_string)
		database_connection = pyodbc.connect(connect_string)
		database = database_connection.cursor()
		return database
	
	# Function that replaces characters not allowed in name with '_'
	def fix_name(name):
		name = name.replace(' ', '_')
		name = name.replace('.','_')
		name = name.replace('\\','_')
		name = name.replace('/','_')
		name = name.replace(':','_')
		name = name.replace('\'','')
		return name
	
	# Feeder Id is included in object names in the finished .glm. 
	#     User may change it here. (especially useful for shortening names)
	def feeder_id_to_print(name):
		db_feeder_id = name
		return 'F' + db_feeder_id[-4:] 	# for Duke feeder, last 4 digits of network ID are the feeder identifier.
										# i.e. all we need to be adding to the names
		
	# Function that converts a number to a phase
	def convert_phase(int_phase):
		if int_phase == 1:
			phase = 'AN'
		elif int_phase == 2:
			phase = 'BN'
		elif int_phase == 3:
			phase = 'CN'
		elif int_phase == 4:
			phase = 'ABN'
		elif int_phase == 5:
			phase = 'ACN'
		elif int_phase == 6:
			phase = 'BCN'
		elif int_phase == 7:
			phase = 'ABCN'
		else:
			phase = None
		return phase
	
	# Function that converts a number to a phase
	def convert_regulator_phase(int_phase):
		if int_phase == 1:
			phase = 'A'
		elif int_phase == 2:
			phase = 'B'
		elif int_phase == 3:
			phase = 'C'
		elif int_phase == 4:
			phase = 'AB'
		elif int_phase == 5:
			phase = 'AC'
		elif int_phase == 6:
			phase = 'BC'
		elif int_phase == 7:
			phase = 'ABC'
		else:
			phase = None           
		return phase
	
	# Function the converts a load classification string to a number
	def convert_load_class(class_from_db):
		classes = {}
		classes['Residential1'] = 0
		classes['Residential2'] = 1
		classes['Residential3'] = 2
		classes['Residential4'] = 3
		classes['Residential5'] = 4
		classes['Residential6'] = 5
		classes['Commercial1'] = 6
		classes['Commercial2'] = 7
		classes['Commercial3'] = 8
		
		if class_from_db in classes.keys():
			return classes[class_from_db]
		else:
			return None
	
	# Function that reads in a .csv file and stores it in an array
	def csvToArray(csvFileName):
		''' Simple .csv data ingester. '''
		with open(csvFileName,'r') as csvFile:
			csvReader = csv.reader(csvFile)
			outArray = []
			for row in csvReader:
				outArray += [row]
			return outArray
	
	# Function returns list of suffixes corresponding to the device(s) on the section. 
	def return_suffix(section_id):
		found = []
		if section_id in regulator_sections.keys():
			found.append('reg')
		if section_id in recloser_sections.keys():
			found.append('rec')
		if section_id in sectionalizer_sections.keys():
			found.append('sectionalizer')
		if section_id in switch_sections.keys():
			found.append('sw')
		if section_id in fuse_sections.keys():
			found.append('fuse')
		return found
	
	# Open the network database file
	net_db = open_database(network_db)
	
	# Open the equipment database file
	eqp_db = open_database(equipment_db)
	
	# Check to see if the network database contains models for more than one database and if we chose a valid feeder_id to convert
	feeder_db = net_db.execute("SELECT NetworkId, DesiredVoltage FROM CYMSOURCE").fetchall()
	valid_feeder_id = []
	feeder_id_is_valid = 0
	if len(feeder_db) >= 1:
		for row in feeder_db:
			valid_feeder_id.append(row.NetworkId)
			if row.NetworkId == feeder_id:
				feeder_id_is_valid = 1
				feeder_kVLL = row.DesiredVoltage
		if len(feeder_db) == 1 and feeder_id == None:
			for row in feeder_db:
				feeder_id = row.NetworkId
				feeder_kVLL = row.DesiredVoltage
				feeder_id_is_valid = 1
		if feeder_id_is_valid == 0:
			raise RuntimeError("The feeder_id given does not match any of the feeders listed in the database. Please choose from this list {:s}.\n".format(valid_feeder_id))

    # if feeder_id == None:
        # raise RuntimeError("No feeder_id was give. Please specify a feeder_id.")
    # else:
        # feeder_id_is_valid = 0
        # if len(feeder_db) >= 1:
            # for row in feeder_db:
                # valid_feeder_id.append(row.NewtorkId)
                # if row.NetworkId == feeder_id:
                    # feeder_id_is_valid = 1
            
            # if feeder_id_is_valid == 0:
                # raise RuntimeError("The feeder_id given is not in the network database file. Please choose from this list {:s}.".format(valid_feeder_id))
        # else:
            # feeder_kVLL = row.DesiredVoltage
            
    # Convert Feeder voltage to V line to neutral.
	feeder_VLN = float(feeder_kVLL)*1000/math.sqrt(3)
	
	# -1-CYME CYMSOURCE *********************************************************************************************************************************************************************
	cymsource = {}                          # Stores information found in CYMSOURCE in the network database
	CYMSOURCE = {	'name' : None,            # information structure for each object found in CYMSOURCE
					'bustype' : 'SWING',
					'nominal_voltage' : None}
	
	swing_db = net_db.execute("SELECT NodeId, NetworkId, EquipmentId FROM CYMSOURCE WHERE NetworkId = ?", feeder_id).fetchone()
	if swing_db == None:
		raise RuntimeError("No source node was found in CYMSOURCE for feeder_id: {:s}.\n".format(feeder_id))
	if swing_db.NodeId not in cymsource.keys():
		cymsource[swing_db.NodeId] = CYMSOURCE.copy()
		cymsource[swing_db.NodeId]['name'] = fix_name(swing_db.NodeId)
		cymsource[swing_db.NodeId]['nominal_voltage'] = str(feeder_VLN)
	
	# -2-CYME NODE ***************************************************************************************************************************************************************************
	cymnode = {}                            # Stores information found in CYMNODE in the network database
	CYMNODE = { 'name' : None}              # information structure for each object found in CYMNODE
	
	node_db = net_db.execute("SELECT NodeId FROM CYMNODE WHERE NetworkId = ?", feeder_id).fetchall()
	if len(node_db) == 0:
		warnings.warn("No node objects were found in CYMNODE for feeder_id: {:s}".format(feeder_id), RuntimeWarning)
	else:
		for row in node_db:
			if row.NodeId not in cymnode.keys():
				cymnode[row.NodeId] = CYMNODE.copy()
				cymnode[row.NodeId]['name'] = fix_name(row.NodeId)
	
	# -3-CYME OVERHEADBYPHASE ****************************************************************************************************************************************************************
	cymoverheadbyphase = {}                     # Stores information found in CYMOVERHEADBYPHASE in the network database
	CYMOVERHEADBYPHASE = { 'name' : None,       # Information structure for each object found in CYMOVERHEADBYPHASE
                           'conductorA' : None,
                           'conductorB' : None,
                           'conductorC' : None,
                           'conductorN' : None,
                           'spacing' : None,
                           'length' : None}
	
	overheadbyphase_db = net_db.execute("SELECT DeviceNumber, PhaseConductorIdA, PhaseConductorIdB, PhaseConductorIdC, NeutralConductorId, ConductorSpacingId, Length FROM CYMOVERHEADBYPHASE WHERE NetworkId = ?", feeder_id).fetchall()
	if len(overheadbyphase_db) == 0:
		warnings.warn("No information on phase conductors, spacing, and lengths were found in CYMOVERHEADBYPHASE for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		# Add all phase conductors to the line configuration dictionary.
		for row in overheadbyphase_db:
			if row.DeviceNumber not in cymoverheadbyphase.keys():
				cymoverheadbyphase[row.DeviceNumber] = CYMOVERHEADBYPHASE.copy()
				cymoverheadbyphase[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber)
				cymoverheadbyphase[row.DeviceNumber]['conductorA'] = fix_name(row.PhaseConductorIdA)
				cymoverheadbyphase[row.DeviceNumber]['conductorB'] = fix_name(row.PhaseConductorIdB)
				cymoverheadbyphase[row.DeviceNumber]['conductorC'] = fix_name(row.PhaseConductorIdC)
				cymoverheadbyphase[row.DeviceNumber]['conductorN'] = fix_name(row.NeutralConductorId)
				cymoverheadbyphase[row.DeviceNumber]['spacing'] = row.ConductorSpacingId
				cymoverheadbyphase[row.DeviceNumber]['length'] = float(row.Length)*m2ft
				if row.PhaseConductorIdA not in OH_conductors:
					OH_conductors.append(row.PhaseConductorIdA)
				if row.PhaseConductorIdB not in OH_conductors:
					OH_conductors.append(row.PhaseConductorIdB)
				if row.PhaseConductorIdC not in OH_conductors:
					OH_conductors.append(row.PhaseConductorIdC)
				if row.NeutralConductorId not in OH_conductors:
					OH_conductors.append(row.NeutralConductorId)
	
	# -4-CYME UNDERGROUNDLINE ****************************************************************************************************************************************************************
	cymundergroundline = {}                         # Stores information found in CYMUNDERGOUNDLINE in the network database
	CYMUNDERGROUNDLINE = { 'name' : None,           # Information structure for each object found in CYMUNDERGROUNDLINE
                           'length' : None,
						   'cable_id': None,
                           'device_number' : None}
	
	ug_line_db = net_db.execute("SELECT DeviceNumber, CableId, Length FROM CYMUNDERGROUNDLINE WHERE NetworkId = ?", feeder_id).fetchall()
	if len(ug_line_db) == 0:
		warnings.warn("No underground_line objects were found in CYMUNDERGROUNDLINE for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in ug_line_db:
			if row.DeviceNumber not in cymundergroundline.keys():
				cymundergroundline[row.DeviceNumber] = CYMUNDERGROUNDLINE.copy()
				cymundergroundline[row.DeviceNumber]['name'] = fix_name(row.CableId)  
				cymundergroundline[row.DeviceNumber]['cable_id'] = row.CableId
				cymundergroundline[row.DeviceNumber]['length'] = float(row.Length)*m2ft
				if row.CableId not in UG_conductors:
					UG_conductors.append(row.CableId)
					
	# -5-CYME CYMSECTION ****************************************************************************************************************************************************************
	cymsection = {}                         # Stores information found in CYMSECTION in the network database
	CYMSECTION = { 'name' : None,           # Information structure for each object found in CYMSECTION
                   'from' : None,
                   'to' : None,
                   'phases' : None}
	
	section_db = net_db.execute("SELECT SectionId, FromNodeId, ToNodeId, Phase FROM CYMSECTION WHERE NetworkId = ?", feeder_id).fetchall()
	if len(section_db) == 0:
		warnings.warn("No section information was found in CYMSECTION for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in section_db:
			if row.SectionId not in cymsection.keys():
				cymsection[row.SectionId] = CYMSECTION.copy()
				cymsection[row.SectionId]['name'] = fix_name(row.SectionId)             
				cymsection[row.SectionId]['from'] = fix_name(row.FromNodeId)
				cymsection[row.SectionId]['to'] = fix_name(row.ToNodeId)
				cymsection[row.SectionId]['phases'] = convert_phase(int(row.Phase))
	
	# -4-CYME CYMSECTIONDEVICE ****************************************************************************************************************************************************************
	regulator_sections = {}
	recloser_sections = {}
	sectionalizer_sections = {}
	switch_sections = {}
	fuse_sections = {}
	capacitor_sections = {}
	sx_section = []
	cymsectiondevice = {}                         # Stores information found in CYMSECTIONDEVICE in the network database
	CYMSECTIONDEVICE = { 'name' : None,           # Information structure for each object found in CYMSECTIONDEVICE
						'device_type' : None,
						'section_name' : None,
						'location' : None}
	section_device_db = net_db.execute("SELECT DeviceNumber, DeviceType, SectionId, Location FROM CYMSECTIONDEVICE WHERE NetworkId = ?", feeder_id).fetchall()
	if len(section_device_db) == 0:
		warnings.warn("No section device information was found in CYMSECTIONDEVICE for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in section_device_db:
			if row.DeviceNumber not in cymsectiondevice.keys(): 
				cymsectiondevice[row.DeviceNumber] = CYMSECTIONDEVICE.copy()
				cymsectiondevice[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber)               
				cymsectiondevice[row.DeviceNumber]['device_type'] = int(row.DeviceType)
				cymsectiondevice[row.DeviceNumber]['section_name'] = row.SectionId
				cymsectiondevice[row.DeviceNumber]['location'] = row.Location
				if row.DeviceType == 4:
					regulator_sections[row.SectionId] = row.DeviceNumber
				if row.DeviceType == 10:
					recloser_sections[row.SectionId] = row.DeviceNumber
				if row.DeviceType == 12:
					sectionalizer_sections[row.SectionId] = row.DeviceNumber
				if row.DeviceType == 13:
					switch_sections[row.SectionId] = row.DeviceNumber
				if row.DeviceType == 14:
					fuse_sections[row.SectionId] = row.DeviceNumber
				if row.DeviceType == 16:
					sx_section.append(row.SectionId)
				if row.DeviceType == 17:
					capacitor_sections[row.SectionId] = row.DeviceNumber
					
	# -5-CYME CYMSWITCH**********************************************************************************************************************************************************************
	cymswitch = {}                          # Stores information found in CYMSWITCH in the network database
	CYMSWITCH = { 'name' : None,            # Information structure for each object found in CYMSWITCH
                  'equipment_name' : None,
                  'status' : None}
	
	switch_db = net_db.execute("SELECT DeviceNumber, EquipmentId, IIF(ClosedPhase <> 0, 1, 0) as Status FROM CYMSWITCH WHERE NetworkId = ?", feeder_id).fetchall()
	if len(switch_db) == 0:
		warnings.warn("No switch objects were found in CYMSWITCH for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in switch_db:
			if row.DeviceNumber not in cymswitch.keys():
				cymswitch[row.DeviceNumber] = CYMSWITCH.copy()
				cymswitch[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber)             
				cymswitch[row.DeviceNumber]['equipment_name'] = row.EquipmentId
				if float(row.Status) == 0:
					cymswitch[row.DeviceNumber]['status'] = 0
				else:
					cymswitch[row.DeviceNumber]['status'] = 1
					
	# -6-CYME CYMSECTIONALIZER**********************************************************************************************************************************************************************
	cymsectionalizer = {}                           # Stores information found in CYMSECTIONALIZER in the network database
	CYMSECTIONALIZER = { 'name' : None,             # Information structure for each object found in CYMSECTIONALIZER
                         'status' : None}
						 
	sectionalizer_db = net_db.execute("SELECT DeviceNumber, NormalStatus FROM CYMSECTIONALIZER WHERE NetworkId = ?", feeder_id).fetchall()
	if len(sectionalizer_db) == 0:
		warnings.warn("No sectionalizer objects were found in CYMSECTIONALIZER for feeder_id: {:s}.".format(feeder_id),RuntimeWarning)
	else:
		for row in sectionalizer_db:
			if row.DeviceNumber not in cymsectionalizer.keys():
				cymsectionalizer[row.DeviceNumber] = CYMSECTIONALIZER.copy()
				cymsectionalizer[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber)   
				if float(row.NormalStatus) == 0:
					cymsectionalizer[row.DeviceNumber]['status'] = 0
				else:
					cymsectionalizer[row.DeviceNumber]['status'] = 1
                
	# -7-CYME CYMFUSE**********************************************************************************************************************************************************************
	cymfuse = {}                           # Stores information found in CYMFUSE in the network database
	CYMFUSE = { 'name' : None,             # Information structure for each object found in CYMFUSE
                'status' : None,
				'equipment_id' : None}
				
	fuse_db = net_db.execute("SELECT DeviceNumber, EquipmentId, NormalStatus FROM CYMFUSE WHERE NetworkId = ?", feeder_id).fetchall()
	if len(fuse_db) == 0:
		warnings.warn("No fuse objects were found in CYMFUSE for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in fuse_db:
			if row.DeviceNumber not in cymfuse.keys():
				cymfuse[row.DeviceNumber] = CYMFUSE.copy()
				cymfuse[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber) 
				cymfuse[row.DeviceNumber]['equipment_id'] = row.EquipmentId
				if float(row.NormalStatus) == 0:
					cymfuse[row.DeviceNumber]['status'] = 0
				else:
					cymfuse[row.DeviceNumber]['status'] = 1
	
	# - -CYME CYMRECLOSER**********************************************************************************************************************************************************************
	cymrecloser = {}
	CYMRECLOSER = {	'name' : None,
					'status' : None}
					
	recloser_db = net_db.execute("SELECT DeviceNumber, NormalStatus FROM CYMRECLOSER WHERE NetworkId = ?", feeder_id).fetchall()
	if len(recloser_db) == 0:
		warnings.warn("No recloser objects were found in CYMRECLOSER for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in recloser_db:
			if row.DeviceNumber not in cymrecloser.keys():
				cymrecloser[row.DeviceNumber] = CYMRECLOSER.copy()
				cymrecloser[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber) 
				if float(row.NormalStatus) == 0:
					cymrecloser[row.DeviceNumber]['status'] = 0
				else:
					cymrecloser[row.DeviceNumber]['status'] = 1
					
	# -8-CYME CYMREGULATOR**********************************************************************************************************************************************************************
	cymregulator = {}                           # Stores information found in CYMREGULATOR in the network database
	CYMREGULATOR = { 'name' : None,             # Information structure for each object found in CYMREGULATOR
                     'equipment_name' : None,
                     'ct_rating' : None,
                     'pt_transducer_ratio' : None,
                     'band_width' : None,
                     'tap_pos_A' : None,
                     'tap_pos_B' : None,
                     'tap_pos_C' : None}
					 
	regulator_db = net_db.execute("SELECT DeviceNumber, EquipmentId, CTPrimaryRating, PTRatio, BandWidth, TapPositionA, TapPositionB, TapPositionC FROM CYMREGULATOR WHERE NetworkId = ?", feeder_id).fetchall()
	if len(regulator_db) == 0:
		warnings.warn("No regulator objects were found in CYMREGULATOR for feeder_id: {:s}".format(feeder_id), RuntimeWarning)
	else:
		for row in regulator_db:
			if row.DeviceNumber not in cymregulator.keys():
				cymregulator[row.DeviceNumber] = CYMREGULATOR.copy()
				cymregulator[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber)           
				cymregulator[row.DeviceNumber]['equipment_name'] = row.EquipmentId
				cymregulator[row.DeviceNumber]['ct_rating'] = row.CTPrimaryRating
				cymregulator[row.DeviceNumber]['pt_transducter_ratio'] = row.PTRatio
				cymregulator[row.DeviceNumber]['band_width'] = row.BandWidth
				cymregulator[row.DeviceNumber]['tap_pos_A'] = row.TapPositionA
				cymregulator[row.DeviceNumber]['tap_pos_B'] = row.TapPositionB
				cymregulator[row.DeviceNumber]['tap_pos_C'] = row.TapPositionC
	
	# -9-CYME CYMSHUNTCAPACITOR**********************************************************************************************************************************************************************
	cymshuntcapacitor = {}                           # Stores information found in CYMSHUNTCAPACITOR in the network database
	CYMSHUNTCAPACITOR = { 'name' : None,             # Information structure for each object found in CYMSHUNTCAPACITOR
                          'equipment_name' : None,
                          'status' : None,
                          'phases' : None,
                          'capacitor_A' : None,
                          'capacitor_B' : None,
                          'capacitor_C' : None,
                          'control' : None,
                          'voltage_set_high' : None,
                          'voltage_set_low' : None,
                          'VAr_set_high' : None,
                          'VAr_set_low' : None,
                          'current_set_high' : None,
                          'current_set_low' : None,
                          'pt_phase' : None}
						  
	shuntcapacitor_db = net_db.execute("SELECT DeviceNumber, EquipmentId, Status, Phase, KVARA, KVARB, KVARC, CapacitorControlType, OnValue, OffValue FROM CYMSHUNTCAPACITOR WHERE NetworkId = ?", feeder_id).fetchall()
	if len(shuntcapacitor_db) == 0:
		warnings.warn("No capacitor objects were found in CYMSHUNTCAPACITOR for feeder_id: {:s}".format(feeder_id), RuntimeWarning)
	else:
		for row in shuntcapacitor_db:
			if row.DeviceNumber not in cymshuntcapacitor.keys():
				cymshuntcapacitor[row.DeviceNumber] = CYMSHUNTCAPACITOR.copy()
				cymshuntcapacitor[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber)           
				cymshuntcapacitor[row.DeviceNumber]['equipment_name'] = row.EquipmentId
				cymshuntcapacitor[row.DeviceNumber]['phases'] = convert_phase(int(row.Phase))
				cymshuntcapacitor[row.DeviceNumber]['status'] = row.Status
				if float(row.KVARA) > 0.0:
					cymshuntcapacitor[row.DeviceNumber]['capacitor_A'] = float(row.KVARA)*1000
				if float(row.KVARB) > 0.0:
					cymshuntcapacitor[row.DeviceNumber]['capacitor_B'] = float(row.KVARB)*1000
				if float(row.KVARC) > 0.0:
					cymshuntcapacitor[row.DeviceNumber]['capacitor_C'] = float(row.KVARC)*1000            
				if int(row.CapacitorControlType) == 2:
					cymshuntcapacitor[row.DeviceNumber]['control'] = 'VAR'
					cymshuntcapacitor[row.DeviceNumber]['VAr_set_high'] = float(row.OnValue)*1000
					cymshuntcapacitor[row.DeviceNumber]['VAr_set_low'] = float(row.OffValue)*1000
					cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = convert_phase(int(row.Phase))                
				elif int(row.CapacitorControlType) == 3:
					cymshuntcapacitor[row.DeviceNumber]['control'] = 'CURRENT'
					cymshuntcapacitor[row.DeviceNumber]['current_set_high'] = row.OnValue
					cymshuntcapacitor[row.DeviceNumber]['current_set_low'] = row.OffValue
					cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = convert_phase(int(row.Phase))               
				elif int(row.CapacitorControlType) == 7:
					cymshuntcapacitor[row.DeviceNumber]['control'] = 'VOLT'
					cymshuntcapacitor[row.DeviceNumber]['voltage_set_high'] = row.OnValue
					cymshuntcapacitor[row.DeviceNumber]['voltage_set_low'] = row.OffValue
					cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = convert_phase(int(row.Phase))                
				else:
					cymshuntcapacitor[row.DeviceNumber]['control'] = 'MANUAL'
					cymshuntcapacitor[row.DeviceNumber]['pt_phase'] = convert_phase(int(row.Phase))
	
	# -9-CYME CYMCUSTOMERLOAD**********************************************************************************************************************************************************************
	cymcustomerload = {}                           # Stores information found in CYMCUSTOMERLOAD in the network database
	CYMCUSTOMERLOAD = { 'name' : None,             # Information structure for each object found in CYMCUSTERLOAD
                      'phases' : None,
                      'constant_power_A' : None,
                      'constant_power_B' : None,
                      'constant_power_C' : None,
					  'load_real' : None,
					  'load_imag' : None,
                      'load_class' : 'R'}
	load_real = 0
	load_imag = 0
	
	# Determine the load
	def determine_load( l_type, l_v1, l_v2):
		l_real = 0
		l_imag = 0
		if l_type == 0: # information was stored as kW & kVAR
			l_real = l_v1 * 1000
			l_imag = l_v2 * 1000
		elif l_type == 1: # information was stored as kVA & power factor
			if l_v2 > 0:
				l_real = l_v1 * l_v2/100 * 1000
				l_imag = l_v1 * math.sqrt(1 - (l_v2/100)**2) * 1000
			else:
				l_real = -l_v1 * l_v2/100 * 1000
				l_imag = -l_v1 * math.sqrt(1 - (l_v2/100)**2) * 1000
		else: # information was stored as kW and power factor
			l_real = l_v1 * 1000
			if l_v2 != 0.0:
				l_imag = l_real/(l_v2/100)*math.sqrt(1-abs(l_v2/100)**2)
		return [l_real, l_imag]
	
	def set_constant_power(l_v2, l_real, l_imag):
		if l_v2 >= 0.0:
			cp_string = '{:0.3f}+{:0.3f}j'.format(l_real,l_imag)
		else:
			cp_string = '{:0.3f}-{:0.3f}j'.format(l_real,l_imag)
		return cp_string
	def clean_phases(phases):
		p = ''
		if 'A' in phases:
			p = p + 'A'
		if 'B' in phases:
			p = p + 'B'
		if 'C' in phases:
			p = p + 'C'
		return p
	customerload_db = net_db.execute("SELECT DeviceNumber, DeviceType, ConsumerClassId, Phase, LoadValueType, Phase, LoadValue1, LoadValue2, ConnectedKVA FROM CYMCUSTOMERLOAD WHERE NetworkId = ?", feeder_id).fetchall()
	if len(customerload_db) == 0:
		warnings.warn("No load objects were found in CYMCUSTOMERLOAD for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in customerload_db:
			if row.DeviceNumber not in cymcustomerload.keys():
				# check for 0 load
				[load_real, load_imag] = determine_load(int(row.LoadValueType), float(row.LoadValue1), float(row.LoadValue2))
				if load_real == 0 and load_imag == 0: 
					continue
				else:
					cymcustomerload[row.DeviceNumber] = CYMCUSTOMERLOAD.copy()
					cymcustomerload[row.DeviceNumber]['name'] = fix_name(row.DeviceNumber)               
					cymcustomerload[row.DeviceNumber]['phases'] = clean_phases(convert_phase(int(row.Phase)))
					# Determine the load classification
					if 'residential' in (row.ConsumerClassId).lower():
						cymcustomerload[row.DeviceNumber]['load_class'] = 'R'
					if 'commercial' in (row.ConsumerClassId).lower():
						cymcustomerload[row.DeviceNumber]['load_class'] = 'C'
					convert_class = convert_load_class(row.ConsumerClassId)
					if convert_class is not None:
						cymcustomerload[row.DeviceNumber]['load_class'] = convert_class
						
					cymcustomerload[row.DeviceNumber]['load_real'] = load_real
					cymcustomerload[row.DeviceNumber]['load_imag'] = load_imag
					
					c_p = set_constant_power(float(row.LoadValue2), load_real, load_imag)
					
					if 'A' in cymcustomerload[row.DeviceNumber]['phases']:
						cymcustomerload[row.DeviceNumber]['constant_power_A'] = c_p
					elif 'B' in cymcustomerload[row.DeviceNumber]['phases']:
						cymcustomerload[row.DeviceNumber]['constant_power_B'] = c_p
					else:
						cymcustomerload[row.DeviceNumber]['constant_power_C'] = c_p    
			else:
				[load_real, load_imag] = determine_load(int(row.LoadValueType), float(row.LoadValue1), float(row.LoadValue2))
				if load_real == 0 and load_imag == 0:
					continue
				else:
					ph = cymcustomerload[row.DeviceNumber]['phases'] + convert_phase(int(row.Phase))
					cymcustomerload[row.DeviceNumber]['phases'] = clean_phases(ph)
					cymcustomerload[row.DeviceNumber]['load_real'] += load_real
					cymcustomerload[row.DeviceNumber]['load_imag'] += load_imag
					c_p = set_constant_power(float(row.LoadValue2), load_real, load_imag)
					if 'A' in cymcustomerload[row.DeviceNumber]['phases'] and cymcustomerload[row.DeviceNumber]['constant_power_A'] is None:
						cymcustomerload[row.DeviceNumber]['constant_power_A'] = c_p
					elif 'B' in cymcustomerload[row.DeviceNumber]['phases'] and cymcustomerload[row.DeviceNumber]['constant_power_B'] is None:
						cymcustomerload[row.DeviceNumber]['constant_power_B'] = c_p
					elif 'C' in cymcustomerload[row.DeviceNumber]['phases'] and cymcustomerload[row.DeviceNumber]['constant_power_C'] is None:
						cymcustomerload[row.DeviceNumber]['constant_power_C'] = c_p    
					
	# -1-CYME CYMEQCONDUCTOR**********************************************************************************************************************************************************************
	cymeqconductor = {}                           # Stores information found in CYMEQCONDUCTOR in the equipment database
	CYMEQCONDUCTOR = { 'name' : None,             # Information structure for each object found in CYMEQCONDUCTOR
                       'rating.summer_continuous' : None,
                       'geometric_mean_radius' : None,
                       'resistance' : None}
	cymeqconductor_db = eqp_db.execute("SELECT EquipmentId, FirstRating, GMR, R50 FROM CYMEQCONDUCTOR").fetchall()
	if len(cymeqconductor_db) == 0:
		warnings.warn("No conductor objects were found in CYMEQCONDUCTOR for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in cymeqconductor_db:
			if row.EquipmentId not in cymeqconductor.keys():
				cymeqconductor[row.EquipmentId] = CYMEQCONDUCTOR.copy()
				cymeqconductor[row.EquipmentId]['name'] = fix_name(row.EquipmentId)               
				cymeqconductor[row.EquipmentId]['rating.summer_continuous'] = row.FirstRating
				cymeqconductor[row.EquipmentId]['geometric_mean_radius'] = float(row.GMR)*m2ft/100 #GMR is stored in cm. Must convert to ft.
				cymeqconductor[row.EquipmentId]['resistance'] = float(row.R50)*5280/(m2ft*1000) # R50 is stored in Ohm/km. Must convert to Ohm/mile
	
	# -2-CYME CYMEQGEOMETRICALARRANGEMENT**********************************************************************************************************************************************************************
	cymeqgeometricalarrangement = {}                           # Stores information found in CYMEQGEOMETRICALARRANGEMENT in the equipment database
	CYMEQGEOMETRICALARRANGEMENT = { 'name' : None,             # Information structure for each object found in CYMEQGEOMETRICALARRANGEMENT
                                    'distance_AB' : None,
                                    'distance_AC' : None,
                                    'distance_AN' : None,
                                    'distance_BC' : None,
                                    'distance_BN' : None,
                                    'distance_CN' : None}
	cymeqgeometricalarrangement_db = eqp_db.execute("SELECT EquipmentId, ConductorA_Horizontal, ConductorA_Vertical, ConductorB_Horizontal, ConductorB_Vertical, ConductorC_Horizontal, ConductorC_Vertical, NeutralConductor_Horizontal, NeutralConductor_Vertical FROM CYMEQGEOMETRICALARRANGEMENT").fetchall()
	if len(cymeqgeometricalarrangement_db) == 0:
		warnings.warn("No geometric spacing information was found in CYMEQGEOMETRICALARRANGEMENT for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in cymeqgeometricalarrangement_db:
			if row.EquipmentId not in cymeqgeometricalarrangement.keys():
				cymeqgeometricalarrangement[row.EquipmentId] = CYMEQGEOMETRICALARRANGEMENT.copy()
				cymeqgeometricalarrangement[row.EquipmentId]['name'] = fix_name(row.EquipmentId)               
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AB'] = math.sqrt((float(row.ConductorA_Horizontal)-float(row.ConductorB_Horizontal))**2 + (float(row.ConductorA_Vertical)-float(row.ConductorB_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AC'] = math.sqrt((float(row.ConductorA_Horizontal)-float(row.ConductorC_Horizontal))**2 + (float(row.ConductorA_Vertical)-float(row.ConductorC_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_AN'] = math.sqrt((float(row.ConductorA_Horizontal)-float(row.NeutralConductor_Horizontal))**2 + (float(row.ConductorA_Vertical)-float(row.NeutralConductor_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_BC'] = math.sqrt((float(row.ConductorC_Horizontal)-float(row.ConductorB_Horizontal))**2 + (float(row.ConductorC_Vertical)-float(row.ConductorB_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_BN'] = math.sqrt((float(row.NeutralConductor_Horizontal)-float(row.ConductorB_Horizontal))**2 + (float(row.NeutralConductor_Vertical)-float(row.ConductorB_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
				cymeqgeometricalarrangement[row.EquipmentId]['distance_CN'] = math.sqrt((float(row.ConductorC_Horizontal)-float(row.NeutralConductor_Horizontal))**2 + (float(row.ConductorC_Vertical)-float(row.NeutralConductor_Vertical))**2)*m2ft # information is stored in meters. must convert to feet.
	
	# -3-CYME Read XLSX Sheet**********************************************************************************************************************************************************************
	cymcsvundergroundcable = {}
	CYMCSVUNDERGROUNDCABLE = { 'name' : None,
                               'rating.summer_continuous' : None,
                               'outer_diameter' : None,
                               'conductor_resistance' : None,
                               'conductor_gmr' : None,
                               'neutral_resistance' : None,
                               'neutral_gmr' : None,
                               'neutral_diameter' : None,
                               'neutral_strands' : None,
                               'distance_AB' : None,
                               'distance_AC' : None,
                               'distance_AN' : None,
                               'distance_BC' : None,
                               'distance_BN' : None,
                               'distance_CN' : None}
	
	if conductor_data_csv != None:
		underground_cable_array = csvToArray(conductor_data_csv)[1:]# skip the first row as it is header information
		for row in underground_cable_array:
			if row[0] not in cymcsvundergroundcable.keys():
				cymcsvundergroundcable[row[0]] = CYMCSVUNDERGROUNDCABLE.copy()
				cymcsvundergroundcable[row[0]]['name'] = fix_name(row[0])
				cymcsvundergroundcable[row[0]]['conductor_resistance'] = row[15]
				cymcsvundergroundcable[row[0]]['conductor_gmr'] = row[12]
				cymcsvundergroundcable[row[0]]['rating.summer_continuous'] = row[16]
				cymcsvundergroundcable[row[0]]['neutral_resistance'] = row[19]
				cymcsvundergroundcable[row[0]]['neutral_gmr'] = row[21]
				cymcsvundergroundcable[row[0]]['neutral_diameter'] = row[18]
				cymcsvundergroundcable[row[0]]['neutral_strands'] = row[20]
				cymcsvundergroundcable[row[0]]['outer_diameter'] = row[19]
				cymcsvundergroundcable[row[0]]['distance_AB'] = row[24]
				cymcsvundergroundcable[row[0]]['distance_AC'] = row[26]
				cymcsvundergroundcable[row[0]]['distance_AN'] = row[27]
				cymcsvundergroundcable[row[0]]['distance_BC'] = row[25]
				cymcsvundergroundcable[row[0]]['distance_BN'] = row[28]
				cymcsvundergroundcable[row[0]]['distance_CN'] = row[29]
	else:
		warnings.warn("No conductor data spreadsheet is provided for feeder_id {:s}.".format(feeder_id), RuntimeWarning)
	
	# -4-CYME CYMEQSHUNTCAPACITOR**********************************************************************************************************************************************************************
	cymeqshuntcapacitor = {}                           # Stores information found in CYMEQSHUNTCAPACITOR in the equipment database
	CYMEQSHUNTCAPACITOR = { 'name' : None,             # Information structure for each object found in CYMEQSHUNTCAPACITOR
                            'ratedKVAR' : None,
                            'nominal_voltage' : None}
	cymeqshuntcapacitor_db = eqp_db.execute("SELECT EquipmentId, RatedKVAR, RatedVoltageKVLL FROM CYMEQSHUNTCAPACITOR").fetchall()
	if len(cymeqshuntcapacitor_db) == 0:
		warnings.warn("No capacitor equipment was found in CYMEQSHUNTCAPACITOR for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in cymeqshuntcapacitor_db:
			if row.EquipmentId not in cymeqshuntcapacitor.keys():
				cymeqshuntcapacitor[row.EquipmentId] = CYMEQSHUNTCAPACITOR.copy()
				cymeqshuntcapacitor[row.EquipmentId]['name'] = fix_name(row.EquipmentId)              
				cymeqshuntcapacitor[row.EquipmentId]['ratedKVAR'] = row.RatedKVAR
				cymeqshuntcapacitor[row.EquipmentId]['nominal_voltage'] = float(row.RatedVoltageKVLL)*1000*math.sqrt(3)
	
	# -5-CYME CYMEQFUSE**********************************************************************************************************************************************************************
	cymeqfuse = {}                           # Stores information found in CYMEQFUSE in the equipment database
	CYMEQFUSE = { 'name' : None,             # Information structure for each object found in CYMEQFUSE
                  'current_limit' : None}
	cymeqfuse_db = eqp_db.execute("SELECT EquipmentId, FirstRatedCurrent FROM CYMEQFUSE").fetchall()
	if len(cymeqfuse_db) == 0:
		warnings.warn("No fuse equipment was found in CYMEQFUSE for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in cymeqfuse_db:
			if row.EquipmentId not in cymeqfuse.keys():
				cymeqfuse[row.EquipmentId] = CYMEQFUSE.copy()
				cymeqfuse[row.EquipmentId]['name'] = fix_name(row.EquipmentId)               
				cymeqfuse[row.EquipmentId]['current_limit'] = row.FirstRatedCurrent
	
	# -6-CYME CYMEQREGULATOR**********************************************************************************************************************************************************************
	cymeqregulator = {}                           # Stores information found in CYMEQREGULATOR in the equipment database
	CYMEQREGULATOR = { 'name' : None,             # Information structure for each object found in CYMEQREGULATOR
                       'raise_taps' : None,
                       'lower_taps' : None}
	cymeqregulator_db = eqp_db.execute("SELECT EquipmentId, NumberOfTaps FROM CYMEQREGULATOR").fetchall()
	if len(cymeqregulator_db) == 0:
		warnings.warn("No regulator equipment was found in CYMEQREGULATOR for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in cymeqregulator_db:
			if row.EquipmentId not in cymeqregulator.keys():
				cymeqregulator[row.EquipmentId] = CYMEQREGULATOR.copy()
				cymeqregulator[row.EquipmentId]['name'] = fix_name(row.EquipmentId)              
				cymeqregulator[row.EquipmentId]['raise_taps'] = int(row.NumberOfTaps * 0.5)
				cymeqregulator[row.EquipmentId]['lower_taps'] = int(row.NumberOfTaps * 0.5)
	
	# -7-CYME CYMEQOVERHEADLINE**********************************************************************************************************************************************************************
	cymeqoverheadline = {}                           # Stores information found in CYMEQOVERHEADLINE in the equipment database
	CYMEQOVERHEADLINE = { 'name' : None,             # Information structure for each object found in CYMEQOVERHEADLINE
                          'phase_conductor' : None,
                          'neutral_conductor' : None,
                          'rating.summer_continuous' : None,
                          'spacing' : None}
	cymeqoverheadline_db = eqp_db.execute("SELECT EquipmentId, PhaseConductorId, NeutralConductorId, ConductorSpacingId, FirstRating FROM CYMEQOVERHEADLINE").fetchall()
	if len(cymeqoverheadline_db) == 0:
		warnings.warn("No overhead line equipment was found in CYMEQOVERHEADLINE for feeder_id: {:s}.".format(feeder_id), RuntimeWarning)
	else:
		for row in cymeqoverheadline_db:
			if row.EquipmentId not in cymeqoverheadline.keys():
				cymeqoverheadline[row.EquipmentId] = CYMEQOVERHEADLINE.copy()
				cymeqoverheadline[row.EquipmentId]['name'] = fix_name(row.EquipmentId)              
				cymeqoverheadline[row.EquipmentId]['phase_conductor'] = fix_name(row.PhaseConductorId)
				cymeqoverheadline[row.EquipmentId]['neutral_conductor'] = fix_name(row.NeutralConductorId)
				cymeqoverheadline[row.EquipmentId]['spacing'] = fix_name(row.ConductorSpacingId)
				cymeqoverheadline[row.EquipmentId]['rating.summer_continuous'] = row.FirstRating 
				if row.PhaseConductorId not in OH_conductors:
					OH_conductors.append(row.PhaseConductorId)
				if row.NeutralConductorId not in OH_conductors:
					OH_conductors.append(row.NeutralConductorId)
	
	# FINISHED READING FROM THE DATABASES*****************************************************************************************************************************************************
	
	# allow for altered feeder_name when printing object names.
	feeder_name = feeder_id_to_print(feeder_id)
	
	# Gather Overhead Line Spacings & Configurations
	collected_line_spacings = [] 	# collect unique list of line spacings
	collected_line_configs = [] 	# collect unique list of line configurations
	section_configuration = {} 		# map line configuration to section for making line objects
	for i in cymoverheadbyphase.keys():
		sectionId = cymsectiondevice[i]['section_name']
		spacing = [cymoverheadbyphase[i]['spacing'], cymsection[sectionId]['phases']]
		configuration = [	cymoverheadbyphase[i]['conductorA'], 
							cymoverheadbyphase[i]['conductorB'],
							cymoverheadbyphase[i]['conductorC'],
							cymoverheadbyphase[i]['conductorN'],
							spacing[0],
							spacing[1]]
		if spacing not in collected_line_spacings:
			collected_line_spacings.append(spacing)
		if configuration not in collected_line_configs:
			collected_line_configs.append(configuration)
		if sectionId not in section_configuration.keys():
			section_configuration[sectionId] = configuration
		
	# Gather Underground Line Spacings (also configurations)
	collected_ug_line_configs = []
	for i in cymundergroundline.keys():
		sectionId = cymsectiondevice[i]['section_name']
		spacing = [cymundergroundline[i]['cable_id'], cymsection[sectionId]['phases']]
		if spacing not in collected_ug_line_configs:
			collected_ug_line_configs.append(spacing)
		if sectionId not in section_configuration.keys():
			section_configuration[sectionId] = spacing
    
    # CYMSOURCE contains the swing bus for the model. That swing bus is represented by a meter object so I must enter it into the list meters.
	number_of_swing_nodes = len(cymsource)
	if len(cymsource) > 1:
		raise RuntimeError("There is more than one swing bus for feeder_id {:s}.\n".format(feeder_id))
	for x in cymsource.keys():
		index = len(meters)
		meters[index] = meter_prop_list[:]
		meters[index][0] = '{:s}_{:s}'.format(feeder_name,cymsource[x]['name'])
		meters[index][1] = 'from_db'
		#meters[index][2] = '{:s}_Substation_Meter'.format(feeder_name) # parent
		meters[index][3] = 'SWING'
		meters[index][8] = str(feeder_VLN) # nominal_voltage
		# remove from nodes
		for y in cymnode.keys():
			if cymnode[y]['name'] == cymsource[x]['name']:
				del cymnode[y]
	
	# # Substation meter
	# index = len(meters)
	# meters[index] = meter_prop_list[:]
	# meters[index][0] = '{:s}_Substation_Meter'.format(feeder_name)
	# meters[index][4] = 'ABCN' # phases
	# meters[index][5] = str(feeder_VLN) + '+0.000j' # voltage_A
	# vB_real = feeder_VLN * math.cos( -120 * math.pi / 180)
	# vB_imag = feeder_VLN * math.sin( -120 * math.pi / 180)
	# if vB_imag > 0:
		# vB = str(vB_real) + '+' + str(vB_imag) + 'j'
	# else:
		# vB = str(vB_real) + str(vB_imag) + 'j'
	# meters[index][6] = vB # voltage_B
	# vC_real = feeder_VLN * math.cos( 120 * math.pi / 180)
	# vC_imag = feeder_VLN * math.sin( 120 * math.pi / 180)
	# if vC_imag > 0:
		# vC = str(vC_real) + '+' + str(vC_imag) + 'j'
	# else:
		# vC = str(vC_real) + str(vC_imag) + 'j'
	# meters[index][7] = vC # voltage_c
	# meters[index][8] = str(feeder_VLN)
	
	# Nodes (from cymnode)
	for x in cymnode.keys():
		index = len(nodes)
		nodes[index] = node_prop_list[:]
		nodes[index][0] = '{:s}_{:s}'.format(feeder_name,cymnode[x]['name'])
		nodes[index][1] = 'from_db'
		nodes[index][5] = str(feeder_VLN)
	
	# Overhead line conductors
	for x in OH_conductors:
		index = len(oh_line_conds)
		oh_line_conds[index] = overhead_line_conductor_prop_list[:]
		oh_line_conds[index][0] = '{:s}_{:s}'.format(feeder_name,fix_name(x))
		if (x in cymeqconductor.keys()):
			oh_line_conds[index][5] = str(cymeqconductor[x]['rating.summer_continuous'])
			oh_line_conds[index][2] = str(cymeqconductor[x]['geometric_mean_radius'])
			oh_line_conds[index][3] = str(cymeqconductor[x]['resistance'])
		elif (x in cymcsvundergroundcable.keys()):
			oh_line_conds[index][5] = str(cymcsvundergroundcable[x]['rating.summer_continuous'])
			oh_line_conds[index][2] = str(cymcsvundergroundcable[x]['conductor_gmr'])
			oh_line_conds[index][3] = str(cymcsvundergroundcable[x]['conductor_resistance'])
		else:
			warnings.warn("No conductor data was found in {:s} or CYMEQCONDUCTOR for overhead line conductor: {:s}.".format(conductor_data_csv,x), RuntimeWarning)
		
	# Underground line conductors
	for x in UG_conductors:
		index = len(ug_line_conds)
		ug_line_conds[index] = underground_line_conductor_prop_list[:]
		ug_line_conds[index][0] = '{:s}_{:s}'.format(feeder_name,fix_name(x))
		if (x in cymcsvundergroundcable.keys()):
			ug_line_conds[index][13] = str(cymcsvundergroundcable[x]['rating.summer_continuous'])
			ug_line_conds[index][2] = str(cymcsvundergroundcable[x]['outer_diameter'])
			ug_line_conds[index][3] = str(cymcsvundergroundcable[x]['conductor_gmr'])
			ug_line_conds[index][4] = str(cymcsvundergroundcable[x]['outer_diameter'])
			ug_line_conds[index][5] = str(cymcsvundergroundcable[x]['conductor_resistance'])
			ug_line_conds[index][6] = str(cymcsvundergroundcable[x]['neutral_gmr'])
			ug_line_conds[index][8] = str(cymcsvundergroundcable[x]['neutral_resistance'])
			ug_line_conds[index][7] = str(cymcsvundergroundcable[x]['neutral_diameter'])
			ug_line_conds[index][9] = str(cymcsvundergroundcable[x]['neutral_strands'])
			ug_line_conds[index][11] = str(0.00)
			ug_line_conds[index][12] = str(0.00)
		else:
			warnings.warn("No conductor data was found in {:s} for underground line conductor: {:s}.".format(conductor_data_csv,cable_id), RuntimeWarning)
			
	# Triplex Line Conductor
	index = len(tp_line_conds)
	tp_line_conds[index] = triplex_line_conductor_prop_list[:]
	tp_line_conds[index][0] = '{:s}_4/0_AA_triplex'.format(feeder_name)
	tp_line_conds[index][2] =  str(0.484)
	tp_line_conds[index][3] =  str(0.0158)
	tp_line_conds[index][4] = str(299)
	
	# Triplex Line Configuration
	index = len(tp_line_configs)
	tp_line_configs[index] = triplex_line_configuration_prop_list[:]
	tp_line_configs[index][0] = '{:s}_TLCFG'.format(feeder_name)
	tp_line_configs[index][2] = '{:s}_4/0_AA_triplex'.format(feeder_name)
	tp_line_configs[index][3] = '{:s}_4/0_AA_triplex'.format(feeder_name)
	tp_line_configs[index][4] = '{:s}_4/0_AA_triplex'.format(feeder_name)
	tp_line_configs[index][5] = str(0.08)
	tp_line_configs[index][6] = str(0.522)
	
	# Overhead Line Spacings
	for x in collected_line_spacings:
		[spacingID, ph] = x
		index = len(line_spacings)
		line_spacings[index] = line_spacing_prop_list[:]
		line_spacings[index][0] = '{:s}_{:s}_{:s}'.format(feeder_name,fix_name(spacingID),ph)
		if spacingID in cymeqgeometricalarrangement.keys():
			if 'A' in ph and 'B' in ph:
				line_spacings[index][2] = str(cymeqgeometricalarrangement[spacingID]['distance_AB'])
			if 'B' in ph and 'C' in ph:
				line_spacings[index][6] = str(cymeqgeometricalarrangement[spacingID]['distance_BC'])
			if 'A' in ph and 'C' in ph:
				line_spacings[index][3] = str(cymeqgeometricalarrangement[spacingID]['distance_AC'])
			if 'N' in ph:
				if 'A' in ph:
					line_spacings[index][4] = str(cymeqgeometricalarrangement[spacingID]['distance_AN'])
				if 'B' in ph:
					line_spacings[index][7] = str(cymeqgeometricalarrangement[spacingID]['distance_BN'])
				if 'C' in ph:
					line_spacings[index][9] = str(cymeqgeometricalarrangement[spacingID]['distance_CN'])
		else:
			warnings.warn("No spacing measurements were found in CYMEQGEOMETRICALARRANGEMENT for spacing: {:s}.".format(spacingID), RuntimeWarning)
			
	# Underground Line Spacings
	for x in collected_ug_line_configs:
		[cableID, ph] = x
		index = len(line_spacings)
		line_spacings[index] = line_spacing_prop_list[:]
		line_spacings[index][0] = '{:s}_{:s}_{:s}_spacing'.format(feeder_name,fix_name(cableID),ph) 
		if cableID in cymcsvundergroundcable.keys():
			if 'A' in ph and 'B' in ph:
				line_spacings[index][2] = str(cymcsvundergroundcable[cableID]['distance_AB'])
			if 'B' in ph and 'C' in ph:
				line_spacings[index][6] = str(cymcsvundergroundcable[cableID]['distance_BC'])
			if 'A' in ph and 'C' in ph:
				line_spacings[index][3] = str(cymcsvundergroundcable[cableID]['distance_AC'])
			if 'N' in ph:
				if 'A' in ph:
					line_spacings[index][4] = str(cymcsvundergroundcable[cableID]['distance_AN'])
				if 'B' in ph:
					line_spacings[index][7] = str(cymcsvundergroundcable[cableID]['distance_BN'])
				if 'C' in ph:
					line_spacings[index][9] = str(cymcsvundergroundcable[cableID]['distance_CN'])
		else:
			warnings.warn("No spacing measurements were found in {:s} for cable: {:s}.".format(conductor_data_csv,cableID), RuntimeWarning)
				
	# Overhead Line Configurations
	c = 0
	line_config_name_map = {}
	for x in collected_line_configs:
		[condA, condB, condC, condN, spacingID, ph] = x
		x_no_None = filter(lambda x: x!=None, x)
		index = len(line_configs)
		line_configs[index] = line_configuration_prop_list[:]
		namestr = '{:s}_{:s}_{:s}_{:s}_{:s}_{:s}'.format(condA,condB,condC,condN,fix_name(spacingID),ph)
		name = 'line_configuration_' + str(c)
		c += 1
		line_config_name_map[namestr] = name
		
		line_configs[index][0] = name
		if 'A' in ph:
			if condA is not None:
				line_configs[index][2] = '{:s}_{:s}'.format(feeder_name,condA)
			else:
				line_configs[index][2] = '{:s}_{:s}'.format(feeder_name,x_no_None[0])
		if 'B' in ph:
			if condB is not None:
				line_configs[index][3] = '{:s}_{:s}'.format(feeder_name,condB)
			else:
				line_configs[index][3] = '{:s}_{:s}'.format(feeder_name,x_no_None[0])
		if 'C' in ph:
			if condC is not None:
				line_configs[index][4] = '{:s}_{:s}'.format(feeder_name,condC)
			else:
				line_configs[index][4] = '{:s}_{:s}'.format(feeder_name,x_no_None[0])
		if 'N' in ph:
			if condN is not None:
				line_configs[index][5] = '{:s}_{:s}'.format(feeder_name,condN)
			else:
				warnings.warn("Line configuration {:s} is missing a specified neutral conductor.".format(name), RuntimeWarning)
		line_configs[index][6] = '{:s}_{:s}_{:s}'.format(feeder_name,fix_name(spacingID),ph)
	
	# Underground Line Configurations
	for x in collected_ug_line_configs:
		[cableID, ph] = x
		index = len(line_configs)
		line_configs[index] = line_configuration_prop_list[:]
		namestr = '{:s}_{:s}'.format(fix_name(cableID),ph)
		name = 'line_configuration_' + str(c)
		c += 1
		line_config_name_map[namestr] = name
		
		line_configs[index][0] = name
		if 'A' in ph:
			line_configs[index][2] = '{:s}_{:s}'.format(feeder_name,fix_name(cableID))
		if 'B' in ph:
			line_configs[index][3] = '{:s}_{:s}'.format(feeder_name,fix_name(cableID))
		if 'C' in ph:
			line_configs[index][4] = '{:s}_{:s}'.format(feeder_name,fix_name(cableID))
		if 'N' in ph:
			line_configs[index][5] = '{:s}_{:s}'.format(feeder_name,fix_name(cableID))
		line_configs[index][6] = '{:s}_{:s}_{:s}_spacing'.format(feeder_name,fix_name(cableID),ph)

	# Map configuration names to corresponding sections for use in line creation
	section_configuration_names = {}
	for x in section_configuration.keys():
		if len(section_configuration[x]) == 6:
			[condA, condB, condC, condN, spacingID, ph] = section_configuration[x]
			namestr = '{:s}_{:s}_{:s}_{:s}_{:s}_{:s}'.format(condA,condB,condC,condN,fix_name(spacingID),ph)
			section_configuration_names[x] = line_config_name_map[namestr]
		else:
			[cableID,ph] = section_configuration[x]
			namestr = '{:s}_{:s}'.format(fix_name(cableID),ph)
			section_configuration_names[x] = line_config_name_map[namestr]
			
	# Switch Objects & Switch Nodes
	device_lines_collected = []
	for x in switch_sections.keys():
		index = len(switches)
		switches[index] = switch_prop_list[:]
		swnode = '{:s}_{:s}_swnode'.format(feeder_name,fix_name(switch_sections[x]))
		switches[index][0] = '{:s}_{:s}_sw'.format(feeder_name,fix_name(x))
		switches[index][2] = str(cymsection[x]['phases'])
		if cymsectiondevice[switch_sections[x]]['location'] == 1: # from side
			switches[index][3] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['from']) 
			switches[index][4] = swnode
			device_lines_collected.append([x,swnode,'SW','from'])
		if cymsectiondevice[switch_sections[x]]['location'] == 2: #to side
			switches[index][3] = swnode
			switches[index][4] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['to'])
			device_lines_collected.append([x,swnode,'SW','to'])
		if cymswitch[switch_sections[x]]['status'] == 0:
			sw_status = 'OPEN'
		else:
			sw_status = 'CLOSED'
		switches[index][5] = sw_status
		switches[index][6] = sw_status
		switches[index][7] = sw_status
		
		index_n = len(nodes)
		nodes[index_n] = node_prop_list[:]
		nodes[index_n][0] = swnode
		nodes[index_n][4] = str(cymsection[x]['phases'])
		nodes[index_n][1] = 'swnode'
		nodes[index_n][5] = str(feeder_VLN)
		
	# Recloser Objects & Recloser Nodes (Populated as Switches)
	for x in recloser_sections.keys():
		index = len(switches)
		switches[index] = switch_prop_list[:]
		recnode = '{:s}_{:s}_recnode'.format(feeder_name,fix_name(recloser_sections[x]))
		switches[index][0] = '{:s}_{:s}_rec'.format(feeder_name,fix_name(x))
		switches[index][2] = str(cymsection[x]['phases'])
		if cymsectiondevice[recloser_sections[x]]['location'] == 1: # from side
			switches[index][3] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['from']) 
			switches[index][4] = recnode
			device_lines_collected.append([x,recnode,'rec','from'])
		if cymsectiondevice[recloser_sections[x]]['location'] == 2: #to side
			switches[index][3] = recnode
			switches[index][4] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['to'])
			device_lines_collected.append([x,recnode,'rec','to'])
		if cymrecloser[recloser_sections[x]]['status'] == 0:
			rec_status = 'OPEN'
		else:
			rec_status = 'CLOSED'
		switches[index][5] = rec_status
		switches[index][6] = rec_status
		switches[index][7] = rec_status
		switches[index][9] = 'Recloser, used as switch for now'
		
		index_n = len(nodes)
		nodes[index_n] = node_prop_list[:]
		nodes[index_n][0] = recnode
		nodes[index_n][4] = str(cymsection[x]['phases'])
		nodes[index_n][1] = 'recnode'
		nodes[index_n][5] = str(feeder_VLN)
	
	# Sectionalizer Objects & Sectionalizer Nodes (Populated as switches)
	for x in sectionalizer_sections.keys():
		index = len(switches)
		switches[index] = switch_prop_list[:]
		sectionalizernode = '{:s}_{:s}_sectionalizernode'.format(feeder_name,fix_name(sectionalizer_sections[x]))
		switches[index][0] = '{:s}_{:s}_sectionalizer'.format(feeder_name,fix_name(x))
		switches[index][2] = str(cymsection[x]['phases'])
		if cymsectiondevice[sectionalizer_sections[x]]['location'] == 1: # from side
			switches[index][3] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['from']) 
			switches[index][4] = sectionalizernode
			device_lines_collected.append([x,sectionalizernode,'sectionalizer','from'])
		if cymsectiondevice[sectionalizer_sections[x]]['location'] == 2: #to side
			switches[index][3] = sectionalizernode
			swtiches[index][4] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['to'])
			device_lines_collected.append([x,sectionalizernode,'sectionalizer','to'])
		if cymsectionalizer[sectionalizer_sections[x]]['status'] == 0:
			status = 'OPEN'
		else:
			status = 'CLOSED'
		switches[index][5] = status
		switches[index][6] = status
		switches[index][7] = status
		switches[index][9] = 'Sectionalizer, used as switch for now'
		
		index_n = len(nodes)
		nodes[index_n] = node_prop_list[:]
		nodes[index_n][0] = sectionalizernode
		nodes[index_n][4] = str(cymsection[x]['phases'])
		nodes[index_n][1] = 'sectionalizernode'
		nodes[index_n][5] = str(feeder_VLN)
		
	# Fuse Objects & Fuse Nodes
	for x in fuse_sections.keys(): 
		index = len(fuses)
		fuses[index] = fuse_prop_list[:]
		fusenode = '{:s}_{:s}_fusenode'.format(feeder_name,fix_name(fuse_sections[x]))
		fuses[index][0] =  '{:s}_{:s}_fuse'.format(feeder_name,fix_name(x))
		fuses[index][2] = str(cymsection[x]['phases'])
		fuses[index][10] = str(2) #mean replacement time
		eqp_id = cymfuse[fuse_sections[x]]['equipment_id']
		fuses[index][9] = str(cymeqfuse[eqp_id]['current_limit'])
		if cymsectiondevice[fuse_sections[x]]['location'] == 1:
			fuses[index][3] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['from'])
			fuses[index][4] = fusenode
			device_lines_collected.append([x,fusenode,'fuse','from'])
		if cymsectiondevice[fuse_sections[x]]['location'] == 2:
			fuses[index][3] = fusenode
			fuses[index][4] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['to'])
			device_lines_collected.append([x,fusenode,'fuse','to'])
		if cymfuse[fuse_sections[x]]['status'] == 0:
			fuse_status = 'OPEN'
		else:
			fuse_status = 'CLOSED'
		fuses[index][12] = fuse_status
		
		index_n = len(nodes)
		nodes[index_n] = node_prop_list[:]
		nodes[index_n][0] = fusenode
		nodes[index_n][4] = str(cymsection[x]['phases'])
		nodes[index_n][1] = 'fusenode'
		nodes[index_n][5] = str(feeder_VLN)
		
	# Regulator Configurations
	for x in regulator_sections.keys():
		index = len(regulator_configs)
		regulator_configs[index] = regulator_configuration_prop_list[:]
		cfg_name = '{:s}_{:s}_regcfg'.format(feeder_name,fix_name(x))
		regulator_configs[index][0] = cfg_name
		regulator_configs[index][2] = 'WYE_WYE' # connect_type
		regulator_configs[index][3] = str(V2nd) # band_center
		regulator_configs[index][4] = str(cymregulator[regulator_sections[x]]['band_width']) # band_width
		regulator_configs[index][5] = str(30) # time_delay
		eqp_id = cymregulator[regulator_sections[x]]['equipment_name']
		regulator_configs[index][7] = str(cymeqregulator[eqp_id]['raise_taps'])
		regulator_configs[index][8] = str(cymeqregulator[eqp_id]['lower_taps'])
		regulator_configs[index][9] = str(cymregulator[regulator_sections[x]]['ct_rating']) # current_transducer_ratio
		regulator_configs[index][10] = str(cymregulator[regulator_sections[x]]['pt_transducer_ratio']) # power_transducer_ratio
		regulator_configs[index][11] = str(6.0) # compensator_r_setting_A
		regulator_configs[index][13] = str(6.0) # compensator_r_setting_B
		regulator_configs[index][15] = str(6.0) # compensator_r_setting_C
		regulator_configs[index][12] = str(12.0) # compensator_x_setting_A
		regulator_configs[index][14] = str(12.0) # compensator_x_setting_B
		regulator_configs[index][16] = str(12.0) # compensastor_x_setting_C
		regulator_configs[index][17] = cymsection[x]['phases'] # CT_phase
		regulator_configs[index][18] = cymsection[x]['phases'] # PT_phase
		regulator_configs[index][19] = str(0.10) # regulation
		regulator_configs[index][23] = str(cymregulator[regulator_sections[x]]['tap_pos_A']) 
		regulator_configs[index][24] = str(cymregulator[regulator_sections[x]]['tap_pos_B']) 
		regulator_configs[index][25] = str(cymregulator[regulator_sections[x]]['tap_pos_C'])
		
		index = len(regulators)
		regulators[index] = regulator_prop_list[:]
		regnode = '{:s}_{:s}_regnode'.format(feeder_name,fix_name(regulator_sections[x]))
		regulators[index][0] = '{:s}_{:s}_reg'.format(feeder_name,fix_name(x))
		regulators[index][2] = cymsection[x]['phases']
		if cymsectiondevice[regulator_sections[x]]['location'] == 1: 
			regulators[index][3] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['from'])
			regulators[index][4] = regnode
		else:
			regulators[index][3] = regnode
			regulators[index][4] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['to'])
		regulators[index][5] = cfg_name
		
		device_lines_collected.append(x,regnode)
		
		index_n = len(nodes)
		nodes[index_n] = node_prop_list[:]
		nodes[index_n][0] = regnode
		nodes[index_n][4] = str(cymsection[x]['phases'])
		nodes[index_n][1] = 'regnode'
		nodes[index_n][5] = str(feeder_VLN)
		
	# Capacitors
	for x in capacitor_sections.keys():
		index = len(capacitors)
		capacitors[index] = capacitor_prop_list[:]
		ph = str(cymshuntcapacitor[capacitor_sections[x]]['phases'])
		name = '{:s}_{:s}'.format(feeder_name,fix_name(capacitor_sections[x]))
		capacitors[index][0] = name
		capacitors[index][2] = '{:s}_{:s}'.format(feeder_name,cymsection[x]['to']) # parent
		capacitors[index][3] = ph # phases
		capacitors[index][5] = str(cymshuntcapacitor[capacitor_sections[x]]['pt_phase'])
		capacitors[index][6] = ph # phases_connected
		ctrl = str(cymshuntcapacitor[capacitor_sections[x]]['control'])
		capacitors[index][10] = ctrl
		capacitors[index][17] = str(cymshuntcapacitor[capacitor_sections[x]]['capacitor_A'])
		capacitors[index][18] = str(cymshuntcapacitor[capacitor_sections[x]]['capacitor_B'])
		capacitors[index][19] = str(cymshuntcapacitor[capacitor_sections[x]]['capacitor_C'])
		capacitors[index][26] = 'INDIVIDUAL'
		if ctrl == 'CURRENT' or ctrl == 'VAR':
			sffx = return_suffix(x)
			if len(sffx) == 0:
				if x in cymoverheadbyphase.keys():
					capacitors[index][24] = '{:s}_{:s}_OH'.format(feeder_name,fix_name(x)) # remote_sense
				elif x in cymundergroundline.keys():
					capacitors[index][24] = '{:s}_{:s}_UG'.format(feeder_name,fix_name(x)) # remote_sense
				else:
					warnings.warn("Capacitor: {:s}. Can't set remote_sense-- section {:s} is neither OH nor UG.".format(capacitor_sections[x],x),RuntimeWarning)
			else:
				capacitors[index][24] = '{:s}_{:s}_{:s}'.format(feeder_name,fix_name(x),sffx[0]) # remote_sense
				if len(sffx) > 1:
					warnings.warn("Capacitor: {:s}. Can't set remote_sense-- multiple devices on section {:s}.".format(capacitor_sections[x],x),RuntimeWarning)
		if ctrl == 'CURRENT':
			capacitors[index][15] = str(cymshuntcapacitor[capacitor_sections[x]]['current_set_high'])
			capacitors[index][16] = str(cymshuntcapacitor[capacitor_sections[x]]['current_set_low'])
		if ctrl == 'VAR':
			capacitors[index][13] = str(cymshuntcapacitor[capacitor_sections[x]]['VAr_set_high'])
			capacitors[index][14] = str(cymshuntcapacitor[capacitor_sections[x]]['VAr_set_low'])
		if cymshuntcapacitor[capacitor_sections[x]]['status'] == 1:
			status = 'OPEN'
		else:
			status = 'CLOSED'
		if 'A' in ph:
			capacitors[index][7] = status # switchA
		if 'B' in ph:
			capacitors[index][8] = status # switchB
		if 'C' in ph:
			capacitors[index][9] = status # switchC
		capacitors[index][21] = str(2.0) # time_delay
		capacitors[index][22] = str(3.0) # dwell_time
		eqp_id = cymshuntcapacitor[capacitor_sections[x]]['equipment_name']
		capacitors[index][20] = str(cymeqshuntcapacitor[eqp_id]['nominal_voltage']) # cap_nominal_voltage
		capacitors[index][4] = str(feeder_VLN) # nominal voltage
		
	# Overhead & Underground Lines
	def make_overhead_line(deviceId,node=None,suffix=None,side=None):
		index = len(oh_lines)
		oh_lines[index] = overhead_line_prop_list[:]
		sectionId = cymsectiondevice[deviceId]['section_name']
		if suffix is not None:
			name = '{:s}_{:s}_OH_{:s}'.format(feeder_name,fix_name(deviceId),sffx)
		else:
			name = '{:s}_{:s}_OH'.format(feeder_name,fix_name(deviceId))
		oh_lines[index][0] = name
		oh_lines[index][2] = str(cymsection[sectionId]['phases'])
		oh_lines[index][3] = '{:s}_{:s}'.format(feeder_name,cymsection[sectionId]['from'])
		oh_lines[index][4] = '{:s}_{:s}'.format(feeder_name,cymsection[sectionId]['to'])
		if side is not None:
			if side == 'from':
				oh_lines[index][3] = node
			else:
				oh_lines[index][4] = node
		oh_lines[index][5] = str(cymoverheadbyphase[deviceId]['length'])
		if sectionId in section_configuration_names.keys():
			oh_lines[index][6] = section_configuration_names[sectionId]
		else:
			warnings.warn("No configuration found for line {:s}.".format(name),RuntimeWarning)
		
	def make_underground_line(deviceId,node=None,suffix=None,side=None):
		index = len(ug_lines)
		ug_lines[index] = underground_line_prop_list[:]
		sectionId = cymsectiondevice[deviceId]['section_name']
		if suffix is not None:
			name = '{:s}_{:s}_UG_{:s}'.format(feeder_name,fix_name(deviceId),sffx)
		else:
			name = '{:s}_{:s}_UG'.format(feeder_name,fix_name(deviceId))
		ug_lines[index][0] = name 
		ug_lines[index][2] = str(cymsection[sectionId]['phases'])
		ug_lines[index][3] = '{:s}_{:s}'.format(feeder_name,cymsection[sectionId]['from'])
		ug_lines[index][4] = '{:s}_{:s}'.format(feeder_name,cymsection[sectionId]['to'])
		if side is not None:
			if side == 'from':
				ug_lines[index][3] = node
			else:
				ug_lines[index][4] = node
		ug_lines[index][5] = str(cymundergroundline[deviceId]['length'])
		if sectionId in section_configuration_names.keys():
			ug_lines[index][6] = section_configuration_names[sectionId]
		else:
			warnings.warn("No configuration found for line {:s}.".format(name),RuntimeWarning)
		
	for x in cymsectiondevice.keys():
		sectionId = cymsectiondevice[x]['section_name']
		sffx = return_suffix(sectionId)
		if len(sffx) == 0:
			if cymsectiondevice[x]['device_type'] == 1:
				make_underground_line(x)
			elif cymsectiondevice[x]['device_type'] == 2 or cymsectiondevice[x]['device_type'] == 3:
				make_overhead_line(x)
				
	for x in device_lines_collected:
		# note: some of the following assumes deviceId = sectionId for all lines in CYMOVERHEADBYPHASE and CYMUNDERGROUNDLINE.
		[sectionId, node, sffx, side] = x
		if sectionId in cymoverheadbyphase.keys():
			make_overhead_line(sectionId,node,sffx,side)
		elif sectionId in cymundergroundline.keys():
			make_underground_line(sectionId,node,sffx,side)
		else:
			warnings.warn("Section: {:s} is found in neither CYMUNDERGROUNDLINE nor CYMOVERHEADBYPHASE.\n".format(sectionId),RuntimeWarning)
			
	# Loads
	for x in cymcustomerload.keys():
		# only non-zero loads allowed
		if cymcustomerload[x]['load_real'] != 0 and cymcustomerload[x]['load_imag'] != 0:
			index = len(loads)
			loads[index] = load_prop_list[:]
			load_parent_name = '{:s}_{:s}_M'.format(feeder_name,fix_name(x))
			load_phases = str(cymcustomerload[x]['phases'])
			load_class = str(cymcustomerload[x]['load_class'])
			loads[index][0] = '{:s}_{:s}_load'.format(feeder_name,fix_name(x))
			loads[index][1] = load_class # groupid
			loads[index][2] = load_parent_name # parent
			loads[index][4] = load_phases
			loads[index][5] = str(feeder_VLN) # nominal_voltage
			loads[index][7] = cymcustomerload[x]['constant_power_A']
			loads[index][8] = cymcustomerload[x]['constant_power_B']
			loads[index][9] = cymcustomerload[x]['constant_power_C']
			loads[index][6] = load_class # load class
			
			index = len(meters)
			meters[index] = meter_prop_list[:]
			meters[index][0] = load_parent_name
			meters[index][4] = load_phases
			meters[index][8] = str(feeder_VLN) # nominal_voltage
			
			sectionId = cymsectiondevice[x]['section_name']
			fromNode = '{:s}_{:s}'.format(feeder_name,cymsection[sectionId]['from'])
			toNode = load_parent_name
			if sectionId in cymoverheadbyphase.keys():
				index = len(oh_lines)
				oh_lines[index] = overhead_line_prop_list[:]
				oh_lines[index][0] = '{:s}_{:s}_OH2'.format(feeder_name,fix_name(x))
				oh_lines[index][2] = load_phases
				oh_lines[index][3] = fromNode
				oh_lines[index][4] = toNode
				oh_lines[index][5] = str(25) # length
				if sectionId in section_configuration_names.keys():
					oh_lines[index][6] = section_configuration_names[sectionId]
			elif sectionId in cymundergroundline.keys():
				index = len(ug_lines)
				ug_lines[index] = underground_line_prop_list[:]
				ug_lines[index][0] = '{:s}_{:s}_UG2'.format(feeder_name,fix_name(x))
				ug_lines[index][2] = load_phases
				ug_lines[index][3] = fromNode
				ug_lines[index][4] = toNode
				ug_lines[index][5] = str(25) # length
				if sectionId in section_configuration_names.keys():
					ug_lines[index][6] = section_configuration_names[sectionId]
			else:
				warnings.warn("Section: {:s} is found in neither CYMUNDERGROUNDLINE nor CYMOVERHEADBYPHASE.\n".format(sectionId),RuntimeWarning)
	
	# FINISHED CONVERSION FROM THE DATABASES****************************************************************************************************************************************************
    
	# Add all node objects to glmTree
	if len(nodes) > 0:
		for x in nodes.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'node', nodes[x])
    
	# Add all meter objects to glmTree
	if len(meters) > 0:
		for x in meters.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'meter', meters[x])
    
	# Add all load objects to glmTree
	if len(loads) > 0:
		for x in loads.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'load', loads[x])
            
	# Add all triplex_node objects to glmTree
	if len(tp_nodes) > 0:
		for x in tp_nodes.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'triplex_node', tp_nodes[x])
            
	# Add all triplex_meter objects to glmTree
	if len(tp_meters) > 0:
		for x in tp_meters.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'triplex_meter', tp_meters[x])
            
	# Add all capacitor objects to glmTree
	if len(capacitors) > 0:
		for x in capacitors.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'capacitor', capacitors[x])
            
	# Add all fuse objects to glmTree
	if len(fuses) > 0:
		for x in fuses.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'fuse', fuses[x])
            
	# Add all switch objects to glmTree
	if len(switches) > 0:
		for x in switches.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'switch', switches[x])
            
	# Add all overhead_line objects to glmTree
	if len(oh_lines) > 0:
		for x in oh_lines.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'overhead_line', oh_lines[x])
            
	# Add all underground_line objects to glmTree
	if len(ug_lines) > 0:
		for x in ug_lines.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'underground_line', ug_lines[x])
            
	# Add all triplex_line objects to glmTree
	if len(tp_lines) > 0:
		for x in tp_lines.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'triplex_line', tp_lines[x])
            
	# Add all transformer objects to glmTree
	if len(transformers) > 0:
		for x in transformers.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'transformer', transformers[x])
            
	# Add all regulator objects to glmTree
	if len(regulators) > 0:
		for x in regulators.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'regulator', regulators[x])
            
	# Add all line_configuration objects to glmTree
	if len(line_configs) > 0:
		for x in line_configs.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'line_configuration', line_configs[x])
            
	# Add all triplex_line_configuration objects to glmTree
	if len(tp_line_configs) > 0:
		for x in tp_line_configs.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'triplex_line_configuration', tp_line_configs[x])
            
	# Add all transformer_configuration objects to glmTree
	if len(transformer_configs) > 0:
		for x in transformer_configs.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'transformer_configuration', transformer_configs[x])
            
	# Add all regulator_configuration objects to glmTree
	if len(regulator_configs) > 0:
		for x in regulator_configs.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'regulator_configuration', regulator_configs[x])
            
	# Add all line_spacing objects to glmTree 
	if len(line_spacings) > 0:
		for x in line_spacings.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'line_spacing', line_spacings[x])
            
	# Add all overhead_line_conductors objects to glmTree
	if len(oh_line_conds) > 0:
		for x in oh_line_conds.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'overhead_line_conductor', oh_line_conds[x])
            
	# Add all underground_line_conductors objects to glmTree
	if len(ug_line_conds) > 0:
		for x in ug_line_conds.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'underground_line_conductor', ug_line_conds[x])
            
	# Add all triplex_line_conductors objects to glmTree
	if len(tp_line_conds) > 0:
		for x in tp_line_conds.keys():
			glmTree = add_glm_object_dictionary.create_glm_object_dictionary(glmTree, 'triplex_line_conductor', tp_line_conds[x])
    
	# Delete any malformed links        
	for key in glmTree.keys():
		# if ('from' in glmTree[key].keys() and 'to' not in glmTree[key].keys()) or ('to' in glmTree[key].keys() and 'from' not in glmTree[key].keys()):
		if glmTree[key]['object'] in ['overhead_line','underground_line','regulator','transformer','switch','fuse'] and ('to' not in glmTree[key].keys() or 'from' not in glmTree[key].keys()):
			print ('Deleting malformed link')
			print [glmTree[key]['name'], glmTree[key]['object']]
			del glmTree[key]
    
	# Delete any islanded nodes and fix phase mismatches
	
	# Create list of all from and to node names
	node_phases = {}
	from_node_phases = {}
	to_node_phases = {}
	for key in glmTree.keys():
		if 'from' in glmTree[key].keys():
			if glmTree[key]['from'] not in from_node_phases.keys():
				from_node_phases[glmTree[key]['from']] = glmTree[key]['phases']
			else:
				from_node_phases[glmTree[key]['from']] = from_node_phases[glmTree[key]['from']] + glmTree[key]['phases']           
		if 'to' in glmTree[key].keys():
			if glmTree[key]['to'] not in to_node_phases.keys():
				to_node_phases[glmTree[key]['to']] = glmTree[key]['phases']
			else:
				to_node_phases[glmTree[key]['to']] = to_node_phases[glmTree[key]['to']] + glmTree[key]['phases']
    
	# Determine a phase mismatch            
	for node in from_node_phases.keys():
		if node in to_node_phases.keys():
			for phase in from_node_phases[node]:
				if phase != 'N' and phase != 'D' and phase != 'S':
					if phase not in to_node_phases[node]:
						#raise RuntimeError("Phase Mismatch on node type object {:s}.".format(node))
						warnings.warn("Phase mismatch on node type object {:s}. From: {:s} To: {:s}.".format(node, from_node_phases[node],to_node_phases[node]),RuntimeWarning)
    
	# Determine the phases for the node object
	# Combine all the phases collected from the 'to' and 'from' links
	for fnode in from_node_phases.keys():
		node_phases[fnode] = from_node_phases[fnode]
		for tnode in to_node_phases.keys():
			if tnode == fnode:
				node_phases[fnode] = from_node_phases[fnode] + to_node_phases[fnode]
    
	# If there are no 'from' links connected to the node object collect phases from the 'to' links                
	for tnode in to_node_phases.keys():
		if tnode not in node_phases.keys():
			node_phases[tnode] = to_node_phases[tnode]
    
	# Find the unique phase information and place them in the node like object dictionaries
	for node in node_phases.keys():
		phase = ''
		if 'A' in node_phases[node]:
			phase = phase + 'A'
		if 'B' in node_phases[node]:
			phase = phase + 'B'
		if 'C' in node_phases[node]:
			phase = phase + 'C'
		if 'N' in node_phases[node]:
			phase = phase + 'N'
		elif 'S' in node_phases[node]:
			phase = phase + 'S'
            
		for x in glmTree.keys():
			if 'name' in glmTree[x].keys() and glmTree[x]['name'] == node and 'phases' not in glmTree[x].keys():
				glmTree[x]['phases'] = phase
                      
	# Delete islanded nodes
	for key in glmTree.keys():
		if 'object' in glmTree[key].keys() and glmTree[key]['object'] in ['node','meter','load','triplex_node','triplex_meter','triplex_load'] and ('parent' in glmTree[key].keys() and 'parent' not in glmTree[key].keys()):
			if glmTree[key]['name'] not in node_phases.keys():
				print('Deleting islanded object.')
				print(glmTree[key]['name'])
				del glmTree[key]
                    
	# Fix nominal voltage
	def fix_nominal_voltage(glm_dict, volt_dict):
		for x in glm_dict:
			if 'parent' in glm_dict[x].keys() and glm_dict[x]['parent'] in volt_dict.keys() and glm_dict[x]['name'] not in volt_dict.keys():
				glm_dict[x]['nominal_voltage'] = volt_dict[glm_dict[x]['parent']]
				volt_dict[glm_dict[x]['name']] = glm_dict[x]['nominal_voltage']
			elif 'from' in glm_dict[x].keys() and glm_dict[x]['from'] in volt_dict.keys() and glm_dict[x]['name'] not in volt_dict.keys(): 
				if glm_dict[x]['object'] == 'transformer':
					# get secondary voltage from transformer configuration
					cnfg = glm_dict[x]['configuration']
					for y in glm_dict:
						if glm_dict[y]['name'] == cnfg:
							nv = glm_dict[y]['secondary_voltage']
							glm_dict[x]['nominal_voltage'] = nv
				else:
					glm_dict[x]['nominal_voltage'] = volt_dict[glm_dict[x]['from']]                 
					volt_dict[glm_dict[x]['name']] = glm_dict[x]['nominal_voltage']
				for y in glm_dict:
					if 'name' in glm_dict[y] and glm_dict[y]['name'] == glm_dict[x]['to']:
						if 'nominal_voltage' in glm_dict[x].keys():
							glm_dict[y]['nominal_voltage'] = glm_dict[x]['nominal_voltage']
							volt_dict[glm_dict[y]['name']] = glm_dict[y]['nominal_voltage'] 
						else:
							warn.warnings("No nominal voltage for object name {:s}.".format(glm_dict[x]['name']),RuntimeWarning)
                                   
	parent_voltage = {}
	current_parents = len(parent_voltage)
	previous_parents = 0
    
	for obj in glmTree:
		if 'bustype' in glmTree[obj] and glmTree[obj]['bustype'] == 'SWING':
			parent_voltage[glmTree[obj]['name']] = glmTree[obj]['nominal_voltage']
			current_parents = len(parent_voltage)
            
	while current_parents > previous_parents:
		fix_nominal_voltage(glmTree, parent_voltage)
		previous_parents = current_parents
		current_parents = len(parent_voltage)
        
	# figure out the PT rating for regulators
	for x in glmTree.keys():
		if 'object' in glmTree[x].keys() and glmTree[x]['object'] == 'regulator':
			for y in glmTree[x].keys():
				if type(glmTree[x][y]) is dict:
					if 'Control' in glmTree[x][y].keys() and glmTree[x][y]['Control'] == 'LINE_DROP_COMP': 
						glmTree[x][y]['power_transducer_ratio'] = str(float(glmTree[x]['nominal_voltage'])/120)
                        
					elif 'Control' in glmTree[x][y].keys() and glmTree[x][y]['Control'] == 'OUTPUT_VOLTAGE':
						band_center = float(glmTree[x][y]['band_center'])
						band_width = float(glmTree[x][y]['band_width'])
						glmTree[x][y]['band_center'] = str(band_center*float(glmTree[x]['nominal_voltage']))
						glmTree[x][y]['band_width'] = str(band_width*float(glmTree[x]['nominal_voltage']))
    
	# Delete nominal_voltage from link objects
	del_nom_volt_list = ['overhead_line', 'underground_line', 'regulator', 'transformer', 'switch', 'fuse', 'ZIPload', 'diesel_dg']
	for x in glmTree:
		if 'object' in glmTree[x].keys() and glmTree[x]['object'] in del_nom_volt_list and 'nominal_voltage' in glmTree[x].keys():
			del glmTree[x]['nominal_voltage']
    
	return glmTree
	
def print_base_GLM(baseDict,f_out):

	# fix load_class property in loads and triplex_nodes
	# change from id number to 'C' for load objects
	# remove load_class from triplex_node objects
	for x in baseDict:
		if 'load_class' in baseDict[x].keys():
			if baseDict[x]['load_class'] in ['C','6','7','8']:
				baseDict[x]['load_class'] = 'C'
			else:
				del baseDict[x]['load_class']

	glm_string = feeder.sortedWrite(baseDict)
	file = open(f_out, 'w')
	file.write('#set iteration_limit=50\n')
	file.write('#set profiler=1\n')
	file.write('#set pauseatexit=1\n')
	file.write('#define stylesheet=http://gridlab-d.svn.sourceforge.net/viewvc/gridlab-d/trunk/core/gridlabd-2_0\n\n')
	file.write('clock{\n\ttimezone EST+5EDT;\n\ttimestamp \'2000-01-01 0:00:00\';\n}\n\n')
	file.write('module powerflow {\n\tsolver_method NR;\n\tdefault_maximum_voltage_error 1e-9;\n};\n\n')
	file.write('module tape;\n\n')
	file.write(glm_string)
	file.close()
	
def main():
	db_network = 'Duke_2407_Net.mdb'
	db_equipment = 'Duke_2407_Eq.mdb'
	id_feeder = None
	conductors = 'duke_conductor_data.csv'
	cyme_base = convert_cyme_model(db_network, db_equipment, id_feeder, conductors)
	
	print_base_GLM(cyme_base, 'output.glm')
	

if __name__ == '__main__':
	main()
glm_object_dict = {}

glm_object_dict[0] = {'object' : 'overhead_line_conductor',
					'name' : 'ohlc_100',
					'geometric_mean_radius' : '0.0244',
					'resistance' : '0.306'}

glm_object_dict[1] = {'object' : 'overhead_line_conductor',
					'name' : 'ohlc_101',
					'geometric_mean_radius' : '0.00814',
					'resistance' : '0.592'}

glm_object_dict[2] = {'object' : 'line_spacing',
					'name' : 'ls_200',
					'distance_AB' : '2.5',
					'distance_BC' : '4.5',
					'distance_AC' : '7.0',
					'distance_AN' : '5.656854',
					'distance_BN' : '4.272002',
					'distance_CN' : '5.0'}

glm_object_dict[3] = {'object' : 'line_configuration',
					'name' : 'lc_300',
					'conductor_A' : 'ohlc_100',
					'conductor_B' : 'ohlc_100',
					'conductor_C' : 'ohlc_100',
					'conductor_N' : 'ohlc_101',
					'spacing' : 'ls_200'}

glm_object_dict[4] = {'object' : 'transformer_configuration',
					'name' : 'tc_400',
					'connect_type' : '1',
					'power_rating' : '70000',
					'powerA_rating' : '8750',
					'powerB_rating' : '17500',
					'powerC_rating' : '43750',
					'primary_voltage' : '7200',
					'secondary_voltage' : '2400',
					'resistance' : '0.01',
					'reactance' : '0.06'}
					
glm_object_dict[5] = {'object' : 'transformer_configuration',
					'name' : 'SPCT_config_A_500k',
					'connect_type' : 'SINGLE_PHASE_CENTER_TAPPED',
					'install_type' : 'PADMOUNT',
					'primary_voltage' : '2400',
					'secondary_voltage' : '124',
					#'power_rating' : '500',
					#'powerA_rating' : '500',
					'power_rating' : '8750',
					'powerA_rating' : '8750',
					'impedance' : '0.015+0.0675j'}

glm_object_dict[6] = {'object' : 'transformer_configuration',
					'name' : 'SPCT_config_B_500k',
					'connect_type' : 'SINGLE_PHASE_CENTER_TAPPED',
					'install_type' : 'PADMOUNT',
					'primary_voltage' : '2400',
					'secondary_voltage' : '124',
					# 'power_rating' : '500',
					# 'powerB_rating' : '500',
					'power_rating' : '17500',
					'powerB_rating' : '17500',
					'impedance' : '0.015+0.0675j'}

glm_object_dict[7] = {'object' : 'transformer_configuration',
					'name' : 'SPCT_config_C_667k',
					'connect_type' : 'SINGLE_PHASE_CENTER_TAPPED',
					'install_type' : 'PADMOUNT',
					'primary_voltage' : '2400',
					'secondary_voltage' : '124',
					# 'power_rating' : '666.7',
					# 'powerC_rating' : '666.7',
					'power_rating' : '43750',
					'powerC_rating' : '43750',
					'impedance' : '0.015+0.0675j'}
					
glm_object_dict[8] = {'object' : 'node',
					'name' : 'node1',
					'phases' : 'ABCN',
					'bustype' : 'SWING',
					'voltage_A' : '+7199.558+0.000j',
					'voltage_B' : '-3599.779-6235.000j',
					'voltage_C' : '-3599.779+6235.000j',
					'nominal_voltage' : '7200'}

glm_object_dict[9] = {'object' : 'overhead_line',
					'name' : 'oh_12',
					'phases' : 'ABCN',
					'from' : 'node1',
					'to' : 'node2',
					'length' : '2000',
					'configuration' : 'lc_300'}

glm_object_dict[10] = {'object' : 'node',
					'name' : 'node2',
					'phases' : 'ABCN',
					'voltage_A' : '+7199.558+0.000j',
					'voltage_B' : '-3599.779-6235.000j',
					'voltage_C' : '-3599.779+6235.000j',
					'nominal_voltage' : '7200'}

glm_object_dict[11] = {'object' : 'transformer',
					'name' : 't_23',
					'phases' : 'ABCN',
					'from' : 'node2',
					'to' : 'node3',
					'configuration' : 'tc_400'}

glm_object_dict[12] = {'object' : 'node',
					'name' : 'node3',
					'phases' : 'ABCN',
					'voltage_A' : '+2401.777+0.000j',
					'voltage_B' : '-1200.889-2080.000j',
					'voltage_C' : '-1200.889+2080.000j',
					'nominal_voltage' : '2400'}

glm_object_dict[13] = {'object' : 'overhead_line',
					'name' : 'oh_34',
					'phases' : 'ABCN',
					'from' : 'node3',
					'to' : 'node4',
					'length' : '2500',
					'configuration' : 'lc_300'}

glm_object_dict[14] = {'object' : 'node',
					'name' : 'node4',
					'phases' : 'ABCN',
					'voltage_A' : '+2401.777+0.000j',
					'voltage_B' : '-1200.889-2080.000j',
					'voltage_C' : '-1200.889+2080.000j',
					'nominal_voltage' : '2400'}
					
glm_object_dict[15] = {'object' : 'transformer',
					'name' : 'SPCT_A_n4-tn4',
					'phases' : 'AS',
					'from' : 'node4',
					'to' : 'tn4A',
					'configuration' : 'SPCT_config_A_500k'}

glm_object_dict[16] = {'object' : 'transformer',
					'name' : 'SPCT_B_n4-tn4',
					'phases' : 'BS',
					'from' : 'node4',
					'to' : 'tn4B',
					'configuration' : 'SPCT_config_B_500k'}

glm_object_dict[17] = {'object' : 'transformer',
					'name' : 'SPCT_C_n4-tn4',
					'phases' : 'CS',
					'from' : 'node4',
					'to' : 'tn4C',
					'configuration' : 'SPCT_config_C_667k'}

glm_object_dict[18] = {'object' : 'triplex_node',
					'name' : 'tn4A',
					'phases' : 'AS',
					#'power_12' : '318750.000+197544.508j',
					'power_12' : '785369.750+258138.553j',
					'nominal_voltage' : '120'}

glm_object_dict[19] = {'object' : 'triplex_node',
					'name' : 'tn4B',
					'phases' : 'BS',
					#'power_12' : '450000.000+217945.947j',
					'power_12' : '1570739.500+516277.107j',
					'nominal_voltage' : '120'}

glm_object_dict[20] = {'object' : 'triplex_node',
					'name' : 'tn4C',
					'phases' : 'CS',
					#'power_12' : '593750.000+195156.187j',
					'power_12' : '3926848.750+1290692.768j',
					'nominal_voltage' : '120'}

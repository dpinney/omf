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
					'power_rating' : '7000',
					'powerA_rating' : '875',
					'powerB_rating' : '1750',
					'powerC_rating' : '4375',
					'primary_voltage' : '7200',
					'secondary_voltage' : '2400',
					'resistance' : '0.01',
					'reactance' : '0.06'}

glm_object_dict[5] = {'object' : 'node',
					'name' : 'node1',
					'phases' : 'ABCN',
					'bustype' : 'SWING',
					'voltage_A' : '+7199.558+0.000j',
					'voltage_B' : '-3599.779-6235.000j',
					'voltage_C' : '-3599.779+6235.000j',
					'nominal_voltage' : '7200'}

glm_object_dict[6] = {'object' : 'overhead_line',
					'name' : 'oh_12',
					'phases' : 'ABCN',
					'from' : 'node1',
					'to' : 'node2',
					'length' : '2000',
					'configuration' : 'lc_300'}

glm_object_dict[7] = {'object' : 'node',
					'name' : 'node2',
					'phases' : 'ABCN',
					'voltage_A' : '+7199.558+0.000j',
					'voltage_B' : '-3599.779-6235.000j',
					'voltage_C' : '-3599.779+6235.000j',
					'nominal_voltage' : '7200'}

glm_object_dict[8] = {'object' : 'transformer',
					'name' : 't_23',
					'phases' : 'ABCN',
					'from' : 'node2',
					'to' : 'node3',
					'configuration' : 'tc_400'}

glm_object_dict[9] = {'object' : 'node',
					'name' : 'node3',
					'phases' : 'ABCN',
					'voltage_A' : '+2401.777+0.000j',
					'voltage_B' : '-1200.889-2080.000j',
					'voltage_C' : '-1200.889+2080.000j',
					'nominal_voltage' : '2400'}

glm_object_dict[10] = {'object' : 'overhead_line',
					'name' : 'oh_34',
					'phases' : 'ABCN',
					'from' : 'node3',
					'to' : 'node4',
					'length' : '2500',
					'configuration' : 'lc_300'}

glm_object_dict[11] = {'object' : 'node',
					'name' : 'node4',
					'phases' : 'ABCN',
					'voltage_A' : '+2401.777+0.000j',
					'voltage_B' : '-1200.889-2080.000j',
					'voltage_C' : '-1200.889+2080.000j',
					'nominal_voltage' : '2400'}

glm_object_dict[12] = {'object' : 'load',
					  'parent' : 'node4',
					  'name' : 'l4A',
					  'phases' : 'AN',
					  'constant_power_A' : '785369.750+258138.553j',
					  'load_class' : 'C',
					  'nominal_voltage' : '2400'}

glm_object_dict[13] = {'object' : 'load',
					  'parent' : 'node4',
					  'name' : 'l4B',
					  'phases' : 'BN',
					  'constant_power_B' : '1570739.500+516277.107j',
					  'load_class' : 'C',
					  'nominal_voltage' : '2400'}

glm_object_dict[14] = {'object' : 'load',
					  'parent' : 'node4',
					  'name' : 'l4C',
					  'phases' : 'CN',
					  'constant_power_C' : '3926848.750+1290692.768j',
					  'load_class' : 'C',
					  'nominal_voltage' : '2400'}
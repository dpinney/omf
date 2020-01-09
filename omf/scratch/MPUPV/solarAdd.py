from omf import feeder
import omf.solvers.gridlabd

feed = feeder.parse('GC-12.47-1.glm')
maxKey = feeder.getMaxKey(feed)
print(feed[1])
feed[maxKey + 1] = {
	'object': 'node', 'name': 'test_solar_node', 'phases': 'ABCN', 
	'nominal_voltage': '7200'
}

feed[maxKey + 2] = {
	'object': 'underground_line', 'name': 'test_solar_line', 'phases': 'ABCN',
	'from': 'test_solar_node', 'to': 'GC-12-47-1_node_26', 'length': '100',
	'configuration': 'line_configuration:6'
}

feed[maxKey + 3] = {
	'object': 'meter', 'name': 'test_solar_meter', 'parent': 'test_solar_node',
	'phases': 'ABCN', 'nominal_voltage': '480'
}
feed[maxKey + 4] = {
	'object': 'inverter', 'name': 'test_solar_inverter', 'parent': 'test_solar_meter',
	'phases': 'AS', 'inverter_type': 'PWM', 'power_factor': '1.0', 
	'generator_status': 'ONLINE', 'generator_mode': 'CONSTANT_PF'
					}
feed[maxKey + 5] = {
	'object': 'solar', 'name': 'test_solar', 'parent': 'test_solar_inverter', 'area': '1000000 sf',
	'generator_status': 'ONLINE', 'efficiency': '0.2', 'generator_mode': 'SUPPLY_DRIVEN',
	'panel_type': 'SINGLE_CRYSTAL_SILICON'
}

feed[maxKey + 6] = {
	'object': 'recorder', 'parent': 'test_solar_meter', 'property': 'voltage_A.real,voltage_A.imag,voltage_B.real,voltage_B.imag,voltage_C.real,voltage_C.imag', 
	'file': 'GC-addSolar-voltages.csv', 'interval': '60', 'limit': '1440' 
}

omf.solvers.gridlabd.runInFilesystem(feed, keepFiles = True, workDir = '.', glmName = 'GC-solarAdd.glm')
'''
output = open('GC-solarAdd.glm', 'w')
output.write(feeder.write(feed))
output.close()
'''
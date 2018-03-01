"""
This file contains a fuction to add external controllers to a feeder based on the feeder configuration

	add_external_control(feeder_dict, config_file, last_key=0):
		This fuction adds external controllers based on the configuration of the feeder

Created Feburary 7, 2017 by Jacob Hansen (jacob.hansen@pnnl.gov)

Copyright (c) 2016 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
Government, including the right to distribute to other Government contractors.
"""

def add_external_control(feeder_dict, config_file, filePath, last_key=0):
	"""
	This fuction adds external controllers based on the configuration of the feeder

	Inputs
		feeder_dict - dictionary containing the full feeder
		config_file - dictionary that contains the configurations of the feeder
		file_path - file path to where you created the modified GLM
		last_object_key - Last object key

	Outputs
		feeder_dict -  dictionary containing the full feeder
	"""

	# Check if last_key is already in glm dictionary
	def unused_key(key):
		if key in feeder_dict.keys():
			while key in feeder_dict.keys():
				key += 1

		return key

	# let's determine the next available key
	last_key = unused_key(last_key)

	# Check if we need to add external controllers to the houses
	if config_file['control_HVAC']:
		fileName = open(filePath + '/houseList.txt', 'w')
		try:
			control_dict = []
			for x in feeder_dict:
				if 'object' in feeder_dict[x] and feeder_dict[x]['object'] == 'house':
					control_dict.append(feeder_dict[x]['name'])
					fileName.write('{:s}\n'.format(feeder_dict[x]['name']))
		finally:
			fileName.close()

		for controlObject in control_dict:
			# adding the external controller
			feeder_dict[last_key] = {'object' : 'external_control',
									   'parent' : '{:s}'.format(controlObject),
									   'name' : '{:s}_external_control'.format(controlObject)}

			if config_file['respect_local_control']:
				feeder_dict[last_key]['respect_local_control'] = 'true'
			else:
				feeder_dict[last_key]['respect_local_control'] = 'false'

			last_key = unused_key(last_key)

			# adding a player object to the external controller we just created
			feeder_dict[last_key] = {'object': 'player',
									 'parent': '{:s}_external_control'.format(controlObject),
									 'name': '{:s}_external_control_player'.format(controlObject),
									 'property' : 'control_signal',
									 'file' : '{:s}.player'.format(controlObject)}

			last_key = unused_key(last_key)

	if config_file['control_WH']:
		fileName = open(filePath + '/waterHeaterList.txt', 'w')
		try:
			control_dict = []
			for x in feeder_dict:
				if 'object' in feeder_dict[x] and feeder_dict[x]['object'] == 'waterheater':
					control_dict.append(feeder_dict[x]['name'])
					fileName.write('{:s}\n'.format(feeder_dict[x]['name']))
		finally:
			fileName.close()

		for controlObject in control_dict:
			# adding the external controller
			feeder_dict[last_key] = {'object': 'external_control',
									 'parent': '{:s}'.format(controlObject),
									 'name': '{:s}_external_control'.format(controlObject)}

			if config_file['respect_local_control']:
				feeder_dict[last_key]['respect_local_control'] = 'true'
			else:
				feeder_dict[last_key]['respect_local_control'] = 'false'

			last_key = unused_key(last_key)

			# adding a player object to the external controller we just created
			feeder_dict[last_key] = {'object': 'player',
									 'parent': '{:s}_external_control'.format(controlObject),
									 'name': '{:s}_external_control_player'.format(controlObject),
									 'property': 'control_signal',
									 'file': '{:s}.player'.format(controlObject)}

			last_key = unused_key(last_key)

	if config_file['control_EV']:
		raise Exception('EV external control is not implemented yet!')

	return feeder_dict

if __name__ == '__main__':
	pass
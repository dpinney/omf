import os
import random
from omf import feeder

def addRandomSolar(feed, item, count):
	'''Adds a solar inverter and panel set, assgined to A, B, or C phase randomly'''
	phase_list = ['A','B','C']
	maxKey = feeder.getMaxKey(feed)
	feed[maxKey + 1] = {
	'object': 'inverter', 'name': 'new_solar_' + str(count), 'parent': feed[item]['name'],
	'phases': random.choice(phase_list) +'S', 'inverter_type': 'PWM', 'power_factor': '1.0',
	'generator_status': 'ONLINE', 'generator_mode': 'CONSTANT_PF'
					}
	feed[maxKey + 2] = {
	'object': 'solar', 'name': 'solar_' + str(count), 'parent': 'new_solar_' + str(count), 'area': '1000 sf',
	'generator_status': 'ONLINE', 'efficiency': '0.2', 'generator_mode': 'SUPPLY_DRIVEN',
	'panel_type': 'SINGLE_CRYSTAL_SILICON'
}

def createNewGLM(glmFile):
	'''Takes a GLM file and adds a solar inverter/panel pair to each meter on GLM.  Based on Taxonomic Feeders'''
	feed = feeder.parse('./Taxonomy_Feeders-master/'+glmFile)

	'''Following block provides automatic coversion for taxonmic feeders'''
	if 'timestamp' in feed[0]:
		feed[0]['starttime'] = feed[0].pop('timestamp')
	if 'omftype' in feed[1] and '#set' in feed[1]['omftype']:
		feed[1]['omftype'] = 'module'
		feed[1]['argument']  = 'tape;\nmodule generators'
	
	meter_list = []
	for item in feed:
		if 'object' not in feed[item]:
			pass
		elif 'meter' in feed[item]['object']:
			meter_list.append(item)

	count = 1
	for item in meter_list:
		addRandomSolar(feed, item, count)
		count += 1

	output = open('./Taxonomy_Feeders-solar/'+'.'.join(glmFile.split('.')[:2])+'-solarAdd.glm', 'w')
	output.write(feeder.write(feed))
	output.close()

for filename in os.listdir('./Taxonomy_Feeders-master'):
	createNewGLM(filename)
'''
Try to import another rural feeder in to the OMF.

Feeder 16: R4-25.00-1
This feeder is a representation of a lightly populated rural area. The load is composed on single family residences with some light commercial. Approximately 88% of the circuit-feet are overhead and 12% underground. This feeder has connections to adjacent feeders. This combined with the low load density ensures the ability to transfer most of the loads from other feeders, and vice versa. Most of the load is located at a substantial distance from the substation, as is common for higher voltages in rural areas.

TODO
XXX Manual bug fixes: change timestamp to starttime in clock. Make sub reg reference its config by name. change the start time to match the prices in the player.
XXX Attach additional utility tech.
XXX Attach prosumers.
OOO Vary prosumers. What do we vary? Size of house...
'''

import omf

# Read in the glm.
baseFeed = omf.feeder.parse('base_R4-25.00-1.glm')

# Fix the colon-number things.
for k in baseFeed:
	thisOb = baseFeed[k]
	if 'object' in thisOb:
		# Name things without names:
		if 'name' not in thisOb:
			thisOb['name'] = thisOb['object'].replace(':','_')
		# Remove the colon and digits from the object:
		if ':' in thisOb['object']:
			thisOb['object'] = thisOb['object'][0:thisOb['object'].find(':')]
	# Change references to use the underscore convention:
	for k2 in thisOb:
		if ':' in thisOb[k2] and 'clock' not in thisOb:
			thisOb[k2] = thisOb[k2].replace(':','_')

# Disembed the feeder.
omf.feeder.fullyDeEmbed(baseFeed)

# Remove all asserts.
for key in baseFeed.keys():
	if baseFeed[key].get('object','') == 'complex_assert':
		del baseFeed[key]

# Attach additional utility technology (DG, Caps, IVVC).
utilityNewTech = omf.feeder.parse('utilityNewTech.glm')
maxKey = omf.feeder.getMaxKey(baseFeed) + 1
for key in utilityNewTech:
	baseFeed[maxKey + key] = dict(utilityNewTech[key])

def nameToKey(tree, name):
	''' Find the key for the object with the name, or None if nothing is found. '''
	try:
		return min([k for k in tree if tree[k].get('name','') == name])
	except:
		return None

prosumerTemplate = omf.feeder.parse('prosumer.glm')

def randomProsumer(feed, nodeKey, houseInt):
	''' Add a single prosumer to feed replacing triplex_node at nodeKey
		with house (etc.) with new ID houseInt. '''
	# tPower = float(feed[nodeKey]['power_1'].replace('j','').split('+')[0])
	tMeter = feed[nameToKey(feed, feed[nodeKey]['parent'])]
	del feed[nodeKey]
	maxKey = omf.feeder.getMaxKey(feed) + 1
	for key in prosumerTemplate:
		newKey = maxKey + key
		feed[newKey] = dict(prosumerTemplate[key])
		# Make sure the prosumer names are unique according to the houseInt:
		for prop in ['name','parent']:
			if prop in feed[newKey]:
				feed[newKey][prop] += str(houseInt)
		# Parent to the tMeter:
		if feed[newKey].get('object','') in ['house','inverter']:
			feed[newKey]['parent'] = tMeter['name']		
		if 'sense_object' in feed[newKey]:
			feed[newKey]['sense_object'] = tMeter['name']
		# Make phasing match tMeter:
		if 'phases' in feed[newKey]:
			feed[newKey]['phases'] = tMeter['phases']
		# Augment the meter to make it market-aware:
		marketMeterStuff = 	{
			'meter_power_consumption':'2+11j',
			'bill_mode':'HOURLY',
			'monthly_fee':'10.00',
			'bill_day':'1',
			'power_market':'Market_1' }
		for k2 in marketMeterStuff:
			tMeter[k2] = marketMeterStuff[k2]

tripLoadKeys = [k for k in baseFeed if baseFeed[k].get('object','')=='triplex_node' and baseFeed[k].get('parent','')!='']

# TODO: add all prosumers.
# randomProsumer(baseFeed, min(tripLoadKeys), 123)
for i, tripKey in enumerate(tripLoadKeys):
	randomProsumer(baseFeed, tripKey, i)

# Get attachments.
superAttach = {fName:open(fName).read() for fName in ['superSchedules.glm','superClimate.tmy2','superCpp.player', 'superClearingPrice.player']}

# Run the thing.
print 'GLD OUTPUT============='
output = omf.solvers.gridlabd.runInFilesystem(
	baseFeed,
	attachments=superAttach, 
	keepFiles=True, 
	workDir='./runningDir',
	glmName='superModelTinyModified.glm')
print output['stderr'],'\n======================='

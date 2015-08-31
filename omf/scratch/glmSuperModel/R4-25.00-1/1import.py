'''
Try to import another rural feeder in to the OMF.

Feeder 16: R4-25.00-1
This feeder is a representation of a lightly populated rural area. The load is composed on single family residences with some light commercial. Approximately 88% of the circuit-feet are overhead and 12% underground. This feeder has connections to adjacent feeders. This combined with the low load density ensures the ability to transfer most of the loads from other feeders, and vice versa. Most of the load is located at a substantial distance from the substation, as is common for higher voltages in rural areas.

TODO
XXX Manual bug fixes: change timestamp to starttime in clock. Make sub reg reference its config by name. change the start time to match the prices in the player.
XXX Attach additional utility tech.
XXX Attach prosumers.
XXX Consumer versus prosumer model.
XXX Vary prosumers. What do we vary? See proVaryingThings.txt.
XXX Bonus: IVVC.
XXX Bonus: single phase wind.
OOO Bonus: Add a third case (different price signals, more utility control).
OOO Full model update and ship to production.
'''

import omf, json, random

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

# Write a clean copy of the GLM for testing elsewhere.
with open('base_R4-25.00-1_CLEAN.glm','w+') as cleanCopy:
	cleanCopy.write(omf.feeder.sortedWrite(baseFeed))

# Attach additional utility technology (DG, Caps, IVVC).
utilityNewTech = omf.feeder.parse('proUtility.glm')
maxKey = omf.feeder.getMaxKey(baseFeed) + 1
for key in utilityNewTech:
	baseFeed[maxKey + key] = dict(utilityNewTech[key])

def getByKeyVal(tree, key, value, getAll=False):
	''' Return (one or more) keys to the first item in tree where that objects key=val.'''
	allMatches = [k for k in tree if tree[k].get(key,'') == value]
	if getAll:
		return allMatches
	elif (not getAll) and len(allMatches) > 0:
		return allMatches[0]
	else:
		return None

def randomProsumer(feed, nodeKey, houseInt):
	''' Add a single prosumer to feed replacing triplex_node at nodeKey
		with house (etc.) with new ID houseInt. '''
	prosumerTemplate = omf.feeder.parse('prosumer.glm')
	tMeter = feed[getByKeyVal(feed, 'name', feed[nodeKey]['parent'])]
	tPower = float(feed[nodeKey]['power_1'].replace('j','').split('+')[0])
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
		# Vary some things.
		if 'schedule_skew' in feed[newKey]:
			feed[newKey]['schedule_skew'] = int(feed[newKey]['schedule_skew'])* \
				random.gauss(0,1)
		if 'floor_area' in feed[newKey]:
			feed[newKey]['floor_area'] = str(tPower)
		if 'area' in feed[newKey]:
			feed[newKey]['area'] = str(random.uniform(400,1600)) + ' sf'
		if 'battery_capacity' in feed[newKey]:
			feed[newKey]['battery_capacity'] = '7 kWh' # Tesla Powerwall daily cycle version.
		if 'base_power' in feed[newKey]:
			feed[newKey]['base_power'] += '*' + str(random.uniform(0.5,3.0))

# Add all prosumers.
tripNodeKeys = getByKeyVal(baseFeed, 'object', 'triplex_node', getAll=True)
tripLoadKeys = [k for k in tripNodeKeys if 'parent' in baseFeed[k]]
for i, tripKey in enumerate(tripLoadKeys):
	randomProsumer(baseFeed, tripKey, i)

# Get attachments.
attachNames = ['superSchedules.glm','superClimate.tmy2','superCpp.player', 'superClearingPrice.player']
superAttach = {fName:open(fName).read() for fName in attachNames}

# Run test the thing.
print 'GLD OUTPUT============='
output = omf.solvers.gridlabd.runInFilesystem(
	baseFeed,
	attachments=superAttach, 
	keepFiles=True, 
	workDir='./runningDir',
	glmName='xOut_superModelRural.glm')
print output['stderr'],'\n======================='

# If everything worked out, create an OMF-formatted JSON file.
fullFeed = dict(omf.feeder.newFeederWireframe)
fullFeed['tree'] = baseFeed
fullFeed['attachments'] = superAttach
with open('xOut_superModelRural.json','w+') as outFile:
	json.dump(fullFeed, outFile, indent=4)

# Also create a no-tech version.
noTechFeed = dict(baseFeed)
newTech = ['solar', 'battery', 'inverter', 'windturb_dg', 'evcharger_det',
	'passive_controller', 'diesel_dg', 'capacitor']
for k in noTechFeed.keys():
	if noTechFeed[k].get('object','') in newTech:
		del noTechFeed[k]
fullNoTech = dict(omf.feeder.newFeederWireframe)
fullNoTech['tree'] = noTechFeed
fullNoTech['attachments'] = superAttach
with open('xOut_regularModelRural.json','w+') as outFile:
	json.dump(fullNoTech, outFile, indent=4)

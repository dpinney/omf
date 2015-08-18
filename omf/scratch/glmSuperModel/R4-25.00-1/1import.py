'''
Try to import another rural feeder in to the OMF.

Feeder 16: R4-25.00-1
This feeder is a representation of a lightly populated rural area. The load is composed on single family residences with some light commercial. Approximately 88% of the circuit-feet are overhead and 12% underground. This feeder has connections to adjacent feeders. This combined with the low load density ensures the ability to transfer most of the loads from other feeders, and vice versa. Most of the load is located at a substantial distance from the substation, as is common for higher voltages in rural areas.

TODO
XXX Manual bug fixes: change timestamp to starttime in clock. Make sub reg reference its config by name. change the start time to match the prices in the player.
XXX Attach additional utility tech.
OOO Attach prosumers. What do we vary? Size of house...
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

def randomProsumer(size):
	prosumer = {}
	# TODO: put it here.
	return prosumer

# Add a prosumer.
tripLoadKeys = [k for k in baseFeed if baseFeed[k].get('object','')=='triplex_node' and baseFeed[k].get('parent','')!='']
target = min(tripLoadKeys)
tPower = float(baseFeed[target]['power_1'].replace('j','').split('+')[0])
tPhase = baseFeed[target]['phases']
tParentName = baseFeed[target]['parent']
tParentKey = nameToKey(baseFeed, tParentName)
# del baseFeed[target]
maxKey = omf.feeder.getMaxKey(baseFeed) + 1
prosumer = omf.feeder.parse('prosumer.glm')
# TODO: augment the meter.
for key in prosumer:
	baseFeed[maxKey + key] = dict(prosumer[key])
	if baseFeed[maxKey + key].get('object','') == 'triplex_meter': baseFeed[maxKey + key]['parent'] = tParentName
# TODO: add all the prosumers.

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

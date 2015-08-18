'''
Try to import another rural feeder in to the OMF.

Feeder 16: R4-25.00-1
This feeder is a representation of a lightly populated rural area. The load is composed on single family residences with some light commercial. Approximately 88% of the circuit-feet are overhead and 12% underground. This feeder has connections to adjacent feeders. This combined with the low load density ensures the ability to transfer most of the loads from other feeders, and vice versa. Most of the load is located at a substantial distance from the substation, as is common for higher voltages in rural areas.

TODO
XXX Manual bug fixes: change timestamp to starttime in clock. Make sub reg reference its config by name.
OOO Attach prosumers. What do we vary?

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

# allMeters = [baseFeed[k]['name'] for k in baseFeed.keys() if baseFeed[k].get('object','') == 'triplex_meter']
# print allMeters

# Run the thing.
output = omf.solvers.gridlabd.runInFilesystem(
	baseFeed,
	attachments={}, 
	keepFiles=True, 
	workDir='./runningDir',
	glmName='superModelTinyModified.glm')
print 'GLD OUTPUT=============\n', output['stderr'],'\n======================='

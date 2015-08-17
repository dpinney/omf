''' Make a GLD superModel. 

TODO:
XXX Get one prosumer working (ish).
XXX Attachments? Added.

'''


import omf, os, json

''' FIRST PART: GET PROTOYPICAL GLM IN TO JSON '''

# Read in the glm (or cache, if it's cached.)
superName = './superModelTiny.json'
if not os.path.isfile(superName):
	baseFeed = omf.feeder.parse('./superModelTiny.glm')
else:
	baseFeed = json.load(open(superName))

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

# Write out the json version.
with open(superName, 'w') as jFile:
	json.dump(baseFeed, jFile, indent=4)

''' SECOND PART: MAKE THE FEEDER SUPER '''

# Attach a prosumer.
superConsumer = omf.feeder.parse('./prosumer.glm')
maxKey = omf.feeder.getMaxKey(baseFeed) + 1
meterKey = min([x for x in superConsumer.keys() if superConsumer[x].get('object','')=='triplex_meter'])
superConsumer[meterKey]['parent'] = 'R1-12-47-3_tn_1' # Meter attaching to a triplex_node.
for key in superConsumer:
	baseFeed[maxKey+key] = dict(superConsumer[key])

# Attachments
superAttach = {fName:open(fName).read() for fName in ['./superSchedules.glm','./superClimate.tmy2','superCpp.player', 'superClearingPrice.player']}

# Try a run.
output = omf.solvers.gridlabd.runInFilesystem(baseFeed, attachments=superAttach, keepFiles=True, workDir='./runningDir', glmName='superModelTinyModified.glm')

print output['stderr']

# # Add attachments to make an OMF formatted fullFeed.
# fullFeed = dict(omf.feeder.newFeederWireframe)
# fullFeed['tree'] = baseFeed
# fullFeed['attachments'] = {}
# ignoreFileNames = ['0import.py', 'glmSuperModel.json', 'superModelTiny.glm', 'glmSuperModelOmfFormat.json', '.DS_Store']
# for fName in [x for x in os.listdir('.') if x not in ignoreFileNames]:
# 	fullFeed['attachments'][fName] = open(fName, 'r').read()


# # Write full feed.
# omfName = 'glmSuperModelOmfFormat.json'
# try:
# 	os.remove(omfName)
# except:
# 	pass
# with open(omfName,'w') as jFile:
# 	json.dump(fullFeed, jFile, indent=4)

# # Try running GLD.
# outPut = omf.solvers.gridlabd.runInFilesystem(fullFeed['tree'], attachments=fullFeed['attachments'])
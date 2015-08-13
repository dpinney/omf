'''
Try to import the GLD superModel.
'''

import omf, os, json

# Read in the glm (or cache, if it's cached.)
superName = './glmSuperModelTiny.json'
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

# # Try deEmbedding all the objects.
# omf.feeder.fullyDeEmbed(baseFeed)

# Try a run.
output = omf.solvers.gridlabd.runInFilesystem(baseFeed, attachments={})

# Write out the json version.
with open(superName, 'w') as jFile:
	json.dump(baseFeed, jFile, indent=4)



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
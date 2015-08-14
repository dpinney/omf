''' Make a GLD superModel. '''

import omf, os, json

''' FIRST PART: GET PROTOYPICAL GLM IN TO JSON '''

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

# Disembed the feeder.
omf.feeder.fullyDeEmbed(baseFeed)

# Write out the json version.
with open(superName, 'w') as jFile:
	json.dump(baseFeed, jFile, indent=4)

''' SECOND PART: MAKE THE FEEDER SUPER '''

# Replace a load with a house.
# Why do that? Because it's what we need. What kind of house? Maybe pull one from the previous GLM SM. And then?
# I feel the need for a way to rapidly test this? What does that mean? Quickly go from... X to Y?
# TODO: easy way to render... feeder in OMF gridedit???? Or I could just look at lat/lon graph. BTW, it should be easy to do a 

loadList = [x for x in baseFeed.values() if x.get('object','') == 'load']
print [x.get('constant_power_C','') for x in loadList]

# Try a run.
output = omf.solvers.gridlabd.runInFilesystem(baseFeed, attachments={}, keepFiles=True, workDir='./runningDir', glmName='glmSuperModelTinyModified.glm')



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
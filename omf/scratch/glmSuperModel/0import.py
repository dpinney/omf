'''
Try to import the GLD superModel.

TODO
XXX Get to JSON.
XXX Add attachments.
OOO Run through GLD.
OOO Clean up visuals.
OOO Put in OMF.
'''

import omf, os, json

# Read in the glm (or cache, if it's cached.)
superName = './glmSuperModel.json'
if not os.path.isfile(superName):
	baseFeed = omf.feeder.parse('./R1_1247_1_t15.glm')
	with open(superName, 'w') as jFile:
		json.dump(baseFeed, jFile, indent=4)
else:
	baseFeed = json.load(open(superName))

# Add attachments to make an OMF formatted fullFeed.
fullFeed = dict(omf.feeder.newFeederWireframe)
fullFeed['tree'] = baseFeed
fullFeed['attachments'] = {}
ignoreFileNames = ['0import.py', 'glmSuperModel.json', 'R1_1247_1_t15.glm', 'glmSuperModelOmfFormat.json']
for fName in [x for x in os.listdir('.') if x not in ignoreFileNames]:
	fullFeed['attachments'][fName] = open(fName, 'r').read()

# Write full feed.
omfName = 'glmSuperModelOmfFormat.json'
try:
	os.remove(omfName)
except:
	pass
with open(omfName,'w') as jFile:
	json.dump(fullFeed, jFile, indent=4)
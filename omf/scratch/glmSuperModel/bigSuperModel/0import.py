'''
Try to import the GLD superModel.

TODO
XXX Get to JSON.
XXX Add attachments to JSON.
XXX Make all input files end with .player.
XXX Run through GLD. Fails with class error on my_std property.
XXX Support classes with multiple values? Giving each property its own class seems to work. Nope. Fix is to set up class manually in the JSON.
XXX Try to fully disembed. Closer.
XXX Debug the players. One was in the wrong format. Manually changed it in the JSON--it works.
XXX Run through GLD successfully.

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

# Try deEmbedding all the objects.
omf.feeder.fullyDeEmbed(baseFeed)

# Add attachments to make an OMF formatted fullFeed.
fullFeed = dict(omf.feeder.newFeederWireframe)
fullFeed['tree'] = baseFeed
fullFeed['attachments'] = {}
ignoreFileNames = ['0import.py', 'glmSuperModel.json', 'R1_1247_1_t15.glm', 'glmSuperModelOmfFormat.json', '.DS_Store']
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

# Try running GLD.
outPut = omf.solvers.gridlabd.runInFilesystem(fullFeed['tree'], attachments=fullFeed['attachments'])
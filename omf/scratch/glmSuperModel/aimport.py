''' Make a GLD superModel. 

TODO
XXX Which prototypical feeder? Smallest (R1-12.47-3_NR). Maybe try R4-25.00-1 later.
XXX Which solution method? Need NR.
XXX Edit the tiny feeder to remove colon-number naming.
XXX What all technologies? List below.
XXX How to get 'em on there? Get one prosumer working (ish).
XXX File attachments? Added.
XXX Run omf.models.gridlabMulti.
XXX Any way to disembed that market player? Yes, by name. Added to prosumer.
XXX Other things to add? Wind. IVVC. 
XXX Base case feeder.
XXX Pin everything in the feeder editor.
XXX Save a nice omf.model.gridlabMulti demo.
XXX Take a look at "R4-25.00-1".
XXX Descriptions of the actual prototype feeders.
OOO Change all loads to residential...
OOO Bonus points? Single phase wind. Get a realistic IVVC.
OOO Publish final to Github.

TINY FEEDER DESCRIPTION
This feeder is a representation of a moderately populated urban area. This is composed mainly of mid-sized commercial loads with some residences, mostly multi-family. Approximately 85% of the circuit-feet are overhead and 15% underground. It would be expected that this feeder is connected to adjacent feeders through normally open switches. For this reason it would be common to limit the feeder loading to 60% to ensure the ability to transfer load from other feeders, and vice versa. Since this is a small urban core the loading of the feeder is well below 60%. The majority of the load is located relatively near the substation.

TECHNOLOGIES
Per-house:
* Storage.
* Solar.
* Diesel (on a very few).
* Wind (on a very few).
* EVs.
Other stuff:
* Market auction (RTP?).
* CPP.
* IVVC.

'''


import omf, os, json

''' FIRST PART: GET PROTOYPICAL GLM IN TO JSON '''

# Read in the glm (or cache, if it's cached.)
superName = './superModelTinyBase.json'
if not os.path.isfile(superName):
	baseFeed = omf.feeder.parse('./superModelTinyBase.glm')
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

# Cache a json version.
with open(superName, 'w') as jFile:
	json.dump(baseFeed, jFile, indent=4)

# Create a base case GLM too for comparison.
caseBaseFeed = dict(omf.feeder.newFeederWireframe)
caseBaseFeed['tree'] = baseFeed
caseBaseFeed['attachments'] = {}
with open('superModelTinyZeroTech.json','w+') as outFile:
	json.dump(caseBaseFeed, outFile, indent=4)

''' SECOND PART: MAKE THE FEEDER SUPER '''

# Attach a prosumer.
superConsumer = omf.feeder.parse('./prosumer.glm')
maxKey = omf.feeder.getMaxKey(baseFeed) + 1
meterKey = min([x for x in superConsumer.keys() if superConsumer[x].get('object','')=='triplex_meter'])
superConsumer[meterKey]['parent'] = 'R1-12-47-3_tn_1' # Meter attaching to a triplex_node.
for key in superConsumer:
	baseFeed[maxKey+key] = dict(superConsumer[key])

# Attachments
superAttach = {fName:open(fName).read() for fName in ['superSchedules.glm','superClimate.tmy2','superCpp.player', 'superClearingPrice.player']}

''' THIRD PART: TEST IN GLD AND SAVE '''

# Try a run.
output = omf.solvers.gridlabd.runInFilesystem(baseFeed, attachments=superAttach, keepFiles=True, workDir='./runningDir', glmName='superModelTinyModified.glm')

print 'GLD OUTPUT=============\n', output['stderr'],'\n======================'

# If everything worked out, create an OMF-formatted JSON file.
fullFeed = dict(omf.feeder.newFeederWireframe)
fullFeed['tree'] = baseFeed
fullFeed['attachments'] = superAttach
with open('superModelTiny.json','w+') as outFile:
	json.dump(fullFeed, outFile, indent=4)
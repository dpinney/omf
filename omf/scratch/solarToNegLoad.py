import omf.feeder as feeder
from os.path import basename
import os

# TODO: Put into callable function, with glmFile and playerFolderPath as input
glmFile = '../static/testFiles/solarToNegLoads.glm'
playerFolderPath = '../static/testFiles/solarToNegLoadPlayerFiles/'
solarObjs = []
dieselObjs = []
solarKeys = []
inverterKeys = []
inverters = []
meterKeys = []
meterNames = []
meters = []
invs = []
tree = feeder.parse(glmFile)
# Find solar objects
for row in tree:
	if 'object' in tree[row].keys():
		if tree[row]['object'] == 'solar':
			solarObjs.append(tree[row])
			solarKeys.append(row)
			inverters.append(tree[row]['parent'])
# Find inverters of solar objs
for row in tree:
	if 'object' in tree[row].keys():
		if tree[row]['object'] == 'inverter':
			if tree[row]['name'] in inverters:
				inverterKeys.append(row)
				invs.append(tree[row])
				meterNames.append(tree[row]['parent'])
# Find meters 
for row in tree:
	if 'object' in tree[row].keys():
		if tree[row]['name'] in meterNames:
			meterKeys.append(row)
for row in tree:
	for met in meterNames:
		if 'name' in tree[row].keys():
			if met == tree[row]['name']:
				meters.append(tree[row])
# Create as many load objects with same name as PVs
# Attach player files to constant_power
for row in solarObjs:
	for inv in invs:
		for met in meters:
			for file in os.listdir(playerFolderPath):
				if inv['name'] == row['parent'] and inv['parent']==met['name'] and file[0:-7] == row['name']:
					player = {'object':'player',
							'file': './solarToNegLoadPlayerFiles/'+file,
							'property':'constant_power_A'
					}
					dieselObj = {'object':'triplex_load',
								'name':row['name'],
								'parent':met['parent'],
								}
					dieselObj['player'] = player
					dieselObjs.append(dieselObj)

# Delete solar objects from tree
for row in solarKeys:
	del tree[row]
# Delete inverter objects from tree
for row in inverterKeys:
	del tree[row]
# Deleter meter objects from tree
for row in meterKeys:
	del tree[row]
# Insert new generators into tree
print dieselObjs
for row in dieselObjs:
	maxKey = max(tree.keys()) +1
	tree[maxKey] = row
newTree = feeder.sortedWrite(tree)
fileName = basename(glmFile)[:-4]
# Write new glm to file
with open('../static/testFiles/'+fileName+'Neg.glm','w+') as outFile:
	outFile.write(newTree)

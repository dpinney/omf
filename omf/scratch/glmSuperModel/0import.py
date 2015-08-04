'''
Try to import the GLD superModel.

'''



import omf, os, json

# Read in the file (or cache, if it's cached.)
fName = './glmSuperModel.json'
if not os.path.isfile(fName):
	myFeed = omf.feeder.parse('./R1_1247_1_t15.glm')
	with open(fName, 'w') as jFile:
		json.dump(myFeed, jFile, indent=4)
else:
	myFeed = json.load(open(fName))


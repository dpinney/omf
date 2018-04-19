import omf
import os
from os.path import join as pJoin
import json
import json, math, random, datetime, os
import shutil
from omf.models import voltageDrop
import random

_myDir = os.path.dirname(os.path.abspath(__file__))
omfDirec =  os.path.dirname(os.path.dirname(_myDir))

thisWorkDir = omf.omfDir + '/scratch/anonymization/'
print(thisWorkDir)
filePath = pJoin(omfDirec, 'static', 'publicFeeders')

# filePath = 'Users/tuomastalvitie/omf/omf/static/public feeders/Olin Barre Geo.omd'
# filePath = omfpJoin(omfDir, 'static', 'publicFeeders', 'Olin Barre Geo.omd')


#Delete Everything in Directory
for i in os.listdir(thisWorkDir):
	files = {'randomLoc', 'randomNames', 'original'}
	if i in (files):
		shutil.rmtree(i)

#Functions
def distRandomizeLocations(inFeeder):
	inFeeder['nodes'] = []
	inFeeder['links'] = []
	inFeeder['hiddenNodes'] = []
	inFeeder['hiddenLinks'] = []
	for key in inFeeder['tree']:
		if ('longitude' in inFeeder['tree'][key]) or ('latitude' in inFeeder['tree'][key]):
			inFeeder['tree'][key]['longitude'] = random.randint(0,1000)
			inFeeder['tree'][key]['latitude'] = random.randint(0,1000)

def distRandomizeNames(inFeeder):
	''' Replace all names in the inFeeder distribution system with a random ID number. '''
	newNameKey = {}
	allKeys = range(len(inFeeder['tree'].keys()))
	random.shuffle(allKeys)
	#randomID = random.randint(0,100)
	'''
	# Alternate approach, maybe use later.
	allKeys = range(len(inFeeder['tree'].keys()))
	random.shuffle(allKeys) # results in [83, 7204, 13, 57, ...]
	allKeys[i]; i+=1# instead of id += 1
	'''
	# Create nameKey dictionary
	for count, key in enumerate(inFeeder['tree']):
		if 'name' in inFeeder['tree'][key]:
			oldName = inFeeder['tree'][key]['name']
			newName = str(allKeys[count])
			newNameKey.update({oldName:newName})
			inFeeder['tree'][key]['name'] = newName
	# Replace names in tree
	for key in inFeeder['tree']:
		if 'parent' in inFeeder['tree'][key]:
			oldParent = inFeeder['tree'][key]['parent']
			inFeeder['tree'][key]['parent'] = newNameKey[oldParent]
		if ('from' in inFeeder['tree'][key]) and ('to' in inFeeder['tree'][key]):
			oldFrom = inFeeder['tree'][key]['from']
			oldTo = inFeeder['tree'][key]['to']
			inFeeder['tree'][key]['from'] = newNameKey[oldFrom]
			inFeeder['tree'][key]['to'] = newNameKey[oldTo]
		# if inFeeder['tree'][key].get('object','') == 'transformer':
		# 	oldConfig = inFeeder['tree'][key]['configuration']
		# 	inFeeder['tree'][key]['configuration'] = newNameKey[oldConfig]
	#Replace triplex line Configs - these dont exsist
		# if inFeeder['tree'][key].get('object','') == 'triplex_line':
		# 	oldConfig = inFeeder['tree'][key]['configuration']
		# 	inFeeder['tree'][key]['configuration'] = newNameKey[oldConfig]

	#Replace triplex line conductors - neither do these
		# if inFeeder['tree'][key].get('object','') == 'triplex_line':
		# 	oldConfig = inFeeder['tree'][key]['configuration']
		# 	inFeeder['tree'][key]['configuration'] = newNameKey[oldConfig]

	#this does, works for line_config objects
		if inFeeder['tree'][key].get('object', '') == 'line_configuration':
			print("activated")
			for prop in inFeeder['tree'][key]:
				slist = {'conductor_N', 'conductor_A', 'conductor_B', 'conductor_C'}
				if prop in slist:
					print("has detected a conductor")
					oldCon = inFeeder['tree'][key][prop]
					inFeeder['tree'][key][prop] = newNameKey[oldCon]
	#Replace Spacing
		if 'spacing' in inFeeder['tree'][key]:
			oldspace = inFeeder['tree'][key]['spacing']
			inFeeder['tree'][key]['spacing'] = newNameKey[oldspace]
	#Replace configs general form
		if 'configuration' in inFeeder['tree'][key]:
			oldConfig = inFeeder['tree'][key]['configuration']
			inFeeder['tree'][key]['configuration'] = newNameKey[oldConfig]
	# Replace names in links
	for i in range(len(inFeeder['links'])):
		for key in inFeeder['links'][i]:
			if (key == 'source') or (key == 'target'):
				oldLink = inFeeder['links'][i][key]['name']
				inFeeder['links'][i][key]['name'] = newNameKey[oldLink]
	# Replace names in 'nodes'
	for i in range(len(inFeeder['nodes'])):
		for key in inFeeder['nodes'][i]:
			if key == 'name':
				oldNode = inFeeder['nodes'][i][key]
				inFeeder['nodes'][i][key] = newNameKey[oldNode]	
	''' Additional types to replace:
	XXX transformer_configuration (transformer)
	OOO triplex_line_configuration (triplex_line) doesnt exsist
	OOO triplex_line_conductor (triplex_line_configuration) doesnt exsist
	OOO overhead_line_conductor (overhead_line_configuration)
	OOO underground_line_conductor (underground_line_configuration)
	OOO overhead_line_configuration (overhead_line)
	OOO underground_line_configuration (underground_line)
	OOO line_spacing (underground_line_configuration AND overhead_line_configuration)
	OOO regulator_configuration (regulator)
	'''

# Get the circuit in to memory.
with open(pJoin(filePath, 'Olin Barre Geo.omd'), "r") as inFile:
	inNetwork = json.load(inFile)
# Randomize names.
	distRandomizeNames(inNetwork)
	FNAMEOUT = "Olin Barre Geo RandomNames.omd"
with open(FNAMEOUT, "w") as outFile:
	json.dump(inNetwork, outFile, indent=4)
# Randomize locations.
with open(pJoin(filePath, 'Olin Barre Geo.omd'), "r") as inFile:
	inNetwork = json.load(inFile)
# Write resulting .omd to disk.
	distRandomizeLocations(inNetwork)
	FNAMEOUT = "Olin Barre Geo randomLoc.omd"
with open(FNAMEOUT, "w") as outFile:
	json.dump(inNetwork, outFile, indent=4)
# Create 2 voltage drop models, copy correct .omd in to those directories.

#I created 3, one for randNames, one for randLoc, one for the original

randomNames = thisWorkDir  + 'randomNames'
randomLoc = thisWorkDir + 'randomLoc'
original_Loc = thisWorkDir + 'original'

#Create three voltageDrop models
voltageDrop.new(randomNames)
voltageDrop.new(randomLoc)
voltageDrop.new(original_Loc)

#Remove extra original .omd files in anonymized subdirectories
os.remove(pJoin(thisWorkDir, "randomLoc", "Olin Barre Geo.omd"))
os.remove(pJoin(thisWorkDir, "randomNames", "Olin Barre Geo.omd"))

#Put randomized voltage drops in correct folders, only 1 omd per folder. Maybe fix this later. 
shutil.move("Olin Barre Geo randomLoc.omd", pJoin(randomLoc, "Olin Barre Geo randomLoc.omd"))
shutil.move("Olin Barre Geo RandomNames.omd", pJoin(randomNames, "Olin Barre Geo RandomNames.omd"))

# Run voltage drop on original olin barre.
voltageDrop.work(original_Loc, json.load(open(original_Loc + "/allInputData.json")))

#Run voltage drop on anonymized names
voltageDrop.work(randomNames, json.load(open(randomNames + "/allInputData.json")))

# #Run voltage drop on anonymized locations
voltageDrop.work(randomLoc, json.load(open(randomLoc + "/allInputData.json")))

# voltageDrop.work(thisWorkDir, )
# voltageDrop.work(thisWorkDir)
# omf.models.voltageDrop.work("original olin barre", inputDict) #
# # Run voltage drop on anonymized olin barre.
# omf.models.voltageDrop.work("anonymized version olin barre", inputDict)
# omf.models.voltageDrop.new(thisWorkDir, inputData)
# Delete confidential data in here: .omd and .glm files in original voltage drop folder, .omd in anonyized voltage drop folder.
for i in os.listdir(pJoin(thisWorkDir, "original")):
	if i.endswith((".omd", ".glm")):
		os.remove(pJoin(thisWorkDir, "original", i))
#Last Line		
#os.remove(pJoin(thisWorkDir, "Olin Barre Geo.omd"))
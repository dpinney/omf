import json, math, random

def refactorNames(inputFeeder):
	newNameKey = {}
	newNameArray = []
	newKeyID = 0
	for key in inputFeeder['tree']:
		if 'name' in inputFeeder['tree'][key]:
			newName = inputFeeder['tree'][key]['object'] + str(newKeyID)
			newKeyID += 1
			inputFeeder['tree'][key]['name'] = newName
			oldName = inputFeeder['tree'][key]['name']
			newNameKey.update({ oldName : newName })
			newNameArray.append(newName)
	return newNameKey, newNameArray

def pseudomizeNames(inputFeeder):
	newNameKey = {}
	newKeyID = 0
	for key in inputFeeder['tree']:
		if 'name' in inputFeeder['tree'][key]:
			oldName = inputFeeder['tree'][key]['name']
			newName = inputFeeder['tree'][key]['object'] + str(newKeyID)
			newKeyID += 1
			newNameKey.update({ oldName : newName })
			inputFeeder['tree'][key]['name'] = newName
	return newNameKey

def randomizeNames(inputFeeder):
	newNameArray = []
	newKeyID = 0
	for key in inputFeeder['tree']:
		if 'name' in inputFeeder['tree'][key]:
			newName = inputFeeder['tree'][key]['object'] + str(newKeyID)
			newKeyID += 1
			newNameArray.append(newName)
			inputFeeder['tree'][key]['name'] = newName
	return newNameArray

def randomizeLocation(inputFeeder):
	inputFeeder['nodes'] = []
	inputFeeder['links'] = []
	inputFeeder['hiddenNodes'] = []
	inputFeeder['hiddenLinks'] = []
	for key in inputFeeder['tree']:
		if ('longitude' in inputFeeder['tree'][key]) or ('latitude' in inputFeeder['tree'][key]):
			inputFeeder['tree'][key]['longitude'] = random.randint(0,1000)
			inputFeeder['tree'][key]['latitude'] = random.randint(0,1000)
	return inputFeeder['tree']

def translateLocation(inputFeeder, translation, rotation):
	inputFeeder['nodes'] = []
	inputFeeder['links'] = []
	inputFeeder['hiddenNodes'] = []
	inputFeeder['hiddenLinks'] = []
	for key in inputFeeder['tree']:
		if ('longitude' in inputFeeder['tree'][key]) or ('latitude' in inputFeeder['tree'][key]):
			inputFeeder['tree'][key]['longitude'] += translation*math.cos(rotation)
			inputFeeder['tree'][key]['latitude'] += translation*math.sin(rotation)
	return inputFeeder['tree']

def addNoise(inputFeeder, percent):
	for key in inputFeeder['tree']:
		for prop in inputFeeder['tree'][key]:
			value = inputFeeder['tree'][key][prop]
			try: 
				if float(value):
					randNoise = random.randint(value - percent * value, value + percent * value)
					print randNoise
					inputFeeder['tree'][key][prop] += randNoise
			except ValueError:
				pass
	return


def combineLoads():
	pass

def modifyConductorLengths():
	pass

def smoothLoads():
	pass

def shuffleLoads(percent):
	# for key in feeder.tree:
	# 	if randint(0,100) <= percent:
	# 		feeder.tree[key]
	pass



def _tests():
	FNAME = "simpleMarketMod.omd"
	with open(FNAME, "r") as inFile:
		inputFeeder = json.load(inFile)

	# Testing pseudomizeNames
	nameKeyDict = pseudomizeNames(inputFeeder)
	# print nameKeyDict
	FNAMEOUT = "simplePseudo.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)

	# Testing randomizeNames
	randNameArray = randomizeNames(inputFeeder)
	# print randNameArray
	FNAMEOUT = "simpleName.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)

	# Testing randomizeLocation
	newLocation = randomizeLocation(inputFeeder)
	# print newLocation
	FNAMEOUT = "simpleLocation.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)

	# Testing translateLocation
	translation = 20
	rotation = 20
	transLocation = translateLocation(inputFeeder, translation, rotation)
	# print transLocation
	FNAMEOUT = "simpleTranslation.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)

	# Testing addNoise
	percent = 0.2
	noises = addNoise(inputFeeder, percent)
	print noises
	FNAMEOUT = "simpleNoise.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)


if __name__ == '__main__':
	_tests()
import json, math, random

# DISTRIBUTION FEEDER FUNCTIONS
def refactorNames(inputFeeder):
	newNameKey = {}
	newNameArray = []
	newKeyID = 0
	for key in inputFeeder['tree']:
		if 'name' in inputFeeder['tree'][key]:
			oldName = inputFeeder['tree'][key]['name']
			newName = inputFeeder['tree'][key]['object'] + str(newKeyID)
			newKeyID += 1
			inputFeeder['tree'][key]['name'] = newName
			newNameKey.update({oldName:newName})
			newNameArray.append(newName)
	return newNameKey, newNameArray

def distPseudomizeNames(inputFeeder):
	newNameKey = {}
	newKeyID = 0
	for key in inputFeeder['tree']:
		if 'name' in inputFeeder['tree'][key]:
			oldName = inputFeeder['tree'][key]['name']
			newName = inputFeeder['tree'][key]['object'] + str(newKeyID)
			newKeyID += 1
			inputFeeder['tree'][key]['name'] = newName
			newNameKey.update({oldName:newName})
	return newNameKey

def distRandomizeNames(inputFeeder):
	newNameArray = []
	newKeyID = 0
	for key in inputFeeder['tree']:
		if 'name' in inputFeeder['tree'][key]:
			newName = inputFeeder['tree'][key]['object'] + str(newKeyID)
			newKeyID += 1
			inputFeeder['tree'][key]['name'] = newName
			newNameArray.append(newName)
	return newNameArray

def distRandomizeLocation(inputFeeder):
	inputFeeder['nodes'] = []
	inputFeeder['links'] = []
	inputFeeder['hiddenNodes'] = []
	inputFeeder['hiddenLinks'] = []
	for key in inputFeeder['tree']:
		if ('longitude' in inputFeeder['tree'][key]) or ('latitude' in inputFeeder['tree'][key]):
			inputFeeder['tree'][key]['longitude'] = random.randint(0,1000)
			inputFeeder['tree'][key]['latitude'] = random.randint(0,1000)
	return inputFeeder['tree']

def distTranslateLocation(inputFeeder, translation, rotation):
	inputFeeder['nodes'] = []
	inputFeeder['links'] = []
	inputFeeder['hiddenNodes'] = []
	inputFeeder['hiddenLinks'] = []
	for key in inputFeeder['tree']:
		if ('longitude' in inputFeeder['tree'][key]) or ('latitude' in inputFeeder['tree'][key]):
			inputFeeder['tree'][key]['longitude'] += translation*math.cos(rotation)
			inputFeeder['tree'][key]['latitude'] += translation*math.sin(rotation)
	return inputFeeder['tree']

def distAddNoise(inputFeeder, noisePerc):
	for key in inputFeeder['tree']:
		for prop in inputFeeder['tree'][key]:
			value = inputFeeder['tree'][key][prop]
			try: 
				complex(value)
				value = float(value)
				randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
				inputFeeder['tree'][key][prop] += str(randNoise)
			except ValueError:
				continue
	return inputFeeder['tree']

def distCombineLoads():
	pass

def distModifyConductorLengths():
	pass

def distSmoothLoads():
	pass

def distShuffleLoads(shufPerc):
	pass


# TRANSMISSION NETWORK FUNCTIONS
def refactorNames(inputNetwork):
	newBusKey = {}
	newBusArray = []
	newKeyID = 0
	for key in inputNetwork['bus'][0]:
		if 'bus_i' in inputNetwork['bus'][0][key]:
			oldBus = inputNetwork['bus'][0][key]['bus_i']
			newBus = 'bus' + str(newKeyID)
			newKeyID += 1
			inputNetwork['bus'][0][key]['bus_i'] = newBus
			newBusKey.update({oldBus:newBus})
			newBusArray.append(newBus)
	return newBusKey, newBusArray

def tranPseudomizeNames(inputNetwork):
	newBusKey = {}
	newKeyID = 0
	for key in inputNetwork['bus'][0]:
		if 'bus_i' in inputNetwork['bus'][0][key]:
			oldBus = inputNetwork['bus'][0][key]['bus_i']
			newBus = 'bus' + str(newKeyID)
			newKeyID += 1
			inputNetwork['bus'][0][key]['bus_i'] = newBus
			newBusKey.update({oldBus:newBus})
	return newBusKey

def tranRandomizeNames(inputNetwork):
	newBusArray = []
	newKeyID = 0
	for key in inputNetwork['bus'][0]:
		if 'bus_i' in inputNetwork['bus'][0][key]:
			newBus = 'bus' + str(newKeyID)
			newKeyID += 1
			inputNetwork['bus'][0][key]['bus_i'] = newBus
			newBusArray.append(newBus)
	return newBusArray

def tranRandomizeLocation(inputNetwork):
	# inputNetwork['bus'] = []
	# inputNetwork['gen'] = []
	# inputNetwork['branch'] = []
	for key in inputNetwork['bus'][0]:
		if ('longitude' in inputNetwork['bus'][0][key]) or ('latitude' in inputNetwork['bus'][0][key]):
			inputNetwork['bus'][0][key]['longitude'] = random.randint(-200,200)
			inputNetwork['bus'][0][key]['latitude'] = random.randint(-200,200)
	return inputNetwork['bus'][0]

def tranTranslateLocation(inputNetwork, translation, rotation):
	# inputNetwork['bus'] = []
	# inputNetwork['gen'] = []
	# inputNetwork['branch'] = []
	for key in inputNetwork['bus'][0]:
		if ('longitude' in inputNetwork['bus'][0][key]) or ('latitude' in inputNetwork['bus'][0][key]):
			inputNetwork['bus'][0][key]['longitude'] = translation*math.cos(rotation)
			inputNetwork['bus'][0][key]['latitude'] = translation*math.sin(rotation)
	return inputNetwork['bus'][0]

def tranAddNoise(inputNetwork, noisePerc):
	for each in inputNetwork:
		if (each == 'bus') or (each == 'gen') or (each == 'branch'):
			for key in inputNetwork[each][0]:
				for prop in inputNetwork[each][0][key]:
					if ('_bus_' not in prop) and ('status' not in prop):
						value = inputNetwork[each][0][key][prop]
						try: 
							complex(value)
							value = float(value)
							randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
							inputNetwork[each][0][key][prop] += str(randNoise)
						except ValueError:
							continue
	# for key in inputNetwork['bus'][0]:
	# 	for prop in inputNetwork['bus'][0][key]:
	# 		if ('_bus_' not in prop) and ('status' not in prop):
	# 			value = inputNetwork['bus'][0][key][prop]
	# 			try: 
	# 				complex(value)
	# 				value = float(value)
	# 				randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
	# 				inputNetwork['bus'][0][key][prop] += str(randNoise)
	# 			except ValueError:
	# 				continue
	# for key in inputNetwork['gen'][0]:
	# 	for prop in inputNetwork['gen'][0][key]:
	# 		if ('_bus_' not in prop) and ('status' not in prop):
	# 			value = inputNetwork['gen'][0][key][prop]
	# 			try: 
	# 				complex(value)
	# 				value = float(value)
	# 				randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
	# 				inputNetwork['gen'][0][key][prop] += str(randNoise)
	# 			except ValueError:
	# 				continue
	# for key in inputNetwork['branch'][0]:
	# 	for prop in inputNetwork['branch'][0][key]:
	# 		if ('_bus_' not in prop) and ('status' not in prop):
	# 			value = inputNetwork['branch'][0][key][prop]
	# 			try: 
	# 				complex(value)
	# 				value = float(value)
	# 				randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
	# 				inputNetwork['branch'][0][key][prop] += str(randNoise)
	# 			except ValueError:
	# 				continue
	return inputNetwork

def tranCombineLoads():
	pass

def tranModifyConductorLengths():
	pass

def tranSmoothLoads():
	pass

def tranShuffleLoads(shufPerc):
	pass


def _tests():
	# DISTRIBUTION FEEDER TESTS
	FNAME = "simpleMarketMod.omd"
	with open(FNAME, "r") as inFile:
		inputFeeder = json.load(inFile)

	# Testing distPseudomizeNames
	nameKeyDict = distPseudomizeNames(inputFeeder)
	# print nameKeyDict
	FNAMEOUT = "simplePseudo.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)

	# Testing distRandomizeNames
	randNameArray = distRandomizeNames(inputFeeder)
	# print randNameArray
	FNAMEOUT = "simpleName.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)

	# Testing distRandomizeLocation
	newLocation = distRandomizeLocation(inputFeeder)
	# print newLocation
	FNAMEOUT = "simpleLocation.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)

	# Testing distTranslateLocation
	translation = 20
	rotation = 20
	transLocation = distTranslateLocation(inputFeeder, translation, rotation)
	# print transLocation
	FNAMEOUT = "simpleTranslation.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)

	# Testing distAddNoise
	noisePerc = 0.2
	noises = distAddNoise(inputFeeder, noisePerc)
	# print noises
	FNAMEOUT = "simpleNoise.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputFeeder, outFile, indent=4)


	# TRANSMISSION NETWORK TESTS
	FNAME = "case9.omt"
	with open(FNAME, "r") as inFile:
		inputNetwork = json.load(inFile)

	# Testing tranPseudomizeNames
	busKeyDict = tranPseudomizeNames(inputNetwork)
	# print busKeyDict
	FNAMEOUT = "casePseudo.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputNetwork, outFile, indent=4)

	# Testing tranRandomizeNames
	randBusArray = tranRandomizeNames(inputNetwork)
	# print randBusArray
	FNAMEOUT = "caseName.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputNetwork, outFile, indent=4)

	# Testing tranRandomizeLocation
	newLocation = tranRandomizeLocation(inputNetwork)
	# print newLocation
	FNAMEOUT = "caseLocation.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputNetwork, outFile, indent=4)

	# Testing tranTranslateLocation
	translation = 20
	rotation = 20
	transLocation = tranTranslateLocation(inputNetwork, translation, rotation)
	# print transLocation
	FNAMEOUT = "caseTranslation.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputNetwork, outFile, indent=4)

	# Testing tranAddNoise
	noisePerc = 0.2
	noises = tranAddNoise(inputNetwork, noisePerc)
	# print noises
	FNAMEOUT = "caseNoise.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inputNetwork, outFile, indent=4)


if __name__ == '__main__':
	_tests()
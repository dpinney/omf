import json, math, random, datetime

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

def distTranslateLocation(inFeeder, translation, rotation):
	inFeeder['nodes'] = []
	inFeeder['links'] = []
	inFeeder['hiddenNodes'] = []
	inFeeder['hiddenLinks'] = []
	for key in inFeeder['tree']:
		if ('longitude' in inFeeder['tree'][key]) or ('latitude' in inFeeder['tree'][key]):
			inFeeder['tree'][key]['longitude'] += translation*math.cos(rotation)
			inFeeder['tree'][key]['latitude'] += translation*math.sin(rotation)
	return inFeeder['tree']

def distAddNoise(inFeeder, noisePerc):
	for key in inFeeder['tree']:
		for prop in inFeeder['tree'][key]:
			value = inFeeder['tree'][key][prop]
			try: 
				complex(value)
				value = float(value)
				randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
				inFeeder['tree'][key][prop] += str(randNoise)
			except ValueError:
				continue
	return inFeeder['tree']

def distShuffleLoads(inFeeder, shufPerc):
	tlParents = []
	tnParents = []
	houseParents = []
	zipParents = []
	for key in inFeeder['tree']:
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key]['object'] == 'triplex_line'):
			tlParents.append(inFeeder['tree'][key]['parent'])
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key]['object'] == 'triplex_node'):
			tnParents.append(inFeeder['tree'][key]['parent'])
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key]['object'] == 'house'):
			houseParents.append(inFeeder['tree'][key]['parent'])
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key]['object'] == 'ZIPload'):
			zipParents.append(inFeeder['tree'][key]['parent'])
	tlIdx = 0
	tnIdx = 0
	houseIdx = 0
	zipIdx = 0
	for key in inFeeder['tree']:
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key]['object'] == 'triplex_line'):
			if random.randint(0,100)/100.0 < shufPerc:
				random.shuffle(tkParents)
				inputFeeder['tree'][key]['parent'] = tlParents[tlIdx]
				tlIdx += 1
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key]['object'] == 'triplex_node'):
			if random.randint(0,100)/100.0 < shufPerc:
				random.shuffle(tnParents)
				inFeeder['tree'][key]['parent'] = tnParents[tnIdx]
				tnIdx += 1
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key]['object'] == 'house'):
			if random.randint(0,100)/100.0 < shufPerc:
				random.shuffle(houseParents)
				inFeeder['tree'][key]['parent'] = houseParents[houseIdx]
				houseIdx += 1
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key]['object'] == 'ZIPload'):
			if random.randint(0,100)/100.0 < shufPerc:
				random.shuffle(zipParents)
				inFeeder['tree'][key]['parent'] = zipParents[zipIdx]
				zipIdx += 1
	return inFeeder['tree']

def distModifyTriplexLengths(inFeeder):
	tLookup = {}
	for key in inFeeder['tree']:
		tDict = {}
		if inFeeder['tree'][key].get('object') == 'triplex_line':
			tDict = {
				inFeeder['tree'][key].get('name'): {
					'length': inFeeder['tree'][key].get('length'),
					'configuration': inFeeder['tree'][key].get('configuration')
				}
			}
			tLookup.update(tDict)
		if inFeeder['tree'][key].get('object') == 'triplex_line_configuration':
			for tLine in tLookup:
				if tLookup[tLine].get('configuration') == inFeeder['tree'][key].get('name'):
					tLookup[tLine].update(diameter=inFeeder['tree'][key].get('diameter'))
					tLookup[tLine].update(conductor_N=inFeeder['tree'][key].get('conductor_N'))
		if inFeeder['tree'][key].get('object') == 'triplex_line_conductor':
			for tLine in tLookup:
				if tLookup[tLine].get('conductor_N') == inFeeder['tree'][key].get('name'):
					tLookup[tLine].update(resistance=inFeeder['tree'][key].get('resistance'))
	for tLine in tLookup:
		try:
			resistivity = ( float(tLookup[tLine].get('resistance')) * math.pi * (float(tLookup[tLine].get('diameter'))/2.0)**2 ) / float(tLookup[tLine].get('length'))
			tLookup[tLine]['length'] = random.uniform( float(tLookup[tLine].get('length'))-float(tLookup[tLine].get('length')), float(tLookup[tLine].get('length'))+float(tLookup[tLine].get('length')) )
			tLookup[tLine]['diameter'] = random.uniform( (float(tLookup[tLine].get('diameter'))-float(tLookup[tLine].get('diameter')))*1000, (float(tLookup[tLine].get('diameter'))+float(tLookup[tLine].get('diameter')))*1000 ) / 1000.0
			tLookup[tLine]['resistance'] = (resistivity*float(tLookup[tLine].get('length'))) / (math.pi*(float(tLookup[tLine].get('diameter'))/2.0)**2)
		except:
			pass
		for key in inFeeder['tree']:
			if inFeeder['tree'][key].get('name') == tLine:
				inFeeder['tree'][key]['length'] == tLookup[tLine].get('length')
			if inFeeder['tree'][key].get('name') == tLookup[tLine].get('configuration'):
				inFeeder['tree'][key]['diameter'] == tLookup[tLine].get('diameter')
			if inFeeder['tree'][key].get('name') == tLookup[tLine].get('conductor_N'):
				inFeeder['tree'][key]['resistance'] == tLookup[tLine].get('resistance')
	return inFeeder['tree']

def distModifyConductorLengths(inFeeder):
	uLookup = {}
	oLookup = {}
	for key in inFeeder['tree']:
		uDict = {}
		oDict = {}
		if inFeeder['tree'][key].get('object') == 'underground_line':
			uDict = {
				inFeeder['tree'][key].get('name'): {
					'length': inFeeder['tree'][key].get('length'),
					'configuration': inFeeder['tree'][key].get('configuration')
				}	
			}
			uLookup.update(uDict)
		elif inFeeder['tree'][key].get('object') == 'overhead_line':
			oDict = {
				inFeeder['tree'][key].get('name'): {
					'length': inFeeder['tree'][key].get('length'), 
					'configuration': inFeeder['tree'][key].get('configuration')
				}	
			}
			oLookup.update(oDict)
		if inFeeder['tree'][key].get('object') == 'line_configuration':
			for uLine in uLookup:
				if uLookup[uLine].get('configuration') == inFeeder['tree'][key].get('name'):
					uLookup[uLine].update(conductor_N=inFeeder['tree'][key].get('conductor_N'))
			for oLine in oLookup:
				if oLookup[oLine].get('configuration') == inFeeder['tree'][key].get('name'):
					oLookup[oLine].update(conductor_N=inFeeder['tree'][key].get('conductor_N'))
		if inFeeder['tree'][key].get('object') == 'underground_line_conductor':
			for uLine in uLookup:
				if uLookup[uLine].get('conductor_N') == inFeeder['tree'][key].get('name'):
					uLookup[uLine].update(conductor_resistance=inFeeder['tree'][key].get('conductor_resistance'))
					uLookup[uLine].update(conductor_diameter=inFeeder['tree'][key].get('conductor_diameter'))
		elif inFeeder['tree'][key].get('object') == 'overhead_line_conductor':
			for oLine in oLookup:
				if oLookup[oLine].get('conductor_N') == inFeeder['tree'][key].get('name'):
					oLookup[oLine].update(resistance=inFeeder['tree'][key].get('resistance'))
					oLookup[oLine].update(geometric_mean_radius=inFeeder['tree'][key].get('geometric_mean_radius'))
	for uLine in uLookup:
		try:
			resistivity = ( float(uLookup[uLine].get('conductor_resistance')) * math.pi * (float(uLookup[uLine].get('conductor_diameter'))/2.0)**2 ) / float(uLookup[uLine].get('length'))
			uLookup[uLine]['length'] = random.uniform( float(uLookup[uLine].get('length'))-float(uLookup[uLine].get('length')), float(uLookup[uLine].get('length'))+float(uLookup[uLine].get('length')) )
			uLookup[uLine]['conductor_diameter'] = random.randint( (float(uLookup[uLine].get('conductor_diameter'))-float(uLookup[uLine].get('conductor_diameter')))*1000, (float(uLookup[uLine].get('conductor_diameter'))+float(uLookup[uLine].get('conductor_diameter')))*1000 ) / 1000.0
			uLookup[uLine]['conductor_resistance'] = (resistivity*float(uLookup[uLine].get('length'))) / (math.pi*(float(uLookup[uLine].get('conductor_diameter'))/2.0)**2)
		except:
			pass
		for key in inFeeder['tree']:
			if inFeeder['tree'][key].get('name') == uLine:
				inFeeder['tree'][key]['length'] == uLookup[uLine].get('length')
			if inFeeder['tree'][key].get('name') == uLookup[uLine].get('conductor_N'):
				try:
					inFeeder['tree'][key]['conductor_resistance'] == uLookup[uLine].get('conductor_resistance')
					inFeeder['tree'][key]['conductor_diameter'] == uLookup[uLine].get('conductor_diameter')
				except:
					pass
	for oLine in oLookup:
		try:
			resistivity = ( float(oLookup[oLine].get('resistance')) * math.pi * float(oLookup[oLine].get('geometric_mean_radius'))**2 ) / float(oLookup[oLine].get('length'))
			oLookup[oLine]['length'] = random.uniform( float(oLookup[oLine].get('length'))-float(oLookup[oLine].get('length')), float(oLookup[oLine].get('length'))+float(oLookup[oLine].get('length')) )
			oLookup[oLine]['geometric_mean_radius'] = random.uniform( (float(oLookup[oLine].get('geometric_mean_radius'))-float(oLookup[oLine].get('geometric_mean_radius')))*1000, (float(oLookup[oLine].get('geometric_mean_radius'))+float(oLookup[oLine].get('geometric_mean_radius')))*1000 ) / 1000.0
			oLookup[oLine]['resistance'] = (resistivity*float(oLookup[oLine].get('length'))) / (math.pi*float(oLookup[oLine].get('geometric_mean_radius'))**2)
		except:
			pass
		for key in inFeeder['tree']:
			if inFeeder['tree'][key].get('name') == oLine:
				inFeeder['tree'][key]['length'] == oLookup[oLine].get('length')
			if inFeeder['tree'][key].get('name') == oLookup[oLine].get('conductor_N'):
				try:
					inFeeder['tree'][key]['resistance'] == oLookup[oLine].get('resistance')
					inFeeder['tree'][key]['geometric_mean_radius'] == oLookup[oLine].get('geometric_mean_radius')
				except:
					pass
	return inFeeder['tree']

def distSmoothLoads(inFeeder):
	outList = []
	scadaFile = inFeeder['attachments']['subScadaCalibrated1.player']
	scadaLines = scadaFile.split('\n')
	scadaPairs = [x.split(',') for x in scadaLines] # [[ts,val],[ts,val],[ts,val],...]
	for pair in scadaPairs:
		s = pair[0]
		s = s[:19]
		try:
			timestamp = datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
		except:
			pass # print 'BAD DATAPOINT:', s
		aggAmount = 0
		aggHour = timestamp.hour
		if (timestamp.minute == 0) and (timestamp.second == 0) and (timestamp.hour == aggHour):
			try:
				aggAmount += float(pair[1])
				outList.append([aggHour, aggAmount])
			except:
				pass
	return outList


# TRANSMISSION NETWORK FUNCTIONS
def refactorNames(inputNetwork):
	newBusKey = {}
	newBusArray = []
	newKeyID = 0
	for dic in inputNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['bus'][idx]:
				for prop in inputNetwork['bus'][idx][key]:
					if 'bus_i' in prop:
						oldBus = inputNetwork['bus'][idx][key]['bus_i']
						newBus = 'bus' + str(newKeyID)
						newKeyID += 1
						inputNetwork['bus'][idx][key]['bus_i'] = newBus
						newBusKey.update({oldBus:newBus})
						newBusArray.append(newBus)
	# for dic in inputNetwork['bus']:
	# 	for key in dic:
	# 		key = int(key) - 1
	# 		for bus in inputNetwork['bus'][key]:
	# 			if 'bus_i' in inputNetwork['bus'][key][bus]:
	# 				oldBus = inputNetwork['bus'][key][bus]['bus_i']
	# 				newBus = 'bus' + str(newKeyID)
	# 				newKeyID += 1
	# 				inputNetwork['bus'][key][bus]['bus_i'] = newBus
	# 				newBusKey.update({oldBus:newBus})
	# 				newBusArray.append(newBus)
	# for key in inputNetwork['bus'][0]:
	# 	if 'bus_i' in inputNetwork['bus'][0][key]:
	# 		oldBus = inputNetwork['bus'][0][key]['bus_i']
	# 		newBus = 'bus' + str(newKeyID)
	# 		newKeyID += 1
	# 		inputNetwork['bus'][0][key]['bus_i'] = newBus
	# 		newBusKey.update({oldBus:newBus})
			# newBusArray.append(newBus)
	return newBusKey, newBusArray

def tranPseudomizeNames(inputNetwork):
	newBusKey = {}
	newKeyID = 0
	for dic in inputNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['bus'][idx]:
				for prop in inputNetwork['bus'][idx][key]:
					if 'bus_i' in prop:
						oldBus = inputNetwork['bus'][idx][key]['bus_i']
						newBus = 'bus' + str(newKeyID)
						newKeyID += 1
						inputNetwork['bus'][idx][key]['bus_i'] = newBus
						newBusKey.update({oldBus:newBus})
	# for dic in inputNetwork['bus']:
	# 	for key in dic:
	# 		key = int(key) - 1
	# 		for bus in inputNetwork['bus'][key]:
	# 			if 'bus_i' in inputNetwork['bus'][key][bus]:
	# 				oldBus = inputNetwork['bus'][key][bus]['bus_i']
	# 				newBus = 'bus' + str(newKeyID)
	# 				newKeyID += 1
	# 				inputNetwork['bus'][key][bus]['bus_i'] = newBus
	# 				newBusKey.update({oldBus:newBus})
	return newBusKey

def tranRandomizeNames(inputNetwork):
	newBusArray = []
	newKeyID = 0
	for dic in inputNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['bus'][idx]:
				for prop in inputNetwork['bus'][idx][key]:
					if 'bus_i' in prop:
						newBus = 'bus' + str(newKeyID)
						newKeyID += 1
						inputNetwork['bus'][idx][key]['bus_i'] = newBus
						newBusArray.append(newBus)
	# for key in inputNetwork['bus'][0]:
	# 	if 'bus_i' in inputNetwork['bus'][0][key]:
	# 		newBus = 'bus' + str(newKeyID)
	# 		newKeyID += 1
	# 		inputNetwork['bus'][0][key]['bus_i'] = newBus
	# 		newBusArray.append(newBus)
	return newBusArray

def tranRandomizeLocation(inputNetwork):
	# inputNetwork['bus'] = []
	# inputNetwork['gen'] = []
	# inputNetwork['branch'] = []
	for dic in inputNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['bus'][idx]:
				for prop in inputNetwork['bus'][idx][key]:
					if 'longitude' in prop:
						inputNetwork['bus'][idx][key]['longitude'] = random.randint(-200,200)
						inputNetwork['bus'][idx][key]['latitude'] = random.randint(-200,200)
	# for dic in inputNetwork['bus']:
	# 	for key in dic:
	# 		key = int(key) - 1
	# 		for bus in inputNetwork['bus'][key]:
	# 			if 'longitude' in inputNetwork['bus'][key][bus]:
	# 				inputNetwork['bus'][key][bus]['longitude'] = random.randint(-200,200)
	# 				inputNetwork['bus'][key][bus]['latitude'] = random.randint(-200,200)
	# for key in inputNetwork['bus'][0]:
	# 	if ('longitude' in inputNetwork['bus'][0][key]) or ('latitude' in inputNetwork['bus'][0][key]):
	# 		inputNetwork['bus'][0][key]['longitude'] = random.randint(-200,200)
	# 		inputNetwork['bus'][0][key]['latitude'] = random.randint(-200,200)
	return inputNetwork['bus']

def tranTranslateLocation(inputNetwork, translation, rotation):
	# inputNetwork['bus'] = []
	# inputNetwork['gen'] = []
	# inputNetwork['branch'] = []
	for dic in inputNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['bus'][idx]:
				for prop in inputNetwork['bus'][idx][key]:
					if 'longitude' in prop:
						inputNetwork['bus'][idx][key]['longitude'] = translation*math.cos(rotation)
						inputNetwork['bus'][idx][key]['latitude'] = translation*math.sin(rotation)
	# for dic in inputNetwork['bus']:
	# 	for key in dic:
	# 		key = int(key) - 1
	# 		for bus in inputNetwork['bus'][key]:
	# 			if 'longitude' in inputNetwork['bus'][key][bus]:
	# 				inputNetwork['bus'][key][bus]['longitude'] = translation*math.cos(rotation)
	# 				inputNetwork['bus'][key][bus]['latitude'] = translation*math.sin(rotation)
	# for key in inputNetwork['bus'][0]:
	# 	if ('longitude' in inputNetwork['bus'][0][key]) or ('latitude' in inputNetwork['bus'][0][key]):
	# 		inputNetwork['bus'][0][key]['longitude'] = translation*math.cos(rotation)
	# 		inputNetwork['bus'][0][key]['latitude'] = translation*math.sin(rotation)
	return inputNetwork['bus']

def tranAddNoise(inputNetwork, noisePerc):
	for array in inputNetwork:
		if (array == 'bus') or (array == 'gen') or (array == 'branch'):
			for dic in inputNetwork[array]:
				for each in dic:
					idx = int(each) - 1
					for key in inputNetwork[array][idx]:
						for prop in inputNetwork[array][idx][key]:
							if ('_bus_' not in prop) and ('status' not in prop):
								value = inputNetwork[array][idx][key][prop]
								try: 
									complex(value)
									value = float(value)
									randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
									inputNetwork[array][idx][key][prop] += str(randNoise)
								except ValueError:
									continue
	# for each in inputNetwork:
	# 	if (each == 'bus') or (each == 'gen') or (each == 'branch'):
	# 		for key in inputNetwork[each][0]:
	# 			for prop in inputNetwork[each][0][key]:
	# 				if ('_bus_' not in prop) and ('status' not in prop):
	# 					value = inputNetwork[each][0][key][prop]
	# 					try: 
	# 						complex(value)
	# 						value = float(value)
	# 						randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
	# 						inputNetwork[each][0][key][prop] += str(randNoise)
	# 					except ValueError:
	# 						continue
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

def tranShuffleLoadsAndGens(inputNetwork, shufPerc):
	qParents = []
	pParents = []
	genParents = []
	for dic in inputNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['bus'][idx]:
				for prop in inputNetwork['bus'][idx][key]:
					if ('Qd' in prop) and ('Pd' in prop):
						qParents.append(inputNetwork['bus'][idx][key]['Qd'])
						pParents.append(inputNetwork['bus'][idx][key]['Pd'])
	for dic in inputNetwork['gen']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['gen'][idx]:
				for prop in inputNetwork['gen'][idx][key]:
					if 'bus' in prop:
						genParents.append(inputNetwork['gen'][idx][key]['bus'])
	qIdx = 0
	pIdx = 0
	genIdx = 0
	for dic in inputNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['bus'][idx]:
				for prop in inputNetwork['bus'][idx][key]:
					if ('Qd' in prop) and ('Pd' in prop):
						if random.randint(0,100)/100.0 < shufPerc:
							random.shuffle(qParents)
							random.shuffle(pParents)
							inputNetwork['bus'][idx][key]['Qd'] = pParents[pIdx]
							inputNetwork['bus'][idx][key]['Pd'] = qParents[qIdx]
							pIdx += 1
							qIdx += 1
	for dic in inputNetwork['gen']:
		for each in dic:
			idx = int(each) - 1
			for key in inputNetwork['gen'][idx]:
				for prop in inputNetwork['gen'][idx][key]:
					if 'bus' in prop:
						if random.randint(0,100)/100.0 < shufPerc:
							random.shuffle(genParents)
							inputNetwork['gen'][idx][key]['bus'] = genParents[genIdx]
							genIdx += 1
	return inputNetwork['bus'], inputNetwork['gen']


def _tests():
	# DISTRIBUTION FEEDER TESTS
	# FNAME = "simpleMarketMod.omd"
	# with open(FNAME, "r") as inFile:
	# 	inputFeeder = json.load(inFile)


	# # Testing distPseudomizeNames
	# nameKeyDict = distPseudomizeNames(inputFeeder)
	# # print nameKeyDict
	# FNAMEOUT = "simplePseudo.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputFeeder, outFile, indent=4)

	# # Testing distRandomizeNames
	# randNameArray = distRandomizeNames(inputFeeder)
	# # print randNameArray
	# FNAMEOUT = "simpleName.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputFeeder, outFile, indent=4)

	# # Testing distRandomizeLocation
	# newLocation = distRandomizeLocation(inputFeeder)
	# # print newLocation
	# FNAMEOUT = "simpleLocation.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputFeeder, outFile, indent=4)

	# Testing distTranslateLocation
	FNAME = "simpleMarketMod.omd"
	with open(FNAME, "r") as inFile:
		inFeeder = json.load(inFile)
	translation = 20
	rotation = 20
	translate = distTranslateLocation(inFeeder, translation, rotation)
	FNAMEOUT = "simpleMarket_distTranslateLocation.omd"
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inFeeder, outFile, indent=4)

	# # Testing distAddNoise
	# FNAME = "simpleMarketMod.omd"
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# noisePerc = 0.2
	# noises = distAddNoise(inFeeder, noisePerc)
	# FNAMEOUT = "simpleMarket_distAddNoise.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

	# # Testing distShuffleLoads
	# FNAME = "simpleMarketMod.omd"
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# shufPerc = 0.5
	# shuffle = distShuffleLoads(inFeeder, shufPerc)
	# FNAMEOUT = "simpleMarket_distShuffleLoads.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

	# # Testing distModifyTriplexLengths
	# FNAME = "simpleMarketMod.omd"
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# triplexLengths = distModifyTriplexLengths(inFeeder)
	# FNAMEOUT = "simpleMarket_distModifyTriplexLengths.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

	# # Testing distModifyConductorLengths
	# FNAME = "Olin Barre GH.omd"
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# conductorLengths = distModifyConductorLengths(inFeeder)
	# FNAMEOUT = "olinBarreGH_distModifyConductorLengths.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

	# # Testing distSmoothLoads
	# FNAME = "Calibrated Feeder.omd"
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# smoothing = distSmoothLoads(inFeeder)
	# FNAMEOUT = "simpleMarket_distSmoothLoads.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)


	# # TRANSMISSION NETWORK TESTS
	# FNAME = "case9.omt"
	# with open(FNAME, "r") as inFile:
	# 	inputNetwork = json.load(inFile)


	# # Testing tranPseudomizeNames
	# busKeyDict = tranPseudomizeNames(inputNetwork)
	# # print busKeyDict
	# FNAMEOUT = "casePseudo.omt"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputNetwork, outFile, indent=4)

	# # Testing tranRandomizeNames
	# randBusArray = tranRandomizeNames(inputNetwork)
	# # print randBusArray
	# FNAMEOUT = "caseName.omt"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputNetwork, outFile, indent=4)

	# # Testing tranRandomizeLocation
	# newLocation = tranRandomizeLocation(inputNetwork)
	# # print newLocation
	# FNAMEOUT = "caseLocation.omt"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputNetwork, outFile, indent=4)

	# # Testing tranTranslateLocation
	# translation = 20
	# rotation = 20
	# transLocation = tranTranslateLocation(inputNetwork, translation, rotation)
	# # print transLocation
	# FNAMEOUT = "caseTranslation.omt"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputNetwork, outFile, indent=4)

	# # Testing tranAddNoise
	# noisePerc = 0.2
	# noises = tranAddNoise(inputNetwork, noisePerc)
	# # print noises
	# FNAMEOUT = "caseNoise.omt"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputNetwork, outFile, indent=4)

	# # Testing tranShuffleLoadsAndGens
	# shufPerc = 0.5
	# shuffle = tranShuffleLoadsAndGens(inputNetwork, shufPerc)
	# # print shuffle
	# FNAMEOUT = "caseShuffle.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inputNetwork, outFile, indent=4)


if __name__ == '__main__':
	_tests()
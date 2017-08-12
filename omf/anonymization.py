''' Functions for anonymizing data in OMF distribution and transmission systems.'''

import json, math, random, datetime

# DISTRIBUTION FEEDER FUNCTIONS
def distPseudomizeNames(inFeeder):
	''' Replace all names in the inFeeder distribution system with pseudonames made up of the object type and a random ID. Return a key with name and ID pairs. '''
	newNameKey = {}
	# newKeyID = 0
	newKeyID = random.randint(0,100)
	# Create nameKey dictionary
	for key in inFeeder['tree']:
		if 'name' in inFeeder['tree'][key]:
			oldName = inFeeder['tree'][key]['name']
			newName = inFeeder['tree'][key]['object'] + str(newKeyID)
			newNameKey.update({oldName:newName})
			inFeeder['tree'][key]['name'] = newName
			newKeyID += 1
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
	return newNameKey

def distRandomizeNames(inFeeder):
	''' Replace all names in the inFeeder distribution system with pseudonames made up of the object type and a random ID.. Return a list of the new IDs. '''
	newNameKey = {}
	newNameArray = []
	# newKeyID = 0
	newKeyID = random.randint(0,100)
	# Create nameKey dictionary
	for key in inFeeder['tree']:
		if 'name' in inFeeder['tree'][key]:
			oldName = inFeeder['tree'][key]['name']
			newName = inFeeder['tree'][key]['object'] + str(newKeyID)
			newNameKey.update({oldName:newName})
			newNameArray.append(newName)
			inFeeder['tree'][key]['name'] = newName
			newKeyID += 1
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
	return newNameArray

def distRandomizeLocations(inFeeder):
	''' Replace all objects' longitude and latitude positions in the inFeeder distribution system with random values. '''
	inFeeder['nodes'] = []
	inFeeder['links'] = []
	inFeeder['hiddenNodes'] = []
	inFeeder['hiddenLinks'] = []
	for key in inFeeder['tree']:
		if ('longitude' in inFeeder['tree'][key]) or ('latitude' in inFeeder['tree'][key]):
			inFeeder['tree'][key]['longitude'] = random.randint(0,1000)
			inFeeder['tree'][key]['latitude'] = random.randint(0,1000)
	return

def distTranslateLocations(inFeeder, translation, rotation):
	''' Move the position of all objects in the inFeeder distribution system by a horizontal translation and counter-clockwise rotation. '''
	inFeeder['nodes'] = []
	inFeeder['links'] = []
	inFeeder['hiddenNodes'] = []
	inFeeder['hiddenLinks'] = []
	for key in inFeeder['tree']:
		if ('longitude' in inFeeder['tree'][key]) or ('latitude' in inFeeder['tree'][key]):
			inFeeder['tree'][key]['longitude'] += translation*math.cos(rotation)
			inFeeder['tree'][key]['latitude'] += translation*math.sin(rotation)
	return

def distAddNoise(inFeeder, noisePerc):
	''' Add random noise to properties with numeric values for all objects in the inFeeder distribution system based on a noisePerc probability. '''
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
	return

def distShuffleLoads(inFeeder, shufPerc):
	''' Shuffle the parent properties between all load objects in the inFeeder distribution system. '''
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
				random.shuffle(tlParents)
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
	return

def distModifyTriplexLengths(inFeeder):
	''' Modifies triplex line length and diameter properties while preserving original impedance in the inFeeder distribution system. '''
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
	return

def distModifyConductorLengths(inFeeder):
	''' Modifies conductor length and diameter properties while preserving original impedance in the inFeeder distribution system. '''
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
	return

def distSmoothLoads(inFeeder):
	''' Reduce the resolution of load shapes by taking all sub-hourly load dispatch data in the inFeeder distribution system and aggregating to the hour level. ''' 
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
def tranPseudomizeNames(inNetwork):
	''' Replace all names in the inNetwork transmission system with pseudonames made up of the object type and a random ID.. Return a key with name and ID pairs. '''
	newBusKey = {}
	# newKeyID = 0
	newKeyID = random.randint(0,100)
	for dic in inNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inNetwork['bus'][idx]:
				for prop in inNetwork['bus'][idx][key]:
					if 'bus_i' in prop:
						oldBus = inNetwork['bus'][idx][key]['bus_i']
						newBus = 'bus' + str(newKeyID)
						newKeyID += 1
						inNetwork['bus'][idx][key]['bus_i'] = newBus
						newBusKey.update({oldBus:newBus})
	return newBusKey

def tranRandomizeNames(inNetwork):
	''' Replace all names in the inNetwork transmission system with pseudonames made up of the object type and a random ID. Return a list of the new IDs. '''
	newBusArray = []
	# newKeyID = 0
	newKeyID = random.randint(0,100)
	for dic in inNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inNetwork['bus'][idx]:
				for prop in inNetwork['bus'][idx][key]:
					if 'bus_i' in prop:
						newBus = 'bus' + str(newKeyID)
						newKeyID += 1
						inNetwork['bus'][idx][key]['bus_i'] = newBus
						newBusArray.append(newBus)
	return newBusArray

def tranRandomizeLocations(inNetwork):
	''' Replace all objects' longitude and latitude positions in the inNetwork transmission system with random values. '''
	# inNetwork['bus'] = []
	# inNetwork['gen'] = []
	# inNetwork['branch'] = []
	for dic in inNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inNetwork['bus'][idx]:
				for prop in inNetwork['bus'][idx][key]:
					if 'longitude' in prop:
						inNetwork['bus'][idx][key]['longitude'] = random.randint(-200,200)
						inNetwork['bus'][idx][key]['latitude'] = random.randint(-200,200)
	return

def tranTranslateLocations(inNetwork, translation, rotation):
	''' Move the position of all objects in the inNetwork transmission system by a horizontal translation and counter-clockwise rotation. '''
	# inNetwork['bus'] = []
	# inNetwork['gen'] = []
	# inNetwork['branch'] = []
	for dic in inNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inNetwork['bus'][idx]:
				for prop in inNetwork['bus'][idx][key]:
					if 'longitude' in prop:
						inNetwork['bus'][idx][key]['longitude'] = translation*math.cos(rotation)
						inNetwork['bus'][idx][key]['latitude'] = translation*math.sin(rotation)
	return

def tranAddNoise(inNetwork, noisePerc):
	''' Add random noise to properties with numeric values for all objects in the inNetwork transmission system based on a noisePerc probability. '''
	for array in inNetwork:
		if (array == 'bus') or (array == 'gen') or (array == 'branch'):
			for dic in inNetwork[array]:
				for each in dic:
					idx = int(each) - 1
					for key in inNetwork[array][idx]:
						for prop in inNetwork[array][idx][key]:
							if ('_bus_' not in prop) and ('status' not in prop):
								value = inNetwork[array][idx][key][prop]
								try: 
									complex(value)
									value = float(value)
									randNoise = random.randint(value - noisePerc*value, value + noisePerc*value)
									inNetwork[array][idx][key][prop] += str(randNoise)
								except ValueError:
									continue
	return

def tranShuffleLoadsAndGens(inNetwork, shufPerc):
	''' Shuffle the parent properties between all load and gen objects in the inNetwork transmission system. '''
	qParents = []
	pParents = []
	genParents = []
	for dic in inNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inNetwork['bus'][idx]:
				for prop in inNetwork['bus'][idx][key]:
					if ('Qd' in prop) and ('Pd' in prop):
						qParents.append(inNetwork['bus'][idx][key]['Qd'])
						pParents.append(inNetwork['bus'][idx][key]['Pd'])
	for dic in inNetwork['gen']:
		for each in dic:
			idx = int(each) - 1
			for key in inNetwork['gen'][idx]:
				for prop in inNetwork['gen'][idx][key]:
					if 'bus' in prop:
						genParents.append(inNetwork['gen'][idx][key]['bus'])
	qIdx = 0
	pIdx = 0
	genIdx = 0
	for dic in inNetwork['bus']:
		for each in dic:
			idx = int(each) - 1
			for key in inNetwork['bus'][idx]:
				for prop in inNetwork['bus'][idx][key]:
					if ('Qd' in prop) and ('Pd' in prop):
						if random.randint(0,100)/100.0 < shufPerc:
							random.shuffle(qParents)
							random.shuffle(pParents)
							inNetwork['bus'][idx][key]['Qd'] = pParents[pIdx]
							inNetwork['bus'][idx][key]['Pd'] = qParents[qIdx]
							pIdx += 1
							qIdx += 1
	for dic in inNetwork['gen']:
		for each in dic:
			idx = int(each) - 1
			for key in inNetwork['gen'][idx]:
				for prop in inNetwork['gen'][idx][key]:
					if 'bus' in prop:
						if random.randint(0,100)/100.0 < shufPerc:
							random.shuffle(genParents)
							inNetwork['gen'][idx][key]['bus'] = genParents[genIdx]
							genIdx += 1
	return

# def _tests():
# 	# DISTRIBUTION FEEDER TESTS
# 	# Test distPseudomizeNames
# 	FNAME = "Simple Market System Modified.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		nameKey = distPseudomizeNames(inFeeder)
# 		print nameKey
# 	FNAMEOUT = "simpleMarket_distPseudomizeNames.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distRandomizeNames
# 	FNAME = "Simple Market System Modified.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		nameArray = distRandomizeNames(inFeeder)
# 		print nameArray
# 	FNAMEOUT = "simpleMarket_distRandomizeNames.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distRandomizeLocations
# 	FNAME = "Simple Market System Modified.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		distRandomizeLocations(inFeeder)
# 	FNAMEOUT = "simpleMarket_distRandomizeLocations.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distTranslateLocations
# 	FNAME = "Simple Market System Modified.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		translation = 20
# 		rotation = 20
# 		distTranslateLocations(inFeeder, translation, rotation)
# 	FNAMEOUT = "simpleMarket_distTranslateLocations.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distAddNoise
# 	FNAME = "Simple Market System Modified.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		noisePerc = 0.2
# 		distAddNoise(inFeeder, noisePerc)
# 	FNAMEOUT = "simpleMarket_distAddNoise.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distShuffleLoads
# 	FNAME = "Simple Market System Modified.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		shufPerc = 0.5
# 		distShuffleLoads(inFeeder, shufPerc)
# 	FNAMEOUT = "simpleMarket_distShuffleLoads.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distModifyTriplexLengths
# 	FNAME = "Simple Market System Modified.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		distModifyTriplexLengths(inFeeder)
# 	FNAMEOUT = "simpleMarket_distModifyTriplexLengths.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distModifyConductorLengths
# 	FNAME = "Olin Barre GH.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		distModifyConductorLengths(inFeeder)
# 	FNAMEOUT = "olinBarreGH_distModifyConductorLengths.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distSmoothLoads
# 	FNAME = "Calibrated Feeder.omd"
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		calibrate = distSmoothLoads(inFeeder)
# 		print calibrate
# 	FNAMEOUT = "calibrated_distSmoothLoads.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)


# 	# TRANSMISSION NETWORK TESTS
# 	# Test tranPseudomizeNames
# 	FNAME = "case9.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		busKey = tranPseudomizeNames(inNetwork)
# 		print busKey
# 	FNAMEOUT = "case_tranPseudomizeNames.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# 	# Test tranRandomizeNames
# 	FNAME = "case9.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		busArray = tranRandomizeNames(inNetwork)
# 		print busArray
# 	FNAMEOUT = "case_tranRandomizeNames.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# 	# Test tranRandomizeLocations
# 	FNAME = "case9.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		tranRandomizeLocations(inNetwork)
# 	FNAMEOUT = "case_tranRandomizeLocations.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# 	# Test tranTranslateLocation
# 	FNAME = "case9.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		translation = 20
# 		rotation = 20
# 		tranTranslateLocations(inNetwork, translation, rotation)
# 	FNAMEOUT = "case_tranTranslateLocations.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# 	# Testing tranAddNoise
# 	FNAME = "case9.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		noisePerc = 0.2
# 		tranAddNoise(inNetwork, noisePerc)
# 	FNAMEOUT = "case_tranAddNoise.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# 	# Testing tranShuffleLoadsAndGens
# 	FNAME = "case9.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		shufPerc = 0.5
# 		tranShuffleLoadsAndGens(inNetwork, shufPerc)
# 	FNAMEOUT = "case_tranShuffleLoadsAndGens.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# if __name__ == '__main__':
# 	_tests()
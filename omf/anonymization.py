''' Functions for anonymizing data in OMF distribution and transmission systems.'''

import json, math, random, datetime, os
from os.path import join as pJoin

omfDir=os.path.dirname(os.path.dirname(__file__))


# DISTRIBUTION FEEDER FUNCTIONS
def distPseudomizeNames(inFeeder):
	''' Replace all names in the inFeeder distribution system with pseudonames composed from the object type and a random ID. Return a key with name and ID pairs. '''
	newNameKey = {}
	randomID = random.randint(0,100)
	# Create nameKey dictionary
	for key in inFeeder['tree']:
		if 'name' in inFeeder['tree'][key]:
			oldName = inFeeder['tree'][key]['name']
			newName = inFeeder['tree'][key]['object'] + str(randomID)
			newNameKey.update({oldName:newName})
			inFeeder['tree'][key]['name'] = newName
			randomID += 1
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
	''' Replace all names in the inFeeder distribution system with a random ID number. '''
	newNameKey = {}
	allKeys = range(len(inFeeder['tree'].keys()))
	random.shuffle(allKeys)

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
		#Line configs
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

	return newNameKey
	
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
	translation = float(translation)
	rotation = float(rotation)
	inFeeder['nodes'] = []
	inFeeder['links'] = []
	inFeeder['hiddenNodes'] = []
	inFeeder['hiddenLinks'] = []
	for key in inFeeder['tree']:
		if ('longitude' in inFeeder['tree'][key]) or ('latitude' in inFeeder['tree'][key]):
			longitude = float(inFeeder['tree'][key]['longitude'])
			latitude = float(inFeeder['tree'][key]['latitude'])
			inFeeder['tree'][key]['longitude'] = longitude + translation*math.cos(rotation)
			inFeeder['tree'][key]['latitude'] = latitude + translation*math.sin(rotation)
		
	return

def distAddNoise(inFeeder, noisePerc):
	''' Add random noise to properties with numeric values for all objects in the inFeeder distribution system based on a noisePerc magnitude. '''
	noisePerc = float(noisePerc)
	for key in inFeeder['tree']:
		for prop in inFeeder['tree'][key]:
			val = inFeeder['tree'][key][prop]
			try:
				parseVal = float(val)
				print(parseVal)
				randNoise = random.uniform(-noisePerc, noisePerc)/100
				print(randNoise)
				randVal = parseVal + randNoise*parseVal
				print(randVal)
				inFeeder['tree'][key][prop] = str(randVal)
			except ValueError:
				try:
					compVal = complex(val)
					realVal = float(compVal.real)
					imagVal = float(compVal.imag)
					randNoise = random.uniform(-noisePerc, noisePerc)/100
					randReal = realVal + randNoise*realVal
					randImag = imagVal + randNoise*imagVal
					randVal = complex(randReal, randImag)
					inFeeder['tree'][key][prop] = str(randVal)
				except ValueError:
					continue
				continue
	return

def distShuffleLoads(inFeeder, shufPerc):
	''' Shuffle the parent properties between all load objects in the inFeeder distribution system. '''
	shufPerc = float(shufPerc)
	houseParents = []
	zipParents = []
	tlParents = []
	# tnParents = []
	for key in inFeeder['tree']:
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key].get('object') == 'house'):
			houseParents.append(inFeeder['tree'][key]['parent'])
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key].get('object') == 'ZIPload'):
			zipParents.append(inFeeder['tree'][key]['parent'])
		if ('from' in inFeeder['tree'][key]) and (inFeeder['tree'][key].get('object') == 'triplex_line'):
			tlParents.append(inFeeder['tree'][key].get('from'))
		# if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key].get('object') == 'triplex_node'):
		# 	tnParents.append(inFeeder['tree'][key]['parent'])
	random.shuffle(houseParents)
	random.shuffle(zipParents)
	random.shuffle(tlParents)
	# random.shuffle(tnParents)
	houseIdx = 0
	zipIdx = 0
	tlIdx = 0
	# tnIdx = 0
	for key in inFeeder['tree']:
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key].get('object') == 'house'):
			if random.randint(0,100) <= shufPerc:
				inFeeder['tree'][key]['parent'] = houseParents[houseIdx]
				houseIdx += 1
		if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key].get('object') == 'ZIPload'):
			if random.randint(0,100) <= shufPerc:
				inFeeder['tree'][key]['parent'] = zipParents[zipIdx]
				zipIdx += 1
		if ('from' in inFeeder['tree'][key]) and (inFeeder['tree'][key].get('object') == 'triplex_line'):
			if random.randint(0,100) <= shufPerc:
				inFeeder['tree'][key]['from'] = tlParents[tlIdx]
				tlIdx += 1
		# if ('parent' in inFeeder['tree'][key]) and (inFeeder['tree'][key].get('object') == 'triplex_node'):
		# 	if random.randint(0,100) < shufPerc:
		# 		inFeeder['tree'][key]['parent'] = tnParents[tnIdx]
		# 		tnIdx += 1
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
	for key in inFeeder['tree']:
		if inFeeder['tree'][key].get('object') == 'triplex_line_configuration':
			for tLine in tLookup:
				if tLookup[tLine].get('configuration') == inFeeder['tree'][key].get('name'):
					tLookup[tLine].update(diameter=inFeeder['tree'][key].get('diameter'))
					tLookup[tLine].update(conductor_1=inFeeder['tree'][key].get('conductor_1'))
					tLookup[tLine].update(conductor_2=inFeeder['tree'][key].get('conductor_2'))
					tLookup[tLine].update(conductor_N=inFeeder['tree'][key].get('conductor_N'))
	for key in inFeeder['tree']:	
		if inFeeder['tree'][key].get('object') == 'triplex_line_conductor':
			for tLine in tLookup:
				if (tLookup[tLine].get('conductor_1') == inFeeder['tree'][key].get('name')) or (tLookup[tLine].get('conductor_2') == inFeeder['tree'][key].get('name')) or (tLookup[tLine].get('conductor_N') == inFeeder['tree'][key].get('name')):
					tLookup[tLine].update(resistance=inFeeder['tree'][key].get('resistance'))
	for tLine in tLookup:
		resistivity = ( float(tLookup[tLine].get('resistance'))*math.pi*(float(tLookup[tLine].get('diameter'))/2.0)**2 ) / float(tLookup[tLine].get('length'))
		tLookup[tLine]['length'] = random.uniform( float(tLookup[tLine].get('length'))-float(tLookup[tLine].get('length')), float(tLookup[tLine].get('length'))+float(tLookup[tLine].get('length')) )
		tLookup[tLine]['diameter'] = random.uniform( (float(tLookup[tLine].get('diameter'))-float(tLookup[tLine].get('diameter')))*1000, (float(tLookup[tLine].get('diameter'))+float(tLookup[tLine].get('diameter')))*1000 ) / 1000.0
		tLookup[tLine]['resistance'] = (resistivity*float(tLookup[tLine].get('length'))) / (math.pi*(float(tLookup[tLine].get('diameter'))/2.0)**2)
		for key in inFeeder['tree']:
			if inFeeder['tree'][key].get('name') == tLine:
				inFeeder['tree'][key]['length'] = tLookup[tLine].get('length')
			if inFeeder['tree'][key].get('name') == tLookup[tLine].get('configuration'):
				inFeeder['tree'][key]['diameter'] = tLookup[tLine].get('diameter')
			if (inFeeder['tree'][key].get('name') == tLookup[tLine].get('conductor_1')) or (inFeeder['tree'][key].get('name') == tLookup[tLine].get('conductor_2')) or (inFeeder['tree'][key].get('name') == tLookup[tLine].get('conductor_N')):
				inFeeder['tree'][key]['resistance'] = tLookup[tLine].get('resistance')
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
	for key in inFeeder['tree']:
		if inFeeder['tree'][key].get('object') == 'line_configuration':
			for uLine in uLookup:
				if uLookup[uLine].get('configuration') == inFeeder['tree'][key].get('name'):
					uLookup[uLine].update(conductor_N=inFeeder['tree'][key].get('conductor_N'))
					uLookup[uLine].update(conductor_A=inFeeder['tree'][key].get('conductor_A'))
					uLookup[uLine].update(conductor_B=inFeeder['tree'][key].get('conductor_B'))
					uLookup[uLine].update(conductor_C=inFeeder['tree'][key].get('conductor_C'))
			for oLine in oLookup:
				if oLookup[oLine].get('configuration') == inFeeder['tree'][key].get('name'):
					oLookup[oLine].update(conductor_N=inFeeder['tree'][key].get('conductor_N'))
					oLookup[oLine].update(conductor_A=inFeeder['tree'][key].get('conductor_A'))
					oLookup[oLine].update(conductor_B=inFeeder['tree'][key].get('conductor_B'))
					oLookup[oLine].update(conductor_C=inFeeder['tree'][key].get('conductor_C'))
	for key in inFeeder['tree']:
		if inFeeder['tree'][key].get('object') == 'underground_line_conductor':
			for uLine in uLookup:
				if (uLookup[uLine].get('conductor_N') == inFeeder['tree'][key].get('name')) or (uLookup[uLine].get('conductor_A') == inFeeder['tree'][key].get('name')) or (uLookup[uLine].get('conductor_B') == inFeeder['tree'][key].get('name')) or (uLookup[uLine].get('conductor_C') == inFeeder['tree'][key].get('name')):
					uLookup[uLine].update(conductor_resistance=inFeeder['tree'][key].get('conductor_resistance'))
					uLookup[uLine].update(conductor_diameter=inFeeder['tree'][key].get('conductor_diameter'))
		elif inFeeder['tree'][key].get('object') == 'overhead_line_conductor':
			for oLine in oLookup:
				if (oLookup[oLine].get('conductor_N') == inFeeder['tree'][key].get('name')) or (oLookup[oLine].get('conductor_A') == inFeeder['tree'][key].get('name')) or (oLookup[oLine].get('conductor_B') == inFeeder['tree'][key].get('name')) or (oLookup[oLine].get('conductor_C') == inFeeder['tree'][key].get('name')):
					oLookup[oLine].update(resistance=inFeeder['tree'][key].get('resistance'))
					oLookup[oLine].update(geometric_mean_radius=inFeeder['tree'][key].get('geometric_mean_radius'))
	for uLine in uLookup:
		resistivity = ( float(uLookup[uLine].get('conductor_resistance'))*math.pi*(float(uLookup[uLine].get('conductor_diameter'))/2.0)**2 ) / float(uLookup[uLine].get('length'))
		uLookup[uLine]['length'] = random.uniform( float(uLookup[uLine].get('length'))-float(uLookup[uLine].get('length')), float(uLookup[uLine].get('length'))+float(uLookup[uLine].get('length')) )
		uLookup[uLine]['conductor_diameter'] = random.randint( (float(uLookup[uLine].get('conductor_diameter'))-float(uLookup[uLine].get('conductor_diameter')))*1000, (float(uLookup[uLine].get('conductor_diameter'))+float(uLookup[uLine].get('conductor_diameter')))*1000 ) / 1000.0
		uLookup[uLine]['conductor_resistance'] = (resistivity*float(uLookup[uLine].get('length'))) / (math.pi*(float(uLookup[uLine].get('conductor_diameter'))/2.0)**2)
		for key in inFeeder['tree']:
			if inFeeder['tree'][key].get('name') == uLine:
				inFeeder['tree'][key]['length'] = uLookup[uLine].get('length')
			if (inFeeder['tree'][key].get('name') == uLookup[uLine].get('conductor_N')) or (inFeeder['tree'][key].get('name') == uLookup[uLine].get('conductor_A')) or (inFeeder['tree'][key].get('name') == uLookup[uLine].get('conductor_B')) or (inFeeder['tree'][key].get('name') == uLookup[uLine].get('conductor_C')):
				inFeeder['tree'][key]['conductor_resistance'] = uLookup[uLine].get('conductor_resistance')
				inFeeder['tree'][key]['conductor_diameter'] = uLookup[uLine].get('conductor_diameter')
	for oLine in oLookup:
		resistivity = ( float(oLookup[oLine].get('resistance'))*math.pi*float(oLookup[oLine].get('geometric_mean_radius'))**2 ) / float(oLookup[oLine].get('length'))
		oLookup[oLine]['length'] = random.uniform( float(oLookup[oLine].get('length'))-float(oLookup[oLine].get('length')), float(oLookup[oLine].get('length'))+float(oLookup[oLine].get('length')) )
		oLookup[oLine]['geometric_mean_radius'] = random.uniform( (float(oLookup[oLine].get('geometric_mean_radius'))-float(oLookup[oLine].get('geometric_mean_radius')))*1000, (float(oLookup[oLine].get('geometric_mean_radius'))+float(oLookup[oLine].get('geometric_mean_radius')))*1000 ) / 1000.0
		oLookup[oLine]['resistance'] = (resistivity*float(oLookup[oLine].get('length'))) / (math.pi*float(oLookup[oLine].get('geometric_mean_radius'))**2)
		for key in inFeeder['tree']:
			if inFeeder['tree'][key].get('name') == oLine:
				inFeeder['tree'][key]['length'] = oLookup[oLine].get('length')
			if (inFeeder['tree'][key].get('name') == oLookup[oLine].get('conductor_N')) or (inFeeder['tree'][key].get('name') == oLookup[oLine].get('conductor_A')) or (inFeeder['tree'][key].get('name') == oLookup[oLine].get('conductor_B')) or (inFeeder['tree'][key].get('name') == oLookup[oLine].get('conductor_C')):
				inFeeder['tree'][key]['resistance'] = oLookup[oLine].get('resistance')
				inFeeder['tree'][key]['geometric_mean_radius'] = oLookup[oLine].get('geometric_mean_radius')
	return

def distSmoothLoads(inFeeder):
	''' Reduce the resolution of load shapes by taking all sub-hourly load dispatch data in the inFeeder distribution system and aggregating to the hour level. ''' 
	agList = []
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
		agAmount = 0
		agHour = timestamp.hour
		if (timestamp.minute == 0) and (timestamp.second == 0) and (timestamp.hour == agHour):
			year = str(timestamp.year)
			month = str(timestamp.month)
			day = str(timestamp.day)
			if len(month) == 1:
				month = '0' + month
			if len(day) == 1:
				day = '0' + day
			agDate = year + '-' + month + '-' + day
			try:
				agAmount = float(pair[1])
			except:
				continue
			agList.append([agDate, agHour, agAmount])
	agZip = zip(*agList)
	for i in range(len(agZip[0])):
		date = str(agZip[0][i])
		hr = str(agZip[1][i])
		val = str(agZip[2][i])
		if len(hr) == 1:
			hr = '0' + hr
		scadaPoint = date + ' ' + hr + ':00:00 PST,' + val
		outList.append(scadaPoint)
	scadaAttach = '\n'.join(outList)
	inFeeder['attachments']['subScadaCalibrated1.player'] = scadaAttach
	return

# TRANSMISSION NETWORK FUNCTIONS
def tranPseudomizeNames(inNetwork):
	''' Replace all names in the inNetwork transmission system with pseudonames composed of the object type and a random ID. Return a key with name and ID pairs. '''
	newBusKey = {}
	randomID = random.randint(0,100)
	# Create busKey dictionary
	for i in inNetwork['bus']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'bus_i' in prop:
				oldBus = i[key]['bus_i']
				# convert newBus to unicode
				newBus = str(randomID).encode("utf-8").decode("utf-8")
				newBusKey.update({oldBus:newBus})
				i[key]['bus_i'] = newBus
				i[newBus] = i.pop(oldBus)
				randomID += 1
	# Replace busNames in generators
	for i in inNetwork['gen']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'bus' in prop:
				oldBus = i[key]['bus']
				i[key]['bus'] = newBusKey[oldBus]
	# Replace busNames in branches
	for i in inNetwork['branch']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'fbus' in prop:
				oldFrom = i[key]['fbus']
				i[key]['fbus'] = newBusKey[oldFrom]
			if 'tbus' in prop:
				oldTo = i[key]['tbus']
				i[key]['tbus'] = newBusKey[oldTo]
	return newBusKey

def tranRandomizeNames(inNetwork):
	''' Replace all names in the inNetwork transmission system with pseudonames composed of the object type and a random ID. '''
	newBusKey = {}
	randomID = random.randint(0,100)
	# Create busKey dictionary
	for i in inNetwork['bus']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'bus_i' in prop:
				oldBus = i[key]['bus_i']
				# convert newBus to unicode
				newBus = str(randomID).encode("utf-8").decode("utf-8")
				newBusKey.update({oldBus:newBus})
				i[key]['bus_i'] = newBus
				i[newBus] = i.pop(oldBus)
				randomID += 1
	# Replace busNames in generators
	for i in inNetwork['gen']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'bus' in prop:
				oldBus = i[key]['bus']
				i[key]['bus'] = newBusKey[oldBus]
	# Replace busNames in branches
	for i in inNetwork['branch']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'fbus' in prop:
				oldFrom = i[key]['fbus']
				i[key]['fbus'] = newBusKey[oldFrom]
			if 'tbus' in prop:
				oldTo = i[key]['tbus']
				i[key]['tbus'] = newBusKey[oldTo]
	return

def tranRandomizeLocations(inNetwork):
	''' Replace all objects' longitude and latitude positions in the inNetwork transmission system with random values. '''
	# inNetwork['bus'] = []
	# inNetwork['gen'] = []
	# inNetwork['branch'] = []
	for i in inNetwork['bus']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'longitude' in prop:
				i[key]['longitude'] = random.randint(0,1000)
			if 'latitude' in prop:
				i[key]['latitude'] = random.randint(0,1000)
	return

def tranTranslateLocations(inNetwork, translation, rotation):
	''' Move the position of all objects in the inNetwork transmission system by a horizontal translation and counter-clockwise rotation. '''
	# inNetwork['bus'] = []
	# inNetwork['gen'] = []
	# inNetwork['branch'] = []
	translation = float(translation)
	rotation = float(rotation)
	for i in inNetwork['bus']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'longitude' in prop:
				longitude = float(i[key]['longitude'])
				i[key]['longitude'] = longitude + translation*math.cos(rotation)
			if 'latitude' in prop:
				latitude = float(i[key]['latitude'])
				i[key]['latitude'] = latitude + translation*math.sin(rotation)
	return

def tranAddNoise(inNetwork, noisePerc):
	''' Add random noise to properties with numeric values for all objects in the inNetwork transmission system based on a noisePerc magnitude. '''
	noisePerc = float(noisePerc)
	for array in inNetwork:
		if (array == 'bus') or (array == 'gen') or (array == 'branch'):
			arrayId = 0
			for i in inNetwork[array]:
				key = str(i.keys()[0])
				for prop in i[key]:
					if ('bus' not in prop) and ('status' not in prop):
						val = i[key][prop]
						try:
							parseVal = float(val)
							randNoise = random.randint(-noisePerc, noisePerc)/100
							randVal = parseVal + randNoise*parseVal
							i[key][prop] = str(randVal)
						except ValueError:
							print 'error'
							continue
				arrayId += 1
	return

def tranShuffleLoadsAndGens(inNetwork, shufPerc):
	''' Shuffle the parent properties between all load and gen objects in the inNetwork transmission system. '''
	shufPerc = float(shufPerc)
	# Shuffle Qd and Pd
	qParents = []
	pParents = []
	busId = 0
	for i in inNetwork['bus']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'Qd' in prop:
				qParents.append(i[key]['Qd'])
			if 'Pd' in prop:
				pParents.append(i[key]['Pd'])
		busId += 1
	random.shuffle(qParents)
	random.shuffle(pParents)
	qIdx = 0
	pIdx = 0
	busId = 0
	for i in inNetwork['bus']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if random.randint(0,100) < shufPerc:
				if 'Qd' in prop:
					i[key]['Qd'] = qParents[qIdx]
					qIdx += 1
				if 'Pd' in prop:
					i[key]['Pd'] = pParents[pIdx]
					pIdx += 1
		busId += 1
	# Shuffle Generators
	genParents = []
	genId = 0
	for i in inNetwork['gen']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'bus' in prop:
				genParents.append(i[key]['bus'])
		genId += 1
	random.shuffle(genParents)
	genId = 0
	genIdx = 0
	for i in inNetwork['gen']:
		key = str(i.keys()[0])
		for prop in i[key]:
			if 'bus' in prop:
				if random.randint(0,100) < shufPerc:
					i[key]['bus'] = genParents[genIdx]
					genIdx += 1
		genId += 1
	return

def _tests():
# 	pass
# 	# DISTRIBUTION FEEDER TESTS
# 	# Test distPseudomizeNames
	# FNAME = "Simple Market System AnonTest.omd"
	# FNAME=pJoin(omfDir,'omf','static','publicFeeders', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# 	nameKey = distPseudomizeNames(inFeeder)
	# 	print nameKey
	# FNAMEOUT = "simpleMarket_distPseudomizeNames.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

# # 	# Test distRandomizeNames
# 	FNAME = "Simple Market System AnonTest.omd"
# 	FNAME=pJoin(omfDir,'omf','static','publicFeeders', FNAME)
# 	with open(FNAME, "r") as inFile:
# 		inFeeder = json.load(inFile)
# 		distRandomizeNames(inFeeder)
# 	FNAMEOUT = "simpleMarket_distRandomizeNames.omd"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inFeeder, outFile, indent=4)

# 	# Test distRandomizeLocations
	# FNAME = "Simple Market System AnonTest.omd"
	# FNAME=pJoin(omfDir,'omf','static','publicFeeders', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# 	distRandomizeLocations(inFeeder)
	# FNAMEOUT = "simpleMarket_distRandomizeLocations.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

# # 	# Test distTranslateLocations
	# FNAME = "Simple Market System AnonTest.omd"
	# FNAME=pJoin(omfDir,'omf','static','publicFeeders', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# 	translation = 20
	# 	rotation = 20
	# 	distTranslateLocations(inFeeder, translation, rotation)
	# FNAMEOUT = "simpleMarket_distTranslateLocations.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

	# Test distAddNoise
	# FNAME = "Simple Market System AnonTest.omd"
	# FNAME=pJoin(omfDir,'omf','static','publicFeeders', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# 	noisePerc = 50
	# 	distAddNoise(inFeeder, noisePerc)
	# FNAMEOUT = "simpleMarket_distAddNoise.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

# 	# Test distShuffleLoads
	# FNAME = "Simple Market System AnonTest.omd"
	# FNAME=pJoin(omfDir,'omf','static','publicFeeders', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# 	shufPerc = 100
	# 	distShuffleLoads(inFeeder, shufPerc)
	# FNAMEOUT = "simpleMarket_distShuffleLoads.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

# 	# Test distModifyTriplexLengths
	# FNAME = "Simple Market System AnonTest.omd"
	# FNAME=pJoin(omfDir,'omf','static','publicFeeders', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# 	distModifyTriplexLengths(inFeeder)
	# FNAMEOUT = "simpleMarket_distModifyTriplexLengths.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

# 	# Test distModifyConductorLengths
	# FNAME = "Olin Barre GH.omd"
	# FNAME=pJoin(omfDir,'omf','static','publicFeeders', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# 	distModifyConductorLengths(inFeeder)
	# FNAMEOUT = "olinBarreGH_distModifyConductorLengths.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)

	# Test distSmoothLoads
	# FNAME = "Calibrated Feeder1.omd"
	# FNAME=pJoin(omfDir,'data','model','public', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inFeeder = json.load(inFile)
	# 	distSmoothLoads(inFeeder)
	# FNAMEOUT = "calibrated_distSmoothLoads.omd"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inFeeder, outFile, indent=4)


# 	TRANSMISSION NETWORK TESTS
# 	Test tranPseudomizeNames	
	# FNAME = "case9.omt"
	# FNAME=pJoin(omfDir,'omf','data','model','admin','Automated Testing of transmission', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inNetwork = json.load(inFile)
	# 	busKey = tranPseudomizeNames(inNetwork)
	# FNAMEOUT = "118_tranPseudomizeNames.omt"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inNetwork, outFile, indent=4)

# 	# Test tranRandomizeNames
	# FNAME = "case9.omt"
	# FNAME=pJoin(omfDir,'omf','data','model','admin','Automated Testing of transmission', FNAME)
	# with open(FNAME, "r") as inFile:
	# 	inNetwork = json.load(inFile)
	# 	tranRandomizeNames(inNetwork)
	# FNAMEOUT = "118_tranRandomizeNames.omt"
	# with open(FNAMEOUT, "w") as outFile:
	# 	json.dump(inNetwork, outFile, indent=4)

# 	# Test tranRandomizeLocations
# 	FNAME = "case118.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		tranRandomizeLocations(inNetwork)
# 	FNAMEOUT = "118_tranRandomizeLocations.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# 	# Test tranTranslateLocation
# 	FNAME = "case118.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		translation = 20
# 		rotation = 20
# 		tranTranslateLocations(inNetwork, translation, rotation)
# 	FNAMEOUT = "118_tranTranslateLocations.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# 	# Testing tranAddNoise
# 	FNAME = "case118.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		noisePerc = 100
#		tranAddNoise(inNetwork, noisePerc)
# 	FNAMEOUT = "118_tranAddNoise.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

# 	# Testing tranShuffleLoadsAndGens
#	FNAME = "case118.omt"
# 	with open(FNAME, "r") as inFile:
# 		inNetwork = json.load(inFile)
# 		shufPerc = 100
# 		tranShuffleLoadsAndGens(inNetwork, shufPerc)
# 	FNAMEOUT = "118_tranShuffleLoadsAndGens.omt"
# 	with open(FNAMEOUT, "w") as outFile:
# 		json.dump(inNetwork, outFile, indent=4)

if __name__ == '__main__':
	_tests()
import csv, feeder, random, math, copy
from StringIO import StringIO

def convert(stdString, seqString):
	''' Take in a .std and .seq from Milsoft and spit out a glmTree.'''

	print 'Beginning Windmil to GLM conversion.'
	
	def csvToArray(csvString):
		''' Simple csv data ingester. '''
		csvReader = csv.reader(StringIO(csvString))
		outArray = []
		for row in csvReader:
			outArray += [row]
		return outArray

	# Get all components from the .std:
	components = csvToArray(stdString)[1:]
	# Get all hardware stats from the .seq:
	hardwareStats = csvToArray(seqString)[1:]
	# We dropped the first rows which are metadata (n.b. there are no headers)

	# Get nominal voltage:
	nominal_voltage = 2400
	for ob in components:
		if ob[1] == 9: nominal_voltage = str(float(ob[14])*1000)

	print nominal_voltage

	# convert numbers in phases filed to alphabets
	def convertPhases():
		for ob in components:
			if ob[2] == '1':
				ob[2] = 'A'
			elif ob[2] == '2':
				ob[2] = 'B'
			elif ob[2] == '3':
				ob[2] = 'C'
			elif ob[2] == '4':
				ob[2] = 'AB'
			elif ob[2] == '5':
				ob[2] = 'AC'
			elif ob[2] == '6':
				ob[2] = 'BC'
			elif ob[2] == '7':
				ob[2] = 'ABC'
			else:
				# by default
				ob[2] = ob[2]

	# The number of allowable sub objects:
	subObCount = 100

	def convertToPixel():
		x_list = []
		y_list = []
		x_pixel_range = 1200
		y_pixel_range = 800
		for component in components:
			x_list.append(float(component[5]))
			y_list.append(float(component[6]))
		# according to convert function  f(x) = a * x + b
		x_a = x_pixel_range / (max(x_list) - min(x_list))
		x_b = -x_a * min(x_list)
		y_a = y_pixel_range / (max(y_list) - min(y_list))
		y_b = -y_a * min(y_list)
		return x_a, x_b, y_a, y_b
	[x_scale, x_b, y_scale, y_b] = convertToPixel()

	def obConvert(objectList):
		''' take a row in the milsoft .std and turn it into a gridlab-type dict'''

		# -----------------------------------------------
		# Globals and helper functions:
		# -----------------------------------------------

		gridlabFields = {	1 : 'overhead_line',	# Overhead Line (Type 1)
							2 : 'capacitor',		# Capacitor (Type 2)
							3 : 'underground_line',	# Underground Line (Type 3)
							4 : 'regulator',		# Regulator (Type 4)
							5 : 'transformer',		# Transformer (Type 5)
							6 : 'switch',			# Switch (Type 6)
							8 : 'node',				# Node (Type 8)
							9 : 'node',				# Source (Type 9)
							10 : 'fuse',			# Overcurrent Device (Type 10)
							11 : 'ZIPload',			# Motor (Type 11)
							12 : 'diesel_dg',		# Generator (Type 12)
							13 : 'load' }			# Consumer (Type 13)
		
		allNames = [x[0] for x in components]

		def statsByName(deviceName):
			''' Helper function to query the hardware csv. '''
			for row in hardwareStats:
				if row[0] == deviceName:
					return row
			return None

		def convertGenericObject(objectList):
			''' this converts attributes that are in every milsoft object regardless of hardware type '''
			newOb = {}
			# Need to replace invalid characters in names:
			newOb['name'] = objectList[0].replace('.','x')
			newOb['object'] = gridlabFields[int(objectList[1])]
			# Coordinate position, except overheadLine and undergoundLine
			# if objectList[1] != '1' and objectList[1] != '3': 
			# convert to the relative pixel position f(x) = a * x + b
			newOb['latitude'] = x_scale * float(objectList[5]) + x_b
			newOb['longitude'] = 800 - (y_scale * float(objectList[6]) + y_b)
			# Some non-Gridlab elements:
			newOb['guid'] = objectList[49].replace('{','').replace('}','')
			newOb['parentGuid'] = objectList[50].replace('{','').replace('}','')
			# Make sure names are unique:
			if allNames.count(newOb['name']) > 1:
				newOb['name'] = newOb['guid']
			return newOb

		# -----------------------------------------------
		# Conversion functions for each type of hardware:
		# -----------------------------------------------

		def convertSwitch(switchList):
			switch = convertGenericObject(switchList)
			switch['status'] = ('OPEN' if switchList[9]=='O' else 'CLOSED')
			switch['phases'] = switchList[2] + 'N'
			return switch

		def convertOvercurrentDevice(ocDeviceList):
			fuse = convertGenericObject(ocDeviceList)
			fuse['phases'] = ocDeviceList[2] + 'N'
			#TODO: set fuse current_limit correctly.
			fuse['current_limit'] = '9999.0 A'
			return fuse

		def convertGenerator(genList):
			generator = convertGenericObject(genList)
			generator['Gen_mode'] = 'CONSTANTP'
			generator['Gen_status'] = ('OFFLINE' if genList[26]=='1' else 'ONLINE')
			# TODO: figure out what other things we need to set.
			return generator

		def convertMotor(motorList):
			motor = convertGenericObject(motorList)
			motor['Gen_mode'] = 'CONSTANTP'
			# Convert horsepower to kW:
			motor['base_power'] = float(motorList[27])*0.73549875
			# These constants come from the fan load in simpleMarketSystem:
			motor['power_fraction'] = 0.013500
			motor['impedance_fraction'] = 0.733200
			motor['current_fraction'] = 0.253400
			motor['power_pf'] = -1.000000
			motor['current_pf'] = 0.950000
			motor['impedance_pf'] = 0.970000
			return motor

		def convertConsumer(consList):
			consumer = convertGenericObject(consList)
			consumer['phases'] = consList[2] + 'N'
			loadClassMap = {	0 : 'R',
								1 : 'C',
								2 : 'C',
								3 : 'U',
								4 : 'U',
								5 : 'A',
								6 : 'I',
								7 : 'U',
								8 : 'U',
								9 : 'U',
								10: 'U'
							}
			consumer['load_class'] = loadClassMap[int(consList[23])]
			#TODO: support kVars.
			consumer['constant_power_A'] = ('100' if float(consList[12])*1000<100 else str(float(consList[12])*1000))
			consumer['constant_power_B'] = ('100' if float(consList[13])*1000<100 else str(float(consList[13])*1000))
			consumer['constant_power_C'] = ('100' if float(consList[14])*1000<100 else str(float(consList[14])*1000))
			consumer['nominal_voltage'] = '120'
			return consumer

		def convertNode(nodeList):
			node = convertGenericObject(nodeList)
			node['phases'] = nodeList[2] + 'N'
			node['nominal_voltage'] = nominal_voltage
			return node

		def convertSource(sourceList):
			source = convertGenericObject(sourceList)
			source['phases'] = sourceList[2]+ 'N'
			source['nominal_voltage'] = str(float(sourceList[14])*1000)
			source['bustype'] = 'SWING'
			return source

		def convertCapacitor(capList):
			capacitor = convertGenericObject(capList)
			capacitor['phases'] = capList[2]+ 'N'
			#TODO: change these from just default values:
			capacitor['pt_phase'] = capacitor['phases']
			capacitor['parent'] = '675;'
			capacitor['phases_connected'] = capacitor['phases']
			capacitor['control'] = 'VOLT'
			capacitor['voltage_set_high'] = '2350.0'
			capacitor['voltage_set_low'] = '2340.0'
			if 'A' in capacitor['phases']:
				capacitor['capacitor_A'] = '0.10 MVAr'
				capacitor['switchA'] = 'CLOSED'
			if 'B' in capacitor['phases']:
				capacitor['capacitor_B'] = '0.10 MVAr'
				capacitor['switchB'] = 'CLOSED'
			if 'C' in capacitor['phases']:
				capacitor['capacitor_C'] = '0.10 MVAr'
				capacitor['switchC'] = 'CLOSED'
			capacitor['control_level'] = 'INDIVIDUAL'
			capacitor['time_delay'] = '300.0'
			capacitor['dwell_time'] = '0.0'
			capacitor['nominal_voltage'] = nominal_voltage
			return capacitor

		def convertOhLine(ohLineList):
			myIndex = components.index(objectList)*subObCount
			overhead = convertGenericObject(ohLineList)
			# TODO: be smarter about multiple neutrals.
			overhead['phases'] = ohLineList[2] + ('N' if ohLineList[33]=='1' else '')
			overhead['length'] = ('10' if float(ohLineList[12])<10 else ohLineList[12])
			overhead[myIndex+1] = {	'omfEmbeddedConfigObject':'configuration object line_configuration',
							'name': overhead['name'] + '-LINECONFIG'}
			overhead[myIndex+1][myIndex+2] = {	'omfEmbeddedConfigObject' : 'spacing object line_spacing',
								'name': overhead['name'] + '-LINESPACING',
								'distance_BC': '7.0',
								'distance_CN': '5.0',
								'distance_AN': '4.272002',
								'distance_AB': '2.5',
								'distance_BN': '5.656854',
								'distance_AC': '4.5'}
			eqdbIndex = {'A':8,'B':9,'C':10,'N':11}
			condIndex = {'A':3,'B':4,'C':5,'N':6}
			for letter in 'ABCN':
				lineIndex = eqdbIndex[letter]
				hardware = statsByName(ohLineList[lineIndex])
				if hardware is None:
					res = '0.185900'
					geoRad = '0.031300'
				else:
					res = hardware[5]
					geoRad = hardware[6]
				overhead[myIndex+1][myIndex+condIndex[letter]] = {	'omfEmbeddedConfigObject':'conductor_' + letter + ' object overhead_line_conductor',
															'resistance': res,
															'geometric_mean_radius': geoRad}
			return overhead

		def convertUgLine(ugLineList):
			myIndex = components.index(objectList)*subObCount
			underground = convertGenericObject(ugLineList)
			# TODO: be smarter about multiple neutrals.
			underground['phases'] = ugLineList[2] + ('N' if ugLineList[33]=='1' else '')
			underground['length'] = ('10' if float(ugLineList[12])<10 else ugLineList[12])
			underground[myIndex+1] = {	'omfEmbeddedConfigObject':'configuration object line_configuration',
								'name': underground['name'] + '-LINECONFIG'}
			underground[myIndex+1][myIndex+2] = {	'omfEmbeddedConfigObject' : 'spacing object line_spacing',
									'name':underground['name'] + '-LINESPACING',
									'distance_AN': '0.000000',
									'distance_CN': '0.000000',
									'distance_BC': '0.500000',
									'distance_AB': '0.500000',
									'distance_AC': '1.000000',
									'distance_BN': '0.000000'}
			#TODO: actually get conductor values!
			condIndex = {'A':3,'B':4,'C':5,'N':6}
			for letter in 'ABCN':
				underground[myIndex+1][myIndex+condIndex[letter]] = {	'omfEmbeddedConfigObject':'conductor_' + letter + ' object underground_line_conductor',
																		'name':underground['name'] + '-PHASE' + letter,
																		'conductor_resistance': '1.540000',
																		'shield_resistance': '0.000000',
																		'neutral_gmr': '0.002080',
																		'outer_diameter': '0.980000',
																		'neutral_strands': '6.000000',
																		'neutral_resistance': '14.872000',
																		'neutral_diameter': '0.064000',
																		'conductor_diameter': '0.292000',
																		'shield_gmr': '0.000000',
																		'conductor_gmr': '0.008830'}
			return underground

		def convertRegulator(regList):
			myIndex = components.index(objectList)*subObCount
			regulator = convertGenericObject(regList)
			regulator['phases'] = regList[2]
			#TODO: figure out whether I'll run into trouble if the following integer isn't unique:
			regulator[myIndex+1] = {}
			regulator[myIndex+1]['name'] = regulator['name'] + '-CONFIG'
			regulator[myIndex+1]['omfEmbeddedConfigObject'] = 'configuration object regulator_configuration'
			#TODO: change these from just default values:
			regulator[myIndex+1]['connect_type'] = '1'
			regulator[myIndex+1]['band_center'] = '2401'
			regulator[myIndex+1]['band_width'] = '50'
			regulator[myIndex+1]['time_delay'] = '30.0'
			regulator[myIndex+1]['raise_taps'] = '16'
			regulator[myIndex+1]['lower_taps'] = '16'
			regulator[myIndex+1]['CT_phase'] = 'ABC'
			regulator[myIndex+1]['PT_phase'] = 'ABC'
			regulator[myIndex+1]['regulation'] = '0.10'
			regulator[myIndex+1]['Control'] = 'MANUAL'
			regulator[myIndex+1]['Type'] = 'A'
			regulator[myIndex+1]['tap_pos_A'] = '1'
			regulator[myIndex+1]['tap_pos_B'] = '1'
			regulator[myIndex+1]['tap_pos_C'] = '1'
			return regulator

		def convertTransformer(transList):
			myIndex = components.index(objectList)*subObCount
			transformer = convertGenericObject(transList)
			transformer['phases'] = transList[2]+ 'N'
			# transformer['nominal_voltage'] = '2400'
			transformer[myIndex+1] = {}
			transformer[myIndex+1]['name'] = transformer['name'] + '-CONFIG'
			transformer[myIndex+1]['omfEmbeddedConfigObject'] = 'configuration object transformer_configuration'
			transformer[myIndex+1]['primary_voltage'] = str(float(transList[10])*1000)
			transformer[myIndex+1]['secondary_voltage'] = str(float(transList[13])*1000)
			#NOTE: seems to be what PNNL uses everywhere:
			transformer[myIndex+1]['shunt_impedance'] = '10000+10000j'
			# NOTE: Windmil doesn't export any information on install type, but Gridlab only puts it in there for info reasons.
			# transformer[1]['install_type'] = 'POLETOP'
			transPhases = transList[2]
			if 1 == len(transPhases):
				transformer[myIndex+1]['connect_type'] = 'SINGLE_PHASE_CENTER_TAPPED'
			else:
				#TODO: support other types of windings (D-D, D-Y, etc.)
				transformer[myIndex+1]['connect_type'] = 'WYE_WYE'
			#TODO: change these from just default values:
			transformer[myIndex+1]['powerA_rating'] = '50 kVA'
			transformer[myIndex+1]['powerB_rating'] = '50 kVA'
			transformer[myIndex+1]['powerC_rating'] = '50 kVA'
			transformer[myIndex+1]['impedance'] = '0.00033+0.0022j'
			#TODO: and change these, which were added to make the transformer work on multiple phases: 
			return transformer

		# Simple lookup table for which function we need to apply:
		objectToFun =	 {	1 : convertOhLine,
							2 : convertCapacitor,
							3 : convertUgLine,
							4 : convertRegulator,
							5 : convertTransformer,
							6 : convertSwitch,
							8 : convertNode,
							9 : convertSource,
							10 : convertOvercurrentDevice,
							11 : convertMotor,
							12 : convertGenerator,
							13 : convertConsumer }
		# Apply fun:
		return objectToFun[int(objectList[1])](objectList)
	# Convert Phases to alphabets type
	convertPhases()
	# Convert to a list of dicts:
	convertedComponents = [obConvert(x) for x in components]

	def fixCompConnectivity(comp):
		''' Rejigger the connectivity attributes to work with Gridlab '''
		# Different object connectivity classes:
		fromToable = ['overhead_line','underground_line','regulator','transformer','switch','fuse']
		nodable = ['node']
		parentable = ['capacitor','ZIPload','diesel_dg','load']

		def getByGuid(guid):
			candidates = [x for x in convertedComponents if 'guid' in x.keys() and x['guid'] == guid]
			if len(candidates) == 0:
				return {}
			else:
				return candidates[0]

		def getByName(name):
			candidates = [x for x in convertedComponents if 'name' in x.keys() and x['name'] == name]
			if len(candidates) == 0:
				return {}
			else:
				return candidates[0]

		def parentType(ob):
			thing = getByGuid(ob['guid'])
			parent = getByGuid(thing['parentGuid'])
			if 'object' in parent.keys():
				return parent['object']
			else:
				pass # print parent

		def phaseMerge(*arg):
			concated = ''.join(arg)
			return ''.join(sorted(set(concated)))

		# If we already stripped the GUID, don't process:
		if 'guid' not in comp.keys():
			return False
		
		# Hang on to the component's parent:
		parent = getByGuid(comp['parentGuid'])
		
		# Rejigger the attributes:
		if comp['object'] in parentable and parentType(comp) in nodable:
			comp['parent'] = parent['name']
		elif comp['object'] in fromToable and parentType(comp) in nodable:
			comp['from'] = parent['name']
		elif comp['object'] in parentable and parentType(comp) in fromToable:
			if 'to' in parent.keys():
				comp['parent'] = parent['to']
				# Making sure our nodes have the superset of connected phases:
				interNode = getByName(parent['to'])
				interNode['phases'] = phaseMerge(interNode['phases'],comp['phases'])
			else:
				# Gotta insert a node between lines and parentable objects:
				newNode = {\
					'object':'node', \
					'phases':comp['phases'],\
					'name': 'node' + comp['name'] + parent['name'], \
					'nominal_voltage':nominal_voltage, \
					'latitude': comp['latitude'],\
					'longitude': comp['longitude']}
				convertedComponents.append(newNode)
				parent['to'] = newNode['name']
				comp['parent'] = newNode['name']
		elif comp['object'] in fromToable and parentType(comp) in fromToable:
			if 'to' in parent.keys():
				comp['from'] = parent['to']
				# Making sure our nodes have the superset of connected phases:
				interNode = getByName(parent['to'])
				interNode['phases'] = phaseMerge(interNode['phases'],comp['phases'])
			else:
				# Gotta insert a node between two lines:
				newNode = {'object':'node', \
							'phases':comp['phases'], \
							'name': 'node' + comp['name'] + parent['name'], \
							'nominal_voltage':nominal_voltage,\
							'latitude': comp['latitude'],\
					'longitude': comp['longitude']}
				convertedComponents.append(newNode)
				parent['to'] = newNode['name']
				comp['from'] = newNode['name']
		else:
			# Here we're in an error case (like loads connected to loads), so do nothing:
			return False
		return True		

	# Fix the connectivity:
	for comp in convertedComponents:
		fixCompConnectivity(comp)

	# Go to a dictionary format so we have a valid glmTree, leave 20 indices for headers:
	glmTree = {20 + convertedComponents.index(x)*subObCount:x for x in convertedComponents}

	#TODO: REMOVE THIS DISASTER HERE AND FIGURE OUT WHY SOME LINKS ARE MALFORMED
	print 'Components removed because they have totally busted connectivity:'
	for key in glmTree.keys():
		# if ('from' in glmTree[key].keys() and 'to' not in glmTree[key].keys()) or ('to' in glmTree[key].keys() and 'from' not in glmTree[key].keys()):
		if glmTree[key]['object'] in ['overhead_line','underground_line','regulator','transformer','switch','fuse'] and ('to' not in glmTree[key].keys() or 'from' not in glmTree[key].keys()):
			# print glmTree[key]
			del glmTree[key]

	#Strip guids:
	for key in glmTree:
		if 'guid' in glmTree[key]: del glmTree[key]['guid']
		if 'parentGuid' in glmTree[key]: del glmTree[key]['parentGuid']

	def fixLinkPhases(comp):
		def getByName(name):
			candidates = [glmTree[x] for x in glmTree if 'name' in glmTree[x] and glmTree[x]['name'] == name]
			if len(candidates) == 0:
				return {}
			else:
				return candidates[0]

		def phaseMin(x,y):
			return ''.join(set(x).intersection(set(y)))

		if comp['object'] in ['overhead_line','underground_line','regulator','transformer','switch','fuse']:
			fromPhases = getByName(comp['from'])['phases']
			toPhases = getByName(comp['to'])['phases']
			comp['phases'] = phaseMin(fromPhases, toPhases)
			return True
		else:
			return False

	for key in glmTree:
		fixLinkPhases(glmTree[key])

	def secondarySystemFix(glm):
		allLoadKeys = [x for x in glm if 'object' in glm[x] and 'parent' in glm[x] and glm[x]['object']=='load']
		allNamesNodesOnLoads = list(set([glm[key]['parent'] for key in allLoadKeys]))
		all2ndTransKeys = []
		all2ndLoadKeys = []
		all2ndNodeKeys = []
		def nameToKey(name):
			hits = [x for x in glm if 'name' in glm[x] and glm[x]['name'] == name]
			if len(hits) == 0:
				return []
			else:
				return hits

		for key in glm:
			if 'object' in glm[key] and glm[key]['object'] == 'transformer':
				fromName = glm[key]['from']
				toName = glm[key]['to']
				if fromName in allNamesNodesOnLoads:
					all2ndTransKeys.append(key)
					all2ndNodeKeys.extend(nameToKey(fromName))
					all2ndLoadKeys.extend([x for x in glm if 'parent' in glm[x] and 'object' in glm[x] and glm[x]['object'] == 'load' and glm[x]['parent'] == fromName])				
				elif toName in allNamesNodesOnLoads:
					all2ndTransKeys.append(key)
					all2ndNodeKeys.extend(nameToKey(toName))
					all2ndLoadKeys.extend([x for x in glm if 'parent' in glm[x] and 'object' in glm[x] and glm[x]['object'] == 'load' and glm[x]['parent'] == toName])
				else:
					# this ain't no poletop transformer
					pass

		# Fix da nodes.
		# {'phases': 'BN', 'object': 'node', 'nominal_voltage': '2400', 'name': 'nodeS1806-32-065T14102'}
		# object triplex_meter { phases BS; nominal_voltage 120; };
		for nodeKey in all2ndNodeKeys:
			newDict = {}
			newDict['object'] = 'triplex_meter'
			newDict['name'] = glm[nodeKey]['name']
			newDict['phases'] = sorted(glm[nodeKey]['phases'])[0] + 'S'
			newDict['nominal_voltage'] = '120'
			glm[nodeKey] = newDict

		# Fix da loads.
		#{'phases': 'BN', 'object': 'load', 'name': 'S1806-32-065', 'parent': 'nodeS1806-32-065T14102', 'load_class': 'R', 'constant_power_C': '0', 'constant_power_B': '1.06969', 'constant_power_A': '0', 'nominal_voltage': '120'}
		for loadKey in all2ndLoadKeys:
			newDict = {}
			newDict['object'] = 'triplex_node'
			newDict['name'] = glm[loadKey]['name']
			newDict['phases'] = sorted(glm[loadKey]['phases'])[0] + 'S'
			a = glm[loadKey]['constant_power_A']
			b = glm[loadKey]['constant_power_B']
			c = glm[loadKey]['constant_power_C']
			powList = [x for x in [a,b,c] if x!='0' and x!='0.0']
			newDict['power_12'] = ('0' if len(powList)==0 else powList.pop())
			newDict['parent'] = glm[loadKey]['parent']
			newDict['nominal_voltage'] = '120'
			glm[loadKey] = newDict

		# Gotta fix the transformer phases too...
		for key in all2ndTransKeys:
			fromName = glm[key]['from']
			toName = glm[key]['to']
			fromToPhases = [glm[x]['phases'] for x in glm if 'name' in glm[x] and glm[x]['name'] in [fromName, toName]]
			glm[key]['phases'] = set('ABC').intersection(*map(set, fromToPhases)).pop() + 'S'
			configKey = [x for x in glm[key] if type(x) is int].pop()
			glm[key][configKey]['connect_type'] = 'SINGLE_PHASE_CENTER_TAPPED'

	# Fixing the secondary (triplex) system.
	secondarySystemFix(glmTree)

	def dedupGlm(compName, glmRef):
		'''
		Assume compName is transformer_configuration
		1. pull out a list of all transformer_configuration dicts.
		2. process to make redundant ones into tuples
		3. go through the list backwards and collapse chains of references. or fold carefully until we can't fold any more.
		4. actually replace the names on other objects and then delete the tuples.
		'''
		def isSameMinusName(x,y):
			newX = {val:x[val] for val in x if val != 'name'}
			newY = {val:y[val] for val in y if val != 'name'}
			return newX==newY
		def dupToTup(inList):
			# Go through a list of components, and given two identicals (up to name) in a row, replace the first one with (name1, name2).
			for i in xrange(0,len(inList)-1):
				if isSameMinusName(inList[i], inList[i+1]):
					inList[i] = (inList[i]['name'], inList[i+1]['name'])
				else:
					pass
		def dechain(tupleList):
			# Go backwards through a list of tuples and change e.g. (1,2),(2,3),(3,4) into (1,4),(2,4),(3,4).
			for i in xrange(len(tupleList)-1,0,-1):
				if tupleList[i][0] == tupleList[i-1][1]:
					tupleList[i-1] = (tupleList[i-1][0], tupleList[i][1])
				else:
					pass

		# sort the components, ignoring their names:
		compList = sorted([glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object']==compName], key=lambda x:{val:x[val] for val in x if val != 'name'})

		dupToTup(compList)

		nameMaps = [x for x in compList if type(x) is tuple]
		realConfigs = [x for x in compList if type(x) is dict]

		dechain(nameMaps)

		#Debug: print the amount of collapse:
		# print 'WORKING ON ' + compName
		# print 'Mappings:'
		# print len(nameMaps)
		# print 'Real configs:'
		# print len(realConfigs)
		# print 'Total:'
		# print len(nameMaps) + len(realConfigs)

		nameDictMap = {x[0]:x[1] for x in nameMaps}

		# Killing duplicate objects
		iterKeys = glmRef.keys()
		for x in iterKeys:
			if 'name' in glmRef[x] and glmRef[x]['name'] in nameDictMap.keys():
				del glmRef[x]

		# Rewiring all objects
		iterKeys = glmRef.keys()
		if compName == 'transformer_configuration': 
			transformers = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'transformer']
			for tranny in transformers:
				if tranny['configuration'] in nameDictMap.keys(): tranny['configuration'] = nameDictMap[tranny['configuration']]
		elif compName == 'regulator_configuration': 
			regulators = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'regulator']
			for reggy in regulators:
				if reggy['configuration'] in nameDictMap.keys(): reggy['configuration'] = nameDictMap[reggy['configuration']]
		elif compName == 'line_spacing': 
			lineConfigs = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'line_configuration']
			for config in lineConfigs:
				if config['spacing'] in nameDictMap.keys(): config['spacing'] = nameDictMap[config['spacing']]
		elif compName == 'overhead_line_conductor' or compName == 'underground_line_conductor': 
			lineConfigs = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] == 'line_configuration']
			for config in lineConfigs:
				if config['conductor_A'] in nameDictMap.keys(): config['conductor_A'] = nameDictMap[config['conductor_A']]
				if config['conductor_B'] in nameDictMap.keys(): config['conductor_B'] = nameDictMap[config['conductor_B']]
				if config['conductor_C'] in nameDictMap.keys(): config['conductor_C'] = nameDictMap[config['conductor_C']]
				if config['conductor_N'] in nameDictMap.keys(): config['conductor_N'] = nameDictMap[config['conductor_N']]
		elif compName == 'line_configuration': 
			lines = [glmRef[x] for x in glmRef if 'object' in glmRef[x] and glmRef[x]['object'] in ['overhead_line','underground_line']]
			for line in lines:
				if line['configuration'] in nameDictMap.keys(): line['configuration'] = nameDictMap[line['configuration']]

	# Fully disembed and remove duplicate configuration objects:
	feeder.fullyDeEmbed(glmTree)
	dedupGlm('transformer_configuration', glmTree)
	dedupGlm('regulator_configuration', glmTree)
	dedupGlm('line_spacing', glmTree)
	dedupGlm('overhead_line_conductor', glmTree)
	dedupGlm('underground_line_conductor', glmTree)
	# NOTE: This last dedup has to come last, because it relies on doing conductors and spacings first!
	dedupGlm('line_configuration', glmTree)
	# Throw some headers on that:
	genericHeaders = [	{"timezone":"PST+8PDT","stoptime":"'2000-01-02 00:00:00'","starttime":"'2000-01-01 00:00:00'","clock":"clock"},
						{"omftype":"#include","argument":"\"schedules.glm\""},
						{"omftype":"#set","argument":"minimum_timestep=60"},
						{"omftype":"#set","argument":"profiler=1"},
						{"omftype":"#set","argument":"relax_naming_rules=1"},
						{"omftype":"module","argument":"generators"},
						{"omftype":"module","argument":"tape"},
						{"omftype":"module","argument":"climate"},
						{"module":"residential","implicit_enduses":"NONE"},
						{"solver_method":"NR","NR_iteration_limit":"50","module":"powerflow"},
						{"object":"climate","name":"Climate","interpolate":"QUADRATIC","tmyfile":"climate.tmy2"}]
	for headId in xrange(len(genericHeaders)):
		glmTree[headId] = genericHeaders[headId]
	
	# to generate position for triplex_meter and triplex_node
	for i in glmTree:
		if glmTree[i].has_key('object') and glmTree[i]['object'] == 'triplex_meter':
			for j in glmTree:
				if glmTree[j].has_key('to') and glmTree[j]['to'] == glmTree[i]['name']:
					glmTree[i]['latitude'] = glmTree[j]['latitude'] + random.uniform(-5,5)
					glmTree[i]['longitude'] = glmTree[j]['longitude'] + random.uniform(-5,5)
					for k in glmTree:
						if glmTree[k].has_key('parent') and glmTree[k]['parent'] == glmTree[i]['name']:
							glmTree[k]['latitude'] = glmTree[i]['latitude'] + random.uniform(-2,2)
							glmTree[k]['longitude'] = glmTree[i]['longitude'] + random.uniform(-2,2)
	# to generate position for load
	for i in glmTree:
		if glmTree[i].has_key('object') and glmTree[i]['object'] == 'load':
			for k in glmTree:
				if glmTree[k].has_key('name') and glmTree[i].has_key('parent') and glmTree[i]['parent'] == glmTree[k]['name']:
					glmTree[i]['latitude'] = glmTree[k]['latitude'] + random.uniform(-2,2)
					glmTree[i]['longitude'] = glmTree[k]['longitude'] + random.uniform(-2,2)
	return glmTree, x_scale, y_scale

if __name__ == '__main__':
	with open('./uploads/INEC-RENOIR.std','r') as stdFile, open('./uploads/INEC.seq','r') as seqFile:
		outGlm = convert(stdFile.read(),seqFile.read())
	from pprint import pprint
	print 'And here is the GLM:'
	pprint(outGlm)
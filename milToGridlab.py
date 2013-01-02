#!/usr/bin/env python

import csv
import treeParser
import os

def convert(stdPath,seqPath):
	''' Take in a .std and .seq from Milsoft and spit out a .glm.'''

	print 'Beginning Windmil to GLM conversion.'

	def csvToArray(csvFileName):
		''' Simple csv data ingester. '''
		with open(csvFileName,'r') as csvFile:
			csvReader = csv.reader(csvFile)
			outArray = []
			for row in csvReader:
				outArray += [row]
			return outArray

	# Get all components from the .std:
	components = csvToArray(stdPath)[1:]
	# Get all hardware stats from the .seq:
	hardwareStats = csvToArray(seqPath)[1:]
	# We dropped the first rows which are metadata (n.b. there are no headers)

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

		def convertGenericObject(objectList):
			''' this converts attributes that are in every milsoft object regardless of hardware type '''
			newOb = {}
			# Need to replace invalid characters in names:
			newOb['name'] = objectList[0].replace('.','x')
			newOb['object'] = gridlabFields[int(objectList[1])]
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
			consumer['constant_power_A'] = consList[12]
			consumer['constant_power_B'] = consList[13]
			consumer['constant_power_C'] = consList[14]
			consumer['nominal_voltage'] = '120'
			return consumer

		def convertNode(nodeList):
			node = convertGenericObject(nodeList)
			node['phases'] = nodeList[2] + 'N'
			#TODO: can we get nominal voltage from the windmil file?
			node['nominal_voltage'] = '2400'
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
			capacitor['pt_phase'] = 'ABCN'
			capacitor['parent'] = '675;'
			capacitor['phases_connected'] = 'ABCN'
			capacitor['control'] = 'VOLT'
			capacitor['voltage_set_high'] = '2350.0'
			capacitor['voltage_set_low'] = '2340.0'
			capacitor['capacitor_A'] = '0.10 MVAr'
			capacitor['capacitor_B'] = '0.10 MVAr'
			capacitor['capacitor_C'] = '0.10 MVAr'
			capacitor['control_level'] = 'INDIVIDUAL'
			capacitor['time_delay'] = '300.0'
			capacitor['dwell_time'] = '0.0'
			capacitor['switchA'] = 'CLOSED'
			capacitor['switchB'] = 'CLOSED'
			capacitor['switchC'] = 'CLOSED'
			capacitor['nominal_voltage'] = '2401.7771'
			return capacitor

		def convertOhLine(ohLineList):
			overhead = convertGenericObject(ohLineList)
			# TODO: be smarter about multiple neutrals.
			overhead['phases'] = ohLineList[2] + ('N' if ohLineList[33]=='1' else '')
			overhead['length'] = ohLineList[12]
			overhead[1] = {	'omfEmbeddedConfigObject':'configuration object line_configuration',
							'name': overhead['name'] + '-LINECONFIG'}
			overhead[1][2] = {	'omfEmbeddedConfigObject' : 'spacing object line_spacing',
								'name': overhead['name'] + '-LINESPACING'}
			if 'A' in overhead['phases']:
				overhead[1][3] = {	'omfEmbeddedConfigObject':'conductor_A object overhead_line_conductor',
									'resistance':statsByName(ohLineList[8])[5],
									'geometric_mean_radius':statsByName(ohLineList[8])[6] }
			if 'B' in overhead['phases']:
				overhead[1][4] = {	'omfEmbeddedConfigObject':'conductor_B object overhead_line_conductor',
									'resistance':statsByName(ohLineList[9])[5],
									'geometric_mean_radius':statsByName(ohLineList[9])[6] }
			if 'C' in overhead['phases']:
				overhead[1][5] = {	'omfEmbeddedConfigObject':'conductor_C object overhead_line_conductor',
									'resistance':statsByName(ohLineList[10])[5],
									'geometric_mean_radius':statsByName(ohLineList[10])[6] }
			if 'N' in overhead['phases']:
				overhead[1][6] = {	'omfEmbeddedConfigObject':'conductor_N object overhead_line_conductor',
									'resistance':statsByName(ohLineList[11])[5],
									'geometric_mean_radius':statsByName(ohLineList[11])[6] }
			return overhead

		def convertUgLine(ugLineList):
			underground = convertGenericObject(ugLineList)
			# TODO: be smarter about multiple neutrals.
			underground['phases'] = ugLineList[2] + ('N' if ugLineList[33]=='1' else '')
			underground['length'] = ugLineList[12]
			underground[1] = {	'omfEmbeddedConfigObject':'configuration object line_configuration',
								'name': underground['name'] + '-LINECONFIG'}
			underground[1][2] = {	'omfEmbeddedConfigObject' : 'spacing object line_spacing',
									'name':underground['name'] + '-LINESPACING'}
			#TODO: actually get conductor values!
			if 'A' in underground['phases']:
				underground[1][3] = {	'omfEmbeddedConfigObject':'conductor_A object underground_line_conductor',
										'name':underground['name'] + '-PHASEA'}
			if 'B' in underground['phases']:
				underground[1][4] = {	'omfEmbeddedConfigObject':'conductor_B object underground_line_conductor',
										'name':underground['name'] + '-PHASEB'}
			if 'C' in underground['phases']:
				underground[1][5] = {	'omfEmbeddedConfigObject':'conductor_C object underground_line_conductor',
										'name':underground['name'] + '-PHASEC'}
			if 'N' in underground['phases']:
				underground[1][6] = {	'omfEmbeddedConfigObject':'conductor_N object underground_line_conductor',
										'name':underground['name'] + '-PHASEN'}
			return underground

		def convertRegulator(regList):
			regulator = convertGenericObject(regList)
			regulator['phases'] = regList[2]
			#TODO: figure out whether I'll run into trouble if the following integer isn't unique:
			regulator[1] = {}
			regulator[1]['name'] = regulator['name'] + '-CONFIG'
			regulator[1]['omfEmbeddedConfigObject'] = 'configuration object regulator_configuration'
			#TODO: change these from just default values:
			regulator[1]['connect_type'] = '1'
			regulator[1]['band_center'] = '2401'
			regulator[1]['band_width'] = '50'
			regulator[1]['time_delay'] = '30.0'
			regulator[1]['raise_taps'] = '16'
			regulator[1]['lower_taps'] = '16'
			regulator[1]['CT_phase'] = 'ABC'
			regulator[1]['PT_phase'] = 'ABC'
			regulator[1]['regulation'] = '0.10'
			regulator[1]['Control'] = 'MANUAL'
			regulator[1]['Type'] = 'A'
			regulator[1]['tap_pos_A'] = '1'
			regulator[1]['tap_pos_B'] = '1'
			regulator[1]['tap_pos_C'] = '1'
			return regulator

		def convertTransformer(transList):
			transformer = convertGenericObject(transList)
			transformer['phases'] = transList[2]+ 'N'
			# transformer['nominal_voltage'] = '2400'
			transformer[1] = {}
			transformer[1]['name'] = transformer['name'] + '-CONFIG'
			transformer[1]['omfEmbeddedConfigObject'] = 'configuration object transformer_configuration'
			transformer[1]['primary_voltage'] = str(float(transList[10])*1000)
			transformer[1]['secondary_voltage'] = str(float(transList[13])*1000)
			#NOTE: seems to be what PNNL uses everywhere:
			transformer[1]['shunt_impedance'] = '10000+10000j'
			# NOTE: Windmil doesn't export any information on install type, but Gridlab only puts it in there for info reasons.
			# transformer[1]['install_type'] = 'POLETOP'
			transPhases = transList[2]
			if 1 == len(transPhases):
				transformer[1]['connect_type'] = 'SINGLE_PHASE_CENTER_TAPPED'
			else:
				#TODO: support other types of windings (D-D, D-Y, etc.)
				transformer[1]['connect_type'] = 'WYE_WYE'
			#TODO: change these from just default values:
			transformer[1]['powerA_rating'] = '50 kVA'
			transformer[1]['powerB_rating'] = '50 kVA'
			transformer[1]['powerC_rating'] = '50 kVA'
			transformer[1]['impedance'] = '0.00033+0.0022j'
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
				newNode = {'object':'node', 'phases':comp['phases'], 'name': 'node' + comp['name'] + parent['name'], 'nominal_voltage':'2400'}
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
				newNode = {'object':'node', 'phases':comp['phases'], 'name': 'node' + comp['name'] + parent['name'], 'nominal_voltage':'2400'}
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

	# Go to a dictionary format so we have a valid glmTree:
	glmTree = {convertedComponents.index(x):x for x in convertedComponents}

	#TODO: REMOVE THIS DISASTER HERE AND FIGURE OUT WHY SOME LINKS ARE MALFORMED
	print 'Components removed because they have connectivity on only one side:'
	for key in glmTree.keys():
		if ('from' in glmTree[key].keys() and 'to' not in glmTree[key].keys()) or ('to' in glmTree[key].keys() and 'from' not in glmTree[key].keys()):
			print glmTree[key]
			del glmTree[key]

	#Strip guids:
	for key in glmTree:
		if 'guid' in glmTree[key]: del glmTree[key]['guid']
		if 'parentGuid' in glmTree[key]: del glmTree[key]['parentGuid']

	genericHeaders =	'clock {\ntimezone PST+8PDT;\nstoptime \'2000-01-02 00:00:00\';\nstarttime \'2000-01-01 00:00:00\';\n};\n\n' + \
						'#set minimum_timestep=60;\n#set profiler=1;\n#set relax_naming_rules=1;\nmodule generators;\nmodule tape;\nmodule climate;\n' + \
						'module residential {\nimplicit_enduses NONE;\n};\n\n' + \
						'module powerflow {\nsolver_method FBS;\nNR_iteration_limit 50;\n};\n\n' + \
						'object climate {\nname Climate;\ninterpolate QUADRATIC;\ntmyfile climate.tmy2;\n};\n\n'

	# TODO: de-embed here?
	# treeParser.fullyDeEmbed(glmTree)

	# Throw some headers on that:
	outGlm = genericHeaders + treeParser.sortedWrite(glmTree)

	return outGlm

def main():
	def convertFile(stdName):
		stdPath = './asciiExports/' + stdName
		seqPath = './asciiExports/' + stdName[0:4] + '.seq'
		outName = stdName[0:-4]
		outGlm = convert(stdPath, seqPath)
		with open('./output/' + outName + '.glm','w') as outFile:
			outFile.write(outGlm)

	allStds = [x for x in os.listdir('asciiExports') if x.endswith('.std')]
	map(convertFile, allStds)

if __name__ == '__main__':
	main()

#TODO: set neutral conductors correctly for all components.
#TODO: get rid of as many magic numbers as possible.
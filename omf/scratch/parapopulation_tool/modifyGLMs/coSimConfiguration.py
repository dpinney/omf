"""
This file contains functions that help configure specific feeders:

	createDistributionSystem(parsedGLM, pathOut, experimentName, selectedFeeder, name, substationkV, substationBus, fncsSubscriptions, randomSeed):
		This function is used to create distribution systems according the user specified settings
	createDistribtutionSystemFNCSConfiguration(glmDict, filePath, name, substationBus, fncsSubscriptions):
		This function adds FNCS capabilities to the feeder in question
	createMATPOWERSystem(populationDict, experimentFilePath, experimentName, matpowerFilePath, matpowerDistPath, matpowerSystem, matpowerAmpFactor, haveMATLAB=False):
		This function creates the MATPOWER simulator according the user specified settings
	createConvenienceScripts(populationDict, fncsExecutablePath, gridlabdExecutablePath, matpowerFilePath, experimentFilePath, experimentName, matpowerSystem, matpowerOPFTime, matpowerFullTime):
		This function creates convenience scripts for running the experiment
	compileMatpowerWrapper(matpowerFilePath, experimentFilePath, experimentName, fncsExecutablePath, matlabExecutablePath):
		This function will create Makefile for MATPOWER and compile the application
	pythonLoadMat(loadProfilePath):
		This funciton is used to load .mat files in python without using MATLAB
	pythonLoadCase(casePath):
		This funciton is used to load a MATPOWER case file without using MATLAB
	pythonSaveCase(casePath, matpowerCaseStruct):
		This funciton is used to save a MATPOWER case file without using MATLAB

Created March 29, 2017 by Jacob Hansen (jacob.hansen@pnnl.gov)

Copyright (c) 2017 Battelle Memorial Institute.  The Government retains a paid-up nonexclusive, irrevocable
worldwide license to reproduce, prepare derivative works, perform publicly and display publicly by or for the
Government, including the right to distribute to other Government contractors.
"""

from __future__ import division
import parseGLM
import feederConfiguration
import feederGenerator
import controllers
import tape
import loads
import numpy as np
import scipy.io as sio
import os, random, math, subprocess, shutil, collections
import traceback
import time

def initLock(l):
    global lock
    lock = l

#def createDistributionSystem(parsedGLM, pathOut, experimentName, selectedFeeder, name, substationkV, substationBus, fncsSubscriptions, randomSeed):
def createDistributionSystem(parsedGLM, pathOut, experimentName, selectedFeederDict, randomSeed, date_list):
	"""
	This function is used to create distribution systems according the user specified settings

	Inputs
		parsedGLM - dictionary that contains the feeder model
		pathOut - path to where we want to save the modified glm
		experimentName - name of the experiment
		selectedFeeder - name of the feeder that you are using as the base
		name - the name of the new glm you want to create
		substationkV - nominal voltage of the substation
		substationBus - the substation bus at which you want to attach this distribution system
		fncsSubscriptions - fncs subscriptions that you are using
		randomSeed - this is the random seed so we can reproduce the results

	Outputs
		None
	"""
	try:

		selectedFeeder = selectedFeederDict['feeder']
		name = selectedFeederDict['name']
		substationkV = selectedFeederDict['substationkV']
		substationBus = selectedFeederDict['substationBus']
		fncsSubscriptions = selectedFeederDict['fncsSubscriptions']
		peakLoad = selectedFeederDict['peakLoad']
		advancedControl = selectedFeederDict['advancedControl']
 		
		# path for this specific system
		filePath =	pathOut + '/' + experimentName + '/' + name

		# create a folder for the feeder
		os.makedirs(filePath)

		# Get information about the feeder we are working with from feederConfiguration()
		feederConfig, useFlags = feederConfiguration.feederConfiguration(selectedFeeder, date_list)

		# Using the settings above we will modify feeder
		modifiedGLM = feederGenerator.modifyFeeder(parsedGLM, feederConfig, useFlags, randomSeed)

		if useFlags['addSubstation'] == 0:
			# addf CCSI substation configuration
			modifiedGLM = feederGenerator.addCCSISubstation(modifiedGLM, feederConfig, useFlags, substationkV)

		if useFlags['addTSEControllers'] == 1:
			if useFlags['addTSEAggregators'] == 1:
				# add the coordinator zpl file if it does not exist already
				createAggregator(pathOut, experimentName, substationBus)

			# Implement controllers if the user asked for it 
			if advancedControl:
				modifiedGLM = controllers.add_residential_control(modifiedGLM, feederConfig, useFlags)

		if useFlags['use_EVs'] == 1:
			# check if we need to implement EVs
			modifiedGLM = loads.add_residential_EVs(modifiedGLM, feederConfig, useFlags)

		if useFlags['use_residential_storage'] == 1:
			# check if we need to implement EVs
			modifiedGLM = loads.add_residential_storage(modifiedGLM, feederConfig, useFlags)

		if useFlags['use_utility_storage'] == 1:
			# check if we need to implement EVs
			modifiedGLM = loads.add_utility_storage(modifiedGLM, feederConfig, useFlags, peakLoad)

		if useFlags['useFNCS'] == 1:
			# add FNCS configuration file and object
			modifiedGLM = createDistribtutionSystemFNCSConfiguration(modifiedGLM, pathOut, experimentName, name, substationBus, fncsSubscriptions, useFlags, advancedControl)

		# add recorders to the GLM
		modifiedGLM = tape.add_recorders(modifiedGLM, feederConfig, filePath, selectedFeeder)

		# write the new feeder model to a file
		glm_string = parseGLM.sortedWrite(modifiedGLM)

		# write the glm to a file
		glmFile = open(filePath + '/' + name + '.glm', 'w')
		glmFile.write(glm_string)
		glmFile.close()
	except Exception as e:
		print "YOU HAVE A MISTAKE IN THE SCRIPT!!!!! ", e
		return False, traceback.format_exc()
	else:
		return True



def createAggregator(pathOut, experimentName, substationBus):
	lock.acquire()
	if not os.path.isdir(pathOut + '/' + experimentName + '/' + 'aggregatorBus' + str(substationBus)):
		os.makedirs(pathOut + '/' + experimentName + '/' + 'aggregatorBus' + str(substationBus))

		# we also need to create the zpl file for the aggregator simulator
		aggregatorFNCSConfigFile = open(pathOut + '/' + experimentName + '/' + 'aggregatorBus' + str(substationBus) +'/fncs.yaml', 'w')

		# create the header for the file
		aggregatorFNCSConfigFile.write('name: {:s}\n'.format('aggregatorBus' + str(substationBus)))
		aggregatorFNCSConfigFile.write('time_delta: 20s\n')
		aggregatorFNCSConfigFile.write('broker: tcp://localhost:5570\n')
		aggregatorFNCSConfigFile.write('values:\n')

		aggregatorFNCSConfigFile.close()
	lock.release()

def createDistribtutionSystemFNCSConfiguration(glmDict, pathOut, experimentName, name, substationBus, fncsSubscriptions, useFlags, advancedControl):
	"""
	This function adds FNCS capabilities to the feeder in question

	Inputs
		glmDict, filePath, name, substationBus, fncsSubscriptions

		glmDict - dictionary that contains the feeder model
		filePath - path to where we want to save the modified glm
		selectedFeeder - name of the feeder that you are using as the base
		name - the name of the new glm you want to create
		substationBus - the substation bus at which you want to attach this distribution system
		fncsSubscriptions - fncs subscriptions that you are using
		useFlags - specific feeder use flags
		advancedControl - bool to determine if advanced control is needed for this system

	Outputs
		glmDict - the modified feeder dictionary
	"""

	# Check if last_key is already in glm dictionary
	def unused_key(key):
		if key in glmDict:
			while key in glmDict:
				key += 1
		return key

	# let's determine the next available key
	last_key = unused_key(0)

	# add the fncs object
	glmDict[last_key] = {'object': 'fncs_msg',
						 'name': '{:s}'.format(name),
						 'configure': 'fncs_configure.cfg'}

	# create the fncs configure file
	fncsFile = open(pathOut + '/' + experimentName + '/' + name + '/fncs_configure.cfg', 'w')
	fncsFile.write('option "transport:hostname localhost, port 5570";\n')
	fncsFile.write('publish "commit:network_node.distribution_load -> distribution_load; 20000";\n')
	# fncsFile.write('publish "commit:network_node.distribution_load.real -> distribution_load_real; 20000";\n')
	fncsFile.write('subscribe "precommit:network_node.positive_sequence_voltage <- {:s}";\n'.format(fncsSubscriptions[0] + '/' + fncsSubscriptions[1] + str(substationBus)))

	if useFlags['addTSEControllers'] == 1 and advancedControl:
		# we need to subscribe to the LMP
		fncsFile.write('subscribe "precommit:retailMarket.fixed_price <- {:s}";\n'.format(fncsSubscriptions[0] + '/' + fncsSubscriptions[2] + str(substationBus)))

		if useFlags['addTSEAggregators'] == 1:
			lock.acquire()
			aggregatorFNCSConfigFile = open(pathOut + '/' + experimentName + '/' + 'aggregatorBus' + str(substationBus) + '/fncs.yaml','a')

			# we also need to publish the bid price and quantity
			for x in glmDict:
				if 'object' in glmDict[x] and glmDict[x]['object'] == 'controller_ccsi':

					fncsName = 'feeder_' + name.split('_')[-1] + '_node_' + glmDict[x]['name'].split('_')[-2] + '_' + glmDict[x]['name'].split('_')[0]
					fncsFile.write('publish "commit:{:s}.bid_price -> {:s}; 0.0001";\n'.format(glmDict[x]['name'], fncsName + '_bid_price'))
					fncsFile.write('publish "commit:{:s}.bid_quantity -> {:s}; 0.0001";\n'.format(glmDict[x]['name'], fncsName + '_bid_quantity'))
					fncsFile.write('publish "commit:{:s}.hvac_load -> {:s}; 0.0001";\n'.format(glmDict[x]['name'].strip('_controller'), fncsName + '_actual_load'))

					aggregatorFNCSConfigFile.write('    {:s}:\n'.format(fncsName + '_bid_price'))
					aggregatorFNCSConfigFile.write('        topic: {:s}/{:s}\n'.format(name, fncsName + '_bid_price'))
					aggregatorFNCSConfigFile.write('        default: 0\n')
					aggregatorFNCSConfigFile.write('        type: double\n')
					aggregatorFNCSConfigFile.write('        list: false\n')
					aggregatorFNCSConfigFile.write('    {:s}:\n'.format(fncsName + '_bid_quantity'))
					aggregatorFNCSConfigFile.write('        topic: {:s}/{:s}\n'.format(name, fncsName + '_bid_quantity'))
					aggregatorFNCSConfigFile.write('        default: 0\n')
					aggregatorFNCSConfigFile.write('        type: double\n')
					aggregatorFNCSConfigFile.write('        list: false\n')
					aggregatorFNCSConfigFile.write('    {:s}:\n'.format(fncsName + '_actual_load'))
					aggregatorFNCSConfigFile.write('        topic: {:s}/{:s}\n'.format(name, fncsName + '_actual_load'))
					aggregatorFNCSConfigFile.write('        default: 0\n')
					aggregatorFNCSConfigFile.write('        type: double\n')
					aggregatorFNCSConfigFile.write('        list: false\n')

			aggregatorFNCSConfigFile.close()
			lock.release()
	fncsFile.close()

	return glmDict

def createMATPOWERSystem(populationDict, experimentFilePath, experimentName, matpowerFilePath, matpowerDistPath, matpowerSystem, matpowerAmpFactor, matpowerPFTime, date_list, haveMATLAB=False):
	"""
	This function creates the MATPOWER simulator according the user specified settings

	Inputs
		populationDict - dictionary containing properties for all the feeders we are using
		experimentFilePath - path to where we want to save the experiment
		experimentName - name of the experiment
		matpowerFilePath - path for the MATPOWER files
		matpowerDistPath - path for the MATPOWER distribution
		matpowerSystem - name of the MATPOWER case being used
		matpowerAmpFactor - amplication factor added to the distribution load
		haveMATLAB - setting to tell the script if you have MATLAB installed

	Outputs
		populationDict - modified dictionary containing properties for all the feeders we are using
	"""

	# Get information about the co-sim we are working on
	feederConfig, useFlags = feederConfiguration.feederConfiguration('', date_list)

	# Initialize psuedo-random seed
	random.seed(10)

	# create folder for MATPOWER simulator
	os.makedirs(experimentFilePath + '/' + experimentName + '/matpower')

	if haveMATLAB is True:
		# open matlab engine and add MATPOWER to the path
		import matlab.engine as MatlabEngine
		eng = MatlabEngine.start_matlab('-nojvm -nodisplay -nosplash')
		eng.addpath(matpowerDistPath)

		# load the MATPOWER case struct
		matpowerCaseStruct = eng.loadcase(matpowerDistPath + '/' + matpowerSystem + '.m')
	else:
		matpowerCaseStruct = pythonLoadCase(matpowerDistPath + '/' + matpowerSystem + '.m')

	# pull out the bus data as we need it to adjust the case
	busData = np.asarray(matpowerCaseStruct['bus'])

	# determine the total distribution load along with the total matpower load
	totalDistributionLoad = sum([populationDict[dist]['peakLoad'] for dist in populationDict])
	totalMatpowerLoad = sum(busData[:, 2])

	# warn the user if the distribution load is larger than the matpower load
	if (totalMatpowerLoad - totalDistributionLoad) < 0:
		print 'WARNING: you are trying to attach more load than the transmission system can support'

	# determine buses that contain load and take the bus number, these will be used to attach distribution systems
	matpowerLoadBuses = busData[busData[:, 2] > 0, 0]
	matpowerLoadBuskV = busData[busData[:, 2] > 0, 9]
	matpowerLoad = busData[busData[:, 2] > 0, 2]

	# this calculates the percentage of system out of the total that should be attached at each bus. This is then multiplied by the user specified number of systems
	# We use ceil() to ensure that the sum will always be greater than or equal to number of distribution systems
	matpowerDistributionCountAtBuses = []
	for load in matpowerLoad:
		matpowerDistributionCountAtBuses.append(math.ceil((load / totalMatpowerLoad) * len(populationDict.keys())))

	# determine the number of regions specified in the MATPWOER case file contains region specification
	if 'region' in matpowerCaseStruct:
		regionFlag = True
		regionData = np.asarray(matpowerCaseStruct['region'])
		regionData = regionData[busData[:, 2] > 0, 1]
		#print regionData
	else:
		regionFlag = False


	# loop through the population dictionary and start placing the distribution systems
	for idx, feeder in enumerate(populationDict):
		success = False
		count = 0
		while success is False:
			if regionFlag is True:
				# pull region from the feeder info
				feederRegion = populationDict[feeder]['region']
				feederRegionIdx = np.nonzero(regionData == feederRegion)[0]
				#print feederRegion, feederRegionIdx, random.choice(feederRegionIdx)
				busIdx = random.choice(feederRegionIdx)  # pick a random bus to use
			else:
				busIdx = random.randint(0, len(matpowerLoadBuses)-1) # pick a random bus to use
			# we will try 20 times to find a bus
			if matpowerDistributionCountAtBuses[busIdx] > 0 and matpowerLoad[busIdx] >= populationDict[feeder]['peakLoad']:
				success = True
				populationDict[feeder]['substationkV'] = matpowerLoadBuskV[busIdx]
				populationDict[feeder]['substationBus'] = int(matpowerLoadBuses[busIdx])
				populationDict[feeder]['fncsSubscriptions'] = ['matpower', 'three_phase_voltage_B', 'LMP_B']
				matpowerLoad[busIdx] -= populationDict[feeder]['peakLoad']
				matpowerDistributionCountAtBuses[busIdx] -= 1


			if count > 20 and success is False:
				# let's find an alternative bus for the system!
				if matpowerLoad[busIdx] >= populationDict[feeder]['peakLoad']:
					success = True
					populationDict[feeder]['substationkV'] = matpowerLoadBuskV[busIdx]
					populationDict[feeder]['substationBus'] = int(matpowerLoadBuses[busIdx])
					populationDict[feeder]['fncsSubscriptions'] = ['matpower', 'three_phase_voltage_B', 'LMP_B']
					matpowerLoad[busIdx] -= populationDict[feeder]['peakLoad']
					matpowerDistributionCountAtBuses[busIdx] -= 1
				else:
					# let's find an alternative bus for the system!
					for secondaryIdx, load in enumerate(matpowerLoad):
						if load >= populationDict[feeder]['peakLoad']:
							if regionFlag is True:
								if regionData[secondaryIdx] == populationDict[feeder]['region']:
									success = True
									populationDict[feeder]['substationkV'] = matpowerLoadBuskV[secondaryIdx]
									populationDict[feeder]['substationBus'] = int(matpowerLoadBuses[secondaryIdx])
									populationDict[feeder]['fncsSubscriptions'] = ['matpower', 'three_phase_voltage_B', 'LMP_B']
									matpowerLoad[secondaryIdx] -= populationDict[feeder]['peakLoad']
									matpowerDistributionCountAtBuses[secondaryIdx] -= 1
									break
							else:
								success = True
								populationDict[feeder]['substationkV'] = matpowerLoadBuskV[secondaryIdx]
								populationDict[feeder]['substationBus'] = int(matpowerLoadBuses[secondaryIdx])
								populationDict[feeder]['fncsSubscriptions'] = ['matpower', 'three_phase_voltage_B', 'LMP_B']
								matpowerLoad[secondaryIdx] -= populationDict[feeder]['peakLoad']
								matpowerDistributionCountAtBuses[secondaryIdx] -= 1
								break

					if success is False:
						# still didn't find a spot so we will just attach it where we first intended it!
						success = True
						populationDict[feeder]['substationkV'] = matpowerLoadBuskV[busIdx]
						populationDict[feeder]['substationBus'] = int(matpowerLoadBuses[busIdx])
						populationDict[feeder]['fncsSubscriptions'] = ['matpower', 'three_phase_voltage_B', 'LMP_B']
						matpowerLoad[busIdx] = 0
						matpowerDistributionCountAtBuses[busIdx] -= 1
			count += 1
		# print populationDict[feeder]

	# now we just need to update the matpower case struct
	for rowIdx, row in enumerate(matpowerCaseStruct['bus']):
		if row[0] in matpowerLoadBuses:
			matpowerCaseStruct['bus'][rowIdx][2] = matpowerLoad[np.where(matpowerLoadBuses==row[0])]
			# we will also adjust the reactive load to be 25% of the real load. Should probably be changed in the future
			matpowerCaseStruct['bus'][rowIdx][3] = matpowerLoad[np.where(matpowerLoadBuses==row[0])]*0.25

	# loop through the population dictionary and start placing the distribution systems
	uniqueSubstationBus = []
	for feeder in populationDict:
		if not populationDict[feeder]['substationBus'] in uniqueSubstationBus:
			uniqueSubstationBus.append(populationDict[feeder]['substationBus'])

	# if we have transactive controllers we need to add dispatcheable loads in the case file
	if useFlags['addTSEControllers'] == 1:
		genLength = matpowerCaseStruct['gen'].shape[1]
		genCostLength = matpowerCaseStruct['gencost'].shape[1]
		for subBus in uniqueSubstationBus:
			temp = np.zeros((genLength,), dtype=np.float64)
			temp2 = np.zeros((genCostLength,), dtype=np.float64)
			temp[0] = subBus
			temp[6] = matpowerCaseStruct['baseMVA']
			temp[16:20] = 'Inf'
			temp2[0] = 2
			matpowerCaseStruct['gen'] = np.vstack([matpowerCaseStruct['gen'], temp])
			matpowerCaseStruct['gencost'] = np.vstack([matpowerCaseStruct['gencost'], temp2])

	# print matpowerCaseStruct['gen'].shape[1]
	# print matpowerCaseStruct['gen']

	if haveMATLAB is True:
		# save the adjusted MATPOWER case struct
		eng.savecase(experimentFilePath + '/' + experimentName + '/matpower/' + matpowerSystem + '.m', matpowerCaseStruct)
	else:
		pythonSaveCase(experimentFilePath + '/' + experimentName + '/matpower/' + matpowerSystem + '.m',matpowerCaseStruct)

	# open the case file again to add in FNCS specific information
	matpowerFile = open(experimentFilePath + '/' + experimentName + '/matpower/' + matpowerSystem + '.m', 'a')

	# this section add all the setting for the FNCS related matrices for MATPOWER
	matpowerFile.write('\n%% ======================================================================\n')
	matpowerFile.write('%% FNCS communication interface\n')
	matpowerFile.write('%% This has been added to simplify the set-up process\n')
	matpowerFile.write('%% ======================================================================\n')
	matpowerFile.write('%% Number of buses where distribution networks are going to be connected to\n')
	matpowerFile.write('mpc.BusFNCSNum = {:d};\n'.format(len(uniqueSubstationBus)))
	matpowerFile.write('%% Buses where distribution networks are going to be connected to\n')
	matpowerFile.write('mpc.BusFNCS = [\n')
	# loop through the unique bus list
	for bus in uniqueSubstationBus:
		matpowerFile.write('\t{:d}\n'.format(int(bus)))

	matpowerFile.write('];\n')
	matpowerFile.write('%% Number of distribution feeders (GridLAB-D instances)\n')
	matpowerFile.write('mpc.SubNumFNCS = {:d}\n'.format(int(len(populationDict.keys()))))
	matpowerFile.write('%% Substation names, and the transmission network bus where it is connected to\n')
	matpowerFile.write('mpc.SubNameFNCS = [\n')
	# loop through the population dictionary and start placing the distribution systems
	for feeder in populationDict:
		matpowerFile.write('\t{:s}\t{:d}\n'.format(populationDict[feeder]['name'], int(populationDict[feeder]['substationBus'])))

	matpowerFile.write('];\n')
	matpowerFile.write('%% ======================================================================\n')
	matpowerFile.write('%% For creating scenarios for visualization\n')
	matpowerFile.write('%% Setting up the matrix of generators that could become off-line\n')
	matpowerFile.write('%% Number of generators that might be turned off-line\n')
	matpowerFile.write('mpc.offlineGenNum = 0;\n')
	matpowerFile.write('%% Matrix contains the bus number of the corresponding off-line generators\n')
	matpowerFile.write('mpc.offlineGenBus = [ ];\n')

	matpowerFile.write('%% ======================================================================\n')
	matpowerFile.write('%% An amplification factor is used to simulate a higher load at the feeder end\n')
	matpowerFile.write('mpc.ampFactor = {:0.3f};\n'.format(matpowerAmpFactor))
	matpowerFile.write('%% ======================================================================\n')

	# add some extra information about matrix sizes that is needed by the MATPOWER wrapper
	for key in matpowerCaseStruct:
		if not (key == 'baseMVA' or key == 'version' or key == 'function'):
			i = len(matpowerCaseStruct[key])
			j = len(matpowerCaseStruct[key][0])
			matpowerFile.write('mpc.{:s}Data = [{:d} {:d}];\n'.format(key, i, j))

	matpowerFile.close()

	# open the file we want to add the load profiles too
	loadprofilerealFile = open(experimentFilePath + '/' + experimentName + '/matpower/real_power_demand.txt', 'w')
	loadprofilereacFile = open(experimentFilePath + '/' + experimentName + '/matpower/reactive_power_demand.txt', 'w')

	if haveMATLAB is True:
		# construct the real power load for matpower. The normalized_load_data.mat contains some normalized load profiles given by Jason
		normalizedLoadData = eng.load(matpowerFilePath + '/normalized_load_data.mat')
		normalizedLoadData = np.asarray(normalizedLoadData['my_data'])
	else:
		# construct the real power load for matpower. The normalized_load_data.mat contains some normalized load profiles given by Jason
		normalizedLoadData = pythonLoadMat(matpowerFilePath + '/normalized_load_data.mat')
		normalizedLoadData = np.asarray(normalizedLoadData['my_data'])

	# this section assigns a random load profile to each bus in the transmission system
	numberOfBuses = len(matpowerCaseStruct['bus'])
	for idx, busRow in enumerate(matpowerCaseStruct['bus']):
		busLoadReal = busRow[2]
		busLoadReac = busRow[3]
		profile = random.randint(0, 8) # we have 9 profiles and we want to pick one at random
		for loadLen in xrange(0, 288):
			if not loadLen == 287:
				loadprofilerealFile.write('{:0.2f} '.format(busLoadReal * normalizedLoadData[loadLen, profile]))
				loadprofilereacFile.write('{:0.2f} '.format(busLoadReac * normalizedLoadData[loadLen, profile]))
			elif idx == numberOfBuses-1:
				loadprofilerealFile.write('{:0.2f}'.format(busLoadReal * normalizedLoadData[loadLen, profile]))
				loadprofilereacFile.write('{:0.2f}'.format(busLoadReac * normalizedLoadData[loadLen, profile]))
			else:
				loadprofilerealFile.write('{:0.2f}\n'.format(busLoadReal * normalizedLoadData[loadLen, profile]))
				loadprofilereacFile.write('{:0.2f}\n'.format(busLoadReac * normalizedLoadData[loadLen, profile]))

	loadprofilerealFile.close()
	loadprofilereacFile.close()

	if haveMATLAB is True:
		# close the matlab engine
		eng.quit()

	# we also need to create the yaml file for the matpower simulator
	matpowerFNCSConfigFile = open(experimentFilePath + '/' + experimentName + '/matpower/fncs.yaml', 'w')

	# create the header for the file
	matpowerFNCSConfigFile.write('name: matpower\n')
	matpowerFNCSConfigFile.write('time_delta: {:d}s\n'.format(int(matpowerPFTime)))
	matpowerFNCSConfigFile.write('broker: tcp://localhost:5570\n')
	matpowerFNCSConfigFile.write('values:\n')

	# loop through the population dictionary and start placing the distribution systems
	for idx, feeder in enumerate(populationDict):
		matpowerFNCSConfigFile.write('    {:s}:\n'.format(populationDict[feeder]['name']))
		matpowerFNCSConfigFile.write('        topic: {:s}/distribution_load\n'.format(populationDict[feeder]['name']))
		matpowerFNCSConfigFile.write('        default: 0 + 0 j MVA\n')
		matpowerFNCSConfigFile.write('        type: complex\n')
		matpowerFNCSConfigFile.write('        list: false\n')

	for subBus in uniqueSubstationBus:
		matpowerFNCSConfigFile.write('    Bus_{:s}_dispLoad:\n'.format(str(subBus)))
		matpowerFNCSConfigFile.write('        topic: aggregatorBus{:s}/dispLoad\n'.format(str(subBus)))
		matpowerFNCSConfigFile.write('        default: 0\n')
		matpowerFNCSConfigFile.write('        type: double\n')
		matpowerFNCSConfigFile.write('        list: false\n')
		matpowerFNCSConfigFile.write('    Bus_{:s}_dispLoadDemandCurve:\n'.format(str(subBus)))
		matpowerFNCSConfigFile.write('        topic: aggregatorBus{:s}/dispLoadDemandCurve\n'.format(str(subBus)))
		matpowerFNCSConfigFile.write('        default: 0,0,0\n')
		matpowerFNCSConfigFile.write('        type: string\n')
		matpowerFNCSConfigFile.write('        list: false\n')

	matpowerFNCSConfigFile.close()

	# copy MATPOWER libraries needed to the experiment
	shutil.copy(matpowerFilePath + '/libMATPOWER.h', experimentFilePath + '/' + experimentName + '/matpower')
	shutil.copy(matpowerFilePath + '/libMATPOWER.so', experimentFilePath + '/' + experimentName + '/matpower')

	return populationDict


def createHeatTemplate(maximumInstanceCount, selectedFlavors, flavors, populationDict, experimentFilePath, experimentName, matpowerSystem, matpowerOPFTime, matpowerAmpFactor, matpowerFullTime, matpowerLogLevel, fncsLogLevel, fncsPort, date_list):
	"""
	This function creates a heat template for running the experiment

	Inputs
		populationDict - dictionary containing properties for all the feeders we are using
		experimentName - name of the experiment
		matpowerSystem - name of the MATPOWER case being used
		matpowerOPFTime - time between OPF solutions in MATPOWER
		matpowerFullTime - full simulation time for MATPOWER

	Outputs
		None
	"""	

	# count FNCS and MATPOWER and thereby decrease the maximum
	maximumInstanceCount -= 2

	# Get information about the feeder we are working with from feederConfiguration()
	feederConfig, useFlags = feederConfiguration.feederConfiguration('', date_list)

	# let's get a count of how many distribution system we have in the simulation
	distributionSystemCount = len(populationDict)

	# estimated memory used per distribution system in GB
	distributionMemoryUsage = 0.8

	# check if the maximum number of instances allowed is enough to support the experiment
	if maximumInstanceCount < math.ceil((distributionSystemCount*distributionMemoryUsage) / float(flavors[selectedFlavors['GridLAB-D']][1])):
		print 'WARNING: your distribution system population is too big for the resources you have'

	
	# determine if we need the maximum number of instances
	if maximumInstanceCount*flavors[selectedFlavors['GridLAB-D']][0] > distributionSystemCount:
		# we have more VCPUs than we need so we scale back on the instances we deploy
		gldInstanceCount = int(math.ceil(distributionSystemCount / flavors[selectedFlavors['GridLAB-D']][0]))
	else:
		gldInstanceCount = int(maximumInstanceCount)

	# number of feeders per chunk
	feederPerChunk = int(math.ceil(distributionSystemCount/gldInstanceCount))

	# create list of feeders and divide into the chunks we need
	feederNames = [populationDict[x]['name'] for x in populationDict]
	feederNames = [feederNames[x:x+feederPerChunk] for x in xrange(0, len(feederNames), feederPerChunk)]

	# open the files we need
	heatFile = open(experimentFilePath + '/' + experimentName + '/heat.txt', 'wb')
	
	heatFile.write('heat_template_version: 2015-04-30\n\n')

	heatFile.write('description: Co-Simulation experiment "{:s}" using transmission model "{:s}" with a total of "{:0.0f}" distribution systems\n\n'.format(experimentName, matpowerSystem, distributionSystemCount))

	heatFile.write('parameters:\n')
	heatFile.write('  private_net_name:\n')
	heatFile.write('    type: string\n')
	heatFile.write('    description: Name of private network to attach to\n')
	heatFile.write('  image_name:\n')
	heatFile.write('    type: string\n')
	heatFile.write('    description: The image to be used for devices\n')
	heatFile.write('  key_name:\n')
	heatFile.write('    type: string\n')
	heatFile.write('    description: Key-pair to be used for devices\n')
	heatFile.write('  FNCS_broker_port:\n')
	heatFile.write('    type: string\n')
	heatFile.write('    description: The port FNCS should run on\n')
	heatFile.write('  experiment_server:\n')
	heatFile.write('    type: string\n')
	heatFile.write('    description: The server at which the experiment is hosted\n\n')

	heatFile.write('resources:\n')
	heatFile.write('  FNCS-machine:\n')
	heatFile.write('    type: OS::Nova::Server\n')
	heatFile.write('    properties:\n')
	heatFile.write('      key_name: {get_param: key_name}\n')
	heatFile.write('      image: {get_param: image_name}\n')
	heatFile.write('      flavor: {:s}\n'.format(selectedFlavors['FNCS']))
	heatFile.write('      networks:\n')
	heatFile.write('      - network: {get_param: private_net_name}\n')
	heatFile.write('      user_data_format: RAW\n')
	heatFile.write('      user_data:\n')
	heatFile.write('        str_replace:\n')
	heatFile.write('          params:\n')
	heatFile.write('            $fncs-port:\n')
	heatFile.write('              {get_param: FNCS_broker_port}\n')
	heatFile.write('            $experiment_server:\n')
	heatFile.write('              {get_param: experiment_server}\n')
	heatFile.write('          template: |\n')
	heatFile.write('            #!/bin/bash\n')
	heatFile.write('              echo "export FNCS_BROKER=tcp://*:$fncs-port" >> /home/ubuntu/CCSI.env\n')
	heatFile.write('              echo "export FNCS_LOG_STDOUT=yes" >> /home/ubuntu/CCSI.env\n')
	heatFile.write('              echo "export FNCS_CONFIG_FILE=fncs.yaml" >> /home/ubuntu/CCSI.env\n')	
	heatFile.write('              echo "export FNCS_LOG_LEVEL={:s}" >> /home/ubuntu/CCSI.env\n'.format(fncsLogLevel))
	heatFile.write('              source /home/ubuntu/CCSI.env\n')
	heatFile.write('              sudo mount $experiment_server:/home/ubuntu/CCSIcode/experiments /home/ubuntu/experiments\n')
	heatFile.write('              cd /home/ubuntu/experiments/{:s}\n'.format(experimentName))
	heatFile.write('              fncs_broker {:d} &> simLog.out &\n'.format(int(distributionSystemCount+1)))
	heatFile.write('            # ...\n\n')

	heatFile.write('  MATPOWER-machine:\n')
	heatFile.write('    type: OS::Nova::Server\n')
	heatFile.write('    properties:\n')
	heatFile.write('      key_name: {get_param: key_name}\n')
	heatFile.write('      image: {get_param: image_name}\n')
	heatFile.write('      flavor: {:s}\n'.format(selectedFlavors['MATPOWER']))
	heatFile.write('      networks:\n')
	heatFile.write('      - network: {get_param: private_net_name}\n')
	heatFile.write('      user_data_format: RAW\n')
	heatFile.write('      user_data:\n')
	heatFile.write('        str_replace:\n')
	heatFile.write('          params:\n')
	heatFile.write('            $fncs-ip:\n')
	heatFile.write('              get_attr: [FNCS-machine, first_address]\n')
	heatFile.write('            $fncs-port:\n')
	heatFile.write('              {get_param: FNCS_broker_port}\n')
	heatFile.write('            $experiment_server:\n')
	heatFile.write('              {get_param: experiment_server}\n')
	heatFile.write('          template: |\n')
	heatFile.write('            #!/bin/bash\n')
	heatFile.write('              echo "export FNCS_BROKER=tcp://$fncs-ip:$fncs-port" >> /home/ubuntu/CCSI.env\n')
	heatFile.write('              echo "export FNCS_LOG_STDOUT=yes" >> /home/ubuntu/CCSI.env\n')
	heatFile.write('              echo "export FNCS_CONFIG_FILE=fncs.yaml" >> /home/ubuntu/CCSI.env\n')
	heatFile.write('              echo "export FNCS_LOG_LEVEL={:s}" >> /home/ubuntu/CCSI.env\n'.format(fncsLogLevel))
	heatFile.write('              echo "export MATPOWER_LOG_LEVEL={:s}" >> /home/ubuntu/CCSI.env\n'.format(matpowerLogLevel))
	heatFile.write('              source /home/ubuntu/CCSI.env\n')
	heatFile.write('              sudo mount $experiment_server:/home/ubuntu/CCSIcode/experiments /home/ubuntu/experiments\n')
	heatFile.write('              cd /home/ubuntu/experiments/{:s}/matpower\n'.format(experimentName))
	heatFile.write('              start_MATPOWER {:s}.m real_power_demand.txt reactive_power_demand.txt {:d} {:d} "{:s}" load_data.txt dispatchable_load_data.txt generator_data.txt &> simLog.out &\n'.format(matpowerSystem, int(matpowerFullTime), int(matpowerOPFTime), feederConfig['startdate']))
	heatFile.write('            # ...\n\n')

	for idx in xrange(0, gldInstanceCount):	
		heatFile.write('  GridLAB-machine-{:d}:\n'.format(idx+1))
		heatFile.write('    type: OS::Nova::Server\n')
		heatFile.write('    properties:\n')
		heatFile.write('      key_name: {get_param: key_name}\n')
		heatFile.write('      image: {get_param: image_name}\n')
		heatFile.write('      flavor: {:s}\n'.format(selectedFlavors['GridLAB-D']))
		heatFile.write('      networks:\n')
		heatFile.write('      - network: {get_param: private_net_name}\n')
		heatFile.write('      user_data_format: RAW\n')
		heatFile.write('      user_data:\n')
		heatFile.write('        str_replace:\n')
		heatFile.write('          params:\n')
		heatFile.write('            $fncs-ip:\n')
		heatFile.write('              get_attr: [FNCS-machine, first_address]\n')
		heatFile.write('            $fncs-port:\n')
		heatFile.write('              {get_param: FNCS_broker_port}\n')
		heatFile.write('            $experiment_server:\n')
		heatFile.write('              {get_param: experiment_server}\n')
		heatFile.write('          template: |\n')
		heatFile.write('            #!/bin/bash\n')
		heatFile.write('              echo "export FNCS_BROKER=tcp://$fncs-ip:$fncs-port" >> /home/ubuntu/CCSI.env\n')
		heatFile.write('              echo "export FNCS_LOG_STDOUT=yes" >> /home/ubuntu/CCSI.env\n')
		heatFile.write('              echo "export FNCS_LOG_LEVEL={:s}" >> /home/ubuntu/CCSI.env\n'.format(fncsLogLevel))
		heatFile.write('              source /home/ubuntu/CCSI.env\n')
		heatFile.write('              sudo mount $experiment_server:/home/ubuntu/CCSIcode/experiments /home/ubuntu/experiments\n')
		for feeder in feederNames[idx]:
			heatFile.write('              cd /home/ubuntu/experiments/{:s}/{:s}\n'.format(experimentName, feeder))
			heatFile.write('              gridlabd {:s}.glm &> simLog.out &\n'.format(feeder))
		heatFile.write('            # ...\n\n')

	       

def createConvenienceScripts(populationDict, experimentResources, matpowerFilePath, aggregatorFilePath, experimentFilePath, experimentName, matpowerSystem, matpowerOPFTime, matpowerAmpFactor, matpowerFullTime, matpowerLogLevel, fncsLogLevel, date_list, fncsPort='5570'):
	"""
	This function creates convenience scripts for running the experiment

	Inputs
		populationDict - dictionary containing properties for all the feeders we are using
		experimentResources - dictionary containing information on the compute resoruce available to the experiment
		gridlabdExecutablePath - path to the GridLAB-D executable
		matpowerFilePath - path for the MATPOWER files
		experimentFilePath - path to where we want to save the experiment
		experimentName - name of the experiment
		matpowerSystem - name of the MATPOWER case being used
		matpowerOPFTime - time between OPF solutions in MATPOWER
		matpowerFullTime - full simulation time for MATPOWER

	Outputs
		None
	"""

	# Get information about the feeder we are working with from feederConfiguration()
	feederConfig, useFlags = feederConfiguration.feederConfiguration('', date_list)

	# get list of aggregators in the system
	aggregatorList = []
	if useFlags['addTSEAggregators'] == 1:
		for feeder in populationDict:
			if populationDict[feeder]['substationBus'] not in aggregatorList:
				aggregatorList.append(populationDict[feeder]['substationBus'])

	# open the files we need
	runFile = open(experimentFilePath + '/' + experimentName + '/runAll.sh', 'wb')
	copyFile = open(experimentFilePath + '/' + experimentName + '/copyAll.sh', 'wb')
	killFile = open(experimentFilePath + '/' + experimentName + '/killAll.sh', 'wb')

	# header for the copy file
	copyFile.write('#!/bin/bash\n\n')
	copyFile.write('clear\n\n')

	# check how many resources we have available
	if len(experimentResources.keys()) == 1:
		# create the run all script. This script will run the experiment. if we only have one resource we do not have to do anything fancy and the script is easy to create
		runFile.write('#!/bin/bash\n\n')
		runFile.write('clear\n')
		runFile.write('echo "Running on single resource"\n\n')

		runFile.write('\necho "Executing experiment..."\n\n')

		runFile.write('logFile="simLog.out"\n')
		runFile.write('fncsConfigFile="fncs.yaml"\n')
		runFile.write('fncsLogLevel="{:s}"\n'.format(fncsLogLevel))
		runFile.write('matpowerLogLevel="{:s}"\n'.format(matpowerLogLevel))
		runFile.write('aggregatorLogLevel="{:s}"\n'.format(matpowerLogLevel))
		runFile.write('fncsPath="{:s}/bin"\n'.format(experimentResources[experimentResources.keys()[0]][3]))
		runFile.write('gldPath="{:s}/bin"\n'.format(experimentResources[experimentResources.keys()[0]][4]))
		runFile.write('experimentPath="{:s}"\n'.format(experimentFilePath + '/' + experimentName))
		runFile.write('fncsBrokerPort="tcp://*:{:s}"\n'.format(fncsPort))
		runFile.write('fncsBrokerIP="tcp://localhost:{:s}"\n\n'.format(fncsPort))

		# Do the exports so FNCS and other software behave the way we want
		runFile.write('export FNCS_LOG_STDOUT=yes\n')
		runFile.write('export FNCS_CONFIG_FILE=$fncsConfigFile\n')
		runFile.write('export FNCS_LOG_LEVEL=$fncsLogLevel\n')
		runFile.write('export MATPOWER_LOG_LEVEL=$matpowerLogLevel\n')
		runFile.write('export AGGREGATOR_LOG_LEVEL=$aggregatorLogLevel\n')
		runFile.write('export FNCS_BROKER=$fncsBrokerIP\n\n')

		# add the broker process
		if useFlags['useFNCS'] == 1:
			runFile.write('export FNCS_BROKER=$fncsBrokerPort\n')
			runFile.write('cd $fncsPath && exec ./fncs_broker {:d} &> $experimentPath/$logFile &\n'.format(int(len(populationDict.keys()))+1+len(aggregatorList)))
			runFile.write('export FNCS_BROKER=$fncsBrokerIP\n')


		# loop through the population dictionary and create a process for each
		for idx, feeder in enumerate(populationDict):
			runFile.write('cd $experimentPath/{:s} && exec $gldPath/gridlabd {:s}.glm &> $logFile &\n'.format(populationDict[feeder]['name'], populationDict[feeder]['name']))

		# add the MATPOWER process
		runFile.write('cd $experimentPath/matpower && exec ./start_MATPOWER {:s}.m real_power_demand.txt reactive_power_demand.txt {:d} {:d} "{:s}" load_data.txt dispatchable_load_data.txt generator_data.txt &> $logFile &\n'.format(matpowerSystem, int(matpowerFullTime), int(matpowerOPFTime), feederConfig['startdate']))

		if useFlags['addTSEAggregators'] == 1:
			for aggregator in aggregatorList:
				runFile.write('cd $experimentPath/aggregatorBus{:d} && exec ./aggregator {:d} {:f} &> $logFile &\n'.format(aggregator, int(matpowerFullTime), matpowerAmpFactor))

		runFile.write('\necho "Done..."\n\n')
		runFile.write('wait\n')
		runFile.write('\nexit 0')

		# create the copy all script. This script adds the ability to copy over all MATPOWER related libraries and executeable
		copyFile.write('cp {:s}/lib*.so {:s}\n'.format(matpowerFilePath, experimentFilePath + '/' + experimentName + '/matpower'))
		copyFile.write('cp {:s}/lib*.h {:s}\n'.format(matpowerFilePath, experimentFilePath + '/' + experimentName + '/matpower'))
		copyFile.write('cp {:s}/start_MATPOWER {:s}\n'.format(matpowerFilePath, experimentFilePath + '/' + experimentName + '/matpower'))
		if useFlags['addTSEAggregators'] == 1:
			for aggregator in aggregatorList:
				copyFile.write('cp {:s}/aggregator {:s}{:d}\n'.format(aggregatorFilePath, experimentFilePath + '/' + experimentName + '/aggregatorBus', aggregator))
		copyFile.write('\nexit 0')

		# create the kill all script. This script will terminate an experiment
		killFile.write('#!/bin/bash\n\n')
		killFile.write('clear\n\n')
		killFile.write('pkill -9 start_MATPOWER\n')
		killFile.write('pkill -9 aggregator\n')
		killFile.write('pkill -9 fncs_broker\n')
		killFile.write('pkill -9 gridlabd\n')
		killFile.write('\nexit 0')

	else:
		# create the run all script. This script will run the experiment. We have more than one resource available and we will now have to not only run the experiment but also distribute it amoung the machines
		# let's order the dictionary such that the main node is always first!
		experimentResources = collections.OrderedDict(sorted(experimentResources.items(), key=lambda t: t[1][0], reverse=True))

		runFile.write('#!/bin/bash\n\n')

		runFile.write('clear\n')
		runFile.write('echo "Running on a total of {:d} compute resources"\n'.format(len(experimentResources.keys())))
		runFile.write('echo "Distributing experiment to available resources..."\n\n')

		# since we have to run on more than one machine we will take the experiment folder and divide it into equal parts. One for each resource!
		# but first we need to obtain a list of all the feeders we have so we can decide a fair distribution
		feederFolderNames = [name for name in os.listdir(experimentFilePath + '/' + experimentName) if os.path.isdir(experimentFilePath + '/' + experimentName + '/' + name) and 'feeder' in name]
		numberOfFeeders = len(feederFolderNames)
		numberOfResources = len(experimentResources.keys())

		if numberOfResources > numberOfFeeders:
			raise Exception("we have more resources that we have distribution systems. Not able to proceed")

		# loop through each resource and assing parts
		for resource, resourceName in enumerate(experimentResources):
			# copy the include folder
			shutil.copytree(experimentFilePath + '/' + experimentName + '/include', experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}/include'.format(resource+1, numberOfResources))

			# copy the kill script
			# shutil.copyfile(experimentFilePath + '/' + experimentName + '/killAll.sh', experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}/killAll.sh'.format(resource + 1, numberOfResources))

			# copy the matpower simulator to resource one only
			if resource == 0:
				shutil.move(experimentFilePath + '/' + experimentName + '/matpower', experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}/matpower'.format(resource + 1, numberOfResources))
				if useFlags['addTSEAggregators'] == 1:
					for aggregator in aggregatorList:
						shutil.move(experimentFilePath + '/' + experimentName + '/aggregatorBus{:d}'.format(aggregator), experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}/aggregatorBus{:d}'.format(resource + 1, numberOfResources, aggregator))

			# we need to update this list as we remove feeders
			feederFolderNames = [name for name in os.listdir(experimentFilePath + '/' + experimentName) if os.path.isdir(experimentFilePath + '/' + experimentName + '/' + name) and 'feeder' in name]

			# if we are at the last resource we need to copy the remanining feeders
			if resource != numberOfResources-1:
				# find number of systems to move. We need at least one!
				numberToMove = max(math.floor(numberOfFeeders/numberOfResources),1)

				# random sample the number of feeders we need to move
				feederNamesToMove = random.sample(feederFolderNames, int(numberToMove))
			else:
				# move the remaining feeders
				feederNamesToMove = feederFolderNames

			for feederName in feederNamesToMove:
				shutil.move(experimentFilePath + '/' + experimentName + '/' + feederName, experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}'.format(resource + 1, numberOfResources) + '/' + feederName)

			# after creating each part we need to add the scp line in the run script so each part will be transfered to the appropiate resource
			if resource != 0:
				runFile.write('ssh {:s}@{:s} "\n\trm -rf {:s}\n\tmkdir -p {:s}\n"\n'.format(experimentResources[resourceName][2], resourceName, experimentResources[resourceName][1], experimentResources[resourceName][1] + '/experiments/' + experimentName))
				runFile.write('scp -rq {:s}/part_{:d}_of_{:d} {:s}@{:s}:{:s}/{:s}/ &\n'.format(experimentFilePath + '/' + experimentName, resource + 1, numberOfResources, experimentResources[resourceName][2], resourceName, experimentResources[resourceName][1] + '/experiments/', experimentName))

		# remove the include folder at root
		shutil.rmtree(experimentFilePath + '/' + experimentName + '/include')

		runFile.write('\nwait\n\n')
		runFile.write('echo "Executing experiment..."\n\n')

		# loop through resource to create processes
		for resource, resourceName in enumerate(experimentResources):
			# open a run file for the specific part we are working on
			runFilePart = open(experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}/run.sh'.format(resource + 1, numberOfResources), 'wb')

			# some basics for the file
			runFilePart.write('logFile="simLog.out"\n')
			runFilePart.write('fncsConfigFile="fncs.yaml"\n')
			runFilePart.write('fncsLogLevel="{:s}"\n'.format(fncsLogLevel))
			runFilePart.write('matpowerLogLevel="{:s}"\n'.format(matpowerLogLevel))
			runFilePart.write('aggregatorLogLevel="{:s}"\n'.format(matpowerLogLevel))
			runFilePart.write('fncsBrokerPort="tcp://*:{:s}"\n'.format(fncsPort))
			runFilePart.write('fncsBrokerIP="tcp://{:s}:{:s}"\n\n'.format(experimentResources.keys()[0], fncsPort))

			# Do the exports so FNCS and other software behave the way we want
			runFilePart.write('export FNCS_LOG_STDOUT=yes\n')
			runFilePart.write('export FNCS_CONFIG_FILE=$fncsConfigFile\n')
			runFilePart.write('export FNCS_LOG_LEVEL=$fncsLogLevel\n')
			runFilePart.write('export MATPOWER_LOG_LEVEL=$matpowerLogLevel\n')
			runFilePart.write('export AGGREGATOR_LOG_LEVEL=$aggregatorLogLevel\n')
			runFilePart.write('export FNCS_BROKER=$fncsBrokerIP\n\n')

			# get a list of feeders in the specific part we are working on
			feederFolderNames = [name for name in os.listdir(experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}'.format(resource + 1, numberOfResources)) if os.path.isdir(experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}'.format(resource + 1, numberOfResources) + '/' + name) and 'feeder' in name]

			# for the main resource we will execute MATPOWER and broker
			if resource == 0:
				runFile.write('{:s}/part_{:d}_of_{:d}/run.sh &\n\n'.format(experimentFilePath + '/' + experimentName, resource + 1, numberOfResources))

				if useFlags['useFNCS'] == 1:
					runFilePart.write('export FNCS_BROKER=$fncsBrokerPort\n')
					runFilePart.write('cd {:s}/bin && exec ./fncs_broker {:d} &> {:s}/$logFile &\n'.format(experimentResources[resourceName][3], int(len(populationDict.keys())) + 1 + len(aggregatorList), experimentFilePath + '/' + experimentName))
					runFilePart.write('export FNCS_BROKER=$fncsBrokerIP\n\n')

				runFilePart.write('cd {:s}/part_{:d}_of_{:d}/matpower && exec ./start_MATPOWER {:s}.m real_power_demand.txt reactive_power_demand.txt {:d} {:d} "{:s}" load_data.txt dispatchable_load_data.txt generator_data.txt &> $logFile &\n'.format(experimentFilePath + '/' + experimentName, resource + 1, numberOfResources, matpowerSystem, int(matpowerFullTime), int(matpowerOPFTime), feederConfig['startdate']))
				#runFilePart.write('disown\n')

				if useFlags['addTSEAggregators'] == 1:
				# if feederConfig['addTSEControllers'] == 1:
					for aggregator in aggregatorList:
						runFilePart.write('cd {:s}/part_{:d}_of_{:d}/aggregatorBus{:d} && exec ./aggregator {:d} {:f} &> $logFile &\n'.format(experimentFilePath + '/' + experimentName, resource + 1, numberOfResources, aggregator, int(matpowerFullTime), matpowerAmpFactor))

			else:
				runFile.write('ssh {:s}@{:s} "'.format(experimentResources[resourceName][2], resourceName))
				runFile.write('{:s}/part_{:d}_of_{:d}/run.sh" &\n\n'.format(experimentFilePath + '/' + experimentName, resource + 1, numberOfResources))


			# loop through feeders
			for feeder in feederFolderNames:
				runFilePart.write('cd {:s}/part_{:d}_of_{:d}/{:s} && exec {:s}/bin/gridlabd {:s}.glm &> $logFile &\n'.format(experimentFilePath + '/' + experimentName, resource + 1, numberOfResources, feeder, experimentResources[resourceName][4], feeder))
				#runFilePart.write('disown\n')


			runFilePart.write('wait\n')
			# close the file
			runFilePart.close()

			termProcess = subprocess.Popen(['chmod', '+x', 'run.sh'], cwd=experimentFilePath + '/' + experimentName + '/part_{:d}_of_{:d}'.format(resource + 1, numberOfResources), stdout=subprocess.PIPE)
			if termProcess.wait() != 0:
				raise Exception('something went wrong when doing "chmod" on run.sh')

		runFile.write('\necho "Experiment is running!"\n\n')

		# wait for the experiment to finish
		runFile.write('wait\n\n')

		# loop through resources so we can collect all the data!
		for resource, resourceName in enumerate(experimentResources):
			if resource != 0:
				runFile.write('scp -rq {:s}@{:s}:{:s}/{:s}/part_{:d}_of_{:d} ./ &\n'.format(experimentResources[resourceName][2], resourceName, experimentResources[resourceName][1] + '/experiments', experimentName, resource + 1, numberOfResources))

		runFile.write('\necho "Transfering files!"\n\n')

		# wait for the experiment to finish
		runFile.write('wait\n\n')

		runFile.write('echo "Done..."\n\n')
		runFile.write('exit 0')

		# create the copy all script. This script adds the ability to copy over all MATPOWER related libraries and executeable
		copyFile.write('cp {:s}/lib*.so {:s}\n'.format(matpowerFilePath, experimentFilePath + '/' + experimentName + '/part_1_of_{:d}/matpower'.format(numberOfResources)))
		copyFile.write('cp {:s}/lib*.h {:s}\n'.format(matpowerFilePath, experimentFilePath + '/' + experimentName + '/part_1_of_{:d}/matpower'.format(numberOfResources)))
		copyFile.write('cp {:s}/start_MATPOWER {:s}\n'.format(matpowerFilePath, experimentFilePath + '/' + experimentName + '/part_1_of_{:d}/matpower'.format(numberOfResources)))
		if useFlags['addTSEAggregators'] == 1:
			for aggregator in aggregatorList:
				copyFile.write('cp {:s}/aggregator {:s}/part_1_of_{:d}/aggregatorBus{:d}\n'.format(aggregatorFilePath, experimentFilePath + '/' + experimentName, numberOfResources, aggregator))
		copyFile.write('\nexit 0')

		# create the kill all script. This script will terminate an experiment
		killFile.write('#!/bin/bash\n\n')
		killFile.write('clear\n\n')
		killFile.write('pkill -9 runAll\n')
		killFile.write('pkill -9 start_MATPOWER\n')
		killFile.write('pkill -9 aggregator\n')
		killFile.write('pkill -9 fncs_broker\n')
		killFile.write('pkill -9 gridlabd\n\n')

		# loop through resource so we can killall of remote resources!
		for resource, resourceName in enumerate(experimentResources):
			if resource != 0:
				killFile.write('ssh {:s}@{:s} "\n\tpkill -9 start_MATPOWER\n\tpkill -9 fncs_broker\n\tpkill -9 gridlabd\n"\n'.format(experimentResources[resourceName][2], resourceName))

		killFile.write('\nexit 0')

	runFile.close()
	copyFile.close()
	killFile.close()


def compileWrappers(matpowerFilePath, aggregatorFilePath, experimentFilePath, experimentName, fncsExecutablePath, matlabExecutablePath, zeroMQLibraryPath, CZMQLibraryPath, date_list):
	"""
	This function will create Makefile for MATPOWER and compile the application

	Inputs
		matpowerFilePath - path for the MATPOWER files
		experimentFilePath - path to where we want to save the experiment
		experimentName - name of the experiment
		fncsExecutablePath - path to the FNCS executable
		matlabExecutablePath - path to the MATLAB executable

	Outputs
		None
	"""

	# Get information about the co-sim we are working on
	feederConfig, useFlags = feederConfiguration.feederConfiguration('', date_list)

	# open the make file for the MATPOWER wrapper
	makeFile = open(matpowerFilePath + '/Makefile', 'wb')

	makeFile.write('MCR_PATH := {:s}\n'.format(matlabExecutablePath))
	makeFile.write('FNCS_PATH := {:s}\n'.format(fncsExecutablePath))
	makeFile.write('zeroMQ_PATH := {:s}\n'.format(zeroMQLibraryPath))
	makeFile.write('CZMQ_PATH := {:s}\n'.format(CZMQLibraryPath))
	makeFile.write('CXX = g++\n\n')

	makeFile.write('CXXFLAGS =\n')
	makeFile.write('CXXFLAGS += -g\n')
	makeFile.write('CXXFLAGS += -ansi\n')
	makeFile.write('CXXFLAGS += -pthread\n')
	makeFile.write('CXXFLAGS += -O0\n\n')

	makeFile.write('CPPFLAGS =\n')
	makeFile.write('CPPFLAGS += -I$(MCR_PATH)/extern/include/cpp\n')
	makeFile.write('CPPFLAGS += -I$(MCR_PATH)/extern/include\n')
	makeFile.write('CPPFLAGS += -I$(FNCS_PATH)/include\n')
	makeFile.write('CPPFLAGS += -I$(zeroMQ_PATH)/include\n')
	makeFile.write('CPPFLAGS += -I$(CZMQ_PATH)/include\n')
	makeFile.write('CPPFLAGS += -D_GNU_SOURCE\n')
	makeFile.write('CPPFLAGS += -DUNIX\n')
	makeFile.write('CPPFLAGS += -DX11\n')
	makeFile.write('CPPFLAGS += -DGLNXA64\n')
	makeFile.write('CPPFLAGS += -DGCC\n')
	makeFile.write('CPPFLAGS += -DNDEBUG\n\n')

	makeFile.write('LDFLAGS =\n')
	makeFile.write('LDFLAGS += -Wl,-rpath=.\n')
	makeFile.write('LDFLAGS += -Wl,-rpath-link,$(MCR_PATH)/bin/glnxa64\n')
	makeFile.write('LDFLAGS += -L$(MCR_PATH)/runtime/glnxa64\n')
	makeFile.write('LDFLAGS += -L$(FNCS_PATH)/lib\n')
	makeFile.write('LDFLAGS += -Wl,-rpath=$(FNCS_PATH)/lib\n')
	makeFile.write('LDFLAGS += -L$(zeroMQ_PATH)/lib\n')
	makeFile.write('LDFLAGS += -Wl,-rpath=$(zeroMQ_PATH)/lib\n')
	makeFile.write('LDFLAGS += -L$(CZMQ_PATH)/lib\n')
	makeFile.write('LDFLAGS += -Wl,-rpath=$(CZMQ_PATH)/lib\n')
	makeFile.write('LDFLAGS += -L.\n\n')

	makeFile.write('LIBS =\n')
	makeFile.write('LIBS += -lmwmclmcrrt\n')
	makeFile.write('LIBS += -lm\n')
	makeFile.write('LIBS += -lMATPOWER\n')
	makeFile.write('LIBS += -lfncs\n')
	makeFile.write('LIBS += -lczmq\n')
	makeFile.write('LIBS += -ljsoncpp\n')
	makeFile.write('LIBS += -lzmq\n\n')

	makeFile.write('all: start_MATPOWER\n\n')

	makeFile.write('start_MATPOWER.o: start_MATPOWER.cpp\n')
	makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

	makeFile.write('matpowerintegrator.o: matpowerintegrator.cpp\n')
	makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

	makeFile.write('read_load_profile.o: read_load_profile.cpp\n')
	makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

	makeFile.write('read_model_dim.o: read_model_dim.cpp\n')
	makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

	makeFile.write('read_model_data.o: read_model_data.cpp\n')
	makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

	makeFile.write('matpowerLoadMetrics.o: matpowerLoadMetrics.cpp\n')
	makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

	makeFile.write('matpowerGeneratorMetrics.o: matpowerGeneratorMetrics.cpp\n')
	makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

	makeFile.write('jsoncpp.o: jsoncpp.cpp\n')
	makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

	makeFile.write('start_MATPOWER: start_MATPOWER.o matpowerintegrator.o read_load_profile.o read_model_dim.o read_model_data.o matpowerLoadMetrics.o matpowerGeneratorMetrics.o jsoncpp.o\n')
	makeFile.write('	$(CXX) -o $@ $^ $(CXXFLAGS) $(LDFLAGS) $(LIBS)\n\n')

	makeFile.write('clean:\n')
	makeFile.write('	rm -f *~\n')
	makeFile.write('	rm -f *.o\n')
	makeFile.write('	rm -f *.mod\n')
	makeFile.write('	rm -f start_MATPOWER\n')
	makeFile.write('	rm -f *.chk\n')
	makeFile.write('	rm -f *.out')

	makeFile.close()

	if useFlags['addTSEAggregators'] == 1:
		# open the make file for the aggregator
		makeFile = open(aggregatorFilePath + '/Makefile', 'wb')

		makeFile.write('FNCS_PATH := {:s}\n'.format(fncsExecutablePath))
		makeFile.write('zeroMQ_PATH := {:s}\n'.format(zeroMQLibraryPath))
		makeFile.write('CZMQ_PATH := {:s}\n'.format(CZMQLibraryPath))
		makeFile.write('CXX = g++\n\n')

		makeFile.write('CXXFLAGS =\n')
		makeFile.write('CXXFLAGS += -g\n')
		makeFile.write('CXXFLAGS += -ansi\n')
		makeFile.write('CXXFLAGS += -pthread\n')
		makeFile.write('CXXFLAGS += -O0\n\n')
		makeFile.write('CXXFLAGS += -std=c++11\n\n')

		makeFile.write('CPPFLAGS =\n')
		makeFile.write('CPPFLAGS += -I$(FNCS_PATH)/include\n')
		makeFile.write('CPPFLAGS += -I$(zeroMQ_PATH)/include\n')
		makeFile.write('CPPFLAGS += -I$(CZMQ_PATH)/include\n')
		makeFile.write('CPPFLAGS += -D_GNU_SOURCE\n')
		makeFile.write('CPPFLAGS += -DUNIX\n')
		makeFile.write('CPPFLAGS += -DX11\n')
		makeFile.write('CPPFLAGS += -DGLNXA64\n')
		makeFile.write('CPPFLAGS += -DGCC\n')
		makeFile.write('CPPFLAGS += -DNDEBUG\n\n')

		makeFile.write('LDFLAGS =\n')
		makeFile.write('LDFLAGS += -Wl,-rpath=.\n')
		makeFile.write('LDFLAGS += -L$(FNCS_PATH)/lib\n')
		makeFile.write('LDFLAGS += -Wl,-rpath=$(FNCS_PATH)/lib\n')
		makeFile.write('LDFLAGS += -L$(zeroMQ_PATH)/lib\n')
		makeFile.write('LDFLAGS += -Wl,-rpath=$(zeroMQ_PATH)/lib\n')
		makeFile.write('LDFLAGS += -L$(CZMQ_PATH)/lib\n')
		makeFile.write('LDFLAGS += -Wl,-rpath=$(CZMQ_PATH)/lib\n')
		makeFile.write('LDFLAGS += -L.\n\n')

		makeFile.write('LIBS =\n')
		makeFile.write('LIBS += -lm\n')
		makeFile.write('LIBS += -lfncs\n')
		makeFile.write('LIBS += -lczmq\n')
		makeFile.write('LIBS += -lzmq\n\n')

		makeFile.write('all: aggregator\n\n')

		makeFile.write('aggregator.o: aggregator.cpp\n')
		makeFile.write('	$(CXX) -c $< -o $@ $(CXXFLAGS) $(CPPFLAGS)\n\n')

		makeFile.write('aggregator: aggregator.o\n')
		makeFile.write('	$(CXX) -o $@ $^ $(CXXFLAGS) $(LDFLAGS) $(LIBS)\n\n')

		makeFile.write('clean:\n')
		makeFile.write('	rm -f *~\n')
		makeFile.write('	rm -f *.o\n')
		makeFile.write('	rm -f *.mod\n')
		makeFile.write('	rm -f aggregator\n')
		makeFile.write('	rm -f *.chk\n')
		makeFile.write('	rm -f *.out')

		makeFile.close()


	# compile the MATPOWER wrapper and change file rights so the experiment is good to go
	termProcess = subprocess.Popen(['make', 'clean'], cwd=matpowerFilePath, stdout=subprocess.PIPE)
	if termProcess.wait() != 0:
		raise Exception('something went wrong when doing "make clean"')

	termProcess = subprocess.Popen(['make'], cwd=matpowerFilePath, stdout=subprocess.PIPE)
	if termProcess.wait() != 0:
		raise Exception('something went wrong when doing "make"')

	termProcess = subprocess.Popen(['chmod', '+x', 'start_MATPOWER'], cwd=matpowerFilePath, stdout=subprocess.PIPE)
	if termProcess.wait() != 0:
		raise Exception('something went wrong when doing "chmod" on matpower')

	if useFlags['addTSEAggregators'] == 1:
		# compile the aggregator
		termProcess = subprocess.Popen(['make', 'clean'], cwd=aggregatorFilePath, stdout=subprocess.PIPE)
		if termProcess.wait() != 0:
			raise Exception('something went wrong when doing "make clean"')

		termProcess = subprocess.Popen(['make'], cwd=aggregatorFilePath, stdout=subprocess.PIPE)
		if termProcess.wait() != 0:
			raise Exception('something went wrong when doing "make"')

		termProcess = subprocess.Popen(['chmod', '+x', 'aggregator'], cwd=aggregatorFilePath, stdout=subprocess.PIPE)
		if termProcess.wait() != 0:
			raise Exception('something went wrong when doing "chmod" on aggregator')


	# changing rights for scripts and executing the copyAll script
	termProcess = subprocess.Popen(['chmod', '+x', 'copyAll.sh', 'killAll.sh', 'runAll.sh'], cwd=experimentFilePath + '/' + experimentName, stdout=subprocess.PIPE)
	if termProcess.wait() != 0:
		raise Exception('something went wrong when doing "chmod" on convenience scripts')

	termProcess = subprocess.Popen(['./copyAll.sh'], cwd=experimentFilePath + '/' + experimentName, stdout=subprocess.PIPE)
	if termProcess.wait() != 0:
		raise Exception('something went wrong when doing "copyAll"')


def pythonLoadMat(loadProfilePath):
	"""
	This funciton is used to load .mat files in python without using MATLAB

	Inputs
		loadProfilePath - path for the load profile file

	Outputs
		loadprofiles
	"""

	return sio.loadmat(loadProfilePath)


def pythonLoadCase(casePath):
	"""
	This funciton is used to load a MATPOWER case file without using MATLAB

	Inputs
		casePath - path for the MATPOWER case file

	Outputs
		matpowerCaseStruct - MATPOWER case struct
	"""

	# open the case file
	caseFile = open(casePath,'r')

	# parse the case file
	matpowerCaseStruct = {}
	while True:
		line = caseFile.readline()
		# print "line is -> ", line
		if not line:
			break
		elif line == '\n':
			continue
		else:
			splitLine = line.split()
			if splitLine[0] == 'function':
				matpowerCaseStruct['function'] = splitLine[3]
			elif splitLine[0] == 'mpc.version':
				matpowerCaseStruct['version'] = splitLine[2]
			elif splitLine[0] == 'mpc.baseMVA':
				matpowerCaseStruct['baseMVA'] = float(splitLine[2].strip(';'))
			elif splitLine[0] == 'mpc.bus':
				array = np.empty((0, 0))
				count = 0
				while True:
					newLine = caseFile.readline()
					if newLine.split()[0] == '];' or newLine.split()[0] == ']':
						matpowerCaseStruct['bus'] = np.reshape(array, [-1, numberCol]).astype(np.float)
						break
					elif count > 100000:
						raise Exception('not able to read the matpower case file format!')
					newLine = newLine.split(';', 1)[0] # remove comments if they are present
					newLine = newLine.split('%', 1)[0]  # remove comments if they are present
					array = np.append(array, newLine.split())
					numberCol = len(newLine.split())
					count += 1
			elif splitLine[0] == 'mpc.branch':
				array = np.empty((0, 0))
				count = 0
				while True:
					newLine = caseFile.readline()
					if newLine.split()[0] == '];' or newLine.split()[0] == ']':
						matpowerCaseStruct['branch'] = np.reshape(array, [-1, numberCol]).astype(np.float)
						break
					elif count > 100000:
						raise Exception('not able to read the matpower case file format!')
					newLine = newLine.split(';', 1)[0] # remove comments if they are present
					newLine = newLine.split('%', 1)[0]  # remove comments if they are present
					array = np.append(array, newLine.split())
					numberCol = len(newLine.split())
					count += 1
			elif splitLine[0] == 'mpc.gen':
				array = np.empty((0, 0))
				count = 0
				while True:
					newLine = caseFile.readline()
					if newLine.split()[0] == '];' or newLine.split()[0] == ']':
						matpowerCaseStruct['gen'] = np.reshape(array, [-1, numberCol]).astype(np.float)
						break
					elif count > 100000:
						raise Exception('not able to read the matpower case file format!')
					newLine = newLine.split(';', 1)[0] # remove comments if they are present
					newLine = newLine.split('%', 1)[0]  # remove comments if they are present
					array = np.append(array, newLine.split())
					numberCol = len(newLine.split())
					count += 1
			elif splitLine[0] == 'mpc.gencost':
				array = np.empty((0, 0))
				count = 0
				while True:
					newLine = caseFile.readline()
					if newLine.split()[0] == '];' or newLine.split()[0] == ']':
						matpowerCaseStruct['gencost'] = np.reshape(array, [-1, numberCol]).astype(np.float)
						break
					elif count > 100000:
						raise Exception('not able to read the matpower case file format!')
					newLine = newLine.split(';', 1)[0] # remove comments if they are present
					newLine = newLine.split('%', 1)[0]  # remove comments if they are present
					array = np.append(array, newLine.split())
					numberCol = len(newLine.split())
					count += 1
			elif splitLine[0] == 'mpc.region':
				array = np.empty((0, 0))
				count = 0
				while True:
					newLine = caseFile.readline()
					if newLine.split()[0] == '];' or newLine.split()[0] == ']':
						matpowerCaseStruct['region'] = np.reshape(array, [-1, numberCol]).astype(np.float)
						break
					elif count > 100000:
						raise Exception('not able to read the matpower case file format!')
					newLine = newLine.split(';', 1)[0] # remove comments if they are present
					newLine = newLine.split('%', 1)[0]  # remove comments if they are present
					array = np.append(array, newLine.split())
					numberCol = len(newLine.split())
					count += 1

	caseFile.close()
	return matpowerCaseStruct


def pythonSaveCase(casePath, matpowerCaseStruct):
	"""
	This funciton is used to save a MATPOWER case file without using MATLAB

	Inputs
		casePath - path where you want to save the modified MATPOWER case file
		matpowerCaseStruct - MATPOWER case struct

	Outputs
		None
	"""

	# open the case file
	caseFile = open(casePath,'w')

	# write out the case file
	caseFile.write('function mpc = {:s}\n'.format(matpowerCaseStruct['function']))
	caseFile.write('% This is -> {:s}\n\n'.format(matpowerCaseStruct['function']))
	caseFile.write('%% MATPOWER Case Format : Version {:s}\n'.format(matpowerCaseStruct['version']))
	caseFile.write('mpc.version = {:s}\n\n'.format(matpowerCaseStruct['version']))
	caseFile.write('%%-----  Power Flow Data  -----%%\n%% system MVA base\n')
	caseFile.write('mpc.baseMVA = {:g};\n\n'.format(matpowerCaseStruct['baseMVA']))
	caseFile.write('%% bus data\n%	bus_i	type	Pd	Qd	Gs	Bs	area	Vm	Va	baseKV	zone	Vmax	Vmin\nmpc.bus = [\n')
	for row in matpowerCaseStruct['bus']:
		for data in row:
			caseFile.write('\t{:g}'.format(data))
		caseFile.write(';\n')
	caseFile.write('];\n\n')
	caseFile.write('%% generator data\n%	bus	Pg	Qg	Qmax	Qmin	Vg	mBase	status	Pmax	Pmin	Pc1	Pc2	Qc1min	Qc1max	Qc2min	Qc2max	ramp_agc	ramp_10	ramp_30	ramp_q	apf\nmpc.gen = [\n')
	for row in matpowerCaseStruct['gen']:
		for data in row:
			caseFile.write('\t{:g}'.format(data))
		caseFile.write(';\n')
	caseFile.write('];\n\n')
	caseFile.write('%% branch data\n%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status	angmin	angmax\nmpc.branch = [\n')
	for row in matpowerCaseStruct['branch']:
		for data in row:
			caseFile.write('\t{:g}'.format(data))
		caseFile.write(';\n')
	caseFile.write('];\n\n')
	caseFile.write('%%-----  OPF Data  -----%%\n%% generator cost data\n%	1	startup	shutdown	n	x1	y1	...	xn	yn\n%	2	startup	shutdown	n	c(n-1)	...	c0\nmpc.gencost = [\n')
	for row in matpowerCaseStruct['gencost']:
		for data in row:
			caseFile.write('\t{:g}'.format(data))
		caseFile.write(';\n')
	caseFile.write('];\n\n')

	if 'region' in matpowerCaseStruct:
		caseFile.write('%% region data\n%	bus region\nmpc.region = [\n')
		for row in matpowerCaseStruct['region']:
			for data in row:
				caseFile.write('\t{:g}'.format(data))
			caseFile.write(';\n')
		caseFile.write('];\n\n')

	caseFile.close()


if __name__ == '__main__':
	pass

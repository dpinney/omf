# break out of code on keyboard interrupt -------------------------------------

import os, signal
def signalHandler(signal, frame):
    os._exit(1)

signal.signal(signal.SIGINT, signalHandler)

# imports ---------------------------------------------------------------------

from glob import glob
from omf import feeder
from scipy.stats import norm
from shutil import copy2, rmtree
from omf.solvers import gridlabd
from omf import omfDir, loadModeling

import time, pathlib, random, csv

# constants -------------------------------------------------------------------

# define simulation params
NUM_INSTACES_OF_EACH_MODEL = 2

# set random seed
SEED = 42;
random.seed(SEED)

# define simulation time params
SIM_START_TIME = '2012-01-01 00:00:00'
SIM_STOP_TIME = '2013-01-01 00:00:00'
TIMEZONE = 'EST5'
TIMESTEP = 60*15

# define simulation file and path params
# define paths relative to this python scripts directory
WORKING_DIR = str( pathlib.Path(__file__).parent.absolute() ) + '/../workingDir/'
MODEL_FILE = 'in_singleHouseTemplate.glm'
SCHEDULE_FILE = 'in_superSchedules.glm'
CLIMATE_FILES = omfDir + '/data/Climate/*'
TEMPLATE_DIR = WORKING_DIR + '../templates/'
TEMP_FILENAME = WORKING_DIR+'temp.csv'

# define different house types
INCLUDE_EV_CHARGER = [False, True]
WATERHEATER_TYPES = ['GASHEAT','ELECTRIC']
COOLING_TYPES = ['HEAT_PUMP','ELECTRIC','NONE']
HEATING_TYPES = ['HEAT_PUMP','GAS','RESISTANCE','NONE']

# define random perturbation variables
HOUSE_SQFT_MEAN, HOUSE_SQFT_STDDEV = 2600,500
SCHEDULE_SKEW_MEAN, SCHEDULE_SKEW_STDDEV = 2000, 600
HEATING_SETPOINT_MEAN, HEATING_SETPOINT_STDDEV = 68, 4
COOLING_SETPOINT_MEAN, COOLING_SETPOINT_STDDEV = 72, 4
SQFT_AS_PERCENT_NOISE_STDDEV = 2
MIN_LOAD_MULTIPLIER, MAX_LOAD_MULTIPLIER = 0.5, 3

# define appliances and properties of interest
APPLIANCES_AND_PROPERTY = {
	'waterheater':['power'],
	'lights':['power'],
	'plugload':['power'],
	'appliance':['power'],
	'clotheswasher':['power'],
	'dishwasher':['power'],
	'dryer':['power'],
	'ev_charger':['power'],
	'freezer':['power'],
	'microwave':['power'],
	'range':['power'],
	'refrigerator':['power'],
	'responsive':['power'],
	'unresponsive':['power'],
	'meter':['measured_power','measured_reactive'],
	'house':['hvac_load','outdoor_temperature',\
		'heating_setpoint','cooling_setpoint',\
		'heating_demand','cooling_demand']
}

# define output file params
OUTPUT_FILENAME = WORKING_DIR + 'dataTest.csv'
lastDot = OUTPUT_FILENAME.rfind('.')
outputFileStartString = OUTPUT_FILENAME[:lastDot]
outputFileExtension = OUTPUT_FILENAME[lastDot:]

# define output structure params
SIMULATION_DIR_PREFIX = 'sim'
SIMULATION_FILE_PREFIX = '/out_*'
DELIMITER = ','


# functions -------------------------------------------------------------------

def getRandomGridlabModelFromTemplate(templatePath, \
	deleteEVCharger, waterHeaterType, coolingType, heatingType):

	# initialize variables
	toDelete = []
	toInsert = []

	# get gridlab model from template
	gridlabModel = feeder.parse(templatePath)

	# calculate random house sqft as gaussian and convert to percent of range
	# percent of range is used to scale unresponsive and responsive loads
	houseSqft = random.gauss(HOUSE_SQFT_MEAN, HOUSE_SQFT_STDDEV)
	normalizedHouseSqft = abs(houseSqft - HOUSE_SQFT_MEAN) / HOUSE_SQFT_STDDEV
	sqftAsPercent = norm.cdf(normalizedHouseSqft) * 100
	
	# set simulation params appropriately
	for modelItemKey,modelItem in gridlabModel.items():

		# skew all schedules by random gaussians
		if (modelItem.get('schedule_skew') != None):
			gridlabModel[modelItemKey]['schedule_skew'] = \
				random.gauss(SCHEDULE_SKEW_MEAN,SCHEDULE_SKEW_STDDEV)

		# set all recoder intervals based on user provided timestep
		if (modelItem.get('object') == 'recorder'):
			gridlabModel[modelItemKey]['interval'] = TIMESTEP

		# make the water heater electric or gas 
		elif (modelItem.get('object') == 'waterheater'):
			gridlabModel[modelItemKey]['heat_mode'] = waterHeaterType

		# set simulation climate randomly
		elif (modelItem.get('object') == 'climate'):
			# climateFile = glob(CLIMATE_FILES)[218]
			climateFile = random.choice(glob(CLIMATE_FILES))
			gridlabModel[modelItemKey]['tmyfile'] = climateFile

		# set time between samples given user provided timestep
		elif (modelItem.get('argument') != None) and \
		modelItem.get('argument').startswith('minimum_timestep='):
			gridlabModel[modelItemKey]['argument'] = \
				'minimum_timestep=' + str(TIMESTEP)

		# set clock given user provided start time, stop time, and timezone
		elif (modelItem.get('clock') != None):
			simStartTime = '\'' + SIM_START_TIME + '\''
			simStopTime = '\'' + SIM_STOP_TIME + '\''
			gridlabModel[modelItemKey]['starttime'] = simStartTime 				
			gridlabModel[modelItemKey]['stoptime'] = simStopTime
			gridlabModel[modelItemKey]['timezone'] = TIMEZONE

		# add random multipliers to house loads based on house sqft
		elif (modelItem.get('base_power') == 'responsive_loads') or \
			(modelItem.get('base_power') == 'unresponsive_loads'):

			# add some noise to sqftAsPercentage to ensure 
			# that the loads do not use the same multiplier
			sqftAsPercentWithNoise = sqftAsPercent + \
				random.gauss(0, SQFT_AS_PERCENT_NOISE_STDDEV)
			if sqftAsPercentWithNoise < 0:
				sqftAsPercentWithNoise = 0
			elif sqftAsPercentWithNoise > 100:
				sqftAsPercentWithNoise = 100

			# scale loads
			multiplierRange = MAX_LOAD_MULTIPLIER-MIN_LOAD_MULTIPLIER
			multiplier = (sqftAsPercentWithNoise/100)*multiplierRange
			multiplier = MIN_LOAD_MULTIPLIER + multiplier
			gridlabModel[modelItemKey]['base_power'] += '*' + str(multiplier)

		# remove the ev charger from house some of the time
		elif (modelItem.get('object') == 'evcharger_det'):

			# create recorder to save ev charger data
			evRecorder = {
				'object': 'recorder',
				'interval': TIMESTEP,
				'property': 'power.real',
				'line_units': 'NONE',
				'file': 'out_ev_charger.csv',
				'parent': 'ev_house0'
			}

			if deleteEVCharger:
				# delete charger and point recorder to
				# an empty meter that just outputs zeros
				toDelete.append(modelItemKey)
				evRecorder['parent'] = 'zero_meter'		
				evRecorder['property'] = 'measured_power.real'
		
			# add recorder to insert queue
			toInsert.append(evRecorder)

		# set house params based on random house and 
		# randomize heating and cooling setpoints, and
		# heating and cooling type
		elif (modelItem.get('object') == 'house'):
			
			# set params of template house based on random house
			house = loadModeling.get_random_new_house()
			house['floor_area'] = houseSqft
			for houseKey, houseVal in house.items():
				if (houseKey != 'name') and (houseKey != 'parent'):
					gridlabModel[modelItemKey][houseKey] = houseVal

			# use user provided gaussian to set 
			# house heating and cooling setpoints
			heatingSetpoint, coolingSetpoint = 0,0
			while (heatingSetpoint >= coolingSetpoint):
				heatingSetpoint = random.gauss( HEATING_SETPOINT_MEAN, 
					HEATING_SETPOINT_STDDEV )
				coolingSetpoint = random.gauss( COOLING_SETPOINT_MEAN, 
					COOLING_SETPOINT_STDDEV )
			gridlabModel[modelItemKey]['heating_setpoint'] = heatingSetpoint
			gridlabModel[modelItemKey]['cooling_setpoint'] = coolingSetpoint

			# set house heating and cooling type 
			gridlabModel[modelItemKey]['heating_system_type'] = heatingType
			gridlabModel[modelItemKey]['cooling_system_type'] = coolingType

	# insert and delete the appropriate items
	for item in toInsert:
		feeder.insert( gridlabModel, item)
	for modelItemKey in toDelete:
		del gridlabModel[modelItemKey]

	# output model
	return gridlabModel

def generateSimulationOutputFile( outputFilename, simulationFiles, \
	deleteEVCharger, waterHeaterType, coolingType, heatingType):

	# initialize variables
	outputHeader = [ 'timestamp', 'EVChargerPresent', \
		'waterHeaterType', 'coolingType', 'heatingType' ]
	appliances = APPLIANCES_AND_PROPERTY.keys()
	
	# create an empty output file
	file = open(outputFilename,'w')
	file.close()

	# get a list of the similulation output files
	# sorting ensures files are always read in the same order
	simFiles = glob(simulationFiles)
	simFiles.sort()

	# loop through each simulation output file (appliance data)
	for filename in simFiles:	
		
		# if we care about the appliance, 
		# open its file and read the properties of interest
		appliance = filename[ (len(simulationFiles)-1):-4 ]
		if appliance in appliances:
			for propertyOfInterest in APPLIANCES_AND_PROPERTY[appliance]:

				# track appliance names for the cosidated output csv header   
				# make sure everything is in watts (meter in watts by 
				# default, everything else in kW by default) 
				
				applianceName = appliance
				powerMultiplier = 1000
				
				# rename meter properties and correct powerMultiplier
				if appliance == 'meter':			
					powerMultiplier = 1
					if propertyOfInterest == 'measured_power':
						applianceName = 'meterRealPower'
					elif propertyOfInterest == 'measured_reactive':
						applianceName = 'meterReactivePower'
				
				# rename house properties
				elif appliance == 'house':

					applianceName = propertyOfInterest
					if propertyOfInterest == 'hvac_load':
						applianceName = 'hvac'			
					elif (propertyOfInterest!='heating_demand') and \
						(propertyOfInterest!='cooling_demand'):
						# use correct multiplier for non-load properties
						powerMultiplier = 1

				# add appliance name to header ensuring correct ordering
				outputHeader.append(applianceName)
				outputHeader = ensureCorrectOrder( \
					outputHeader, appliance, propertyOfInterest )

				# copy actual data to file ------------------------------------

				# open preexisting consolidated output file and read header
				with open(outputFilename,'r') as outputFile:
					outputFile.readline()
					
					# open temporary output file and write header
					with open(TEMP_FILENAME,'w') as tempFile:	
						tempFile.write(DELIMITER.join(outputHeader)+'\n')
						
						# read from current appliance file (simulation output)
						with open( filename ,'r' ) as inputFile:
							applianceReader = csv.reader(inputFile, \
							delimiter=DELIMITER)
							
							# loop through header in current appliance file
							# find the index of the property of interest
							appliancePowerIndex = None
							for inputRow in applianceReader:
								if '# timestamp' in inputRow:
									for index, propertyName in \
										enumerate(inputRow):
										if propertyOfInterest in propertyName:
											appliancePowerIndex = index;
											break
									break

							# loop through the current appliance file and 
							# append data to prexisting data from other
							# appliances
							for inputRow in applianceReader:

								# get relevant data
								timestamp = inputRow[0]
								timestamp = timestamp[:19]
								appliancePower = powerMultiplier * \
									float(inputRow[appliancePowerIndex])

								# if the preexisting output file is empty, 
								outputRow = outputFile.readline()
								if outputRow == '':
			
									# add the timestamp
									outputRow = [ timestamp, \
										str(deleteEVCharger), \
										waterHeaterType, \
										coolingType, \
										heatingType ]
								
								else:
					
									# get data from preexisting file 
									outputRow = outputRow.replace('\n','')
									outputRow = outputRow.split(DELIMITER)
									
								# append cuurent appliance data and make sure 
								# its in the correct order			
								outputRow.append(str(appliancePower))
								outputRow = ensureCorrectOrder( \
									outputRow, appliance, propertyOfInterest )
								
								# write data to temp file
								toWrite = DELIMITER.join(outputRow)
								tempFile.write(toWrite+'\n')
				
				# remove prexisting file and replace with the temp file
				# to which we just copied prexisting data and appended new data
				os.remove(outputFilename)
				os.rename(TEMP_FILENAME,outputFilename)

# helper functions ------------------------------------------------------------

def ensureCorrectOrder(dataArray, appliance, propertyOfInterest):
	
	# make sure that the 
	# meter properties are at the front followed by 
	# the temprature properties (model inputs at the front, 
	# appliance loads/model outputs at the end)
	if appliance == 'meter':
		if propertyOfInterest == 'measured_power':
			dataArray = swap(dataArray,5,-1)
		elif propertyOfInterest == 'measured_reactive':
			dataArray = swap(dataArray,6,-1)
	elif appliance == 'house':
		if propertyOfInterest == 'outdoor_temperature':
			dataArray = swap(dataArray,7,-1)
		elif propertyOfInterest == 'heating_setpoint':
			dataArray = swap(dataArray,8,-1)
		elif propertyOfInterest == 'cooling_setpoint':
			dataArray = swap(dataArray,9,-1)

	return dataArray

def swap( dataArray, index1, index2 ):

	if (index1<len(dataArray)) and (index2<len(dataArray)):
		temp = dataArray[index1]
		dataArray[index1] = dataArray[index2]
		dataArray[index2] = temp

	return dataArray

# main ------------------------------------------------------------------------

simNum = 0
numSims = NUM_INSTACES_OF_EACH_MODEL * len(INCLUDE_EV_CHARGER) * \
	len(WATERHEATER_TYPES) * len(HEATING_TYPES) * len(COOLING_TYPES)

for instanceNum in range(NUM_INSTACES_OF_EACH_MODEL):
	for deleteEVCharger in INCLUDE_EV_CHARGER:
		for waterHeaterType in WATERHEATER_TYPES:
			for coolingType in COOLING_TYPES:
				for heatingType in HEATING_TYPES:

					# print(instanceNum, deleteEVCharger, \
					# 	waterHeaterType, coolingType, heatingType)

					# if first simulation, delete everything
					# otherwise retain directories
					files = glob(WORKING_DIR+'/*')
					for file in files:
						try:
							os.remove(file)
						except IsADirectoryError:
							if simNum == 0:
								rmtree(file)

					# copy model and its schedule into the working directory
					copy2(TEMPLATE_DIR+MODEL_FILE,WORKING_DIR)
					copy2(TEMPLATE_DIR+SCHEDULE_FILE,WORKING_DIR)

					# get gridlab model from template
					gridlabModel = getRandomGridlabModelFromTemplate( \
						WORKING_DIR+MODEL_FILE, deleteEVCharger, \
						waterHeaterType, coolingType, heatingType)

					# run gridlabd
					start = time.time()
					gridlabd.runInFilesystem( gridlabModel, 
						workDir=WORKING_DIR, keepFiles=True )
					end = time.time()

					# move all csv files into a new folder,
					# delete all files, retain directories
					newFolder = WORKING_DIR+SIMULATION_DIR_PREFIX+str(simNum)
					os.mkdir(newFolder)
					files = glob(WORKING_DIR+'*')
					for file in files:
						if file[-3:] == 'csv':
							copy2(file,newFolder)
						try:
							os.remove(file)
						except IsADirectoryError:
							continue

					# print time taken by the run
					simNum += 1
					print('simulation',simNum,'/',numSims,
						'completed in',(end - start),'secs')

# concatenate individual appliance files into a signle house file per sim -----

simNum = 0
for instanceNum in range(NUM_INSTACES_OF_EACH_MODEL):
	for deleteEVCharger in INCLUDE_EV_CHARGER:
		for waterHeaterType in WATERHEATER_TYPES:
			for coolingType in COOLING_TYPES:
				for heatingType in HEATING_TYPES:
				
					folder = WORKING_DIR+SIMULATION_DIR_PREFIX+str(simNum)
					# consolidate simulation outputs into a single file
					simulationFiles = folder+SIMULATION_FILE_PREFIX
					intermediaryOutputFilename = outputFileStartString + \
						str(simNum) + outputFileExtension
					generateSimulationOutputFile( \
						intermediaryOutputFilename, simulationFiles, \
						deleteEVCharger, waterHeaterType, \
						coolingType, heatingType )

					rmtree(folder)
					simNum += 1
					print('consolidated output for simulation', \
						simNum,'/',numSims)

# concatenate individual house files into the final output file ---------------

firstFile = True
filenames = glob(outputFileStartString + '*')
with open(OUTPUT_FILENAME, 'w') as outputFile:
	finalOutputWriter = csv.writer( outputFile, delimiter=DELIMITER )

	for filename in filenames:
		with open(filename,'r') as simOutputFile:
			simOutputReader = csv.reader( simOutputFile, delimiter=DELIMITER )

			header = next(simOutputReader)
			if firstFile:
				finalOutputWriter.writerow(header)
				firstFile = False
				
			for row in simOutputReader:
				finalOutputWriter.writerow(row)					
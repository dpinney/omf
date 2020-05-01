# imports ---------------------------------------------------------------------

import glob, csv, os

# constants -------------------------------------------------------------------

PATH_TO_SIMULATION_FILES = './NetZeroEnergyHouseSim/out_*'
OUTPUT_FILENAME = 'disaggData.csv'
TEMP_FILENAME = 'temp.csv'

APPLIANCES_AND_PROPERTY = {
	'waterheater':'power',
	'lights':'power',
	'plugload':'power',
	'appliance':'power',
	'clotheswasher':'power',
	'dishwasher':'power',
	'dryer':'power',
	'ev_charger':'power',
	'freezer':'power',
	'microwave':'power',
	'range':'power',
	'refrigerator':'power',
	'responsive':'power',
	'unresponsive':'power',
	'meter':'power',
	'house':'hvac_load'
}

DELIMITER = ','

# helper functions ------------------------------------------------------------

def swap( dataArray, index1, index2 ):
	temp = dataArray[index1]
	dataArray[index1] = dataArray[index2]
	dataArray[index2] = temp

# load simulation files and write their data to output file -------------------

outputHeader = ['timestamp', 'meter']
appliances = APPLIANCES_AND_PROPERTY.keys()
file = open(OUTPUT_FILENAME,'w')
file.close()

simulatedFiles = glob.glob(PATH_TO_SIMULATION_FILES)
for filename in simulatedFiles:	
	
	# if we care about the appliance, open its file
	appliance = filename[ (len(PATH_TO_SIMULATION_FILES)-1):-4 ]
	if appliance in appliances:
		with open( filename ,'r' ) as inputFile:
			applianceReader = csv.reader(inputFile, delimiter=DELIMITER)

			# track appliance names for csv header and multiplier to make sure
			# everything is in watts (meter in watts by default, 
			# everything else in kW by default) 
			powerMultiplier = 1
			if appliance != 'meter':
				powerMultiplier = 1000
				applianceName = appliance
				if appliance == 'house':
					applianceName = 'hvac'
				outputHeader.append(applianceName)
			print(applianceName)

			# loop through header and find 
			# the index of the property of interest
			propertyOfInterest = APPLIANCES_AND_PROPERTY[appliance]
			appliancePowerIndex = None
			for inputRow in applianceReader:
				if '# timestamp' in inputRow:
					for index, item in enumerate(inputRow):
						if propertyOfInterest in item:
							appliancePowerIndex = index;
							break
					break

			# open previous output and skip header
			with open(OUTPUT_FILENAME,'r') as outputFile:
				outputFile.readline()
				
				# open new output and write header
				with open(TEMP_FILENAME,'w') as tempFile:	
					tempFile.write(DELIMITER.join(outputHeader)+'\n')
				
					# loop through the rest of the file and 
					# save out relevant data
					for inputRow in applianceReader:

						# get relevant data
						timestamp = inputRow[0]
						timestamp = timestamp[:19]
						appliancePower = powerMultiplier * \
							float(inputRow[appliancePowerIndex])

						# if the previous output file is empty, 
						outputRow = outputFile.readline()
						if outputRow == '':
	
							# add the timestamp and power data
							toWrite = timestamp+DELIMITER+' '+str(appliancePower)
						
						else:
			
							# append just power data 
							outputRow = outputRow.replace('\n','')
							outputRow = outputRow.split(DELIMITER)
							outputRow.append(' '+str(appliancePower))
							# make sure meter data is 
							# the first column after timestamps			
							if appliance == 'meter':
								swap(outputRow,1,-1)
							toWrite = DELIMITER.join(outputRow)
							
						tempFile.write(toWrite+'\n')
		
		os.remove(OUTPUT_FILENAME)
		os.rename(TEMP_FILENAME,OUTPUT_FILENAME)
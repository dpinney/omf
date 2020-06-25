import csv, glob
import pandas as pd 

# user provided constants -----------------------------------------------------

FRACTION_DATA_TRAIN = 0.6
SAMPLE_RATE_SECS = 60
COL_NAMES = ['time','power','appliance']

INPUT_FILES_PATH = './NetZeroEnergyHouseSim/out_*'
OUTPUT_FILENAME_TRAIN = 'disaggTraining.csv'
OUTPUT_FILENAME_TEST = 'disaggTesting.csv'
OUTPUT_FILENAME_TRUTH = 'disaggTestingTruth.csv'
METER_FILENAME = './NetZeroEnergyHouseSim/out_meter.csv'
HOUSE_FILENAME = './NetZeroEnergyHouseSim/out_house.csv'
HVAC_FILENAME = './NetZeroEnergyHouseSim/out_hvac.csv'

APPLIANCES = ['waterheater', 'lights', 'plugload', 'appliance', 
	'clotheswasher', 'dishwasher', 'dryer', 'ev_charger', 'freezer', 
	'microwave', 'range', 'refrigerator', 'responsive', 'unresponsive', 
	'hvac']


# create hvac files -----------------------------------------------------------

with open( HVAC_FILENAME, 'w' ) as outputFileHvac:
	hvacWriter = csv.writer(outputFileHvac, delimiter=',')

	# look at file with meter data
	hvacPowerIndex = None
	with open( HOUSE_FILENAME ,'r' ) as houseFile:
		houseReader = csv.reader(houseFile, delimiter=',')

		#loop through header and find the power index locations
		for houseRow in houseReader:

			# copy files verbatim till you hit the line with column names
			if '# timestamp' not in houseRow:
				hvacWriter.writerow(houseRow)				

			# use col names to determine power indices and data row format
			else:

				for index, item in enumerate(houseRow):
					if 'hvac_load' in item:
						hvacPowerIndex = index;
						break

				hvacToWrite =[houseRow[0], 'hvac_power']
				hvacWriter.writerow(hvacToWrite)				
				break

		# loop through rest of  file (actual data) and copy it usinf the 
		# previously defined data format
		for houseRow in houseReader:
			hvacToWrite =[houseRow[0], houseRow[hvacPowerIndex]]
			hvacWriter.writerow(hvacToWrite)				

# create train file -----------------------------------------------------------

applianceFiles = glob.glob(INPUT_FILES_PATH)

with open( OUTPUT_FILENAME_TRAIN, 'w' ) as outputFileTrain:
	trainWriter = csv.writer(outputFileTrain, delimiter=',')

	with open( OUTPUT_FILENAME_TRUTH, 'w' ) as outputFileTruth:
		truthWriter = csv.writer(outputFileTruth, delimiter=',')

		# look at file with meter data
		sampleCount = 0
		meterPowerIndex = None
		with open( METER_FILENAME ,'r' ) as meterFile:
			meterReader = csv.reader(meterFile, delimiter=',')

			#loop through header and find the power index location
			for meterRow in meterReader:
				if '# timestamp' in meterRow:
					for index, item in enumerate(meterRow):
						if 'power' in item:
							meterPowerIndex = index;
							break
					break

			if meterPowerIndex == None:
				raise Exception('No power values in file: ' + METER_FILENAME)

			#loop through data and get a row count
			for meterRow in meterReader:
				timestamp = meterRow[0]
				timestamp = timestamp[:19]
				meterPower = float(meterRow[meterPowerIndex])
				toWrite = [timestamp,meterPower,'meter']
				trainWriter.writerow(toWrite)
				sampleCount = sampleCount +1
			

		# go through each appliance file and write out training data
		numTrainSamples = round(sampleCount * FRACTION_DATA_TRAIN)
		for filename in applianceFiles:
			
			appliance = filename[ (len(INPUT_FILES_PATH)-1):-4 ]
			if appliance in APPLIANCES:

				with open( filename ,'r' ) as inputFile:
					applianceReader = csv.reader(inputFile, delimiter=',')

					with open( METER_FILENAME ,'r' ) as meterFile:
						meterReader = csv.reader(meterFile, delimiter=',')

						#loop through header
						appliancePowerIndex = None
						for applianceRow in applianceReader:
							if '# timestamp' in applianceRow:
								for index, item in enumerate(applianceRow):
									if 'power' in item:
										appliancePowerIndex = index;
										break
								break

						# read actual data
						rowNum = 0
						for applianceRow in applianceReader:
							
							timestamp = applianceRow[0]
							timestamp = timestamp[:19]

							appliancePower = 1000*float(applianceRow[appliancePowerIndex])
							toWrite = [timestamp,appliancePower,appliance]
							
							if appliancePower != 0:
								if rowNum < numTrainSamples:
									trainWriter.writerow(toWrite)
								else:
									truthWriter.writerow(toWrite)

							rowNum += 1

# -----------------------------------------------------------------------------
# load training and truth file that we just created and 
# sort it by time and add sample time info

def sortAndAddSampleInfo( filename, columns, sampleRate):

	data = pd.read_csv(filename, header=None, names=columns)
	data.sort_values(by=['time'],inplace=True, axis=0)

	toWrite = data.to_csv( index=False, header=None)
	toWrite = toWrite.split('\n')
	del(toWrite[-1])
	for index,row in enumerate(toWrite):
		toWrite[index] = toWrite[index].split(',')

	with open( filename, 'w' ) as outputFileTrain:
		writer = csv.writer(outputFileTrain, delimiter=',')
		writer.writerow([sampleRate])
		writer.writerows(toWrite)

sortAndAddSampleInfo( OUTPUT_FILENAME_TRAIN, COL_NAMES, SAMPLE_RATE_SECS)
sortAndAddSampleInfo( OUTPUT_FILENAME_TRUTH, COL_NAMES, SAMPLE_RATE_SECS)

# create test file ------------------------------------------------------------

with open( OUTPUT_FILENAME_TEST, 'w' ) as outputFileTest:
	testWriter = csv.writer(outputFileTest, delimiter=',')
	testWriter.writerow([SAMPLE_RATE_SECS])

	# look at file with meter data
	with open( METER_FILENAME ,'r' ) as meterFile:
		meterReader = csv.reader(meterFile, delimiter=',')

		#loop through header and find the power index location
		for meterRow in meterReader:
			if '# timestamp' in meterRow:
				break

		#loop through data and write to test file
		rowNum = 0
		for meterRow in meterReader:
			timestamp = meterRow[0]
			timestamp = timestamp[:19]
			if rowNum >= numTrainSamples:
				meterPower = float(meterRow[meterPowerIndex])
				toWrite =[timestamp,meterPower]
				testWriter.writerow(toWrite)
			rowNum += 1
			
import csv, glob
import pandas as pd 

# user provided constants -----------------------------------------------------

FRACTION_DATA_TRAIN = 0.6
SAMPLE_RATE_SECS = 60
TRAIN_COL_NAMES = ['time','power','appliance']

INPUT_FILES_PATH = './NetZeroEnergyHouseSim/out_*'
METER_FILENAME = './NetZeroEnergyHouseSim/out_meter.csv'
OUTPUT_FILENAME_TRAIN = 'disaggTraining.csv'
OUTPUT_FILENAME_TEST = 'disaggTesting.csv'

APPLIANCES = ['waterheater', 'lights', 'plugload', 'appliance', 
	'clotheswasher', 'dishwasher', 'dryer', 'ev_charger', 'freezer', 
	'microwave', 'range', 'refrigerator', 'responsive', 'unresponsive']


# create train file -----------------------------------------------------------

applianceFiles = glob.glob(INPUT_FILES_PATH)

with open( OUTPUT_FILENAME_TRAIN, 'w' ) as outputFileTrain:
	trainWriter = csv.writer(outputFileTrain, delimiter=',')

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

		#loop through data and get a row count
		for meterRow in meterReader:
			sampleCount = sampleCount +1
		
		if meterPowerIndex == None:
			raise Exception('No power values in file: ' + METER_FILENAME)

	# go through each appliance file and write ou training data
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
						meterRow = meterReader.next()
						if '# timestamp' in applianceRow:
							for index, item in enumerate(applianceRow):
								if 'power' in item:
									appliancePowerIndex = index;
									break
							break

					# read actual data
					rowNum = 0
					for applianceRow in applianceReader:
						
						meterRow = meterReader.next()
						timestamp = applianceRow[0]
						timestamp = timestamp[:19]

						appliancePower = \
							float(applianceRow[appliancePowerIndex])*1000
						if (appliancePower != 0) and (rowNum < numTrainSamples):
							meterPower = float(meterRow[meterPowerIndex])*1000
							toWrite =[timestamp,meterPower,appliance]
							trainWriter.writerow(toWrite)
						rowNum += 1

# load training file that we just created and 
# sort it by time and add sample time info
data = pd.read_csv(OUTPUT_FILENAME_TRAIN, header=None, names=TRAIN_COL_NAMES)
data.sort_values(by=['time'],inplace=True, axis=0)
toWrite = data.to_csv( index=False, header=None)
toWrite = toWrite.split('\n')
del(toWrite[-1])
for index,row in enumerate(toWrite):
	toWrite[index] = toWrite[index].split(',')

with open( OUTPUT_FILENAME_TRAIN, 'w' ) as outputFileTrain:
	trainWriter = csv.writer(outputFileTrain, delimiter=',')
	trainWriter.writerow([SAMPLE_RATE_SECS])
	trainWriter.writerows(toWrite)

print('DONE')

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
				meterPower = float(meterRow[meterPowerIndex])*1000
				toWrite =[timestamp,meterPower]
				testWriter.writerow(toWrite)
			rowNum += 1
			
# imports ---------------------------------------------------------------------

import pathlib, csv

# constants -------------------------------------------------------------------

# define input file params
DATA_DIR = str( pathlib.Path(__file__).parent.absolute() ) + \
	'/../data/48Types10HousesPerType'
INPUT_FILENAME_START = DATA_DIR + '/dataTest'
FILE_EXT = '.csv'

# define output file params
OUTPUT_FILENAME = DATA_DIR + 'dataSubset.csv'
DELIMITER = ','

# define file structure params
NUM_HOUSE_TYPES = 48
NUM_INSTANCES = 4

# concatenate individual house files into a final output file ---------------

numDesiredFiles = NUM_HOUSE_TYPES*NUM_INSTANCES

with open(OUTPUT_FILENAME, 'w') as outputFile:
	outputWriter = csv.writer( outputFile, delimiter=DELIMITER )

	for fileNum in range(numDesiredFiles):
		
		filename = INPUT_FILENAME_START + str(fileNum) + FILE_EXT
		# print(filename)

		with open(filename,'r') as inputFile:
			inputReader = csv.reader( inputFile, delimiter=DELIMITER )

			header = next(inputReader)
			if fileNum==0:
				outputWriter.writerow(header)
				
			for row in inputReader:
				outputWriter.writerow(row)	

		print('consolidated output for simulation', \
				fileNum+1,'/',numDesiredFiles)

		
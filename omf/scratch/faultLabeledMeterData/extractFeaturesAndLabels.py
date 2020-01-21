import csv

with open( 'extractedData.csv', 'w' ) as outputFile:
	writer = csv.writer(outputFile, delimiter=',')
	with open( 'faultyData.csv','r' ) as faultyMeterFile:
		readerFaulty = csv.reader(faultyMeterFile, delimiter=',')
		with open( 'faultFreeData.csv','r' ) as faultFreeMeterFile:
			readerFaultFree = csv.reader(faultFreeMeterFile, delimiter=',')

			#loop past header
			next(readerFaulty)
			next(readerFaultFree)

			# read acctual data
			for reader in [readerFaulty, readerFaultFree]:
				for row in reader:
					toWrite = []
					for index,data in enumerate(row):
						# ignore the timestamps and meterId, write the label as is 
						# otherwise wirte the float
						if index == (len(row)-2):
							toWrite.append(data)
						elif (index > 0) and (index < (len(row)-1)):
							toWrite.append(float(data))
					writer.writerow(toWrite)


# ----------------------------------------------------------------------------------
print('DONE')
# ----------------------------------------------------------------------------------
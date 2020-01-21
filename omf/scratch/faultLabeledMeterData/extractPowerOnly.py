import csv

with open( 'data.csv','r' ) as meterFile:
	reader = csv.reader(meterFile, delimiter=',')
	with open( 'powerOnly.csv', 'w' ) as outputFile:
		writer = csv.writer(outputFile, delimiter=',')

		#loop past header
		next(reader)

		# read acctual data
		for row in reader:
			power = float(row[1])
			writer.writerow([power])

# ----------------------------------------------------------------------------------
print('DONE')
# ----------------------------------------------------------------------------------
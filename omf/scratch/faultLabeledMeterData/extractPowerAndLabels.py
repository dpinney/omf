import csv

with open( 'data.csv','r' ) as meterFile:
	reader = csv.reader(meterFile, delimiter=',')
	with open( 'powerAndLabels.csv', 'w' ) as outputFile:
		writer = csv.writer(outputFile, delimiter=',')

		#loop past header
		next(reader)

		# read acctual data
		for row in reader:
			power = float(row[1])
			label = row[2]
			writer.writerow([power, label])

# ----------------------------------------------------------------------------------
print('DONE')
# ----------------------------------------------------------------------------------
import csv

with open('data.csv','w') as dataFile:
	writer = csv.writer(dataFile,delimiter=',')

	with open('normalTheftAndMalfunction-3month.csv','r') as largeFile:
		reader = csv.reader(largeFile,delimiter=',')
	
		for row in reader:
			writer.writerow(row)
			# if ('meterID' in row) or ('2000-01-0' in row[1]) :
			# 	writer.writerow(row)
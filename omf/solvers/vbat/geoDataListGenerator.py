import json
import os.path
import csv

filename = 'geodata.csv'

text = []
with open (filename) as f:
	rows = list(csv.reader(f, delimiter=','))
	for column in rows:
		text.append( '<option value="' + "'" + column[2] + "'" + '">' + column[1] + ' - ' +  column[2].title() + '</option>' )

with open('text.txt', 'w') as outfile:
	for line in text:
		outfile.write('%s\n' % line)
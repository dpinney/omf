import csv
import json
import os.path

filelist = os.listdir('C:\\Users\\simon\\Desktop\\NRECA\\alltmy3a')
print filelist
results = []
for filename in filelist:
	if filename[-3:] == 'CVS':
		with open('C:\\Users\\simon\\Desktop\\NRECA\\' + filename) as f:
			rows = list(csv.reader(f, delimiter=','))
			
			temp = []

			#print rows[0][2]
			state = rows[0][2]
			city = rows[0][1]
			for row in rows[2:]: #32 is the index of bulb temp
				temp.append(row[31])

				


			results.append({
				'State':state,
				'City':city,
				'Temperatures':temp})


with open('data.json', 'w') as outfile:
        json.dump(results, outfile,sort_keys=True, indent=4)
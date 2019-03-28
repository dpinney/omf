import json, omf, csv

# Visualize the circuit.
omf.distNetViz.viz('trip37.glm')

# Read it in.
tree = omf.feeder.parse('trip37.glm')

# Modify all line lengths.
for key in tree:
	if tree[key].get('object','') == 'overhead_line':
		print tree[key]['name']
		tree[key]['length'] = '5'

# Write new output.
with open('trip37tinyLines.glm','w') as outFile:
	myStr = omf.feeder.sortedWrite(tree)
	outFile.write(myStr)

# Run the .glm.
#TODO: insert code here.

# Pulling out a mean voltage.
lines = open('trip37 xVoltDump.csv').readlines()
data = list(csv.DictReader(lines[1:]))
accum = 0
for row in data:
	phaseAvolt = complex(float(row['voltA_real']), float(row['voltA_imag']))
	accum = accum + abs(phaseAvolt)
print 'MEAN!', accum / len(data)
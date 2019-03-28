import json, omf

# Visualize the circuit.
# omf.distNetViz.viz('trip37.glm')

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
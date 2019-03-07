import json, omf

# Loading a circuit.
with open('trip37.omd','r') as omdFile:
	omd = json.load(omdFile)

print 'Keys in the OMD', omd.keys()

# Visualize the circuit.
omf.distNetViz.viz('trip37.omd')

# Write out a .glm
glm = omf.feeder.sortedWrite(omd['tree'])
with open('trip37.glm','w') as glmFile:
	glmFile.write(glm)
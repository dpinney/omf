import omf
import json

thisWorkDir = omf.omfDir + '/scratch/anonymization/'

filePath = '/blah/blah/olin barre.omd'

# Get the circuit in to memory.

# Randomize names.

# Randomize locations.

# Write resulting .omd to disk.

# Create 2 voltage drop models, copy correct .omd in to those directories.

# Run voltage drop on original olin barre.

# Run voltage drop on anonymized olin barre.
# omf.models.voltageDrop.new(thisWorkDir, inputData)

# Delete confidential data in here: .omd and .glm files in original voltage drop folder, .omd in anonyized voltage drop folder.
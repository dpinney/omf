import json, omf

# Visualize the circuit.
omf.distNetViz.viz('trip37.glm')

# Read it in.
tree = omf.feeder.parse('trip37.glm')
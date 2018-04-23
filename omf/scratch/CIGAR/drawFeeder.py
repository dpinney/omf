import omf
import sys
from matplotlib import pyplot as plt

FNAME = 'R2-12.47-3.glm'

# help(omf.feeder.parse)

feed = omf.feeder.parse(FNAME)

# All object types.
x = set()
for obj in feed.values():
	if 'object' in obj:
		x.add(obj['object'])
print x

# Draw it.
# omf.feeder.latLonNxGraph(omf.feeder.treeToNxGraph(feed), labels=False, neatoLayout=True, showPlot=False)
# plt.savefig('blah.png')

# Viz it.
sys.path.append('../distNetViz/')
import distNetViz
distNetViz.viz(FNAME, forceLayout=True, outputPath=None)
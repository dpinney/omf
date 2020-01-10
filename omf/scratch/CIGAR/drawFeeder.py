from omf.models import voltageDrop
from matplotlib import pyplot as plt

FNAME = 'test_base_R4-25.00-1.glm_CLEAN.glm'
# FNAME = 'test_Exercise_4_2_1.glm'
# FNAME = 'test_ieee37node.glm'
# FNAME = 'test_ieee123nodeBetter.glm'
# FNAME = 'test_large-R5-35.00-1.glm_CLEAN.glm'
# FNAME = 'test_medium-R4-12.47-1.glm_CLEAN.glm'
# FNAME = 'test_smsSingle.glm'

# help(omf.feeder.parse)
# feed = omf.feeder.parse(FNAME)

# All object types.
# x = set()
# for obj in feed.values():
# 	if 'object' in obj:
# 		x.add(obj['object'])
#print x

# Draw it.
# omf.feeder.latLonNxGraph(omf.feeder.treeToNxGraph(feed), labels=False, neatoLayout=True, showPlot=False)
# plt.savefig('blah.png')

# Viz it interactively.
# omf.distNetViz.viz(FNAME, forceLayout=True, outputPath=None)

# Test code for parsing/modifying feeders.
# tree = omf.feeder.parse('smsSingle.glm')
# tree[35]['name'] = 'OH NO CHANGED'

# chart = omf.models.voltageDrop.drawPlot(FNAME, neatoLayout=True, edgeCol=True, nodeLabs="VoltageImbalance", customColormap=True, perUnitScale=False)
chart = voltageDrop.drawPlot(FNAME, neatoLayout=True, edgeCol=True, nodeLabs="Voltage", edgeLabs="Current", rezSqIn=600)
chart.savefig("./VOLTOUT.png")

#testAllVarCombos()
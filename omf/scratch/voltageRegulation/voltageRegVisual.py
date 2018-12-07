import omf
import sys
from matplotlib import pyplot as plt

print sys.path
import voltageDropVoltageViz

# FNAME='/Users/tuomastalvitie/omf/omf/scratch/voltageRegulation/outGLM.glm'
FNAME = '/Users/tuomastalvitie/Desktop/UCS_Egan_Housed_Solar.omd'

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
chart = voltageDropVoltageViz.drawPlot(FNAME, neatoLayout=True, edgeCol=True, nodeLabs="Voltage", edgeLabs="Current", perUnitScale=False, rezSqIn=600)
chart.savefig("./VOLTOUT.png")

#testAllVarCombos()

#put below in voltagedrop.py
#gridlabOut = omf.solvers.gridlabd_gridballast.runInFilesystem(tree, attachments=attachments, workDir=workDir)

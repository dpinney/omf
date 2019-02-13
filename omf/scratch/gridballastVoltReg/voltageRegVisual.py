import omf
import sys
import os
from os.path import join as pJoin

from matplotlib import pyplot as plt
from voltageDropVoltageViz import drawPlot

# volRegDir = os.path.dirname(os.path.dirname(__file__))
# FNAME = pJoin(volRegDir, 'UCS_Egan_Housed_Solar.omd')

# FNAME='/Users/tuomastalvitie/omf/omf/scratch/voltageRegulation/outGLMtest.glm'
FNAME = './outGLM.glm'

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

def voltRegViz(FNAME):
# chart = omf.models.voltageDrop.drawPlot(FNAME, neatoLayout=True, edgeCol=True, nodeLabs="VoltageImbalance", customColormap=True, perUnitScale=False)
	chart = drawPlot(FNAME, neatoLayout=True, edgeCol="PercentOfRating", nodeCol="perUnitVoltage", nodeLabs="Voltage", edgeLabs="Name", rezSqIn=400)
	chart.savefig("./VOLTOUT.png")

#testAllVarCombos()

#put below in voltagedrop.py
#gridlabOut = omf.solvers.gridlabd_gridballast.runInFilesystem(tree, attachments=attachments, workDir=workDir)


if __name__ == '__main__':
	voltRegViz(FNAME)
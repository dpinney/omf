import omf

milTree = omf.feeder.parse("GridLabD Conversion/Emily.glm", filePath=True)
omfTree = omf.milToGridlab.convert(open("Emily.std").read(), open("Emily.seq").read())

print tree

# Takes 10 minutes, no output:
# omf.feeder.latLonNxGraph(omf.feeder.treeToNxGraph(tree), labels=False, neatoLayout=True)
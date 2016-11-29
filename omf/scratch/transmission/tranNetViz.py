'''
Load an OMF network in to the new viewer.
'''

import tempfile, shutil, os, fileinput, json, networkx as nx, platform, webbrowser, sys
import network as network
from os.path import join as pJoin

def main():
	SOURCE_DIR = './'

	# Handle the command line arguments.
	argCount = len(sys.argv)
	errorMessage = 'Incorrect inputs. Usage: tranNetViz -f <Path_to_network.omt>'
	if argCount == 1:
		print 'Running tests. Normal usage: tranNetViz -f <Path_to_network.omt>'
		NETWORK_PATH = pJoin(os.getcwd(),'outData','case30.omt')
	elif argCount == 2:
		NETWORK_PATH = sys.argv[1]
	elif argCount == 3:
		if sys.argv[1] != '-f':
			print errorMessage
		NETWORK_PATH = sys.argv[2]
	elif argCount > 3:
		print errorMessage

	# Load in the network.
	with open(NETWORK_PATH,'r') as netFile:
		if NETWORK_PATH.endswith('.omt'):
			thisNet = json.load(netFile)

	# Force layout of network since it came from matpower which has no lat/lon information.
	print "Force laying out the graph..."
	# Use graphviz to lay out the graph.
	inGraph = network.netToNxGraph(thisNet)
	# HACK: work on a new graph without attributes because graphViz tries to read attrs.
	cleanG = nx.Graph(inGraph.edges())
	# HACK2: might miss nodes without edges without the following.
	cleanG.add_nodes_from(inGraph)
	pos = nx.nx_agraph.graphviz_layout(cleanG, prog='neato')
	# # Charting the feeder in matplotlib:
	# feeder.latLonNxGraph(inGraph, labels=False, neatoLayout=True, showPlot=True)
	# Insert the latlons.
	for compType in thisNet:
		if compType in ['bus']:
			comp = thisNet[compType]
			for compVal in comp:
				for idnum,item in compVal.iteritems():
					obName = item.get('bus_i')
					thisPos = pos.get(obName, None)
					if thisPos != None:
						print "path: %s %s"%(compType,idnum)
						thisNet[compType][int(float(idnum))-1][idnum]['longitude'] = thisPos[0]
						thisNet[compType][int(float(idnum))-1][idnum]['latitude'] = thisPos[1]

	# Set up temp directory and copy the feeder and viewer in to it.
	tempDir = tempfile.mkdtemp()
	shutil.copy(SOURCE_DIR + '/tranNetViz.html', tempDir + '/viewer.html')

	# Print the lat/lon.
	# import pprint as pprint
	# pprint.pprint(thisNet)

	# Grab the library we need.
	with open(pJoin(SOURCE_DIR,'inData','svg-pan-zoom.js'),'r') as pzFile:
		pzData = pzFile.read()

	# Rewrite the load lines in viewer.html
	# Note: you can't juse open the file in r+ mode because, based on the way the file is mapped to memory, you can only overwrite a line with another of exactly the same length.
	for line in fileinput.input(tempDir + '/viewer.html', inplace=1):
		if line.lstrip().startswith("<script id='feederLoadScript''>"):
			print "" # Remove the existing load.
		elif line.lstrip().startswith("<script id='feederInsert'>"):
			print "<script id='feederInsert'>\ntestFeeder=" + json.dumps(thisNet, indent=4) # load up the new feeder.
		elif line.lstrip().startswith("<script id='panZoomInsert'>"):
			print "<script id='panZoomInsert'>\n" + pzData # load up the new feeder.
		else:
			print line.rstrip()

	webbrowser.open_new("file://" + tempDir + '/viewer.html')

if __name__ == '__main__':
	main()
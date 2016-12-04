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

	# Set up temp directory and copy the feeder and viewer in to it.
	tempDir = tempfile.mkdtemp()
	shutil.copy(SOURCE_DIR + '/tranNetViz.html', tempDir + '/viewer.html')

	# Grab the library we need.
	with open(pJoin(SOURCE_DIR,'inData','svg-pan-zoom.js'),'r') as pzFile:
		pzData = pzFile.read()

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
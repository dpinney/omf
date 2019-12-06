"""
Load an OMF feeder in to the new viewer.
"""

import tempfile, shutil, os, fileinput, json, networkx as nx, platform, omf.feeder as feeder, webbrowser, sys
import omf


def main():
	''' Handle the command line arguments for distNetViz.'''
	argCount = len(sys.argv)
	errorMessage = 'Incorrect inputs. Usage: distNetViz -f <Path_to_feeder.glm or .omd>'
	if argCount == 1:
		print 'Running tests. Normal usage: distNetViz -f <Path_to_feeder.glm or .omd>'
		FEEDER_PATH = omf.omfDir + '/static/publicFeeders/Simple Market System.omd'
		DO_FORCE_LAYOUT = True
	elif argCount == 2:
		print 'Beginning display of ' + sys.argv[1]
		DO_FORCE_LAYOUT = False
		FEEDER_PATH = sys.argv[1]
	elif argCount == 3:
		print 'Force laying out and displaying ' + sys.argv[2]
		if sys.argv[1] == '-f':
			DO_FORCE_LAYOUT = True
		else:
			print errorMessage
		FEEDER_PATH = sys.argv[2]
	elif argCount > 3:
		print errorMessage
	viz(FEEDER_PATH, forceLayout=DO_FORCE_LAYOUT, outputPath=None)


def insert_coordinates(tree):
	# type: (dict) -> None
	"""Insert additional latitude and longitude data into the dictionary."""
	print("Force laying out the graph...")
	# Use graphviz to lay out the graph.
	inGraph = feeder.treeToNxGraph(tree)
	# HACK: work on a new graph without attributes because graphViz tries to read attrs.
	cleanG = nx.Graph(inGraph.edges())
	# HACK2: might miss nodes without edges without the following.
	cleanG.add_nodes_from(inGraph)
	pos = nx.nx_agraph.graphviz_layout(cleanG, prog='neato')
	# # Charting the feeder in matplotlib:
	# feeder.latLonNxGraph(inGraph, labels=False, neatoLayout=True, showPlot=True)
	# Insert the latlons.
	for key in tree:
		obName = tree[key].get('name','')
		thisPos = pos.get(obName, None)
		if thisPos != None:
			tree[key]['longitude'] = thisPos[0]
			tree[key]['latitude'] = thisPos[1]


def contains_coordinates(tree):
	"""Return True if the dictionary contains latitude and longitude data, otherwise False."""
	for key in tree:
		for sub_key in ['latitude', 'longitude']:
			if sub_key in tree[key]:
				return True
	return False

def get_components():
	directory = os.path.join(omf.omfDir, "data/Component")
	components = {}
	for dirpath, dirnames, file_names in os.walk(directory):
		for name in file_names:
			if name.endswith(".json"):
				path = os.path.join(dirpath, name)
				with open(path) as f:
					components[name[0:-5]] = json.load(f) # Load the file as a regular object into the dictionary
	return json.dumps(components) # Turn the dictionary of objects into a string

def viz(pathToOmdOrGlm, forceLayout=False, outputPath=None, outputName='viewer.html', open_file=True):
	''' Vizualize a distribution system.'''
	# HACK: make sure we have our homebrew binaries available.
	os.environ['PATH'] += os.pathsep + '/usr/local/bin'
	# Load in the feeder.
	with open(pathToOmdOrGlm,'r') as feedFile:
		if pathToOmdOrGlm.endswith('.omd'):
			thisFeed = {'tree':json.load(feedFile)['tree']} # TODO: later bring back attachments.
		elif pathToOmdOrGlm.endswith('.glm'):
			thisFeed = {'tree':feeder.parse(pathToOmdOrGlm, filePath=True)}
		tree = thisFeed['tree']
	## Force layout of feeders with no lat/lon information so we can actually see what's there.
	if forceLayout:
		print('forceLayout was set to True, so force layout is applied regardless of coordinate detection.')
		insert_coordinates(tree)
	elif not contains_coordinates(tree):
		print('Warning: no lat/lon coordinates detected, so force layout required.')
		insert_coordinates(tree)
	# Set up temp directory and copy the feeder and viewer in to it.
	if outputPath is None:
		tempDir = tempfile.mkdtemp()
	else:
		tempDir = os.path.abspath(outputPath)
	#HACK: make sure we get the required files from the right place.
	# shutil.copy(omf.omfDir + '/templates/distNetViz.html', tempDir + '/' + outputName)
	# shutil.copy(omf.omfDir + '/static/svg-pan-zoom.js', tempDir + '/svg-pan-zoom.js')
	# Grab the library we need.
	with open(omf.omfDir + '/static/svg-pan-zoom.js','r') as pzFile:
		pzData = pzFile.read()
	with open(omf.omfDir + '/static/chroma.min.js','r') as chromaFile:
		chromaData = chromaFile.read()
	with open(omf.omfDir + '/static/papaparse.min.js','r') as papaFile:
		papaData = papaFile.read()
	with open(omf.omfDir + '/static/jquery.js', 'r') as jquery_file:
		jquery_data = jquery_file.read()
	with open(omf.omfDir + '/static/jquery-ui.min.js', 'r') as jquery_ui_file:
		jquery_ui_data = jquery_ui_file.read()
	with open(omf.omfDir + '/static/jquery-ui.min.css', 'r') as jquery_css_file:
		jquery_css_data = jquery_css_file.read()
	# TEMPLATE HACKING
	from jinja2 import Template
	templateCont = open(omf.omfDir + '/templates/distNetViz.html', 'r+').read()
	templateString = templateCont.encode('utf-8')
	template = Template(templateString)
	def id():
		return ""
	component_json = get_components()
	rend = template.render(thisFeederData=json.dumps(thisFeed), thisFeederName=pathToOmdOrGlm, thisFeederNum=1,
		thisModelName="Local Filesystem", thisOwner="NONE", components=component_json, jasmine=None, spec=None,
		publicFeeders=[], userFeeders=[], csrf_token=id, showFileMenu=True, currentUser=None
	)
	with open(tempDir + '/' + outputName, 'w') as outFile:
		outFile.write(rend)
	# Insert the panZoom library.
	# Note: you can't juse open the file in r+ mode because, based on the way the file is mapped to memory, you can only overwrite a line with another of exactly the same length.
	for line in fileinput.input(tempDir + '/' + outputName, inplace=1):
		if line.lstrip().startswith('<link rel="stylesheet" href="/static/jquery-ui.min.css">'):
			print ""
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/jquery.js"></script>'):
			print ""
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/jquery-ui.min.js"></script>'):
			print ""
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/svg-pan-zoom.js"></script>'):
			print ""
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/chroma.min.js"></script>'):
			print ""
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/papaparse.min.js"></script>'):
			print ""
		elif line.lstrip().startswith('<link rel="shortcut icon" href="/static/favicon.ico"/>'):
			print('<link rel="shortcut icon" href="data:image/x-icon;base64,AAABAAEAEBAQAAAAAAAoAQAAFgAAACgAAAAQAAAAIAAAAAEABAAAAAAAgAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAioqKAGlpaQDU1NQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIiIiIiIiIAAgACAAIAAgACAzIzMjMyMwIDAgMCAwIDAiIiIiIiIgMCAwEDAgMCAwIDMTMyMzIzAgMBAwIDAgMCIiIiIiIiAwIDAQMCAwIDAgMxMzIzMjMCAwEDAgMCAwIiIiIiIiIDAAMAAwADAAMAAzMzMzMzMwAAAAAAAAAAAABwAAd3cAAEABAABVVQAAAAUAAFVVAABAAQAAVVUAAAAFAABVVQAAQAEAAFVVAAAABQAA3d0AAMABAAD//wAA"/>')
		elif line.lstrip().startswith('<script id="panZoomInsert">'):
			print '<script id="panZoomInsert">\n' + pzData # load up the new feeder.
		elif line.lstrip().startswith('<script id="chromaInsert">'):
			print '<script id="chromaInsert">\n' + chromaData
		elif line.lstrip().startswith('<script id="papaParseInsert">'):
			print '<script id="papaParseInsert">\n' + papaData
		elif line.lstrip().startswith('<script id="jqueryInsert">'):
			print '<script id="jqueryInsert">\n' + jquery_data
		elif line.lstrip().startswith('<script id="jqueryUiInsert">'):
			print '<script id="jqueryUiInsert">\n' + jquery_ui_data
		elif line.lstrip().startswith('<style id="jqueryCssInsert">'):
			print '<style id="jqueryCssInsert">\n' + jquery_css_data
		else:
			print line.rstrip()
	# os.system('open -a "Google Chrome" ' + '"file://' + tempDir + '/' + outputName"')
	# webbrowser.open_new("file://" + tempDir + '/' + outputName)
	if open_file:
		open_browser(tempDir, outputName)

def open_browser(tempDir, outputName):
	webbrowser.open_new("file://" + tempDir + '/' + outputName)

if __name__ == '__main__':
	main()
	#viz('/Users/tuomastalvitie/OneDrive/NRECA Code/DEC Robinsonville Original.omd', forceLayout=False, outputPath=None)
	#viz('C:\Users\Tuomas\SkyDrive\NRECA Code\Utility Data\DEC Robinsonville Substation\DEC Robinsonville Original.omd', forceLayout=False, outputPath=None)
	# viz('/Users/dpinney/Desktop/LATERBASE/NRECA/GridBallast/DM1.3.1 Go-No-Go - Demonstration of GridBallast Performance in Simulation - FINISHED/Utility Data/DEC Robinsonville Substation/DEC Robinsonville Original.omd', forceLayout=False, outputPath=None)
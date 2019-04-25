''' Functions for manipulating electrical transmission network models. '''

import datetime, copy, os, re, warnings, networkx as nx, json, math, tempfile, shutil, fileinput, webbrowser
from os.path import join as pJoin
from matplotlib import pyplot as plt
import omf
# import matpower



def parse(inputStr, filePath=True):
	''' Parse a MAT into an omf.network json. This is so we can walk the json, change things in bulk, etc.
	Input can be a filepath or MAT string.
	'''
	matDict = _dictConversion(inputStr, filePath)
	return matDict

def write(inNet):
	''' Turn an omf.network json object into a MAT-formatted string. '''
	output = ''
	for key in inNet:
		output += _dictToString(inNet[key]) + '\n'
	return output

def layout(inNet):
	''' Add synthetic lat/lon data to a graph to give it a nice human-readable shape. '''
	nxG = netToNxGraph(inNet)
	inNet = latlonToNet(nxG, inNet)

def _dictConversion(inputStr, filePath=True):
	''' Turn a MAT file/string into a dictionary.

	E.g. turn a string like this:
	mpc.bus = [
	1	3	0	0	0	0	1	1	0	135	1	1.05	0.95;
	...
	]

	Into a Python dict like this:
	{"baseMVA":"100.0","mpcVersion":"2.0","bus":[{"1": {"bus_i": 1,"type": 3,"Pd": 0,"Qd": 0,"Gs": 0,"Bs": 0,"area": 1,"Vm": 1,"Va": 0,"baseKV": 135,"zone": 1,"Vmax": 1.05,"Vmin": 0.95}}],"gen":[],
	"branch":[]}
	'''
	# Wireframe for new network objects:
	newNetworkWireframe = {"baseMVA":"100.0","mpcVersion":"2.0","bus":{},"gen":{}, "branch":{}}
	if filePath:
		with open(inputStr,'r') as matFile:
			data = matFile.readlines()
	else:
		data = inputStr
	# Parse data.
	todo = None
	for i,line in enumerate(data):
		if todo!=None:
			# Parse lines.
			line = line.translate(None,'\r;\n')
			if "]" in line:
				todo = None
			if todo in ['bus','gen','bus','branch']:
				line = line.split('\t')
			else:
				line = line.split(' ')
			line = filter(lambda a: a!= '', line)
			if todo=="version":
				version = line[-1][1]
				if version<2:
					print "MATPOWER VERSION MUST BE 2: %s"%(version)
					break
				todo = None
			elif todo=="mva":
				mva = line[-1]
				newNetworkWireframe['baseMVA'] = str(mva)
				todo = None
			elif todo=="bus":
				maxKey = str(len(newNetworkWireframe['bus'])+1)
				bus = {"bus_i":line[0],"type":line[1],"Pd": line[2],"Qd": line[3],"Gs": line[4],"Bs": line[5],"area": line[6],"Vm": line[7],"Va": line[8],"baseKV": line[9],"zone": line[10],"Vmax": line[11],"Vmin": line[12]}
				newNetworkWireframe['bus'][maxKey] = bus
			elif todo=="gen":
				maxKey = str(len(newNetworkWireframe['gen'])+1)
				gen = {"bus": line[0],"Pg": line[1],"Qg": line[2],"Qmax": line[3],"Qmin": line[4],"Vg": line[5],"mBase": line[6],"status": line[7],"Pmax": line[8],"Pmin": line[9],"Pc1": line[10],"Pc2": line[11],"Qc1min": line[12],"Qc1max": line[13],"Qc2min": line[14],"Qc2max": line[15],"ramp_agc": line[16],"ramp_10": line[17],"ramp_30": line[18],"ramp_q": line[19],"apf": line[20]}
				newNetworkWireframe['gen'][maxKey] = gen
			elif todo=='branch':
				maxKey = str(len(newNetworkWireframe['branch'])+1)
				branch =  {"fbus":line[0],"tbus":line[1],"r": line[2],"x": line[3],"b": line[4],"rateA": line[5],"rateB": line[6],"rateC": line[7],"ratio": line[8],"angle": line[9],"status": line[10],"angmin": line[11],"angmax": line[12]}
				newNetworkWireframe['branch'][maxKey] = branch
		else:
			# Determine what type of data is coming up.
			if "matpower case format" in line.lower():
				todo = "version"
			elif "system mva base" in line.lower():
				todo = "mva"
			elif "mpc.bus = [" in line.lower():
				todo = "bus"
			elif "mpc.gen = [" in line.lower():
				todo = "gen"
			elif "mpc.branch = [" in line.lower():
				todo = "branch"
	return newNetworkWireframe

def _dictToString(inDict):
	''' Helper function: given a single dict representing a NETWORK, concatenate it into a string. '''
	return ''

def netToNxGraph(inNet):
	''' Convert network.omt to networkx graph. '''
	outGraph = nx.Graph()
	for compType in ['bus','gen','branch']:
		for idNum, item in inNet[compType].iteritems():
			if 'fbus' in item.keys():
				outGraph.add_edge(item['fbus'],item['tbus'],attr_dict={'type':'branch'})
			elif compType=='bus':
				if item.get('bus_i',0) in outGraph:
					# Edge already led to node's addition, so just set the attributes:
					outGraph.node[item['bus_i']]['type']='bus'
				else:
					outGraph.add_node(item['bus_i'])
			elif compType=='gen':
				pass
	return outGraph

def latlonToNet(inGraph, inNet):
	''' Add lat/lon information to network json. '''
	cleanG = nx.Graph(inGraph.edges())
	cleanG.add_nodes_from(inGraph)
	pos = nx.nx_agraph.graphviz_layout(cleanG, prog='neato')
	for idnum, item in inNet['bus'].iteritems():
		obName = item.get('bus_i')
		thisPos = pos.get(obName, None)
		if thisPos != None:
			inNet['bus'][idnum]['longitude'] = thisPos[0]
			inNet['bus'][idnum]['latitude'] = thisPos[1]
	return inNet

def netToMat(inNet, networkName):
	'''Convert a network dict to .m string. '''
	# Write header.
	matStr = []
	matStr.append('function mpc = '+networkName+'\n')
	matStr.append('%'+networkName+'\tThis is an OMF.network() generated .m file created from the transmission network saved in '+networkName+'.omt'+'\n')
	matStr.append('\n')
	matStr.append('%% MATPOWER Case Format : Version '+inNet.get('mpcVersion','2')+'\n')
	matStr.append('mpc.version = \''+inNet.get('mpcVersion','2')+'\';\n')
	matStr.append('\n')
	matStr.append('%%-----  Power Flow Data  -----%%\n')
	# Write bus voltage.
	matStr.append('%% system MVA base\n')
	matStr.append('mpc.baseMVA = '+inNet.get('baseMVA','100')+';\n')
	matStr.append('\n')
	# Write bus/gen/branch data.
	electricalKey = [
		['bus_i', 'type', 'Pd', 'Qd', 'Gs', 'Bs', 'area', 'Vm', 'Va', 'baseKV', 'zone', 'Vmax', 'Vmin'],
		['bus', 'Pg', 'Qg', 'Qmax', 'Qmin', 'Vg', 'mBase', 'status', 'Pmax', 'Pmin', 'Pc1', 'Pc2', 'Qc1min', 'Qc1max', 'Qc2min', 'Qc2max', 'ramp_agc', 'ramp_10', 'ramp_30', 'ramp_q', 'apf'],
		['fbus', 'tbus', 'r', 'x', 'b', 'rateA', 'rateB', 'rateC', 'ratio', 'angle', 'status', 'angmin', 'angmax']]
	for i,electrical in enumerate(['bus','gen','branch']):
		matStr.append('%% '+electrical+' data\n')
		matStr.append('%\t'+'\t'.join(str(x) for x in electricalKey[i])+'\n')
		matStr.append('mpc.'+electrical+' = [\n')
		for j,electricalDict in enumerate(inNet[electrical]):
			valueDict = inNet[electrical][str(electricalDict)]
			electricalValues = '\t'.join(valueDict[val] for val in electricalKey[i])
			matStr.append('\t'+electricalValues+';\n')
		matStr.append('];\n')
		matStr.append('\n')
	return matStr

def viz(pathToOmt, outputPath=None):
	''' Open the network in our HTML visualization interface. '''
	# HACK: make sure we have our homebrew binaries available.
	# os.environ['PATH'] += os.pathsep + '/usr/local/bin'
	# Load in the network.
	# Set up temp directory and copy the network and viewer in to it.
	if outputPath == None:
		outputPath = tempfile.mkdtemp()
	template_path = get_abs_path("templates/transEdit.html")
	viewer_path = os.path.join(outputPath, "viewer.html")
	shutil.copy(template_path, viewer_path)
	# Rewrite the load lines in viewer.html
	# Note: you can't just open the file in r+ mode because, based on the way the file is mapped to memory, you can only overwrite a line with another of exactly the same length.
	for line in fileinput.input(viewer_path, inplace=1):
		if line.lstrip().startswith("<script>networkData="):
			print "<script>networkData={}</script>".format(get_file_contents(pathToOmt))
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/svg-pan-zoom.js">'):
			print('<script type="text/javascript" src="{}"></script>'.format(get_abs_path("static/svg-pan-zoom.js")))
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/omf.js">'):
			print('<script type="text/javascript" src="{}"></script>'.format(get_abs_path("static/omf.js")))
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/jquery-1.9.1.js">'):
			print('<script type="text/javascript" src="{}"></script>'.format(get_abs_path("static/jquery-1.9.1.js")))
		elif line.lstrip().startswith('<link rel="stylesheet" href="/static/omf.css"/>'):
			print('<link rel="stylesheet" href="{}"/>'.format(get_abs_path("static/omf.css")))
		elif line.lstrip().startswith('<link rel="shortcut icon" href="/static/favicon.ico"/>'):
			print('<link rel="shortcut icon" href="{}"/>'.format(get_abs_path("static/favicon.ico")))
		elif line.lstrip().startswith('{%'):
			print '' # Remove the is_admin check for saving changes.
		else:
			print line.rstrip()
	# os.system('open -a "Google Chrome" ' + '"file://' + tempDir + '/viewer.html"')
	webbrowser.open_new("file://" + viewer_path)
	##webbrowser.open_new("file://" + tempDir + '/viewer.html')

def get_file_contents(filepath):
	with open(filepath) as f: return f.read()

def get_abs_path(relative_path):
	return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

def get_HTML_interface_path(omt_filepath):
	"""
	Get a path to an .omt file that was saved on the server after a grip API consumer POSTed their desired .omt file.
	Render the .omt file data using the transEdit.html template and injected library code, then return HTML filename.
	"""
	filename = "viewer.html"
	temp_dir = os.path.dirname(omt_filepath)
	viewer_path = os.path.join(temp_dir, filename)
	shutil.copy(os.path.join(os.path.dirname(__file__), "templates/transEdit.html"), viewer_path)
	for line in fileinput.input(viewer_path, inplace=1):
		if line.lstrip().startswith("<script>networkData="):
			print("<script>networkData={}</script>".format(get_file_contents(omt_filepath)))
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/svg-pan-zoom.js">'):
			print('<script type="text/javascript">{}</script>'.format(get_file_contents(os.path.join(os.path.dirname(__file__), "static/svg-pan-zoom.js"))))
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/omf.js">'):
			print('<script type="text/javascript">{}</script>'.format(get_file_contents(os.path.join(os.path.dirname(__file__), "static/omf.js"))))
		elif line.lstrip().startswith('<script type="text/javascript" src="/static/jquery-1.9.1.js">'):
			print('<script type="text/javascript">{}</script>'.format(get_file_contents(os.path.join(os.path.dirname(__file__), "static/jquery-1.9.1.js"))))
		elif line.lstrip().startswith('<link rel="stylesheet" href="/static/omf.css"/>'):
			print('<style>{}</style>'.format(get_file_contents(os.path.join(os.path.dirname(__file__), "static/omf.css"))))
		elif line.lstrip().startswith('<link rel="shortcut icon" href="/static/favicon.ico"/>'):
			print('<link rel="shortcut icon" href="data:image/x-icon;base64,AAABAAEAEBAQAAAAAAAoAQAAFgAAACgAAAAQAAAAIAAAAAEABAAAAAAAgAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAioqKAGlpaQDU1NQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIiIiIiIiIAAgACAAIAAgACAzIzMjMyMwIDAgMCAwIDAiIiIiIiIgMCAwEDAgMCAwIDMTMyMzIzAgMBAwIDAgMCIiIiIiIiAwIDAQMCAwIDAgMxMzIzMjMCAwEDAgMCAwIiIiIiIiIDAAMAAwADAAMAAzMzMzMzMwAAAAAAAAAAAABwAAd3cAAEABAABVVQAAAAUAAFVVAABAAQAAVVUAAAAFAABVVQAAQAEAAFVVAAAABQAA3d0AAMABAAD//wAA"/>')
		elif line.lstrip().startswith('{%'):
			print ""
		else:
			print line.rstrip()
	return filename

def _tests():
	# Parse mat to dictionary.
	networkName = 'case9'
	networkJson = parse(pJoin(omf.omfDir,'solvers','matpower5.1',networkName+'.m'), filePath=True)
	keyLen = len(networkJson.keys())
	print 'Parsed MAT file with %s buses, %s generators, and %s branches.'%(len(networkJson['bus']),len(networkJson['gen']),len(networkJson['branch']))
	# Use python nxgraph to add lat/lon to .omt.json.
	nxG = netToNxGraph(networkJson)
	networkJson = latlonToNet(nxG, networkJson)
	# with open(pJoin(os.getcwd(),'scratch','transmission','outData',networkName+'.omt'),'w') as inFile:
	# 	json.dump(networkJson, inFile, indent=4)
	# print 'Wrote network to: %s'%(pJoin(os.getcwd(),'scratch','transmission',"outData",networkName+".omt"))
	# Convert back to .mat and run matpower.
	matStr = netToMat(networkJson, networkName)
	# with open(pJoin(os.getcwd(),'scratch','transmission',"outData",networkName+".m"),"w") as outMat:
	# 	for row in matStr: outMat.write(row)
	# print 'Converted .omt back to .m at: %s'%(pJoin(os.getcwd(),'scratch','transmission',"outData",networkName+".m"))
	# inputDict = {
	# 	"algorithm" : "FDBX",
	# 	"model" : "DC",
	# 	"iteration" : 10,
	# 	"tolerance" : math.pow(10,-8),
	# 	"genLimits" : 0,
	# 	}
	# matpower.runSim(pJoin(os.getcwd(),'scratch','transmission',"outData",networkName), inputDict, debug=False)
	#viz(os.path.join(os.path.dirname(__file__), "static/SimpleNetwork.json")

if __name__ == '__main__':
	viz(os.path.join(os.path.dirname(__file__), "static/SimpleNetwork.json"))
	#_tests()
''' Functions for manipulating electrical transmission network models. '''

import datetime, copy, os, re, warnings, networkx as nx, json, math
from os.path import join as pJoin
from matplotlib import pyplot as plt
import omf
# import matpower

# Wireframe for new netork objects:
newNetworkWireframe = {"baseMVA":"100.0","mpcVersion":"2.0","bus":{},"gen":{},
	"branch":{}}

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
	for compType in inNet:
		if compType in ['bus','gen','branch']:
			comp = inNet[compType]
			for compVal in comp:
				for idnum,item in compVal.iteritems():
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
	for compType in inNet:
		if compType in ['bus']:
			comp = inNet[compType]
			for compVal in comp:
				for idnum,item in compVal.iteritems():
					obName = item.get('bus_i')
					thisPos = pos.get(obName, None)
					if thisPos != None:
						inNet[compType][int(float(idnum))-1][idnum]['longitude'] = thisPos[0]
						inNet[compType][int(float(idnum))-1][idnum]['latitude'] = thisPos[1]
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

def tests():
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

if __name__ == '__main__':
	_secretTests()
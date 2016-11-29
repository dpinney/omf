''' Functions for manipulating electrical transmission network models. '''

import datetime, copy, os, re, warnings, networkx as nx, json
from os.path import join as pJoin
from matplotlib import pyplot as plt

# Wireframe for new netork objects:
newNetworkWireframe = {"baseMVA":"100.0","mpcVersion":"2.0","bus":[],"gen":[],
	"branch":[]}

def parse(inputStr, filePath=True):
	''' Parse a MAT into an omf.network json. This is so we can walk the json, change things in bulk, etc.
	Input can be a filepath or MAT string.
	'''
	matDict = _dictConversion(inputStr, filePath)
	return matDict

def write(inTree):
	''' Turn an omf.network json object into a MAT-formatted string. '''
	output = ''
	for key in inTree:
		output += _dictToString(inTree[key]) + '\n'
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
		# Parse lines.
		if todo!=None:
			line = line.strip('\n').strip(';').strip('\'')
			if "]" in line:
				todo = None
			if todo in ['bus','gen','bus','branch']:
				line = line.split('\t')
			else:
				line = line.split(' ')				
			line = filter(lambda a: a!= '', line)	
			if todo=="version":
				version = float(line[-1][1])
				if version<2: 
					print "MATPOWER VERSION MUST BE 2: %s"%(version)
					break
				todo = None
			elif todo=="mva":
				mva = float(line[-1])
				newNetworkWireframe['baseMVA'] = float(mva)
				todo = None
			elif todo=="bus":
				bus = {"bus_i": int(float(line[0])),"type": int(float(line[1])),"Pd": float(line[2]),"Qd": float(line[3]),"Gs": float(line[4]),"Bs": float(line[5]),"area": float(line[6]),"Vm": float(line[7]),"Va": float(line[8]),"baseKV": float(line[9]),"zone": float(line[10]),"Vmax": float(line[11]),"Vmin": float(line[12])}
				maxKey = len(newNetworkWireframe['bus'])+1
				newNetworkWireframe['bus'].append({maxKey : bus})
			elif todo=="gen":
				gen = {"bus_i": float(line[0]),"Pg": float(line[1]),"Qg": float(line[2]),"Qmax": float(line[3]),"Qmin": float(line[4]),"Vg": float(line[5]),"mBase": float(line[6]),"status": float(line[7]),"Pmax": float(line[8]),"Pmin": float(line[9]),"Pc1": float(line[10]),"Pc2": float(line[11]),"QC1min": float(line[12]),"QC1max": float(line[13]),"QC2min": float(line[14]),"Q21max": float(line[15]),"ramp_agc": float(line[16]),"ramp_10": float(line[17]),"ramp_30": float(line[18]),"ramp_q": float(line[19]),"apf": float(line[20])}
				maxKey = len(newNetworkWireframe['gen'])+1
				newNetworkWireframe['gen'].append({maxKey : gen})
			elif todo=='branch':
				branch =  {"fbus": float(line[0]),"tbus": float(line[1]),"r": float(line[2]),"x": float(line[3]),"b": float(line[4]),"rateA": float(line[5]),"rateB": float(line[6]),"rateC": float(line[7]),"ratio": float(line[8]),"angle": float(line[9]),"status": float(line[10]),"angmin": float(line[11]),"angmax": float(line[12])}
				maxKey = len(newNetworkWireframe['branch'])+1
				newNetworkWireframe['branch'].append({maxKey : branch})
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

def _tests():
	# MAT parsing test.
	networkName = 'case30'
	networkJson = parse(pJoin(os.getcwd(),'inData','matpower6.0b1',networkName+'.m'), filePath=True)
	keyLen = len(networkJson.keys())
	print 'Parsed a test MAT file with %s buses, %s generators, and %s branches.'%(len(networkJson['bus']),len(networkJson['gen']),len(networkJson['branch']))
	# Write to omt.json.
	with open(pJoin(os.getcwd(),"outData",networkName+".omt.json"),"w") as inFile:
		json.dump(networkJson, inFile, indent=4)
	print 'Wrote to: %s'%(pJoin(os.getcwd(),"outData",networkName+".omt.json"))

if __name__ == '__main__':
	_tests()
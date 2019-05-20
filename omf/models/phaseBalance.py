''' Calculate phase unbalance and determine mitigation options. '''

import json, os, shutil, csv
import numpy as np
import pandas as pd

from os.path import join as pJoin
from matplotlib import pyplot as plt

# OMF imports 
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf.models.voltageDrop import drawPlot as voltagePlot
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf.weather import zipCodeToClimateName

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Calculate phase unbalance and determine mitigation options."
hidden = True

def n(num):
	return "${:,.2f}".format(num)

def work(modelDir, ind):
	''' Run the model in its directory. '''
	o = {}
	
	price = float(ind['retailCost'])

	with open(pJoin(modelDir, [x for x in os.listdir(modelDir) if x.endswith('.omd')][0])) as f:
		tree = json.load(f)['tree']

	tree = _addCollectors(tree)
	with open(modelDir + '/withCollectors.glm', 'w') as f:
		treeString = feeder.sortedWrite(tree)
		f.write(treeString)

	# ---------------------------- BUILD CHART ----------------------------- #
	neato = False if ind.get("layoutAlgorithm", "geospatial") == "geospatial" else True
	edgeColValue = ind.get("edgeCol", None) if ind.get("edgeCol") != "None" else None
	nodeColValue = ind.get("nodeCol", None) if ind.get("nodeCol") != "None" else None
	edgeLabsValue = ind.get("edgeLabs", None) if ind.get("edgeLabs") != "None" else None
	nodeLabsValue = ind.get("nodeLabs", None) if ind.get("nodeLabs") != "None" else None
	customColormapValue = True if ind.get("customColormap", "True") == "True" else False
	
	voltagePlot(
		pJoin(modelDir, "withCollectors.glm"), workDir=modelDir, neatoLayout=False, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"])
	).savefig(pJoin(modelDir,"output.png"))
	with open(pJoin(modelDir,"output.png"),"rb") as f:
		o["voltageDrop"] = f.read().encode("base64")
	# ----------------------------------------------------------------------- #
	
	# --------------------------- SERVICE TABLE ----------------------------- #
	price = float(ind['retailCost'])
	sub_d = {'base': np.nan,'solar': np.nan,'controlled_solar': np.nan,}
	o['service_cost'] = {
		'load': {
			'base': np.nan, 
			'solar': n(_totals(pJoin(modelDir, 'load.csv')) * price),
			'controlled_solar': np.nan
		},
		'distributed_gen': {
			'base': '$0.00',
			'solar': n(_totals(pJoin(modelDir, 'distributedGen.csv')) * price),
			'controlled_solar': np.nan
		},
		'losses': {
			'base': np.nan,
			'solar': n(sum([_totals(pJoin(modelDir, 'Zlosses_'+loss+'.csv')) for loss in 
				['transformer', 'underground_line', 'overhead_line', 'triplex_line']]) * -price),
			'controlled_solar': np.nan
		},
	}
	# ----------------------------------------------------------------------- #

	
	# -------------------------- INVERTER TABLE ----------------------------- #
	df_inv = _readCSV(pJoin(modelDir, 'all_inverters_VA_Out_AC.csv'))
	o['inverter_table'] = ''.join([(
		"<tr>"
			"<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{3}</td>"
		"</tr>"
	).format(inverter, row['real'], row['imag'], np.nan) for inverter, row in df_inv.iterrows()])
	# ----------------------------------------------------------------------- #


	# ---------------------------- MOTOR TABLE ------------------------------ #
	df_all_motors = pd.DataFrame()
	for phase in ['A', 'B', 'C']:
		df_phase = _readCSV(pJoin(modelDir, 'threephase_VA_'+ phase +'.csv'))
		df_phase.columns = [phase + '_' + c for c in df_phase.columns]
		if df_all_motors.shape[0] == 0:
			df_all_motors = df_phase
		else:
			df_all_motors = df_all_motors.join(df_phase)

	o['motor_table'] = ''.join([(
		"<tr>"
			"<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td>"
		"</tr>"
	).format(motor, r['A_real'], r['A_imag'], r['B_real'], r['B_imag'], r['C_real'], r['C_imag']) 
		for motor, r in df_all_motors.iterrows()])
	# ----------------------------------------------------------------------- #

	return o

def _addCollectors(tree):
	for x in tree.values():
		if 'object' in x and 'load' in x['object'] and all([phase in x['phases'] for phase in 'ABC']):
			x['groupid'] = 'threePhase'

	# load on system and inverters
	all_power = 'sum(power_A.real),sum(power_A.imag),sum(power_B.real),sum(power_B.imag),sum(power_C.real),sum(power_C.imag)'
	tree[len(tree)] = {'property': all_power, 'object': 'collector', 'group': 'class=inverter', 'limit': '0', 'file': 'distributedGen.csv'}
	tree[len(tree)] = {'property': all_power, 'object': 'collector', 'group': 'class=load', 'limit': '0', 'file': 'load.csv'}
	
	# Load on motor phases
	for phase in ['A', 'B', 'C']:
		tree[len(tree)] = {'property':'power_' + phase, 'object':'group_recorder', 'group':'class=load AND groupid=threePhase', 'limit': '1', 'file':'threephase_VA_'+ phase +'.csv'}
	
	# Loss across system
	all_losses = 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'
	for loss in ['transformer', 'underground_line', 'overhead_line', 'triplex_line']:
		tree[len(tree)] = {'property': all_losses, 'object': 'collector', 'group': 'class='+loss, 'limit': '0', 'file': 'Zlosses_'+loss+'.csv'}
	# Individual inverters
	tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=inverter', 'limit':'1', 'file':'all_inverters_VA_Out_AC.csv'}
	
	return tree

def _readCSV(filename):
	df = pd.read_csv(filename, skiprows=8)
	df = df.T
	df = df[df.columns[:-2]]
	df = df[~df.index.str.startswith('#')]
	df[0] = [complex(i) for i in df[0]]
	df['imag'] = df[0].imag.astype(float)
	df['real'] = df[0].real.astype(float)
	df = df.drop([0], axis=1)
	return df

def _totals(filename):
	df = pd.read_csv(filename, skiprows=8)
	df = df.T
	df = df[~df.index.str.startswith('#')]
	return sum(df[0])

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "Taxonomic Feeder Rooftop Solar",
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "forceDirected",
		"zipCode": "64735",
		"retailCost": "0.05",
		"discountRate": "7",
		"edgeCol" : "None",
		"nodeCol" : "VoltageImbalance",
		"nodeLabs" : "None",
		"edgeLabs" : "None",
		"customColormap" : "False",
		"rezSqIn" : "225",
		"parameterOne": "42",
		"parameterTwo": "42"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _debugging():
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	if os.path.isdir(modelLoc):
		shutil.rmtree(modelLoc)
	new(modelLoc)
	runForeground(modelLoc)
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

# Copy spcific climate data into model directory (I think this is unnecessary?)
# ind["climateName"] = zipCodeToClimateName(ind["zipCode"])
# shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", ind["climateName"] + ".tmy2"), 
# 	pJoin(modelDir, "climate.tmy2"))

# def _readCollectorCSV(filename):
# 	dataDictionary = {}
# 	with open(filename, 'r') as csvFile:
# 		reader = csv.reader(csvFile)
# 		for row in reader:
# 			if '# property.. timestamp' in row:
# 				key_row = row
# 				value_row = reader.next()
# 				for pos, key in enumerate(key_row):
# 					if key == '# property.. timestamp':
# 						continue
# 					dataDictionary[key] = value_row[pos]
# 	return dataDictionary

	# # Three phase motor loads.
	# tree[len(tree)] = {
	# 	'property': all_power,
	# 	'object': 'collector',
	# 	'group': 'class=load AND groupid=threePhase', 
	# 	'limit': '0', 
	# 	'file': 'threephaseload.csv'
	# } #TODO: delete me

# chart = voltPlot(omd, workDir=modelDir, neatoLayout=neato)

# def _readGroupRecorderCSV( filename ):
# 	dataDictionary = {}
# 	with open(filename,'r') as csvFile:
# 		reader = csv.reader(csvFile)
# 		# loop past the header, 
# 		[keys,vals] = [[],[]]
# 		for row in reader:
# 			if '# timestamp' in row:
# 				keys = row
# 				i = keys.index('# timestamp')
# 				keys.pop(i)
# 				vals = reader.next()
# 				vals.pop(i)
# 		for pos,key in enumerate(keys):
# 			dataDictionary[key] = vals[pos]
# 	return dataDictionary
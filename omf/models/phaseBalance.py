''' Calculate phase unbalance and determine mitigation options. '''

import json, os, shutil, csv
import numpy as np
import pandas as pd
from os.path import join as pJoin
from shutil import copyfile

# OMF imports 
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
from omf.models.voltageDrop import drawPlot as voltagePlot
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf.weather import zipCodeToClimateName
from omf.solvers.SteinmetzController import SteinmetzController

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Calculate phase unbalance and determine mitigation options."
hidden = True

def n(num):
	return "{:,.2f}".format(num)

def work(modelDir, ind):
	''' Run the model in its directory. '''
	o = {}
	
	price = float(ind['retailCost'])
	
	neato = False if ind.get("layoutAlgorithm", "geospatial") == "geospatial" else True
	edgeColValue = ind.get("edgeCol", None) if ind.get("edgeCol") != "None" else None
	nodeColValue = ind.get("nodeCol", None) if ind.get("nodeCol") != "None" else None
	edgeLabsValue = ind.get("edgeLabs", None) if ind.get("edgeLabs") != "None" else None
	nodeLabsValue = ind.get("nodeLabs", None) if ind.get("nodeLabs") != "None" else None
	customColormapValue = True if ind.get("customColormap", "True") == "True" else False


	# -------------------------- BASE CHART --------------------------- #
	with open(pJoin(modelDir, [x for x in os.listdir(modelDir) if x.endswith('.omd')][0])) as f:
		tree_base = json.load(f)['tree']
	with open(pJoin(modelDir, 'input.glm'), 'w') as f:
		treeString = feeder.sortedWrite(tree_base)
		f.write(treeString)

	base_suffix = "_base"
	tree_base = _turnOffSolar(tree_base)
	tree_base = _addCollectors(tree_base, suffix=base_suffix)
	with open(pJoin(modelDir, '_base.glm'), 'w') as f:
		treeString = feeder.sortedWrite(tree_base)
		f.write(treeString)
	
	voltagePlot(
		pJoin(modelDir, "_base.glm"), workDir=modelDir, neatoLayout=neato, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"])
	).savefig(pJoin(modelDir,"output" + base_suffix + ".png"))
	with open(pJoin(modelDir,"output" + base_suffix + ".png"),"rb") as f:
		o["base_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_base.csv"))

	# ---------------------------- SOLAR CHART ----------------------------- #
	with open(pJoin(modelDir, [x for x in os.listdir(modelDir) if x.endswith('.omd')][0])) as f:
		tree_solar = json.load(f)['tree']

	solar_suffix = "_solar"
	tree_solar = _addCollectors(tree_solar, suffix=solar_suffix)
	with open(modelDir + '/_solar.glm', 'w') as f:
		treeString = feeder.sortedWrite(tree_solar)
		f.write(treeString)
	
	voltagePlot(
		pJoin(modelDir, "_solar.glm"), workDir=modelDir, neatoLayout=neato, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"])
	).savefig(pJoin(modelDir,"output" + solar_suffix + ".png"))
	with open(pJoin(modelDir,"output" + solar_suffix + ".png"),"rb") as f:
		o["solar_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_solar.csv"))
	
	# ---------------------------- CONTROLLED CHART ----------------------------- #
	
	controlled_suffix = '_controlled'
	SteinmetzController(pJoin(modelDir, 'input.glm'), 
		ind['pvConnection'], ind['criticalNode'], 
		int(ind['iterations']), ind['objectiveFunction'], modelDir)

	glmPath = pJoin(modelDir, 'input_NewDeltaPV_Final.glm') 
	omdPath = pJoin(modelDir, '_controlled.omd')
	feeder.glmToOmd(glmPath, omdPath)
	
	with open(omdPath) as f:
		tree_controlled = json.load(f)['tree']
	
	for k, v in tree_controlled.iteritems():
		if ('PV' in v.get('groupid', '')) and v.get('object', '') == 'load':
			v['groupid'] = 'PV'

	tree_controlled = _addCollectors(tree_controlled, suffix=controlled_suffix)
	with open(pJoin(modelDir, '_controlled.glm'), 'w') as f:
		treeString = feeder.sortedWrite(tree_controlled)
		f.write(treeString)
	
	voltagePlot(
		pJoin(modelDir, "_controlled.glm"), workDir=modelDir, neatoLayout=neato, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"])
	).savefig(pJoin(modelDir,"output" + controlled_suffix + ".png"))
	with open(pJoin(modelDir,"output" + controlled_suffix + ".png"),"rb") as f:
		o["controlled_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_controlled.csv"))
	
	# --------------------------- SERVICE TABLE ----------------------------- #
	price = float(ind['retailCost'])
	
	o['service_cost'] = {
		'load': {
			'base': n(_totals(pJoin(modelDir, 'load' + base_suffix + '.csv'), 'real')),
			'solar': n(_totals(pJoin(modelDir, 'load' + solar_suffix + '.csv'), 'real')),
			'controlled': n(_totals(pJoin(modelDir, 'load' + controlled_suffix + '.csv'), 'real'))
		},
		'distributed_gen': {
			'base': n(_totals(pJoin(modelDir, 'distributedGen' + base_suffix + '.csv'), 'real')),
			'solar': n(_totals(pJoin(modelDir, 'distributedGen' + solar_suffix + '.csv'), 'real')),
			'controlled': n(_totals(pJoin(modelDir, 'distributedGen' + controlled_suffix + '.csv'), 'real'))
		},
		'losses': {
			'base': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + base_suffix + '.csv'), 'real') for loss in 
				['transformer', 'underground_line', 'overhead_line', 'triplex_line']])),
			'solar': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + solar_suffix + '.csv'), 'real') for loss in 
				['transformer', 'underground_line', 'overhead_line', 'triplex_line']])),
			'controlled':n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + controlled_suffix + '.csv'), 'real') for loss in 
				['transformer', 'underground_line', 'overhead_line', 'triplex_line']])),
		},
		'VARs': {
			'base': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + base_suffix + '.csv'), 'imag') for loss in 
				['transformer', 'underground_line', 'overhead_line', 'triplex_line']])),
			'solar': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + solar_suffix + '.csv'), 'imag') for loss in 
				['transformer', 'underground_line', 'overhead_line', 'triplex_line']])),
			'controlled': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + controlled_suffix + '.csv'), 'imag') for loss in 
				['transformer', 'underground_line', 'overhead_line', 'triplex_line']]))
		}
	}

	# hack correction
	o['service_cost']['load']['controlled'] = n(float(o['service_cost']['load']['controlled'].replace(',', '')) - float(o['service_cost']['distributed_gen']['controlled'].replace(',', '')))
	
	df_inv = _readCSV(pJoin(modelDir, 'all_inverters_VA_Out_AC' + solar_suffix + '.csv'))
	o['service_cost']['distributed_gen']['solar'] = n(-sum([x['real'] for i, x in df_inv.iterrows()]))
	# ----------------------------------------------------------------------- #

	
	# -------------------------- INVERTER TABLE ----------------------------- #
	o['inverter_table'] = ''.join([(
		"<tr>"
			"<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{3}</td>"
		"</tr>"
	).format(inverter, n(row['real']), n(row['imag']), np.nan) for inverter, row in df_inv.iterrows()])
	# ----------------------------------------------------------------------- #


	# ----------------- MOTOR VOLTAGE and IMBALANCE TABLES ------------------ #
	df_vs = {}
	for suffix in [base_suffix, solar_suffix, controlled_suffix]:
		df_v = pd.DataFrame()
		for phase in ['A', 'B', 'C']:
			df_phase = _readCSV(pJoin(modelDir, 'threephase_VA_'+ phase + suffix + '.csv'))
			df_phase.columns = [phase + '_' + c for c in df_phase.columns]
			if df_v.shape[0] == 0:
				df_v = df_phase
			else:
				df_v = df_v.join(df_phase)
		df_vs[suffix] = df_v

	motor_names = [motor for motor, r in df_v.iterrows()]

	for suffix in [base_suffix, solar_suffix, controlled_suffix]:
		df_all_motors = pd.DataFrame()

		df_all_motors = _readVoltage(pJoin(modelDir, 'voltDump' + suffix + '.csv'), motor_names)
		
		o['motor_table' + suffix] = ''.join([(
			"<tr>"
				"<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td>"
			"</tr>" 
				if r['node_name'] != ind['criticalNode'] else 
			"<tr>"
				"<td {7}>{0}</td><td {7}>{1}</td><td {7}>{2}</td><td {7}>{3}</td><td {7}>{4}</td><td {7}>{5}</td><td {7}>{6}</td>"
			"</tr>"
		).format(r['node_name'], 
					n(r2['A_real'] + r2['B_real'] + r2['C_real']),
					n(r2['A_imag'] + r2['B_imag'] + r2['C_imag']),
					n(r['voltA']), n(r['voltB']), n(r['voltC']), 
					n(r['unbalance']), "style='background:yellow'") 
				for (i, r), (j, r2) in zip(df_all_motors.iterrows(), df_vs[suffix].iterrows())])
	# ----------------------------------------------------------------------- #

	return o

def _addCollectors(tree, suffix=None):
	for x in tree.values():
		# if 'object' in x and 'load' in x['object'] and all([phase in x['phases'] for phase in 'ABC']):
		if 'object' in x and ('load' in x['object'] or 'node' in x['object']) and all([phase in x['phases'] for phase in 'ABC']):
			x['groupid'] = 'threePhase'

	# load on system and inverters
	all_power = 'sum(power_A.real),sum(power_A.imag),sum(power_B.real),sum(power_B.imag),sum(power_C.real),sum(power_C.imag)'
	tree[len(tree)] = {'property': all_power, 'object': 'collector', 'group': 'class=load', 'limit': '0', 'file': 'load' + suffix + '.csv'}
	
	# Load on motor phases
	for phase in ['A', 'B', 'C']:
		# tree[len(tree)] = {'property':'power_' + phase, 'object':'group_recorder', 'group':'class=load AND groupid=threePhase', 'limit': '1', 'file':'threephase_VA_'+ phase + suffix + '.csv'}
		tree[len(tree)] = {'property':'power_' + phase, 'object':'group_recorder', 'group':'groupid=threePhase', 'limit': '1', 'file':'threephase_VA_'+ phase + suffix + '.csv'}
	
	# Loss across system
	all_losses = 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'
	for loss in ['transformer', 'underground_line', 'overhead_line', 'triplex_line']:
		tree[len(tree)] = {'property': all_losses, 'object': 'collector', 'group': 'class='+loss, 'limit': '0', 'file': 'Zlosses_'+loss + suffix +'.csv'}
	# Individual inverters

	if suffix != '_controlled':
		tree[len(tree)] = {'property': all_power, 'object': 'collector', 'group': 'class=inverter', 'limit': '0', 'file': 'distributedGen' + suffix + '.csv'}
		tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=inverter', 'limit':'1', 'file':'all_inverters_VA_Out_AC' + suffix + '.csv'}
	else:
		tree[len(tree)] = {'property': all_power, 'object': 'collector', 'group': 'class=load AND groupid=PV', 'limit': '0', 'file': 'distributedGen' + suffix + '.csv'}
		# tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=load AND groupid=PV', 'limit':'1', 'file':'all_inverters_VA_Out_AC' + suffix + '.csv'}

	return tree

def _turnOffSolar(tree):
	for k, v in tree.iteritems():
		if v.get("object", "") in ["solar", "inverter"]:
			tree[k]["generator_status"] = "OFFLINE"
	return tree

def _readVoltage(filename, motor_names):
	return_df = pd.DataFrame()
	df = pd.read_csv(filename, skiprows=1)
	df_motors = df[df['node_name'].isin(motor_names)]
	for phase in ['voltA', 'voltB', 'voltC']:
		return_df[phase] = np.sqrt(df_motors[phase + '_imag']**2 + df_motors[phase + '_real']**2)
	return_df['unbalance'] = return_df.apply(unbalance, axis=1)
	return_df['node_name'] = df_motors['node_name']
	return return_df

def unbalance(r):
	a = float(r['voltA'])
	b = float(r['voltB'])
	c = float(r['voltC'])
	avgVolts = (a + b + c)/3
	maxDiff = max([abs(a-b), abs(a-c), abs(b-c)])
	return maxDiff/avgVolts

def _readCSV(filename):
	df = pd.read_csv(filename, skiprows=8)
	df = df.T
	df = df[df.columns[:-2]]
	df = df[~df.index.str.startswith('#')]
	df[0] = [complex(i) if i != '+0+0i' else complex(0) for i in df[0]]
	df['imag'] = df[0].imag.astype(float)
	df['real'] = df[0].real.astype(float)
	df = df.drop([0], axis=1)
	return df

def _totals(filename, component=None):
	df = pd.read_csv(filename, skiprows=8)
	df = df.T
	df = df[~df.index.str.startswith('#')]
	if component == "real":
		return sum(df[df.index.str.contains('real')][0])
	else:
		return sum(df[df.index.str.contains('imag')][0])

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"feederName1": "phase_balance_test",
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "forceDirected", #geospatial
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
		"parameterTwo": "42",
		"colorMin": "0",
		"colorMax": "1000",
		"criticalNode": 'R1-12-47-1_node_1',
		"objectiveFunction": 'VUF', #'I0'
		"pvConnection": 'Delta',
		"iterations": "5"
	}
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "testFiles", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _debugging():
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	if os.path.isdir(modelLoc):
		shutil.rmtree(modelLoc)
	new(modelLoc)
	renderAndShow(modelLoc)
	runForeground(modelLoc)
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

# sourceFileName = pJoin(modelDir, '_controlled.glm')
# copyfile(pJoin(__neoMetaModel__._omfDir, "static", "testFiles", 'R1-12.47-1-AddSolar-Wye.glm'), sourceFileName)
# glmPath = pJoin(modelDir, '_controlled.glm') 
# omdPath = pJoin(modelDir, 'phase_balance_test.omd')
# feeder.glmToOmd(glmPath, omdPath)

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
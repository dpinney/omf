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

	SIGN_CORRECTION = -1 if ind['pvConnection'] == 'Delta' else 1

	# sourceFileName = pJoin(modelDir, '_controlled.glm')
	# copyfile(pJoin(__neoMetaModel__._omfDir, "static", "testFiles", 'phase_balance_test_2.glm'), sourceFileName)
	# glmPath = pJoin(modelDir, '_controlled.glm') 
	# omdPath = pJoin(modelDir, 'phase_balance_test_2.omd')
	# feeder.glmToOmd(glmPath, omdPath)

	# -------------------------- BASE CHART --------------------------- #
	with open(pJoin(modelDir, [x for x in os.listdir(modelDir) if x.endswith('.omd')][0])) as f:
		tree_base = json.load(f)['tree']
	
	with open(pJoin(modelDir, 'input.glm'), 'w') as f:
		treeString = feeder.sortedWrite(tree_base)
		f.write(treeString)

	base_suffix = "_base"
	tree_base = _turnOffSolar(tree_base)
	tree_base = _addCollectors(tree_base, suffix=base_suffix, pvConnection=ind['pvConnection'])
	with open(pJoin(modelDir, '_base.glm'), 'w') as f:
		treeString = feeder.sortedWrite(tree_base)
		f.write(treeString)
	
	voltagePlot(
		pJoin(modelDir, "_base.glm"), workDir=modelDir, neatoLayout=neato, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"]), 
			colorMin=float(ind['colorMin']) if ind['colorMin'].lower() != 'auto' else None, 
			colorMax=float(ind['colorMax']) if ind['colorMax'].lower() != 'auto' else None
	).savefig(pJoin(modelDir,"output" + base_suffix + ".png"))
	with open(pJoin(modelDir,"output" + base_suffix + ".png"),"rb") as f:
		o["base_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_base.csv"))

	# ---------------------------- SOLAR CHART ----------------------------- #
	with open(pJoin(modelDir, [x for x in os.listdir(modelDir) if x.endswith('.omd')][0])) as f:
		tree_solar = json.load(f)['tree']

	solar_suffix = "_solar"
	tree_solar = _addCollectors(tree_solar, suffix=solar_suffix, pvConnection=ind['pvConnection'])
	with open(modelDir + '/_solar.glm', 'w') as f:
		treeString = feeder.sortedWrite(tree_solar)
		f.write(treeString)
	
	voltagePlot(
		pJoin(modelDir, "_solar.glm"), workDir=modelDir, neatoLayout=neato, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"]), 
			colorMin=float(ind['colorMin']) if ind['colorMin'] != 'auto' else None,
			colorMax=float(ind['colorMax']) if ind['colorMax'] != 'auto' else None
	).savefig(pJoin(modelDir,"output" + solar_suffix + ".png"))
	with open(pJoin(modelDir,"output" + solar_suffix + ".png"),"rb") as f:
		o["solar_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_solar.csv"))
	
	# ---------------------------- CONTROLLED CHART ----------------------------- #
	
	controlled_suffix = '_controlled'
	
	SteinmetzController(pJoin(modelDir, 'input.glm'), 
		ind['pvConnection'], ind['criticalNode'], 
		int(ind['iterations']), ind['objectiveFunction'], modelDir)

	if ind["pvConnection"] == 'Delta':
		glmPath = pJoin(modelDir, 'input_NewDeltaPV_Final.glm')
	else:
		glmPath = pJoin(modelDir, 'input_Final.glm')
	omdPath = pJoin(modelDir, '_controlled.omd')
	feeder.glmToOmd(glmPath, omdPath)
	
	with open(omdPath) as f:
		tree_controlled = json.load(f)['tree']
	
	for k, v in tree_controlled.iteritems():
		if ('PV' in v.get('groupid', '')) and v.get('object', '') == 'load':
			v['groupid'] = 'PV'

	tree_controlled = _addCollectors(tree_controlled, suffix=controlled_suffix, pvConnection=ind['pvConnection'])
	
	with open(pJoin(modelDir, '_controlled.glm'), 'w') as f:
		treeString = feeder.sortedWrite(tree_controlled)
		f.write(treeString)
	
	voltagePlot(
		pJoin(modelDir, "_controlled.glm"), workDir=modelDir, neatoLayout=neato, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"]), 
			colorMin=float(ind['colorMin']) if ind['colorMin'] != 'auto' else None,
			colorMax=float(ind['colorMax']) if ind['colorMax'] != 'auto' else None
	).savefig(pJoin(modelDir,"output" + controlled_suffix + ".png"))
	with open(pJoin(modelDir,"output" + controlled_suffix + ".png"),"rb") as f:
		o["controlled_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_controlled.csv"))
	
	# --------------------------- SERVICE TABLE ----------------------------- #
	price = float(ind['retailCost'])
	
	df_invs = {}
	sums = {}
	for suffix in [base_suffix, solar_suffix, controlled_suffix]:
		df_invs[suffix] = { phase: _readCSV(pJoin(modelDir, 'all_inverters_VA_Out_AC_' + phase + suffix + '.csv')) for phase in 'ABC' }

	for suffix in [base_suffix, solar_suffix, controlled_suffix]:
		df_invs[suffix] = {}
		sums[suffix] = 0
		for phase in 'ABC':
			df = _readCSV(pJoin(modelDir, 'all_inverters_VA_Out_AC_' + phase + suffix + '.csv'))
			df_invs[suffix][phase] = df
			sums[suffix] += df['real'].sum()

	o['service_cost'] = {
		'load': {
			'base': n(_totals(pJoin(modelDir, 'load' + base_suffix + '.csv'), 'real')),
			'solar': n(_totals(pJoin(modelDir, 'load' + solar_suffix + '.csv'), 'real')),
			'controlled': n(_totals(pJoin(modelDir, 'load' + controlled_suffix + '.csv'), 'real'))
		},
		'distributed_gen': {
			'base': n(sums[base_suffix]),
			'solar': n(sums[solar_suffix]),
			'controlled': n(SIGN_CORRECTION*sums[controlled_suffix])
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
	if ind['pvConnection'] == 'Delta':
		o['service_cost']['load']['controlled'] = n(float(o['service_cost']['load']['controlled'].replace(',', '')) + float(o['service_cost']['distributed_gen']['controlled'].replace(',', '')))
	# ----------------------------------------------------------------------- #
	
	# -------------------------- INVERTER TABLE ----------------------------- #
	if ind['pvConnection'] == 'Wye':
		inverter_list = set(
			list(df_invs[controlled_suffix]['A'].index) + list(df_invs[controlled_suffix]['B'].index) + list(df_invs[controlled_suffix]['C'].index)
		)
	else:
		inverter_list = df_invs[controlled_suffix]['A'].index
	inverter_rows = {
		inverter: {
			'_solarA': '0j',
			'_solarB': '0j',
			'_solarC': '0j',
			'_controlledA': '0j',
			'_controlledB': '0j',
			'_controlledC': '0j',
		} for inverter in inverter_list
	}

	for suffix in [solar_suffix, controlled_suffix]:
		for phase in 'ABC':
			for inverter, row in df_invs[suffix][phase].iterrows():
				inverter_rows[inverter][suffix + phase] = str(
					SIGN_CORRECTION*complex(row['real'], row['imag']) if suffix == controlled_suffix else complex(row['real'], row['imag'])
				).strip('()')

	o['inverter_table'] = ''.join([(
		"<tr>"
			"<td>{}</td><td style='border-left: solid black 1px;'>{}</td><td>{}</td><td>{}</td><td style='border-left: solid black 1px;'>{}</td><td>{}</td><td>{}</td>"
		"</tr>"
	).format(inverter, v['_solarA'], v['_solarB'], v['_solarC'], v['_controlledA'], v['_controlledB'], v['_controlledC']) for (inverter, v) in inverter_rows.items()])
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

		df_all_motors = _readVoltage(pJoin(modelDir, 'voltDump' + suffix + '.csv'), motor_names, ind['objectiveFunction'])
		
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

def _addCollectors(tree, suffix=None, pvConnection=None):
	for x in tree.values():
		if 'object' in x and ('load' in x['object'].lower() or 'node' in x['object'].lower()) and all([phase in x['phases'] for phase in 'ABC']):
			x['groupid'] = 'threePhase'

	# load on system and inverters
	all_power = 'sum(power_A.real),sum(power_A.imag),sum(power_B.real),sum(power_B.imag),sum(power_C.real),sum(power_C.imag)'
	
	tree[len(tree)] = {'property': all_power, 'object': 'collector', 'group': 'class=load', 'limit': '0', 'file': 'load' + suffix + '.csv'}

	# Load on motor phases
	for phase in ['A', 'B', 'C']:
		# tree[len(tree)] = {'property':'power_' + phase, 'object':'group_recorder', 'group':'class=load AND groupid=threePhase', 'limit': '1', 'file':'threephase_VA_'+ phase + suffix + '.csv'}
		tree[len(tree)] = {'property':'power_' + phase, 'object':'group_recorder', 'group':'groupid=threePhase', 'limit': '1', 'file':'threephase_VA_'+ phase + suffix + '.csv'}
	
	# # Loss across system
	all_losses = 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'
	for loss in ['transformer', 'underground_line', 'overhead_line', 'triplex_line']:
		tree[len(tree)] = {'property': all_losses, 'object': 'collector', 'group': 'class='+loss, 'limit': '0', 'file': 'Zlosses_'+loss + suffix +'.csv'}
	# # Individual inverters

	if suffix != '_controlled' or pvConnection == 'Wye':
		for x in tree.values():
			if x.get('object', '') == 'inverter':
				if 'A' in x['phases']:
					x['groupid'] = 'PVA'
				elif 'B' in x['phases']:
					x['groupid'] = 'PVB'
				elif 'C' in x['phases']:
					x['groupid'] = 'PVC'

		tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=inverter AND groupid=PVA', 'limit':'1', 'file':'all_inverters_VA_Out_AC_A' + suffix + '.csv'}
		tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=inverter AND groupid=PVB', 'limit':'1', 'file':'all_inverters_VA_Out_AC_B' + suffix + '.csv'}
		tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=inverter AND groupid=PVC', 'limit':'1', 'file':'all_inverters_VA_Out_AC_C' + suffix + '.csv'}
		
	else:
		tree[len(tree)] = {'property':'constant_power_A', 'object':'group_recorder', 'group':'class=load AND groupid=PV', 'limit':'1', 'file':'all_inverters_VA_Out_AC_A' + suffix + '.csv'}
		tree[len(tree)] = {'property':'constant_power_B', 'object':'group_recorder', 'group':'class=load AND groupid=PV', 'limit':'1', 'file':'all_inverters_VA_Out_AC_B' + suffix + '.csv'}
		tree[len(tree)] = {'property':'constant_power_C', 'object':'group_recorder', 'group':'class=load AND groupid=PV', 'limit':'1', 'file':'all_inverters_VA_Out_AC_C' + suffix + '.csv'}

		# for x in tree.values():
		# 	if x.get('object', '') == 'load': 
		# 		if 'groupid' not in x:
		# 			x['groupid'] = 'notSolar'

		# tree[len(tree)] = {'property': all_power, 'object': 'group_recorder', 'group': 'class=load AND groupid=notSolar', 'limit': '0', 'file': 'load' + suffix + '.csv'}		

	return tree

def _turnOffSolar(tree):
	for k, v in tree.iteritems():
		if v.get("object", "") in ["solar", "inverter"]:
			tree[k]["generator_status"] = "OFFLINE"
	return tree

def _readVoltage(filename, motor_names, objectiveFunction):
	return_df = pd.DataFrame()
	df = pd.read_csv(filename, skiprows=1)
	df_motors = df[df['node_name'].isin(motor_names)]
	return_df['node_name'] = df_motors['node_name']
	for phase in ['voltA', 'voltB', 'voltC']:
		return_df[phase] = np.sqrt(df_motors[phase + '_imag']**2 + df_motors[phase + '_real']**2)

	if objectiveFunction == 'VUF':
		return_df['unbalance'] = df_motors.apply(unbalanceVUF, axis=1)
	else:
		return_df['unbalance'] = return_df.apply(unbalanceI, axis=1)
	return return_df

def unbalanceVUF(r):
	a = complex(r['voltA_real'], r['voltA_imag'])
	b = complex(r['voltB_real'], r['voltB_imag'])
	c = complex(r['voltC_real'], r['voltC_imag'])
	j = complex(-0.5, math.sqrt(3)/2)
	V_p = (a + j*b + j*j*c)/3
	V_n = (a + j*j*b + j*c)/3
	return abs(V_n)/abs(V_p)*100

def unbalanceI(r):
	a = float(r['voltA'])
	b = float(r['voltB'])
	c = float(r['voltC'])
	avgVolts = (a + b + c)/3
	maxDiff = max([abs(a-b), abs(a-c), abs(b-c)])
	return maxDiff/avgVolts*100

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
		"criticalNode": 'R1-12-47-1_node_17',
		# "feederName1": "phase_balance_test_2",
		# "criticalNode": 'R1-12-47-2_node_28',
		"modelType": modelName,
		"runTime": "",
		"layoutAlgorithm": "forceDirected", #forceDirected
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
		"colorMin": "auto",
		"colorMax": "auto",
		"objectiveFunction": 'VUF', #'I0'
		"pvConnection": 'Wye',
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
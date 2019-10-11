''' Calculate phase unbalance and determine mitigation options. '''

import json, os, shutil, csv
import numpy as np
import pandas as pd
from os.path import join as pJoin
from shutil import copyfile
import math

# OMF imports 
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
# OMF imports 
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf.models.voltageDrop import drawPlot as voltagePlot
import omf.feeder as feeder
from omf.solvers import gridlabd
from omf.weather import zipCodeToClimateName
from omf.solvers.SteinmetzController import SteinmetzController

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "Calculate phase unbalance and determine mitigation options."
# hidden = True

def get_loss_items(tree):
	s = set()
	for i, d in tree.iteritems():
		s.add(d.get('object', ''))
	return [x for x in s if x in ['transformer', 'underground_line', 'overhead_line', 'triplex_line']]

def motor_efficiency(x):
	return 100 - (.0179 + .402*x + .134*x**2) # curve fit from data from NREL analysis

def pf(real, var):
	real, var = floats(real), floats(var)
	return float(real) / math.sqrt(real**2 + var**2)

def n(num):
	return "{:,.2f}".format(num)

def floats(f):
	return float(f.replace(',', ''))

def work(modelDir, ind):
	''' Run the model in its directory. '''
	o = {}
	
	assert not (ind['pvConnection'] == 'Delta' and ind['objectiveFunction'] == 'I0'), (
		'Delta function does not currently support I0 minimization function.'
	)

	SIGN_CORRECTION = -1 if ind['pvConnection'] == 'Delta' else 1
	
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
	tree_base = _addCollectors(tree_base, suffix=base_suffix, pvConnection=ind['pvConnection'])
	with open(pJoin(modelDir, '_base.glm'), 'w') as f:
		treeString = feeder.sortedWrite(tree_base)
		f.write(treeString)
	
	voltagePlot(
		pJoin(modelDir, "_base.glm"), workDir=modelDir, neatoLayout=neato, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"]), 
			scaleMin=float(ind['colorMin']) if ind['colorMin'].lower() != 'auto' else None, 
			scaleMax=float(ind['colorMax']) if ind['colorMax'].lower() != 'auto' else None
	).savefig(pJoin(modelDir,"output" + base_suffix + ".png"))
	with open(pJoin(modelDir,"output" + base_suffix + ".png"),"rb") as f:
		o["base_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_base.csv"))

	# ---------------------------- SOLAR CHART ----------------------------- #
	# with open(pJoin(modelDir, [x for x in os.listdir(modelDir) if x.endswith('.omd')][0])) as f:
	# 	tree_solar = json.load(f)['tree']

	# solar_suffix = "_solar"
	# tree_solar = _addCollectors(tree_solar, suffix=solar_suffix, pvConnection=ind['pvConnection'])
	# with open(modelDir + '/_solar.glm', 'w') as f:
	# 	treeString = feeder.sortedWrite(tree_solar)
	# 	f.write(treeString)
	
	# voltagePlot(
	# 	pJoin(modelDir, "_solar.glm"), workDir=modelDir, neatoLayout=neato, 
	# 	edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
	# 	edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"]), 
	# 		scaleMin=float(ind['colorMin']) if ind['colorMin'] != 'auto' else None,
	# 		scaleMax=float(ind['colorMax']) if ind['colorMax'] != 'auto' else None
	# ).savefig(pJoin(modelDir,"output" + solar_suffix + ".png"))
	# with open(pJoin(modelDir,"output" + solar_suffix + ".png"),"rb") as f:
	# 	o["solar_image"] = f.read().encode("base64")
	# os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_solar.csv"))
	
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
			scaleMin=float(ind['colorMin']) if ind['colorMin'] != 'auto' else None,
			scaleMax=float(ind['colorMax']) if ind['colorMax'] != 'auto' else None
	).savefig(pJoin(modelDir,"output" + controlled_suffix + ".png"))
	with open(pJoin(modelDir,"output" + controlled_suffix + ".png"),"rb") as f:
		o["controlled_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_controlled.csv"))
	
	# ------ SOLAR TAKE 2

	if ind["pvConnection"] == 'Delta':
		glmPath = pJoin(modelDir, 'input_NewDeltaPV_Start.glm')
	else:
		glmPath = pJoin(modelDir, 'input_Wye_Start.glm')
	omdPath = pJoin(modelDir, '_solar.omd')
	feeder.glmToOmd(glmPath, omdPath)
	
	with open(omdPath) as f:
		tree_solar = json.load(f)['tree']

	for k, v in tree_solar.iteritems():
		if ('PV' in v.get('groupid', '')) and v.get('object', '') == 'load':
			v['groupid'] = 'PV'

	solar_suffix = "_solar"
	tree_solar = _addCollectors(tree_solar, suffix=solar_suffix, pvConnection=ind['pvConnection'])
	with open(modelDir + '/_solar.glm', 'w') as f:
		treeString = feeder.sortedWrite(tree_solar)
		f.write(treeString)
	
	voltagePlot(
		pJoin(modelDir, "_solar.glm"), workDir=modelDir, neatoLayout=neato, 
		edgeCol=edgeColValue, nodeCol=nodeColValue, nodeLabs=nodeLabsValue, 
		edgeLabs=edgeLabsValue, customColormap=customColormapValue, rezSqIn=int(ind["rezSqIn"]), 
			scaleMin=float(ind['colorMin']) if ind['colorMin'] != 'auto' else None,
			scaleMax=float(ind['colorMax']) if ind['colorMax'] != 'auto' else None
	).savefig(pJoin(modelDir,"output" + solar_suffix + ".png"))
	with open(pJoin(modelDir,"output" + solar_suffix + ".png"),"rb") as f:
		o["solar_image"] = f.read().encode("base64")
	os.rename(pJoin(modelDir, "voltDump.csv"), pJoin(modelDir, "voltDump_solar.csv"))

	# --------------------------- SERVICE TABLE ----------------------------- 
	
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
			sums[suffix] += complex(df['real'].sum(), df['imag'].sum())

	loss_items = get_loss_items(tree_base)

	o['service_cost'] = {
		'load': {
			'base': n(_totals(pJoin(modelDir, 'load' + base_suffix + '.csv'), 'real') + _totals(pJoin(modelDir, 'load_node' + base_suffix + '.csv'), 'real')),
			'solar': n(_totals(pJoin(modelDir, 'load' + solar_suffix + '.csv'), 'real') + _totals(pJoin(modelDir, 'load_node' + solar_suffix + '.csv'), 'real')),
			'controlled': n(_totals(pJoin(modelDir, 'load' + controlled_suffix + '.csv'), 'real') + _totals(pJoin(modelDir, 'load_node' + controlled_suffix + '.csv'), 'real'))
		},
		'distributed_gen': {
			'base': n(sums[base_suffix].real),
			'solar': n(SIGN_CORRECTION*sums[solar_suffix].real),
			'controlled': n(SIGN_CORRECTION*sums[controlled_suffix].real)
		},
		'losses': {
			'base': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + base_suffix + '.csv'), 'real') for loss in 
				loss_items])),
			'solar': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + solar_suffix + '.csv'), 'real') for loss in 
				loss_items])),
			'controlled':n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + controlled_suffix + '.csv'), 'real') for loss in 
				loss_items])),
		},
		'VARs': {
			'base': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + base_suffix + '.csv'), 'imag') for loss in 
				loss_items]) + sums[base_suffix].imag +
				_totals(pJoin(modelDir, 'load' + base_suffix + '.csv'), 'imag') + _totals(pJoin(modelDir, 'load_node' + base_suffix + '.csv'), 'imag')
			),
			'solar': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + solar_suffix + '.csv'), 'imag') for loss in 
				loss_items]) + sums[solar_suffix].imag +
				_totals(pJoin(modelDir, 'load' + solar_suffix + '.csv'), 'imag') + _totals(pJoin(modelDir, 'load_node' + solar_suffix + '.csv'), 'imag')
			),
			'controlled': n(sum([_totals(pJoin(modelDir, 'Zlosses_' + loss + controlled_suffix + '.csv'), 'imag') for loss in 
				loss_items]) + sums[controlled_suffix].imag +
				_totals(pJoin(modelDir, 'load' + controlled_suffix + '.csv'), 'imag') + _totals(pJoin(modelDir, 'load_node' + controlled_suffix + '.csv'), 'imag')
			)
		}
	}
	o['service_cost']['power_factor'] = {
		'base': n(pf(o['service_cost']['load']['base'], o['service_cost']['VARs']['base'])),
		'solar': n(pf(o['service_cost']['load']['solar'], o['service_cost']['VARs']['solar'])),
		'controlled': n(pf(o['service_cost']['load']['controlled'], o['service_cost']['VARs']['controlled'])),
	}

	# hack correction
	if ind['pvConnection'] == 'Delta':
		o['service_cost']['load']['controlled'] = n(float(o['service_cost']['load']['controlled'].replace(',', '')) + float(o['service_cost']['distributed_gen']['controlled'].replace(',', '')))
		o['service_cost']['load']['solar'] = n(float(o['service_cost']['load']['solar'].replace(',', '')) + float(o['service_cost']['distributed_gen']['solar'].replace(',', '')))
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
					SIGN_CORRECTION*complex(row['real'], row['imag'])
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

	all_motor_unbalance = {}
	for suffix in [base_suffix, solar_suffix, controlled_suffix]:
		df_all_motors = pd.DataFrame()

		df_all_motors = _readVoltage(pJoin(modelDir, 'voltDump' + suffix + '.csv'), motor_names, ind['objectiveFunction'])
		
		o['motor_table' + suffix] = ''.join([(
			"<tr>"
				"<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td><td>{7}</td>"
			"</tr>" 
				if r['node_name'] != ind['criticalNode'] else 
			"<tr>"
				"<td {8}>{0}</td><td {8}>{1}</td><td {8}>{2}</td><td {8}>{3}</td><td {8}>{4}</td><td {8}>{5}</td><td {8}>{6}</td><td {8}>{7}</td>"
			"</tr>"
		).format(r['node_name'], 
					n(r2['A_real'] + r2['B_real'] + r2['C_real']),
					n(r2['A_imag'] + r2['B_imag'] + r2['C_imag']),
					n(r['voltA']), n(r['voltB']), n(r['voltC']), 
					n(r['unbalance']), n(motor_efficiency(r['unbalance'])), "style='background:yellow'") 
				for (i, r), (j, r2) in zip(df_all_motors.iterrows(), df_vs[suffix].iterrows())])
		
		all_motor_unbalance[suffix] = [r['unbalance'] for i, r in df_all_motors.iterrows()]

	# ----------------------------------------------------------------------- #

	# ---------------------------- COST TABLE ------------------------------- #
	cost = float(ind['productionCost'])
	revenue = float(ind['retailCost'])
	pf_p = float(ind['pf_penalty'])
	pf_t = float(ind['pf_threshold'])
	motor_p = float(ind['motor_penalty'])
	motor_t = float(ind['motor_threshold'])

	o['cost_table'] = {
		'energy_cost': {
			'base': '-$' + n(cost*floats(o['service_cost']['load']['base'])),
			'solar': '-$' + n(cost*floats(o['service_cost']['load']['solar'])),
			'controlled': '-$' + n(cost*floats(o['service_cost']['load']['controlled'])),
		},
		'energy_revenue': {
			'base': '$' + n(revenue*floats(o['service_cost']['load']['base']) - cost*floats(o['service_cost']['distributed_gen']['base'])),
			'solar': '$' + n(revenue*floats(o['service_cost']['load']['solar']) - cost*floats(o['service_cost']['distributed_gen']['solar'])),
			'controlled': '$' + n(revenue*floats(o['service_cost']['load']['controlled']) - cost*floats(o['service_cost']['distributed_gen']['controlled'])),
		},
		'pf_penalty': {
			'base': '-$' + n(pf_p if floats(o['service_cost']['power_factor']['base']) <= pf_t else 0),
			'solar': '-$' + n(pf_p if floats(o['service_cost']['power_factor']['solar']) <= pf_t else 0),
			'controlled': '-$' + n(pf_p if floats(o['service_cost']['power_factor']['controlled']) <= pf_t else 0),
		},
		'motor_damage': {
			'base': '-$' + n(motor_p*len([m for m in all_motor_unbalance['_base'] if m > motor_t])),
			'solar': '-$' + n(motor_p*len([m for m in all_motor_unbalance['_solar'] if m > motor_t])),
			'controlled': '-$' + n(motor_p*len([m for m in all_motor_unbalance['_controlled'] if m > motor_t])),
		},
	}

	# ----------------------------------------------------------------------- #

	if ind['pvConnection'] == 'Delta':
		o['inverter_header'] = "<tr><th>Name</th><th>AB (VA)</th><th>BC (VA)</th><th>AC (VA)</th><th>AB (VA)</th><th>BC (VA)</th><th>AC (VA)</th></tr>"
	else:
		o['inverter_header'] = "<tr><th>Name</th><th>A (VA)</th><th>B (VA)</th><th>C (VA)</th><th>A (VA)</th><th>B (VA)</th><th>C (VA)</th></tr>"
		
	return o

def _addCollectors(tree, suffix=None, pvConnection=None):
	for x in tree.values():
		if 'object' in x and ('load' in x['object'].lower() or 'node' in x['object'].lower()) and all([phase in x['phases'] for phase in 'ABC']):
			x['groupid'] = 'threePhase'

	loss_items = get_loss_items(tree)

	# load on system and inverters
	all_power = 'sum(power_A.real),sum(power_A.imag),sum(power_B.real),sum(power_B.imag),sum(power_C.real),sum(power_C.imag)'
	
	tree[len(tree)] = {'property': all_power, 'object': 'collector', 'group': 'class=load', 'limit': '0', 'file': 'load' + suffix + '.csv'}
	tree[len(tree)] = {'property': 'sum(power_12.real),sum(power_12.imag)', 'object': 'collector', 'group': 'class=triplex_node', 'limit': '0', 'file': 'load_node' + suffix + '.csv'}

	# Load on motor phases
	for phase in 'ABC':
		tree[len(tree)] = {'property':'power_' + phase, 'object':'group_recorder', 'group':'groupid=threePhase', 'limit': '1', 'file':'threephase_VA_'+ phase + suffix + '.csv'}
	
	# Loss across system
	all_losses = 'sum(power_losses_A.real),sum(power_losses_A.imag),sum(power_losses_B.real),sum(power_losses_B.imag),sum(power_losses_C.real),sum(power_losses_C.imag)'
	for loss in loss_items:
		tree[len(tree)] = {'property': all_losses, 'object': 'collector', 'group': 'class='+loss, 'limit': '0', 'file': 'Zlosses_'+loss + suffix +'.csv'}

	solar_A, solar_B, solar_C = False, False, False
	if suffix not in ['_controlled', '_solar'] or pvConnection == 'Wye':
		for x in tree.values():
			if x.get('object', '') == 'inverter':
				if 'A' in x['phases']:
					x['groupid'] = 'PVA'
					solar_A = True
				elif 'B' in x['phases']:
					x['groupid'] = 'PVB'
					solar_B = True
				elif 'C' in x['phases']:
					x['groupid'] = 'PVC'
					solar_C = True

		if solar_A:
			tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=inverter AND groupid=PVA', 'limit':'1', 'file':'all_inverters_VA_Out_AC_A' + suffix + '.csv'}
		if solar_B: 
			tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=inverter AND groupid=PVB', 'limit':'1', 'file':'all_inverters_VA_Out_AC_B' + suffix + '.csv'}
		if solar_C:
			tree[len(tree)] = {'property':'VA_Out', 'object':'group_recorder', 'group':'class=inverter AND groupid=PVC', 'limit':'1', 'file':'all_inverters_VA_Out_AC_C' + suffix + '.csv'}
		
	else:
		tree[len(tree)] = {'property':'constant_power_A', 'object':'group_recorder', 'group':'class=load AND groupid=PV', 'limit':'1', 'file':'all_inverters_VA_Out_AC_A' + suffix + '.csv'}
		tree[len(tree)] = {'property':'constant_power_B', 'object':'group_recorder', 'group':'class=load AND groupid=PV', 'limit':'1', 'file':'all_inverters_VA_Out_AC_B' + suffix + '.csv'}
		tree[len(tree)] = {'property':'constant_power_C', 'object':'group_recorder', 'group':'class=load AND groupid=PV', 'limit':'1', 'file':'all_inverters_VA_Out_AC_C' + suffix + '.csv'}

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
		"pvConnection": 'Wye',
		"layoutAlgorithm": "geospatial",
		# ---------------------------------------- #
		"feederName1": "phase_balance_test_2",
		"criticalNode": 'R1-12-47-2_node_28',
		"pvConnection": 'Delta',
		"layoutAlgorithm": "forceDirected",
		# ---------------------------------------- #
		# "feederName1": 'bavarian_solar',
		# "criticalNode": "node2283458290",
		# "pvConnection": 'Delta',
		# "layoutAlgorithm": "geospatial",
		# ---------------------------------------- #
		# "feederName1": 'turkey_solar',
		# "criticalNode": "nodeOH5041-S1689OH15730",
		# "pvConnection": 'Wye',
		# "layoutAlgorithm": "geospatial",
		# ---------------------------------------- #
		# "feederName1": 'swaec',
		# "criticalNode": "nodespan_192258span_177328",
		# "pvConnection": 'Wye',
		# "layoutAlgorithm": "geospatial",
		# ---------------------------------------- #
		"modelType": modelName,
		"runTime": "",
		"zipCode": "64735",
		"retailCost": "0.05",
		"productionCost": "0.03",
		"pf_penalty": "50000",
		"pf_threshold": "0.95",
		"motor_threshold": "2.5",
		"motor_penalty": "3000000",
		"discountRate": "7",
		"edgeCol" : "None",
		"nodeCol" : "perUnitVoltage",
		"nodeLabs" : "None",
		"edgeLabs" : "None",
		"customColormap" : "False",
		"rezSqIn" : "225",
		"colorMin": "0.92",
		"colorMax": "1.08",
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

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime as dt, csv, math, warnings
import traceback
from os.path import join as pJoin
from jinja2 import Template
from matplotlib import pyplot as plt
import matplotlib
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *
plt.switch_backend('Agg')

# # OMF imports 
# import omf.feeder as feeder
# from omf.solvers import gridlabd

# def voltagePlot(path, workDir=None, neatoLayout=False, edgeLabs=None, nodeLabs=None, edgeCol=None, nodeCol=None, customColormap=False, rezSqIn=400, gldBinary=None, scaleMin=None, scaleMax=None):
# 	''' Draw a color-coded map of the voltage drop on a feeder.
# 	path is the full path to the GridLAB-D .glm file or OMF .omd file.
# 	workDir is where GridLAB-D will run, if it's None then a temp dir is used.
# 	neatoLayout=True means the circuit is displayed using a force-layout approach.
# 	edgeCol property must be either 'Current', 'Power', 'Rating', 'PercentOfRating', or None
# 	nodeCol property must be either 'Voltage', 'VoltageImbalance', 'perUnitVoltage', 'perUnit120Voltage', or None
# 	edgeLabs and nodeLabs properties must be either 'Name', 'Value', or None
# 	edgeCol and nodeCol can be set to false to avoid coloring edges or nodes
# 	customColormap=True means use a one that is nicely scaled to perunit values highlighting extremes.
# 	Returns a matplotlib object.'''
# 	colorMin, colorMax = scaleMin, scaleMax

# 	# Be quiet matplotlib:
# 	warnings.filterwarnings("ignore")
# 	if path.endswith('.glm'):
# 		tree = omf.feeder.parse(path)
# 		attachments = []
# 	elif path.endswith('.omd'):
# 		omd = json.load(open(path))
# 		tree = omd.get('tree', {})
# 		attachments = omd.get('attachments',[])
# 	else:
# 		raise Exception('Invalid input file type. We require a .glm or .omd.')
# 	# dictionary to hold info on lines present in glm
# 	edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator', 'fuse', 'switch'], False)
# 	# Map to speed up name lookups.
# 	nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}
# 	# Get rid of schedules and climate and check for all edge types:
# 	for key in tree.keys():
# 		obtype = tree[key].get("object","")
# 		if obtype == 'underground_line':
# 			edge_bools['underground_line'] = True
# 		elif obtype == 'overhead_line':
# 			edge_bools['overhead_line'] = True
# 		elif obtype == 'triplex_line':
# 			edge_bools['triplex_line'] = True
# 		elif obtype == 'transformer':
# 			edge_bools['transformer'] = True
# 		elif obtype == 'regulator':
# 			edge_bools['regulator'] = True
# 		elif obtype == 'fuse':
# 			edge_bools['fuse'] = True
# 		elif obtype == 'switch':
# 			edge_bools['switch'] = True
# 		if tree[key].get("argument","") == "\"schedules.glm\"" or tree[key].get("tmyfile","") != "":
# 			del tree[key]
# 	# Make sure we have a voltDump:
# 	def safeInt(x):
# 		try: return int(x)
# 		except: return 0
# 	biggestKey = max([safeInt(x) for x in tree.keys()])
# 	tree[str(biggestKey*10)] = {"object":"voltdump","filename":"voltDump.csv"}
# 	tree[str(biggestKey*10 + 1)] = {"object":"currdump","filename":"currDump.csv"}
# 	# Line rating dumps
# 	tree[omf.feeder.getMaxKey(tree) + 1] = {
# 		'module': 'tape'
# 	}
# 	for key in edge_bools.keys():
# 		if edge_bools[key]:
# 			tree[omf.feeder.getMaxKey(tree) + 1] = {
# 				'object':'group_recorder', 
# 				'group':'"class='+key+'"',
# 				'limit':1,
# 				'property':'continuous_rating',
# 				'file':key+'_cont_rating.csv'
# 			}
# 	# Run Gridlab.
# 	if not workDir:
# 		workDir = tempfile.mkdtemp()
# 		# print '@@@@@@', workDir
# 	gridlabOut = omf.solvers.gridlabd.runInFilesystem(tree, attachments=attachments, workDir=workDir, gldBinary=gldBinary)
# 	# read voltDump values into a dictionary.
# 	try:
# 		dumpFile = open(pJoin(workDir,'voltDump.csv'),'r')
# 	except:
# 		raise Exception('GridLAB-D failed to run with the following errors:\n' + gridlabOut['stderr'])
# 	reader = csv.reader(dumpFile)
# 	reader.next() # Burn the header.
# 	keys = reader.next()
# 	voltTable = []
# 	for row in reader:
# 		rowDict = {}
# 		for pos,key in enumerate(keys):
# 			rowDict[key] = row[pos]
# 		voltTable.append(rowDict)
# 	# read currDump values into a dictionary
# 	with open(pJoin(workDir,'currDump.csv'),'r') as currDumpFile:
# 		reader = csv.reader(currDumpFile)
# 		reader.next() # Burn the header.
# 		keys = reader.next()
# 		currTable = []
# 		for row in reader:
# 			rowDict = {}
# 			for pos,key in enumerate(keys):
# 				rowDict[key] = row[pos]
# 			currTable.append(rowDict)
# 	# read line rating values into a single dictionary
# 	lineRatings = {}
# 	rating_in_VA = []
# 	for key1 in edge_bools.keys():
# 		if edge_bools[key1]:		
# 			with open(pJoin(workDir,key1+'_cont_rating.csv'),'r') as ratingFile:
# 				reader = csv.reader(ratingFile)
# 				# loop past the header, 
# 				keys = []
# 				vals = []
# 				for row in reader:
# 					if '# timestamp' in row:
# 						keys = row
# 						i = keys.index('# timestamp')
# 						keys.pop(i)
# 						vals = reader.next()
# 						vals.pop(i)
# 				for pos,key2 in enumerate(keys):
# 					lineRatings[key2] = abs(float(vals[pos]))
# 	#edgeTupleRatings = lineRatings copy with to-from tuple as keys for labeling
# 	edgeTupleRatings = {}
# 	for edge in lineRatings:
# 		for obj in tree.values():
# 			if obj.get('name','').replace('"','') == edge:
# 				nodeFrom = obj.get('from')
# 				nodeTo = obj.get('to')
# 				coord = (nodeFrom, nodeTo)
# 				ratingVal = lineRatings.get(edge)
# 				edgeTupleRatings[coord] = ratingVal
# 	# Calculate average node voltage deviation. First, helper functions.
# 	def digits(x):
# 		''' Returns number of digits before the decimal in the float x. '''
# 		return math.ceil(math.log10(x+1))
# 	def avg(l):
# 		''' Average of a list of ints or floats. '''
# 		return sum(l)/len(l)
# 	# Detect the feeder nominal voltage:
# 	for key in tree:
# 		ob = tree[key]
# 		if type(ob)==dict and ob.get('bustype','')=='SWING':
# 			feedVoltage = float(ob.get('nominal_voltage',1))
# 	# Tot it all up.
# 	nodeVolts = {}
# 	nodeVoltsPU = {}
# 	nodeVoltsPU120 = {}
# 	voltImbalances = {}
# 	for row in voltTable:
# 		allVolts = []
# 		allVoltsPU = []
# 		allDiffs = []
# 		nodeName = row.get('node_name','')
# 		for phase in ['A','B','C']:
# 			realVolt = abs(float(row['volt'+phase+'_real']))
# 			imagVolt = abs(float(row['volt'+phase+'_imag']))
# 			phaseVolt = math.sqrt((realVolt ** 2) + (imagVolt ** 2))
# 			if phaseVolt != 0.0:
# 				treeKey = nameToIndex.get(nodeName, 0)
# 				nodeObj = tree.get(treeKey, {})
# 				try:
# 					nominal_voltage = float(nodeObj['nominal_voltage'])
# 				except:
# 					nominal_voltage = feedVoltage
# 				allVolts.append(phaseVolt)
# 				normVolt = (phaseVolt/nominal_voltage)
# 				allVoltsPU.append(normVolt)
# 		avgVolts = avg(allVolts)
# 		avgVoltsPU = avg(allVoltsPU)
# 		avgVoltsPU120 = 120 * avgVoltsPU
# 		nodeVolts[nodeName] = float("{0:.2f}".format(avgVolts))
# 		nodeVoltsPU[nodeName] = float("{0:.2f}".format(avgVoltsPU))
# 		nodeVoltsPU120[nodeName] = float("{0:.2f}".format(avgVoltsPU120))
# 		if len(allVolts) == 3:
# 			voltA = allVolts.pop()
# 			voltB = allVolts.pop()
# 			voltC = allVolts.pop()
# 			allDiffs.append(abs(float(voltA-voltB)))
# 			allDiffs.append(abs(float(voltA-voltC)))
# 			allDiffs.append(abs(float(voltB-voltC)))
# 			maxDiff = max(allDiffs)
# 			voltImbal = maxDiff/avgVolts
# 			voltImbalances[nodeName] = float("{0:.2f}".format(voltImbal))
# 		# Use float("{0:.2f}".format(avg(allVolts))) if displaying the node labels
# 	nodeNames = {}
# 	for key in nodeVolts.keys():
# 		nodeNames[key] = key
# 	# find edge currents by parsing currdump
# 	edgeCurrentSum = {}
# 	edgeCurrentMax = {}
# 	for row in currTable:
# 		allCurr = []
# 		for phase in ['A','B','C']:
# 			realCurr = abs(float(row['curr'+phase+'_real']))
# 			imagCurr = abs(float(row['curr'+phase+'_imag']))
# 			phaseCurr = math.sqrt((realCurr ** 2) + (imagCurr ** 2))
# 			allCurr.append(phaseCurr)
# 		edgeCurrentSum[row.get('link_name','')] = sum(allCurr)
# 		edgeCurrentMax[row.get('link_name','')] = max(allCurr)
# 	# When just showing current as labels, use sum of the three lines' current values, when showing the per unit values (current/rating), use the max of the three
# 	#edgeTupleCurrents = edgeCurrents copy with to-from tuple as keys for labeling
# 	edgeTupleCurrents = {}
# 	#edgeValsPU = values normalized per unit by line ratings
# 	edgeValsPU = {}
# 	#edgeTupleValsPU = edgeValsPU copy with to-from tuple as keys for labeling
# 	edgeTupleValsPU = {}
# 	#edgeTuplePower = dict with to-from tuples as keys and sim power as values for debugging
# 	edgeTuplePower = {}
# 	#edgeTupleNames = dict with to-from tuples as keys and names as values for debugging
# 	edgeTupleNames = {}
# 	#edgeTupleNames = dict with to-from tuples as keys and names as values for debugging
# 	edgePower = {}
# 	for edge in edgeCurrentSum:
# 		for obj in tree.values():
# 			obname = obj.get('name','').replace('"','')
# 			if obname == edge:
# 				nodeFrom = obj.get('from')
# 				nodeTo = obj.get('to')
# 				coord = (nodeFrom, nodeTo)
# 				currVal = edgeCurrentSum.get(edge)
# 				voltVal = avg([nodeVolts.get(nodeFrom), nodeVolts.get(nodeTo)])
# 				power = (currVal * voltVal)/1000
# 				lineRating = lineRatings.get(edge, 10.0**9)
# 				edgePerUnitVal = (edgeCurrentMax.get(edge))/lineRating
# 				edgeTupleCurrents[coord] = "{0:.2f}".format(currVal)
# 				edgeTuplePower[coord] = "{0:.2f}".format(power)
# 				edgePower[edge] = power
# 				edgeValsPU[edge] = edgePerUnitVal
# 				edgeTupleValsPU[coord] = "{0:.2f}".format(edgePerUnitVal)
# 				edgeTupleNames[coord] = edge
# 	#define which dict will be used for edge line color
# 	edgeColors = edgeValsPU
# 	#define which dict will be used for edge label
# 	edgeLabels = edgeTupleValsPU
# 	# Build the graph.
# 	fGraph = omf.feeder.treeToNxGraph(tree)
# 	# TODO: consider whether we can set figsize dynamically.
# 	wlVal = int(math.sqrt(float(rezSqIn)))
# 	voltChart = plt.figure(figsize=(wlVal, wlVal))
# 	plt.axes(frameon = 0)
# 	plt.axis('off')
# 	voltChart.gca().set_aspect('equal')
# 	plt.tight_layout()
# 	# Need to get edge names from pairs of connected node names.
# 	edgeNames = []
# 	for e in fGraph.edges():
# 		edgeNames.append((fGraph.edge[e[0]][e[1]].get('name','BLANK')).replace('"',''))
# 	#set axes step equal
# 	if neatoLayout:
# 		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
# 		cleanG = nx.Graph(fGraph.edges())
# 		cleanG.add_nodes_from(fGraph)
# 		positions = graphviz_layout(cleanG, prog='neato')
# 	else:
# 		positions = {n:fGraph.node[n].get('pos',(0,0)) for n in fGraph}
# 	#create custom colormap
# 	if customColormap:
# 		custom_cm = matplotlib.colors.LinearSegmentedColormap.from_list('custColMap',[(0.0,'blue'),(0.15,'darkgray'),(0.7,'darkgray'),(1.0,'red')])
# 		custom_cm.set_under(color='black')
# 		vmin = 0 if colorMin is None else colorMin
# 		vmax = 1.25 if colorMax is None else colorMax
# 	else:
# 		custom_cm = plt.cm.get_cmap('viridis')
# 		vmin = None if colorMin is None else colorMin
# 		vmax = None if colorMax is None else colorMax
# 	drawColorbar = False
# 	emptyColors = {}
# 	#draw edges with or without colors
# 	if edgeCol != None:
# 		drawColorbar = True
# 		if edgeCol == "Current":
# 			edgeList = [edgeCurrentSum.get(n,1) for n in edgeNames]
# 			drawColorbar = True
# 		elif edgeCol == "Power":
# 			edgeList = [edgePower.get(n,1) for n in edgeNames]
# 			drawColorbar = True
# 		elif edgeCol == "Rating":
# 			edgeList = [lineRatings.get(n, 10.0**9) for n in edgeNames]
# 			drawColorbar = True
# 		elif edgeCol == "PercentOfRating":
# 			edgeList = [edgeValsPU.get(n,.5) for n in edgeNames]
# 			drawColorbar = True
# 		else:
# 			edgeList = [emptyColors.get(n,.6) for n in edgeNames]
# 			print "WARNING: edgeCol property must be 'Current', 'Power', 'Rating', 'PercentOfRating', or None"
# 	else:
# 		edgeList = [emptyColors.get(n,.6) for n in edgeNames]
# 	edgeIm = nx.draw_networkx_edges(fGraph,
# 		pos = positions,
# 		edge_color = edgeList,
# 		width = 1,
# 		edge_cmap = custom_cm)
# 	#draw edge labels
# 	if edgeLabs != None:
# 		if edgeLabs == "Name":
# 			edgeLabels = edgeTupleNames
# 		elif edgeLabs == "Value":
# 			if edgeCol == "Current":
# 				edgeLabels = edgeTupleCurrents
# 			elif edgeCol == "Power":
# 				edgeLabels = edgeTuplePower
# 			elif edgeCol == "Rating":
# 				edgeLabels = edgeTupleRatings
# 			elif edgeCol == "PercentOfRating":
# 				edgeLabels = edgeTupleValsPU
# 			else:
# 				edgeLabels = None
# 				print "WARNING: edgeCol property cannot be set to None when edgeLabs property is set to 'Value'"
# 		else:
# 			edgeLabs = None
# 			print "WARNING: edgeLabs property must be either 'Name', 'Value', or None"
# 	if edgeLabs != None:
# 		edgeLabelsIm = nx.draw_networkx_edge_labels(fGraph,
# 			pos = positions,
# 			edge_labels = edgeLabels,
# 			font_size = 8)
# 	# draw nodes with or without color
# 	if nodeCol != None:
# 		if nodeCol == "Voltage":
# 			nodeList = [nodeVolts.get(n,1) for n in fGraph.nodes()]
# 			drawColorbar = True
# 		elif nodeCol == "VoltageImbalance":
# 			nodeList = [voltImbalances.get(n,1) for n in fGraph.nodes()]
# 			print nodeList
# 			drawColorbar = True
# 		elif nodeCol == "perUnitVoltage":
# 			nodeList = [nodeVoltsPU.get(n,.5) for n in fGraph.nodes()]
# 			drawColorbar = True
# 		elif nodeCol == "perUnit120Voltage":
# 			nodeList = [nodeVoltsPU120.get(n,60) for n in fGraph.nodes()]
# 			drawColorbar = True
# 		else:
# 			nodeList = [emptyColors.get(n,1) for n in fGraph.nodes()]
# 			print "WARNING: nodeCol property must be 'Voltage', 'VoltageImbalance', 'perUnitVoltage', 'perUnit120Voltage', or None"
# 	else:
# 		nodeList = [emptyColors.get(n,.6) for n in fGraph.nodes()]

# 	nodeIm = nx.draw_networkx_nodes(fGraph,
# 		pos = positions,
# 		node_color = nodeList,
# 		linewidths = 0,
# 		node_size = 30,
# 		vmin = vmin,
# 		vmax = vmax,
# 		cmap = custom_cm)
# 	#draw node labels
# 	nodeLabels = {}
# 	if nodeLabs != None:
# 		if nodeLabs == "Name":
# 			nodeLabels = nodeNames
# 		elif nodeLabs == "Value":
# 			if nodeCol == "Voltage":
# 				nodeLabels = nodeVolts
# 			elif nodeCol == "VoltageImbalance":
# 				nodeLabels = voltImbalances
# 			elif nodeCol == "perUnitVoltage":
# 				nodeLabels = nodeVoltsPU
# 			elif nodeCol == "perUnit120Voltage":
# 				nodeLabels = nodeVoltsPU120
# 			else:
# 				nodeLabels = None
# 				print "WARNING: nodeCol property cannot be set to None when nodeLabs property is set to 'Value'"
# 		else:
# 			nodeLabs = None
# 			print "WARNING: nodeLabs property must be either 'Name', 'Value', or None"
# 	if nodeLabs != None:
# 		nodeLabelsIm = nx.draw_networkx_labels(fGraph,
# 			pos = positions,
# 			labels = nodeLabels,
# 			font_size = 8)
# 	plt.sci(nodeIm)
# 	# plt.clim(110,130)
# 	if drawColorbar:
# 		plt.colorbar()
# 	return voltChart

# ----------------------------------------------- Commenting starts here ---------------------------------------

# sourceFileName = pJoin(modelDir, '_controlled.glm')
# copyfile(pJoin(__neoMetaModel__._omfDir, "static", "testFiles", 'R1-12.47-1-AddSolar-Wye.glm'), sourceFileName)
# glmPath = pJoin(modelDir, '_controlled.glm') 
# omdPath = pJoin(modelDir, 'phase_balance_test.omd')
# feeder.glmToOmd(glmPath, omdPath)

# sourceFileName = pJoin(modelDir, '_controlled.glm')
# copyfile(pJoin(__neoMetaModel__._omfDir, "static", "testFiles", 'phase_balance_test_2.glm'), sourceFileName)
# glmPath = pJoin(modelDir, '_controlled.glm') 
# omdPath = pJoin(modelDir, 'phase_balance_test_2.omd')
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
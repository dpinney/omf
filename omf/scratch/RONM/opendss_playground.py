import random, re, datetime, json, os, tempfile, shutil, csv, math, base64
from os.path import join as pJoin
import subprocess
import pandas as pd
import numpy as np
import scipy
from scipy import spatial
import scipy.stats as st
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import plotly as py
import plotly.graph_objs as go
from plotly.tools import make_subplots

# OMF imports
import omf
from omf import geo
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.models import flisr
from omf.solvers.opendss import dssConvert

# Model metadata:
# tooltip = 'outageCost calculates reliability metrics and creates a leaflet graph based on data from an input csv file.'
# modelName, template = __neoMetaModel__.metadata(__file__)
# hidden = True

def play(pathToOmd, pathToDss, workDir, microgrids, faultedLine, radial):
	# 1) isolate the fault (using step one of flisr model)
	if not workDir:
		workDir = tempfile.mkdtemp()
		print('@@@@@@', workDir)

	# read in the tree
	with open(pathToOmd) as inFile:
		tree = json.load(inFile)['tree']

	# find a node associated with the faulted line
	faultedNode = ''
	faultedNode2 = ''
	for key in tree.keys():
		if tree[key].get('name','') == faultedLine:
			faultedNode = tree[key]['from']
			faultedNode2 = tree[key]['to']

	# initialize the list of ties closed and reclosers opened
	bestTies = []
	bestReclosers = []

	buses = []
	for key in microgrids.keys():
		buses.append(microgrids[key].get('gen_bus', ''))

	tree, bestReclosers, badBuses = flisr.cutoffFault(tree, faultedNode, bestReclosers, workDir, radial, buses)

	# 2) get list of loads associated with each microgrid component
	# and create a loadshape containing all said loads
	buses = []
	for key in microgrids.keys():
		buses.append(microgrids[key].get('gen_bus', ''))
	buses = [x for x in buses if x not in badBuses]

	busShapes = {}
	shape_insert_list = {}
	i = 0
	# for each power source
	while len(buses) > 0:
		# create an adjacency list representation of tree connectivity
		adjacList, reclosers, vertices = flisr.adjacencyList(tree)
		bus = buses[0]
		loadShapes = {}
		# check to see if there is a path between the power source and the fault 
		subtree = flisr.getMaxSubtree(adjacList, bus)
		for node in subtree:
			for key in tree.keys():
				obtype = tree[key].get('object','')
				if obtype == 'load' or obtype == 'triplex_load':
					if tree[key].get('parent','').startswith(str(node)):
						loadshapeName = tree[key].get('yearly', '')
						for key1 in tree.keys():
							if tree[key1].get('name','') == loadshapeName:
								loadshape = eval(tree[key1].get('mult',''))
								if '.1' in tree[key].get('!CONNCODE',''):
									if '.1' in loadShapes:
										loadShapes['.1'] = [a + b for a, b in zip(loadShapes.get('.1',''), loadshape)]
									else: loadShapes['.1'] = loadshape
								if '.2' in tree[key].get('!CONNCODE',''):
									if '.2' in loadShapes:
										loadShapes['.2'] = [a + b for a, b in zip(loadShapes.get('.2',''), loadshape)]
									else: loadShapes['.2'] = loadshape
								if '.3' in tree[key].get('!CONNCODE',''):
									if '.3' in loadShapes:
										loadShapes['.3'] = [a + b for a, b in zip(loadShapes.get('.3',''), loadshape)]
									else: loadShapes['.3'] = loadshape

# 3) obtain the diesel loadshape by subtracting off solar from load
		dieselShapes = {}
		for key in tree.keys():
			if tree[key].get('object','').startswith('generator'):
				if tree[key].get('name','').startswith('solar') and tree[key].get('parent','') == bus:
					solarshapeName = tree[key].get('yearly','')
					for key1 in tree.keys():
						if tree[key1].get('name','') == solarshapeName:
							solarshape = eval(tree[key1].get('mult',''))
							if '.1' in loadShapes:
								dieselShapes['.1'] = [a - b for a, b in zip(loadShapes.get('.1',''), solarshape)]
							if '.2' in loadShapes:
								dieselShapes['.2'] = [a - b for a, b in zip(loadShapes.get('.2',''), solarshape)]
							if '.3' in loadShapes:
								dieselShapes['.3'] = [a - b for a, b in zip(loadShapes.get('.3',''), solarshape)]
							print('hi')
		busShapes[buses[0]] = [dieselShapes.get('.1',''), dieselShapes.get('.2',''), dieselShapes.get('.3','')]
	# 4) add diesel generation to the opendss formatted system and solve
		shape_name = 'NewDiesel_' + str(buses[0]) + '_shape'
		shape_data = dieselShapes.get('.1','')
		shape_insert_list[i] = {
				'!CMD': 'new',
				'object': f'loadshape.{shape_name}',
				'npts': f'{len(shape_data)}',
				'interval': '1',
				'useactual': 'no',
				'mult': f'{list(shape_data)}'
			}
		i+=1
		del (buses[0])

	# insert new diesel loadshapes
	treeDSS = dssConvert.dssToTree(pathToDss)
	for key in shape_insert_list:
		min_pos = min(shape_insert_list.keys())
		treeDSS.insert(min_pos, shape_insert_list[key])

	# Write new DSS file.
	FULL_NAME = 'lehigh_full_newDiesel.dss'
	dssConvert.treeToDss(treeDSS, FULL_NAME)
		
# 5) open switches to isolate the fault in opendss version of system

#### for each switch that is flipped in flisr model:
	# repeat steps 2-5), trying to slowly make microgrids network with each other

microgrids = {
	'm1': {
		'loads': ['634a_supermarket','634b_supermarket','634c_supermarket'],
		'switch': '632633',
		'gen_bus': '634'
	},
	'm2': {
		'loads': ['675a_residential1','675b_residential1','675c_residential1'],
		'switch': '671692',
		'gen_bus': '675'
	},
	'm3': {
		'loads': ['671_hospital','652_med_apartment'],
		'switch': '671684',
		'gen_bus': '684'
	},
	'm4': {
		'loads': ['645_warehouse1','646_med_office'],
		'switch': '632645',
		'gen_bus': '646'
	}
}

play('C:/Users/granb/microgridup-main/lehigh.dss.omd', 'C:/Users/granb/microgridup-main/lehigh_full.dss', None, microgrids, '670671', False)
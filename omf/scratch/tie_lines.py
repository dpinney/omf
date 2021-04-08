import json, os, shutil, subprocess, datetime, re, random, copy, warnings, base64, platform
import os.path
from os.path import join as pJoin
import numpy as np
import networkx as nx

import matplotlib
if platform.system() == 'Darwin':
	matplotlib.use('TkAgg')
else:
	matplotlib.use('Agg')
from matplotlib import pyplot as plt

from geopy import distance

# OMF imports
import omf
from omf import feeder, weather, distNetViz
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.weather import get_ndfd_data
from omf.solvers.opendss import dssConvert
from omf.solvers import opendss

# modelName, template = __neoMetaModel__.metadata(__file__)

def node_distance(circuit, node_name_1, node_name_2):
	# Given two nodes, node_name_1 and node_name_2, in a circuit, find the physical distance between the two
	dist = -1.0
	lat_1 = 0.0
	lat_2 = 0.0
	lon_1 = 0.0
	lon_2 = 0.0
	for omdObj in circuit["tree"]:
		if circuit["tree"][omdObj]["name"] == node_name_1:
			lat_1 = float(circuit["tree"][omdObj]["latitude"])
			lon_1 = float(circuit["tree"][omdObj]["longitude"])
		if circuit["tree"][omdObj]["name"] == node_name_2:
			lat_2 = float(circuit["tree"][omdObj]["latitude"])
			lon_2 = float(circuit["tree"][omdObj]["longitude"])
	coords_1 = (lat_1, lon_1)
	coords_2 = (lat_2, lon_2)
	dist = distance.distance(coords_1, coords_2).km
	return dist

def path_distance(circuit, node_name_1, node_name_2):
	# Given two nodes, node_name_1 and node_name_2, in a circuit, find the number of lines between the two
	distance = -1.0
	#TODO: Get Daniel's code for path distance
	return distance

def find_all_ties(circuit):
	#Given a cicuit, find all possible tie lines between all nodes, excluding ones that already exist
	all_ties = {}
	nodes = {}
	existing_lines = {}
	# keys for the dict are pairs of node names, with the first value being physical distance and second being path distance
	for omdObj in circuit["tree"]:
		if circuit["tree"][omdObj]["object"] == "line":
			line_name = circuit["tree"][omdObj]["name"]
			line_to = circuit["tree"][omdObj]["to"]
			line_from = circuit["tree"][omdObj]["from"]
			existing_lines[line_name] = (line_to, line_from)
		elif "latitude" in circuit["tree"][omdObj]:
			node_name = circuit["tree"][omdObj]["name"]
			nodes[node_name] = omdObj
	
	for node1 in nodes:
		for node2 in nodes:
			if node1 != node2:
				# Narrow down results by eliminating existing lines on the circuit
				if (node1, node2) not in existing_lines.values() and (node2, node1) not in existing_lines.values():
					# Make sure you haven't already added (node1, node2) to your list of possible tie lines
					if (node1, node2) not in all_ties and (node2, node1) not in all_ties:
						physical_dist = node_distance(circuit, node1, node2)
						path_dist = path_distance(circuit, node1, node2)
						all_ties[(node1, node2)] = [physical_dist, path_dist]
	return all_ties

def find_candidate_pair(circuit):
	candidates = []

def run_fault_study(circuit, tempFilePath, faultDetails=None):
	niceDss = dssConvert.evilGldTreeToDssTree(tree)
	dssConvert.treeToDss(niceDss, tempFilePath)
	#TODO: add fault, see Daniel.
	opendss.runDSS(tempFilePath)
	#TODO: look at the output files, see what happened to the loads.

def _runModel():
	with open(pJoin(__neoMetaModel__._omfDir,"static","publicFeeders","iowa240c1.clean.dss.omd"), 'r') as omdFile:
		circuit = json.load(omdFile)
	# Test node_distance()
	dist1 = node_distance(circuit, "load_1003", "load_3019")
	print("load_1003 to load_3019 = " + dist1)
	# Test the tie line creation code
	# all_ties = find_all_ties(circuit)
	# print(all_ties)

if __name__ == '__main__':
	_runModel()
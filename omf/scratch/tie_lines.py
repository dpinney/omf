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
	# if dist_units == 'km':
	# 	dist = distance.distance(coords_1, coords_2).km
	# elif dist_units == 'ft':
	# 	dist = distance.distance(coords_1, coords_2).ft
	# elif dist_units == 'mi':
	# 	dist = distance.distance(coords_1, coords_2).mi
	# else:
	# 	dist = distance.distance(coords_1, coords_2).km
	return dist

def path_distance(circuit, node_name_1, node_name_2):
	# Given two nodes, node_name_1 and node_name_2, in a circuit, find the number of lines between the two
	distance = -1.0
	#TODO: Incorporate networkx path distance with length of lines as weights
	# Create networkx graph
	circuit_graph = feeder.treeToNxGraph(circuit["tree"])
	#create edge_lengths dict to stor the distance of lines
	edge_lengths = {}
	for omdObj in circuit["tree"]:
		if circuit["tree"][omdObj]["object"] == "line":
			line_name = circuit["tree"][omdObj]["name"]
			line_from = circuit["tree"][omdObj]["from"]
			line_to = circuit["tree"][omdObj]["to"]
			circuit_graph.edges[line_from, line_to]["weight"] = node_distance(circuit, line_from, line_to)

	try:
		# This returns the number of edges between the source and target node, but doesn't incorporate length of the path as a weight
		#distance = nx.shortest_path_length(circuit_graph, source=node_name_1, target=node_name_2, weight="length")
		distance, path_list = nx.single_source_dijkstra(circuit_graph, source=node_name_1, target=node_name_2, cutoff=None, weight="weight")
		#distance = nx.single_source_dijkstra_path_length(circuit_graph, source=node_name_1, target=node_name_2, weight=)
	except nx.NetworkXNoPath:
		distance = -1.0

	return distance

def find_all_ties(circuit, circuit_name, bus_limit):
	#Given a cicuit, find all possible tie lines between all nodes, excluding ones that already exist
	all_ties = {}
	all_ties_json = {}
	nodes = {}
	nodes_limited = {}
	existing_lines = {}
	# keys for the dict are pairs of node names, with the first value being physical distance and second being path distance
	for omdObj in circuit["tree"]:
		if circuit["tree"][omdObj]["object"] == "line":
			line_name = circuit["tree"][omdObj]["name"]
			line_to = circuit["tree"][omdObj]["to"]
			line_from = circuit["tree"][omdObj]["from"]
			existing_lines[line_name] = (line_to, line_from)
		# elif "latitude" in circuit["tree"][omdObj]:
		elif circuit["tree"][omdObj]["object"] == "bus":
			node_name = circuit["tree"][omdObj]["name"]
			nodes[node_name] = omdObj
	# Optional search reduction.
	# all_pairs = zip(nodes, nodes) # [(n1, n2), (n2, n1), ...]
	# unique_pairs = set([sorted(x) for x in all_pairs])
	# get rid of the source bus for optimization purposes
	# nodes.pop("eq_source_bus")
	if bus_limit > 0:
		# randomly add the number of nodes denoted by bus_limit and the possible tie_lines will only be ones that are within this set
		import random
		node_keys = list(nodes.keys())
		for x in range(0, bus_limit):
			random_key = random.choice(node_keys)
			nodes_limited[random_key] = nodes[random_key]
			node_keys.remove(random_key)
	else:
		nodes_limited = nodes
	all_ties["selected_buses"] = nodes_limited
	all_ties_json["selected_buses"] = nodes_limited
	nodes_temp = {}
	for node1 in nodes_limited:
		print("node1 = " + node1)
		# Remove node1 from nodes_temp to avoid multiple checks of same node pairings
		nodes_temp[node1] = nodes[node1]
		for node2 in nodes:
			if node2 in nodes_temp:
				pass
			else:
				print("node2 = " + node2)
				# if node1 != node2:
				contains_1 = (node1, node2) in existing_lines.values()
				contains_2 = (node2, node1) in existing_lines.values()
				# Narrow down results by eliminating existing lines on the circuit
				if (not contains_1) and (not contains_2):
					contains_3 = (node1, node2) in all_ties
					contains_4 = (node2, node1) in all_ties
					# Make sure you haven't already added (node1, node2) to your list of possible tie lines
					if (not contains_3) and (not contains_4):
						physical_dist = node_distance(circuit, node1, node2)
						path_dist = path_distance(circuit, node1, node2)
						all_ties[(node1, node2)] = [physical_dist, path_dist]
						# json cannot have tuples as keys, so make a new dict with string type keys
						json_key = ", ".join((node1, node2))
						all_ties_json[json_key] = [physical_dist, path_dist]
						tie_str = ", ".join(str(x) for x in all_ties[(node1, node2)])
						print("New addition to all_ties: (" + json_key + "): [" + tie_str + "]")
	# For testing purposes, save all_ties dict to a file to prevent LONG runtime of find_all_ties()
	ties_file_name = circuit_name+"_allTies.json"
	with open(pJoin(__neoMetaModel__._omfDir,"scratch",ties_file_name), 'w') as jsonFile:
		json.dump(all_ties_json, jsonFile)
	return all_ties

def find_candidate_pair(circuit, circuit_name, bus_limit, saved_ties):
	candidates = {}
	all_ties = {}
	short_phys_pair = ()
	short_phys_val = 0.0
	long_path_pair = ()
	long_path_val = 0.0
	phys_path_dif_pair = ()
	phys_path_dif_val = 0.0
	if saved_ties:
		# read in values from saved json file with all ties
		ties_file_name = circuit_name+"_allTies.json"
		try:
			with open(pJoin(__neoMetaModel__._omfDir,"scratch",ties_file_name), 'r') as tiesFile:
				all_ties_json = json.load(tiesFile)
				# Convert json string key back into tuple
				for tie_key in all_ties_json:
					if tie_key != "selected_buses":
						tuple_key = tuple(tie_key.split(", "))
						all_ties[tuple_key] = all_ties_json[tie_key]
					else:
						all_ties[tie_key] = all_ties_json[tie_key]
		except IOError as e:
			print("Error reading " + pJoin(__neoMetaModel__._omfDir,"scratch",ties_file_name) + ":")
			print(e)
			all_ties = find_all_ties(circuit, circuit_name, bus_limit=bus_limit)
		except:
			print("Unknown Error reading " + pJoin(__neoMetaModel__._omfDir,"scratch",ties_file_name) + ":")
			all_ties = find_all_ties(circuit, circuit_name, bus_limit=bus_limit)
	else:
		all_ties = find_all_ties(circuit, circuit_name, bus_limit=bus_limit)
	for tie in all_ties.keys():
		if tie != "selected_buses":
			#Find the tie with the shortest physical distance
			if short_phys_pair == ():
				short_phys_pair = tie
				short_phys_val = all_ties[tie][0]
			if long_path_pair == ():
				long_path_pair = tie
				long_path_val = all_ties[tie][1]
			if phys_path_dif_pair == ():
				phys_path_dif_pair = tie
				phys_path_dif_val = all_ties[tie][1] - all_ties[tie][0]
			if short_phys_val > all_ties[tie][0]:
				short_phys_pair = tie
				short_phys_val = all_ties[tie][0]
			if long_path_val < all_ties[tie][1]:
				long_path_pair = tie
				long_path_val = all_ties[tie][1]
			if phys_path_dif_val < all_ties[tie][1] - all_ties[tie][0]:
				phys_path_dif_pair = tie
				phys_path_dif_val = all_ties[tie][1] - all_ties[tie][0]
	candidates['short_phys_pair'] = short_phys_pair
	candidates['short_phys_val'] = short_phys_val
	candidates['long_path_pair'] = long_path_pair
	candidates['long_path_val'] = long_path_val
	candidates['phys_path_dif_pair'] = phys_path_dif_pair
	candidates['phys_path_dif_val'] = phys_path_dif_val
	candidates['selected_buses'] = all_ties["selected_buses"]

	return candidates

def add_tie_line(circuit, circuit_path, circuit_name, tie_line, create_copy=True, tie_circuit_name = None):
	lineOb_index = len(circuit["tree"])+1
	#create new line object for given tie line
	tie_from = tie_line[0]
	tie_to = tie_line[1]
	tie_name = "tie_" + tie_from + "_" + tie_to
	tie_length = node_distance(circuit, tie_from, tie_to)
	tie_info = {"object": "line",
				"name": tie_name,
				"from": tie_from,
				"to": tie_to,
				"!FROCODE": ".1.2.3",
				"!TOCODE": ".1.2.3",
				"phases": "3",
				"length": tie_length,
				"units": "km",
				"linecode": "ug_3p_type1"}
	circuit["tree"][lineOb_index] = tie_info
	if create_copy:
		# create new file in scratch folder
		if tie_circuit_name != None:
			omd_tie_name = tie_circuit_name
		else:
			omd_tie_name = circuit_name[:-4] + "." + tie_name + ".omd"
		full_circuit_path = pJoin(__neoMetaModel__._omfDir, "scratch", omd_tie_name)
		with open(full_circuit_path, 'w') as omdFile:
			json.dump(circuit, omdFile)
	else:
		# edit the original omd
		full_circuit_path = pJoin(circuit_path, circuit_name)
		with open(full_circuit_path, w) as omdFile:
			json.dump(circuit, omdFile)
	return full_circuit_path

def run_fault_study(circuit, tempFilePath, faultDetails=None):
	niceDss = dssConvert.evilGldTreeToDssTree(tree)
	dssConvert.treeToDss(niceDss, tempFilePath)
	#TODO: add fault, see Daniel.
	opendss.runDSS(tempFilePath)
	#TODO: look at the output files, see what happened to the loads.

def _runModel():
	circuit_path = pJoin(__neoMetaModel__._omfDir,"static","publicFeeders")
	circuit_name = "iowa240c1.clean.dss.omd"
	full_circuit_name = pJoin(circuit_path, circuit_name)
	with open(full_circuit_name, 'r') as omdFile:
		circuit = json.load(omdFile)
	# Test node_distance()
	load1 = "load_1003"
	load2 = "load_3019"
	dist_units = "km"
	dist1 = node_distance(circuit, load1, load2)
	dist2 = path_distance(circuit, load1, load2)
	print("Straight distance from " + load1 + " to " + load2 + " = " + str(dist1) + dist_units)
	if dist2 == -1.0:
		print(load1 + " and " + load2 + " are not connected.")
	else:
		print("Line distance from " + load1 + " to " + load2 + " = " + str(dist2) + dist_units)
	# Test find_all_ties()
	# all_ties_list = find_all_ties(circuit, circuit_name, bus_limit=5)
	# print("find_all_ties() completed!")
	# Test find_candidate_pair()
	potential_tie_lines = {}
	# potential_tie_lines = find_candidate_pair(circuit, circuit_name, bus_limit=3, saved_ties=False)
	potential_tie_lines = find_candidate_pair(circuit, circuit_name, bus_limit=3, saved_ties=True)
	# print("Potential tie lines: " + potential_tie_lines)
	print("Selected buses are " + str(potential_tie_lines['selected_buses']))
	print("Shortest physical distance between buses is " + '{0:.4f}'.format(potential_tie_lines['short_phys_val']) + "km between " + potential_tie_lines['short_phys_pair'][0] + " and " + potential_tie_lines['short_phys_pair'][1])
	print("Longest line distance between buses is " + '{0:.4f}'.format(potential_tie_lines['long_path_val']) + "km between " + potential_tie_lines['long_path_pair'][0] + " and " + potential_tie_lines['long_path_pair'][1])
	print("Greatest difference of line and physical distance between buses is " + '{0:.4f}'.format(potential_tie_lines['phys_path_dif_val']) + "km between " + potential_tie_lines['phys_path_dif_pair'][0] + " and " + potential_tie_lines['phys_path_dif_pair'][1])
	# Add the tie line(s) to the omd file and visualize
	tie_line_to_add = potential_tie_lines['phys_path_dif_pair']
	omd_with_tie_path = add_tie_line(circuit, circuit_path, circuit_name, tie_line_to_add, create_copy=True)
	# visualize original circuit
	distNetViz.viz(full_circuit_name, forceLayout=False, outputPath=None)
	# visualize circuit with tie line
	distNetViz.viz(omd_with_tie_path, forceLayout=False, outputPath=None)


if __name__ == '__main__':
	_runModel()
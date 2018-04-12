import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, math,copy
import multiprocessing, platform
from os.path import join as pJoin
from jinja2 import Template
import pprint as pprint
import matplotlib
import matplotlib.cm as cm
from matplotlib import pyplot as plt
import omf.network as network
import omf


# Read feeder and convert to .mat.
networkName = 'case9'
networkTestJson = json.load(open(pJoin("C:\Users\Justin Yang\Documents\Programming Projects\omf\omf\data\Model/admin\Automated Testing of transmission",networkName+".omt")))

def scaleCase9(networkJson, iterations):
	newBuses = {}
	newGens = {}
	newBranches ={}
	busCounter = 0
	for x in range(iterations):
		for key, bus in networkJson["bus"].iteritems():
			newKey = str(int(key) + busCounter)
			newBuses[newKey] = copy.deepcopy(bus)
			newBuses[newKey]["bus_i"] = newKey
		busCounter = busCounter + 9

	genCounter = 0
	for x in range(iterations):
		for key, gen in networkJson["gen"].iteritems():
			newKey = str(int(key) + genCounter)
			newGens[newKey] = copy.deepcopy(gen)
			newGens[newKey]["bus"] = newKey
		genCounter = genCounter + 9

	branchCounter = 0
	for x in range(iterations):
		for key, branch in networkJson["branch"].iteritems():
			newKey = str(int(key) + branchCounter)
			newBranches[newKey] = copy.deepcopy(branch)
			newBranches[newKey]["fbus"] = str(int(branch["fbus"]) + branchCounter)
			newBranches[newKey]["tbus"] = str(int(branch["tbus"]) + branchCounter)
		branchCounter = branchCounter + 9

	networkJson["bus"] = newBuses
	networkJson["gen"] = newGens
	networkJson["branch"] = newBranches

	matStr = network.netToMat(networkJson, networkName)
	with open("manyCase9Scaled.m","w") as outMat:
		for row in matStr: outMat.write(row)
	return networkJson

def runFDGTest(networkJson):
	nxG = network.netToNxGraph(networkJson)
	networkJson = network.latlonToNet(nxG, networkJson)
	with open("manyCase9FDGTest.omt",'w') as inFile:
	 	json.dump(networkJson, inFile)
	return networkJson

def scaleCase9ToMapbox(networkJson, iterations):
	objectTemplate = {
		"type" : "Feature",
		"properties" : {
			"title": "",
		},
		"geometry" : {
			"coordinates": [
			0,0
			],
			"type": ""
		}
	}

	geoJSON = {
		"features": [],
		"type" : "FeatureCollection"
	}

	busLong = {}
	busLat = {}

	busCounter = 0
	for x in range(iterations):
		for key, bus in networkJson["bus"].iteritems():
			newObject = copy.deepcopy(objectTemplate)
			newKey = str(int(key) + busCounter)
			newObject["properties"]["title"] = "Bus_"+ newKey
			newObject["geometry"]["coordinates"][0] = bus["longitude"]/1000
			newObject["geometry"]["coordinates"][1] = bus["latitude"]/1000
			busLong[newKey] = bus["longitude"]/1000
			busLat[newKey] = bus["latitude"]/1000
			newObject["geometry"]["type"] = "Point"
			newObject["properties"]["Va"] = bus["Va"]
			newObject["properties"]["Gs"] = bus["Gs"]
			newObject["properties"]["zone"] = bus["zone"]
			newObject["properties"]["Vmin"] = bus["Vmin"]
			newObject["properties"]["area"] = bus["area"]
			newObject["properties"]["Vm"] = bus["Vm"]
			newObject["properties"]["Vmax"] = bus["Vmax"]
			newObject["properties"]["Qd"] = bus["Qd"]
			newObject["properties"]["Pd"] = bus["Pd"]
			newObject["properties"]["Bs"] = bus["Bs"]
			newObject["properties"]["baseKV"] = bus["baseKV"]
			newObject["properties"]["type"] = bus["type"]
			geoJSON["features"].append(newObject)
		busCounter = busCounter + 9
	'''
	genCounter = 0
	for x in range(iterations):
		for key, gen in networkJson["gen"].iteritems():
			newObject = copy.deepcopy(objectTemplate)
			newKey = str(int(key) + busCounter)
			newObject["properties"]["title"] = "Bus_"+ newKey
			newObject["geometry"]["coordinates"][0] = bus["longitude"]/100
			newObject["geometry"]["coordinates"][1] = bus["latitude"]/100
			busLong[newKey] = bus["longitude"]/100
			busLat[newKey] = bus["latitude"]/100
			newObject["geometry"]["type"] = "Point"
			geoJSON["features"].append(newObject)
		genCounter = genCounter + 9
	'''
	branchCounter = 0
	for x in range(iterations):
		for key, branch in networkJson["branch"].iteritems():
			newObject = copy.deepcopy(objectTemplate)
			newKey = str(int(key) + branchCounter)
			newObject["properties"]["title"] = "Branch_"+ newKey
			newObject["geometry"]["coordinates"] = []
			newObject["geometry"]["coordinates"].append([busLong[branch["fbus"]], busLat[branch["fbus"]]]) 
			newObject["geometry"]["coordinates"].append([busLong[branch["tbus"]], busLat[branch["tbus"]]])
			newObject["geometry"]["type"] = "LineString"
			newObject["properties"]["status"] = branch["status"]
			newObject["properties"]["angmin"] = branch["angmin"]
			newObject["properties"]["b"] = branch["b"]
			newObject["properties"]["rateC"] = branch["rateC"]
			newObject["properties"]["rateB"] = branch["rateB"]
			newObject["properties"]["rateA"] = branch["rateA"]
			newObject["properties"]["angmax"] = branch["angmax"]
			newObject["properties"]["r"] = branch["r"]
			newObject["properties"]["x"] = branch["x"]
			newObject["properties"]["ratio"] = branch["ratio"]
			newObject["properties"]["angle"] = branch["angle"]
			geoJSON["features"].append(newObject)
		branchCounter = branchCounter + 9

	with open("case9GeoJSON.json", "w") as outFile:
		json.dump(geoJSON, outFile, indent=4)
	return networkJson

if __name__ == '__main__':
	testNetwork = scaleCase9(networkTestJson, 300)
	fdgNetwork = runFDGTest(testNetwork)
	scaleCase9ToMapbox(fdgNetwork, 1)
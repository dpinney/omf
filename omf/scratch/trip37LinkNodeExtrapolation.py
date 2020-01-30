import json, copy, random
from os.path import join as pJoin

from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

def highLow():
	feederName = "Simple Market System"
	with open(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", feederName + '.omd'), "r") as jsonIn:
		feederModel = json.load(jsonIn)

	highestX = -100000000000
	lowestX = 100000000000
	highestY =  -10000000000
	lowestY = 1000000000000

	for node in feederModel["nodes"]:
		if highestX < node["x"]:
			highestX = node["x"]

		if lowestX > node["x"]:
			lowestX = node["x"]

		if highestY < node["y"]:
			highestY = node["y"]

		if lowestY > node["y"]:
			lowestY = node["y"]

	print("highestX: " + str(highestX))
	print("lowestX: " + str(lowestX))
	print("highestY :" + str(highestY))
	print("lowestY: " + str(lowestY))


def function():
	feederName = "trip37"
	with open(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", feederName + '.omd'), "r") as jsonIn:
		feederModel = json.load(jsonIn)

	linkTemplate = {
		"source": {
			"index": 9,
			"name": "n630",
			"weight": 3,
			"px": 515.8855720607148,
			"py": 506.4381606171009,
			"objectType": "gridNode",
			"y": 506.4381606171009,
			"x": 515.8855720607148,
			"fixed": True,
			"chargeMultiple": 1,
			"treeIndex": 18
		}, 
		"treeIndex": 19, 
		"target": {
			"index": 12,
			"name": "tn_1",
			"weight": 2,
			"px": 509.61450605689737,
			"py": 511.73425866525673,
			"objectType": "triplex_node",
			"y": 511.73425866525673,
			"x": 509.61450605689737,
			"fixed": 1,
			"chargeMultiple": 1,
			"treeIndex": 23
		}, 
		"objectType": "fromTo"
	}
	
	'''
	LINE EXAMPLE
	"13": {
			"phases": "\"ABC\"",
			"from": "A_node711",
			"name": "TIE_A_to_C",
			"object": "underground_line",
			"to": "C_node707",
			"length": "400",
			"configuration": "lc_7231"
		},

	NODE EXAMPLE:
		"205": {
			"phases": "\"ABC\"",
			"name": "C_node707",
			"object": "node",
			"voltage_B": "-2400.000000 -1385.640646j",
			"voltage_C": "0.000000+2771.281292j",
			"voltage_A": "2400.000000 -1385.640646j",
			"nominal_voltage": "4800"
		},
		'''

	nodeTemplate = {
		"index": 0,
		"treeIndex": 8,
		"weight": 0,
		"px": 530.4008195466031,
		"py": 493.0561704740412,
		"y": 493.0561704740412,
		"x": 530.4008195466031,
		"fixed": True,
		"chargeMultiple": 1
	}

	nodeDict = {}
	typeDict = {}

	#two runthroughs are required, to populate all nodes before lines
	for key,value in feederModel["tree"].items():
		nodeIndexCounter = 0
		if "object" in value:
			typeDict[value["object"]] = value["object"]
			if value["object"] == "node" or value["object"] == "load":
				newNode = copy.deepcopy(nodeTemplate)
				newNode["treeIndex"] = key
				newNode["index"] = nodeIndexCounter
				newX = random.uniform(-72.8,-72.74) 
				newY = random.uniform(41.6, 41.65)
				newNode["px"] = newX
				newNode["py"] = newY
				newNode["x"] = newNode["px"]
				newNode["y"] = newNode["py"]
				nodeDict[value["name"]] = {"nodeIndex" : nodeIndexCounter, "treeIndex" : key, "objectType" : value["object"], "x": newX, "y": newY} #to help with line searching node indexes
				nodeIndexCounter = nodeIndexCounter + 1
				feederModel["nodes"].append(newNode)

			
	for key,value in feederModel["tree"].items():
		if "object" in value:
			if value["object"] == "underground_line" or value["object"] == "transformer":
				newLine = copy.deepcopy(linkTemplate)
				newLine["objectType"] = value["object"]
				sourceNodeName = value["from"]
				newLine["source"]["name"] = sourceNodeName
				newLine["source"]["treeIndex"] = nodeDict[sourceNodeName]["treeIndex"]
				newLine["source"]["index"] = nodeDict[sourceNodeName]["nodeIndex"]
				newLine["source"]["objectType"] = nodeDict[sourceNodeName]["objectType"]
				newLine["source"]["px"] = nodeDict[sourceNodeName]["x"]
				newLine["source"]["py"] = nodeDict[sourceNodeName]["y"]
				newLine["source"]["x"] = nodeDict[sourceNodeName]["x"]
				newLine["source"]["y"] =nodeDict[sourceNodeName]["y"]
				targetNodeName = value["to"]
				newLine["target"]["name"] = targetNodeName
				newLine["target"]["treeIndex"] = nodeDict[targetNodeName]["treeIndex"]
				newLine["target"]["index"] = nodeDict[targetNodeName]["nodeIndex"]
				newLine["target"]["objectType"] = nodeDict[targetNodeName]["objectType"]
				newLine["treeIndex"] = key
				newLine["target"]["px"] = nodeDict[targetNodeName]["x"]
				newLine["target"]["py"] = nodeDict[targetNodeName]["y"]
				newLine["target"]["x"] = nodeDict[targetNodeName]["x"]
				newLine["target"]["y"] =nodeDict[targetNodeName]["y"]
				feederModel["links"].append(newLine)

	print(typeDict)
	modelName = "resilientDist"
	with open(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", feederName + '_new.omd'), 'w') as outfile:
		json.dump(feederModel, outfile, indent = 4)


if __name__ == '__main__':
	highLow()
	function()

import csv, datetime as dt, json, subprocess
from matplotlib import pyplot as plt
import os, re, sys, shutil
import tempfile
from os.path import join as pJoin

# OMF imports
import feeder
from solvers import gridlabd

# Get SCADA data.
def _processScadaData(workDir,scadaPath):
	'''generate a SCADA player file from raw SCADA data'''
	with open(scadaPath,"r") as scadaFile:
		scadaReader = csv.DictReader(scadaFile, delimiter='\t')
		allData = [row for row in scadaReader]
	inputData = [float(row["power"]) for row in allData]
	# Write the player.
	maxPower = max(inputData)
	with open(pJoin(workDir,"subScada.player"),"w") as playFile:
		for row in allData:
			timestamp = dt.datetime.strptime(row["timestamp"], "%m/%d/%Y %H:%M:%S")
			power = float(row["power"]) / maxPower
			line = timestamp.strftime("%Y-%m-%d %H:%M:%S") + " PST," + str(power) + "\n"
			playFile.write(line)
	return inputData

def omfCalibrate(workDir,feeder_path,scadaPath):
	'''calibrates a feeder and saves the calibrated tree at a location'''
	jsonIn = json.load(open(feeder_path))
	tree = jsonIn.get("tree", {})
	inputData = _processScadaData(workDir,scadaPath)
	# Attach player.
	classOb = {"class":"player", "variable_names":["value"], "variable_types":["double"]}
	playerOb = {"object":"player", "property":"value", "name":"scadaLoads", "file":"subScada.player", "loop":"0"}
	maxKey = feeder.getMaxKey(tree)
	tree[maxKey+1] = classOb
	tree[maxKey+2] = playerOb
	# Make loads reference player.
	loadTemplate = {"object": "triplex_load",
		"power_pf_12": "0.95",
		"impedance_pf_12": "0.98",
		"power_pf_12": "0.90",
		"impedance_fraction_12": "0.7",
		"power_fraction_12": "0.3"}
	for key in tree:
		ob = tree[key]
		if ob.get("object","") == "triplex_node" and ob.get("power_12","") != "":
			newOb = dict(loadTemplate)
			newOb["name"] = ob.get("name", "")
			newOb["parent"] = ob.get("parent", "")
			newOb["phases"] = ob.get("phases", "")
			newOb["nominal_voltage"] = ob.get("nominal_voltage","")
			newOb["latitude"] = ob.get("latitude","0")
			newOb["longitude"] = ob.get("longitude","0")
			oldPow = ob.get("power_12","").replace("j","d")
			pythagPower = gridlabd._strClean(oldPow)
			newOb["base_power_12"] = "scadaLoads.value*" + str(pythagPower)
			tree[key] = newOb
	#search for the substation regulator
	for key in tree:
		if tree[key].get('bustype','').lower() == 'swing':
			swingIndex = key
			swingName = tree[key].get('name')
	for key in tree:
		if tree[key].get('object','') == 'regulator' and tree[key].get('from','') == swingName:
			regIndex = key
			SUB_REG_NAME = tree[key]['name']
	# Give it a test run.
	recOb = {"object": "recorder",
		"parent": SUB_REG_NAME,
		"property": "power_in.real, power_in.imag",
		"file": "outPower.csv",
		"interval": "900"}
	tree[maxKey + 3] = recOb
	# Creating a copy of the calibrated feeder in the outpath.
	with open(pJoin(workDir,"calibrated feeder.json"),"w") as outFile:
		json.dump(tree, outFile, indent=4)
	HOURS = 100
	feeder.adjustTime(tree, HOURS, "hours", "2011-01-01")
	glmFilePath = pJoin(workDir, "out.glm")
	with open(glmFilePath,"w") as outGlm:
		outGlm.write(feeder.sortedWrite(tree))
	# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!)
	output = gridlabd.runInFilesystem(tree,keepFiles=True,workDir=workDir)
	# Do some plotting.
	powerdata = output['outPower.csv']['power_in.real']
	#calculate scaling constant here
	SCAL_CONST = sum(powerdata)/sum(inputData[:len(powerdata)])
	scaledPowerData = []
	for element in powerdata:
		scaledPowerData.append(float(element)/SCAL_CONST)
	#TODO: rewrite the subScada.player file so all the power values are multiplied by the SCAL_CONSTANT.
	temp = []
	with open(pJoin(workDir,"subScada.player"),"r") as playerFile:
		for line in playerFile:
			(key,val) = line.split(',')
			temp.append(str(key) + ',' +str(float(val)*SCAL_CONST) + "\n")
	with open(pJoin(workDir,"subScada.player"),"w") as playerFile:
		for row in temp:
			playerFile.write(row)
	# plt.plot(range(len(powerdata)), scaledPowerData,range(len(powerdata)),inputData[:len(powerdata)])
	# plt.show()
	try:
		os.remove(pJoin(workDir, "main.glm"))
	except:
		pass # Main.glm failed to write.

def _tests():
	'''test function for ABEC Coloma and Frank feeders'''
	print "Beginning to test calibrate.py"
	workDir = tempfile.mkdtemp()
	print "currently working in", workDir
	scadaPath = pJoin("uploads","colScada.tsv")
	feeder_path = pJoin("data", "Feeder", "public","ABEC Frank LO.json")
	assert None == omfCalibrate(workDir,feeder_path,scadaPath), "feeder calibration failed"

if __name__ == '__main__':
	'''runs certain test functions for feeder calibration'''
	_tests()
import csv, datetime as dt, json, tempfile
from matplotlib import pyplot as plt
from os.path import join as pJoin
# OMF imports
import feeder
from solvers import gridlabd

def omfCalibrate(workDir, feederPath, scadaPath):
	'''calibrates a feeder and saves the calibrated tree at a location'''
	with open(feederPath, "r") as jsonIn:
		feederJson = json.load(jsonIn)
		tree = feederJson.get("tree", {})
	scadaSubPower, firstDateTime = _processScadaData(workDir,scadaPath)
	# Force FBS powerflow, because NR fails a lot.
	for key in tree:
		if tree[key].get("module","").lower() == "powerflow":
			tree[key] = {"module":"powerflow","solver_method":"FBS"}
	# Attach player.
	classOb = {'omftype':'class player','argument':'{double value;}'}
	playerOb = {"object":"player", "property":"value", "name":"scadaLoads", "file":"subScada.player", "loop":"0"}
	maxKey = feeder.getMaxKey(tree)
	playerKey = maxKey + 2
	tree[maxKey+1] = classOb
	tree[playerKey] = playerOb
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
	# Search for the substation regulator and attach a recorder there.
	for key in tree:
		if tree[key].get('bustype','').lower() == 'swing':
			swingName = tree[key].get('name')
	for key in tree:
		if tree[key].get('object','') in ['regulator', 'overhead_line', 'underground_line', 'transformer', 'fuse'] and tree[key].get('from','') == swingName:
			regIndex = key
			SUB_REG_NAME = tree[key]['name']
	recOb = {"object": "recorder",
		"parent": SUB_REG_NAME,
		"property": "power_in.real,power_in.imag",
		"file": "caliSub.csv",
		"interval": "900"}
	outputRecorderKey = maxKey + 3
	tree[outputRecorderKey] = recOb
	HOURS = 100
	feeder.adjustTime(tree, HOURS, "hours", firstDateTime.strftime("%Y-%m-%d"))
	# Run Gridlabd, calculate scaling constant.
	output = gridlabd.runInFilesystem(tree, keepFiles=True, workDir=workDir)
	outRealPow = output["caliSub.csv"]["power_in.real"]
	outImagPower = output["caliSub.csv"]["power_in.imag"]
	outAppPowerKw = [(x[0]**2 + x[1]**2)**0.5/1000 for x in zip(outRealPow, outImagPower)]
	previousFile = "subScada.player"
	nextFile = "subScadaCalibrated.player"
	nextPower = outAppPowerKw[1:HOURS]
	iterationTimes = 2
	for i in range(1, iterationTimes+1):
		# HACK: ignore first time step in output and input because GLD sometimes breaks the first step.
		SCAL_CONST = sum(scadaSubPower[1:HOURS])/sum(nextPower)
		# Rewrite the subScada.player file so all the power values are multiplied by the SCAL_CONSTANT.
		newPlayData = []
		with open(pJoin(workDir, previousFile), "r") as playerFile:
			for line in playerFile:
				(key,val) = line.split(',')
				newPlayData.append(str(key) + ',' + str(float(val)*SCAL_CONST) + "\n")
		with open(pJoin(workDir, nextFile), "w") as playerFile:
			for row in newPlayData:
				playerFile.write(row)
		# Test by running a glm with subScadaCalibrated.player and caliSub.csv2.
		tree[playerKey]["file"] = nextFile
		tree[outputRecorderKey]["file"] = "caliSubCheck.csv" #Note: this caliSubCheck.csv will be overwritten each iteration.
		nextOutput = gridlabd.runInFilesystem(tree, keepFiles=True, workDir=workDir)
		outRealPow2nd = nextOutput["caliSubCheck.csv"]["power_in.real"]
		outImagPower2nd = nextOutput["caliSubCheck.csv"]["power_in.imag"]
		nextAppKw = [(x[0]**2 + x[1]**2)**0.5/1000
			for x in zip(outRealPow2nd, outImagPower2nd)]
		# Set the in and out playerFiles and out power for the next iteration.
		previousFile = nextFile
		nextFile = "subScadaCalibrated"+str(i)+".player"
		nextPower = nextAppKw[1:HOURS]
	plt.figure()
	plt.plot(outAppPowerKw[1:HOURS], label="initialGuess")
	plt.plot(scadaSubPower[1:HOURS], label="scadaSubPower")
	plt.plot(nextAppKw[1:HOURS], label="finalGuess")
	plt.legend(loc=3)
	plt.savefig(pJoin(workDir,"caliCheckPlot.png"))
	# Write the final output.
	with open(pJoin(workDir,"calibratedFeeder.json"),"w") as outJson:
		playerString = open(pJoin(workDir,previousFile)).read()
		feederJson["attachments"][previousFile] = playerString
		feederJson["tree"] = tree
		json.dump(feederJson, outJson, indent=4)
	return

def _processScadaData(workDir,scadaPath):
	'''generate a SCADA player file from raw SCADA data'''
	with open(scadaPath,"r") as scadaFile:
		scadaReader = csv.DictReader(scadaFile, delimiter='\t')
		allData = [row for row in scadaReader]
	scadaSubPower = [float(row["power"]) for row in allData]
	firstDateTime = dt.datetime.strptime(allData[1]["timestamp"], "%m/%d/%Y %H:%M:%S")
	# Write the player.
	maxPower = max(scadaSubPower)
	with open(pJoin(workDir,"subScada.player"),"w") as playFile:
		for row in allData:
			timestamp = dt.datetime.strptime(row["timestamp"], "%m/%d/%Y %H:%M:%S")
			power = float(row["power"]) / maxPower
			line = timestamp.strftime("%Y-%m-%d %H:%M:%S") + " PST," + str(power) + "\n"
			playFile.write(line)
	return scadaSubPower, firstDateTime

def _tests():
	print "Beginning to test calibrate.py"
	workDir = tempfile.mkdtemp()
	print "Currently working in: ", workDir
	scadaPath = pJoin("uploads", "FrankScada.tsv")
	feederPath = pJoin("data", "Feeder", "public","ABEC Frank pre calib.json")
	assert None == omfCalibrate(workDir, feederPath, scadaPath), "feeder calibration failed"

if __name__ == '__main__':
	_tests()
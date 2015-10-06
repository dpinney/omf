import csv, datetime as dt, json, tempfile
from matplotlib import pyplot as plt
from os.path import join as pJoin
# OMF imports
import feeder
from solvers import gridlabd
import random

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

def attachVolts(workDir, feederPath, voltVectorA, voltVectorB, voltVectorC):
	'''read voltage vectors of 3 different phases, run gridlabd, and attach output to the feeder.'''
	try:
		timeStamp = [dt.datetime.strptime('01/01/2011 00:00:00', "%m/%d/%Y %H:%M:%S")]
		for x in range (1, 8760):
			timeStamp.append(timeStamp[x-1] + dt.timedelta(hours=1))
		firstDateTime = timeStamp[1]
		with open(pJoin(workDir,"phaseAVoltage.player"),"w") as voltFile:
			for x in range(0, 8760):
				timestamp = timeStamp[x]
				voltage = str("%0.2f"%float(voltVectorA[x]))+"+0j"
				line = timestamp.strftime("%Y-%m-%d %H:%M:%S") + " PST," + str(voltage) + "\n"
				voltFile.write(line)
		with open(pJoin(workDir,"phaseBVoltage.player"),"w") as voltFile:
			for x in range(0, 8760):
				timestamp = timeStamp[x]
				voltage = str("%0.2f"%float(voltVectorB[x]))+"-"+str("%0.4f"%float(random.uniform(6449,6460)))+"j"
				line = timestamp.strftime("%Y-%m-%d %H:%M:%S") + " PST," + str(voltage) + "\n"
				voltFile.write(line)
		with open(pJoin(workDir,"phaseCVoltage.player"),"w") as voltFile:
			for x in range(0, 8760):
				timestamp = timeStamp[x]
				voltage = str("%0.2f"%float(voltVectorC[x]))+"+"+str("%0.4f"%float(random.uniform(6449,6460)))+"j"
				line = timestamp.strftime("%Y-%m-%d %H:%M:%S") + " PST," + str(voltage) + "\n"
				voltFile.write(line)
		with open(feederPath, "r") as jsonIn:
			feederJson = json.load(jsonIn)
			tree = feederJson.get("tree", {})
		# Find swingNode name.
		for key in tree:
			if tree[key].get('bustype','').lower() == 'swing':
				swingName = tree[key].get('name')
		# Attach player.
		classOb = {'omftype':'class player','argument':'{double value;}'}
		voltageObA = {"object":"player", "property":"voltage_A", "file":"phaseAVoltage.player", "loop":"0", "parent":swingName}
		voltageObB = {"object":"player", "property":"voltage_B", "file":"phaseBVoltage.player", "loop":"0", "parent":swingName}
		voltageObC = {"object":"player", "property":"voltage_C", "file":"phaseCVoltage.player", "loop":"0", "parent":swingName}
		maxKey = feeder.getMaxKey(tree)
		voltplayerKeyA = maxKey + 2
		voltplayerKeyB = maxKey + 3
		voltplayerKeyC = maxKey + 4
		tree[maxKey+1] = classOb
		tree[voltplayerKeyA] = voltageObA
		tree[voltplayerKeyB] = voltageObB
		tree[voltplayerKeyC] = voltageObC
		# Adjust time and run output.
		HOURS = 100
		feeder.adjustTime(tree, HOURS, "hours", firstDateTime.strftime("%Y-%m-%d"))
		output = gridlabd.runInFilesystem(tree, keepFiles=True, workDir=workDir)
		# Write the output.
		with open(pJoin(workDir,"calibratedFeeder.json"),"w") as outJson:
			playerStringA = open(pJoin(workDir,"phaseAVoltage.player")).read()
			playerStringB = open(pJoin(workDir,"phaseBVoltage.player")).read()
			playerStringC = open(pJoin(workDir,"phaseCVoltage.player")).read()
			feederJson["attachments"]["phaseAVoltage.player"] = playerStringA
			feederJson["attachments"]["phaseBVoltage.player"] = playerStringB
			feederJson["attachments"]["phaseCVoltage.player"] = playerStringC
			feederJson["tree"] = tree
			json.dump(feederJson, outJson, indent=4)
		return pJoin(workDir,"calibratedFeeder.json"), True
	except:
		return feederPath, False

def _tests():
	print "Beginning to test calibrate.py"
	workDir = tempfile.mkdtemp()
	print "Currently working in: ", workDir
	scadaPath = pJoin("uploads", "FrankScada.csv")
	feederPath = pJoin("data", "Feeder", "public","ABEC Frank pre calib.json")
	voltVectorA = [random.uniform(7380,7620) for x in range(0,8760)]
	voltVectorC = [-random.uniform(3699,3780) for x in range(0, 8760)]
	voltVectorB = [-random.uniform(3699,3795) for x in range(0, 8760)]
	calibFeederPath, outcome = attachVolts(workDir, feederPath, voltVectorA, voltVectorB, voltVectorC)
	if outcome == False: print "\n   attachVolts failed."
	assert None == omfCalibrate(workDir, calibFeederPath, scadaPath), "feeder calibration failed"

if __name__ == '__main__':
	_tests()
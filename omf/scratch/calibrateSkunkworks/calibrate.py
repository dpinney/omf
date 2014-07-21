import csv, datetime as dt, json, subprocess
from matplotlib import pyplot as plt
import os, re, sys

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(_myDir)
print _omfDir
sys.path.append(_omfDir)

# OMF imports
sys.path.append(_omfDir)
import feeder
import feederCalibrate
from solvers import gridlabd


# Get SCADA data.
def getScadaData(SCADA_FNAME,PQPLAYER_FNAME,VPLAYER_FNAME=None):
	'''generate a SCADA player file from raw SCADA data'''
	with open(SCADA_FNAME,"r") as scadaFile:
		scadaReader = csv.DictReader(scadaFile, delimiter='\t')
		allData = [row for row in scadaReader]

	inputData = [float(row["power"]) for row in allData]

	# Write the player.
	maxPower = max(inputData)
	with open(PQPLAYER_FNAME,"w") as playFile:
		for row in allData:
			timestamp = dt.datetime.strptime(row["timestamp"], "%m/%d/%Y %H:%M:%S")
			power = float(row["power"]) / maxPower
			line = timestamp.strftime("%Y-%m-%d %H:%M:%S") + " PST," + str(power) + "\n"
			playFile.write(line)

	return inputData

# Get tree.
def _calibrateFeeder(inputData,FEEDER_FNAME,PQPLAYER_FNAME,VPLAYER_FNAME=None):
	'''calibrates a feeder and saves the calibrated tree at a location'''
	jsonIn = json.load(open(FEEDER_FNAME))
	tree = jsonIn.get("tree", {})

	# Attach player.
	classOb = {"class":"player", "variable_names":["value"], "variable_types":["double"]}
	playerOb = {"object":"player", "property":"value", "name":"scadaLoads", "file":PQPLAYER_FNAME, "loop":"0"}
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
			newOb["latitude"] = ob.get("latitude","")
			newOb["longitude"] = ob.get("longitude","")
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
	for key in tree.keys():
		try:
			del tree[key]["latitude"]
			del tree[key]["longitude"]
		except:
			pass # No lat lons.

	feeder.adjustTime(tree, 100, "hours", "2011-01-01")
	with open("out.glm","w") as outGlm:
		outGlm.write(feeder.sortedWrite(tree))
	proc = subprocess.Popen(['gridlabd', "-w", "out.glm"])
	proc.wait()


	#calculate scaling constant here
	SCAL_CONST = 300.0

	# Do some plotting.
	listdict = []
	with open("outPower.csv","r") as outcsvFile:
		for i,line in enumerate(outcsvFile):
			if i > 8:
				listdict.append(line)

	tempdata = []
	for row in listdict:
		tempdata.append(row.split(','))


	powerdata = []
	for rowt in tempdata:
		powerdata.append(float(rowt[1])/SCAL_CONST)

	plt.plot
	plt.plot(range(len(powerdata)), powerdata,range(len(powerdata)),inputData[:len(powerdata)])
	plt.show()

	return None

def omfCalibrate(FEEDER_FNAME,SCADA_FNAME,PQPLAYER_FNAME,VPLAYER_FNAME=None):
	'''calls _calibrateFeeder and gets the work done'''
	inputData = getScadaData(SCADA_FNAME,PQPLAYER_FNAME,VPLAYER_FNAME) 
	_calibrateFeeder(inputData,FEEDER_FNAME,PQPLAYER_FNAME,VPLAYER_FNAME) #passing input data for scaling 

	return None


def _tests():
	'''test function for ABEC Coloma and Frank feeders'''
	SCADA_FNAME = "colScada.tsv"
	PQPLAYER_FNAME = "scada.player"
	FEEDER_FNAME = "ABEC Frank Lo.json"
	#SUB_REG_NAME = "REG27"

	omfCalibrate(FEEDER_FNAME,SCADA_FNAME,PQPLAYER_FNAME)

	return None



if __name__ == '__main__':
	'''runs certain test functions for feeder calibration'''
	_tests()
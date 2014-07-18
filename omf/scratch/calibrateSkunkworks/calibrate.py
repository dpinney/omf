import csv, datetime as dt, json, subprocess
import omf
from matplotlib import pyplot as plt

SCADA_FNAME = "colScada.tsv"
PLAYER_FNAME = "scada.player"
FEEDER_FNAME = "ABEC Columbia.json"
SUB_REG_NAME = "Coloma Bus Regs"

# Get SCADA data.
with open(SCADA_FNAME,"r") as scadaFile:
	scadaReader = csv.DictReader(scadaFile, delimiter='\t')
	allData = [row for row in scadaReader]

# Write the player.
maxPower = max([float(row["power"]) for row in allData])
with open(PLAYER_FNAME,"w") as playFile:
	for row in allData:
		timestamp = dt.datetime.strptime(row["timestamp"], "%m/%d/%Y %H:%M:%S")
		power = float(row["power"]) / maxPower
		line = timestamp.strftime("%Y/%m/%d %H:%M:%S") + " EDT," + str(power) + "\n"
		playFile.write(line)

# Get tree.
jsonIn = json.load(open(FEEDER_FNAME))
tree = jsonIn.get("tree", {})

# Attach player.
classOb = {"class":"player", "variable_names":["value"], "variable_types":["double"]}
playerOb = {"object":"player", "property":"value", "name":"scadaLoads", "file":PLAYER_FNAME, "loop":"0"}
maxKey = omf.feeder.getMaxKey(tree)
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
		pythagPower = omf.solvers.gridlabd._strClean(oldPow)
		newOb["base_power_12"] = "scadaLoads.value*" + str(pythagPower)
		tree[key] = newOb

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
omf.feeder.adjustTime(tree, 1, "days", "2013-01-01")
with open("out.glm","w") as outGlm:
	outGlm.write(omf.feeder.sortedWrite(tree))
proc = subprocess.Popen(['gridlabd', "-w", "out.glm"])
proc.wait()

# Do some plotting.
plt.plot([float(row["power"]) for row in allData[:1000]])
plt.show()

# WHAT NEXT? csv to table format.


'''

object triplex_node {
	phases BS;
	power_12 8845.18+4792.29j;
	name S1807-25-012_B;
	parent nodeS1807-25-0111807-25-003_B;
	longitude 263.276266686;
	nominal_voltage 120;
	latitude 605.788600445;
};

object triplex_load {
	phases BS;
	name 99330306_B_loadshape;
	parent node99330306T99330306_B;
	power_pf_12 residential_power_pfB.value*0.946486;
	impedance_pf_12 0.970000;
	current_pf_12 0.970000;
	impedance_fraction_12 0.000000;
	current_fraction_12 0.000000;
	nominal_voltage 120.0;
	power_fraction_12 1.000000;
	base_power_12 norm_feeder_loadshape.value*3291.537058;
};

'''
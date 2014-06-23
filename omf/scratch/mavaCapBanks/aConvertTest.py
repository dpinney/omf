import omf, json
from matplotlib import pyplot as plt

def convert():
	with open("fGOOD-25-01_new.seq","r") as seqFile, open("fGOOD-25-01_new.std","r") as stdFile:
		seqString = seqFile.read()
		stdString = stdFile.read() 
	(tree, x, y) = omf.milToGridlab.convert(stdString, seqString)
	# BUGFIX: transformer impedances with zero reactances cause powerflow failure.
	for key in tree:
		if tree[key].get("object","") == "transformer_configuration":
			tree[key]["impedance"] = tree[key]["impedance"].replace("+0.0j","+0.0022j")
			print "Replaced zero reactance in", tree[key].get("name")
	with open("faNewestConversion.json","w") as outFile:
		json.dump(tree, outFile, indent=4)
	with open("faNewestConversion.glm","w") as outFile:
		outFile.write(omf.feeder.sortedWrite(tree))

def powerTest():
	with open("faNewestConversion.json", "r") as inFile:
		tree = json.load(inFile)
	output = omf.solvers.gridlabd.runInFilesystem(tree)
	with open("bOutput.json","w") as outFile:
		json.dump(output,outFile, indent=4)

def draw():
	with open("faNewestConversion.json", "r") as inFile:
		tree = json.load(inFile)
	graph = omf.feeder.treeToNxGraph(tree)
	omf.feeder.latLonNxGraph(graph)
	plt.show()

if __name__ == '__main__':
	powerTest()
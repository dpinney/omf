''' Grab Simple Market System from our data store and write out the glms for it. '''
import omf, json, os

def feedJsonToFiles():
	feedJson = json.load(open("./ABEC Frank Calibrated.json"))
	with open("AVEC Frank Calibrated.glm","w") as outFile:
		outFile.write(omf.feeder.sortedWrite(feedJson["tree"]))
	for name in feedJson["attachments"].keys():
		with open(name, "w") as outFile:
			outFile.write(feedJson["attachments"][name])

if __name__ == '__main__':
	feedJsonToFiles()

# NOTE: you need to put a tmy file named "climate.tmy2" in this folder.
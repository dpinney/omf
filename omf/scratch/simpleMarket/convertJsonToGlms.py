''' Grab Simple Market System from our data store and write out the glms for it. '''
import omf, json, os

feedJson = json.load(open("../../data/Feeder/public/Simple Market System.json"))

with open("sms.glm","w") as outFile:
	outFile.write(omf.feeder.sortedWrite(feedJson["tree"]))

with open("schedules.glm","w") as outSched:
	outSched.write(feedJson["attachments"]["schedules.glm"])

# NOTE: you need to put a tmy file named "climate.tmy2" in this folder.
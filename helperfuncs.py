
"""These are helper functions used in web.py"""

# os.path.join is supposed to be a platform independent way to do paths, although our unix paths seem to work on windows, but also I personally find it annoying to do the string concats everywhere, and it'll git rid of errors where we forget to add a slash.  I made a really obvious variable name so that we don't have to type out the whole thing, but we know exactly which function it is.
import os
import json
OS_PJ = os.path.join

def feederDump(owner, name, data):
	convOrFeedDump("Feeder", owner, name, data)
	
def conversionDump(owner, name, data):
	convOrFeedDump("Conversion", owner, name, data)

def conversionPath(owner, name):
	return convOrFeedPath("Conversion", owner, name)
	
def convOrFeedDump(objType, owner, name, data):
	json.dump(data, open(convOrFeedPath(objType, owner, name), "w"))

def convOrFeedPath(objType, owner, name):
	return OS_PJ("data", objType, owner, name+".json")

def feederPath(owner, name):
	return convOrFeedPath("Feeder", owner, name)

def modelPath(owner, name):
	return OS_PJ("data", "Model", owner, name)

def objIn(objectName, directory, mapfunc=lambda x: x):
	# I repeat this idiom frequently: objectName in [f.replace(".json", "") for f in os.listdir("data/Feeder/public")]
	# To do the same with this function you would do:
	# objIn(objectName, "data/Feeder/public", lambda f: f.replace(".json", ""))
	# Or to do objectName in os.listdir("data/Model/public")
	# You would simply do:
	# objIn(objectName, "data/Model/public")
	# I think this will make our code cleaner and safer and more concise
	return objectName in map(mapfunc, os.listdir(directory))

def nojson(objectType, directory):
	# A wrapper for objIn.  I remove ".json" from the end of files a lot
	return objIn(objectName, directory, lambda x: x.replace(".json", ""))

def pubhelper(objectType, objectName):
	# publicObject was poorly thought out and it returns "Yep"/"Nope" instead of simply true/false, so this is a helper that just returns a boolean value that is used in the actual view function to return "Yep"/"Nope"
	if objectType == "Feeder":
		return nojson(objectName, "data/Feeder/public")
	elif objectType == "Model":
		return objIn(objectName, "data/Model/public") # heck this one could also use nojson and it would be the same thing.... maybe default should be to use nojson and then we always have the underlying objIn if we want something more specific?

import json

with open('metadata.js','r') as jsonFile:
	jsonFile.readline() # Burn one.
	print json.load(jsonFile)
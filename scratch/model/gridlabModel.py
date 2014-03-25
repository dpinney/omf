import json

with open('metadata.js','r') as jsonFile:
	jsonFile.readline() # Burn one.
	print json.load(jsonFile)

def showModel():
	''' Render the model template. '''
	pass

def saveModel():
	''' Save the model template. '''
	pass

def runModel():
	''' Run the model. '''
	pass

def deleteModel():
	pass
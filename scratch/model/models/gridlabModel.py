import json, os
myDir = os.path.dirname(__file__)

with open(myDir + "/gridlabModel.html","r") as tempFile:
	template = tempFile.read()

def showModel(inputDataDictionary, outputDataDictionary):
	''' Render the model template. '''
	pass

def runModel(workingDirectory, inputDataDictionary):
	''' Run the model. '''
	# Make a directory. Put files into it. Translate files to needed format. Run Gridlab.
	pass

def readingJsonExample():
	with open('metadata.js','r') as jsonFile:
		jsonFile.readline() # Burn one.
		print json.load(jsonFile)

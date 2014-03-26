import json, os, sys, tempfile, webbrowser, time
from jinja2 import Template

_myDir = os.path.dirname(__file__)
# TODO: import feeder.py, etc.
# sys.path.append(os.path.dirname(_myDir))

with open(_myDir + "/gridlabSingle.html","r") as tempFile:
	template = Template(tempFile.read())

userInput = {
	"modelName": "Single Gridlab Run",
	"simLength": "2048",
	"simLengthUnits": "hours",
	"simStartDate": "2014-01-01"
}
userInputNeedsTranslation = {
	"feederName": "Test Feeder",
	"climateName": "Test Climate"
}
machineInput = {
	"status": None, 
	"created": None,
	"modelType": "gridlabSingle",
	"runTime": None
}

def renderTemplate(workingDirectory="", absolutePaths=False):
	''' Render the model template. By default render a blank one for new input.
	If workingDirectory is valid, render results post-model-run.
	If absolutePaths, the HTML can be opened without a server. '''
	try:
		with open(workingDirectory + '/allInputData.json','r') as inFile:
			allInputData = inFile.read()
		with open(workingDirectory + '/allOutputData.json','r') as outFile:
			allOutputData = outFile.read()
	except IOError:
		allInputData = None
		allOutputData = None
	if absolutePaths:
		# Parent of current folder.
		pathPrefix = os.path.dirname(_myDir)
	else:
		pathPrefix = ""
	return template.render(allInputData=allInputData, allOutputData=allOutputData,
		pathPrefix=pathPrefix)

def create(workingDirectory, inputDataDictionary):
	name = inputDataDictionary['modelName']
	with open(os.path.join(workDir, 'allInputData.json'),'w') as inputFile:
		json.dump(inputDataDictionary, inputFile)

def run(workingDirectory):
	''' Run the model. '''
	if inputDataDictionary:
		# Create a new model
		setup(workingDirectory)
	else:
		# Re-run existing model.
		pass
	# Make a directory. Put files into it. Translate files to needed format. Run Gridlab.

def _tests():
	# Test rendering a no-input template:
	with tempfile.NamedTemporaryFile() as temp:
		temp.write(renderTemplate(absolutePaths=True))
		temp.flush()
		os.rename(temp.name, temp.name + '.html')
		fullArg = 'file://' + temp.name + '.html'
		webbrowser.open(fullArg)
		# It's going to SPACE! Could you give it a SECOND to get back from SPACE?!
		time.sleep(1)
	# Render completed template.
	with tempfile.NamedTemporaryFile() as temp:
		testDir = os.path.dirname(_myDir) + '/data/Model/Single Gridlab Run'
		temp.write(renderTemplate(workingDirectory=testDir, absolutePaths=True))
		temp.flush()
		os.rename(temp.name, temp.name + '.html')
		fullArg = 'file://' + temp.name + '.html'
		webbrowser.open(fullArg)
		time.sleep(1)

if __name__ == '__main__':
	_tests()
from flask import Flask, send_from_directory
from jinja2 import Template
import models, json

app = Flask(__name__)

# Debug section
print "Available models: " + str(models.__all__)

# URLS
@app.route("/")
def mainScreen():
	return "This is the home screen."

@app.route("/newModel/<modelType>")
def newModel(modelType):
	''' Display the module template for creating a new model. '''
	return getattr(models, modelType).renderTemplate()

@app.route("/runModel/")
def runModel():
	pass

@app.route("/model/<modelName>")
def showModel(modelName):
	''' Render a model template with saved data. '''
	workDir = './data/Model/' + modelName + '/'
	with open(workDir + 'allInputData.json') as inJson:
		modelType = json.load(inJson)['modelType']
	return getattr(models, modelType).renderTemplate(workingDirectory=workDir)

if __name__ == '__main__':
	app.run(debug=True)

from flask import Flask, send_from_directory
from jinja2 import Template
import models, json, os

app = Flask(__name__)

# URLS
@app.route("/")
def mainScreen():
	outStr = "New model of type: " + ', '.join(models.__all__) + "</br>"
	outStr += "Instances: " + ', '.join(os.listdir("./data/Model/"))
	return outStr

@app.route("/newModel/<modelType>")
def newModel(modelType):
	''' Display the module template for creating a new model. '''
	return getattr(models, modelType).renderTemplate()

@app.route("/runModel/", methods=['POST'])
def runModel():
	pData = flask.request.form.to_dict()

@app.route("/model/<modelName>")
def showModel(modelName):
	''' Render a model template with saved data. '''
	workDir = './data/Model/' + modelName + '/'
	with open(workDir + 'allInputData.json') as inJson:
		modelType = json.load(inJson)['modelType']
	return getattr(models, modelType).renderTemplate(workingDirectory=workDir)

if __name__ == '__main__':
	app.run(debug=True)

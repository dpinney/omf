from flask import Flask, send_from_directory
from jinja2 import Template
import models

app = Flask(__name__)

# Debug section
print "Available models: " + str(models.__all__)

# URLS
@app.route("/")
def mainScreen():
	return "This is the home screen."

@app.route("/newModel/<modelName>")
def newModel(modelName):
	''' Display the module template for creating a new model. '''
	return getattr(models, modelName).renderTemplate()

@app.route("/model/<savedModelName>")
def showModel(savedModelName):
	''' Render a model template with saved data. '''
	pass

if __name__ == '__main__':
	app.run()

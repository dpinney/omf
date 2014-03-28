''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request
from jinja2 import Template
import models, json, os

app = Flask(__name__)

homeTemplate = '''
<body>
	<p>New Model of Type:</p>
	{% for x in modTypes %}
		<a href='/newModel/{{ x }}'>{{ x }}</a>
	{% endfor %}
	<p>Instances:</p>
	{% for x in instances %}
		<a href='/model/{{ x }}'>{{ x }}</a>
	{% endfor %}
</body>
'''

def getDataNames():
	''' Query the OMF datastore to list all the names of things we might need.'''
	feeders = [x[0:-5] for x in os.listdir('./data/Feeder/')]
	climates = [x[0:-5] for x in os.listdir('./data/Weather/')]
	return 	{'feeders':feeders, 'climates':climates}

# URLS
@app.route("/")
def mainScreen():
	return Template(homeTemplate).render(modTypes=models.__all__,
		instances=os.listdir('./data/Model/'))

@app.route("/newModel/<modelType>")
def newModel(modelType):
	''' Display the module template for creating a new model. '''
	return getattr(models, modelType).renderTemplate(datastoreNames=getDataNames())

@app.route("/runModel/", methods=['POST'])
def runModel():
	pData = request.form.to_dict()
	return str(pData)

@app.route("/model/<modelName>")
def showModel(modelName):
	''' Render a model template with saved data. '''
	workDir = './data/Model/' + modelName + '/'
	with open(workDir + 'allInputData.json') as inJson:
		modelType = json.load(inJson)['modelType']
	return getattr(models, modelType).renderTemplate(workingDirectory=workDir,
		datastoreNames=getDataNames())



if __name__ == '__main__':
	# TODO: remove debug code.
	app.run(debug=True, extra_files=['./models/gridlabSingle.html'])

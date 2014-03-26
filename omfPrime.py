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

# URLS
@app.route("/")
def mainScreen():
	return Template(homeTemplate).render(modTypes=models.__all__,
		instances=os.listdir('./data/Model/'))

@app.route("/newModel/<modelType>")
def newModel(modelType):
	''' Display the module template for creating a new model. '''
	return getattr(models, modelType).renderTemplate()

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
	return getattr(models, modelType).renderTemplate(workingDirectory=workDir)

if __name__ == '__main__':
	app.run(debug=True)

#!/bin/python

import flask
import os
import multiprocessing
import analysis as da
import json
import treeParser as tp
import shutil
import reports

app = flask.Flask(__name__)

class backgroundProc(multiprocessing.Process):
	def __init__(self, analysisName):
		self.analysisName = analysisName
		multiprocessing.Process.__init__(self)
	def run(self):
		da.run(self.analysisName)

####################################################
# VIEWS
####################################################

@app.route('/')
def root():
	analyses = da.listAll()
	metadatas = [da.getMetadata(x) for x in analyses]
	return flask.render_template('home.html', metadatas=metadatas)

@app.route('/newAnalysis/')
def newAnalysis():
	# Get lists of various things:
	tmy2s = os.listdir('tmy2s')
	feeders = os.listdir('feeders')
	reportList = reports.listAll()
	return flask.render_template('newAnalysis.html', tmy2s=tmy2s, feeders=feeders, reportList=reportList)

@app.route('/viewReports/<analysisName>')
def viewReports(analysisName):
	# Get some variables.
	reportFiles = os.listdir('analyses/' + analysisName + '/reports/')
	reportList = []
	# Iterate over reports and collect what we need: 
	for report in reportFiles:
		# call the relevant reporting function by name.
		try:
			reportFunc = getattr(reports, report.replace('.txt',''))
			reportList.append(reportFunc(analysisName))
		except:
			# there's no report matching the saved file...
			pass
	reportsJson = json.dumps(reportList)
	return flask.render_template('viewReports.html', analysisName=analysisName, reportsJson=reportsJson)

@app.route('/model/<model_id>')
def show_model(model_id):
	return flask.render_template('gridEdit.html', model_id=model_id)

####################################################
# API FUNCTIONS
####################################################

@app.route('/run/', methods=['POST'])
@app.route('/reRun/', methods=['POST'])
def run():
	runProc = backgroundProc(flask.request.form['analysisName'])
	runProc.start()
	return flask.redirect(flask.url_for('root'))

@app.route('/delete/', methods=['POST'])
def delete():
	da.delete(flask.request.form['analysisName'])
	return flask.redirect(flask.url_for('root'))

@app.route('/saveAnalysis/', methods=['POST'])
def saveAnalysis():
	postData = json.loads(flask.request.form.to_dict()['json'])
	print postData
	da.createAnalysis(postData['analysisName'], int(postData['simLength']), postData['simLengthUnits'], postData['simStartDate'], postData['studies'], postData['reports'])
	return flask.redirect(flask.url_for('root'))

@app.route('/terminate/', methods=['POST'])
def terminate():
	da.terminate(flask.request.form['analysisName'])
	return flask.redirect(flask.url_for('root'))

@app.route('/api/models/<model_id>.json')
def api_model(model_id):
	#check file system or check for GLM file
	if model_id+'.json' in os.listdir('./json'):
		in_file = file('./json/' + model_id + '.json', 'r')
		as_json = in_file.read()
		return as_json
	elif model_id in os.listdir('./feeders'):
		tree = tp.parse('./feeders/' + model_id + '/main.glm')
		nodes = []
		links = []
		filesAvailable = os.listdir('./feeders/' + model_id)
		if 'nodes.json' in filesAvailable and 'links.json' in filesAvailable:
			with open('./feeders/' + model_id + '/nodes.json') as nodesFile, open('./feeders/' + model_id + '/links.json') as linksFile:
				nodes = json.loads(nodesFile.read())
				links = json.loads(linksFile.read())
			# cache the file for later
			with open('./json/' + model_id + '.json', 'w') as out:
				out.write(json.dumps({'tree':tree, 'nodes':nodes, 'links':links}))
		jsonLoad = json.dumps({'tree':tree, 'nodes':nodes, 'links':links})
		return jsonLoad
	return ''

@app.route('/getComponents/')
def getComponents():
	compFiles = os.listdir('./components/')
	components = {}
	for fileName in compFiles:
		with open('./components/' + fileName,'r') as compFile:
			fileContents = compFile.read()
			components[fileName] = eval(fileContents)
	print components
	return json.dumps(components)

@app.route('/saveFeeder/', methods=['POST'])
def updateGlm():
	postData = flask.request.form.to_dict()
	sourceFeeder = str(postData['feederName'])
	newFeeder = str(postData['newName'])	
	allFeeders = os.listdir('./feeders/')
	tree = json.loads(postData['tree'])
	# Nodes and links are the information about how the feeder is layed out.
	nodes = postData['nodes']
	links = postData['links']
	if newFeeder not in allFeeders:
		# if we've created a new feeder, copy over the associated files:
		shutil.copytree('./feeders/' + sourceFeeder,'./feeders/' + newFeeder)
	else:
		# else if we've saved an existing feeder we might need to blow away the cached json:
		if newFeeder + '.json' in os.listdir('./json/'):
			os.remove('./json/' + newFeeder + '.json')
	with open('./feeders/' + newFeeder + '/main.glm','w') as newMainGlm, open('./feeders/' + newFeeder + '/nodes.json','w') as newNodes, open('./feeders/' + newFeeder + '/links.json','w') as newLinks:
		newMainGlm.write(tp.sortedWrite(tree))
		newNodes.write(nodes)
		newLinks.write(links)
	return flask.redirect(flask.url_for('newAnalysis'))

# This will run on all interface IPs.
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug='False', port=5001)
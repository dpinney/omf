#!/bin/python

import flask
import os
import threading
import analysis as da
import json
import treeParser as tp
import grapher as tg
import shutil
import reports

app = flask.Flask(__name__)

class backgroundThread(threading.Thread):
	def __init__(self, analysisName):
		self.analysisName = analysisName
		threading.Thread.__init__(self)
	def run(self):
		da.run(self.analysisName)

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
	reportFiles = os.listdir('static/analyses/' + analysisName + '/reports/')
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

@app.route('/run/', methods=['POST'])
@app.route('/reRun/', methods=['POST'])
def run():
	runThread = backgroundThread(flask.request.form['analysisName'])
	runThread.start()
	return flask.redirect(flask.url_for('root'))

@app.route('/delete/', methods=['POST'])
def delete():
	da.delete(flask.request.form['analysisName'])
	return flask.redirect(flask.url_for('root'))

@app.route('/saveAnalysis/', methods=['POST'])
def saveAnalysis():
	postData = json.loads(flask.request.form.to_dict()['json'])
	print postData
	da.createAnalysis(postData['analysisName'], int(postData['simLength']), postData['simLengthUnits'], postData['studies'], postData['reports'])
	return flask.redirect(flask.url_for('root'))

@app.route('/terminate/', methods=['POST'])
def terminate():
	da.terminate(flask.request.form['analysisName'])
	return flask.redirect(flask.url_for('root'))

@app.route('/model/<model_id>')
def show_model(model_id):
	return flask.render_template('gridEdit.html', model_id=model_id)

@app.route('/api/models/<model_id>.json')
def api_model(model_id):
	#check file system or check for GLM file
	if model_id+'.json' in os.listdir('./json'):
		in_file = file('./json/' + model_id + ".json", "r")
		as_json = in_file.read()
		return as_json
	elif model_id in os.listdir('./feeders'):
		tree = tp.parse('./feeders/' + model_id + "/main.glm")
		# cache the file for later
		out = file('./json/' + model_id + ".json", "w")
		jsonTree = json.dumps(tree)
		out.write(jsonTree)
		out.close()
		return jsonTree
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
	tree = json.loads(postData['tree'])
	shutil.copytree('./feeders/' + sourceFeeder,'./feeders/' + newFeeder)
	os.remove('./feeders/' + newFeeder + '/main.glm')
	with open('./feeders/' + newFeeder + '/main.glm','w') as newMainGlm:
		newMainGlm.write(tp.sortedWrite(tree))
	return flask.redirect(flask.url_for('newStudy'))

# This will run on all interface IPs.
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug='False', port=5001)
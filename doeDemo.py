#!/bin/python

import flask
import os
import threading
import doeAnalysis as da
import json
import treeParser as tp
import doeGrapher as tg
import shutil

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
	# Get all the template TMY2s available.
	tmy2s = os.listdir('tmy2s')
	# Get all the template feeders available.
	feeders = os.listdir('feeders')
	return flask.render_template('newAnalysis.html', tmy2s=tmy2s, feeders=feeders)

@app.route('/viewReports/<analysisName>')
def viewReports(analysisName):
	pngs = [x for x in os.listdir('static/analyses/' + analysisName) if x.endswith('.png')]
	# Get the stdout, stderr from the gridlabd run:
	stdout = open('static/analyses/' + analysisName + '/stdout.txt', 'r')
	profile = ''.join(stdout.readlines())
	# Hack: drop leading \r newlines:
	profile = profile.replace('\r','')
	stdout.close()
	return flask.render_template('viewReports.html', analysisName=analysisName, pngs=pngs, profile=profile)

@app.route('/reRun/', methods=['POST'])
def reRun():
	runThread = backgroundThread(flask.request.form['analysisName'])
	runThread.start()
	return flask.redirect(flask.url_for('root'))

@app.route('/run/', methods=['POST'])
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
	da.create(flask.request.form.to_dict())
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

@app.route('/saveFeeder/', methods=['POST'])
def updateGlm():
	postData = flask.request.form.to_dict()
	sourceFeeder = str(postData['feederName'])
	newFeeder = sourceFeeder + '-1'
	tree = json.loads(postData['tree'])
	shutil.copytree('./feeders/' + sourceFeeder,'./feeders/' + newFeeder)
	os.remove('./feeders/' + newFeeder + '/main.glm')
	with open('./feeders/' + newFeeder + '/main.glm','w') as newMainGlm:
		newMainGlm.write(tp.sortedWrite(tree))
	return flask.redirect(flask.url_for('newAnalysis'))

@app.route('/ECHOPOST/', methods=['POST'])
def ECHOPOST():
	postData = flask.request.form.to_dict()
	return str(postData)

# This will run on all interface IPs.
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug='False', port=5001)
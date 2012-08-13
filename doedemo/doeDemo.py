#!/bin/python

import flask
import os
import threading
import doeAnalysis as da
import models
import json
import treeParser as tp
import doeGrapher as tg

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
	print flask.request.form.to_dict()
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
    #check file system
    #or, check for GLM file
    if model_id+'.json' in os.listdir('./files/json'):
        in_file = file('./files/json/' + model_id + ".json", "r")
        as_json = in_file.read()
        return as_json
    elif model_id+'.glm' in os.listdir('./files/glms'):
        parsed = tp.parse('./files/glms/' + model_id + ".glm")
        graph = tg.node_groups(parsed)
        # cache the file for later
        out = file('./files/json/' + model_id + ".json", "w")
        graph_json = tg.to_d3_json(graph)
        as_json = json.dumps(graph_json)
        out.write(as_json)
        out.close()
        return as_json
    return ''
	# return render_template('default_model.json')

@app.route('/api/objects')
def api_objects():
    all_types = filter(lambda x: x[0] is not '_', dir(models))
    # all_types = ['House', 'Triplex Meter', 'Meter', 'Node', 'Load']
    return json.dumps(all_types)
    # defaults = map(lambda x: getattr(models, x)().__dict__, all_types)
    # print defaults
    # return json.dumps(defaults)



# This will run on all interface IPs.
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug='False', port=5001)
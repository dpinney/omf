#!/bin/python

import flask
import os
import multiprocessing
import analysis
import json
import feeder
import shutil
import time
import reports
import studies
import lib
from werkzeug import secure_filename
import milToGridlab
import threading, thread
# import logging_system
import storage

app = flask.Flask(__name__)

store = storage.Filestore('data')

class backgroundProc(multiprocessing.Process):
	def __init__(self, backFun, funArgs):
		self.name = 'omfWorkerProc'
		self.backFun = backFun
		self.funArgs = funArgs
		multiprocessing.Process.__init__(self)
	def run(self):
		self.backFun(*self.funArgs)

class background_thread(threading.Thread):
    def __init__(self, backFun, funArgs):
        threading.Thread.__init__(self)
        self.backFun = backFun
        self.funArgs = funArgs
         
    def run(self):
        self.backFun(*self.funArgs)

###################################################
# VIEWS
###################################################

#COMPLETED!!!
@app.route('/')
def root():
	browser = flask.request.user_agent.browser
	metadatas = [store.getMetadata('Analysis', x) for x in store.listAll('Analysis')]
	feeders = store.listAll('Feeder')
	conversions = store.listAll('Conversion')
	if browser == 'msie':
		return 'The OMF currently must be accessed by Chrome, Firefox or Safari.'
	else:
		return flask.render_template('home.html', metadatas=metadatas, feeders=feeders, conversions=conversions)

@app.route('/newAnalysis/')
@app.route('/newAnalysis/<analysisName>')
def newAnalysis(analysisName=None):
	# Get some prereq data:
	tmy2s = store.listAll('Weather')
	feeders = store.listAll('Feeder')
	analyses = store.listAll('Analysis')
	reportTemplates = reports.__templates__
	studyTemplates = studies.__templates__
	studyRendered = {}
	for study in studyTemplates:
		studyRendered[study] = str(flask.render_template_string(studyTemplates[study], tmy2s=tmy2s, feeders=feeders))
	# If we aren't specifying an existing name, just make a blank analysis:
	if analysisName is None or analysisName not in analyses:
		existingStudies = None
		existingReports = None
		analysisMd = None
	# If we specified an analysis, get the studies, reports and analysisMd:
	else:
		# TODO: implement this.
		analysisMd = store.getMetadata('Analysis', analysisName)
		analysis = store.get('Analysis', analysisName)
		reportDicts = [json.loads(lib.fileSlurp(reportPrefix + x)) for x in reportNames]
		existingReports = json.dumps(reportDicts)
		studyNames = os.listdir(studyPrefix)
		studyDicts = [json.loads(lib.fileSlurp(studyPrefix + x + '/metadata.json')) for x in studyNames]
		existingStudies = json.dumps(studyDicts)
	return flask.render_template('newAnalysis.html', studyTemplates=studyRendered, reportTemplates=reportTemplates, existingStudies=existingStudies, existingReports=existingReports, analysisMd=analysisMd)

#COMPLETED!!!
@app.route('/viewReports/<analysisName>')
def viewReports(analysisName):
	if not store.exists('Analysis', analysisName):
		return flask.redirect(flask.url_for('root'))
	reportList = analysis.Analysis(analysisName, store.getMetadata('Analysis',analysisName), store.get('Analysis',analysisName)).generateReportHtml()
	return flask.render_template('viewReports.html', analysisName=analysisName, reportList=reportList)

#COMPLETED!!!
@app.route('/feeder/<feederName>')
def feederGet(feederName):
	return flask.render_template('gridEdit.html', feederName=feederName, anaFeeder=False)

#COMPLETED!!!
@app.route('/analysisFeeder/<analysis>/<study>')
def analysisFeeder(analysis, study):
	return flask.render_template('gridEdit.html', feederName=analysis+'---'+study, anaFeeder=True)


####################################################
# API FUNCTIONS
####################################################

#COMPLETED!!!
@app.route('/uniqueName/<name>')
def uniqueName(name):
	return json.dumps(name not in store.listAll('Analysis'))

#COMPLETED!!!
@app.route('/run/', methods=['POST'])
@app.route('/reRun/', methods=['POST'])
def run():
	anaName = flask.request.form.get('analysisName')
	anaInstance = analysis.Analysis(anaName, store.getMetadata('Analysis', anaName), store.get('Analysis', anaName))
	anaInstance.status = 'running'
	store.put('Analysis', anaInstance.name, mdDict=anaInstance.mdToJson())
	runProc = backgroundProc(analysisRun, [anaInstance, store])
	runProc.start()
	return flask.render_template('metadata.html', md=anaInstance.mdToJson())

#COMPLETED!!!
# Helper function to run an analyses in a new process.
def analysisRun(anaInstance, store):
	anaInstance.run()
	store.put('Analysis', anaInstance.name, mdDict=anaInstance.mdToJson(), jsonDict=anaInstance.toJson())
	for study in anaInstance.studies:
		store.put('Study', study.analysisName + '---' + study.name, mdDict=study.mdToDict(), jsonDict=study.toDict())

@app.route('/delete/', methods=['POST'])
def delete():
	analysis.delete(flask.request.form['analysisName'])
	return flask.redirect(flask.url_for('root'))

@app.route('/saveAnalysis/', methods=['POST'])
def saveAnalysis():
	postData = json.loads(flask.request.form.to_dict()['json'])
	analysis.create(postData['analysisName'], int(postData['simLength']), postData['simLengthUnits'], postData['simStartDate'], postData['studies'], postData['reports'])
	return flask.redirect(flask.url_for('root'))

@app.route('/terminate/', methods=['POST'])
def terminate():
	analysis.terminate(flask.request.form['analysisName'])
	return flask.redirect(flask.url_for('root'))

#COMPLETED!!!
@app.route('/feederData/<anaFeeder>/<feederName>.json')
def feederData(anaFeeder, feederName):
	if anaFeeder == 'True':
		data = store.get('Study',feederName)['inputJson']
		del data['attachments']
		return json.dumps(data)
	else:
		return json.dumps(store.get('Feeder', feederName))

#COMPLETED!!!
@app.route('/getComponents/')
def getComponents():
	components = {name:store.get('Component', name) for name in store.listAll('Component')}
	return json.dumps(components, indent=4)

#COMPLETED!!!
@app.route('/saveFeeder/', methods=['POST'])
def saveFeeder():
	postObject = flask.request.form.to_dict()
	store.put('Feeder', str(postObject['name']), jsonDict=json.loads(postObject['feederObjectJson']), mdDict=None)
	return flask.redirect(flask.url_for('root') + '#feeders')

#COMPLETED!!!
@app.route('/runStatus')
def runStatus():
	name = flask.request.args.get('name')
	md = store.getMetadata('Analysis', name)
	if md['status'] != 'running':
		return flask.render_template('metadata.html', md=md)
	else:
		return flask.Response("waiting", content_type="text/plain")

@app.route('/milsoftImport/', methods=['POST'])
def milsoftImport():
	feederName = str(flask.request.form.to_dict()['feederName'])
	stdName = ''
	seqName = ''
	allFiles = flask.request.files
	for f in allFiles:
		fName = secure_filename(allFiles[f].filename)
		if fName.endswith('.std'): stdName = fName
		elif fName.endswith('.seq'): seqName = fName
		allFiles[f].save('./uploads/' + fName)
	runProc = backgroundProc(milToGridlab.omfConvert, [feederName, stdName, seqName])
	runProc.start()
	time.sleep(1)
	return flask.redirect(flask.url_for('root') + '#feeders')

# This will run on all interface IPs.
if __name__ == '__main__':
	# thread_logging = background_thread(logging_system.logging_system(app).logging_run, (app,))
	# thread_logging.start()
	app.run(host='0.0.0.0', debug=True, port=5001, threaded=True)

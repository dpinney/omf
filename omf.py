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
import datetime

app = flask.Flask(__name__)

store = storage.Filestore('data')

class backgroundProc(multiprocessing.Process):
	def __init__(self, backFun, funArgs):
		self.name = 'omfWorkerProc'
		self.backFun = backFun
		self.funArgs = funArgs
		self.myPid = os.getpid()
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
		analysisMd = json.dumps(store.getMetadata('Analysis', analysisName))
		analysisData = store.get('Analysis', analysisName)
		existingReports = json.dumps(analysisData['reports'])
		#TODO: remove analysis name from study names. Dang DB keys.
		existingStudies = json.dumps([store.getMetadata('Study', analysisName + '---' + studyName) for studyName in analysisData['studyNames']])
	return flask.render_template('newAnalysis.html', studyTemplates=studyRendered, reportTemplates=reportTemplates, existingStudies=existingStudies, existingReports=existingReports, analysisMd=analysisMd)

@app.route('/viewReports/<analysisName>')
def viewReports(analysisName):
	if not store.exists('Analysis', analysisName):
		return flask.redirect(flask.url_for('root'))
	thisAnalysis = analysis.Analysis(store.getMetadata('Analysis',analysisName), store.get('Analysis',analysisName))
	#TODO: support non-Gridlab studies.
	studyList = [studies.gridlabd.Gridlabd(studyName, thisAnalysis.name, store.getMetadata('Study', thisAnalysis.name + '---' + studyName), store.get('Study', thisAnalysis.name + '---' + studyName)) for studyName in thisAnalysis.studyNames]
	reportList = thisAnalysis.generateReportHtml(studyList)
	return flask.render_template('viewReports.html', analysisName=analysisName, reportList=reportList)

@app.route('/feeder/<feederName>')
def feederGet(feederName):
	return flask.render_template('gridEdit.html', feederName=feederName, anaFeeder=False)

@app.route('/analysisFeeder/<analysis>/<study>')
def analysisFeeder(analysis, study):
	return flask.render_template('gridEdit.html', feederName=analysis+'---'+study, anaFeeder=True)


####################################################
# API FUNCTIONS
####################################################

@app.route('/uniqueName/<name>')
def uniqueName(name):
	return json.dumps(name not in store.listAll('Analysis'))

@app.route('/run/', methods=['POST'])
@app.route('/reRun/', methods=['POST'])
def run():
	anaName = flask.request.form.get('analysisName')
	anaMd = store.getMetadata('Analysis', anaName)
	anaMd['status'] = 'running'
	store.put('Analysis', anaName, mdDict=anaMd)
	runProc = backgroundProc(analysisRun, [anaName, store])
	runProc.start()
	return flask.render_template('metadata.html', md=anaMd)

# Helper function to run an analyses in a new process.
def analysisRun(anaName, store):
	anaInstance = analysis.Analysis(store.getMetadata('Analysis', anaName), store.get('Analysis', anaName))
	anaInstance.status = 'running'
	#TODO: support non-Gridlab studies.
	studyList = [studies.gridlabd.Gridlabd(studyName, anaInstance.name, store.getMetadata('Study', anaInstance.name + '---' + studyName), store.get('Study', anaInstance.name + '---' + studyName)) for studyName in anaInstance.studyNames]
	anaInstance.run(studyList)
	store.put('Analysis', anaInstance.name, mdDict=anaInstance.mdToJson(), jsonDict=anaInstance.toJson())
	for study in anaInstance.studies:
		store.put('Study', study.analysisName + '---' + study.name, mdDict=study.mdToDict(), jsonDict=study.toDict())

@app.route('/delete/', methods=['POST'])
def delete():
	anaName = flask.request.form['analysisName']
	# Delete studies.
	childStudies = [x for x in store.listAll('Study') if x.startswith(anaName + '---')]
	for study in childStudies:
		store.delete('Study', study)
	# Delete analysis.
	store.delete('Analysis', anaName)
	return flask.redirect(flask.url_for('root'))

@app.route('/saveAnalysis/', methods=['POST'])
def saveAnalysis():
	pData = json.loads(flask.request.form.to_dict()['json'])
	#TODO: unique string join.
	def uniqJoin(stringList):
		return ', '.join(set(stringList))
	anaMetadata = {	'status':'preRun',
					'sourceFeeder':uniqJoin([stud['feederName'] for stud in pData['studies']]),
					'climate':uniqJoin([stud['tmy2name'] for stud in pData['studies']]),
					'created':str(datetime.datetime.now()),
					'simStartDate':pData['simStartDate'],
					'simLength':pData['simLength'],
					'simLengthUnits':pData['simLengthUnits'],
					'runTime':'' }
	anaData = {	'reports':pData['reports'],
				'studyNames':[stud['studyName'] for stud in pData['studies']] }
	store.put('Analysis', pData['analysisName'], mdDict=anaMetadata, jsonDict=anaData)
	for study in pData['studies']:
		if study['studyType'] == 'gridlabd':
			studyMd = {	'studyType':'gridlabd',
						'simLength':pData['simLength'],
						'simLengthUnits':pData['simLengthUnits'],
						'simStartDate':pData['simStartDate'],
						'sourceFeeder':study['feederName'],
						'climate':study['tmy2name'],
						'analysisName':pData['analysisName'] }
			studyFeeder = store.get('Feeder', study['feederName'])
			studyFeeder['attachments']['climate.tmy2'] = store.get('Weather', study['tmy2name']+'.tmy2', raw=True)
			studyData = {'inputJson':studyFeeder,'outputJson':{}}
			studyObj = studies.gridlabd.Gridlabd(study['studyName'], pData['analysisName'], studyMd, studyData, new=True)
			store.put('Study', pData['analysisName'] + '---' + study['studyName'], mdDict=studyObj.mdToDict(), jsonDict=studyObj.toDict())
		elif study['studyType'] == 'XXX':
			#TODO: implement me.
			pass
	return flask.redirect(flask.url_for('root'))

@app.route('/terminate/', methods=['POST'])
def terminate():
	anaName = flask.request.form['analysisName']
	for runDir in os.listdir('running'):
		if runDir.startswith(anaName + '---'):
			try:
				with open('running/' + runDir + '/PID.txt','r') as pidFile:
					os.kill(int(pidFile.read()), 15)
			except:
				pass
	return flask.redirect(flask.url_for('root'))

@app.route('/feederData/<anaFeeder>/<feederName>.json')
def feederData(anaFeeder, feederName):
	if anaFeeder == 'True':
		data = store.get('Study',feederName)['inputJson']
		del data['attachments']
		return json.dumps(data)
	else:
		return json.dumps(store.get('Feeder', feederName))

@app.route('/getComponents/')
def getComponents():
	components = {name:store.get('Component', name) for name in store.listAll('Component')}
	return json.dumps(components, indent=4)

@app.route('/saveFeeder/', methods=['POST'])
def saveFeeder():
	postObject = flask.request.form.to_dict()
	store.put('Feeder', str(postObject['name']), jsonDict=json.loads(postObject['feederObjectJson']), mdDict=None)
	return flask.redirect(flask.url_for('root') + '#feeders')

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
	runProc = backgroundProc(milImportAndConvert, [store, feederName, stdName, seqName])
	runProc.start()
	time.sleep(1)
	return flask.redirect(flask.url_for('root') + '#feeders')

def milImportAndConvert(store, feederName, stdName, seqName):
	store.put('Conversion', feederName, {'data':'none'})
	newFeeder = {'links':[],'hiddenLinks':[],'nodes':[],'hiddenNodes':[],'layoutVars':{'theta':'0.8','gravity':'0.01','friction':'0.9','linkStrength':'5'}}
	newFeeder['tree'] = milToGridlab.convert('./uploads/' + stdName, './uploads/' + seqName)
	with open('./schedules.glm','r') as schedFile:
		newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
	store.put('Feeder', feederName, newFeeder)
	store.delete('Conversion', feederName)

# This will run on all interface IPs.
if __name__ == '__main__':
	# thread_logging = background_thread(logging_system.logging_system(app).logging_run, (app,))
	# thread_logging.start()
	app.run(host='0.0.0.0', debug=True, port=5001, threaded=True)

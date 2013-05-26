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
import otherObjects
import threading, thread
# import logging_system

app = flask.Flask(__name__)

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

@app.route('/')
def root():
	browser = flask.request.user_agent.browser
	analyses = analysis.listAll()
	feeders = feeder.listAll()
	conversions = otherObjects.listAllConversions()
	metadatas = [analysis.getMetadata(x) for x in analyses]
	#DEBUG: print metadatas
	if browser == 'msie':
		return 'The OMF currently must be accessed by Chrome, Firefox or Safari.'
	else:
		return flask.render_template('home.html', metadatas=metadatas, feeders=feeders, conversions=conversions)

@app.route('/newAnalysis/')
@app.route('/newAnalysis/<analysisName>')
def newAnalysis(analysisName=None):
	# Get some prereq data:
	tmy2s = otherObjects.listAllWeather()
	feeders = feeder.listAll()
	reportTemplates = reports.__templates__
	studyTemplates = studies.__templates__
	studyRendered = {}

	for study in studyTemplates:
		studyRendered[study] = str(flask.render_template_string(studyTemplates[study], tmy2s=tmy2s, feeders=feeders))

	analyses = analysis.listAll()
	# If we aren't specifying an existing name, just make a blank analysis:
	if analysisName is None or analysisName not in analyses:
		existingStudies = None
		existingReports = None
		analysisMd = None
	# If we specified an analysis, get the studies, reports and analysisMd:
	else:

		reportPrefix = 'analyses/' + analysisName + '/reports/'
		reportNames = os.listdir(reportPrefix)
		reportDicts = [json.loads(lib.fileSlurp(reportPrefix + x)) for x in reportNames]
		existingReports = json.dumps(reportDicts)
		studyPrefix = 'analyses/' + analysisName + '/studies/'
		studyNames = os.listdir(studyPrefix)
		studyDicts = [json.loads(lib.fileSlurp(studyPrefix + x + '/metadata.json')) for x in studyNames]

		existingStudies = json.dumps(studyDicts)
		analysisMd = json.dumps(analysis.getMetadata(analysisName))
	return flask.render_template('newAnalysis.html', studyTemplates=studyRendered, reportTemplates=reportTemplates, existingStudies=existingStudies, existingReports=existingReports, analysisMd=analysisMd)

@app.route('/viewReports/<analysisName>')
def viewReports(analysisName):
	if not analysis.is_name_of_analysis(analysisName):
		return flask.redirect(flask.url_for('root'))
	reportList = analysis.generateReportHtml(analysisName)
	return flask.render_template('viewReports.html', analysisName=analysisName, reportList=reportList)

@app.route('/feeder/<feederName>')
def feederGet(feederName):
	return flask.render_template('gridEdit.html', feederName=feederName, path='feeders')

@app.route('/analysisFeeder/<analysis>/<study>')
def analysisFeeder(analysis, study):
	return flask.render_template('gridEdit.html', feederName=study, path='analyses/' + analysis + '/studies/')


####################################################
# API FUNCTIONS
####################################################

@app.route('/uniqueName/<name>')
def uniqueName(name):
	return json.dumps(not analysis.is_name_of_analysis(name))

@app.route('/run/', methods=['POST'])
@app.route('/reRun/', methods=['POST'])
def run():
	runProc = backgroundProc(analysis.run, [flask.request.form['analysisName']])
	runProc.start()
	time.sleep(1)
	return flask.redirect(flask.url_for('root'))

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

@app.route('/feederData/<path:path>/<feederName>.json')
def api_model(path, feederName):
	fullPrefix = './' + path + '/'
	# check for JSON model:
	if feederName in os.listdir(fullPrefix) and 'main.json' in os.listdir(fullPrefix + feederName):
		with open(fullPrefix + feederName + '/main.json') as jsonFile:
			return jsonFile.read()
	elif feederName in os.listdir(fullPrefix):
		# Grab data from filesystem:
		tree = feeder.parse(fullPrefix + feederName + '/main.glm')
		outDict = {'tree':tree, 'nodes':[], 'links':[], 'hiddenNodes':[], 'hiddenLinks':[], 'layoutVars':{'gravity':'0.1','theta':'0.8','friction':'0.9','linkStrength':'1'}}
		# cache the file for later
		jsonLoad = json.dumps(outDict, indent=4)
		with open(fullPrefix + feederName + '/main.json', 'w') as jsonOut:
			jsonOut.write(jsonLoad)
		return jsonLoad
	else:
		# Failed to find the feeder:
		return ''

@app.route('/getComponents/')
def getComponents():
	components = otherObjects.getAllComponents()
	return json.dumps(components, indent=4)

@app.route('/saveFeeder/', methods=['POST'])
def updateGlm():
	postData = flask.request.form.to_dict()
	sourceFeeder = str(postData['feederName'])
	newFeeder = str(postData['newName'])	
	allFeeders = feeder.listAll()
	tree = json.loads(postData['tree'])
	# Nodes and links are the information about how the feeder is layed out.
	nodes = json.loads(postData['nodes'])
	hiddenNodes = json.loads(postData['hiddenNodes'])
	links = json.loads(postData['links'])
	hiddenLinks = json.loads(postData['hiddenLinks'])
	layoutVars = json.loads(postData['layoutVars'])
	if newFeeder not in allFeeders:
		# if we've created a new feeder, copy over the associated files:
		shutil.copytree('./feeders/' + sourceFeeder,'./feeders/' + newFeeder)
	with open('./feeders/' + newFeeder + '/main.glm','w') as newMainGlm, open('./feeders/' + newFeeder + '/main.json','w') as jsonCache:
		newMainGlm.write(feeder.sortedWrite(tree))
		outDict = {'tree':tree, 'nodes':nodes, 'links':links, 'hiddenNodes':hiddenNodes, 'hiddenLinks':hiddenLinks, 'layoutVars':layoutVars}
		json.dump(outDict, jsonCache, indent=4)
	return flask.redirect(flask.url_for('root') + '#feeders')

@app.route('/runStatus/')
def runStatus():
	''' Gives all analysis MD info. Useful for updating home.html automatically. '''
	analyses = analysis.listAll()
	statuses = {ana:analysis.getMetadata(ana)['status'] for ana in analysis.listAll()}
	return json.dumps(statuses)

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
	app.run(host='0.0.0.0', debug=False, port=5001)

#!/bin/python

import flask
import os
import multiprocessing
import analysis
import json
import treeParser as tp
import shutil
import time
import reports
import lib

app = flask.Flask(__name__)

class backgroundProc(multiprocessing.Process):
	def __init__(self, analysisName):
		self.analysisName = analysisName
		multiprocessing.Process.__init__(self)
	def run(self):
		analysis.run(self.analysisName)

###################################################
# VIEWS
###################################################

@app.route('/')
def root():
	browser = flask.request.user_agent.browser
	analyses = analysis.listAll()
	feeders = tp.listAll()
	metadatas = [analysis.getMetadata(x) for x in analyses]
	#DEBUG: print metadatas
	if browser == 'msie':
		return "The OMF currently must be accessed by Chrome, Firefox or Safari."
	else:
		return flask.render_template('home.html', metadatas=metadatas, feeders=feeders)

@app.route('/newAnalysis/')
@app.route('/newAnalysis/<analysisName>')
def newAnalysis(analysisName=None):
	# Get some prereq data:
	tmy2s = os.listdir('tmy2s')
	feeders = os.listdir('feeders')
	reportTemplates = reports.__templates__
	analyses = os.listdir('analyses')
	# If we aren't specifying an existing name, just make a blank analysis:
	if analysisName is None or analysisName not in analyses:
		existingStudies = None
		existingReports = None
		analysisMd = None
	# If we specified an analysis, get the studies, reports and analysisMd:
	else:
		reportPrefix = 'analyses/' + analysisName + '/reports/'
		reportNames = os.listdir(reportPrefix)
		reportDicts = [eval(lib.fileSlurp(reportPrefix + x)) for x in reportNames]
		existingReports = json.dumps(reportDicts)
		studyPrefix = 'analyses/' + analysisName + '/studies/'
		studyNames = os.listdir(studyPrefix)
		studyDicts = [eval(lib.fileSlurp(studyPrefix + x + '/metadata.txt')) for x in studyNames]
		existingStudies = json.dumps(studyDicts)
		analysisMd = eval(lib.fileSlurp('analyses/' + analysisName + '/metadata.txt'))
	return flask.render_template('newAnalysis.html', tmy2s=tmy2s, feeders=feeders, reportTemplates=reportTemplates, existingStudies=existingStudies, existingReports=existingReports, analysisMd=analysisMd)

@app.route('/viewReports/<analysisName>')
def viewReports(analysisName):
	# Get some variables.
	reportFiles = os.listdir('analyses/' + analysisName + '/reports/')
	reportList = []
	# Iterate over reports and collect what we need: 
	for report in reportFiles:
		# call the relevant reporting function by name.
		reportModule = getattr(reports, report.replace('.txt',''))
		reportList.append(reportModule.outputHtml(analysisName))
	return flask.render_template('viewReports.html', analysisName=analysisName, reportList=reportList)

@app.route('/model/<model_id>')
def show_model(model_id):
	return flask.render_template('gridEdit.html', model_id=model_id, analysisModel=False)

@app.route('/analysisModel/<anaNameDotStudy>')
def showAnalysisModel(anaNameDotStudy):
	anaName = anaNameDotStudy.split('.')[0]
	study = anaNameDotStudy.split('.')[-1]
	model_id = analysis.getMetadata(anaName + '/studies/' + study)['sourceFeeder']
	return flask.render_template('gridEdit.html', model_id=model_id, anaName=anaName, study=study)

####################################################
# API FUNCTIONS
####################################################

@app.route('/run/', methods=['POST'])
@app.route('/reRun/', methods=['POST'])
def run():
	runProc = backgroundProc(flask.request.form['analysisName'])
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
	#DEBUG: print postData
	analysis.createAnalysis(postData['analysisName'], int(postData['simLength']), postData['simLengthUnits'], postData['simStartDate'], postData['studies'], postData['reports'])
	return flask.redirect(flask.url_for('root'))

@app.route('/terminate/', methods=['POST'])
def terminate():
	analysis.terminate(flask.request.form['analysisName'])
	return flask.redirect(flask.url_for('root'))

@app.route('/api/models/<model_id>.json')
def api_model(model_id):
	# check for JSON model:
	if model_id in os.listdir('./feeders/') and 'main.json' in os.listdir('./feeders/' + model_id):
		with open('./feeders/' + model_id + '/main.json') as jsonFile:
			return jsonFile.read()
	elif model_id in os.listdir('./feeders/'):
		# Grab data from filesystem:
		tree = tp.parse('./feeders/' + model_id + '/main.glm')
		outDict = {'tree':tree, 'nodes':[], 'links':[], 'hiddenNodes':[], 'hiddenLinks':[]}
		# cache the file for later
		jsonLoad = json.dumps(outDict, indent=4)
		with open('./feeders/' + model_id + '/main.json', 'w') as jsonOut:
			jsonOut.write(jsonLoad)
		return jsonLoad
	else:
		# Failed to find the feeder:
		return ''

@app.route('/api/analysisModel/<anaName>/<study>')
def analysisModel(anaName, study):
	#check for a json model:
	if anaName in os.listdir('./analyses/') and study in os.listdir('./analyses/' + anaName + '/studies/') and 'main.json' in os.listdir('./analyses/' + anaName + '/studies/' + study):
		with open('./analyses/' + anaName + '/studies/' + study + '/main.json') as jsonFile:
			return jsonFile.read()
	#just grab the GLM file:
	elif anaName in os.listdir('./analyses/') and study in os.listdir('./analyses/' + anaName + '/studies/'):
		tree = tp.parse('./analyses/' + anaName + '/studies/' + study + '/main.glm')
		filesAvailable = os.listdir('./analyses/' + anaName + '/studies/' + study)
		outDict = {'tree':tree, 'nodes':[], 'links':[], 'hiddenNodes':[], 'hiddenLinks':[]}
		# grab all the layout nodes, links, etc.
		for fileName in filesAvailable:
			if fileName.endswith('.json') and fileName != 'main.json':
				with open('./analyses/' + anaName + '/studies/' + study + '/' + fileName) as openFile:
					outDict[fileName[0:-5]] = json.loads(openFile.read())
		# cache the file for later
		jsonLoad = json.dumps(outDict, indent=4)
		with open('./analyses/' + anaName + '/studies/' + study + '/main.json', 'w') as jsonCache:
			jsonCache.write(jsonLoad)
		return jsonLoad
	else:
		return ''

@app.route('/getComponents/')
def getComponents():
	compFiles = os.listdir('./components/')
	components = {}
	for fileName in compFiles:
		with open('./components/' + fileName,'r') as compFile:
			fileContents = compFile.read()
			components[fileName] = eval(fileContents)
	# DEBUG: print components
	return json.dumps(components, indent=4)

@app.route('/saveFeeder/', methods=['POST'])
def updateGlm():
	postData = flask.request.form.to_dict()
	sourceFeeder = str(postData['feederName'])
	newFeeder = str(postData['newName'])	
	allFeeders = os.listdir('./feeders/')
	tree = json.loads(postData['tree'])
	# Nodes and links are the information about how the feeder is layed out.
	nodes = json.loads(postData['nodes'])
	hiddenNodes = json.loads(postData['hiddenNodes'])
	links = json.loads(postData['links'])
	hiddenLinks = json.loads(postData['hiddenLinks'])
	if newFeeder not in allFeeders:
		# if we've created a new feeder, copy over the associated files:
		shutil.copytree('./feeders/' + sourceFeeder,'./feeders/' + newFeeder)
	with open('./feeders/' + newFeeder + '/main.glm','w') as newMainGlm, open('./feeders/' + newFeeder + '/main.json','w') as jsonCache:
		newMainGlm.write(tp.sortedWrite(tree))
		outDict = {'tree':tree, 'nodes':nodes, 'links':links, 'hiddenNodes':hiddenNodes, 'hiddenLinks':hiddenLinks}
		jsonLoad = json.dumps(outDict, indent=4)
		jsonCache.write(jsonLoad)
	return flask.redirect(flask.url_for('newAnalysis'))

@app.route('/runStatus/')
def runStatus():
	analyses = os.listdir('./analyses/')
	outDict = {}
	for ana in analyses:
		md = analysis.getMetadata(ana)
		outDict[ana] = md['status']
	return json.dumps(outDict)

# This will run on all interface IPs.
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug='False', port=5001)
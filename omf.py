#!/bin/python

# third party modules
import flask, werkzeug, os, multiprocessing, json, time, datetime, copy, flask_login
# our modules
import analysis, feeder, reports, studies, milToGridlab, storage, work, User

app = flask.Flask(__name__)


try:
	with open('S3KEY.txt','r') as keyFile:
		USER_PASS = keyFile.read()
	store = storage.S3store('AKIAISPAZIA6NBEX5J3A', USER_PASS, 'crnomf')
	worker = work.ClusterWorker('AKIAISPAZIA6NBEX5J3A', USER_PASS, 'crnOmfJobQueue', 'crnOmfTerminateQueue')
	print 'Running on S3 cluster.'
except:
	USER_PASS = 'YEAHRIGHT'
	store = storage.Filestore('data')
	worker = work.LocalWorker()
	print 'Running on local file system.'
	
	
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
app.secret_key = "Here is a secret key"
user_manager = User.UserManager(store)

@login_manager.user_loader
def load_user(username):
	return user_manager.get(username)

class backgroundProc(multiprocessing.Process):
	def __init__(self, backFun, funArgs):
		self.name = 'omfWorkerProc'
		self.backFun = backFun
		self.funArgs = funArgs
		self.myPid = os.getpid()
		multiprocessing.Process.__init__(self)
	def run(self):
		self.backFun(*self.funArgs)

###################################################
# VIEWS
###################################################

@app.route("/login_page")
def login_page():
	return flask.render_template("login.html")

@app.route("/logout")
def logout():
	flask_login.logout_user()
	return flask.redirect("/")

@app.route("/login", methods = ["POST"])
def login():
	print "We should print something ehre"
	username, password = map(flask.request.form.get, ["username",
							  "password"])
	if username and password:
		user = user_manager.authenticate(username, password)
		if user:
			flask_login.login_user(user)
	return flask.redirect("/")
	
	# return flask.render_template("login.html")

@app.route("/register", methods = ["POST"])
def register():
	user = user_manager.create_user(*map(flask.request.form.get,
					     ["username",
					      "password",
					      "confirm_password"]))
	if user:
		flask_login.login_user(user)
	return flask.redirect("/")
	
	

@app.route('/')
@flask_login.login_required
def root():
	browser = flask.request.user_agent.browser
	metadatas = [flask_login.current_user.get('Analysis', x) for x in flask_login.current_user.listAll('Analysis')]
	feeders = flask_login.current_user.listAll('Feeder')
	conversions = flask_login.current_user.listAll('Conversion')
	
	if browser == 'msie':
		return 'The OMF currently must be accessed by Chrome, Firefox or Safari.'
	else:
		return flask.render_template('home.html', metadatas=metadatas, feeders=feeders, conversions=conversions)

@app.route('/newAnalysis/')
@app.route('/newAnalysis/<analysisName>')
@flask_login.login_required
def newAnalysis(analysisName=None):
	# Get some prereq data:
	tmy2s = store.listAll('Weather')
	feeders = flask_login.current_user.listAll('Feeder')
	analyses = flask_login.current_user.listAll('Analysis')
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
		thisAnalysis = flask_login.current_user.get('Analysis', analysisName)
		analysisMd = json.dumps({key:thisAnalysis[key] for key in thisAnalysis if type(thisAnalysis[key]) is not list})
		existingReports = json.dumps(thisAnalysis['reports'])
		#TODO: remove analysis name from study names. Dang DB keys.
		existingStudies = json.dumps([flask_login.current_user.get('Study', analysisName + '---' + studyName) for studyName in thisAnalysis['studyNames']])
	return flask.render_template('newAnalysis.html', studyTemplates=studyRendered, reportTemplates=reportTemplates, existingStudies=existingStudies, existingReports=existingReports, analysisMd=analysisMd)

@app.route('/viewReports/<analysisName>')
@flask_login.login_required
def viewReports(analysisName):
	if not flask_login.current_user.exists('Analysis', analysisName):
		return flask.redirect(flask.url_for('root'))
	thisAnalysis = analysis.Analysis(flask_login.current_user.get('Analysis',analysisName))
	studyList = []
	for studyName in thisAnalysis.studyNames:
		studyData = flask_login.current_user.get('Study', thisAnalysis.name + '---' + studyName)
		studyData['name'] = studyName
		studyData['analysisName'] = thisAnalysis.name
		moduleRef = getattr(studies, studyData['studyType'])
		classRef =  getattr(moduleRef, studyData['studyType'].capitalize())
		studyList.append(classRef(studyData))
	reportList = thisAnalysis.generateReportHtml(studyList)
	return flask.render_template('viewReports.html', analysisName=analysisName, reportList=reportList)

@app.route('/feeder/<feederName>')
@flask_login.login_required
def feederGet(feederName):
	return flask.render_template('gridEdit.html', feederName=feederName, anaFeeder=False)

@app.route('/analysisFeeder/<analysis>/<study>')
@flask_login.login_required
def analysisFeeder(analysis, study):
	return flask.render_template('gridEdit.html', feederName=analysis+'---'+study, anaFeeder=True)


####################################################
# API FUNCTIONS
####################################################

@app.route('/uniqueName/<name>')
@flask_login.login_required
def uniqueName(name):
	return json.dumps(name not in flask_login.current_user.listAll('Analysis'))

@app.route('/run/', methods=['POST'])
@app.route('/reRun/', methods=['POST'])
@flask_login.login_required
def run():
	# Get the analysis, and set it running on the data store.
	anaName = flask.request.form.get('analysisName')
	thisAnalysis = analysis.Analysis(flask_login.current_user.get('Analysis', anaName, False))
	thisAnalysis.status = 'running'
	flask_login.current_user.put('Analysis', anaName, thisAnalysis.__dict__)
	# Run in background and immediately return.
	worker.run(thisAnalysis, store)
	return flask.render_template('metadata.html', md=dict(thisAnalysis.__dict__.items() + {"name":anaName}.items()))

@app.route('/delete/', methods=['POST'])
@flask_login.login_required
def delete():
	anaName = flask.request.form['analysisName']
	# Delete studies.
	childStudies = [x for x in flask_login.current_user.listAll('Study') if x.startswith(anaName + '---')]
	for study in childStudies:
		flask_login.current_user.delete('Study', study)
	# Delete analysis.
	flask_login.current_user.delete('Analysis', anaName)
	return flask.redirect(flask.url_for('root'))

@app.route('/saveAnalysis/', methods=['POST'])
@flask_login.login_required
def saveAnalysis():
	pData = json.loads(flask.request.form.to_dict()['json'])
	def uniqJoin(stringList):
		return ', '.join(set(stringList))
	analysisData = {'status':'preRun',
					'sourceFeeder': uniqJoin([stud.get('feederName','') for stud in pData['studies']]),
					'climate': uniqJoin([stud.get('tmy2name','') for stud in pData['studies']]),
					'created': str(datetime.datetime.now()),
					'simStartDate': pData['simStartDate'],
					'simLength': pData['simLength'],
					'simLengthUnits': pData['simLengthUnits'],
					'runTime': '',
					'reports': pData['reports'],
					'studyNames': [stud['studyName'] for stud in pData['studies']] }
	flask_login.current_user.put('Analysis', pData['analysisName'], analysisData)
	for study in pData['studies']:
		studyData = {	'simLength': pData.get('simLength',0),
						'simLengthUnits': pData.get('simLengthUnits',''),
						'simStartDate': pData.get('simStartDate',''),
						'sourceFeeder': study.get('feederName',''),
						'analysisName': pData.get('analysisName',''),
						'climate': study.pop('tmy2name',''),
						'studyType': study.pop('studyType',''),
						'outputJson': {}}
		if studyData['studyType'] == 'gridlabd':
			studyFeeder = flask_login.current_user.get('Feeder', study['feederName'])
			studyFeeder['attachments']['climate.tmy2'] = store.get('Weather', studyData['climate'])['tmy2']
			studyData['inputJson'] = studyFeeder
		elif studyData['studyType'] in ['nrelswh','pvwatts']:
			study['attachments'] = {'climate.tmy2': store.get('Weather', studyData['climate'])['tmy2']}
			studyData['inputJson'] = study
		moduleRef = getattr(studies, studyData['studyType'])
		classRef =  getattr(moduleRef, studyData['studyType'].capitalize())
		studyObj = classRef(studyData, new=True)
		flask_login.current_user.put('Study', pData['analysisName'] + '---' + study['studyName'], studyObj.__dict__)
	return flask.redirect(flask.url_for('root'))

@app.route('/terminate/', methods=['POST'])
def terminate():
	anaName = flask.request.form['analysisName']
	worker.terminate(anaName)
	return flask.redirect(flask.url_for('root'))

@app.route('/feederData/<anaFeeder>/<feederName>.json')
@flask_login.login_required
def feederData(anaFeeder, feederName):
	if anaFeeder == 'True':
		#TODO: fix this.
		data = flask_login.current_user.get('Study', feederName)['inputJson']
		del data['attachments']
		return json.dumps(data)
	else:
		return json.dumps(flask_login.current_user.get('Feeder', feederName))

@app.route('/getComponents/')
def getComponents():
	components = {name:store.get('Component', name) for name in store.listAll('Component')}
	return json.dumps(components, indent=4)

@app.route('/saveFeeder/', methods=['POST'])
@flask_login.login_required
def saveFeeder():
	postObject = flask.request.form.to_dict()
	flask_login.current_user.put('Feeder', str(postObject['name']), json.loads(postObject['feederObjectJson']))
	return flask.redirect(flask.url_for('root') + '#feeders')

@app.route('/runStatus')
@flask_login.login_required
def runStatus():
	name = flask.request.args.get('name')
	md = flask_login.current_user.get('Analysis', name)
	if md['status'] != 'running':
		return flask.render_template('metadata.html', md=md)
	else:
		return flask.Response("waiting", content_type="text/plain")

@app.route('/milsoftImport/', methods=['POST'])
@flask_login.login_required
def milsoftImport():
	feederName = str(flask.request.form.to_dict()['feederName'])
	stdName = ''
	seqName = ''
	allFiles = flask.request.files
	for f in allFiles:
		fName = werkzeug.secure_filename(allFiles[f].filename)
		if fName.endswith('.std'): stdName = fName
		elif fName.endswith('.seq'): seqName = fName
		allFiles[f].save('./uploads/' + fName)
		# allFiles[f].save(fName)
	runProc = backgroundProc(milImportAndConvert, [store, feederName, stdName, seqName, flask_login.current_user.get_id()])
	runProc.start()
	time.sleep(1)
	return flask.redirect(flask.url_for('root') + '#feeders')

# Helper function for importing.
def milImportAndConvert(store, feederName, stdName, seqName, username):
	current_user = user_manager.get(username)		
	current_user.put('Conversion', feederName, {'data':'none'})
	newFeeder = {'links':[],'hiddenLinks':[],'nodes':[],'hiddenNodes':[],'layoutVars':{'theta':'0.8','gravity':'0.01','friction':'0.9','linkStrength':'5'}}
	newFeeder['tree'] = milToGridlab.convert('./uploads/' + stdName, './uploads/' + seqName)
	with open('./schedules.glm','r') as schedFile:
		newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
		current_user.put('Feeder', feederName, newFeeder)
	current_user.delete('Conversion', feederName)

if __name__ == '__main__':
	# Run a debug server all interface IPs.
	app.run(host='0.0.0.0', debug=True, port=5001, threaded=True)

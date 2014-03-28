#!/bin/python

# third party modules
import flask, werkzeug, json, time, datetime, copy, flask_login, boto.ses, hashlib, random, traceback, hashlib, time, random
# our modules
import analysis, feeder, reports, studies, storage, work, user

app = flask.Flask(__name__)

USER_PASS = 'YEAHRIGHT'
store = storage.Filestore('data')
worker = work.LocalWorker()
URL = 'localhost:5001'
print 'Running on local file system.'

def some_random_string():
	# Generate a cryptographically secure random string for signing/encrypting cookies.
	if 'COOKIE_KEY' in globals():
		return COOKIE_KEY
	else:
		return hashlib.md5(str(random.random())+str(time.time())).hexdigest()
	
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
app.secret_key = some_random_string()
user_manager = user.UserManager(store)

@app.before_request
def csrf_protect():
    if flask.request.user_agent.browser == 'msie' or flask.request.user_agent.browser == 'firefox':
		return 'The OMF currently must be accessed by Chrome or Safari.'
    if flask.request.method == "POST":
        token = flask.session.get('_csrf_token', None)
        if not token or token != flask.request.form.get('_csrf_token'):
            flask.abort(403)

def generate_csrf_token():
    if '_csrf_token' not in flask.session:
        flask.session['_csrf_token'] = some_random_string()
    return flask.session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@login_manager.user_loader
def load_user(username):
	return user_manager.get(username)

@app.route('/robots.txt')
def static_from_root():
    return flask.send_from_directory(app.static_folder, flask.request.path[1:])

###################################################
# VIEWS
###################################################

@app.route("/login_page")
def login_page():
	if flask_login.current_user.is_authenticated():
		return flask.redirect("/")
	return flask.render_template("clusterLogin.html")

@app.route("/logout")
def logout():
	flask_login.logout_user()
	return flask.redirect("/")

@app.route("/login", methods = ["POST"])
def login():
	username, password, remember = map(flask.request.form.get, ["username",
																"password",
																"remember"])
	if username and password:
		user = user_manager.authenticate(username, password)
		if user:
			flask_login.login_user(user, remember = remember == "on")
	return flask.redirect("/")

@app.route("/deleteUser", methods=["POST"])
@flask_login.login_required
def deleteUser():
	if flask_login.current_user.username != "admin":
		return "You are not authorized to delete users"

	username = flask.request.form.get("username")
	user_dict = store.get("User", username)
	
	if user_dict.get("password_digest"):
		user = user_manager.get(flask.request.form.get("username"))

		for objectType in ["Analysis", "Feeder", "Study"]:
			for objectName in user.listAll(objectType):
				user.delete(objectType, objectName)
	store.delete("User", username)
	return "Success"

@app.route("/new_user", methods=["POST"])
@flask_login.login_required
def new_user():
	if flask_login.current_user.username != "admin":
		return flask.redirect("/")
	email = flask.request.form.get("email")
	u = store.get("User", email)
	# if u and u.get("registered", True) and not flask.request.form.get("resend"): # so if the registered key is not there, assume they have registered
	if u and (u.get("password_digest") or not u.get("password_digest") and not flask.request.form.get("resend")):
		return "Already Exists"
	message = "Click the link below to register your account for the OMF.  This link will expire in 24 hours:\nreg_link"
	return send_link(email, message)

def send_link(email, message, u={}):
	c = boto.ses.connect_to_region("us-east-1",
								   aws_access_key_id="AKIAIFNNIT7VXOXVFPIQ",
								   aws_secret_access_key="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")
	reg_key = hashlib.md5(str(time.time())+str(random.random())).hexdigest()
	u["reg_key"] = reg_key
	u["timestamp"] = datetime.datetime.strftime(datetime.datetime.now(), format="%c")
	u["registered"] = False
	u["email"] = email
	store.put("User", email, u)
	outDict = c.send_email("david.pinney@omf.coop",
						   "OMF Registration Link",
						   message.replace("reg_link", "http://"+URL+"/register/"+email+"/"+reg_key),	
						   [email])
	return "Success"

@app.route("/forgotpwd", methods=["POST"])
def forgotpwd():
	if not store.get("User", flask.request.form.get("email")):
		return "Error"
	user = user_manager.get(flask.request.form.get("email"))
	if user:
		return send_link(user.username,
						 "Click the link below to reset your password for the OMF.  This link will expire in 24 hours.\nreg_link",
						 store.get("User", user.username))
	
@app.route("/register/<email>/<reg_key>", methods=["GET", "POST"])
def register(email, reg_key):
	if flask_login.current_user.is_authenticated():
		return flask.redirect("/")
	user = store.get("User", email)
	if not (user and
			reg_key == user.get("reg_key") and
			user.get("timestamp") and
			datetime.timedelta(1) > datetime.datetime.now() - datetime.datetime.strptime(user.get("timestamp"), "%c")):
		return "This page either expired, or you are not supposed to access it.  It might not even exist"
	if flask.request.method == "GET":
		return flask.render_template("register.html", email=email)
	password, confirm_password = map(flask.request.form.get, ["password", "confirm_password"])
	if password == confirm_password:
		user["username"] = email
		store.put("User", email, user)
		user = user_manager.get(email)
		# user = user_manager.authenticate(user["username"], password)
		user.changepwd(password)
		user = user_manager.authenticate(user.username, password)
		flask_login.login_user(user)
	return flask.redirect("/")
	
@app.route("/adminControls")
@flask_login.login_required
def adminControls():
	if flask_login.current_user.username != "admin":
		return flask.redirect("/")
	users = []
	# for username in store.listAll("User"):
	# 	if username not in ["public", "admin"] and store.get("User", username).get("username"):
	# 		users.append(user_manager.get(username))
	for username in store.listAll("User"):
		if username != "admin" and username != "public":
			u = {"username":username}
			user_dict = store.get("User", username)
			try:
				if user_dict.get("password_digest"):
					u["status"] = u["status_class"] = "Registered"
				elif datetime.timedelta(1) > datetime.datetime.now() - datetime.datetime.strptime(user_dict["timestamp"], "%c"):
					u["status"] = "Email sent"
					u["status_class"] = "emailSent"
				else:
					u["status"] = "Email expired"
					u["status_class"] = "emailExpired"
			except KeyError:
				return flask.Response(str(user_dict)+"\n"+username, content_type="text/plain")
			users.append(u)
	return flask.render_template("adminControls.html", users = users)
	
@app.route("/myaccount")
@flask_login.login_required
def myaccount():
	return flask.render_template("myaccount.html",
								 user=flask_login.current_user)

@app.route("/changepwd", methods=["POST"])
@flask_login.login_required
def changepwd():
	old_pwd, new_pwd, conf_pwd = map(flask.request.form.get, ["old_pwd", "new_pwd", "conf_pwd"])
	if user_manager.authenticate(flask_login.current_user.username, old_pwd):
		if new_pwd == conf_pwd:
			flask_login.current_user.changepwd(new_pwd)
			return "Success"
		else:
			return "not_match"
	else:
		return "not_auth"

FEEDERS_PER_PAGE = 10.
ANALYSES_PER_PAGE = 10.
@app.route("/")
@flask_login.login_required
def root():
	d = {}
	my_ciel = lambda x: (int(x) + 1) if int(x) < x else int(x)
	is_admin = flask_login.current_user.username == "admin"
	for header, user, url in [["Private", flask_login.current_user, "?public=false"],
							  ["Public", user_manager.get("public"), "?public=true"]]:
		metadatas = [user.get("Analysis", x) for x in user.listAll("Analysis")]
		feeders = user.listAll("Feeder")
		not_public_or_blank = lambda x: not (x.startswith("public_") or x.strip() == "")
		if is_admin and header == "Private":
			metadatas = filter(lambda x: not_public_or_blank(x["name"]), metadatas)
			feeders = filter(not_public_or_blank, feeders)
		d[header] = {"metadatas":metadatas[:int(ANALYSES_PER_PAGE)],
					 "amount_of_analysis_pages":my_ciel(len(metadatas)/ANALYSES_PER_PAGE),
					 "feeders":feeders[:int(FEEDERS_PER_PAGE)],
					 "amount_of_feeder_pages":my_ciel(len(feeders)/FEEDERS_PER_PAGE),
					 "conversions":user.listAll("Conversion"),
					 "url":url,
					}
	return flask.render_template('home.html', d=d, is_admin = is_admin)

@app.route("/retrievePage/<objectType>/<permission>/<page_number>")
@flask_login.login_required
def retrievePage(objectType, permission, page_number):
	page_number = int(page_number)
	url, user = ("?public=true", user_manager.get("public")) if permission == "Public" else ("?public=false", flask_login.current_user)
	if objectType == "Feeders":
		template, s, l, inc = ["feeder.html", "feeders", user.listAll("Feeder"), int(FEEDERS_PER_PAGE)]
	else:
		template, s, l, inc = ["metadata_loop.html",
							   "metadatas",
							   [user.get("Analysis", x) for x in user.listAll("Analysis")],
							   int(ANALYSES_PER_PAGE)]
	value = {s:l[inc*(page_number-1):inc*page_number], "url":url}
	return flask.render_template(template,
								 key=permission,
								 is_admin = flask_login.current_user.username == "admin",
								 conversions=user.listAll("Conversion"),
								 value = value)
		

@app.route("/publicObject/<objectType>/<objectName>")
def publicObject(objectType, objectName):
	if flask_login.current_user.username == "admin":
		objectName = objectName[objectName.find("_")+1:]
	if user_manager.get("public").get(objectType, objectName):
		return "Nope"
	return "Yep"
	
@app.route("/makePublic/<objectType>/<objectName>", methods=["POST"])
@flask_login.login_required
def makePublic(objectType, objectName):
	if not user_manager.get("public").get(objectType, objectName):
		flask_login.current_user.make_public(objectType, objectName)
	if objectType == "Analysis":
		for study in [s for s in flask_login.current_user.listAll("Study")
					  if s[:s.find("---")] == objectName]:
			flask_login.current_user.make_public("Study", study)
	return flask.redirect('/')

@app.route('/newAnalysis/')
@app.route('/newAnalysis/<analysisName>')
@flask_login.login_required
def newAnalysis(analysisName=None):
	# Get some prereq data:
	tmy2s = store.listAll('Weather')
	if flask.request.args.get("public") == "true":
		is_public = True
		user = user_manager.get("public")
	else:
		is_public = False
		user = flask_login.current_user
	public_feeders = user_manager.get("public").listAll("Feeder")
	private_feeders = [f for f in flask_login.current_user.listAll("Feeder") if f[:f.find("_")] != "public"]
	# if flask_login.current_user.username == "admin":
	# 	private_feeders
	# else:
	# 	private_feeders = flask_login.current_user.listAll("Feeder")
	feeders = {"Private":private_feeders, "Public":public_feeders}
	# feeders = user.listAll('Feeder')
	analyses = user.listAll('Analysis')
	# feeders = store.listAll("Feeder")
	# analyses = store.listAll("Analysis")
	reportTemplates = reports.__templates__
	studyTemplates = studies.__templates__
	studyRendered = {}
	is_admin = flask_login.current_user.username == "admin"
	for study in studyTemplates:
		studyRendered[study] = str(flask.render_template_string(studyTemplates[study], tmy2s=tmy2s, feeders=feeders, is_admin=is_admin))
	# If we aren't specifying an existing name, just make a blank analysis:
	if analysisName is None or analysisName not in analyses:
		existingStudies = None
		existingReports = None
		analysisMd = None
	# If we specified an analysis, get the studies, reports and analysisMd:
	else:
		thisAnalysis = user.get('Analysis', analysisName)
		analysisMd = json.dumps({key:thisAnalysis[key] for key in thisAnalysis if type(thisAnalysis[key]) is not list})
		existingReports = json.dumps(thisAnalysis['reports'])
		studyList = []
		for studyName in thisAnalysis['studyNames']:
			studyJson = user.get('Study', analysisName + '---' + studyName)
			studyJson.update({'name':studyName})
			studyJson.pop('inputJson','')
			studyJson.pop('outputJson','')
			studyList.append(studyJson)
		existingStudies = json.dumps(studyList)
	return flask.render_template('newAnalysis.html',
								 studyTemplates=studyRendered,
								 reportTemplates=reportTemplates,
								 existingStudies=existingStudies,
								 existingReports=existingReports,
								 analysisMd=analysisMd,
								 is_public=is_public,
								 is_admin = is_admin )

@app.route('/viewReports/<analysisName>')
@flask_login.login_required
def viewReports(analysisName):
	user, is_public = (user_manager.get("public"), True) if flask.request.args.get("public") == "true" else (flask_login.current_user, False)
	if not user.exists('Analysis', analysisName):
		return flask.redirect('/')
	thisAnalysis = analysis.Analysis(user.get('Analysis',analysisName))
	studyList = []
	for studyName in thisAnalysis.studyNames:
		studyData = user.get('Study', thisAnalysis.name + '---' + studyName)
		studyData['name'] = studyName
		studyData['analysisName'] = thisAnalysis.name
		moduleRef = getattr(studies, studyData['studyType'])
		classRef =  getattr(moduleRef, studyData['studyType'].capitalize())
		studyList.append(classRef(studyData))
	reportList = thisAnalysis.generateReportHtml(studyList)
	return flask.render_template('viewReports.html', analysisName=analysisName, reportList=reportList, public = is_public)

@app.route('/feeder/<feederName>')
@flask_login.login_required
def feederGet(feederName):
	return flask.render_template('gridEdit.html',
								 feederName=feederName,
								 ref = flask.request.referrer,
								 is_admin = flask_login.current_user.username == "admin",
								 anaFeeder=False,
								 public = flask.request.args.get("public") == "true")
								 

@app.route('/analysisFeeder/<analysis>/<study>')
@flask_login.login_required
def analysisFeeder(analysis, study):
	# , public = user_manager.get("public").exists("Analysis", analysis))
	return flask.render_template('gridEdit.html',
								 feederName=analysis+'---'+study,
								 anaFeeder=True,
								 public=flask.request.args.get("public"))

####################################################
# API FUNCTIONS
####################################################

@app.route('/workerStatus')
def workerStatus():
	return json.dumps(worker.status())

@app.route('/uniqueName/<name>')
@flask_login.login_required
def uniqueName(name):
	return json.dumps(name not in flask_login.current_user.listAll('Analysis'))

@app.route('/run/', methods=['POST'])
@app.route('/reRun/', methods=['POST'])
@flask_login.login_required
def run():
	# Get the analysis, and set it running on the data store.
	user, key = (user_manager.get("public"), "Public") if flask.request.args.get("public") == "true" else (flask_login.current_user, "Private")
	anaName = flask.request.form.get('analysisName')
	thisAnalysis = analysis.Analysis(user.get('Analysis', anaName, False))
	thisAnalysis.status = 'running'
	user.put('Analysis', anaName, thisAnalysis.__dict__)
	# Run in background and immediately return.
	worker.run(thisAnalysis, store)
	return flask.render_template('metadata.html',
								 md=dict(thisAnalysis.__dict__.items() + {"name":anaName}.items()),
								 key=key,
								 is_admin = flask_login.current_user.username == "admin",
								 value = {"url":"?public="+("true" if user.username == "public" else "false")})

@app.route('/delete/', methods=['POST'])
@flask_login.login_required
def delete():
	user = user_manager.get("public") if flask.request.args.get("public") == "true" else flask_login.current_user	
	anaName = flask.request.form['analysisName']
	# Delete studies.
	childStudies = [x for x in user.listAll('Study') if x.startswith(anaName + '---')]
	for study in childStudies:
		user.delete('Study', study)
	# Delete analysis.
	user.delete('Analysis', anaName)
	return flask.redirect('/')

@app.route("/deleteFeeder/", methods=["POST"])
@flask_login.login_required
def deleteGrid():
	feedername, csrf = map(flask.request.form.get, ["feedername", "csrf"])
	print 'THIS FEEDER:', feedername
	if flask_login.current_user.username == "admin":
		store.delete("Feeder", feedername)
	else:
		feedNoUser = feedername[feedername.find('_')+1:-1]
		flask_login.current_user.delete("Feeder", feedNoUser)
	return flask.redirect("/#feeders")


@app.route('/saveAnalysis/', methods=['POST'])
@flask_login.login_required
def saveAnalysis():
	pData = json.loads(flask.request.form.to_dict()['json'])
	user = (user_manager.get("public") if pData["is_public"] == "True" else flask_login.current_user)
	adminPrefix = ("admin_" if flask_login.current_user.username == "admin" else "")
	def uniqJoin(stringList):
		return ', '.join(set(stringList))
	analysisData = {'status':'preRun',
					'sourceFeeder': uniqJoin([stud.get('feederName','').split("?")[0] for stud in pData['studies']]),
					'climate': uniqJoin([stud.get('tmy2name','') for stud in pData['studies']]),
					'created': str(datetime.datetime.now()),
					'simStartDate': pData['simStartDate'],
					'simLength': pData['simLength'],
					'simLengthUnits': pData['simLengthUnits'],
					'runTime': '',
					'reports': pData['reports'],
					'studyNames': [stud['studyName'] for stud in pData['studies']] }
	flask_login.current_user.put('Analysis', adminPrefix+pData['analysisName'], analysisData)
	for study in pData['studies']:
		studyData = {	'simLength': pData.get('simLength',0),
						'simLengthUnits': pData.get('simLengthUnits',''),
						'simStartDate': pData.get('simStartDate',''),
						'sourceFeeder': 'N/A',
						'analysisName': pData.get('analysisName',''),
						'climate': study.pop('tmy2name',''),
						'studyType': study.pop('studyType',''),
						'outputJson': {}}
		if studyData['studyType'] == 'gridlabd':
			fname, pub = study["feederName"].split("?")
			studyData['sourceFeeder'] = fname
			if "true" in pub:
				studyFeeder = user_manager.get("public").get("Feeder",fname)
			else:
				studyFeeder = flask_login.current_user.get('Feeder', fname)
			studyFeeder['attachments']['climate.tmy2'] = store.get('Weather', studyData['climate'])['tmy2']
			studyData['inputJson'] = studyFeeder
		elif studyData['studyType'] in ['nrelswh','pvwatts']:
			study['attachments'] = {'climate.tmy2': store.get('Weather', studyData['climate'])['tmy2']}
			studyData['inputJson'] = study
		elif studyData['studyType'] == 'scada':
			studyData['inputJson'] = study
		moduleRef = getattr(studies, studyData['studyType'])
		classRef =  getattr(moduleRef, studyData['studyType'].capitalize())
		studyObj = classRef(studyData, new=True)
		flask_login.current_user.put('Study', adminPrefix+pData['analysisName'] + '---' + study['studyName'], studyObj.__dict__)
	return flask.redirect('/')

@app.route('/terminate/', methods=['POST'])
@flask_login.login_required
def terminate():
	# Get the analysis, and set it terminated on the data store.
	user = user_manager.get("public") if flask.request.args.get("public") == "true" else flask_login.current_user
	anaName = flask.request.form.get('analysisName')
	thisAnalysis = analysis.Analysis(user.get('Analysis', anaName))
	thisAnalysis.status = 'terminated'
	user.put('Analysis', anaName, thisAnalysis.__dict__)
	# Now actually do the termination:
	worker.terminate(user.prepend+anaName)
	return flask.redirect('/')

@app.route('/feederData/<anaFeeder>/<feederName>.json')
@flask_login.login_required
def feederData(anaFeeder, feederName):
	user = user_manager.get("public") if flask.request.args.get("public") == "true" else flask_login.current_user
	if anaFeeder == 'True':
		#TODO: fix this.
		data = user.get('Study', feederName)['inputJson']
		del data['attachments']
		return json.dumps(data)
	else:
		return json.dumps(user.get('Feeder', feederName))

@app.route('/getComponents/')
def getComponents():
	components = {name:store.get('Component', name) for name in store.listAll('Component')}
	return json.dumps(components, indent=4)

@app.route('/saveFeeder/<public>', methods=['POST'])
@flask_login.login_required
def saveFeeder(public):
	postObject = flask.request.form.to_dict()
	if public == "True":
		if flask_login.current_user.username == "admin":
			user_manager.get("public").put("Feeder", str(postObject["name"]), json.loads(postObject["feederObjectJson"]))
		else:
			return "You are not authorized to modify public feeders"
	else:
		if flask_login.current_user.username == "admin":
			if store.get("Feeder", str(postObject["name"])):
				store.put("Feeder", str(postObject["name"]), json.loads(postObject["feederObjectJson"]))
			else:
				store.put("Feeder", "admin_"+str(postObject["name"]), json.loads(postObject["feederObjectJson"]))
		else:
			flask_login.current_user.put("Feeder", str(postObject["name"]), json.loads(postObject["feederObjectJson"]))
	return flask.redirect(flask.request.form.get("ref", "/#feeders"))

@app.route('/feederName/<new_name>')
@flask_login.login_required
def feederName(new_name):
	if flask_login.current_user.get('Feeder', new_name):
		return 'Nope'
	return 'Yep'

@app.route('/runStatus')
@flask_login.login_required
def runStatus():
	name = flask.request.args.get('name')
	is_public = flask.request.args.get("is_public") == "true"
	if is_public:
		key = "Public"
		user = user_manager.get("public")
	else:
		key="Private"
		user = flask_login.current_user
	md = user.get("Analysis", name)
	# md = flask_login.current_user.get('Analysis', name)
	# md = (user_manager.get("public") if flask.request.args.get("is_public") == "true" else flask_login.current_user).get("Analysis", name)
	# print md
	if md['status'] != 'running':
		return flask.render_template('metadata.html',
									 md=md,
									 key=key,
									 is_admin = flask_login.current_user.username == "admin",
									 value={"url":"?public="+("true" if is_public else "false")})
	else:
		return flask.Response("waiting", content_type="text/plain")

@app.route('/milsoftImport/', methods=['POST'])
@flask_login.login_required
def milsoftImport():
	feederName = str(flask.request.form.to_dict()['feederName'])
	if flask_login.current_user.username == "admin":
		feederName = "admin_" + feederName 
	current_user = user_manager.get(flask_login.current_user.get_id())		
	current_user.put('Conversion', feederName, {'data':'none'})
	stdString = flask.request.files['stdFile'].stream.read()
	seqString = flask.request.files['seqFile'].stream.read()
	worker.milImport(store, current_user.prepend+feederName, stdString, seqString)
	return flask.redirect('/#feeders')

@app.route('/gridlabdImport/', methods=['POST'])
@flask_login.login_required
def gridlabdImport():
	feederName = str(flask.request.form.to_dict()['feederName'])
	if flask_login.current_user.username == "admin":
		feederName = "admin_" + feederName 
	current_user = user_manager.get(flask_login.current_user.get_id())

	newFeeder = {'links':[],'hiddenLinks':[],'nodes':[],'hiddenNodes':[],'layoutVars':{'theta':'0.8','gravity':'0.01','friction':'0.9','linkStrength':'5','linkDistance':'5','charge':'-5'}}
	newFeeder['tree'] = feeder.parse(flask.request.files['glmFile'].stream.read(), False)

	newFeeder['layoutVars']['xScale'] = 0
	newFeeder['layoutVars']['yScale'] = 0
	with open('./schedules.glm','r') as schedFile:
		newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
	current_user.put('Feeder', feederName, newFeeder)
	return flask.redirect('/#feeders')


if __name__ == '__main__':
	# Run a debug server all interface IPs.
	app.run(host='0.0.0.0', port=5001, threaded=True, debug=True, use_reloader=False)

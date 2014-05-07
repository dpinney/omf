''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort, jsonify, Response
from jinja2 import Template
import models, json, os, flask_login, hashlib, random, time, datetime, shutil, milToGridlab
from passlib.hash import pbkdf2_sha512

app = Flask("omf")

def getDataNames():
	''' Query the OMF datastore to list all the names of things that can be included.'''
	currUser = flask_login.current_user
	feeders = [x[:-5] for x in os.listdir('./data/Feeder/' + currUser.username)]
	publicFeeders = [x[:-5] for x in os.listdir('./data/Feeder/public/')]
	climates = [x[:-5] for x in os.listdir('./data/Climate/')]
	return {'feeders':feeders, 'publicFeeders':publicFeeders, 'climates':climates, 
		'currentUser':currUser.__dict__}

@app.before_request
def csrf_protect():
	pass
	if request.user_agent.browser == 'msie' or request.user_agent.browser == 'firefox':
		return 'The OMF currently must be accessed by Chrome or Safari.'
	# TODO: fix csrf validation.
	# if request.method == "POST":
	#	token = session.get('_csrf_token', None)
	#	if not token or token != request.form.get('_csrf_token'):
	#		abort(403)

def send_link(email, message, u={}):
	c = boto.ses.connect_to_region("us-east-1",
		aws_access_key_id="AKIAIFNNIT7VXOXVFPIQ",
		aws_secret_access_key="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")
	reg_key = hashlib.md5(str(time.time())+str(random.random())).hexdigest()
	u["reg_key"] = reg_key
	u["timestamp"] = datetime.datetime.strftime(datetime.datetime.now(), format="%c")
	u["registered"] = False
	u["email"] = email
	json.dump(u, open("data/User/"+email+".json", "w"))
	outDict = c.send_email("david.pinney@omf.coop",
		"OMF Registration Link",
		message.replace("reg_link", "http://"+URL+"/register/"+email+"/"+reg_key),	
		[email])
	return "Success"

def milImportBackground(owner, feederName, stdString, seqString):
	newFeederWireframe = {'links':[],'hiddenLinks':[],'nodes':[],'hiddenNodes':[],
		'layoutVars':{'theta':'0.8','gravity':'0.01','friction':'0.9','linkStrength':'5','linkDistance':'5','charge':'-5'}}
	newFeeder = dict(**newFeederWireframe)
	[newFeeder['tree'], xScale, yScale] = milToGridlab.convert(stdString, seqString)
	newFeeder['layoutVars']['xScale'] = xScale
	newFeeder['layoutVars']['yScale'] = yScale
	with open('./schedules.glm','r') as schedFile:
		newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
	hlp.feederDump(owner, feederName, newFeeder)
	
def milImport(owner, feederName, stdString, seqString):
	# Setup.
	# TODO: switch to multiprocessing for better control.
	importThread = Thread(target=milImportBackground, args=[owner, feederName, stdString, seqString])
	importThread.start()

###################################################
# AUTHENTICATION AND SECURITY STUFF
###################################################

class User:
	def __init__(self, jsonBlob):
		self.username = jsonBlob["username"]
	# Required flask_login functions.
	def is_admin(self): return self.username == "admin"
	def get_id(self): return self.username	
	def is_authenticated(self): return True
	def is_active(self): return True
	def is_anonymous(self): return False

def cryptoRandomString():
	''' Generate a cryptographically secure random string for signing/encrypting cookies. '''
	if 'COOKIE_KEY' in globals():
		return COOKIE_KEY
	else:
		return hashlib.md5(str(random.random())+str(time.time())).hexdigest()

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
app.secret_key = cryptoRandomString()

@login_manager.user_loader
def load_user(username):
	''' Required by flask_login to return instance of the current user '''
	return User(json.load(open("./data/User/" + username + ".json")))

def generate_csrf_token():
	if '_csrf_token' not in session:
		session['_csrf_token'] = cryptoRandomString()
	return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.route("/login_page")
def login_page():
	if flask_login.current_user.is_authenticated():
		return redirect("/")
	return render_template("clusterLogin.html")

@app.route("/logout")
def logout():
	flask_login.logout_user()
	return redirect("/")

@app.route("/login", methods = ["POST"])
def login():
	username, password, remember = map(request.form.get, ["username",
		"password", "remember"])
	userJson = None
	for u in os.listdir("./data/User/"):
		if u.lower() == username.lower() + ".json":
			userJson = json.load(open("./data/User/" + u))
			break
	if userJson and pbkdf2_sha512.verify(password,
			userJson["password_digest"]):
		user = User(userJson)
		flask_login.login_user(user, remember = remember == "on")
	return redirect("/")

###################################################
# API CALLS
###################################################

@app.route("/deleteUser", methods=["POST"])
@flask_login.login_required
def deleteUser():
	if flask_login.current_user.username != "admin":
		return "You are not authorized to delete users"
	username = request.form.get("username")
	for objectType in ["Model", "Feeder"]:
		try:
			shutil.rmtree("data/"+username+objectType)
		except Exception, e:
			print e
			return "Failure"
	return "Success"

@app.route("/new_user", methods=["POST"])
@flask_login.login_required
def new_user():
	if flask_login.current_user.username != "admin":
		return redirect("/")
	email = request.form.get("email")
	if email in [f.replace(".json", "") for f in os.listdir("data/User")]:
		u = User.gu(email)
		if u.get("password_digest") or not request.form.get("resend"):
			return "Already Exists"
	message = "Click the link below to register your account for the OMF.  This link will expire in 24 hours:\nreg_link"
	return send_link(email, message)

@app.route("/forgotpwd", methods=["POST"])
def forgotpwd():
	email = request.form.get("email")
	try:
		user = User.gu(email)
		message = "Click the link below to reset your password for the OMF.  This link will expire in 24 hours.\nreg_link"
		return send_link(email,message,user)
	except Exception, e:
		print e
		return "Error"
	
@app.route("/register/<email>/<reg_key>", methods=["GET", "POST"])
def register(email, reg_key):
	if flask_login.current_user.is_authenticated():
		return redirect("/")
	# This is super ug, sorry
	try:
		user = User.gu(email)
	except Exception:
		user = None
	if not (user and
			reg_key == user.get("reg_key") and
			user.get("timestamp") and
			datetime.timedelta(1) > datetime.datetime.now() - datetime.datetime.strptime(user.get("timestamp"), "%c")):
		return "This page either expired, or you are not supposed to access it.  It might not even exist"
	if request.method == "GET":
		return render_template("register.html", email=email)
	password, confirm_password = map(request.form.get, ["password", "confirm_password"])
	if password == confirm_password:
		user["username"] = email
		user["password_digest"] = pbkdf2_sha512.encrypt(password)
		flask_login.login_user(User(user))
		User.du(user)
	return redirect("/")

@app.route("/changepwd", methods=["POST"])
@flask_login.login_required
def changepwd():
	old_pwd, new_pwd, conf_pwd = map(flask.request.form.get, ["old_pwd", "new_pwd", "conf_pwd"])
	user = User.gu(flask_login.current_user.username)
	if pbkdf2_sha512.verify(old_pwd, user["password_digest"]):
		if new_pwd == conf_pwd:
			user["password_digest"] = pbkdf2_sha512.encrypt(new_pwd)
			User.du(user)
			return "Success"
		else:
			return "not_match"
	else:
		return "not_auth"

@app.route("/makePublic/<objectType>/<objectName>", methods=["POST"])
@flask_login.login_required
def makePublic(objectType, objectName):
	username = flask.current_user.username
	if objectType == "Feeder":
		ext = ".json"
	else:
		ext = ""
	srcpth = "data/"+objectType+"/"+username+"/"+objectName+ext
	destpth = "data/"+objectType+"/public/"+objectName+ext
	shutil.move(srcpth, destpth)
	return flask.redirect('/')


@app.route("/delete/<objectType>/<name>/<owner>")
@flask_login.login_required
def delete(objectType, name, owner):
	if owner != User.cu() and User.cu() != "admin":
		return
	try:
		# Just in case someone tries to delete something not through the web interface or for some reason the web interface is displaying something that doesn't actually exist
		if objectType == "Feeder":
			os.remove(hlp.feederPath(owner, name))
		elif objectType == "Model":
			shutil.rmtree(hlp.modelPath(owner, name))
	except Exception:
		pass
	return

# Need to do some massive feeder refactoring before I get started on this badboy
@app.route('/saveFeeder/<owner>/<feederName>', methods=['POST'])
@flask_login.login_required
def saveFeeder(owner, feederName):
	"""How to save the feeder"""
	# If the owner is public, then the current user must be admin
	# The admin is also allowed to do whatever the durn eff he pleases
	postObject = request.form.to_dict()
	if owner == User.cu() or User.is_admin():
		# Then feel free to dump
		json.dump(postObject["feederObjectJson"], open(hlp.feederPath(owner, feederName), "w"))
	return redirect(request.form.get("ref", "/#feeders"))

@app.route('/milsoftImport/', methods=['POST'])
@flask_login.login_required
def milsoftImport():
	"""This function is used for milsoftImporting"""
	feederName = str(flask.request.form.to_dict()['feederName'])
	stdString, seqString = map(lambda x: flask.request.files[x].stream.read(), ["stdFile", "seqFile"])
	milImport(User.cu(), current_user.prepend+feederName, stdString, seqString)
	hlp.conversionDump(User.cu(), feederName, {"data":"none"})
	return flask.redirect('/#feeders')

@app.route('/gridlabdImport/', methods=['POST'])
@flask_login.login_required
def gridlabdImport():
	"""This function is used for gridlabdImporting"""
	feederName = str(flask.request.form.to_dict()['feederName'])
	newFeeder = dict(**hlp.newFeederWireframe)	# copies the dictionary..
	newFeeder['tree'] = feeder.parse(flask.request.files['glmFile'].stream.read(), False)
	newFeeder['layoutVars']['xScale'] = 0
	newFeeder['layoutVars']['yScale'] = 0
	with open('./schedules.glm','r') as schedFile:
		newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
	hlp.feederDump(User.cu(), feederName, newFeeder)
	return flask.redirect('/#feeders')

@app.route("/feederData/<owner>/<feederName>/") 
@app.route("/feederData/<owner>/<feederName>/<modelFeeder>")
@flask_login.login_required
def feederData(owner, feederName, modelFeeder=False):
	#TODO: fix modelFeeder capability.
	cUser = flask_login.current_user.username
	if cUser=="admin" or owner==cUser or owner=="public":
		with open("data/Feeder/" + owner + "/" + feederName + ".json", "r") as feedFile:
			return feedFile.read()

@app.route("/getComponents/")
def getComponents():
	path = "data/Component/"
	components = {name[0:-5]:json.load(open(path+name))	for name in os.listdir(path)}
	return json.dumps(components)

@app.route('/uniqueName/<objectType>/<name>')
@flask_login.login_required
def uniqueName(objectType, name):
	# hello
	return hlp.nojson(objectType, name)

@app.route("/uniqObjName/<objtype>/<owner>/<name>")
@flask_login.login_required
def uniqObjName(objtype, owner, name):
	# This should replace all the functions that check for unique names
	if objtype == "Model":
		path = hlp.modelPath(owner, name)
	elif objtype == "Feeder":
		path = hlp.feederPath(owner, name)
	return jsonify(exists=os.path.exists(path))

@app.route("/publicObject/<objectType>/<objectName>")
def publicObject(objectType, objectName):
	# This is supposed to be for when you are going to publish an object, and we are looking for name conflicts.
	# So it's like two layers of stupid because it returns Nope if it IS the name of a public object and Yep otherwise...
	# I guess the intention is, Can I publish this? Nope, because it has the same name as a public object, or Yep, you can because there is no public object with that name
	# A refactor so that the front end expects true/false rather than Yep/Nope is definitely necessary
	return "Nope" if hlp.pubhelper(objectType, objectName) else "Yep"

###################################################
# VIEWS
###################################################

@app.route("/")
@flask_login.login_required
def root():
	''' Render the home screen of the OMF. '''
	isAdmin = flask_login.current_user.username == "admin"
	uName = flask_login.current_user.username
	publicModels = [{"owner":"public","name":x} for x in os.listdir("data/Model/public/")]
	userModels = [{"owner":uName, "name":x} for x in os.listdir("data/Model/" + uName)]
	# TODO: allow admin to see all models.
	publicFeeders = [{"owner":"public","name":x[0:-5]} for x in os.listdir("data/Feeder/public/")]
	userFeeders = [{"owner":uName,"name":x[0:-5]} for x in os.listdir("data/Feeder/" + uName)]
	# Grab metadata for models and feeders.
	allModels = publicModels + userModels
	for mod in allModels:
		modPath = "data/Model/" + mod["owner"] + "/" + mod["name"]
		allInput = json.load(open(modPath + "/allInputData.json","r"))
		hasOutput = os.path.isfile(modPath + "/allOutputData.json")
		hasPID = os.path.isfile(modPath + "/PID.txt")
		mod["runTime"] = allInput.get("runTime","")
		mod["modelType"] = allInput.get("modelType","")
		if hasPID and not hasOutput:
			mod["status"] = "running"
		elif not hasPID and hasOutput:
			mod["status"] = "postRun"
		elif not hasPID and not hasOutput:
			mod["status"] = "cancelled"
		else: # hasPID and hasOutput
			mod["status"] = "running"
		# mod["created"] = allInput.get("created","")
		mod["editDate"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(os.stat(modPath).st_ctime)) 
	allFeeders = publicFeeders + userFeeders
	for feed in allFeeders:
		feedPath = "data/Feeder/" + feed["owner"] + "/" + feed["name"] + ".json"
		feed["editDate"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(os.stat(feedPath).st_ctime))
		feed["status"] = "Ready"
	#TODO: get status into feeders/models.
	return render_template("home.html", models = allModels, feeders = allFeeders,
		current_user = flask_login.current_user.username, is_admin = isAdmin, modelNames = models.__all__)

@app.route("/model/<user>/<modelName>")
@flask_login.login_required
def showModel(user, modelName):
	''' Render a model template with saved data. '''
	# TODO: do user check.
	modelDir = "./data/Model/" + user + "/" + modelName
	with open(modelDir + "/allInputData.json") as inJson:
		modelType = json.load(inJson)["modelType"]
	return getattr(models, modelType).renderTemplate(modelDir, False, getDataNames())

@app.route("/newModel/<modelType>")
@flask_login.login_required
def newModel(modelType):
	''' Display the module template for creating a new model. '''
	return getattr(models, modelType).renderTemplate(datastoreNames=getDataNames())

@app.route("/runModel/", methods=["POST"])
@flask_login.login_required
def runModel():
	''' Start a model running and redirect to its running screen. '''
	pData = request.form.to_dict()
	modelModule = getattr(models, pData["modelType"])
	if pData.get("created","NOKEY") == "":
		# New model.
		pData["user"] = flask_login.current_user.username
		modelModule.create("./data/Model/", pData)
	modelModule.run("./data/Model/" + pData["user"]+ "/" + pData["modelName"])
	return redirect("/model/" + pData["user"] + "/" + pData["modelName"])

@app.route('/feeder/<owner>/<feederName>')
@flask_login.login_required
def feederGet(owner, feederName):
	# TODO: fix modelFeeder
	return render_template('gridEdit.html', feederName=feederName, ref=request.referrer,
		is_admin=flask_login.current_user.username=="admin", modelFeeder=False, public=owner=="public",
		currUser = flask_login.current_user.username,
		owner = owner)

@app.route("/adminControls")
@flask_login.login_required
def adminControls():
	''' Render admin controls. '''
	if flask_login.current_user.username != "admin":
		return redirect("/")
	users = []
	for username in [f.replace(".json", "") for f in os.listdir("data/User")]:
		if username != "admin" and username != "public":
			u = {"username":username}
			user_dict = User.gu(username)
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
				return Response(str(user_dict)+"\n"+username, content_type="text/plain")
			users.append(u)
	return render_template("adminControls.html", users = users)

@app.route("/myaccount")
@flask_login.login_required
def myaccount():
	''' Render account info for any user. '''
	return render_template("myaccount.html", user=flask_login.current_user)

@app.route("/robots.txt")
def static_from_root():
	return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
	# TODO: remove debug?
	template_files = ["templates/"+ x  for x in os.listdir("templates")]
	app.run(debug=True, extra_files=template_files)
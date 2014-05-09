''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort, jsonify, Response
from jinja2 import Template
import models, json, os, flask_login, hashlib, random, time, datetime, shutil, milToGridlab, boto.ses
from multiprocessing import Process
from passlib.hash import pbkdf2_sha512

app = Flask("omf")
URL = "http://omf.coop"

###################################################
# HELPER FUNCTIONS
###################################################

def safeListdir(path):
	''' Helper function that returns [] for dirs that don't exist. Otherwise new users can cause exceptions. '''
	try: return os.listdir(path)
	except:	return []

def getDataNames():
	''' Query the OMF datastore to get names of all objects.'''
	currUser = flask_login.current_user
	feeders = [x[:-5] for x in safeListdir('./data/Feeder/' + currUser.username)]
	publicFeeders = [x[:-5] for x in safeListdir('./data/Feeder/public/')]
	climates = [x[:-5] for x in safeListdir('./data/Climate/')]
	return {'feeders':feeders, 'publicFeeders':publicFeeders, 'climates':climates, 
		'currentUser':currUser.__dict__}

@app.before_request
def csrf_protect():
	if request.user_agent.browser == 'msie' or request.user_agent.browser == 'firefox':
		return 'The OMF currently must be accessed by Chrome or Safari.'
	# TODO: fix csrf validation.
	# if request.method == "POST":
	#	token = session.get('_csrf_token', None)
	#	if not token or token != request.form.get('_csrf_token'):
	#		abort(403)

def send_link(email, message, u={}):
	''' Send message to email using Amazon SES. '''
	c = boto.ses.connect_to_region("us-east-1",
		aws_access_key_id="AKIAIFNNIT7VXOXVFPIQ",
		aws_secret_access_key="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")
	reg_key = hashlib.md5(str(time.time())+str(random.random())).hexdigest()
	u["reg_key"] = reg_key
	u["timestamp"] = datetime.datetime.strftime(datetime.datetime.now(), format="%c")
	u["registered"] = False
	u["email"] = email
	json.dump(u, open("data/User/"+email+".json", "w"), indent=4)
	outDict = c.send_email("admin@omf.coop", "OMF Registration Link",
		message.replace("reg_link", URL+"/register/"+email+"/"+reg_key), [email])
	return "Success"

###################################################
# AUTHENTICATION AND SECURITY SETUP
###################################################

class User:
	def __init__(self, jsonBlob): self.username = jsonBlob["username"]
	# Required flask_login functions.
	def is_admin(self): return self.username == "admin"
	def get_id(self): return self.username	
	def is_authenticated(self): return True
	def is_active(self): return True
	def is_anonymous(self): return False
	@classmethod
	def cu(self):
		"""Returns current user's username"""
		return flask_login.current_user.username

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

###################################################
# API CALLS
###################################################

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

@app.route("/deleteUser", methods=["POST"])
@flask_login.login_required
def deleteUser():
	if User.cu() != "admin":
		return "You are not authorized to delete users"
	username = request.form.get("username")
	# Clean up user data.
	for objectType in ["Model", "Feeder"]:
		try:
			shutil.rmtree("data/" + objectType + "/" + username)
		except Exception, e:
			print "USER DATA DELETION FAILED FOR", e
	os.remove("data/User/" + username + ".json")
	return "Success"

@app.route("/new_user", methods=["POST"])
@flask_login.login_required
def new_user():
	if User.cu() != "admin":
		return redirect("/")
	email = request.form.get("email")
	if email in [f[0:-5] for f in os.listdir("data/User")]:
		u = json.load(open("data/User/" + email + ".json"))
		if u.get("password_digest") or not request.form.get("resend"):
			return "Already Exists"
	message = "Click the link below to register your account for the OMF.  This link will expire in 24 hours:\n\nreg_link"
	return send_link(email, message)

@app.route("/forgotpwd", methods=["POST"])
def forgotpwd():
	email = request.form.get("email")
	try:
		user = User.gu(email)
		message = "Click the link below to reset your password for the OMF.  This link will expire in 24 hours.\n\nreg_link"
		return send_link(email,message,user)
	except Exception, e:
		print e
		return "Error"
	
@app.route("/register/<email>/<reg_key>", methods=["GET", "POST"])
def register(email, reg_key):
	if flask_login.current_user.is_authenticated():
		return redirect("/")
	try:
		user = json.load(open("data/User/" + email + ".json"))
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
		with open("data/User/"+user["username"]+".json","w") as outFile:
			json.dump(user, outFile)
	return redirect("/")

@app.route("/changepwd", methods=["POST"])
@flask_login.login_required
def changepwd():
	old_pwd, new_pwd, conf_pwd = map(flask.request.form.get, ["old_pwd", "new_pwd", "conf_pwd"])
	user = User.gu(User.cu())
	if pbkdf2_sha512.verify(old_pwd, user["password_digest"]):
		if new_pwd == conf_pwd:
			user["password_digest"] = pbkdf2_sha512.encrypt(new_pwd)
			User.du(user)
			return "Success"
		else:
			return "not_match"
	else:
		return "not_auth"

@app.route("/delete/<objectType>/<owner>/<objectName>", methods=["POST"])
@flask_login.login_required
def delete(objectType, objectName, owner):
	''' Delete models or feeders. '''
	if owner != User.cu() and User.cu() != "admin":
		return False
	if objectType == "Feeder":
		os.remove("data/Feeder/" + owner + "/" + objectName + ".json")
	elif objectType == "Model":
		shutil.rmtree("data/Model/" + owner + "/" + objectName)
	return redirect("/")

@app.route('/saveFeeder/<owner>/<feederName>', methods=['POST'])
@flask_login.login_required
def saveFeeder(owner, feederName):
	''' Save feeder data. '''
	if owner == User.cu() or "admin" == User.cu() or owner=="public":
		# If we have a new user, make sure to make their folder:
		if not os.path.isdir("data/Feeder/" + owner):
			os.makedirs("data/Feeder/" + owner)
		#TODO: make sure non-admins can't overwrite public feeders.
		with open("data/Feeder/" + owner + "/" + feederName + ".json", "w") as outFile:
			payload = json.loads(request.form.to_dict().get("feederObjectJson","{}"))
			json.dump(payload, outFile, indent=4)
	return redirect(request.form.get("ref", "/#feeders"))

@app.route('/milsoftImport/', methods=['POST'])
@flask_login.login_required
def milsoftImport():
	''' API for importing a milsoft feeder. '''
	feederName = str(flask.request.form.to_dict()['feederName'])
	stdString, seqString = map(lambda x: flask.request.files[x].stream.read(), ["stdFile", "seqFile"])
	importProc = Process(target=milImportBackground, args=[owner, feederName, stdString, seqString])
	importProc.start()
	hlp.conversionDump(User.cu(), feederName, {"data":"none"})
	return flask.redirect('/#feeders')

def milImportBackground(owner, feederName, stdString, seqString):
	''' Function to run in the background for Milsoft import. '''
	newFeederWireframe = {'links':[],'hiddenLinks':[],'nodes':[],'hiddenNodes':[],
		'layoutVars':{'theta':'0.8','gravity':'0.01','friction':'0.9','linkStrength':'5','linkDistance':'5','charge':'-5'}}
	newFeeder = dict(**newFeederWireframe)
	[newFeeder['tree'], xScale, yScale] = milToGridlab.convert(stdString, seqString)
	newFeeder['layoutVars']['xScale'] = xScale
	newFeeder['layoutVars']['yScale'] = yScale
	with open('./schedules.glm','r') as schedFile:
		newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
	hlp.feederDump(owner, feederName, newFeeder)
	
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
	if User.cu()=="admin" or owner==User.cu() or owner=="public":
		with open("data/Feeder/" + owner + "/" + feederName + ".json", "r") as feedFile:
			return feedFile.read()

@app.route("/getComponents/")
def getComponents():
	path = "data/Component/"
	components = {name[0:-5]:json.load(open(path + name)) for name in os.listdir(path)}
	return json.dumps(components)

@app.route("/uniqObjName/<objtype>/<owner>/<name>")
@flask_login.login_required
def uniqObjName(objtype, owner, name):
	# This should replace all the functions that check for unique names
	if objtype == "Model":
		path = "data/Model/" + owner + "/" + name
	elif objtype == "Feeder":
		path = "data/Feeder/" + owner + "/" + name
	return jsonify(exists=os.path.exists(path))

###################################################
# VIEWS
###################################################

@app.route("/")
@flask_login.login_required
def root():
	''' Render the home screen of the OMF. '''
	# Gather object names.
	publicModels = [{"owner":"public","name":x} for x in safeListdir("data/Model/public/")]
	userModels = [{"owner":User.cu(), "name":x} for x in safeListdir("data/Model/" + User.cu())]
	publicFeeders = [{"owner":"public","name":x[0:-5]} for x in safeListdir("data/Feeder/public/")]
	userFeeders = [{"owner":User.cu(),"name":x[0:-5]} for x in safeListdir("data/Feeder/" + User.cu())]
	# Allow admin to see all models.
	isAdmin = User.cu() == "admin"
	if isAdmin:
		userFeeders = [{"owner":owner,"name":feed[0:-5]} for owner in safeListdir("data/Feeder/")
			for feed in safeListdir("data/Feeder/" + owner)]
		userModels = [{"owner":owner, "name":mod} for owner in safeListdir("data/Model/") 
			for mod in safeListdir("data/Model/" + owner)]
	# Grab metadata for models and feeders.
	allModels = publicModels + userModels
	for mod in allModels:
		modPath = "data/Model/" + mod["owner"] + "/" + mod["name"]
		allInput = json.load(open(modPath + "/allInputData.json","r"))
		hasOutput = os.path.isfile(modPath + "/allOutputData.json")
		hasPID = os.path.isfile(modPath + "/PID.txt")
		if hasPID and not hasOutput:
			mod["status"] = "running"
		elif not hasPID and hasOutput:
			mod["status"] = "postRun"
		elif not hasPID and not hasOutput:
			mod["status"] = "cancelled"
		else: # hasPID and hasOutput
			mod["status"] = "running"
		mod["runTime"] = allInput.get("runTime","")
		mod["modelType"] = allInput.get("modelType","")
		# mod["created"] = allInput.get("created","")
		mod["editDate"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(os.stat(modPath).st_ctime)) 
	allFeeders = publicFeeders + userFeeders
	for feed in allFeeders:
		feedPath = "data/Feeder/" + feed["owner"] + "/" + feed["name"] + ".json"
		feed["editDate"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(os.stat(feedPath).st_ctime))
		feed["status"] = "Ready"
	return render_template("home.html", models = allModels, feeders = allFeeders,
		current_user = User.cu(), is_admin = isAdmin, modelNames = models.__all__)

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
		pData["user"] = User.cu()
		modelModule.create("./data/Model/", pData)
	modelModule.run("./data/Model/" + pData["user"]+ "/" + pData["modelName"])
	return redirect("/model/" + pData["user"] + "/" + pData["modelName"])

@app.route('/feeder/<owner>/<feederName>')
@flask_login.login_required
def feederGet(owner, feederName):
	''' Editing interface for feeders. '''
	# TODO: fix modelFeeder
	return render_template('gridEdit.html', feederName=feederName, ref=request.referrer,
		is_admin=User.cu()=="admin", modelFeeder=False, public=owner=="public",
		currUser = User.cu(), owner = owner)

@app.route("/adminControls")
@flask_login.login_required
def adminControls():
	''' Render admin controls. '''
	if User.cu() != "admin":
		return redirect("/")
	users = [{"username":f[0:-5]} for f in safeListdir("data/User")
		if f not in ["admin.json","public.json"]]
	for user in users:
		userDict = json.load(open("data/User/" + user["username"] + ".json"))
		if userDict.get("password_digest"):
			user["status"] = "Registered"
		elif datetime.timedelta(1) > datetime.datetime.now() - datetime.datetime.strptime(userDict.get("timestamp",""), "%c"):
			user["status"] = "emailSent"
		else:
			user["status"] = "emailExpired"
	return render_template("adminControls.html", users = users)

@app.route("/myaccount")
@flask_login.login_required
def myaccount():
	''' Render account info for any user. '''
	return render_template("myaccount.html", user=User.cu())

@app.route("/robots.txt")
def static_from_root():
	return send_from_directory(app.static_folder, request.path[1:])

@app.route("/login_page")
def login_page():
	if flask_login.current_user.is_authenticated():
		return redirect("/")
	return render_template("clusterLogin.html")

@app.route("/logout")
def logout():
	flask_login.logout_user()
	return redirect("/")

if __name__ == "__main__":
	# TODO: remove debug?
	URL = "http://localhost:5000"
	template_files = ["templates/"+ x  for x in os.listdir("templates")]
	app.run(debug=True, extra_files=template_files)
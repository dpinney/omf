''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort, jsonify, Response
from jinja2 import Template
import models, json, os, flask_login, hashlib, random, time, datetime, shutil
from passlib.hash import pbkdf2_sha512

app = Flask("omf")

def getDataNames():
	''' Query the OMF datastore to list all the names of things that can be included.'''
	currUser = flask_login.current_user
	feeders = [x[len(currUser.username)+1:-5] for x in os.listdir('./data/Feeder/')
		if x.startswith(currUser.username + "_")]
	publicFeeders = [x[7:-5] for x in os.listdir('./data/Feeder/')
		if x.startswith('public_')]
	climates = [x[:-5] for x in os.listdir('./data/Climate/')]
	return		{'feeders':feeders, 'publicFeeders':publicFeeders, 'climates':climates, 
		'currentUser':currUser.__dict__}

def getAllData(dataType):
	''' Get metadata for everything we need for the home screen. '''
	if dataType == "Feeder":
		path = os.path.join("data", "Feeder")
	elif dataType == "Model":
		path = os.path.join("data", "Model")
	if flask_login.current_user.username == "admin":
		owners = os.listdir(path)
	else:
		owners = ["public", flask_login.current_user.username]
	allData = []
	for o in owners:
		for fname in os.listdir(os.path.join(path, o)):
			if dataType == "Feeder":
				datum = {"name":fname[:-len(".json")], "status":"Ready"}
				statstruct = os.stat(os.path.join(path, o, fname))
			elif dataType == "Model":
				datum = json.load(open(os.path.join(path, o, fname, "allInputData.json")))
				datum["name"] = datum["modelName"]
				statstruct = os.stat(os.path.join(path, o, fname, "allInputData.json"))
			datum["ctime"] = statstruct.st_ctime
			datum["formattedctime"] = time.ctime(datum["ctime"])
			datum["owner"] = o
			
			if o == "public":
				datum["url"] = "?public=true"
			else:
				datum["url"] = "?public=false"
			allData.append(datum)
	return sortAccPreferences(allData, dataType)

def strcmp(a, b):
	# Python doesn't have this built in even though it runs on top of C.  What the heck, man?
	if a < b:
		return -1
	if a == b:
		return 0
	if a > b:
		return 1

def sortAccPreferences(allData, dataType):
	'''Sort according to user preferences'''
	fname = "./data/User/"+flask_login.current_user.username+".json"
	userJson = json.load(open(fname))
	if userJson.get("sort"):
		column, i = userJson["sort"][dataType]
		if column == "name":
			return sorted(allData, cmp=lambda x, y: i*strcmp(x["name"], y["name"]))
		elif column == "ctime":
			return sorted(allData, cmp=lambda x, y: int(i*(x["ctime"] - y["ctime"])))
	return allData

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

###################################################
# AUTHENTICATION AND SECURITY STUFF
###################################################

class User:
	def __init__(self, jsonBlob):
		# I think it could possibly be useful to be able to access the json blob after the user has been loaded
		self.jsonBlob = jsonBlob
		self.username = jsonBlob["username"]
	# Required flask_login functions.
	def is_admin(self):		return self.username == "admin"
	def get_id(self): return self.username	
	def is_authenticated(self): return True
	def is_active(self): return True
	def is_anonymous(self): return False

	def __getitem__(self, key):
		# This allows us to access the json blob with user["username"], for example, instead of doing user.jsonBlob["username"]
		return self.jsonBlob[key]

	# I found myself repeating the idioms in these functions all the time, so I abstracted them into class methods.  If you want to read a user dict from json on disk, just do User.gu(<username>) and to dump do User.du(<userdict>).  Short function names because I hate typing.  They are class methods which means you don't need to instantiate the User to use them.
	@classmethod
	def gu(self, username):
		# get user
		return json.load(open("data/User/"+username+".json"))

	@classmethod
	def du(self, userdict):
		# dump user
		json.dump(userdict, open("data/User/"+userdict["username"]+".json", "w"))
	
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
# VIEWS
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

@app.route("/adminControls")
@flask_login.login_required
def adminControls():
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
	return render_template("myaccount.html",
						   user=flask_login.current_user)

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

def objIn(objectName, directory, mapfunc=lambda x: x):
	# I repeat this idiom frequently: objectName in [f.replace(".json", "") for f in os.listdir("data/Feeder/public")]
	# To do the same with this function you would do:
	# objIn(objectName, "data/Feeder/public", lambda f: f.replace(".json", ""))
	# Or to do objectName in os.listdir("data/Model/public")
	# You would simply do:
	# objIn(objectName, "data/Model/public")
	# I think this will make our code cleaner and safer and more concise
	
	return objectName in map(mapfunc, os.listdir(directory))

def nojson(objectType, directory):
	# A wrapper for objIn.  I remove ".json" from the end of files a lot
	return objIn(objectName, directory, lambda x: x.replace(".json", ""))

def pubhelper(objectType, objectName):
	# publicObject was poorly thought out and it returns "Yep"/"Nope" instead of simply true/false, so this is a helper that just returns a boolean value that is used in the actual view function to return "Yep"/"Nope"
	if objectType == "Feeder":
		return nojson(objectName, "data/Feeder/public")
	elif objectType == "Model":
		return objIn(objectName, "data/Model/public") # heck this one could also use nojson and it would be the same thing.... maybe default should be to use nojson and then we always have the underlying objIn if we want something more specific?
	
@app.route("/publicObject/<objectType>/<objectName>")
def publicObject(objectType, objectName):
	# This is supposed to be for when you are going to publish an object, and we are looking for name conflicts.
	# So it's like two layers of stupid because it returns Nope if it IS the name of a public object and Yep otherwise... I guess the intention is, Can I publish this? Nope, because it has the same name as a public object, or Yep, you can because there is no public object with that name
	# A refactor so that the front end expects true/false rather than Yep/Nope is definitely necessary
	return "Nope" if pubhelper(objectType, objectName) else "Yep"

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

@app.route("/robots.txt")
def static_from_root():
	return send_from_directory(app.static_folder, request.path[1:])

@app.route("/")
@flask_login.login_required
def root():
	return render_template('home.html', 
		analyses=[], 
		feeders=getAllData("Feeder"),
		current_user=flask_login.current_user.username, 
		is_admin = flask_login.current_user.username == "admin",
		modelNames = models.__all__)

@app.route("/getAllData/<dataType>")
@flask_login.login_required
def getAllDataView(dataType):
	return jsonify(data=getAllData(dataType))

@app.route("/sort/<dataType>/<column>", methods=["POST"])
@flask_login.login_required
def sortData(dataType, column):
	fname = "./data/User/"+flask_login.current_user.username+".json"
	userJson = json.load(open(fname))
	if not userJson.get("sort"):
		userJson["sort"] = {}
	l = userJson["sort"].get(dataType)
	# Boolean logic is tricky with negatives so I did it this way
	if l and l[0] == column:
		pass
	else:
		userJson["sort"][dataType] = [column, 1]
	userJson["sort"][dataType][1] *= -1
	with open(fname, "w") as jfile:
		json.dump(userJson, jfile, indent=4)
	return "OK"

@app.route('/feeder/<feederName>')
@flask_login.login_required
def feederGet(feederName):
	return render_template('gridEdit.html',
						   feederName=feederName,
						   ref = request.referrer,
						   is_admin = flask_login.current_user.username == "admin",
						   anaFeeder=False,
						   public = request.args.get("public") == "true")

@app.route('/feederData/<anaFeeder>/<feederName>.json')
@flask_login.login_required
def feederData(anaFeeder, feederName):
	# Not worrying about analysis feeders for right now
	# if anaFeeder == 'True':
	# 	#TODO: fix this.
	# 	data = user.get('Study', feederName)['inputJson']
	# 	del data['attachments']
	# 	return json.dumps(data)
	# else:
	path = "data/Feeder/"
	if request.args.get("public") == "true":
		path += "public"
	else:
		path += flask_login.current_user.username
	path += "/"+feederName+".json"
	return jsonify(**json.load(open(path)))

@app.route('/getComponents/')
def getComponents():
	path = "data/Component/"
	components = {name.replace(".json", ""):json.load(open(path+name)) for name in os.listdir(path)}
	return jsonify(**components)		# The flask function for returning json.  Probably takes care of some "Content-Type" headers or something

@app.route("/newModel/<modelType>")
@flask_login.login_required
def newModel(modelType):
	''' Display the module template for creating a new model. '''
	return getattr(models, modelType).renderTemplate(datastoreNames=getDataNames())

@app.route("/runModel/", methods=["POST"])
@flask_login.login_required
def runModel():
	pData = request.form.to_dict()
	modelModule = getattr(models, pData["modelType"])
	if pData.get("created","NOKEY") == "":
		# New model.
		pData["user"] = flask_login.current_user.username
		modelModule.create("./data/Model/" + pData["user"] + "/", pData)
	modelModule.run("./data/Model/" + pData["user"]+ "/" + pData["modelName"])
	return redirect("/model/" + pData["user"] + "/" + pData["modelName"])

@app.route("/model/<user>/<modelName>")
@flask_login.login_required
def showModel(user, modelName):
	''' Render a model template with saved data. '''
	modelDir = "./data/Model/" + user + "/" + modelName
	with open(modelDir + "/allInputData.json") as inJson:
		modelType = json.load(inJson)["modelType"]
	return getattr(models, modelType).renderTemplate(modelDir, False, getDataNames())

if __name__ == "__main__":
	# TODO: remove debug and extra_files arguments.
	app.run(debug=True, extra_files=["./models/gridlabSingle.html"])

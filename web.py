''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort, jsonify
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
	climates = [x[:-5] for x in os.listdir('./data/Weather/')]
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
		self.username = jsonBlob["username"]
	# Required flask_login functions.
	def is_admin(self):		return self.username == "admin"
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
# VIEWS
###################################################

@app.route("/deleteUser", methods=["POST"])
@flask_login.login_required
def deleteUser():
	if flask_login.current_user.username != "admin":
		return "You are not authorized to delete users"
	username = flask.request.form.get("username")
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
		return flask.redirect("/")
	email = flask.request.form.get("email")
	if email in [f.replace(".json", "") for f in os.listdir("data/User")]:
		u = json.load(open("data/User/"+email+".json"))
		if u.get("password_digest") or not flask.request.form.get("resend"):
			return "Already Exists"
	message = "Click the link below to register your account for the OMF.  This link will expire in 24 hours:\nreg_link"
	return send_link(email, message)

@app.route("/forgotpwd", methods=["POST"])
def forgotpwd():
	email = flask.request.form.get("email")
	try:
		user = json.load(open("data/User/"+email+".json")) # I'm repeating this idiom quite a lot.  Should abstract somehow
		message = "Click the link below to reset your password for the OMF.  This link will expire in 24 hours.\nreg_link"
		return send_link(email,message,user)
	except Exception, e:
		print e
		return "Error"

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
		is_admin = flask_login.current_user.username == "admin")

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
	if not userJson["sort"].get(dataType):
		userJson["sort"][dataType] = [column, 1]
	userJson["sort"][dataType][1] *= -1
	with open(fname, "w") as jfile:
		json.dump(userJson, jfile, indent=4)
	return "OK"



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
def showModel(modelName):
	''' Render a model template with saved data. '''
	modelDir = "./data/Model/" + user + "/" + modelName
	with open(modelDir + "/allInputData.json") as inJson:
		modelType = json.load(inJson)["modelType"]
	return getattr(models, modelType).renderTemplate(modelDirectory=modelDir,
		datastoreNames=getDataNames())

if __name__ == "__main__":
	# TODO: remove debug and extra_files arguments.
	app.run(debug=True, extra_files=["./models/gridlabSingle.html"])

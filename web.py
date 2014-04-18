''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort, jsonify, Response
from jinja2 import Template
import models, json, os, flask_login, hashlib, random, time, datetime, shutil
from passlib.hash import pbkdf2_sha512
import helperfuncs as hlp
from omfuser import User

app = Flask("omf")

def getDataNames():
	''' Query the OMF datastore to list all the names of things that can be included.'''
	currUser = flask_login.current_user
	feeders = [x[:-5] for x in os.listdir('./data/Feeder/' + currUser.username)]
	publicFeeders = [x[:-5] for x in os.listdir('./data/Feeder/public/')]
	climates = [x[:-5] for x in os.listdir('./data/Climate/')]
	return {'feeders':feeders, 'publicFeeders':publicFeeders, 'climates':climates, 
		'currentUser':currUser.__dict__}

def getAllData(dataType):
	''' Get metadata for everything we need for the home screen. '''
	# This is turning into a beast.  Requires clean up at some point.
	path = hlp.OS_PJ("data", dataType)
	if flask_login.current_user.username == "admin":
		owners = os.listdir(path)
	else:
		owners = ["public", flask_login.current_user.username]
	allData = []
	for o in owners:
		for fname in os.listdir(os.path.join(path, o)):
			if dataType in ["Feeder", "Conversion"]:
				datum = {"name":fname[:-len(".json")]}
				if dataType == "Feeder":
					datum["status"] = "Ready"
				elif dataType == "Conversion":
					datum["status"] = "converting"
				statstruct = os.stat(os.path.join(path, o, fname))
			elif dataType == "Model":
				datum = json.load(open(os.path.join(path, o, fname, "allInputData.json")))
				datum["name"] = datum["modelName"]
				statstruct = os.stat(os.path.join(path, o, fname, "allInputData.json"))
			datum["ctime"] = statstruct.st_ctime
			datum["formattedctime"] = time.ctime(datum["ctime"])
			datum["owner"] = o
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
	# So it's like two layers of stupid because it returns Nope if it IS the name of a public object and Yep otherwise... I guess the intention is, Can I publish this? Nope, because it has the same name as a public object, or Yep, you can because there is no public object with that name
	# A refactor so that the front end expects true/false rather than Yep/Nope is definitely necessary
	return "Nope" if hlp.pubhelper(objectType, objectName) else "Yep"

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
	if dataType == "Feeder":
		return jsonify(data=getAllData("Feeder")+getAllData("Conversion"))
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

@app.route('/feeder/<owner>/<feederName>')
@flask_login.login_required
def feederGet(owner, feederName):
	return render_template('gridEdit.html',
						   feederName=feederName,
						   ref = request.referrer,
						   is_admin = User.ia(),
						   modelFeeder=False,
						   public = owner == "public", 
						   # ^Kinda want to get rid of this
						   currUser = User.cu(),
						   owner = owner)

@app.route("/feederData/<owner>/<feederName>/") 
@app.route("/feederData/<owner>/<feederName>/<modelFeeder>") # None of this .json nonsense, ya silly goose
@flask_login.login_required
def feederData(owner, feederName, modelFeeder=False):
	# Dealing with this modelFeeder stuff later
	if User.ia() or owner == User.cu() or owner == "public":
		# This is so weird.  the json.load returned a unicode string for some reason so I used json.loads around it to turn it into a dictionary.  Something wonky is going on here because that doesn't make sense.
		return jsonify(**json.loads(json.load(open(hlp.feederPath(owner, feederName)))))

@app.route("/getComponents/")
def getComponents():
	path = "data/Component/"
	components = {name.replace(".json", ""):json.load(open(path+name))
		for name in os.listdir(path)}
	return jsonify(**components)

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
		modelModule.create("./data/Model/", pData)
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

@app.route('/uniqueName/<objectType>/<name>')
@flask_login.login_required
def uniqueName(objectType, name):
	return hlp.nojson(objectType, name)


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
	# If the owner is public, then the current user must be admin
	# The admin is also allowed to do whatever the durn eff he pleases
	postObject = request.form.to_dict()
	if owner == User.cu() or User.ia():
		# Then feel free to dump
		json.dump(postObject["feederObjectJson"], open(hlp.feederPath(owner, feederName), "w"))
	return redirect(request.form.get("ref", "/#feeders"))

@app.route('/milsoftImport/', methods=['POST'])
@flask_login.login_required
def milsoftImport():
	feederName = str(flask.request.form.to_dict()['feederName'])
	stdString, seqString = map(lambda x: flask.request.files[x].stream.read(), ["stdFile", "seqFile"])
	worker.milImport(User.cu(), current_user.prepend+feederName, stdString, seqString)
	hlp.conversionDump(User.cu(), feederName, {"data":"none"})
	return flask.redirect('/#feeders')

@app.route('/gridlabdImport/', methods=['POST'])
@flask_login.login_required
def gridlabdImport():
	feederName = str(flask.request.form.to_dict()['feederName'])
	newFeeder = dict(**hlp.newFeederWireframe)	# copies the dictionary..
	newFeeder['tree'] = feeder.parse(flask.request.files['glmFile'].stream.read(), False)
	newFeeder['layoutVars']['xScale'] = 0
	newFeeder['layoutVars']['yScale'] = 0
	with open('./schedules.glm','r') as schedFile:
		newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
	hlp.feederDump(User.cu(), feederName, newFeeder)
	return flask.redirect('/#feeders')

if __name__ == "__main__":
	# TODO: remove debug.
	app.run(debug=True)

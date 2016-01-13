''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort, jsonify, Response
from jinja2 import Template
from multiprocessing import Process
from passlib.hash import pbkdf2_sha512
import json, os, flask_login, hashlib, random, time, datetime as dt, shutil, boto.ses
import models, feeder, milToGridlab
import cymeToGridlab

app = Flask("web")
URL = "http://www.omf.coop"
_omfDir = os.path.dirname(os.path.abspath(__file__))

###################################################
# HELPER FUNCTIONS
###################################################

def safeListdir(path):
	''' Helper function that returns [] for dirs that don't exist. Otherwise new users can cause exceptions. '''
	try: return [x for x in os.listdir(path) if not x.startswith(".")]
	except:	return []

def getDataNames():
	''' Query the OMF datastore to get names of all objects.'''
	try:
		currUser = User.cu()
	except:
		currUser = "public"
	feeders = [x[:-5] for x in safeListdir("./data/Feeder/" + currUser)]
	publicFeeders = [x[:-5] for x in safeListdir("./data/Feeder/public/")]
	climates = [x[:-5] for x in safeListdir("./data/Climate/")]
	return {"feeders":sorted(feeders), "publicFeeders":sorted(publicFeeders), "climates":sorted(climates), 
		"currentUser":currUser}

@app.before_request
def csrf_protect():
	if request.user_agent.browser != "chrome":
		return "<img style='width:400px;margin-right:auto; margin-left:auto;display:block;' \
			src='http://goo.gl/1GvUMA'><br> \
			<h2 style='text-align:center'>The OMF currently must be accessed by <a href='http://goo.gl/X2ZGhb''>Chrome</a></h2>"
	## NOTE: when we fix csrf validation this needs to be uncommented.
	# if request.method == "POST":
	#	token = session.get("_csrf_token", None)
	#	if not token or token != request.form.get("_csrf_token"):
	#		abort(403)

###################################################
# AUTHENTICATION AND USER FUNCTIONS
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
login_manager.login_view = "login_page"
app.secret_key = cryptoRandomString()

def send_link(email, message, u={}):
	''' Send message to email using Amazon SES. '''
	try:
		key = open("emailCredentials.key").read()
		c = boto.ses.connect_to_region("us-east-1",
			aws_access_key_id="AKIAJLART4NXGCNFEJIQ",
			aws_secret_access_key=key)
		reg_key = hashlib.md5(str(time.time())+str(random.random())).hexdigest()
		u["reg_key"] = reg_key
		u["timestamp"] = dt.datetime.strftime(dt.datetime.now(), format="%c")
		u["registered"] = False
		u["email"] = email
		outDict = c.send_email("admin@omf.coop", "OMF Registration Link",
			message.replace("reg_link", URL+"/register/"+email+"/"+reg_key), [email])
		json.dump(u, open("data/User/"+email+".json", "w"), indent=4)
		return "Success"
	except:
		return "Failed"

@login_manager.user_loader
def load_user(username):
	''' Required by flask_login to return instance of the current user '''
	return User(json.load(open("./data/User/" + username + ".json")))

def generate_csrf_token():
	if "_csrf_token" not in session:
		session["_csrf_token"] = cryptoRandomString()
	return session["_csrf_token"]

app.jinja_env.globals["csrf_token"] = generate_csrf_token

@app.route("/login", methods = ["POST"])
def login():
	''' Authenticate a user and send them to the URL they requested. '''
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
	nextUrl = str(request.form.get("next","/"))
	return redirect(nextUrl)

@app.route("/login_page")
def login_page():
	nextUrl = str(request.args.get("next","/"))
	if flask_login.current_user.is_authenticated():
		return redirect(urlTarget)
	# Generate list of models with quickRun
	modelNames = []
	for modelName in models.__all__:
		thisModel = getattr(models, modelName)
		if hasattr(thisModel, 'quickRender'):
			modelNames.append(modelName)
	if not modelNames:
		modelNames.append("No Models Available")
	return render_template("clusterLogin.html", next=nextUrl, modelNames=modelNames)

@app.route("/logout")
def logout():
	flask_login.logout_user()
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
	print "SUCCESFULLY DELETE USER", username
	return "Success"

@app.route("/new_user", methods=["POST"])
# @flask_login.login_required #TODO: REVIEW
def new_user():
	email = request.form.get("email")
	if email == "": return "EMPTY"
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
		user = json.load(open("data/User/" + email + ".json"))
		message = "Click the link below to reset your password for the OMF.  This link will expire in 24 hours.\n\nreg_link"
		return send_link(email, message, user)
	except Exception, e:
		print "ERROR: failed to password reset user", email, "with exception", e
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
			dt.timedelta(1) > dt.datetime.now() - dt.datetime.strptime(user.get("timestamp"), "%c")):
		return "This page either expired, or you are not supposed to access it.  It might not even exist"
	if request.method == "GET":
		return render_template("register.html", email=email)
	password, confirm_password = map(request.form.get, ["password", "confirm_password"])
	if password == confirm_password:
		user["username"] = email
		user["password_digest"] = pbkdf2_sha512.encrypt(password)
		flask_login.login_user(User(user))
		with open("data/User/"+user["username"]+".json","w") as outFile:
			json.dump(user, outFile, indent=4)
	return redirect("/")

@app.route("/changepwd", methods=["POST"])
@flask_login.login_required
def changepwd():
	old_pwd, new_pwd, conf_pwd = map(request.form.get, ["old_pwd", "new_pwd", "conf_pwd"])
	user = json.load(open("./data/User/" + User.cu() + ".json"))
	if pbkdf2_sha512.verify(old_pwd, user["password_digest"]):
		if new_pwd == conf_pwd:
			user["password_digest"] = pbkdf2_sha512.encrypt(new_pwd)
			with open("./data/User/" + User.cu() + ".json","w") as outFile:
				json.dump(user, outFile, indent=4)
			return "Success"
		else:
			return "not_match"
	else:
		return "not_auth"

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
		tStamp = userDict.get("timestamp","")
		if userDict.get("password_digest"):
			user["status"] = "Registered"
		elif dt.timedelta(1) > dt.datetime.now() - dt.datetime.strptime(tStamp, "%c"):
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

###################################################
# MODEL FUNCTIONS
###################################################

@app.route("/model/<owner>/<modelName>")
@flask_login.login_required
def showModel(owner, modelName):
	''' Render a model template with saved data. '''
	if owner==User.cu() or "admin"==User.cu() or owner=="public":
		modelDir = "./data/Model/" + owner + "/" + modelName
		with open(modelDir + "/allInputData.json") as inJson:
			modelType = json.load(inJson).get("modelType","")
		thisModel = getattr(models, modelType) 
		return thisModel.renderTemplate(thisModel.template, modelDir, False, getDataNames())
	else:
		return redirect("/")

@app.route("/newModel/<modelType>")
@flask_login.login_required
def newModel(modelType):
	''' Display the module template for creating a new model. '''
	thisModel = getattr(models, modelType)
	return thisModel.renderTemplate(thisModel.template, datastoreNames=getDataNames())

@app.route("/runModel/", methods=["POST"])
@flask_login.login_required
def runModel():
	''' Start a model running and redirect to its running screen. '''
	pData = request.form.to_dict()
	modelModule = getattr(models, pData["modelType"])
	# Handle the user.
	if User.cu() == "admin" and pData["user"] == "public":
		user = "public"
	elif User.cu() == "admin" and pData["user"] != "public" and pData["user"] != "":
		user = pData["user"].replace('/','')
	else:
		user = User.cu()
	del pData["user"]
	# Handle the model name.
	modelName = pData["modelName"]
	del pData["modelName"]
	modelModule.run(os.path.join(_omfDir, "data", "Model", user, modelName), pData)
	return redirect("/model/" + user + "/" + modelName)

@app.route("/quickNew/<modelType>")
def quickNew(modelType):
	thisModel = getattr(models, modelType)
	if hasattr(thisModel, 'quickRender'):
		return thisModel.quickRender(thisModel.template, datastoreNames=getDataNames())
	else:
		return redirect("/")

@app.route("/quickRun/", methods=["POST"])
def quickRun():
	pData = request.form.to_dict()
	modelModule = getattr(models, pData["modelType"])
	user = pData["quickRunEmail"]
	modelName = "QUICKRUN-" + pData["modelType"]
	modelModule.run(os.path.join(_omfDir, "data", "Model", user, modelName), pData)
	return redirect("/quickModel/" + user + "/" + modelName)

@app.route("/quickModel/<owner>/<modelName>")
def quickModel(owner, modelName):
	''' Render a quickrun model template with saved data. '''
	modelDir = "./data/Model/" + owner + "/" + modelName
	with open(modelDir + "/allInputData.json") as inJson:
		modelType = json.load(inJson).get("modelType","")
	thisModel = getattr(models, modelType)
	return thisModel.quickRender(thisModel.template, modelDir, False, getDataNames())

@app.route("/cancelModel/", methods=["POST"])
@flask_login.login_required
def cancelModel():
	''' Cancel an already running model. '''
	pData = request.form.to_dict()
	modelModule = getattr(models, pData["modelType"])
	modelModule.cancel(os.path.join(_omfDir,"data","Model",pData["user"],pData["modelName"]))
	return redirect("/model/" + pData["user"] + "/" + pData["modelName"])

@app.route("/duplicateModel/<owner>/<modelName>/", methods=["POST"])
@flask_login.login_required
def duplicateModel(owner, modelName):
	newName = request.form.get("newName","")
	if owner==User.cu() or "admin"==User.cu() or "public"==owner:
		destinationPath = "./data/Model/" + User.cu() + "/" + newName
		shutil.copytree("./data/Model/" + owner + "/" + modelName, destinationPath)
		with open(destinationPath + "/allInputData.json","r") as inFile:
			inData = json.load(inFile)
		inData["created"] = str(dt.datetime.now())
		with open(destinationPath + "/allInputData.json","w") as outFile:
			json.dump(inData, outFile, indent=4)
		return redirect("/model/" + User.cu() + "/" + newName)
	else:
		return False

@app.route("/publishModel/<owner>/<modelName>/", methods=["POST"])
@flask_login.login_required
def publishModel(owner, modelName):
	newName = request.form.get("newName","")
	if owner==User.cu() or "admin"==User.cu():
		destinationPath = "./data/Model/public/" + newName
		shutil.copytree("./data/Model/" + owner + "/" + modelName, destinationPath)
		with open(destinationPath + "/allInputData.json","r+") as inFile:
			inData = json.load(inFile)
			inData["created"] = str(dt.datetime.now())
			inFile.seek(0)
			json.dump(inData, inFile, indent=4)
		return redirect("/model/public/" + newName)
	else:
		return False

###################################################
# FEEDER FUNCTIONS
###################################################

@app.route("/feeder/<owner>/<feederName>")
@flask_login.login_required
def feederGet(owner, feederName):
	''' Editing interface for feeders. '''
	# MAYBEFIX: fix modelFeeder
	return render_template("gridEdit.html", feederName=feederName, ref=request.referrer,
		is_admin=User.cu()=="admin", modelFeeder=False, public=owner=="public",
		currUser = User.cu(), owner = owner)

@app.route("/getComponents/")
@flask_login.login_required
def getComponents():
	path = "data/Component/"
	components = {name[0:-5]:json.load(open(path + name)) for name in os.listdir(path)}
	return json.dumps(components)

@app.route("/milsoftImport/", methods=["POST"])
@flask_login.login_required
def milsoftImport():
	''' API for importing a milsoft feeder. '''
	feederName = str(request.form.get("feederName",""))
	stdString, seqString = map(lambda x: request.files[x].stream.read(), ["stdFile", "seqFile"])
	if not os.path.isdir("data/Conversion/" + User.cu()):
		os.makedirs("data/Conversion/" + User.cu())
	with open("data/Conversion/" + User.cu() + "/" + feederName + ".json", "w+") as conFile:
		conFile.write("WORKING")
	importProc = Process(target=milImportBackground, args=[User.cu(), feederName, stdString, seqString])
	importProc.start()
	return redirect("/#feeders")

def milImportBackground(owner, feederName, stdString, seqString):
	''' Function to run in the background for Milsoft import. '''
	newFeeder = dict(**feeder.newFeederWireframe)
	[newFeeder["tree"], xScale, yScale] = milToGridlab.convert(stdString, seqString)
	newFeeder["layoutVars"]["xScale"] = xScale
	newFeeder["layoutVars"]["yScale"] = yScale
	with open("./schedules.glm","r") as schedFile:
		newFeeder["attachments"] = {"schedules.glm":schedFile.read()}
	with open("data/Feeder/" + owner + "/" + feederName + ".json", "w") as outFile:
		json.dump(newFeeder, outFile, indent=4)
	os.remove("data/Conversion/" + owner + "/" + feederName + ".json")

@app.route("/gridlabdImport/", methods=["POST"])
@flask_login.login_required
def gridlabdImport():
	'''This function is used for gridlabdImporting'''
	feederName = str(request.form.get("feederName",""))
	glmString = request.files["glmFile"].stream.read()
	if not os.path.isdir("data/Conversion/" + User.cu()):
		os.makedirs("data/Conversion/" + User.cu())
	with open("data/Conversion/" + User.cu() + "/" + feederName + ".json", "w+") as conFile:
		conFile.write("WORKING")
	importProc = Process(target=gridlabImportBackground, args=[User.cu(), feederName, glmString])
	importProc.start()
	return redirect("/#feeders")

def gridlabImportBackground(owner, feederName, glmString):
	''' Function to run in the background for Milsoft import. '''
	newFeeder = dict(**feeder.newFeederWireframe)
 	newFeeder["tree"] = feeder.parse(glmString, False)
 	newFeeder["layoutVars"]["xScale"] = 0
 	newFeeder["layoutVars"]["yScale"] = 0
	with open("./schedules.glm","r") as schedFile:
		newFeeder["attachments"] = {"schedules.glm":schedFile.read()}
	with open("data/Feeder/" + owner + "/" + feederName + ".json", "w") as outFile:
		json.dump(newFeeder, outFile, indent=4)
	os.remove("data/Conversion/" + owner + "/" + feederName + ".json")

# TODO: Check if rename mdb files worked
@app.route("/cymeImport/", methods=["POST"])
@flask_login.login_required
def cymeImport():
	''' API for importing a cyme feeder. '''
	feederName = str(request.form.get("feederName",""))
	mdbNetString, mdbEqString = map(lambda x: request.files[x], ["mdbNetFile", "mdbEqFile"])
	if not os.path.isdir("data/Conversion/" + User.cu()):
		os.makedirs("data/Conversion/" + User.cu())
	with open("data/Conversion/" + User.cu() + "/" + feederName + ".json", "w+") as conFile:
		conFile.write("WORKING")
	importProc = Process(target=cymeImportBackground, args=[User.cu(), feederName, mdbNetString.filename, mdbEqString.filename])
	importProc.start()
	return redirect("/#feeders")

def cymeImportBackground(owner, feederName, mdbNetString, mdbEqString):
	''' Function to run in the background for Milsoft import. '''
	newFeeder = dict(**feeder.newFeederWireframe)
	[newFeeder["tree"], xScale, yScale] = cymeToGridlab.convertCymeModel(mdbNetString, mdbEqString)
	newFeeder["layoutVars"]["xScale"] = xScale
	newFeeder["layoutVars"]["yScale"] = yScale
	with open("./schedules.glm","r") as schedFile:
		newFeeder["attachments"] = {"schedules.glm":schedFile.read()}
	with open("data/Feeder/" + owner + "/" + feederName + ".json", "w") as outFile:
		json.dump(newFeeder, outFile, indent=4)
	os.remove("data/Conversion/" + owner + "/" + feederName + ".json")

@app.route("/newBlankFeeder/", methods=["POST"])
@flask_login.login_required
def newBlankFeeder():
	'''This function is used for creating a new blank feeder.'''
	feederName = str(request.form.get("feederName",""))
	with open("./static/SimpleFeeder.json", "r") as simpleFeederFile:
		with open("data/Feeder/" + User.cu() + "/" + feederName + ".json", "w") as outFile:
			outFile.write(simpleFeederFile.read())
	feederLink = "./feeder/" + User.cu() + "/" + feederName
	return redirect(feederLink)
	
@app.route("/feederData/<owner>/<feederName>/") 
@app.route("/feederData/<owner>/<feederName>/<modelFeeder>")
@flask_login.login_required
def feederData(owner, feederName, modelFeeder=False):
	#MAYBEFIX: fix modelFeeder capability.
	if User.cu()=="admin" or owner==User.cu() or owner=="public":
		with open("data/Feeder/" + owner + "/" + feederName + ".json", "r") as feedFile:
			return feedFile.read()

@app.route("/saveFeeder/<owner>/<feederName>", methods=["POST"])
@flask_login.login_required
def saveFeeder(owner, feederName):
	''' Save feeder data. '''
	if owner == User.cu() or "admin" == User.cu() or owner=="public":
		# If we have a new user, make sure to make their folder:
		if not os.path.isdir("data/Feeder/" + owner):
			os.makedirs("data/Feeder/" + owner)
		with open("data/Feeder/" + owner + "/" + feederName + ".json", "w") as outFile:
			payload = json.loads(request.form.to_dict().get("feederObjectJson","{}"))
			json.dump(payload, outFile, indent=4)
	return redirect("/#feeders")

###################################################
# OTHER FUNCTIONS
###################################################

@app.route("/")
@flask_login.login_required
def root():
	''' Render the home screen of the OMF. '''
	# Gather object names.
	publicModels = [{"owner":"public","name":x} for x in safeListdir("data/Model/public/")]
	userModels = [{"owner":User.cu(), "name":x} for x in safeListdir("data/Model/" + User.cu())]
	publicFeeders = [{"owner":"public","name":x[0:-5],"status":"Ready"} for x in safeListdir("data/Feeder/public/")]
	userFeeders = [{"owner":User.cu(),"name":x[0:-5],"status":"Ready"} for x in safeListdir("data/Feeder/" + User.cu())]
	conversions = [{"owner":User.cu(),"name":x[0:-5],"status":"Converting"} for x in safeListdir("data/Conversion/" + User.cu())]
	allModels = publicModels + userModels
	allFeeders = publicFeeders + userFeeders
	# Allow admin to see all models and feeders.
	isAdmin = User.cu() == "admin"
	if isAdmin:
		allFeeders = [{"owner":owner,"name":feed[0:-5],"status":"Ready"} for owner in safeListdir("data/Feeder/")
			for feed in safeListdir("data/Feeder/" + owner)]
		allModels = [{"owner":owner,"name":mod} for owner in safeListdir("data/Model/") 
			for mod in safeListdir("data/Model/" + owner)]
	# Grab metadata for models and feeders.
	for mod in allModels:
		try:
			modPath = "data/Model/" + mod["owner"] + "/" + mod["name"]
			allInput = json.load(open(modPath + "/allInputData.json"))
			mod["runTime"] = allInput.get("runTime","")
			mod["modelType"] = allInput.get("modelType","")
			mod["status"] = getattr(models, mod["modelType"]).getStatus(modPath)
			# mod["created"] = allInput.get("created","")
			mod["editDate"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(os.stat(modPath).st_ctime)) 
		except:
			continue
	for feed in allFeeders:
		try:
			feedPath = "data/Feeder/" + feed["owner"] + "/" + feed["name"] + ".json"
			feed["editDate"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(os.stat(feedPath).st_ctime))
		except:
			continue
	for conversion in conversions:
		try:
			convPath = "data/Conversion/" + conversion["owner"] + "/" + conversion["name"] + ".json"
			conversion["editDate"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(os.stat(convPath).st_ctime))		
		except:
			continue
	return render_template("home.html", models = allModels, feeders = allFeeders + conversions,
		current_user = User.cu(), is_admin = isAdmin, modelNames = models.__all__)

@app.route("/delete/<objectType>/<owner>/<objectName>", methods=["POST"])
@flask_login.login_required
def delete(objectType, objectName, owner):
	''' Delete models or feeders. '''
	if owner != User.cu() and User.cu() != "admin":
		return False
	if objectType == "Feeder":
		os.remove("data/Feeder/" + owner + "/" + objectName + ".json")
		return redirect("/#feeders")
	elif objectType == "Model":
		shutil.rmtree("data/Model/" + owner + "/" + objectName)
	return redirect("/")

@app.route("/downloadModelData/<owner>/<modelName>/<path:fullPath>")
@flask_login.login_required
def downloadModelData(owner, modelName, fullPath):
	pathPieces = fullPath.split('/')
	return send_from_directory("data/Model/"+owner+"/"+modelName+"/"+"/".join(pathPieces[0:-1]), pathPieces[-1])

@app.route("/uniqObjName/<objtype>/<owner>/<name>")
@flask_login.login_required
def uniqObjName(objtype, owner, name):
	''' Checks if a given object type/owner/name is unique. '''
	if objtype == "Model":
		path = "data/Model/" + owner + "/" + name
	elif objtype == "Feeder":
		path = "data/Feeder/" + owner + "/" + name + ".json"
	return jsonify(exists=os.path.exists(path))

if __name__ == "__main__":
	URL = "http://localhost:5000"
	template_files = ["templates/"+ x  for x in os.listdir("templates")]
	model_files = ["models/" + x for x in os.listdir("models")]
	app.run(debug=True, extra_files=template_files + model_files)

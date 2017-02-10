''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort, jsonify, Response, url_for
from jinja2 import Template
from multiprocessing import Process
from passlib.hash import pbkdf2_sha512
import json, os, flask_login, hashlib, random, time, datetime as dt, shutil, boto.ses, csv
import models, feeder, network, milToGridlab
import signal
import cymeToGridlab
import omf
from omf.calibrate import omfCalibrate

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
	climates = [x[:-5] for x in safeListdir("./data/Climate/")]
	feeders = []
	for (dirpath, dirnames, filenames) in os.walk(os.path.join(_omfDir, "data","Model", currUser)):
		for file in filenames:
			if '.omd' in file and file != 'feeder.omd':
				feeders.append({'name': file.strip('.omd'), 'model': dirpath.split('/')[-1]})
	networks = []
	for (dirpath, dirnames, filenames) in os.walk(os.path.join(_omfDir, "scratch","transmission", "outData")):
		for file in filenames:
			if '.omt' in file and file != 'feeder.omt':
				networks.append({'name': file.strip('.omt'), 'model': 'DRPOWER'})
	# Public feeders too.
	publicFeeders = []
	for (dirpath, dirnames, filenames) in os.walk(os.path.join(_omfDir, "data","Model", "public")):
		for file in filenames:
			if '.omd' in file and file != 'feeder.omd':
				publicFeeders.append({'name': file.strip('.omd'), 'model': dirpath.split('/')[-1]})		
	return {"climates":sorted(climates), "feeders":feeders, "networks":networks, "publicFeeders":publicFeeders, "currentUser":currUser}

@app.before_request
def csrf_protect():
	pass
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
	for u in safeListdir("./data/User/"):
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
	# Generate list of models:
	modelNames = []
	for modelName in models.__all__:
		thisModel = getattr(models, modelName)
		if not modelName.startswith('_'):
			modelNames.append(modelName)
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
	try:
		shutil.rmtree("data/Model/" + username)
	except Exception, e:
		print "USER DATA DELETION FAILED FOR", e
	os.remove("data/User/" + username + ".json")
	print "SUCCESFULLY DELETE USER", username
	return "Success"

@app.route("/new_user", methods=["POST"])
def new_user():
	email = request.form.get("email")
	if email == "": return "EMPTY"
	if email in [f[0:-5] for f in safeListdir("data/User")]:
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
		return "This page either expired, or you are not supposed to access it. It might not even exist"
	if request.method == "GET":
		return render_template("register.html", email=email)
	password, confirm_password = map(request.form.get, ["password", "confirm_password"])
	if password == confirm_password and request.form.get("legalAccepted","") == "on":
		user["username"] = email
		user["password_digest"] = pbkdf2_sha512.encrypt(password)
		flask_login.login_user(User(user))
		with open("data/User/"+user["username"]+".json","w") as outFile:
			json.dump(user, outFile, indent=4)
	else:
		return "Passwords must both match and you must accept the Terms of Use and Privacy Policy. Please go back and try again."
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
		return thisModel.renderTemplate(modelDir, absolutePaths=False, datastoreNames=getDataNames())
	else:
		return redirect("/")

@app.route("/newModel/<modelType>/<modelName>", methods=["POST","GET"])
@flask_login.login_required
def newModel(modelType, modelName):
	''' Create a new model with given name. '''
	modelDir = os.path.join(_omfDir, "data", "Model", User.cu(), modelName)
	thisModel = getattr(models, modelType)
	thisModel.new(modelDir)
	return redirect("/model/" + User.cu() + "/" + modelName)

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

@app.route("/fastRun/<modelType>/<email>")
def fastRun(modelType, email):
	''' Create a new user, email them their password, and immediately create a new model for them.'''
	if email in [f[0:-5] for f in safeListdir("data/User")]:
		return "User with email {} already exists. Please log in or go back and use the 'Forgot Password' link. Or try the fast model creation feature with a different email address.".format(email)
	else:
		randomPass = ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for x in range(15)])
		user = {"username":email, "password_digest":pbkdf2_sha512.encrypt(randomPass)}
		flask_login.login_user(User(user))
		with open("data/User/"+user["username"]+".json","w") as outFile:
			json.dump(user, outFile, indent=4)
		message = "Thanks for registering for OMF.coop. Your password is: " + randomPass
		key = open("emailCredentials.key").read()
		c = boto.ses.connect_to_region("us-east-1", aws_access_key_id="AKIAJLART4NXGCNFEJIQ", aws_secret_access_key=key)
		mailResult = c.send_email("admin@omf.coop", "OMF.coop User Account", message, [email])
		return redirect("/newModel/" + modelType + "/FASTRUN" + modelType)

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

def writeToInput(workDir, entry, key):
	try:
		with open(workDir + "/allInputData.json") as inJson:
			allInput = json.load(inJson)
		allInput[key] = entry
		with open(workDir+"/allInputData.json","w") as inputFile:
			json.dump(allInput, inputFile, indent = 4)
	except: return "Failed"

@app.route("/feeder/<owner>/<modelName>/<feederNum>")
@flask_login.login_required
def feederGet(owner, modelName, feederNum):
	''' Editing interface for feeders. '''
	allData = getDataNames()
	yourFeeders = allData["feeders"]
	publicFeeders = allData["publicFeeders"]
	modelDir = os.path.join(_omfDir, "data","Model", owner, modelName)
	feederName = json.load(open(modelDir + "/allInputData.json")).get('feederName'+str(feederNum))
	# MAYBEFIX: fix modelFeeder
	return render_template("gridEdit.html", feeders=yourFeeders, publicFeeders=publicFeeders, modelName=modelName, feederName=feederName, feederNum=feederNum, ref=request.referrer, is_admin=User.cu()=="admin", modelFeeder=False, public=owner=="public",
		currUser = User.cu(), owner = owner)

@app.route("/network/<owner>/<modelName>/<networkNum>")
@flask_login.login_required
def networkGet(owner, modelName, networkNum):
	''' Editing interface for networks. '''
	allData = getDataNames()
	yourNetworks = allData["networks"]
	publicNetworks = allData["networks"]
	modelDir = os.path.join(_omfDir, "data","Model", owner, modelName)
	networkName = json.load(open(modelDir + "/allInputData.json")).get('networkName')
	networkPath = modelDir + "/" + networkName + ".omt"
	with open(modelDir + "/" + networkName + ".omt", "r") as netFile:
		networkData = json.dumps(json.load(netFile), indent=4)
	return render_template("transEdit.html", networks=yourNetworks, publicNetworks=publicNetworks, modelName=modelName, networkData=networkData, networkName=networkName, networkNum=networkNum, ref=request.referrer, is_admin=User.cu()=="admin", public=owner=="public",
		currUser = User.cu(), owner = owner)

@app.route("/getComponents/")
@flask_login.login_required
def getComponents():
	path = "data/Component/"
	components = {name[0:-5]:json.load(open(path + name)) for name in safeListdir(path)}
	return json.dumps(components)

@app.route("/checkConversion/<modelName>", methods=["POST","GET"])
def checkConversion(modelName):
	print modelName
	owner = User.cu()
	path = ("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt")
	errorPath = "data/Model/"+owner+"/"+modelName+"/gridError.txt"
	print "Check conversion status:", os.path.exists(path), "for path", path
	if os.path.isfile(errorPath):
		with open(errorPath) as errorFile:
			errorString = errorFile.read()
			os.remove(errorPath)
		return errorString
	else:
		return jsonify(exists=os.path.exists(path))

@app.route("/milsoftImport/<owner>", methods=["POST"])
@flask_login.login_required
def milsoftImport(owner):
	''' API for importing a milsoft feeder. '''
	modelName = request.form.get("modelName","")
	feederName = str(request.form.get("feederNameM","feeder"))
	modelFolder = "data/Model/"+owner+"/"+modelName
	feederNum = request.form.get("feederNum",1)
	# Delete exisitng .std and .seq, .glm files to not clutter model file
	path = "data/Model/"+owner+"/"+modelName
	fileList = safeListdir(path)
	for file in fileList:
		if file.endswith(".glm") or file.endswith(".std") or file.endswith(".seq"):
			os.remove(path+"/"+file)
	stdFile, seqFile = map(lambda x: request.files[x], ["stdFile", "seqFile"])
	# stdFile, seqFile= request.files['stdFile','seqFile']
	stdFile.save(os.path.join(modelFolder,feederName+'.std'))
	seqFile.save(os.path.join(modelFolder,feederName+'.seq'))
	if os.path.isfile("data/Model/"+owner+"/"+modelName+"/gridError.txt"):
		os.remove("data/Model/"+owner+"/"+modelName+"/gridError.txt")
	with open("data/Model/"+owner+"/"+modelName+'/'+feederName+'.std') as stdInput:
		stdString = stdInput.read()
	with open("data/Model/"+owner+"/"+modelName+'/'+feederName+'.seq') as seqInput:
		seqString = seqInput.read()
	with open("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt", "w+") as conFile:
		conFile.write("WORKING")
	importProc = Process(target=milImportBackground, args=[owner, modelName, feederName, feederNum, stdString, seqString])
	importProc.start()
	return ('',204)

def milImportBackground(owner, modelName, feederName, feederNum, stdString, seqString):
	''' Function to run in the background for Milsoft import. '''
	modelDir = "data/Model/"+owner+"/"+modelName
	feederDir = modelDir+"/"+feederName+".omd"
	newFeeder = dict(**feeder.newFeederWireframe)
	[newFeeder["tree"], xScale, yScale] = milToGridlab.convert(stdString, seqString)
	newFeeder["layoutVars"]["xScale"] = xScale
	newFeeder["layoutVars"]["yScale"] = yScale
	with open("./schedules.glm","r") as schedFile:
		newFeeder["attachments"] = {"schedules.glm":schedFile.read()}
	try: os.remove(feederDir)
	except: pass
	with open(feederDir, "w") as outFile:
		json.dump(newFeeder, outFile, indent=4)
	with open(feederDir) as feederFile:
		feederTree =  json.load(feederFile)
	if len(feederTree['tree']) < 12:
		with open("data/Model/"+owner+"/"+modelName+"/gridError.txt", "w+") as errorFile:
			errorFile.write('milError')
	os.remove("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt")
	removeFeeder(owner, modelName, feederNum)
	writeToInput(modelDir, feederName, 'feederName'+str(feederNum))

@app.route("/matpowerImport/<owner>", methods=["POST"])
@flask_login.login_required
def matpowerImport(owner):
	''' API for importing a milsoft feeder. '''
	modelName = request.form.get("modelName","")
	networkName = str(request.form.get("networkNameM","network1"))
	networkNum = request.form.get("networkNum",1)
	# Delete existing .m files to not clutter model
	path = "data/Model/"+owner+"/"+modelName
	fileList = safeListdir(path)
	for file in fileList:
		if file.endswith(".m"): os.remove(path+"/"+file)
	matFile = request.files["matFile"]
	matFile.save(os.path.join("data/Model/"+owner+"/"+modelName,networkName+'.m'))
	# TODO: Remove error files.
	with open("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt", "w+") as conFile:
		conFile.write("WORKING")
	importProc = Process(target=matImportBackground, args=[owner, modelName, networkName, networkNum])
	importProc.start()
	return ('',204)

def matImportBackground(owner, modelName, networkName, networkNum):
	''' Function to run in the background for Milsoft import. '''
	# TODO: Layout vars x/y scale left over from d3?
	modelDir = "data/Model/"+owner+"/"+modelName
	networkDir = modelDir+"/"+networkName+".m"
	newFeeder = network.parse(networkDir, filePath=True)
	nxG = network.netToNxGraph(newFeeder)
	newFeeder = network.latlonToNet(nxG, newFeeder)
	try: os.remove(networkDir)
	except: pass
	with open(networkDir.replace('.m','.omt'), "w") as outFile:
		json.dump(newFeeder, outFile, indent=4)
	os.remove("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt")
	removeNetwork(owner, modelName, networkNum)
	writeToInput(modelDir, networkName, 'networkName'+str(networkNum))

@app.route("/gridlabdImport/<owner>", methods=["POST"])
@flask_login.login_required
def gridlabdImport(owner):
	'''This function is used for gridlabdImporting'''
	modelName = request.form.get("modelName","")
	feederName = str(request.form.get("feederNameG",""))
	feederNum = request.form.get("feederNum",1)
	glm = request.files['glmFile']
	# Delete exisitng .std and .seq, .glm files to not clutter model file
	path = "data/Model/"+owner+"/"+modelName
	fileList = safeListdir(path)
	for file in fileList:
		if file.endswith(".glm") or file.endswith(".std") or file.endswith(".seq"):
			os.remove(path+"/"+file)
	# Save .glm file to model folder
	glm.save(os.path.join("data/Model/"+owner+"/"+modelName,feederName+'.glm'))
	with open("data/Model/"+owner+"/"+modelName+'/'+feederName+'.glm') as glmFile:
		glmString = glmFile.read()
	if os.path.isfile("data/Model/"+owner+"/"+modelName+"/gridError.txt"):
		os.remove("data/Model/"+owner+"/"+modelName+"/gridError.txt")
	with open("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt", "w+") as conFile:
		conFile.write("WORKING")
	importProc = Process(target=gridlabImportBackground, args=[owner, modelName, feederName, feederNum, glmString])
	importProc.start()
	return ('',204)

def gridlabImportBackground(owner, modelName, feederName, feederNum, glmString):
	''' Function to run in the background for Milsoft import. '''
	try:
		modelDir = "data/Model/"+owner+"/"+modelName
		feederDir = modelDir+"/"+feederName+".omd"
		newFeeder = dict(**feeder.newFeederWireframe)
		newFeeder["tree"] = feeder.parse(glmString, False)
		newFeeder["layoutVars"]["xScale"] = 0
		newFeeder["layoutVars"]["yScale"] = 0
		with open("./schedules.glm","r") as schedFile:
			newFeeder["attachments"] = {"schedules.glm":schedFile.read()}
		try: os.remove(feederDir)
		except: pass
		with open(feederDir, "w") as outFile:
			json.dump(newFeeder, outFile, indent=4)
		os.remove("data/Model/"+owner+"/"+modelName+"/ZPID.txt")
		removeFeeder(owner, modelName, feederNum)
		writeToInput(modelDir, feederName, 'feederName'+str(feederNum))
	except Exception as error:
		with open("data/Model/"+owner+"/"+modelName+"/gridError.txt", "w+") as errorFile:
			errorFile.write('glmError')

@app.route("/scadaLoadshape/<owner>/<feederName>", methods=["POST"])
@flask_login.login_required
def scadaLoadshape(owner,feederName):
	loadName = 'calibration'
	feederNum = request.form.get("feederNum",1)
	modelName = request.form.get("modelName","")
	# delete calibration csv and error file if they exist
	if os.path.isfile("data/Model/" + owner + "/" +  modelName + "/error.txt"):
		os.remove("data/Model/" + owner + "/" +  modelName + "/error.txt")
	if os.path.isfile("data/Model/" + owner + "/" +  modelName + "/calibration.csv"):
		os.remove("data/Model/" + owner + "/" +  modelName + "/calibration.csv")
	file = request.files['scadaFile']
	file.save(os.path.join("data/Model/"+owner+"/"+modelName,loadName+".csv"))	
	modelDir = "data/Model/"+owner+"/"+modelName
	if not os.path.isdir(modelDir+'/calibration/gridlabD'):
		os.makedirs(modelDir+'/calibration/gridlabD')
	workDir = modelDir + '/calibration'
	feederPath = modelDir+"/"+feederName+".omd"
	scadaPath = modelDir+"/"+loadName+".csv"
	# TODO: parse the csv using .csv library, set simStartDate to earliest timeStamp, length to number of rows, units to difference between first 2 timestamps (which is a function in datetime library). We'll need a link to the docs in the import dialog and a short blurb saying how the CSV should be built.
	with open(scadaPath) as csvFile:
		scadaReader = csv.DictReader(csvFile, delimiter='\t')
		allData = [row for row in scadaReader]
	firstDateTime = dt.datetime.strptime(allData[1]["timestamp"], "%m/%d/%Y %H:%M:%S")
	secondDateTime = dt.datetime.strptime(allData[2]["timestamp"], "%m/%d/%Y %H:%M:%S")
	csvLength = len(allData)
	units =  (secondDateTime - firstDateTime).total_seconds()
	if abs(units/3600) == 1.0:
		simLengthUnits = 'hours'
	simDate = firstDateTime
	simStartDate = {"Date":simDate,"timeZone":"PST"}
	simLength = csvLength
	# Run omf calibrate in background
	importProc = Process(target=backgroundScadaCalibration, args =[owner, modelName, workDir, feederPath, scadaPath, simStartDate, simLength, simLengthUnits, "FBS", (0.05,5), 5])
	# write PID to txt file in model folder here
	importProc.start()
	pid = str(importProc.pid)
	with open(modelDir+"/CPID.txt", "w+") as outFile:
		outFile.write(pid)
	return ('',204)

def backgroundScadaCalibration(owner, modelName, workDir, feederPath, scadaPath, simStartDate, simLength, simLengthUnits, solver, calibrateError, trim):
	# heavy lifting background process/omfCalibrate and then deletes PID file
	try:
		omfCalibrate(workDir, feederPath, scadaPath, simStartDate, simLength, simLengthUnits, solver, calibrateError, trim)
		modelDirec="data/Model/" + owner + "/" +  modelName
		# move calibrated file to model folder, old omd files are backedup
		if feederPath.endswith('.omd'):
			os.rename(feederPath, feederPath+".backup")
		os.rename(workDir+'/calibratedFeeder.omd',feederPath)
		# shutil.move(workDir+"/"+feederFileName, modelDirec)
		os.remove("data/Model/" + owner + "/" +  modelName + "/CPID.txt")
	except Exception as error:
		modelDirec="data/Model/" + owner + "/" +  modelName
		errorString = ''.join(error)
		with open(modelDirec+'/error.txt',"w+") as errorFile:
		 	errorFile.write("The CSV used is incorrectly formatted. Please refer to the OMF Wiki for CSV formatting information. The Wiki can be access by clicking the Help button on the toolbar.")

@app.route("/checkScadaCalibration/<modelName>", methods=["POST","GET"])
def checkScadaCalibration(modelName):
	try:
		owner = User.cu()
	except:
		return 'Server crashed during calibration. Please attempt calibration again.'
	pidPath = ('data/Model/' + owner + '/' + modelName + '/CPID.txt')
	errorPath = ('data/Model/' + owner + '/' + modelName + '/error.txt')
	print 'Check conversion status:', os.path.exists(pidPath), 'for path', pidPath
	# return error message if one exists
	if os.path.exists(errorPath):
		with open(errorPath) as errorFile:
			errorMsg = errorFile.read()
		return errorMsg
	else:
	# checks to see if PID file exists, if theres no PID file process is done.
		return jsonify(exists=os.path.exists(pidPath))

@app.route("/cancelScadaCalibration/<modelName>", methods = ["POST","GET"])
def cancelScadaCalibration(modelName):
	owner = User.cu()
	path = "data/Model/" + owner + "/" + modelName
	if os.path.isfile("data/Model/" + owner + "/" +  modelName + "/error.txt"):
		os.remove("data/Model/" + owner + "/" +  modelName + "/error.txt")
	if os.path.isfile("data/Model/" + owner + "/" +  modelName + "/calibration.csv"):
		os.remove("data/Model/" + owner + "/" +  modelName + "/calibration.csv")
	#Read PID file, kill process with that PID number, delete calibration file, delete PID.txt
	with open(path+"/CPID.txt") as pidFile:
		pidNum = int(pidFile.read())
	os.kill(pidNum, signal.SIGTERM)
	os.remove("data/Model/" + owner + "/" +  modelName + "/CPID.txt")
	shutil.rmtree("data/Model/" + owner + "/" +  modelName + "/calibration")
	return ('cancel',204)

# TODO: Check if rename mdb files worked
@app.route("/cymeImport/<owner>", methods=["POST"])
@flask_login.login_required
def cymeImport(owner):   
	''' API for importing a cyme feeder. '''
	modelName = request.form.get("modelName","")
	feederName = str(request.form.get("feederNameC",""))
	feederNum = request.form.get("feederNum",1)
	modelFolder = "data/Model/"+owner+"/"+modelName
	mdbNetString, mdbEqString = map(lambda x: request.files[x], ["mdbNetFile", "mdbEqFile"])
	# Saves .mdb files to model folder
	mdbNetString.save(os.path.join(modelFolder,'mdbNetFile.mdb'))
	mdbEqString.save(os.path.join(modelFolder,'mdbEqString.mdb'))
	if not os.path.isdir("data/Conversion/" + owner):
		os.makedirs("data/Conversion/" + owner)
	with open("data/Conversion/" + owner + "/" + feederName + ".json", "w+") as conFile:
		conFile.write("WORKING")
	importProc = Process(target=cymeImportBackground, args=[owner, modelName, feederName, feederNum, mdbNetString.filename, mdbEqString.filename])
	importProc.start()
	return ('',204)

def cymeImportBackground(owner, modelName, feederName, feederNum, mdbNetString, mdbEqString):
	''' Function to run in the background for Milsoft import. '''
	modelDir = "data/Model/"+owner+"/"+modelName
	feederDir = modelDir+"/"+feederName+".omd"
	newFeeder = dict(**feeder.newFeederWireframe)
	[newFeeder["tree"], xScale, yScale] = cymeToGridlab.convertCymeModel(mdbNetString, mdbEqString)
	newFeeder["layoutVars"]["xScale"] = xScale
	newFeeder["layoutVars"]["yScale"] = yScale
	with open("./schedules.glm","r") as schedFile:
		newFeeder["attachments"] = {"schedules.glm":schedFile.read()}
	try: os.remove(feederDir)
	except: pass
	with open(feederDir, "w") as outFile:
		json.dump(newFeeder, outFile, indent=4)
	os.remove("data/Conversion/" + owner + "/" + feederName + ".json")
	removeFeeder(owner, modelName, feederNum)
	writeToInput(modelDir, feederName, 'feederName'+str(feederNum))

@app.route("/newSimpleFeeder/<owner>/<modelName>/<feederNum>/<writeInput>", methods=["POST", "GET"])
def newSimpleFeeder(owner, modelName, feederNum=1, writeInput=False, feederName='feeder1'):
	if User.cu() == "admin" or owner == User.cu():
		modelDir = os.path.join(_omfDir, "data", "Model", owner, modelName)
		for i in range(2,6):
			if not os.path.isfile(os.path.join(modelDir,feederName+'.omd')):
				with open("./static/SimpleFeeder.json", "r") as simpleFeederFile:
					with open(os.path.join(modelDir, feederName+".omd"), "w") as outFile:
						outFile.write(simpleFeederFile.read())
				break
			else: feederName = 'feeder'+str(i)
		if writeInput: writeToInput(modelDir, feederName, 'feederName'+str(feederNum))
		return ('Success',204)
	else: return ('Invalid Login', 204)

@app.route("/newSimpleNetwork/<owner>/<modelName>/<networkNum>/<writeInput>", methods=["POST", "GET"])
def newSimpleNetwork(owner, modelName, networkNum=1, writeInput=False, networkName='network1'):
	if User.cu() == "admin" or owner == User.cu():
		modelDir = os.path.join(_omfDir, "data", "Model", owner, modelName)
		for i in range(2,6):
			if not os.path.isfile(os.path.join(modelDir,networkName+'.omt')):
				with open("./static/SimpleNetwork.json", "r") as simpleNetworkFile:
					with open(os.path.join(modelDir, networkName+".omt"), "w") as outFile:
						outFile.write(simpleNetworkFile.read())
				break
			else: networkName = 'network'+str(i)
		if writeInput: writeToInput(modelDir, networkName, 'networkName'+str(networkNum))
		return ('Success',204)
	else: return ('Invalid Login', 204)

@app.route("/newBlankFeeder/<owner>", methods=["POST"])
@flask_login.login_required
def newBlankFeeder(owner):
	'''This function is used for creating a new blank feeder.'''
	modelName = request.form.get("modelName","")
	feederName = str(request.form.get("feederNameNew"))
	feederNum = request.form.get("feederNum",1)
	if feederName == '': feederName = 'feeder'
	modelDir = os.path.join(_omfDir, "data","Model", owner, modelName)
	try: 
		os.remove("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt")
		print "removed, ", ("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt")	
	except: pass
	removeFeeder(owner, modelName, feederNum)
	newSimpleFeeder(owner, modelName, feederNum, False, feederName)
	writeToInput(modelDir, feederName, 'feederName'+str(feederNum))
	return redirect(url_for('feederGet', owner=owner, modelName=modelName, feederNum=feederNum))

@app.route("/newBlankNetwork/<owner>", methods=["POST"])
@flask_login.login_required
def newBlankNetwork(owner):
	'''This function is used for creating a new blank network.'''
	modelName = request.form.get("modelName","")
	networkName = str(request.form.get("networkNameNew"))
	networkNum = request.form.get("networkNum",1)
	if networkName == '': networkName = 'network1'
	modelDir = os.path.join(_omfDir, "data","Model", owner, modelName)
	try: 
		os.remove("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt")
		print "removed, ", ("data/Model/"+owner+"/"+modelName+'/' + "ZPID.txt")	
	except: pass
	removeNetwork(owner, modelName, networkNum)
	newSimpleNetwork(owner, modelName, networkNum, False, networkName)
	writeToInput(modelDir, networkName, 'networkName'+str(networkNum))
	return redirect(url_for('networkGet', owner=owner, modelName=modelName, networkNum=networkNum))

@app.route("/feederData/<owner>/<modelName>/<feederName>/")
@app.route("/feederData/<owner>/<modelName>/<feederName>/<modelFeeder>")
@flask_login.login_required
def feederData(owner, modelName, feederName, modelFeeder=False):
	#MAYBEFIX: fix modelFeeder capability.
	if User.cu()=="admin" or owner==User.cu() or owner=="public":
		with open("data/Model/" + owner + "/" + modelName + "/" + feederName + ".omd", "r") as feedFile:
			return feedFile.read()

@app.route("/networkData/<owner>/<modelName>/<networkName>/")
@flask_login.login_required
def networkData(owner, modelName, networkName):
	if User.cu()=="admin" or owner==User.cu() or owner=="public":
		with open("data/Model/" + owner + "/" + modelName + "/" + networkName + ".omt", "r") as netFile:
			thisNet = json.load(netFile)
		return json.dumps(thisNet, indent=4)
		# return jsonify(netFile.read())

@app.route("/saveFeeder/<owner>/<modelName>/<feederName>", methods=["POST"])
@flask_login.login_required
def saveFeeder(owner, modelName, feederName):
	''' Save feeder data. '''
	print "Saving feeder for:%s, with model: %s, and feeder: %s"%(owner, modelName, feederName)
	if owner == User.cu() or "admin" == User.cu() or owner=="public":
		with open("data/Model/" + owner + "/" + modelName + "/" + feederName + ".omd", "w") as outFile:
			payload = json.loads(request.form.to_dict().get("feederObjectJson","{}"))
			json.dump(payload, outFile, indent=4)
	return ('Success',204)

@app.route("/saveNetwork/<owner>/<modelName>/<networkName>", methods=["POST"])
@flask_login.login_required
def saveNetwork(owner, modelName, networkName):
	''' Save network data. '''
	print "Saving network for:%s, with model: %s, and network: %s"%(owner, modelName, networkName)
	if owner == User.cu() or "admin" == User.cu() or owner=="public":
		with open("data/Model/" + owner + "/" + modelName + "/" + networkName + ".omt", "w") as outFile:
			payload = json.loads(request.form.to_dict().get("networkObjectJson","{}"))
			json.dump(payload, outFile, indent=4)
	return ('Success',204)

@app.route("/renameFeeder/<owner>/<modelName>/<oldName>/<feederName>/<feederNum>", methods=["POST"])
@flask_login.login_required
def renameFeeder(owner, modelName, oldName, feederName, feederNum):
	''' rename a feeder. '''
	modelDir = os.path.join(_omfDir, "data","Model", owner, modelName)
	feederDir = os.path.join(modelDir, feederName+'.omd')
	oldfeederDir = os.path.join(modelDir, oldName+'.omd')
	if not os.path.isfile(feederDir) and os.path.isfile(oldfeederDir):
		with open(oldfeederDir, "r") as feederIn:
			with open(feederDir, "w") as outFile:
				outFile.write(feederIn.read())
	elif os.path.isfile(feederDir): return ('Failure', 204)
	elif not os.path.isfile(oldfeederDir): return ('Failure', 204)
	os.remove(oldfeederDir)
	writeToInput(modelDir, feederName, 'feederName'+str(feederNum))
	return ('Success',204)

@app.route("/renameNetwork/<owner>/<modelName>/<oldName>/<networkName>/<networkNum>", methods=["POST"])
@flask_login.login_required
def renameNetwork(owner, modelName, oldName, networkName, networkNum):
	''' rename a feeder. '''
	modelDir = os.path.join(_omfDir, "data","Model", owner, modelName)
	networkDir = os.path.join(modelDir, networkName+'.omt')
	oldnetworkDir = os.path.join(modelDir, oldName+'.omt')
	if not os.path.isfile(networkDir) and os.path.isfile(oldnetworkDir):
		with open(oldnetworkDir, "r") as networkIn:
			with open(networkDir, "w") as outFile:
				outFile.write(networkIn.read())
	elif os.path.isfile(networkDir): return ('Failure', 204)
	elif not os.path.isfile(oldnetworkDir): return ('Failure', 204)
	os.remove(oldnetworkDir)
	writeToInput(modelDir, networkName, 'networkName'+str(networkNum))
	return ('Success',204)

@app.route("/removeFeeder/<owner>/<modelName>/<feederNum>", methods=["GET","POST"])
@app.route("/removeFeeder/<owner>/<modelName>/<feederNum>/<feederName>", methods=["GET","POST"])
@flask_login.login_required
def removeFeeder(owner, modelName, feederNum, feederName=None):
	'''Remove a feeder from input data.'''
	if User.cu() == "admin" or owner == User.cu():
		try:
			modelDir = os.path.join(_omfDir, "data","Model", owner, modelName)
			with open(modelDir + "/allInputData.json") as inJson:
				allInput = json.load(inJson)
			try:
				feederName = str(allInput.get('feederName'+str(feederNum)))
				os.remove(os.path.join(modelDir, feederName +'.omd'))
			except: print "Couldn't remove feeder file in web.removeFeeder()."
			allInput.pop("feederName"+str(feederNum))
			with open(modelDir+"/allInputData.json","w") as inputFile:
				json.dump(allInput, inputFile, indent = 4)
			return ('Success',204)
		except:
			return ('Failed',204)
	else: 
		return ('Invalid Login', 204)

@app.route("/loadFeeder/<frfeederName>/<frmodelName>/<modelName>/<feederNum>/<frUser>/<owner>", methods=["GET","POST"])
@flask_login.login_required
def loadFeeder(frfeederName, frmodelName, modelName, feederNum, frUser, owner):
	'''Load a feeder from one model to another.'''
	if frUser != "public": frUser = User.cu()
	print "Entered loadFeeder with info: frfeederName %s, frmodelName: %s, modelName: %s, feederNum: %s"%(frfeederName, frmodelName, str(modelName), str(feederNum))
	frmodelDir = "./data/Model/" + frUser + "/" + frmodelName
	modelDir = "./data/Model/" + owner + "/" + modelName
	with open(modelDir + "/allInputData.json") as inJson:
		feederName = json.load(inJson).get('feederName'+str(feederNum))
	with open(os.path.join(frmodelDir, frfeederName+'.omd'), "r") as inFeeder:
		with open(os.path.join(modelDir, feederName+".omd"), "w") as outFile:
			outFile.write(inFeeder.read())
	return redirect(url_for('feederGet', owner=owner, modelName=modelName, feederNum=feederNum))

@app.route("/cleanUpFeeders/<owner>/<modelName>", methods=["GET", "POST"])
@flask_login.login_required
def cleanUpFeeders(owner, modelName):
	'''Go through allInputData and fix feeder Name keys'''
	modelDir = "./data/Model/" + owner + "/" + modelName
	with open(modelDir + "/allInputData.json") as inJson:
		allInput = json.load(inJson)
	feeders = {}
	feederKeys = ['feederName1', 'feederName2', 'feederName3', 'feederName4', 'feederName5']
	import pprint as pprint
	pprint.pprint(allInput)
	for key in feederKeys:
		feederName = allInput.get(key,'')
		if feederName != '':
			feeders[key] = feederName
		allInput.pop(key,None)
	for i,key in enumerate(sorted(feeders)):
		allInput['feederName'+str(i+1)] = feeders[key]
	pprint.pprint(allInput)
	with open(modelDir+"/allInputData.json","w") as inputFile:
		json.dump(allInput, inputFile, indent = 4)
	return redirect("/model/" + owner + "/" + modelName)

@app.route("/removeNetwork/<owner>/<modelName>/<networkNum>", methods=["GET","POST"])
@app.route("/removeNetwork/<owner>/<modelName>/<networkNum>/<networkName>", methods=["GET","POST"])
@flask_login.login_required
def removeNetwork(owner, modelName, networkNum, networkName=None):
	'''Remove a network from input data.'''
	if User.cu() == "admin" or owner == User.cu():
		try:
			modelDir = os.path.join(_omfDir, "data","Model", owner, modelName)
			with open(modelDir + "/allInputData.json") as inJson:
				allInput = json.load(inJson)
			try:
				networkName = str(allInput.get('networkName'+str(networkNum)))
				os.remove(os.path.join(modelDir, networkName +'.omt'))
			except: print "Couldn't remove network file in web.removeNetwork()."
			allInput.pop("networkName"+str(networkNum))
			with open(modelDir+"/allInputData.json","w") as inputFile:
				json.dump(allInput, inputFile, indent = 4)
			return ('Success',204)
		except:
			return ('Failed',204)
	else: 
		return ('Invalid Login', 204)

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
	allModels = publicModels + userModels
	# Allow admin to see all models.
	isAdmin = User.cu() == "admin"
	if isAdmin:
		allModels = [{"owner":owner,"name":mod} for owner in safeListdir("data/Model/")
			for mod in safeListdir("data/Model/" + owner)]
	# Grab metadata for models.
	for mod in allModels:
		try:
			modPath = "data/Model/" + mod["owner"] + "/" + mod["name"]
			allInput = json.load(open(modPath + "/allInputData.json"))
			mod["runTime"] = allInput.get("runTime","")
			mod["modelType"] = allInput.get("modelType","")
			try:
				mod["status"] = getattr(models, mod["modelType"]).getStatus(modPath)
				creation = allInput.get("created","")
				mod["created"] = creation[0:creation.rfind('.')]
				# mod["editDate"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(os.stat(modPath).st_ctime))
			except: # the model type was deprecated, so the getattr will fail.
				mod["status"] = "stopped"
				mod["editDate"] = "N/A"
		except:
			continue
	modelTips = {}
 	for name in models.__all__:
 		try:
 			modelTips[name] = getattr(omf.models,name).tooltip
 		except:
 			pass
  	return render_template("home.html", models=allModels, current_user=User.cu(), is_admin=isAdmin, modelNames=models.__all__, modelTips=modelTips)

@app.route("/delete/<objectType>/<owner>/<objectName>", methods=["POST"])
@flask_login.login_required
def delete(objectType, objectName, owner):
	''' Delete models or feeders. '''
	if owner != User.cu() and User.cu() != "admin":
		return False
	if objectType == "Feeder":
		os.remove("data/Model/" + owner + "/" + objectName + "/" + "feeder.omd")
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
@app.route("/uniqObjName/<objtype>/<owner>/<name>/<modelName>")
@flask_login.login_required
def uniqObjName(objtype, owner, name, modelName=False):
	''' Checks if a given object type/owner/name is unique. '''
	print "Entered uniqobjname", owner, name, modelName
	if objtype == "Model":
		path = "data/Model/" + owner + "/" + name
	elif objtype == "Feeder":
		path = "data/Model/" + owner + "/" + modelName + "/" + name + ".omd"
		if name == 'feeder': return jsonify(exists=True)
	elif objtype == "Network":
		path = "data/Model/" + owner + "/" + modelName + "/" + name + ".omt"
		if name == 'feeder': return jsonify(exists=True)
	return jsonify(exists=os.path.exists(path))

if __name__ == "__main__":
	URL = "http://localhost:5000"
	template_files = ["templates/"+ x  for x in safeListdir("templates")]
	model_files = ["models/" + x for x in safeListdir("models")]
	app.run(debug=True, extra_files=template_files + model_files)
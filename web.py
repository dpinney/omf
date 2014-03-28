''' Web server for model-oriented OMF interface. '''

from flask import Flask, send_from_directory, request, redirect, render_template, session, abort
from jinja2 import Template
import models, json, os, flask_login, hashlib, random, time
from passlib.hash import pbkdf2_sha512

app = Flask("omf")

homeTemplate = '''
<body>
	<p>New Model of Type:</p>
	{% for x in modTypes %}
		<a href='/newModel/{{ x }}'>{{ x }}</a>
	{% endfor %}
	<p>Instances:</p>
	{% for x in instances %}
		<a href='/model/{{ x }}'>{{ x }}</a>
	{% endfor %}
	<p> Other Stuff</p>
	<a href="/logout">Logout</a>
</body>
'''

def getDataNames():
	''' Query the OMF datastore to list all the names of things we might need.'''
	currUser = flask_login.current_user
	feeders = [x[len(currUser.username)+1:-5] for x in os.listdir('./data/Feeder/')
		if x.startswith(currUser.username + "_")]
	publicFeeders = [x[7:-5] for x in os.listdir('./data/Feeder/')
		if x.startswith('public_')]
	climates = [x[:-5] for x in os.listdir('./data/Weather/')]
	return 	{'feeders':feeders, 'publicFeeders':publicFeeders, 'climates':climates, 
		'currentUser':currUser.__dict__}

@app.before_request
def csrf_protect():
	pass
	if request.user_agent.browser == 'msie' or request.user_agent.browser == 'firefox':
		return 'The OMF currently must be accessed by Chrome or Safari.'
	# TODO: fix csrf stuff.
	# if request.method == "POST":
	# 	token = session.get('_csrf_token', None)
	# 	if not token or token != request.form.get('_csrf_token'):
	# 		abort(403)

###################################################
# AUTHENTICATION AND SECURITY STUFF
###################################################

class User:
	def __init__(self, jsonBlob):
		self.username = jsonBlob["username"]

	def is_admin(self):
		return self.username == "admin"

	def get_id(self):
		return self.username	

	# Required flask_login functions
	def is_authenticated(self): return True
	def is_active(self): return True
	def is_anonymous(self):	return False

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
# MISCELLANEOUS VIEWS
###################################################

@app.route("/robots.txt")
def static_from_root():
	return send_from_directory(app.static_folder, request.path[1:])

@app.route("/")
@flask_login.login_required
def mainScreen():
	return Template(homeTemplate).render(modTypes=models.__all__,
		instances=os.listdir("./data/Model/"))

@app.route("/newModel/<modelType>")
@flask_login.login_required
def newModel(modelType):
	''' Display the module template for creating a new model. '''
	return getattr(models, modelType).renderTemplate(datastoreNames=getDataNames())

@app.route("/runModel/", methods=["POST"])
@flask_login.login_required
def runModel():
	pData = request.form.to_dict()
	pData["user"] = flask_login.current_user.username
	pData["status"] = "preRun"
	getattr(models, pData["modelType"]).create('./data/Model/', pData)
	return redirect("/model/" + pData["user"] + "_" + pData["modelName"])

@app.route("/model/<modelName>")
@flask_login.login_required
def showModel(modelName):
	''' Render a model template with saved data. '''
	workDir = "./data/Model/" + modelName + "/"
	with open(workDir + "allInputData.json") as inJson:
		modelType = json.load(inJson)["modelType"]
	return getattr(models, modelType).renderTemplate(modelDirectory=workDir,
		datastoreNames=getDataNames())

if __name__ == "__main__":
	# TODO: remove debug and extra_files arguments.
	app.run(debug=True, extra_files=["./models/gridlabSingle.html"])

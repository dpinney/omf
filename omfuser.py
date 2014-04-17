
import flask_login
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

	@classmethod
	def cu(self):
		"""Returns current user's username"""
		return flask_login.current_user.username

	@classmethod
	def ia(self):
		"""ia == is admin.  Returns if the current user is the admin"""
		return self.cu() == "admin"

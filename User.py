
try:
	from passlib.hash import pbkdf2_sha512
except ImportError, e:
	print "install passlib - 'pip install passlib'"
	raise Exception, e

import os
import json
import hashlib
import random
import time

class UserManager:
	def __init__(self, store):
		self.store = store
		
	def create_user(self, username, password, confirm_password):
		# For now, just creating user in file store
		if self.store.exists("User", username):
			return
		if username and  password == confirm_password and username not in ["admin","public"]:
			u_dict = {"username":username,
					  "password_digest":pbkdf2_sha512.encrypt(password),
					  }
			self.store.put("User", username, u_dict)
			return User(self.store, **u_dict)
			
	def authenticate(self, username, password):
		user = self.store.get("User", username)
		if user and pbkdf2_sha512.verify(password,
										 user["password_digest"]):
			self.store.put("User", username, user)
			return User(self.store, **user)

	def get(self, username):
		return User(self.store, **self.store.get("User", username))
		
class User:
	def __init__(self, store, **kwargs):
		self.store = store
		map((lambda k, v: setattr(self, k, v)),
			kwargs.keys(),
			kwargs.values())
		self.prepend = self.username+"_"

	def changepwd(self, new_pwd):
		self.password_digest = pbkdf2_sha512.encrypt(new_pwd)
		self.store.put("User", self.username, {"username":self.username,
											   "password_digest":self.password_digest})

	def is_admin(self):
		return self.username == "admin"

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.username

	def listAll(self, objectType):
		return [e[len(self.prepend):] for e in self.store.listAll(objectType)
				if e[:len(self.prepend)] == self.prepend]

	def get(self, objectType, objectName, crop_name=True):
		gdict = self.store.get(objectType, self.prepend+objectName)
		if gdict and crop_name:
			gdict["name"] = gdict["name"][len(self.prepend):]
		return gdict

	def exists(self, objectType, objectName):
		return self.store.exists(objectType, self.prepend+objectName)

	def delete(self, objectType, objectName):
		return self.store.delete(objectType, self.prepend+objectName)
	
	def put(self, objectType, objectName, putDict):
		return self.store.put(objectType, self.prepend+objectName, putDict)

	def make_public(self, objectType, objectName):
		dataDict = self.store.get(objectType, self.prepend+objectName)
		if self.username == "admin":
			objectName = objectName[objectName.find("_")+1:]
		if dataDict:
			self.store.put(objectType, "public_"+objectName, dataDict)
		
		
			

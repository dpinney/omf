

try:
    from passlib.hash import pbkdf2_sha512
except ImportError, e:
    print "install passlib - 'pip install passlib'"
    raise Exception, e

import os
import json

class UserManager:
    def __init__(self, store):
        self.store = store
        
    def create_user(self, username, password, confirm_password):
        # For now, just creating user in file store
        if self.store.exists("User", username):
            return
        if username and  password == confirm_password:
            u_dict = {"username":username,
                      "password_digest":pbkdf2_sha512.encrypt(password),
                      "analyses":[],
                      "studies":[],
                      "feeders":[]
                      }
            self.store.put("User", username, u_dict)
            return User(self.store, u_dict)
            
    def authenticate(self, username, password):
        user = self.store.get("User", username)
        if user and pbkdf2_sha512.verify(password,
                                         user["password_digest"]):
            return User(store, **user)

    def get(self, username):
        return User(self.store, self.store.get("User", username))
        
class User:
    def __init__(self, store, **kwargs):
        self.store = store
        map((lambda k, v: setattr(self, k, v)),
            kwargs.keys(),
            kwargs.values())

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def list_all(self, objectType):
        return [e for e in self.store.listAll(objectType)
                if e[:len(self.username)+1] == self.username+"_"]

    def get(self, objectType, objectName):
        return self.store.get(objectType, self.username+"_"+objectName)

    def exists(self, objectType, objectName):
        return self.store.exists(objectType, self.username+"_"+objectName)

    def delete(self, objectType, objectName):
        return self.store.delete(objectType, self.username+"_"+objectName)

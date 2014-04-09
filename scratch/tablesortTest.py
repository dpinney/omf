#!/usr/bin/env python

# I'm tailoring the file system navigation to the assumption that this script is being run from the top level scratch/ directory

from random import choice, randint
import os
import json

os.chdir("../data/Model")

def randPad(l, p_amt=2):
    return str(random.choice(l)).zfill(p_amt)

def rdstr(timeRanges):
    return "{0}{1}{2} {3}:{4}".format(*map(randPad, timeRanges))

def randDate():
    timeRanges = [
        [1900, 2050],                   # years
        [1, 13],                        # months
        [1, 29],                        # days
        [24],                           # hours
        [60],                           # minutes
        ]
    return rdstr(map(lambda l: range(*l), timeRanges))

def oneModel():
    # Assume we're within user dir
    # Need to assign random date
    modelName = randStr()
    os.mkdir(modelName)
    json.dump(randModJson(modelName), open(modelName+"/allInputData.json", "w"))

def oneUser(limit=10):
    while True:
        username = randStr()
        if username not in os.listdir("."):
            break
    os.mkdir(username)
    os.chdir(username)
    numModels = randint(1, limit)
    for i in range(numModels):
        oneModel()
    return numModels, username

def allModels():
    totalModels = 10
    removeUsers = []
    while totalModels:
        numModels, username = oneUser()
        totalModels -= numModels
        removeUsers.append(username)
    return removeUsers
    
def randStr(l=20):
    # This one is just the digits, letters, and the space character:
    # acceptableChars = range(48, 58) + range(65, 91) + range(97, 123) + [32]
    # This one is all typeable ASCII characters... should we test the full unicode spectrum at some point?
    acceptableChars = range(32, 127)    # DEL isn't a character you could type at your keyboard, right?  That's why I'm not including 127
    return "".join([chr(choice(acceptableChars)) for i in range(l)])

def randModJson(name):
    return {
        "modelName": name, 
        "simStartDate": "2012-04-01", 
        "simLengthUnits": "hours", 
        "feederName": "Simple Market System", 
        "created": "2014-03-31 16:19:30.848000", 
        "modelType": "gridlabSingle", 
        "climateName": "AL-HUNSTVILLE.tmy2", 
        "simLength": "100", 
        "user": "admin", 
        "runTime": ""
        }


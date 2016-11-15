''' The transmission model. '''

'''
TODO:
    1. Add cancel functionality.

'''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime, traceback, math
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *

# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import nrelsam2013
from weather import zipCodeToClimateName

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"transmission.html"),"r") as tempFile:
    template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
    return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def run(modelDir, inputDict):
    ''' Run the model in its directory. '''
    # Delete output file every run if it exists
    try:
        os.remove(pJoin(modelDir,"allOutputData.json")) 
    except Exception, e:
        pass
    # Check whether model exist or not
    try:
        if not os.path.isdir(modelDir):
            os.makedirs(modelDir)
            inputDict["created"] = str(datetime.datetime.now())
        # MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
        with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
            json.dump(inputDict, inputFile, indent = 4)         
        startTime = datetime.datetime.now()
        outData = {}        
        # Model operations goes here.
        powerReal = inputDict.get("input1", 123)
        powerReact = inputDict.get("input2", 867)
        volts = []
        outData["tableData"]["powerReal"] = [["node123", "node124"], [500, 100]]
        outData["tableData"]["powerReact"] = [["node123", "node124"], [100, 50]]
        outData["tableData"]["volts"] =  [["node123", "node124"], [120, 100]]
        # Model operations typically ends here.
        # Stdout/stderr.
        outData["stdout"] = "Success"
        outData["stderr"] = ""
        # Write the output.
        with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
            json.dump(outData, outFile, indent=4)
        # Update the runTime in the input file.
        endTime = datetime.datetime.now()
        inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
        with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
            json.dump(inputDict, inFile, indent=4)
    except:
        # If input range wasn't valid delete output, write error to disk.
        cancel(modelDir)                
        thisErr = traceback.format_exc()
        print 'ERROR IN MODEL', modelDir, thisErr
        inputDict['stderr'] = thisErr
        with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
            errorFile.write(thisErr)
        with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
            json.dump(inputDict, inFile, indent=4)

def cancel(modelDir):
    ''' PV Watts runs so fast it's pointless to cancel a run. '''
    pass


def _tests():
    # Variables
    workDir = pJoin(__metaModel__._omfDir,"data","Model")
    inData = {"user" : "admin", "modelName" : "Automated Transmission Model Testing",
        "networkName" : "9-Bus System",
        "algorithm" : "NR",
        "model" : "AC",
        "tolerance" : math.pow(10,-8),
        "iteration" : 10,
        "genLimits" : 0}
    modelDir = pJoin(workDir, inData["user"], inData["modelName"])
    # Blow away old test results if necessary.
    try:
        shutil.rmtree(modelDir)
    except:
        # No previous test results.
        pass
     # Run the model & show the output.
    run(modelDir, inData)
    renderAndShow(template, modelDir = modelDir)

if __name__ == '__main__':
    _tests()            
''' Display circuit simulator in real time. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime
from os.path import join as pJoin
from jinja2 import Template
#_circuitRealTime.py
# from omf.models import __metaModel__
# circuitRealtime.py
import __metaModel__
from __metaModel__ import *
# OMF imports
sys.path.append(__metaModel__._omfDir)

# Our HTML template for the interface:
'''in scratch'''
# with open(pJoin(os.getcwd(), "_circuitRealTime.html"),"r") as tempFile:
	# template = Template(tempFile.read())
'''if in models dir'''
with open(pJoin(__metaModel__._myDir,"_circuitRealTime.html"),"r") as tempFile:
	template = Template(tempFile.read())
#TODO: I think this is where its breaking. Reading hte html file and template.render seeing the include throws it off.
# Maybe find a way to pass it to .html some other way. 
# In meta model, add an inputtype, if inputtype = circuitmodel then do a unique templaterender that doesn't fail. it can have the html added and then inserted 
# using a variable and a safe argument. 
# first is the path of the file the problem? determine this first.
# if it isnt, pass the iframe or javascript render the above way. 

# with open(pJoin(__metaModel__._myDir,"circuitRealTime.html"),"r") as tempFile:
# 	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	# print "\n   template=", str(template)
	# print "\n   dataStoreNames=", datastoreNames
	# print "\n   modelDir=", modelDir
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)


def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	print os.getcwd()
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
		startTime = datetime.datetime.now()

		# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
		# Update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
		print "\n   inputDict[runTime]", inputDict["runTime"]
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
		# Stdout/stderr.
		outData = {}		
		outData["stdout"] = "Success"
		outData["stderr"] = ""
		# Write the output.
		with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
			json.dump(outData, outFile, indent=4)
	except:
		#if input range wasn't valid delete output and pass
		try:
			os.remove(pJoin(modelDir,"allOutputData.json"))
		except Exception, e:
			pass

def cancel(modelDir):
	''' PV Watts runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	inData = {"modelType": "circuitRealTime","circuitFile" : "zenerreffollow.txt"}
	modelLoc = pJoin(workDir,"admin","Automated realTimeCircuit Testing")
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow(template)
	# Run the model.
	run(modelLoc, inData)
	# Show the output.
	renderAndShow(template, modelDir = modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()
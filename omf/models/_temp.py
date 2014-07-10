""" Common functions for all models """

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, datetime
from os.path import join as pJoin
from jinja2 import Template
import __util__ as util
# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(_myDir)

# OMF imports
sys.path.append(_omfDir)

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	''' Render the model template to an HTML string.
	By default render a blank one for new input.
	If modelDir is valid, render results post-model-run.
	If absolutePaths, the HTML can be opened without a server. '''
	try:
		allInputData = open(pJoin(modelDir,"allInputData.json")).read()
	except IOError:
		allInputData = None
	try:
		allOutputData = open(pJoin(modelDir,"allOutputData.json")).read()
	except IOError:
		allOutputData = None
	if absolutePaths:
		# Parent of current folder.
		pathPrefix = _omfDir
	else:
		pathPrefix = ""
	return template.render(allInputData=allInputData,
		allOutputData=allOutputData, modelStatus=getStatus(modelDir), pathPrefix=pathPrefix,
		datastoreNames=datastoreNames)


def renderAndShow(modelDir="", datastoreNames={}):
	''' Render and open a template (blank or with output) in a local browser. '''
	with tempfile.NamedTemporaryFile() as temp:
		temp.write(renderTemplate(modelDir=modelDir, absolutePaths=True))
		temp.flush()
		os.rename(temp.name, temp.name + ".html")
		fullArg = "file://" + temp.name + ".html"
		webbrowser.open(fullArg)
		# It's going to SPACE! Could you give it a SECOND to get back from SPACE?!
		time.sleep(1)

def getStatus(modelDir):
	''' Is the model stopped, running or finished? '''
	try:
		modFiles = os.listdir(modelDir)
	except:
		modFiles = []
	hasInput = "allInputData.json" in modFiles
	hasPID = "PPID.txt" in modFiles
	hasOutput = "allOutputData.json" in modFiles
	if hasInput and not hasOutput and not hasPID:
		return "stopped"
	elif hasInput and not hasOutput and hasPID:
		return "running"
	elif hasInput and hasOutput and not hasPID:
		return "finished"
	else:
		# Broken! Make the safest choice:
		return "stopped"


def cancel(modelDir):
	''' Try to cancel a currently running model. '''
	# Kill GLD process if already been created
	try:
		with open(pJoin(modelDir,"PID.txt"),"r") as pidFile:
			pid = int(pidFile.read())
			# print "pid " + str(pid)
			os.kill(pid, 15)
			print "PID KILLED"
	except:
		pass
	# Kill runForeground process
	try:
		with open(pJoin(modelDir, "PPID.txt"), "r") as pPidFile:
			pPid = int(pPidFile.read())
			os.kill(pPid, 15)
			print "PPID KILLED"
	except:
		pass
	# Remove PID, PPID, and allOutputData file if existed
	try:
		for fName in os.listdir(modelDir):
			if fName in ["PID.txt","PPID.txt","allOutputData.json"]:
				os.remove(pJoin(modelDir,fName))
		print "CANCELED", modelDir
	except:
		pass

def _test():
	""" No test required for this file. """
	pass
""" Common functions for all models """

import json, os, sys, tempfile, webbrowser, math, shutil, datetime, omf, multiprocessing, traceback, hashlib, traceback, re, io
from jinja2 import Template
from os.path import join as pJoin
from os.path import split as pSplit
from omf.web import locked_open

# Locational variables so we don't have to rely on OMF being in the system path.
_myDir = os.path.dirname(os.path.abspath(__file__))
_omfDir = os.path.dirname(_myDir)

def metadata(fileUnderObject):
	''' Get the model name and template for a given model from its filename and associated .html file.
	The argument fileUnderObject should always be __file__.'''
	fileName = os.path.basename(fileUnderObject)
	modelName = fileName[0:fileName.rfind('.')]
	with open(pJoin(_myDir, modelName+".html")) as f:
		template = Template(f.read()) #HTML Template for showing output.
	return modelName, template

def heavyProcessing(modelDir):
	''' Wrapper to handle model running safely and uniformly. '''
	try:
		# Start a timer.
		startTime = datetime.datetime.now()
		# Get the inputs.
		with locked_open(pJoin(modelDir, 'allInputData.json')) as f:
			inputDict = json.load(f)
		# Remove old outputs.
		try: os.remove(pJoin(modelDir,"allOutputData.json"))
		except Exception, e: pass
		# Get the function and run it.
		work = getattr(omf.models, inputDict['modelType']).work
		#This grabs the new outData model
		outData = work(modelDir, inputDict)
	except:
		# If input range wasn't valid delete output, write error to disk.
		cancel(modelDir)
		thisErr = traceback.format_exc()
		print 'ERROR IN MODEL', modelDir, thisErr
		inputDict['stderr'] = thisErr
		with locked_open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
	else:
		# No errors, so update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
		# Write output.
		modelType = inputDict["modelType"]
		#Get current file hashes and dd to the output
		with open(pJoin(_myDir, modelType+".html")) as f:
			htmlFile = f.read()
		currentHtmlHash = hashlib.sha256(htmlFile).hexdigest()
		with open(pJoin(_myDir, modelType+".py")) as f:
			pythonFile = f.read()
		currentPythonHash = hashlib.sha256(pythonFile).hexdigest()
		outData['htmlHash'] = currentHtmlHash
		outData['pythonHash'] = currentPythonHash
		outData['oldVersion'] = False
		# Raw input/output file names.
		outData['fileNames'] = os.listdir(modelDir)
		outData['fileNames'].append('allOutputData.json')
		with locked_open(pJoin(modelDir, "allOutputData.json"),"w") as outFile:
			json.dump(outData, outFile, indent=4)
	finally:
		# Clean up by updating input data.
		try:
			with locked_open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
				json.dump(inputDict, inFile, indent=4)
		except: pass
		try: os.remove(pJoin(modelDir,"PPID.txt"))
		except: pass

def run(modelDir):
	''' Run the model in a separate process. web.py calls this to run the model.
	This function will return fast, but results take a while to hit the file system.'''
	backProc = multiprocessing.Process(target = heavyProcessing, args = (modelDir,))
	backProc.start()
	with locked_open(pJoin(modelDir, "PPID.txt"),"w+") as pPidFile:
		pPidFile.write(str(backProc.pid))
	print "SENT TO BACKGROUND", modelDir

def runForeground(modelDir):
	''' Run all model work immediately in the same thread. '''
	with locked_open(pJoin(modelDir, "PPID.txt"),"w+") as pPidFile:
		pPidFile.write('-999') # HACK: put in an invalid PID to indicate the model is running.
	print "FOREGROUND RUNNING", modelDir
	heavyProcessing(modelDir)

def renderTemplate(modelDir, absolutePaths=False, datastoreNames={}):
	''' Render the model template to an HTML string.
	By default render a blank one for new input.
	If modelDir is valid, render results post-model-run.
	If absolutePaths, the HTML can be opened without a server. '''
	try:
		with locked_open(pJoin(modelDir, 'allInputData.json')) as f:
			inJson = json.load(f)
		modelPath, modelName = pSplit(modelDir)
		deepPath, user = pSplit(modelPath)
		inJson["modelName"] = modelName
		inJson["user"] = user
		modelType = inJson["modelType"]
		template = getattr(omf.models, modelType).template
		allInputData = json.dumps(inJson)
		# Get hashes for model python and html files 
		with open(pJoin(_myDir, modelType+".html")) as f:
			htmlFile = f.read()
		currentHtmlHash = hashlib.sha256(htmlFile).hexdigest()
		with open(pJoin(_myDir, modelType+".py")) as f:
			pythonFile = f.read()
		currentPythonHash = hashlib.sha256(pythonFile).hexdigest()
	except IOError:
		allInputData = None
		inJson = None
	try:
		with locked_open(pJoin(modelDir,"allOutputData.json")) as f:
			allOutputData = f.read()
		with locked_open(pJoin(modelDir, "allOutputData.json")) as f:
			outJson = json.load(f)
		try:
			#Needed? Should this be handled a different way? Add hashes to the output if they are not yet present
			if ('pythonHash' not in outJson) or ('htmlHash' not in outJson):
				print('new model')
				outJson['htmlHash'] = currentHtmlHash
				outJson['pythonHash'] = currentPythonHash
				outJson['oldVersion'] = False
			#If the hashes do not match, mark the model as an old version
			elif outJson['htmlHash'] != currentHtmlHash or outJson['pythonHash'] != currentPythonHash:
				outJson['oldVersion'] = True
			#If the hashes match, mark the model as up to date
			else:	
				outJson['oldVersion'] = False
		except (UnboundLocalError, KeyError), e:
			print(traceback.print_exc())
			print('error:' + str(e))
	except IOError:
		allOutputData = None
		outJson = None
	if absolutePaths:
		# Parent of current folder.
		pathPrefix = _omfDir
	else:
		pathPrefix = ""
	# Raw input output include.
	return template.render(allInputData=allInputData, allOutputData=allOutputData, modelStatus=getStatus(modelDir), pathPrefix=pathPrefix,
		datastoreNames=datastoreNames, modelName=modelType, allInputDataDict=inJson, allOutputDataDict=outJson)

def renderAndShow(modelDir, datastoreNames={}):
	''' Render and open a template (blank or with output) in a local browser. '''
	with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp:
		temp.write(renderTemplate(modelDir, absolutePaths=True))
		temp.flush()
		webbrowser.open("file://" + temp.name)

def renderTemplateToFile(modelDir, datastoreNames={}):
	''' Render and open a template (blank or with output) in a local browser. '''
	with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as baseTemplate:
		baseTemplate.write(renderTemplate(modelDir, absolutePaths=False))
		baseTemplate.flush()
		baseTemplate.seek(0)
		with locked_open(pJoin(modelDir,'inlineTemplate.html'), 'w', encoding='utf-8', io_open=True) as inlineTemplate:
			for line in baseTemplate:
				#add backslash to regex between signle and double quote
				matchObj = re.match( r"(.*)/static(.+?)(['\"])(.+?)", line, re.M|re.I)
				scriptTags = re.match( r"(.*)<script(.*)static/(.*)</script>", line, re.M|re.I)
				styleTags = re.match( r"(.*)<link(.*)stylesheet", line, re.M|re.I)
				if scriptTags:
					with open(_omfDir + "/static"+ matchObj.group(2)) as f:
						sourceFile = f.read() 
					with io.open(_omfDir + "/static"+ matchObj.group(2), 'r', encoding='utf-8') as yFile:
						ttempfile = yFile.readlines()
					tmp = '<script>'+sourceFile+'</script>'
					inlineTemplate.write(unicode('<script>'))
					for i in ttempfile:
						try:
							inlineTemplate.write(i)
						except (UnicodeEncodeError):
							print(i)
					inlineTemplate.write(unicode('</script>'))
				elif styleTags:
					with io.open(_omfDir + "/static"+ matchObj.group(2), 'r', encoding='utf-8') as yFile:
						ttempfile = yFile.readlines()
					inlineTemplate.write(unicode('<style>'))
					for i in ttempfile:
						try:
							inlineTemplate.write(i)
						except (UnicodeEncodeError):
							print(i)
					inlineTemplate.write(unicode('</style>'))
				else:
					inlineTemplate.write(unicode(line))

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

def new(modelDir, defaultInputs):
	''' Create a new instance of a model. Returns true on success, false on failure. '''
	alreadyThere = os.path.isdir(modelDir) or os.path.isfile(modelDir)
	try:
		if not alreadyThere:
			os.makedirs(modelDir)
		else:
			return False
		defaultInputs["created"] = str(datetime.datetime.now())
		with locked_open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
			json.dump(defaultInputs, inputFile, indent = 4)
		return True
	except:
		return False

def cancel(modelDir):
	''' Try to cancel a currently running model. '''
	# Kill GLD process if already been created
	try:
		with locked_open(pJoin(modelDir,"PID.txt"),"r") as pidFile:
			pid = int(pidFile.read())
		# print "pid " + str(pid)
		os.kill(pid, 15)
		print "PID KILLED"
	except:
		pass
	# Kill runForeground process
	try:
		with locked_open(pJoin(modelDir, "PPID.txt"), "r") as pPidFile:
			pPid = int(pPidFile.read())
		os.kill(pPid, 15)
		print "PPID KILLED"
	except:
		pass
	# Remove PID, PPID, and allOutputData file if existed
	for fName in ["PID.txt","PPID.txt","allOutputData.json"]:
		try: 
			os.remove(pJoin(modelDir,fName))
		except:
			pass
	print "CANCELED", modelDir

def roundSig(x, sig=3):
	''' Round to a given number of sig figs. '''
	roundPosSig = lambda y,sig: round(y, sig-int(math.floor(math.log10(y)))-1)
	if x == 0: return 0
	elif x!=x: return 0 # This is handling float's NaN.
	elif x < 0: return -1*roundPosSig(-1*x, sig)
	else: return roundPosSig(x, sig)

def _test():
	""" No test required for this file. """
	pass
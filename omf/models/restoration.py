import os, shutil
from os.path import join as pJoin

# OMF imports
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "This is a stub for the creation of new models. Update this description to match your model's purpose."
hidden = True # Change to False to make visible in the omf's "new model" list
hidden = False

def castAddInputs(val1,val2):
	''' Casts string inputs to appropriate type and returns their sum. 
		If inputs are cast to floats, rounds their sum to avoid float subtraction errors.'''
	try:
		cast1 = int(val1)
		cast2 = int(val2)
		return cast1+cast2
	except ValueError:
		try:
			cast1 = float(val1)
			cast2 = float(val2)
            #Find longest decimal place of the numbers and round their sum to that place to avoid float arithmetic errors
			decPl1 = val1.strip()[::-1].find('.')
			decPl2 = val2.strip()[::-1].find('.')  
            #valX.strip() used instead of str(castX) because str(castX) may return scientific notation
			roundedSum = round(cast1+cast2,max(decPl1,decPl2,1))     
			return roundedSum
		except ValueError:
			return val1+val2

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	outData = {}		

	# Model operations goes here.
	inputOne = inputDict.get("number1", 123)
	inputTwo = inputDict.get("number2", 867)
	outData["output"] = castAddInputs(inputOne, inputTwo)
	# Model operations typically end here.

	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData


def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	omd_fn = "iowa240c1.clean.dss"
	ex_fn = "example.csv" # example file input

	with open(pJoin(omf.omfDir, "static", "testFiles", "restoration", ex_fn)) as ex_stream:
		ex_ins = ex_stream.read()

	defaultInputs = {
		"modelType": modelName,
		"date": "2019-07-01T00:00:00Z",
		"number1": "123",
		"number2": "987",
		"feederName1": omd_fn,
		"exampleFileName": ex_fn,
		"exampleFileContent": ex_ins,
	}

	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, 'static', 'publicFeeders', defaultInputs['feederName1']+'.omd'), pJoin(modelDir, defaultInputs['feederName1']+'.omd'))
	except:
		return False
	return creationCode

@neoMetaModel_test_setup
def _debugging():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

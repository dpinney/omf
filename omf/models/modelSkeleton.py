''' A model skeleton for future models: Calculates the sum of two integers. '''

import warnings
# warnings.filterwarnings("ignore")

import shutil, datetime
from os.path import join as pJoin

# OMF imports
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
import omf.feeder as feeder
from omf.models.voltageDrop import drawPlot

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	outData = {}		
	# Model operations goes here.
	inputOne = inputDict.get("input1", 123)
	inputTwo = inputDict.get("input2", 867)
	output = inputOne + inputTwo
	outData["output"] = output
	# Model operations typically ends here.
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"user" : "admin",
		"modelType": modelName,
		"input1": "abc1 Easy as...",
		"input2": "123 Or Simple as...",
		"created":str(datetime.datetime.now())
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def _tests():
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
	#_tests()
	pass
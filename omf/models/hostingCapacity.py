''' Calculate solar photovoltaic system output using PVWatts. '''

import shutil, datetime
from os.path import join as pJoin
import mohca_cl;

# OMF imports
from omf import weather
from omf.solvers import nrelsam2013
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Model metadata:
tooltip = "The hostingCapacity model calculates the kW hosting capacity available at each meter in the provided AMI data."
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

def work(modelDir, inputDict):

	rowCount = 0
	# Writing the content from the input into a file for the mohca algorithm to read in.
	with open(pJoin(modelDir,"meter_data_input.csv"),"w", newline='') as pv_stream:
		pv_stream.write(inputDict['inputDataFileContent'])
	'''
	# Checking the number of rows in the file
	try:
		with open(pJoin(modelDir,"meter_data_input.csv"), newline='') as pv_stream2:
			reader = csv.reader(pv_stream2)
			for row in reader:
				rowCount = rowCount+1
	except:
		#TODO change to an appropriate warning message
		errorMessage = "CSV file is incorrect format."
		raise Exception(errorMessage)
	'''
	
	#ncols is variable
	# csvInput = csvValidateAndLoad( file_input = modelDir + "/meter_data_input.csv", modelDir=modelDir, header=0, return_type='list_by_col', ignore_nans=False)

	'''
	if ( inputDict[ "mohcaAlgorithm" ] == "sandia1" ):
		mohcaOutput = mohca_cl.sandia1( modelDir + "/meter_data_input.csv", modelDir + "/mohcaOutput.csv" )

	elif (inputDict[ "mohcaAlgorithm" ] == "sandia2"):
		mohcaOutput = mohca_cl.sandia2( modelDir + "/meter_data_input.csv", modelDir + "/mohcaOutput.csv" )
	'''


	mohcaOutput = {}
	mohcaOutput = mohca_cl.sandia1( modelDir + "/meter_data_input.csv", modelDir + "/mohcaOutput.csv" )
    # Should I worry about validating the output that the algorithm returns?
	# mohcaAlgo = csvValidateAndLoad(mohcaOutput.csv, modelDir, header=None, ignore_nans=False, return_type='list_by_col', save_file=None)
	
	# Timestamp output.
	
	outData = {}
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def runtimeEstimate(modelDir):
	''' Estimated runtime of model in minutes. '''
	return 0.5

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		"dataVariableName": "None",
		"inputDataFile": "None",
		"modelType": modelName,
		"mohcaAlgorithm": "None"
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
	_tests()

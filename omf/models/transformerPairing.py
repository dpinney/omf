import warnings
# warnings.filterwarnings("ignore")

# Import Python libraries
import shutil
import numpy as np
from pathlib import Path
import pandas as pd
import base64

# OMF imports
import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Import custom libraries
from omf.solvers import sdsmc 

# Model metadata:
tooltip = "Transformer Pairing"
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False


def work(modelDir, inputDict):

	outData = {}
	useTrueLabels = True
	outData["useTrueLabels"] = useTrueLabels

	with open(Path(modelDir,inputDict['voltageInputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['voltageInputDataFileContent'])
	voltageInputPathCSV = Path(modelDir, inputDict['voltageInputDataFileName'])

	with open(Path(modelDir,inputDict['realPowerInputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['realPowerInputDataFileContent'])
	realPowerInputPathCSV = Path(modelDir, inputDict['realPowerInputDataFileName'])

	with open(Path(modelDir,inputDict['reactivePowerInputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['reactivePowerInputDataFileContent'])
	reactivePowerInputPathCSV = Path(modelDir, inputDict['reactivePowerInputDataFileName'])

	with open(Path(modelDir,inputDict['customerIDInputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['customerIDInputDataFileContent'])
	custIDInputPathCSV = Path(modelDir, inputDict['customerIDInputDataFileName'])

	test_data_file_path = Path(omf.omfDir,'static','testFiles', 'transformerPairing')

	transformer_labels_errors_file_name = 'TransformerLabelsErrors_AMI.csv'
	transformerLabelsErrorsPathCSV = Path( test_data_file_path, transformer_labels_errors_file_name )

	if useTrueLabels:
		transformer_labels_true_file_name = 'TransformerLabelsTrue_AMI.csv'
		transformerLabelsTruePath = Path( test_data_file_path, transformer_labels_true_file_name )

	saveResultsPath = modelDir

	sdsmc.MeterTransformerPairing.TransformerPairing.run( voltageInputPathCSV, realPowerInputPathCSV, reactivePowerInputPathCSV, custIDInputPathCSV, transformerLabelsErrorsPathCSV, transformerLabelsTruePath, saveResultsPath, useTrueLabels )
	
	changedCustomersDF = pd.read_csv( Path(modelDir, "outputs_ChangedCustomers_M2T.csv") )
	outData['customerTableHeadings'] = changedCustomersDF.columns.values.tolist()
	outData['customerTableValues'] = ( list(changedCustomersDF.sort_values( by="customer ID", ascending=True, ignore_index=True ).itertuples(index=False, name=None)))

	improvementStats = pd.read_csv( Path(modelDir, "outputs_ImprovementStats.csv") )
	outData['improvementTableHeadings'] = improvementStats.columns.values.tolist()
	outData['improvementTableValues'] = (list(improvementStats.itertuples(index=False, name=None)))

	with open( Path(modelDir,"CCThresholdSweep_NumFlaggedTrans_LINE.png"),"rb") as inFile:
		outData["correlationCoefficientPic"] = base64.standard_b64encode(inFile.read()).decode('ascii')
	
	# Delete output file every run if it exists
	outData['stdout'] = "Success"
	outData['stderr'] = ""
	return outData

def runtimeEstimate(modelDir):
	''' Estimated runtime of model in minutes. '''
	return 1.0

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	test_data_file_path = Path(omf.omfDir,'static','testFiles', 'transformerPairing')

	voltage_file_name = 'voltageData_AMI.csv'
	voltage_file_path = Path( test_data_file_path, voltage_file_name )
	voltage_file_contents = open( voltage_file_path).read()

	reactive_power_file_name = 'reactivePowerData_AMI.csv'
	reactive_power_file_path = Path( test_data_file_path, reactive_power_file_name )
	reactive_power_file_contents = open(reactive_power_file_path).read()

	real_power_file_name = 'realPowerData_AMI.csv'
	real_power_file_path = Path( test_data_file_path, real_power_file_name )
	real_power_file_contents = open(real_power_file_path).read()

	customer_ids_file_name = 'CustomerIDs_AMI.csv'
	customer_ids_file_path = Path( test_data_file_path, customer_ids_file_name )
	customer_ids_file_contents = open(customer_ids_file_path).read()

	defaultInputs = {
		"modelType": modelName,
		"voltageInputDataFileName": voltage_file_name,
		"voltageInputDataFileContent": voltage_file_contents,
		"realPowerInputDataFileName": real_power_file_name,
		"realPowerInputDataFileContent": real_power_file_contents,
		"reactivePowerInputDataFileName": reactive_power_file_name,
		"reactivePowerInputDataFileContent": reactive_power_file_contents,
		"customerIDInputDataFileName": customer_ids_file_name,
		"customerIDInputDataFileContent": customer_ids_file_contents
	}

	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)

	return creationCode

@neoMetaModel_test_setup
def _disabled_tests():
	# Location
	modelLoc = Path(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		pass # No previous test results.
	# Create New.
	new(modelLoc)
	# Pre-run.
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_disabled_tests()

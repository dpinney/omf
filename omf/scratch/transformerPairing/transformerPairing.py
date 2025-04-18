import warnings
# warnings.filterwarnings("ignore")

# Import Python libraries
import shutil
import numpy as np
from pathlib import Path
import pandas as pd

# OMF imports
import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

# Import custom libraries
from omf.solvers import transformerPairing

# Model metadata:
tooltip = "Transformer Pairing"
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = False

# -*- coding: utf-8 -*-
"""
BSD 3-Clause License

Copyright 2021 National Technology & Engineering Solutions of Sandia, LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

###############################################################################
# Input Data Notes

# custIDInput: list of str (customers) - the list of customer IDs as strings
# transLabelsTrue: numpy array of int (1,customers) - the transformer labels for each customer as integers.  This is the ground truth transformer labels
# transLabelsErrors: numpy array of int (1,customers) - the transformer labels for each customer which may contain errors.
    # In the sample data, customer_3 transformer was changed from 1 to 2 and customer_53 transformer was changed from 23 to 22
# voltageInput: numpy array of float (measurements,customers) - the raw voltage AMI measurements for each customer in Volts
# pDataInput: numpy array of float (measurements, customers) - the real power measurements for each customer in Watts
# qDataInput: numpy array of float (measurements, customers) - the reactive power measurements for each customer in VAr

# Note that the indexing of all variables above should match in the customer index, i.e. custIDInput[0], transLabelsInput[0,0], voltageInput[:,0], pDataInput[:,0], and qDataInput[:,0] should all be the same customer

###############################################################################

def work(modelDir, inputDict):
	''' Run the model in its directory. '''

	useTrueLabels = True # specifies whether to load and use ground truth transformer labels, this will be true when using the provided sample data
	outData = {}
	outData['useTrueLabels'] = useTrueLabels

	with open(Path(modelDir,inputDict['voltageInputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['voltageInputDataFileContent'])
	voltageInputPath = Path(modelDir, inputDict['voltageInputDataFileName'])
	voltageDataSet = pd.read_csv(voltageInputPath, header=None)
	voltageInput = np.array( (pd.DataFrame(voltageDataSet) ).values)

	with open(Path(modelDir,inputDict['realPowerInputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['realPowerInputDataFileContent'])
	realPowerInputPath = Path(modelDir, inputDict['realPowerInputDataFileName'])
	pDataSet = pd.read_csv(realPowerInputPath, header=None)
	pDataInput = np.array( (pd.DataFrame(pDataSet) ).values)

	with open(Path(modelDir,inputDict['reactivePowerInputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['reactivePowerInputDataFileContent'])
	reactivePowerInputPath = Path(modelDir, inputDict['reactivePowerInputDataFileName'])
	qDataSet = pd.read_csv(reactivePowerInputPath, header=None)
	qDataInput = np.array( (pd.DataFrame(qDataSet) ).values)

	with open(Path(modelDir,inputDict['customerIDInputDataFileName']),'w', newline='') as pv_stream:
		pv_stream.write(inputDict['customerIDInputDataFileContent'])
	custIDInputPath = Path(modelDir, inputDict['customerIDInputDataFileName'])
	with open(custIDInputPath, 'r') as file:
		custIDInput = [x.rstrip() for x in file]

	test_data_file_path = Path(omf.omfDir,'static','testFiles', 'transformerPairing')

	transformer_labels_errors_file_name = 'TransformerLabelsErrors_AMI.csv'
	transformer_labels_errors_file_path = Path( test_data_file_path, transformer_labels_errors_file_name )
	transLabelsErrorsDataSet = pd.read_csv(transformer_labels_errors_file_path, header=None)
	transLabelsErrors = np.array( (pd.DataFrame(transLabelsErrorsDataSet) ).values)

	if useTrueLabels:
		transformer_labels_true_file_name = 'TransformerLabelsTrue_AMI.csv'
		transformer_labels_true_file_path = Path( test_data_file_path, transformer_labels_true_file_name )
		transLabelsTrueDataSet = pd.read_csv(transformer_labels_true_file_path, header=None)
		transLabelsTrue = np.array( (pd.DataFrame(transLabelsTrueDataSet) ).values)

	saveResultsPath = modelDir

	###############################################################################
	# Data pre-processing
	# Convert the raw voltage measurements into per unit and difference (delta voltage) representation
	vPU = transformerPairing.M2TUtils.ConvertToPerUnit_Voltage(voltageInput)
	vDV = transformerPairing.M2TUtils.CalcDeltaVoltage(vPU)

	##############################################################################
	#
	#        Error Flagging Section - Correlation Coefficient Analysis

	# Calculate CC Matrix

	#print for Correlation Coefficient
	ccMatrix,noVotesIndex,noVotesIDs = transformerPairing.M2TUtils.CC_EnsMedian(vDV,windowSize=384,custID=custIDInput)

	# The function CC_EnsMedian takes the median CC across windows in the dataset. 
	# This is mainly done to deal with the issue of missing measurements in the dataset
	# If your data does not have missing measurements you could use numpy.corrcoef directly

	# Do a sweep of possible CC Thresholds and rank the flagged results
	notMemberVector = [0.25,0.26,0.27,0.28,0.29,0.30,0.31,0.32,0.33,0.34,0.35,0.36,0.37,0.38,0.39,0.4,0.41,0.42,0.43,0.44,0.45,0.46,0.47,0.48,0.49,0.50,0.51,0.52,0.53,0.54,0.55,0.56,0.57,0.58,0.59,0.60,0.61,0.62,0.63,0.64,0.65,0.66,0.67,0.68,0.69,0.70,0.71,0.72,0.73,0.74,0.75,0.76,0.78,0.79,0.80,0.81,0.82,0.83,0.84,0.85,0.86,0.87,0.88,0.90,0.91]
	allFlaggedTrans, allNumFlagged, rankedFlaggedTrans, rankedTransThresholds = transformerPairing.M2TFuncs.RankFlaggingBySweepingThreshold(transLabelsErrors,notMemberVector,ccMatrix)
	# Plot the number of flagged transformers for all threshold values
	transformerPairing.M2TUtils.PlotNumFlaggedTrans_ThresholdSweep(notMemberVector,allNumFlagged,transLabelsErrors,savePath=saveResultsPath)

	# The main output from this Error Flagging section is rankedFlaggedTrans which
	# contains the list of flagged transformers ranked by correlation coefficient.
	# Transformers at the beginning of the list were flagged with lower CC, indicating
	# higher confidence that those transformers do indeed have errors.

	##############################################################################
	#
	#             Transformer Assignment Section - Linear Regression Steps
	#

	# Calculate the pairwise linear regression
	# print('Starting regression calculation')
	r2Affinity,rDist,xDist,regRDistIndiv,regXDistIndiv,mseMatrix = transformerPairing.M2TUtils.ParamEst_LinearRegression(voltageInput,pDataInput,qDataInput,savePath=saveResultsPath)

	additiveFactor = 0.02
	minMSE, mseThreshold = transformerPairing.M2TUtils.FindMinMSE(mseMatrix,additiveFactor)
	#This sets the mse threshold based on adding a small amount to the smallest MSE value in the pairwise MSE matrix
	# Alternatively you could set the mse threshold manually
	#mseThreshold = 0.3

	# Plot CDF for adjusted reactance distance
	replacementValue = np.max(np.max(xDist))
	xDistAdjusted = transformerPairing.M2TFuncs.AdjustDistFromThreshold(mseMatrix,xDist,mseThreshold, replacementValue)


	# Select a particular set of ranked results using a correlation coefficient threshold
	notMemberThreshold=0.7
	flaggingIndex = np.where(np.array(notMemberVector)==notMemberThreshold)[0][0]
	flaggedTrans = allFlaggedTrans[flaggingIndex]
	predictedTransLabels,allChangedIndices,allChangedOrgTrans,allChangedPredTrans = transformerPairing.M2TFuncs.CorrectFlaggedTransErrors(flaggedTrans,transLabelsErrors,custIDInput,ccMatrix,notMemberThreshold, mseMatrix,xDistAdjusted,reactanceThreshold=0.046)


	# predictedTransLabels: numpy array of int (1,customers) - the predicted labels 
	#   for each customer.  Positive labels will be unchanged from the original
	#   set of transformer labels.  Negative labels will be new transformer groupings
	#   which should be the correct groups of customers served by a particular 
	#   transformer but will require mapping back to a particular physical transformer.
	# In the sample data customer_4 was injected with an incorrect label and should now be grouped with customer_5 and customer_6
	# customer_53 was also injected with an incorrect label and should now be grouped with customer_54 and customer_55

	#transformerPairing.M2TUtils.PrettyPrintChangedCustomers(predictedTransLabels,transLabelsErrors,custIDInput)

	# This function calculates two transformer level metrics of accuracy that we have been using
	# incorrectTrans is a list of incorrect transformers where incorrect means customers added or omitted to the correct grouping
	# This defines Transformer Accuracy, i.e. the number of correct transformers out of the total transformers
	# incorrectPairedIDs lists the customers from incorrect trans which allows us to define 
	# Customer Pairing Accuracy which is the number of customers in the correct groupings, i.e. no customers added or omitted from the grouping
	if useTrueLabels:
			incorrectTrans,incorrectPairedIndices, incorrectPairedIDs= transformerPairing.M2TUtils.CalcTransPredErrors(predictedTransLabels,transLabelsTrue,custIDInput,singleCustMarker=-999)
			incorrectTransOrg,incorrectPairedIndicesOrg, incorrectPairedIDsOrg= transformerPairing.M2TUtils.CalcTransPredErrors(transLabelsErrors,transLabelsTrue,custIDInput, singleCustMarker=-999)
			improvementNum = (len(incorrectTransOrg) - len(incorrectTrans))
			improvementPercent = np.round(((improvementNum  / len(incorrectTransOrg)) * 100),decimals=2)
			outData['incorrectTransOrg'] = str(len(incorrectTransOrg))
			outData['incorrectTransPostAlgo'] = str(len(incorrectTrans))
			outData['improvementNum'] = str(improvementNum)
			outData['improvementPercentage'] = str(improvementPercent) + '%'
			# In the sample data, these will be empty because all customers were correctly grouped together by their service transformer.  

	# Write output to a csv file
	if useTrueLabels:
			df = pd.DataFrame()
			df['customer ID'] = custIDInput
			df['Original Transformer Labels (with errors)'] = transLabelsErrors[0,:]
			df['Predicted Transformer Labels'] = predictedTransLabels[0,:]
			df['Actual Transformer Labels'] = transLabelsTrue[0,:]
			df.to_csv(Path(saveResultsPath,'outputs_PredictedTransformerLabels.csv'))
	else:
			df = pd.DataFrame()
			df['customer ID'] = custIDInput
			df['Original Transformer Labels (with errors)'] = transLabelsErrors[0,:]
			df['Predicted Transformer Labels'] = predictedTransLabels[0,:]
			df.to_csv(Path(saveResultsPath,'outputs_PredictedTransformerLabels.csv'))
	# print('Predicted transformer labels written to outputs_PredictedTransformerLabels.csv')

	df = pd.DataFrame()
	df['Ranked Flagged Transformers'] = flaggedTrans
	df.to_csv(Path(saveResultsPath,'outputs_RankedFlaggedTransformers.csv'))
	# print('Flagged and ranked transformers written to outputs_RankedFlaggedTransformers.csv')

	changedIndices = np.where(predictedTransLabels != transLabelsErrors)[1]
	changedCustomersDF = pd.DataFrame()
	changedCustomersDF['customer ID'] = list(np.array(custIDInput)[changedIndices])
	changedCustomersDF['Original Transformer Labels (with Errors)'] = transLabelsErrors[0,changedIndices]
	changedCustomersDF['Predicted Transformer Labels'] = predictedTransLabels[0,changedIndices]
	filename = 'ChangedCustomers_M2T.csv'
	changedCustomersDF.to_csv(Path(saveResultsPath,filename))
	# print('All customers with changed transformer labels written to ChangedCustomers_M2T.csv')

	# Delete output file every run if it exists	
	outData['minMSEValue'] = minMSE
	outData['customerTableHeadings'] = changedCustomersDF.columns.values.tolist()
	outData['customerTableValues'] = ( list(changedCustomersDF.sort_values( by="customer ID", ascending=True, ignore_index=True ).itertuples(index=False, name=None)))
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

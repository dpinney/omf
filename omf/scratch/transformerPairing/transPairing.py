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


##############################################################################

# Import standard Python libraries
import sys
import numpy as np
#import datetime
#from copy import deepcopy
from pathlib import Path
import pandas as pd

# Import custom libraries
from omf.solvers import transformerPairing
import omf
 
###############################################################################


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

useTrueLabels = True # specifies whether to load and use ground truth transformer labels, this will be true when using the provided sample data
# dont need to support this comparison - set to false

# Load Sample data
currentDirectory = Path(__file__).parent.resolve()
filePath = Path(omf.omfDir,'static','testFiles', 'transformerPairing')

filename = Path(filePath,'voltageData_AMI.csv')
voltageDataSet = pd.read_csv(filename, header=None)
voltageInput = np.array( (pd.DataFrame(voltageDataSet) ).values)

filename = Path(filePath,'realPowerData_AMI.csv')
pDataSet = pd.read_csv(filename, header=None)
pDataInput = np.array( (pd.DataFrame(pDataSet) ).values)

filename = Path(filePath,'reactivePowerData_AMI.csv')
qDataSet = pd.read_csv(filename, header=None)
qDataInput = np.array( (pd.DataFrame(qDataSet) ).values)

filename = Path(filePath,'TransformerLabelsErrors_AMI.csv')
transLabelsErrorsDataSet = pd.read_csv(filename, header=None)
transLabelsErrors = np.array( (pd.DataFrame(transLabelsErrorsDataSet) ).values)

filename = Path(filePath,'CustomerIDs_AMI.csv')
with open(filename, 'r') as file:
	custIDInput = [x.rstrip() for x in file]

if useTrueLabels:
    filename = Path(filePath,'TransformerLabelsTrue_AMI.csv')
    transLabelsTrueDataSet = pd.read_csv(filename, header=None)
    transLabelsTrue = np.array( (pd.DataFrame(transLabelsTrueDataSet) ).values)

saveResultsPath = Path(currentDirectory,'Results_M2T_pqvlabels')

###############################################################################

###############################################################################
# Data pre-processing
# Convert the raw voltage measurements into per unit and difference (delta voltage) representation
vPU = transformerPairing.M2TUtils.ConvertToPerUnit_Voltage(voltageInput)
vDV = transformerPairing.M2TUtils.CalcDeltaVoltage(vPU)


##############################################################################
#
#        Error Flagging Section - Correlation Coefficient Analysis

# Calculate CC Matrix
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
print('Starting regression calculation')
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

print('')
print('')
print('Meter to Transformer Pairing Algorithm Results')
transformerPairing.M2TUtils.PrettyPrintChangedCustomers(predictedTransLabels,transLabelsErrors,custIDInput)


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
    print('')
    print('There were originally ' + str(len(incorrectTransOrg)) + ' incorrect transformer groupings with the injected incorrect labels')
    print('After running algorithm there are ' + str(len(incorrectTrans)) + ' incorrect transformer groupings')
    print(str(improvementNum) + ' transformer groupings were corrected, which is an improvement of ' + str(improvementPercent) + '%')
    # In the sample data, these will be empty because all customers were correctly grouped together by their service transformer.  
    


# Write output to a csv file
print('')
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
print('Predicted transformer labels written to outputs_PredictedTransformerLabels.csv')

df = pd.DataFrame()
df['Ranked Flagged Transformers'] = flaggedTrans
df.to_csv(Path(saveResultsPath,'outputs_RankedFlaggedTransformers.csv'))
print('Flagged and ranked transformers written to outputs_RankedFlaggedTransformers.csv')



changedIndices = np.where(predictedTransLabels != transLabelsErrors)[1]
df = pd.DataFrame()
df['customer ID'] = list(np.array(custIDInput)[changedIndices])
df['Original Transformer Labels (with Errors)'] = transLabelsErrors[0,changedIndices]
df['Predicted Transformer Labels'] = predictedTransLabels[0,changedIndices]
filename = 'ChangedCustomers_M2T.csv'
df.to_csv(Path(saveResultsPath,filename))
print('All customers with changed transformer labels written to ChangedCustomers_M2T.csv')
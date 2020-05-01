import csv, time, itertools
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.metrics import confusion_matrix
from scipy import stats

import warnings
warnings.filterwarnings("ignore", 
    message="The input array could not be properly checked for nan values. nan values will be ignored.")

# constants -------------------------------------------------------------------

TRAIN_FRACTION = 0.8
VALIDATION_FRACTION = 0.1
TEST_FRACTION = 0.1
TIMEPOINTS_PER_THEFT = 4*24

TRAIN_FILE = '../data/dataOlin-1b-6mo.csv'
TEST_FILE = '../data/dataOlin-1-6mo.csv'
SEED = 42

IGNORE_LABELS = ['']

# helper functions ------------------------------------------------------------

def plot_confusion_matrix(cm, classes, normalize=False, title='Confusion matrix', 
    cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')

# read in train data ----------------------------------------------------------

trainX, trainY = [], []
header  = []
colorList = []
uniqueLabels = []
colorNum = -1
lastLabel = ''

with open( TRAIN_FILE,'r' ) as trainFile:
    reader = csv.reader(trainFile, delimiter=',')
    
    for row in reader:
        if 'meterID' in row:
            header = row
        else:

            datapoint = []
            label = row[-1]

            if label not in IGNORE_LABELS:

                # restart counter when we transition to new label and update colorNum
                if label != lastLabel:
                    count = 0
                    colorNum += 1
                    uniqueLabels.append(label)
                
                datapoint.append(count)
                colorList.append(colorNum)

                # populate datapoint
                for index,data in enumerate(row):

                    # timestamp and meterID and label are not part of the datapoint 
                    # convert everything to float
                    if (index>1) and (index != (len(row)-1)):
                        datapoint.append(float(data))
                        
                trainX.append( datapoint )
                trainY.append( label )
                
                count += 1
                lastLabel = label


# read in test data -----------------------------------------------------------

testX, testY = [], []
header  = []
colorList = []
colorNum = -1
lastLabel = ''

with open( TEST_FILE,'r' ) as testFile:
    reader = csv.reader(testFile, delimiter=',')
    
    for row in reader:
        if 'meterID' in row:
            header = row
        else:

            datapoint = []
            label = row[-1]

            if label not in IGNORE_LABELS:

                # restart counter when we transition to new label and update colorNum
                if label != lastLabel:
                    count = 0
                    colorNum += 1
                
                datapoint.append(count)
                colorList.append(colorNum)

                # populate datapoint
                for index,data in enumerate(row):

                    # timestamp and meterID and label are not part of the datapoint 
                    # convert everything to float
                    if (index>1) and (index != (len(row)-1)):
                        datapoint.append(float(data))
                        
                testX.append( datapoint )
                testY.append( label )
                
                count += 1
                lastLabel = label

# sort data -------------------------------------------------------------------

newX = np.array(trainX)
trainX = np.array(trainX)
trainY = np.array(trainY)
testX = np.array(testX)
testY = np.array(testY)

ordering = np.argsort(trainX[:,0])
trainX = trainX[ordering]
trainY = trainY[ordering]
ordering = np.argsort(testX[:,0])
testX = testX[ordering]
testY = testY[ordering]

# classify --------------------------------------------------------------------

numPoints = trainX.shape[0]
split = int(TRAIN_FRACTION * numPoints)
xTrain = trainX[:split,:]
yTrain = trainY[:split]

numPoints = int(VALIDATION_FRACTION * numPoints)
xVal = trainX[split:split+numPoints,:]
yVal = trainY[split:split+numPoints]

numPoints = testX.shape[0]
numPoints = int(TEST_FRACTION * numPoints) 
xHoldout = testX[-numPoints:,:]
yHoldout = testY[-numPoints:]
    
labels = np.unique(yTrain)
labels = np.sort(labels)

# iterate over classifiers
for condition in ['val','holdout']:
    print(condition)
    for depth in range(1,51):

        if condition == 'val':
            xTest = xVal
            yTest = yVal
        elif condition == 'holdout':
            xTest = xHoldout
            yTest = yHoldout

        # classify all conditions   
        clf = DecisionTreeClassifier(max_depth=depth, random_state=SEED)
        clf.fit(xTrain,yTrain)
        yPredicted = clf.predict(xTest)
        confMat = confusion_matrix(yTest, yPredicted)
        score1 = np.sum(yPredicted==yTest) / float(yTest.shape[0])

        # if a datapoint is predicted as theft, make sure its actually theft by
        # making sure a majority of the previous TIMEPOINTS_PER_THEFT points were also 
        # predicted as theft, gets rid of erronous theft predictions that may only occur for
        # a few timepoints
        yPredictedNew = np.array(yPredicted)
        for pNum, prediction in enumerate(yPredicted):
            
            if prediction == 'theft':
                trueClass = yTest[pNum]
                previousPredictionsLocs = yTest==trueClass
                previousPredictionsLocs[pNum+1:] = False
                previousPredictions = yPredicted[previousPredictionsLocs] 
                if len(previousPredictions)>TIMEPOINTS_PER_THEFT:
                    previousPredictions = previousPredictions[-TIMEPOINTS_PER_THEFT:]

                mode = stats.mode(previousPredictions, axis=None)
                yPredictedNew[pNum] = mode[0][0]        
           
        confMatNew = confusion_matrix(yTest, yPredictedNew)
        scoreNew = np.sum(yPredictedNew==yTest) / float(yTest.shape[0])
        
        print(depth,round(score1,2),round(scoreNew,2))    
        # plt.figure()
        # plot_confusion_matrix(confMat, labels, normalize=True, title=name)  
        # plt.figure()
        # plot_confusion_matrix(confMatNew, labels, normalize=True, title=name)
        # plt.show()
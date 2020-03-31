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

# constants -------------------------------------------------------------------

TRAIN_FRACTION = 0.9
TIMEPOINTS_PER_THEFT = 8

TRAIN_FILE = '../data/dataOlin-1b-6mo.csv'
TEST_FILE = '../data/dataOlin-1-6mo.csv'

IGNORE_LABELS = ['']

# TRAIN_FILE = '../data/dataABEC-1mo.csv'
# TEST_FILE = '../data/dataOlin-DEC-1mo.csv'

# TRAIN_FILE = '../data/dataDEC-1mo.csv'
# TEST_FILE = '../data/dataOlin-ABEC-1mo.csv'

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

names = ["Nearest Neighbors", "Linear SVM", "RBF SVM",
         "Decision Tree", "Random Forest", "Neural Net", "AdaBoost",
         "Naive Bayes"]

classifiers = [
    KNeighborsClassifier(3),
    SVC(kernel="linear", C=0.025),
    SVC(gamma=2, C=1),
    DecisionTreeClassifier(max_depth=5),
    RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
    MLPClassifier(alpha=1, max_iter=1000),
    AdaBoostClassifier(),
    GaussianNB()
]

# normalize data and split into train/test
trainX = StandardScaler().fit_transform(trainX)
testX = StandardScaler().fit_transform(testX)

numPoints = trainX.shape[0]
split = int(TRAIN_FRACTION * numPoints)
xTrain = trainX[:split,:]
yTrain = trainY[:split]

numPoints = testX.shape[0]
split = int(TRAIN_FRACTION * numPoints)
xTest = testX[split:,:]
yTest = testY[split:]
    
labels = np.unique(yTest)
labels = np.sort(labels)


xTrainTheft = []
for index in range( xTrain.shape[0]-TIMEPOINTS_PER_THEFT ):
    datapoint = []
    for pointNum in range(TIMEPOINTS_PER_THEFT):
        datapoint = np.concatenate( (datapoint,xTrain[index+pointNum,1:]) )
    xTrainTheft.append(datapoint)

xTestTheft = []
for index in range( xTest.shape[0]-TIMEPOINTS_PER_THEFT ):
    datapoint = []
    for pointNum in range(TIMEPOINTS_PER_THEFT):
        datapoint = np.concatenate( (datapoint,xTest[index+pointNum,1:]) )
    xTestTheft.append(datapoint)

xTrainTheft = np.array(xTrainTheft)
yTrainTheft = np.array(yTrain[:-TIMEPOINTS_PER_THEFT])
yTrainTheft[ yTrainTheft != 'theft' ] = 'notTheft'

xTrainNotTheft = xTrain[ yTrain != 'theft', : ]
yTrainNotTheft = yTrain[ yTrain != 'theft' ]

# iterate over classifiers
for name, clf in zip(names, classifiers):

    # classify all conditions    
    clf.fit(xTrain,yTrain)
    yPredicted = clf.predict(xTest)
    confMat = confusion_matrix(yTest, yPredicted)
    score1 = np.sum(yPredicted==yTest) / float(yTest.shape[0])

    # classify theft vs non-theft first
    clf.fit(xTrainTheft, yTrainTheft)
    yPredicted = clf.predict(xTestTheft)
    yPredictedTheft = yPredicted[ yPredicted == 'theft' ]
    # filter out predicted non-thefts 
    xTestNotTheft = xTest[ :-TIMEPOINTS_PER_THEFT, : ]
    xTestNotTheft = xTestNotTheft[ yPredicted != 'theft', : ]
    # classify non thefts further 
    clf.fit(xTrainNotTheft, yTrainNotTheft)
    yPredictedNotTheft = clf.predict(xTestNotTheft)
    # comparmentalize out ground truths
    yTestTheft = yTest[ :-TIMEPOINTS_PER_THEFT ]
    yTestTheft = yTestTheft[ yPredicted == 'theft' ]
    yTestNotTheft = yTest[ :-TIMEPOINTS_PER_THEFT ]
    yTestNotTheft = yTestNotTheft[ yPredicted != 'theft' ]
    # generate confmat
    yPredictedNew = np.concatenate((yPredictedTheft,yPredictedNotTheft))
    yTestNew = np.concatenate((yTestTheft,yTestNotTheft))
    confMatNew = confusion_matrix(yTestNew, yPredictedNew)
    score2 = np.sum(yPredictedNew==yTestNew) / float(yTestNew.shape[0])
    
    print(name,round(score1,2),round(score2,2))
    # plt.figure()
    # plt.subplot(1,2,1)
    # plot_confusion_matrix(confMat, labels, normalize=True, title=name)  
    # plt.subplot(1,2,2)
    # plot_confusion_matrix(confMatNew, labels, normalize=True, title=name)
    # plt.show()
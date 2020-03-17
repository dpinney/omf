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

PLOTTING_FEATURE_NUM_1 = 0
PLOTTING_FEATURE_NUM_2 = 1
VISUALIZE_DATA_ONLY = False
TRAIN_FRACTION = 0.9
INPUT_FILE = '../data/dataABEC-1mo.csv'

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

# load data
x, y, header, colorList, uniqueLabels = [], [], [], [], []
colorNum = -1
lastLabel = ''

with open( INPUT_FILE,'r' ) as dataFile:
    reader = csv.reader(dataFile, delimiter=',')
    
    for row in reader:
        
        if 'meterID' in row:
            header = row

        else:

            datapoint = []
            label = row[-1]

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
                    
            x.append( datapoint )
            y.append( label )
            
            count += 1
            lastLabel = label

newX = np.array(x)
x = np.array(x)
y = np.array(y)
ordering = np.argsort(x[:,0])

x = x[ordering]
y = y[ordering]

numPoints = x.shape[0]
print(numPoints)
split = int(TRAIN_FRACTION * numPoints)


if VISUALIZE_DATA_ONLY: 
    pass;

else: # classify

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
    x = StandardScaler().fit_transform(x)
    
    xTrain, xTest, yTrain, yTest = x[:split,:], x[split:,:], y[:split], y[split:]
    print(xTrain.shape)
    print(yTrain.shape)
    print(xTest.shape)
    print(yTest.shape)


    # iterate over classifiers
    for name, clf in zip(names, classifiers):
        
        start = time.time()
        clf.fit(xTrain, yTrain)
        endTrain = time.time()
        yPredicted = clf.predict(xTest)
        endTest = time.time()
        totalTrain = endTrain-start
        totalTest = endTest-endTrain
        print('Train: {} seconds, Predict: {} seconds'.format(totalTrain, totalTest))        
        
        confMat = confusion_matrix(yTest, yPredicted, labels=uniqueLabels)
        score = clf.score(xTest, yTest)
        
        plt.figure()
        plot_confusion_matrix(confMat, uniqueLabels, normalize=True, title=name)
        print(name,score)
        print('')
    
# plot data
header = ['timepoint'] + header[2:-1]
plt.figure()
plt.scatter(newX[:,PLOTTING_FEATURE_NUM_1], newX[:,PLOTTING_FEATURE_NUM_2], c=colorList)
plt.colorbar()
plt.tight_layout()
plt.ylabel(header[PLOTTING_FEATURE_NUM_2])
plt.xlabel(header[PLOTTING_FEATURE_NUM_1])
plt.show()
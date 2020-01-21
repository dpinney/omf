import csv, time
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

h = 1  # step size in the mesh

names = ["Nearest Neighbors", "Linear SVM", "RBF SVM", "Gaussian Process",
         "Decision Tree", "Random Forest", "Neural Net", "AdaBoost",
         "Naive Bayes", "QDA"]

classifiers = [
    KNeighborsClassifier(3),
    SVC(kernel="linear", C=0.025),
    SVC(gamma=2, C=1),
    GaussianProcessClassifier(1.0 * RBF(1.0)),
    DecisionTreeClassifier(max_depth=5),
    RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
    MLPClassifier(alpha=1, max_iter=1000),
    AdaBoostClassifier(),
    GaussianNB(),
    QuadraticDiscriminantAnalysis()]

# preprocess dataset, split into training and test part
X, y = [], []
count = 0
firstNonFault = False

with open( 'extractedData.csv','r' ) as dataFile:
    reader = csv.reader(dataFile, delimiter=',')
    
    for row in reader:
        
        datapoint = []
        label = -1
        
        # if fault, label is 1; otherwise label is 0
        if row[-1] != 'None':
            label = 1
        
        else:
            label = 0

            # restart counter when we transition from faulty data to fault free data
            if firstNonFault == False:
                firstNonFault = True
                count = 0
        
        datapoint.append(count)
        count += 1

        for index,data in enumerate(row):

            # if not label, convert to float
            if index != (len(row)-1):
                datapoint.append(float(data))
            
    
        X.append( datapoint )
        y.append( label )


newX = np.array(X)
plt.scatter(newX[:,0], newX[:,1], c=y)
plt.colorbar()
plt.show()

#raise Exception('STOP')

# normalize data and split into train/test
X = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = \
    train_test_split(X, y, test_size=.4, random_state=42)

# iterate over classifiers
for name, clf in zip(names, classifiers):
    clf.fit(X_train, y_train)
    score = clf.score(X_test, y_test)
    print(name,score)
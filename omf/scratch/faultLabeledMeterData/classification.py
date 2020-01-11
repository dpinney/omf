import csv, time
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

with open( 'powerAndLabels.csv','r' ) as dataFile:
    reader = csv.reader(dataFile, delimiter=',')
    
    for row in reader:
        
        X.append( [count,float(row[0])] )
        
        if row[1] == 'None':
            y.append(0)

            if firstNonFault == False:
                firstNonFault = True
                count = 0
        
        else:
            y.append(1)

        count += 1

# normalize data and split into train/test
X = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = \
    train_test_split(X, y, test_size=.4, random_state=42)

# iterate over classifiers
for name, clf in zip(names, classifiers):
    
    start = time.time()
    clf.fit(X_train, y_train)
    score = clf.score(X_test, y_test)
    print(name,score)
    end = time.time()
    print((end - start)/60.0)
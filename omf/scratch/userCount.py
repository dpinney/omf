# Count the number of registered users of the OMF locally.

import os

omfDir = os.path.dirname(os.path.dirname(__file__))

# User files, ignoring hidden and removing .json file extensions:
userFiles = [x[0:-5] for x in os.listdir(os.path.join(omfDir,'data','User')) if not x.startswith('.')]

# Any quickrun users:
modelDirs = [x for x in os.listdir(os.path.join(omfDir,'data','Model')) if not x.startswith('.')]

# Combine everything and remove duplicates with sets:
allUsers = set(userFiles).union(set(modelDirs)) - set(['public','admin','test'])

print 'Number of users:', len(allUsers)
print 'All registered emails:', list(allUsers)

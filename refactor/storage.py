#!/usr/bin/env python

import cPickle as pickle
import os

class Storage:
	''' A class for storing OMF data in a filesystem... '''
	directory = None
	supportedTypes = ['StudyGridlab','Grid','GridComponent','Climate']

	def __init__(self, directory):
		self.directory = directory
		# if we don't already have the required folders here, make them:
		directories = os.listdir(self.directory)
		for objectType in self.supportedTypes:
			if objectType not in directories:
				os.mkdir(self.directory + '/' + objectType)

	def persist(self, objectInstance):
		''' persist(objectName)-> success boolean.'''
		objectType = objectInstance.__class__.__name__
		objectName = objectInstance.name
		if objectType not in self.supportedTypes:
			return False
		else:
			metadata = {}
			for attribute in dir(objectInstance):
				attrValue = getattr(objectInstance,attribute)
				if type(attrValue) in [str,int,float]:
					metadata[attribute] = attrValue
			with open(objectType + '/' + objectName + '.md','w') as mdFile, open(objectType + '/' + objectName + '.pickle','w') as pickFile:
				mdFile.write(str(metadata))
				pickle.dump(objectInstance,pickFile)
			return True

	def path(self, objectType, objectName):
		pathToMd = self.directory + '/' + objectType + '/' + objectName + '.md'
		if os.path.isfile(pathToMd):
			return pathToMd
		else:
			return ''

	def fetch(self, objectType, objectName):
		pathToMd = self.path(objectType, objectName)
		if pathToMd != '':
			with open(pathToMd,'r') as mdFile, open(pathToMd[0:-2] + 'pickle') as pickFile:
				md = eval(mdFile.read())
				objectInstance = pickle.load(pickFile)
				# synch the metadata back up with the object:
				for key in md:
					if key[0] != '_':
						setattr(objectInstance, key, md[key])
				return objectInstance
		else:
			return False

	def listAll(self, objectType):
		if objectType not in self.supportedTypes:
			return []
		else:
			return os.listdir(self.directory + '/' + objectType)

	def getMetadata(self, objectType, objectName):
		pathToMd = self.path(objectType, objectName)
		if pathToMd != '':
			with open(pathToMd,'r') as mdFile:
				return eval(mdFile.read())
		else:
			return False

	def putMetadata(self, objectType, objectName, mdDict):
		pathToMd = self.path(objectType, objectName)
		if pathToMd != '':
			with open(pathToMd,'w') as mdFile:
				mdFile.write(str(mdDict))
				return True
		else:
			return False

	def delete(self, objectType, objectName):
		pathToMd = self.path(objectType, objectName)
		if pathToMd != '':
			os.remove(pathToMd)
			os.remove(pathToMd[0:-2] + 'pickle')
			return True
		else:
			return False


def main():
	''' Testing here. '''
	storeHere = Storage('.')
	print str(storeHere.listAll('Grid'))
	import studyGridlab
	test = studyGridlab.main()
	storeHere.persist(test)
	print storeHere.getMetadata('StudyGridlab','chicken')
	print storeHere.putMetadata('StudyGridlab','chicken',{'status': 'postRun', '__module__': 'studyGridlab', 'runTime': 666, 'pid': 4888, 'name': 'chicken'})
	print storeHere.getMetadata('StudyGridlab','chicken')
	testBack = storeHere.fetch('StudyGridlab','chicken')
	print dir(testBack)
	storeHere.delete('StudyGridlab','chicken')

if __name__ == '__main__':
	main()
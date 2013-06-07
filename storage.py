#!/usr/bin/env python


''' First attempt at a storage abstraction layer. '''

import os
import traceback
import json

class Filestore:
	storagePath = None

	def __init__(self, inStoragePath):
		if not os.path.exists(inStoragePath):
			# We're using an existing store:
			os.mkdir(inStoragePath)
		self.storagePath = os.path.abspath(inStoragePath)

	def __checkObjectFolder(self, objectType):
		folderPath = os.path.join(self.storagePath, objectType)
		if not os.path.isdir(folderPath):
			os.mkdir(folderPath)

	def put(self, objectType, objectName, jsonDict=None, mdDict=None):
		if jsonDict==None and mdDict==None:
			# Degenerate case.
			return False
		try:
			basePath = os.path.join(self.storagePath, objectType, objectName)
			self.__checkObjectFolder(objectType)
			if jsonDict != None:
				if self.exists(objectType, objectName):
					# Overwrite with no mercy:
					self.delete(objectType, objectName)
				with open(basePath + '.json', 'w') as objectFile:
					json.dump(jsonDict, objectFile, indent=4)
			if mdDict != None:
				if self.hasMetadata(objectType, objectName):
					# Overwrite!
					self.deleteMd(objectType, objectName)
				with open(basePath + '.md.json', 'w') as mdFile:
					json.dump(mdDict, mdFile, indent=4)
			return True
		except:
			traceback.print_exc()
			return False

	def get(self, objectType, objectName, raw=False):
		try:
			# This hack is in here to deal with tmy2s. Eventually we'll make a serializable weather object.
			if raw == True:
				with open(os.path.join(self.storagePath, objectType, objectName), 'r') as objectFile:
					return objectFile.read()
			else:
				with open(os.path.join(self.storagePath, objectType, objectName) + '.json', 'r') as objectFile:
					return json.load(objectFile)
		except:
			traceback.print_exc()
			return ''

	def getMetadata(self, objectType, objectName):
		try:
			with open(os.path.join(self.storagePath, objectType, objectName) + '.md.json', 'r') as objectFile:
				data = json.load(objectFile)
				data['name'] = objectName
				return data
		except:
			traceback.print_exc()
			return {}

	def delete(self, objectType, objectName):
		basePath = os.path.join(self.storagePath, objectType, objectName)
		try:
			os.remove(basePath + '.json')
			if self.hasMetadata(objectType, objectName):
				os.remove(basePath + '.md.json')
			return True
		except:
			traceback.print_exc()
			return False

	def deleteMd(self, objectType, objectName):
		basePath = os.path.join(self.storagePath, objectType, objectName)
		try:
			os.remove(basePath + '.md.json')
			return True
		except:
			traceback.print_exc()
			return False

	def listAll(self, objectType):
		try:
			return [obFile[0:-5] for obFile in os.listdir(os.path.join(self.storagePath,objectType)) if not obFile.endswith('.md.json')]
		except:
			traceback.print_exc()
			return []

	def hasMetadata(self, objectType, objectName):
		return os.path.isfile(os.path.join(self.storagePath,objectType,objectName + '.md.json'))

	def exists(self, objectType, objectName):
		return os.path.isfile(os.path.join(self.storagePath,objectType,objectName + '.json'))

class DatabaseStore:
	# TODO: implement me.
	pass

if __name__ == '__main__':
	# Tests go here.
	import shutil
	test = Filestore('./testFileStore/')
	print 'Feeder ACEC in the store?', test.exists('Feeder', 'ACEC')
	print 'Can we store a simple int?', test.put('int', 'testInt', jsonDict={'value':34})
	print 'Get it back', test.get('int', 'testInt')
	print 'Now put something with an MD.', test.put('feeder', 'testFeeder', jsonDict={"component1":{"test":1},"component2":{"bullseye":5}}, mdDict={"name":"powder"})
	print 'What was that MD?', test.getMetadata('feeder', 'testFeeder')
	print 'List something.', test.listAll('feeder')
	# Cleanup:
	shutil.rmtree('./testFileStore/')
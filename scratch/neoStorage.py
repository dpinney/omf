#!/usr/bin/env python


''' First attempt at a storage abstraction layer. '''

import os
import traceback
import json

class Filestore:
	def __init__(self, inStoragePath):
		if not os.path.exists(inStoragePath):
			# We're using an existing store:
			os.mkdir(inStoragePath)
		self.storagePath = os.path.abspath(inStoragePath)

	def __checkObjectFolder(self, objectType):
		folderPath = os.path.join(self.storagePath, objectType)
		if not os.path.isdir(folderPath):
			os.mkdir(folderPath)

	def put(self, objectType, objectName, putDict, justMd=False):
		dataDict = {key:putDict[key] for key in putDict if type(putDict[key]) is dict or type(putDict[key]) is list}
		mdDict = {key:putDict[key] for key in putDict if type(putDict[key]) is not dict and type(putDict[key]) is not list}
		try:
			basePath = os.path.join(self.storagePath, objectType, objectName)
			self.__checkObjectFolder(objectType)
			if not justMd and dataDict != {}:
				if self.hasData(objectType, objectName):
					self.delete(objectType, objectName)
				with open(basePath + '.json', 'w') as objectFile:
					json.dump(dataDict, objectFile, indent=4)
			if self.exists(objectType, objectName):
				self.delete(objectType, objectName, justMd=True)
			with open(basePath + '.md', 'w') as mdFile:
				json.dump(mdDict, mdFile, indent=4)
			return True
		except:
			traceback.print_exc()
			return False

	def get(self, objectType, objectName, justMd=False):
		try:
			dataDict = {}
			pathPrefix = os.path.join(self.storagePath, objectType, objectName)
			if not justMd and self.hasData(objectType, objectName):
				with open(pathPrefix + '.json', 'r') as objectFile:
					dataDict = json.load(objectFile)
			with open(pathPrefix + '.md', 'r') as objectFile:
				mdDict = json.load(objectFile)
			return dict({'name':objectName}.items() + mdDict.items() + dataDict.items())
		except:
			traceback.print_exc()
			return ''

	def delete(self, objectType, objectName, justMd=False):
		basePath = os.path.join(self.storagePath, objectType, objectName)
		try:
			if not justMd and self.hasData(objectType, objectName):
				os.remove(basePath + '.json')
			if self.exists(objectType, objectName):
				os.remove(basePath + '.md')
			return True
		except:
			traceback.print_exc()
			return False

	def listAll(self, objectType):
		try:
			return [obFile[0:-3] for obFile in os.listdir(os.path.join(self.storagePath,objectType)) if obFile.endswith('.md')]
		except:
			traceback.print_exc()
			return []

	def hasData(self, objectType, objectName):
		return os.path.isfile(os.path.join(self.storagePath,objectType,objectName + '.json'))

	def exists(self, objectType, objectName):
		return os.path.isfile(os.path.join(self.storagePath,objectType,objectName + '.md'))

class DatabaseStore:
	# TODO: implement me.
	pass

if __name__ == '__main__':
	# Tests go here.
	import shutil
	test = Filestore('./testFileStore/')
	print 'Feeder ACEC in the store?', test.exists('Feeder', 'ACEC')
	print 'Can we store a simple int?', test.put('int', 'testInt', {'value':34})
	print 'Get it back', test.get('int', 'testInt')
	print 'Now put something with an MD.', test.put('feeder', 'testFeeder', {"component1":{"test":1},"component2":{"bullseye":5}, "norman":"powder"})
	print 'What was that MD?', test.get('feeder', 'testFeeder', justMd=True)
	print 'List something.', test.listAll('feeder')
	print 'Full feeder get back', test.get('feeder','testFeeder')
	# Cleanup:
	shutil.rmtree('./testFileStore/')
#!/usr/bin/env python


import os, traceback, json, boto
from boto.s3.connection import S3Connection

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

	def put(self, objectType, objectName, putDict):
		try:
			basePath = os.path.join(self.storagePath, objectType, objectName)
			self.__checkObjectFolder(objectType)
			if self.exists(objectType, objectName):
				self.delete(objectType, objectName)
			with open(basePath + '.json', 'w') as objectFile:
				json.dump(putDict, objectFile, indent=4)
			return True
		except:
			traceback.print_exc()
			return False

	def get(self, objectType, objectName):
		try:
			pathPrefix = os.path.join(self.storagePath, objectType, objectName)
			with open(pathPrefix + '.json', 'r') as objectFile:
				dataDict = json.load(objectFile)
				dataDict['name'] = objectName
				return dataDict
		except:
			traceback.print_exc()
			return {}

	def delete(self, objectType, objectName):
		basePath = os.path.join(self.storagePath, objectType, objectName)
		try:
			if self.exists(objectType, objectName):
				os.remove(basePath + '.json')
			return True
		except:
			traceback.print_exc()
			return False

	def listAll(self, objectType):
		try:
			pathPrefix = os.path.join(self.storagePath,objectType)
			return [obFile[0:-5] for obFile in os.listdir(pathPrefix) if obFile.endswith('.json')]
		except:
			traceback.print_exc()
			return []

	def exists(self, objectType, objectName):
		return os.path.isfile(os.path.join(self.storagePath,objectType,objectName + '.json'))

class S3store:
	def __init__(self, publicKey, privateKey, bucketName):
		self.conn = S3Connection(publicKey, privateKey)
		self.bucket = self.conn.get_bucket(bucketName)

	def put(self, objectType, objectName, putDict):
		try:
			if self.exists(objectType, objectName):
				thisKey = self.bucket.get_key(objectType + '/' + objectName + '.json')
			else:
				thisKey = self.bucket.new_key(objectType + '/' + objectName + '.json')
			thisKey.set_contents_from_string(json.dumps(putDict, indent=4))
			return True
		except:
			traceback.print_exc()
			return False

	def get(self, objectType, objectName):
		try:
			thisOb = json.loads(self.bucket.get_key(objectType + '/' + objectName + '.json').get_contents_as_string())
			thisOb['name'] = objectName
			return thisOb
		except:
			traceback.print_exc()
			return {}

	def delete(self, objectType, objectName):
		try:
			self.bucket.delete_key(objectType + '/' + objectName + '.json')
			return True
		except:
			traceback.print_exc()
			return False

	def listAll(self, objectType):
		try:
			keyList = self.bucket.list(prefix=objectType+'/',delimiter='/')
			return [key.name[len(objectType)+1:-5] for key in keyList if key.name.endswith('.json')]
		except:
			traceback.print_exc()
			return []

	def exists(self, objectType, objectName):
		try:
			return self.bucket.get_key(objectType + '/' + objectName + '.json') is not None
		except:
			return None

if __name__ == '__main__':
	# Filstore tests with cleanup.
	import shutil
	print '---TESTING FILESTORE---'
	test = Filestore('./testFileStore/')
	print 'Feeder ACEC in the store?', test.exists('Feeder', 'ACEC')
	print 'Can we store a simple int?', test.put('int', 'testInt', {'value':34})
	print 'Get it back', test.get('int', 'testInt')
	print 'Now put something with an MD.', test.put('feeder', 'testFeeder', {"component1":{"test":1},"component2":{"bullseye":5}, "norman":"powder"})
	print 'What was that MD?', test.get('feeder', 'testFeeder')
	print 'List something.', test.listAll('feeder')
	print 'Full feeder get back', test.get('feeder','testFeeder')
	shutil.rmtree('./testFileStore/')
	# S3store tests with cleanup.
	print '---TESTING S3STORE---'
	s3 = S3store('AKIAIFNNIT7VXOXVFPIQ', 'stNtF2dlPiuSigHNcs95JKw06aEkOAyoktnWqXq+', 'ohdwptestthisbucket')
	print 'Feeder ACEC in the store?', s3.exists('Feeder', 'ACEC')
	print 'Can we store a simple int?', s3.put('int', 'testInt', {'value':34})
	print 'Get it back', s3.get('int', 'testInt')
	print 'Now put something with an MD.', s3.put('feeder', 'testFeeder', {"component1":{"test":1},"component2":{"bullseye":5}, "norman":"powder"})
	print 'What was that MD?', s3.get('feeder', 'testFeeder')
	print 'List something.', s3.listAll('feeder')
	print 'Full feeder get back', s3.get('feeder','testFeeder')

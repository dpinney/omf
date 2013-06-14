#!/usr/bin/env python


import os, trackeback, json, boto

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
	def __init__(self):
		self.conn = S3Connection('AKIAIFNNIT7VXOXVFPIQ', 'stNtF2dlPiuSigHNcs95JKw06aEkOAyoktnWqXq+')
		bucket = conn.get_bucket('ohdwptestthisbucket')

	def put(self, objectType, objectName, putDict):
		try:
			if self.exists(objectType, objectName):
				thisKey = bucket.get_key(objectType + '/' + objectName + '.json')
			else:
				thisKey = bucket.new_key(objectType + '/' + objectName + '.json')
			thisKey.set_contents_from_string(json.dumps(putDict, indent=4))
			return True
		except:
			traceback.print_exc()
			return False

	def get(self, objectType, objectName):
		try:
			thisOb = json.loads(bucket.get_key(objectType + '/' + objectName + '.json').get_contents_as_string())
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
			return [key.name[0:-5] for key in keyList if key.name.endswith('.json')]
		except:
			traceback.print_exc()
			return []

	def exists(self, objectType, objectName):
		try:
			return self.bucket.get_key(objectType + '/' + objectName + '.json') is not None
		else:
			return None

if __name__ == '__main__':
	# Tests go here.
	import shutil
	test = Filestore('./testFileStore/')
	print 'Feeder ACEC in the store?', test.exists('Feeder', 'ACEC')
	print 'Can we store a simple int?', test.put('int', 'testInt', {'value':34})
	print 'Get it back', test.get('int', 'testInt')
	print 'Now put something with an MD.', test.put('feeder', 'testFeeder', {"component1":{"test":1},"component2":{"bullseye":5}, "norman":"powder"})
	print 'What was that MD?', test.get('feeder', 'testFeeder')
	print 'List something.', test.listAll('feeder')
	print 'Full feeder get back', test.get('feeder','testFeeder')
	# Cleanup:
	shutil.rmtree('./testFileStore/')
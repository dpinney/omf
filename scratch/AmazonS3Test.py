#!/usr/bin/env python

import boto, json, traceback

from boto.s3.connection import S3Connection
from boto.s3.key import Key

# We're running as dwpTestUser
conn = S3Connection('AKIAIFNNIT7VXOXVFPIQ', 'stNtF2dlPiuSigHNcs95JKw06aEkOAyoktnWqXq+')

## Create a bucket.
# bucket = conn.create_bucket('ohdwptestthisbucket')

# Get a reference to the bucket.
bucket = conn.get_bucket('ohdwptestthisbucket')

# Get a specific key.
k = bucket.get_key('foobar')
print 'Foobar bucket contains:', k.get_contents_as_string()

# List all keys, get all metadata.
keyList = bucket.list()
for key in keyList:
	print 'Key name:', key.name
	print '\tMD:', bucket.get_key(key).metadata

# Testing for a specific key.
def exists(keyName):
	return bucket.get_key(keyName) is not None
print 'FooNotThere exists?', exists('fooNotThere')
print 'foobar exists?', exists('foobar')

# Write a key
bucket.new_key('testkey1').set_contents_from_string('{"mock":"tortoise"}')

# Read key
print 'testkey1 Contents:', bucket.get_key('testkey1').get_contents_as_string()

# Delete that key
bucket.delete_key('testkey1')

class S3filestore:
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
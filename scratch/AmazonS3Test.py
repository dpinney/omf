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


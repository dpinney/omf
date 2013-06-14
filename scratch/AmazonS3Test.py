#!/usr/bin/env python

import boto

from boto.s3.connection import S3Connection
from boto.s3.key import Key
conn = S3Connection('AKIAIBEYABXHAKRQCB5Q', 'yaright')
bucket = conn.create_bucket('ohdwptestthisbucket')
k = boto.s3.key.Key(bucket)
k.key = 'foobar'
k.set_contents_from_string('Hello David here we are.')
print k.get_contents_as_string()
#!/usr/bin/env python

import json

with open('json/small.json','r') as smallJson:
	small = json.loads(smallJson.read())

print small.keys()
print small['nodes']
print small['links']
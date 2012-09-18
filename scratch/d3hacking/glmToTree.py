#!/usr/bin/env python

''' We're going to try putting the graph format into a radial format that D3 will like.'''

import json
from pprint import pprint

with open('small.json','r') as smallFile:
	smallJson = json.load(smallFile)

pprint(smallJson)
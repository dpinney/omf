#!/usr/bin/env python
# encoding: utf-8

"""
GLMParser-nonrec.py
Created by David Pinney on 2012-05-07.
"""

import sys
import getopt
import re

def main(argv=None):
	pass

#Take in a glm file as string and return a dict of all the objects.
def parse(glmData):
	# Strip comments.
	data = re.sub(r'\/\/.*\n', '', glmData)
	
	# try to grab all the objects
	# NOTE: this is a hack, because we're using the whitespace to grab only objects that aren't nested.
	objects = re.findall(r'^object\s+\w+\s+\{.*?\}',data,re.M|re.S)
	
	# Turn all the objects into dicts.
	dictList = []
	count = -1
	for x in objects:
		count += 1
		splitPoint = x.find('{')
		# Find all the properties.
		props = x[splitPoint+1:]
		
		# Tear out nested objects.
		cleanProps = props.replace('\n','').replace('\r','').replace('\t','')
		cleanerProps = re.sub(r'\{.*?\}', 'XXX', cleanProps, re.M|re.S)
		
		#Split it up.
		splitCleanProps = cleanerProps.split(';')[:-1]
		try:
			obj = dict(map(lambda y:y.split(None, 1), splitCleanProps))
		except:
			print splitCleanProps
		
		#Add the type
		obj['type'] = x[:splitPoint].split()[1]
		dictList.append(obj)
	
	return dictList

if __name__ == "__main__":
	main()

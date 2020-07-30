#!/usr/bin/env python

'''
Count the number of lines of code in this project. Ignores the data stores and libraries, etc.
2.5 kLOC as of 2012-10-24.
9.6 kLOC as of 2013-06-10.
98 kLOC as of 2020-07-24.
'''

import os, pathlib
import omf

def cleanList(inList):
	goodSuffixes = ['py','js','htm','html']
	prefix = pathlib.Path(omf.omfDir)
	libraries = [prefix / 'static/d3.v3.js', prefix / 'static/highcharts.src.js', prefix / 'static/jquery-1.9.1.js']
	return [x for x in inList if (x.split('.')[-1] in goodSuffixes and x not in libraries)]

def lineCount(fileName):
	lines = 0
	try:
		f = open(fileName)
		for line in f:
			lines += 1
	except:
		pass
	finally:
		f.close()
	return lines

def fileNameAndLineCount(fileName):
	return [fileName, lineCount(fileName)]

def recursiveFileList(direct):
	fileList = []
	for x in os.walk(direct):
		fileList = fileList + [x[0] + '/' + fPath for fPath in x[2]]
	return fileList

allSource = cleanList(recursiveFileList(omf.omfDir))
lineCountList = list(map(lineCount, allSource))

print('Per-file breakdown:')
for pair in map(fileNameAndLineCount, allSource):
	print(pair[1], 'lines in', pair[0])

print('Total:', sum(lineCountList), 'lines.')

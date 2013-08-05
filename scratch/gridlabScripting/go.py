#!/usr/bin/env python

import webbrowser, os, sys, json
os.chdir('../..')
sys.path.append(os.getcwd())
import storage, feeder, analysis

thisFile = os.path.realpath(__file__)
outputPath = os.path.join(os.path.split(thisFile)[0],'output.html')

print outputPath

with open(outputPath,'w') as output:
	output.write('<head></head><body>Here we go Python.</body>')

webbrowser.open_new('file://' + os.path.abspath(outputPath))
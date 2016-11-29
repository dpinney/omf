# Imports.
import os, sys, json
from os.path import join as pJoin
import subprocess
import shutil
import math
import pprint as pprint

# Read matout.txt and format data into dictionaries.
outData = {
	'voltages': [[],[]]	,
	'power' : [[],[]],
	'power_im' : [[],[]]
	}
gennums=[]
todo = None
with open("outData/matout.txt") as f:
	for i,line in enumerate(f):
		# Determine what type of data is coming up.
		if "How many?" in line:
			todo = "count"
		elif "Generator Data" in line:
			todo = "gen"
			lineNo = i
		elif "Bus Data" in line:
			todo = "node"
			lineNo = i
		elif "Branch Data" in line:
			todo = "line"
			lineNo = i
		# Parse lines.
		line = line.split(' ')
		line = filter(lambda a: a!= '', line) # separate a line of text into an array by spaces
		if todo=="count":
			if "Buses" in line:
				busCount = int(line[1])
			elif "Generators" in line:
				genCount = int(line[1])
			elif "Loads" in line:
				loadCount = int(line[1])
			elif "Branches" in line:
				branchCount = int(line[1])
			elif "Transformers" in line:
				transfCount = int(line[1])
				todo = None
		elif todo=="gen":
			if i>(lineNo+4) and i<(lineNo+4+genCount+1): 
				# gen bus numbers.
				gennums.append(line[1])
			elif i>(lineNo+4+genCount+1):
				todo = None
		elif todo=="node":
			if i>(lineNo+4) and i<(lineNo+4+busCount+1): 
				# voltage
				if line[0] in gennums: comp="gen"
				else: comp="node"
				outData['voltages'][0].append(comp+str(line[0]))
				outData['power'][0].append(comp+str(line[0]))
				outData['power_im'][0].append(comp+str(line[0]))
				outData['voltages'][1].append(line[1])
				outData['power'][1].append(line[3])
				outData['power_im'][1].append(line[4])
			elif i>(lineNo+4+busCount+1):
				todo = None
		elif todo=="line":
			if i>(lineNo+4) and i<(lineNo+4+branchCount+1): 
				# power
				outData['power'][0].append("line"+str(line[0]))
				outData['power_im'][0].append("line"+str(line[0]))
				outData['power'][1].append(line[3])
				outData['power_im'][1].append(line[4])
			elif i>(lineNo+4+branchCount+1):
				todo = None
				
# Print results.
pprint.pprint(outData)
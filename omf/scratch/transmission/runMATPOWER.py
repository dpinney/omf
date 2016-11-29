'''
Matpower reference manual: https://drive.google.com/file/d/0Bzhw95nTE7NOOW1FOEhXQzdUazQ/view?usp=sharing
'''

# Imports.
import os, sys, json
from os.path import join as pJoin
import subprocess
import shutil
import math

# Create inoput data.
inputDict = {
	"algorithm" : "FDBX",
	"model" : "DC",
	"iteration" : 10,
	"tolerance" : math.pow(10,-8),
	"genLimits" : 0,
	}

# Set and make directories.
workDir = os.getcwd()
inDir = pJoin(workDir,'inData')
outDir = pJoin(workDir,'outData')
if not os.path.exists(outDir):
	os.makedirs(outDir)
caseFile = 'case9.m'.strip('.m')
algorithm = inputDict.get("algorithm","NR")
pfArg = "\'pf.alg\', \'"+algorithm+"\'"
modelArg = "\'model\', \'"+inputDict.get("model","AC")+"\'"
iterCode = "pf."+algorithm[:2].lower()+".max_it"
pfItArg = "\'"+iterCode+"\', "+str(inputDict.get("iteration",10))
pfTolArg = "\'pf.tol\', "+str(inputDict.get("tolerance",math.pow(10,-8)))
pfEnflArg = "\'pf.enforce_q_lims\', "+str(inputDict.get("genLimits",0))
out = "\'out.all\', "+str(1)
mpoptArg = "mpopt = mpoption("+pfArg+", "+modelArg+", "+pfItArg+", "+pfTolArg+", "+pfEnflArg+", "+out+"); "

# Smart switch to matpower directory.
class cd:
	"""Context manager for changing the current working directory"""
	def __init__(self, newPath):
		self.newPath = os.path.expanduser(newPath)

	def __enter__(self):
		self.savedPath = os.getcwd()
		os.chdir(self.newPath)

	def __exit__(self, etype, value, traceback):
		os.chdir(self.savedPath)

# Run matpower commands.
with cd(pJoin(inDir, "matpower6.0b1")):
	# command = "octave runpf.m; runpf(\''case9\'')"
	# command = "octave --no-gui --eval 'runpf(\''case9\'')' > "+"/home/dev/Desktop/out.txt"
	# command = "octave --no-gui --eval \""+"results = runpf(\'"+caseFile+"\'); results.success;\""
	command = "octave --no-gui --eval \""+mpoptArg+"runpf(\'"+caseFile+"\', mpopt)\" > "+"/home/dev/Desktop/matout.txt" # Can't save in scratch due to windows sharing.
	print "command:", command
	proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()

# Write output.
shutil.copy("/home/dev/Desktop/matout.txt", pJoin(workDir,'outData', 'matout.txt'))
os.remove("/home/dev/Desktop/matout.txt")
f = open("outData/matout.txt")
contents = f.read()
print "\n\nMATOUT.TXT CONTENTS: \n*********************************************************************************************"
print contents, "\n*********************************************************************************************"

'''
Useful links:
1) Command linehttps://www.gnu.org/software/octave/doc/v4.0.1/Command-Line-Options.html
'''

# Imports.
import os, sys, json
from os.path import join as pJoin
import subprocess

# Set and make directories.
workDir = os.getcwd()
inDir = pJoin(workDir,'inData')
outDir = pJoin(workDir,'outData')
if not os.path.exists(outDir):
	os.makedirs(outDir)

# Functions.
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

# Run matpower.
with cd(pJoin(inDir, "matpower6.0b1")):
	# command = "octave runpf.m; runpf(\''case9\'')"
	command = "octave --no-gui && runpf(\''case9\'')"
	proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
print out
''' Put me in a directory with all the TMY2s and run me to rename them according to their state and city. '''

import os

allNames = os.listdir(".")[1:]

for fName in allNames:
	firstLine = open(fName).readline().split()
	newName = firstLine[2]+"-"+firstLine[1] + ".tmy2"
	print fName, newName, firstLine
	os.rename(fName,newName)
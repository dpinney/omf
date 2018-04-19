
import json, math, random, datetime, os
from os.path import join as pJoin
import csv
import collections


randomNamesList = []
regularNamesList = []

omfDir='C:/Users/Tuomas/SkyDrive/omf'
FNAME=pJoin(omfDir,'omf','scratch','anonymization','randomNames', 'voltDump.csv')
with open(FNAME, "r") as inFile:
	voltDump = csv.reader(inFile, delimiter=',')
	voltDump.next()
	for row in voltDump:
		randomNamesList.append(row[1:])


omfDir='C:/Users/Tuomas/SkyDrive/omf'
FNAME=pJoin(omfDir,'omf','scratch','anonymization','original', 'voltDump.csv')
with open(FNAME, "r") as inFile:
	voltDump = csv.reader(inFile, delimiter=',')
	voltDump.next()
	for row in voltDump:
		regularNamesList.append(row[1:])

# reg = set(regularNamesList)
# ran = set(randomNamesList)

# compare = lambda x, y: collections.Counter(x) == collections.Counter(y)

# compare(reg, ran)

print(regularNamesList == randomNamesList)
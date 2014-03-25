''' See what the performance looks like for readings lots of files.
	
	Assuming 10,000 analyses (high coop estimated volume) then listing and paging MD takes
	only 0.4 seconds total.
'''

import os, json, timeit, shutil


'''
How many analyses do we expect to get?
900 coops * 1 user * 10 analyses. Let's say 10,000.
'''

TARGET = 10000

testMd = {
	"status": "postRun", 
	"climate": "IL-TAYLORVILLE", 
	"name": "admin_ACEC Year", 
	"simStartDate": "2012-06-01", 
	"simLengthUnits": "hours", 
	"created": "2013-10-03 11:59:24.514000", 
	"sourceFeeder": "ABEC Frank LO Houses", 
	"simLength": 8760, 
	"monVars": {
			"opAndMaintCost": "1000", 
			"distrCapacityRate": "20", 
			"distrEnergyRate": "0.11", 
			"equipAndInstallCost": "30000", 
			"reportType": "monetization"
	}, 
	"runTime": "0:00:20"
}

# File Setup
if 'testDir' not in os.listdir('.'):
	os.mkdir('testDir')
	for i in xrange(TARGET):
		os.mkdir('testDir/' + str(i))
		with open('testDir/' + str(i) + '/metadata.json','w') as mdFile:
			json.dump(testMd,mdFile)

# Need file list.
allDirs = os.listdir('testDir')

# Test Listing the Directory: TAKES ABOUT 0.4 SECONDS.
print 'ListingDir Time:', min(timeit.Timer('os.listdir("testDir")', setup='import os').repeat(7, 100))

# Test reading one "page" of results: TAKES ONLY 0.4 SECONDS.
def readOnePage():
	allData = []
	for i in xrange(30):
		with open('testDir/' + str(i) + '/metadata.json','r') as inFile:
			allData.append(json.load(inFile))
print 'Getting JSON in for one page:', min(timeit.Timer('readOnePage()', setup='from __main__ import os, json, readOnePage').repeat(7, 100))

# Cleanup func.
cleanup = True
if cleanup:
	shutil.rmtree('testDir')

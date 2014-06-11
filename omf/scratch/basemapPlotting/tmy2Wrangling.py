import os, json

if 'tmy2Data.json' in os.listdir('.'):
	with open('tmy2Data.json','r') as inFile:
		points = json.load(inFile)
else:
	# Basic Setup
	baseDir = '/Users/dwp0/Desktop/TMY2-Full/'
	names = os.listdir(baseDir)

	# Collect the first lines:
	firstLines = []
	testName = names[0]
	for name in names:
		with open(baseDir + name,'r') as testFile:
			firstLines.append(testFile.readline())

	# Turn these into (lon, lat, elev) points
	points = []
	for tmy in firstLines:
		breakDown = tmy.split()
		lat = 1.0*float(breakDown[5]) + float(breakDown[6])/60.0
		lon = -1.0*float(breakDown[8]) + float(breakDown[9])/60.0
		ele = float(breakDown[10])
		points.append((lon,lat,ele))
		#print (lon,lat,ele)
	
	with open('tmy2Data.json','w') as outFile:
		json.dump(points, outFile)
''' RF Coverage Model'''

import json, os, sys, tempfile, webbrowser, shutil, subprocess, traceback, requests, tempfile, xml.etree.ElementTree as ET
from zipfile import ZipFile
from os.path import join as pJoin
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

#Imaging library
from PIL import Image

# Model metadata:
tooltip = "The rfCoverage model provides the "
modelName, template = metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	
	sourceQth = [
		"Source Name",
		str(inputDict['towerLatitude']),
		str(inputDict['towerLongitude']),
		str(inputDict['towerHeight']) + 'm'
		]

	with open(pJoin(modelDir, inputDict['qthFile']),'w') as qthFile:
		for i in sourceQth:
			qthFile.write(i)
			qthFile.write("\n")

	#Which to get user entry and which to autopopulate
	sourceLrp = [
		"15.000 ; Earth Dielectric Constant (Relative permittivity)",
		"0.005 ; Earth Conductivity (Siemens per meter)",
		"301.000 ; Atmospheric Bending Constant (N-units)",
		str(inputDict['frequency']),
		"5 ; Radio Climate",
		str(inputDict['polarization']),
		"0.50 ; Fraction of situations (50 % of locations)",
		"0.90 ; Fraction of time (90% of the time)",
		"150000.0 ; Effective Radiated Power (ERP) in Watts (optional)"
		]

	with open(pJoin(modelDir, inputDict['lrpFile']),'w') as lrpFile:
		for i in sourceLrp:
			lrpFile.write(i)
			lrpFile.write("\n")

	'''
	#get the terrain files and convert to sdf on as needed basis. Will not need if all are stored in static
	#longitude max = 180W
	#longitude min = 043W
	#try +/- 5 for the 
	#latitude min = 10N
	#latitude max = 60N
	response = requests.get("https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/North_America/N20W079.hgt.zip")
	with tempfile.TemporaryFile() as tmp:
		tmp.write(response.content)
		with ZipFile(tmp, 'r') as zipper:
			zipper.extractall(modelDir)
			args = ["srtm2sdf", "N20W079.hgt"]
			subprocess.Popen(args).wait()'''

	#create the image file of the coverage
	#need to figure out where sdf will live
	args = ["splat", "-t", pJoin(modelDir, inputDict['qthFile']), "-L", "10", "-metric", "-o", pJoin(modelDir, "coverageMap.ppm"), "-kml", "-d", "/home/erik/omf/omf/scratch/commsModeling/sdfFiles", "-ngs", "-db", "90"]
	subprocess.Popen(args).wait()

	#Convert the image file to use in leaflet
	im = Image.open(pJoin(modelDir, "coverageMap.ppm"))
	im.save(pJoin(modelDir,"coverageMap.png"))

	#parse kml for image bounding box
	kml = pJoin(modelDir, "coverageMap.kml")
	tree = ET.parse(kml)
	root = tree.getroot()
	all_descendants = list(tree.iter())
	for i in all_descendants:
		if i.tag == '{http://earth.google.com/kml/2.1}south':
			south = i.text
		elif i.tag == '{http://earth.google.com/kml/2.1}north':
			north = i.text
		elif i.tag == '{http://earth.google.com/kml/2.1}east':
			east = i.text
		elif i.tag == '{http://earth.google.com/kml/2.1}west':
			west = i.text
	# Stdout/stderr.
	outData = {}
	outData['towerLatitude'] = inputDict['towerLatitude']
	outData['towerLongitude'] = inputDict['towerLongitude']
	with open(pJoin(modelDir,"coverageMap.png"),"rb") as inFile:
		outData["coverageMap"] = inFile.read().encode("base64")
	outData['north'] = north
	outData['south'] = south
	outData['east'] = east
	outData['west'] = west
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	qthFile = "tx1.qth"
	lrpFile = "tx1.lrp"
	defaultInputs = {
		"modelType": modelName,
		"towerLatitude": "36.42708056",
		"towerLongitude": "103.48500000",
		"towerHeight":"50",
		"frequency":"900.000",
		"polarization":"0",
		"qthFile": qthFile,
		"lrpFile": lrpFile
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
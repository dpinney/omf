import sys, os, sys, json, copy
from os.path import join as pJoin
from matplotlib import pyplot as plt
import subprocess, random, webbrowser
import pprint as pprint

# OMF imports
import omf.feeder as feeder
from omf.solvers import gridlabd

#ask what feeders do, what their format is, and how they affect how the code is run, how they combine into Poleandhazard.json
#Retrieve user inputted variables from omf/data/models/admin/allInputData.json   FIND WHERE web.py DEPOSITS uploaded files!
#Combine the two: feeders and user data and package them into a format for GFM

#def prepGFMInput(feeder, poleData, weatherImpacts):
	#helper function for runGFM() method, meant to be run like runGFM(prepGFMInput())
	#feeder, poleData, weatherImpacts are all file locations

	#Retrieve Feeder data?????
	#Retrieve Pole data(user uploaded)assume correct?
	#Retrieve Weather Impacts(User uploaded)  ex: WindGrid_lpnorm_example.asc assume correct?
	#Combine everything into something that resembles "_fragility_input_example"
	#Save this modified json to disk in the "../../solvers/GFM" as arbitrary name
	#return filename including .filetype



def GFMPrep():
	fragIn = {}

	with open(pJoin("../../", 'solvers','gfm', "_fragility_input_example.json"), "r") as fragInBase:
		fragInputBase = json.load(fragInBase)

	fragIn['assets'] = []
	fragIn['hazardFields'] = fragInputBase['hazardFields']
	fragIn['responseEstimators'] = fragInputBase['responseEstimators']

	baseAsset = fragInputBase['assets'][1]

	with open(pJoin('../../data', 'model', 'admin', 'Automated Testing of _resilientDist', "Olin Barre Geo.omd"), "r") as jsonIn:
		feederModel = json.load(jsonIn)

	for key in feederModel['tree'].keys():
		asset = copy.deepcopy(baseAsset)
		asset['id'] = key
		if "longitude" in feederModel['tree'][key] and "latitude" in feederModel['tree'][key]:
			asset['assetGeometry']['coordinates'] = [feederModel['tree'][key]['longitude'], feederModel['tree'][key]['latitude']]
		fragIn['assets'].append(asset)

	with open("data.json", "w") as outFile:
		json.dump(fragIn, outFile, indent=4)	

def checkInput():
	with open(pJoin("../../data/Model/admin/Automated Testing of _resilientDist/allInputData.json"), "r") as fragOutBase:
		fragOutBase = json.load(fragOutBase)

	test = json.loads(fragOutBase["poleData"])
	print test["assets"]

	with open(pJoin("../../", 'solvers','gfm', "_fragility_input_example.json"), "r") as fragInBase:
		fragInputBase = json.load(fragInBase)
	#print fragInputBase["assets"]


def runGFM(inputFileName):
	os.chdir("../../solvers/GFM")
	proc = subprocess.Popen(['java','-jar','Fragility.jar', inputFileName, 'out.json'])

#def runGridLabD(glmFile):
	#Calls gridlabd binary, gridlabd.bin and gets obtains line resistance and impedance data, is this based on feeders? what inputs should the binary take? study this more
	#outputs line_codes.json
	#return line_codes.json file location

#def prepRDTInput():
	# combines line_codes.json, user inputted data from html page in allInputsFile.json, and scenarios.json in RDT input format, name it rdtInput.json
	#return file name including .filetype

def runRDT(inputFileName):
	#outputs 'out.json' which is rdtOutput.json in specs
	os.chdir("../../solvers/rdt")
	proc = subprocess.Popen(['java','-jar','micot-rdt.jar', '-c', inputFileName, '-e', 'out.json'])





def resDist():
	gfmInput = prepGFMInput()
	runGFM(gfmInput)
	runGridLabD(PLACEhOLDER)
	rdtInput = prepRDTInput()
	runRDT(rdtInput)
	runGridLabD(PLACEHOLDER)




def runExample(toRun):
	if(toRun == "rdt"):
		os.chdir("../../solvers/rdt")
		proc = subprocess.Popen(['java','-jar','micot-rdt.jar', '-c', 'example.json', '-e', 'out.json'])

	elif(toRun == "gfm"):
		os.chdir("../../solvers/GFM")
		proc = subprocess.Popen(['java','-jar','Fragility.jar', '../../scratch/LPNORM Integration Code/data.json', 'out.json'])

if __name__=='__main__':
	#runExample("gfm")
	#GFMPrep();
	checkInput()
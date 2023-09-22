'''Calculate the Impacts of Intervention on Outage Incidence'''
import string
import pandas as pd
from random import random, seed
import numpy as np
import networkx as nx

# OMF imports
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.comms import createGraph

# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
tooltip = "This is a stub for the creation of new models. Update this description to match your model's purpose."
hidden = True # Change to False to make visible in the omf's "new model" list
#hidden = False

def obDictToDf(propertyName, obTypes, obDict):
	''' Returns a dataframe constructed by concatenating together series 
		stored in each circuit object in obDict, accessed with the key propertyName.
		Only uses series from circuit objects whose type accessed with the key 'object'
		is contained in obTypes.		
		
		obDict is expected to be a dictionary with keys in the format obType.obName 
		(e.g. load.load_2060) whose corresponding values are dictionaries
		with circuit object properties such as 'name':'load_2060' and 'object':'load' as its items.
	''' 
	types = [obTypes] if type(obTypes) == string else obTypes
	seriesList = [ob[propertyName] for ob in obDict.values() if ob['object'] in types]
	df = pd.concat(seriesList, axis = 'columns')
	return df

def addDfToObDict(propertyName, df, obDict):
	''' Breaks df into individual columns represented as series and adds those columns to the properties of
		circuit objects with corresponding names in obDict. 
		
		obDict is expected to be a dictionary with keys in the format obType.obName 
		(e.g. load.load_2060) whose corresponding values are dictionaries
		with circuit object properties such as 'name':'load_2060' and 'object':'load' as its items. 
		
		propertyName is used as the key to access a series.

		For example, if a dataframe of outage data without intervention is provided as df,
		the string 'outageNoInterv' might be provided as propertyName. Then once this function is called, 
		the column of outage data without intervention for a load called load.load2060 can be accessed with
		obDict['load.load2060']['outageNoInterv'] 
	'''
	seriesList = [df.loc[:,i] for i in df.columns]
	for series in seriesList:
		obKey = series.name
		if propertyName in obDict[obKey].keys():
			raise Exception(propertyName+' is already a property')
		else:
			obDict[obKey][propertyName] = series

def getObjects(omdFilePath):
	''' Returns a dictionary of circuit objects and their properties from a given omd file
		with a list of downline loads and a list of downline objects (including loads) 
		added to their properties with the keys 'downlineLoads' and 'downlineObs'.
		
		The specific return format is a dictionary with keys representing circuit objects
		in the format of 'obType.obName' (e.g. load.load_2060) which correspond to values that are 
		dictionaries of circuit object properties such as:
		'name':'load_2060', 'object':'load', 'downlineLoads':[], 'downlineObs':[]
		'''	
	omd = json.load(open(omdFilePath))
	obDict = {}
	for ob in omd.get('tree',{}).values():
		obType = ob['object']
		obName = ob['name']
		key = obType+'.'+obName
		obDict[key] = ob
	del omd

	digraph = createGraph(omdFilePath)
	nodes = digraph.nodes()
	namesToKeys = {v.get('name'):k for k,v in obDict.items()}
	for obKey, ob in obDict.items():
		obType = ob['object']
		obName = ob['name']
		obTo = ob.get('to')
		if obName in nodes:
			startingPoint = obName
		elif obTo in nodes:
			startingPoint = obTo
		else:
			continue 
		successors = nx.dfs_successors(digraph, startingPoint).values()
		ob['downlineObs'] = []
		ob['downlineLoads'] = []
		for list in successors:
			for element in list:
				elementKey = namesToKeys.get(element)
				elementType = elementKey.split('.')[0]
				if elementKey not in ob['downlineObs']:
					ob['downlineObs'].append(elementKey)
				if elementKey not in ob['downlineLoads'] and elementType == 'load':
					ob['downlineLoads'].append(elementKey)
	del successors
	del namesToKeys
	del nodes
	del digraph
	return obDict

def createSimData(omdFilePath, troubledObjects, csvFilePath = None):
	'''	Creates timeseries outage data by probabilistically simulating outage status 
		of circuit objects and propagating those statuses to downline loads.
		Loads and other circuit objects are read from a given omd file and the types 
		of other circuit objects are specified by troubledObjects.

		If csvFilePath is provided, timeseries data is output at that location as a csv
		file with circuit objects in the format of 'obType.obName' (e.g. load.load_2060) as 
		column names and time in minutes as row indecies. Load object columns are grouped left
		with columns representing other circuit objects to the right of the load object columns.

		If csvFilePath isn't provided, a dictionary of circuit objects and their properties 
		from the omd file with the timeseries data added to their properties as series with 
		the key 'outageNoInterv'. The specific return format is a dictionary with keys 
		representing circuit objects in the format of 'obType.obName' (e.g. load.load_2060) 
		which correspond to values that are dictionaries of circuit object properties such as:
		'name':'load_2060', 'object':'load', 'outageNoInterv':(pandas series representation of 
		timeseries corresponding to load.load_2060)
	'''
	times = [i for i in range(0, 4*60+1, 15)]
	obDict = getObjects(omdFilePath)
	allLoadKeys		= [k for k,v in obDict.items() if v['object'] == 'load']	
	troubledObKeys 	= [k for k,v in obDict.items() if v['object'] in troubledObjects]
	dfLoads		= pd.DataFrame(np.ones((len(times),len(allLoadKeys))), dtype=int, index=times, columns=allLoadKeys)
	dfObjects	= pd.DataFrame(np.ones((len(times),len(troubledObKeys))), dtype=int, index=times, columns=troubledObKeys)

	midway = len(times)/2

	objIterRows = dfObjects.iterrows()
	prevIndex, row1 = next(objIterRows)
	for i, row in objIterRows:
		dfObjects.loc[i,:] = dfObjects.loc[prevIndex,:]
		dfLoads.loc[i,:] = dfLoads.loc[prevIndex,:]

		loadsToUpdate = set()
		for obKey, obStatus in row.items():
			threshold = (1.0-(abs(dfObjects.index.get_loc(i)-midway)/(1.05*midway)))/(midway*4)
			if random() <= threshold and obStatus == 1:
				dfObjects.at[i,obKey] = 0
				if obKey in dfLoads.columns:
					loadsToUpdate.add(obKey)
				else:
					loadsToUpdate.update(set(obDict[obKey]['downlineLoads']))
		for load in dfLoads.columns:
			if load in loadsToUpdate:
				dfLoads.at[i,load] = 0
		prevIndex = i
	
	dfConcat = pd.concat([dfLoads, dfObjects], axis='columns')
	if csvFilePath:
		dfConcat.to_csv(csvFilePath)
	else:
		addDfToObDict('outageNoInterv', dfConcat, obDict)
		return obDict

def OutObjToOutLoads(objDownstreamDict, objStatusDict): #Update this or get rid of it. Clarify Name
	''' Returns loads experiencing an outage based on the status of upstream circuit objects.
		loads not returned are considered not experiencing an outage'''
	if objDownstreamDict.keys() != objStatusDict.keys():
		raise Exception("objDownstreamDict and objStatusDict must have identical keys")
	outLoads = set()
	for obName in objDownstreamDict.keys():
		if objStatusDict[obName] == 0:
			outLoads.update(set(objDownstreamDict[obName]['downlineLoads']))
	return outLoads
	
def cleanIntegerInput(inputVal, defaultVal=0, minVal=float('-inf'), maxVal=float('inf')):
	''' Tries to return the inputVal cast to an integer. If unsuccessful, returns the defaultVal. 
		If inputVal is outside of bounds, set to closest bound.'''
	if minVal >= maxVal: 
		raise Exception("minVal must be < maxVal")
	try:
		return max(minVal,min(maxVal,int(inputVal)))
	except ValueError:
		return defaultVal


def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	outData = {}
 
	# Model operations goes here.
	omdFilePath = pJoin(omf.omfDir, "static", "publicFeeders", inputDict.get("feederName1")+'.omd')

	if inputDict.get("simOutageBool"):
		if inputDict.get("simRandomSeed") != "None":
			seed(int(inputDict.get("simRandomSeed")))
		troubledObj = []
		if inputDict.get("simLinesBool"):
			troubledObj.append('line')
		if inputDict.get("simTransformersBool"):
			troubledObj.append('transformer')
		obDict = createSimData(omdFilePath, troubledObj)
		seed()
	else:
		outageDataCSV = pJoin(omf.omfDir, "static", "testFiles", "restoration", inputDict.get("exampleFileName"))
		obDict = getObjects(omdFilePath)
		addDfToObDict('outageNoInterv', pd.read_csv(outageDataCSV,index_col=0), obDict)

	dfOutage = obDictToDf('outageNoInterv','load',obDict)	
	dfOutageIncidence = dfOutage.sum(axis=1,).map(lambda x:100*(1.0-(x/dfOutage.shape[1])))
	timeStep = int(dfOutageIncidence.index[-1])-int(dfOutageIncidence.index[-2])
	steps = cleanIntegerInput(inputDict.get("timeStepsInInterval",1), defaultVal = 1, minVal = 1, maxVal = dfOutageIncidence.size-1)
	dSpeedInterval = timeStep*steps

	outData["timeStep"] = timeStep
	outData["dSpeedInterval"] = dSpeedInterval
	outData["startTime"] = int(dfOutageIncidence.index[0])
	outData["endTime"] = int(dfOutageIncidence.index[-1])
	outData["outageIncidence"] = dfOutageIncidence.values.tolist()
	
	dfDisruptionSpeed = dfOutageIncidence.diff(steps).div(dSpeedInterval)
	outData["disruptionSpeed"] = dfDisruptionSpeed.fillna(0).values.tolist()

	del dfOutage
	del dfOutageIncidence
	# Model operations typically end here.

	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData


def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	omd_fn = "iowa240c1.clean.dss"
	ex_fn = "example.csv" # example file input


	#Uncomment below to generate a new ex_fn (overwrites old one; shared among instances) when a model is created
	#createSimData(
	#	omdFilePath = pJoin(omf.omfDir, "static", "publicFeeders", omd_fn+'.omd'), 
	#	troubledObjects = ['line'],
	#	csvFilePath = pJoin(omf.omfDir, "static", "testFiles","restoration", ex_fn),
	#)

	with open(pJoin(omf.omfDir, "static", "testFiles","restoration", ex_fn)) as ex_stream:
		ex_ins = ex_stream.read()

	defaultInputs = {
		"modelType": modelName,
		"date": "2019-07-01T00:00:00Z",
		"timeStepsInInterval":"1",
		"feederName1": omd_fn,
		"exampleFileName": ex_fn,
		"exampleFileContent": ex_ins,
	}

	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	try:
		shutil.copyfile(pJoin(__neoMetaModel__._omfDir, 'static', 'publicFeeders', defaultInputs['feederName1']+'.omd'), pJoin(modelDir, defaultInputs['feederName1']+'.omd'))
	except:
		return False
	return creationCode

@neoMetaModel_test_setup
def _debugging():
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
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	_debugging()

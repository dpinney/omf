''' Performs a cost-benefit analysis for a utility or cooperative member interested in 
controlling behind-the-meter distributed energy resources (DERs).'''

import warnings
# warnings.filterwarnings("ignore")

import shutil, datetime, csv
from os.path import join as pJoin

# OMF imports
from omf import feeder
from omf.models.voltageDrop import drawPlot
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
from omf.models import vbatDispatch as vb
from omf.solvers import reopt_jl as RE

# Model metadata:
tooltip = ('The derUtilityCost model evaluates the financial costs of controlling behind-the-meter '
	'distributed energy resources (DERs) using the NREL renewable energy optimization tool (REopt) and '
	'the OMF virtual battery dispatch module (vbatDispatch).')
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	# Delete output file every run if it exists
	outData = {}		
	solar = inputDict['solar'] 
	generator = inputDict['generator']
	battery = inputDict['battery']
	outData['solar'] = inputDict['solar']
	outData['generator'] = inputDict['generator'] ## TODO: make generator switch on only during outage?
	outData['battery'] = inputDict['battery']
	outData['year'] = inputDict['year']

	latitude = float(inputDict['latitude'])
	longitude = float(inputDict['longitude'])

	## Setting up the demand file (hourly kWh) and temperature file
	with open(pJoin(modelDir, 'demand.csv'), 'w') as f:
		f.write(inputDict['demandCurve'].replace('\r', ''))
	with open(pJoin(modelDir, 'demand.csv'), newline='') as f:
		demand = [float(r[0]) for r in csv.reader(f)]
		assert len(demand) == 8760

	with open(pJoin(modelDir, 'temp.csv'), 'w') as f:
		lines = inputDict['tempCurve'].split('\n')
		outData["tempData"] = [float(x) if x != '999.0' else float(inputDict['setpoint']) for x in lines if x != '']
		correctData = [x+'\n' if x != '999.0' else inputDict['setpoint']+'\n' for x in lines if x != '']
		f.write(''.join(correctData))
	assert len(correctData) == 8760
	
	outage = True if inputDict["outage"] == "on" else False

	## Run REopt and gather outputs for vbatDispath
	## TODO: Create a function that will gather the urdb label from a user provided location (city,state)
	#RE.run_reopt_jl(modelDir,inputFile,outages)
	RE.run_reopt_jl(path="/Users/astronobri/Documents/CIDER/reopt/inputs/", inputFile="UP_PV_outage_1hr.json", outages=outage) # UP coop PV 

	#with open(pJoin(modelDir, 'results.json')) as jsonFile:
#		results = json.load(jsonFile)

	#getting REoptInputs to access default input values more easily 
#	with open(pJoin(modelDir, 'REoptInputs.json')) as jsonFile:
#		reopt_inputs = json.load(jsonFile)

	if (outage):
		with open(pJoin(modelDir, 'resultsResilience.json')) as jsonFile:
			resultsResilience = json.load(jsonFile)
	
	## Run vbatDispatch with outputs from REopt
	#VB.new(modelDir)
	#modelDir = "/Users/astronobri/Documents/CIDER/omf/omf/data/Model/admin/meowtest"

	test = vb.work(modelDir,inputDict)
	print(test)
	#print(modDirvbatt)
	#vbattWork_out = vb.work(modelDir,vbattNew_out[1])

	# Model operations typically ends here.
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_1yr_Load.csv")) as f:
		demand_curve = f.read()
	with open(pJoin(__neoMetaModel__._omfDir,"static","testFiles","Texas_1yr_Temp.csv")) as f:
		temp_curve = f.read()
	defaultInputs = {
		"user" : "admin",
		"modelType": modelName,
		"latitude" : '39.7392358',
		"longitude" : '-104.990251',
		"year" : '2018',
		"analysis_years" : 25,
		"urdbLabel" : '612ff9c15457a3ec18a5f7d3',
		"demandCurve": demand_curve,
		"tempCurve": temp_curve,
		"outage": False,
		"solar" : "on",
		"battery" : "on",
		"generator" : "off",
		"created":str(datetime.datetime.now()),
		"load_type": "1",
		"number_devices": "2000",
		"power": "5.6",
		"capacitance": "2",
		"resistance": "2",
		"cop": "2.5",
		"setpoint": "22.5",
		"deadband": "0.625",
		"demandChargeCost":"25",
		"electricityCost":"0.06",
		"projectionLength":"15",
		"discountRate":"2",
		"unitDeviceCost":"150",
		"unitUpkeepCost":"5",
		"fileName": "Texas_1yr_Load.csv",
		"tempFileName": "Texas_1yr_Temp.csv",
		"modelType": modelName,
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def _debugging():
#def _tests():
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
	#_tests()
	#pass


"""import omf.models.vbatDispatch as vb

modelDir = "C:\\Users\\lisam\\Desktop\\Repositories\\omf\\omf\\data\\Model\\admin\testVbatt_CIDER"
[modDirvbatt, inputdict] = vb.new(modelDir)
vbattWork_out = vb.work(modelDir,vbattNew_out[1])"""

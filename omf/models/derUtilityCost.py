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
from omf.models import vbatDispatch as VB
from omf.solvers import reopt_jl as RE

# Model metadata:
tooltip = ('The derUtilityCost model evaluates the financial costs of controlling behind-the-meter '
	'distributed energy resources (DERs) using the NREL renewable energy optimization tool (REopt) and '
	'the OMF virtual battery dispatch module (vbatDispatch).')
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def castAddInputs(val1,val2):
	''' Casts string inputs to appropriate type and returns their sum. 
		If inputs are cast to floats, rounds their sum to avoid float subtraction errors.'''
	try:
		cast1 = int(val1)
		cast2 = int(val2)
		return cast1+cast2
	except ValueError:
		try:
			cast1 = float(val1)
			cast2 = float(val2)
            #Find longest decimal place of the numbers and round their sum to that place to avoid float arithmetic errors
			decPl1 = val1.strip()[::-1].find('.')
			decPl2 = val2.strip()[::-1].find('.')  
            #valX.strip() used instead of str(castX) because str(castX) may return scientific notation
			roundedSum = round(cast1+cast2,max(decPl1,decPl2,1))     
			return roundedSum
		except ValueError:
			return val1+val2

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	# Delete output file every run if it exists
	outData = {}		
	
	# Model operations goes here.
	#inputOne = inputDict.get("Demand Curve", 123)
	#inputTwo = inputDict.get("input2", 867)
	#output = str(castAddInputs(inputOne,inputTwo))
	#outData["output"] = output

	## Gather inputs, including demand file (hourly kWh)
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
	
	outage = True if inputDict["Outage"] == "on" else False

	## Run REopt and gather outputs
	#RE.run_reopt_jl(path,inputFile,outages)
	RE.run_reopt_jl(path="/Users/astronobri/Documents/CIDER/reopt/inputs/", inputFile="UP_PV_outage_1hr.json", outages=True) # UP coop PV 

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
		"demandCurve": demand_curve,
		"tempCurve": temp_curve,
		"fileName": "Texas_1yr_Load.csv",
		"tempFileName": "Texas_1yr_Temp.csv",
		"Outage": False,
		"created":str(datetime.datetime.now())
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
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
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
	#_tests()
	pass
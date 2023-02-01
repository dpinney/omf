from omf.models import cyberInverters
from omf.solvers.opendss import dssConvert
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *
import os

def getInputs(directory):
	files = os.listdir(directory)
	dss_fn = [file for file in files if 'dss' in file.lower()][0]
	pv_fn = [file for file in files if 'solar' or 'pv' in file.lower()][0]
	dev_fn = [file for file in files if 'device' or 'battery' in file.lower()][0]
	misc_fn = [file for file in files if 'misc' and 'csv' in file.lower()][0]
	bp_fn = [file for file in files if 'break' and 'csv' in file.lower()][0]
	return dss_fn, pv_fn, dev_fn, misc_fn, bp_fn
    
def contentOf(dir, fn=''):
	with open(os.path.join(dir, fn)) as fileContent:
		content = fileContent.read()
	return content
    
def inputDictFor(modelDir):
	dss_fn, pv_fn, dvc_fn, misc_fn, bp_fn = getInputs(modelDir)
	inputDict = {
		"simStartDate": "2019-07-01T00:00:00Z",
		"simLength": "7500",
		"simStepUnits": "seconds",
		"simEntryStep": "100",
		"feederName1": dss_fn[-4], # this is the .omd file (used by distnetviz.html and web.saveFeeder)
		"circuitFileNameDSS": dss_fn, # this is the .dss file (used by distText.html and web.saveFile)
		"loadPVFileName": pv_fn,
		"loadPVFileContent": contentOf(modelDir, pv_fn),
		"breakpointsFileName":bp_fn,
		"breakpointsFileContent": contentOf(modelDir, bp_fn),
		"miscFileName": misc_fn,
		"miscFileContent": contentOf(modelDir, misc_fn),
		"deviceFileName": dvc_fn,
		"deviceFileContent": contentOf(modelDir, dvc_fn),
		"includeBattery": "True",
		"modelType": "cyberInverters",
		"zipCode": "59001",
		"trainAgent": "False",
		"attackVariable": "None",
		"defenseVariable": "None",
		"hackStart": "250",
		"hackEnd": "650",
		"hackPercent": "50",
		"defenseAgentNames": "policy_ieee37_oscillation_sample,policy_ieee37_unbalance_sample"
	}
	return inputDict

# TODO: Figure out why the file names aren't resolving correctly. Should we hard-code cases/filenames?
# TODO: Why on earth is the simulation time vs attack start and end times failing assertions?
# TODO: Why aren't the pycigarOutput directories being created?
# Open Question: should any of this be integrated into defaults for cyberInverters.new() or cyberInverters.work()?

thisPath = os.path.dirname(os.path.abspath(__file__))
dirs = [os.path.join(thisPath, name) for name in os.listdir(thisPath) if os.path.isdir(os.path.join(thisPath,name)) and name.startswith('nreca')]
for modelDir in dirs:
	print('Creating model ' + modelDir)
	defaultInputs = inputDictFor(modelDir)
	creationCode = __neoMetaModel__.new(modelDir, inputDictFor(modelDir))
	try: 
		# Convert DSS file to OMD.
		dssConvert.dssToOmd(os.path.join(modelDir, defaultInputs["feederName1"]),os.path.join(modelDir, defaultInputs["feederName1"]))
		# Move in default files and empty results folders.
		os.mkdir(pJoin(modelDir,"PyCIGAR_inputs"))
		os.mkdir(pJoin(modelDir,"pycigarOutput"))
		for name in defaultInputs['defenseAgentNames'].split(','):
			shutil.copytree(
				pJoin(__neoMetaModel__._omfDir, "static", "testFiles", "pyCIGAR", name),
				pJoin(modelDir, "pycigarOutput", name)
			)
		# Generate .dss file from .omd so we can open text editor right out of the gate.
		with open(f'{modelDir}/{defaultInputs["feederName1"]}.omd', 'r') as omdFile:
			omd = json.load(omdFile)
		tree = omd['tree']
		niceDss = dssConvert.evilGldTreeToDssTree(tree)
		dssConvert.treeToDss(niceDss, f'{modelDir}/{defaultInputs["circuitFileNameDSS"]}')
	except:
		pass
	# Run the model.
	__neoMetaModel__.runForeground(modelDir)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelDir)
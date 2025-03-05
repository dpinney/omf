'''Return wildfire risk for custom geographic regions in the US.'''
import shutil
from pathlib import Path
from omf.models import __neoMetaModel__

# Model metadata:
tooltip = 'Return wildfire risk for custom geographic regions in the US.'
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

def work(modelDir, inputDict):
	outData = {}
	return outData

def new(modelDir):
	defaultInputs = {
		'modelType': modelName
    }
	creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
	return creationCode

def _tests():
    # Location
	modelLoc = Path(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		pass # No previous test results.
	# Create New.
	new(modelLoc)
	# Pre-run.
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)
	
if __name__ == '__main__':
	_tests()
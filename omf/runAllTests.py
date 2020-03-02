''' Walk the /omf/ directory, run _tests() in all modules. '''

import os, sys, subprocess, re
from pathlib import PurePath, Path


#IGNORE_FILES = ['runAllTests.py', 'install.py', 'setup.py', 'webProd.py', 'web.py', 'omfStats.py', '__init__.py']
INCLUDE_DIRS = ['omf', 'models']

IGNORE_FILES = [
'__init__.py',
'__neoMetaModel__.py',
'anomalyDetector.py',
'circuitRealTime.py',
'commsBandwidth.py',
'cvrDynamic.py',
'cvrStatic.py',
'cyberInverters.py',
'demandResponse.py',
'derInterconnection.py',
'disaggregation.py',
'evInterconnection.py',
'faultAnalysis.py',
'forecastLoad.py',
'forecastTool.py',
'gridlabMulti.py',
'microgridDesign.py',
'modelSkeleton.py',
'networkStructure.py',
'outageCost.py',
'phaseBalance.py',
'phaseId.py',
'pvWatts.py',
'resilientDist.py',
'rfCoverage.py',
#'smartSwitching.py',
'solarCashflow.py',
'solarConsumer.py',
'solarDisagg.py',
'solarEngineering.py',
'solarFinancial.py',
'solarSunda.py',
'storageArbitrage.py',
'storageDeferral.py',
'storagePeakShave.py',
'transmission.py',
'vbatDispatch.py',
'vbatStacked.py',
'voltageDrop.py',
'weatherPull.py',
'anomalyDetection.py',
'anonymization.py',
'calibrate.py',
'comms.py',
'cosim.py',
'cyberAttack.py',
'cymeToGridlab.py',
'distNetViz.py',
'feeder.py',
'forecast.py',
'geo.py',
'loadModeling.py',
'loadModelingAmi.py',
'milToGridlab.py',
'network.py',
'omfStats.py',
'runAllTests.py',
'weather.py',
'web.py',
'webProd.py',
]


def runAllTests(startingdir):
	os.chdir(startingdir)
	nextdirs = []
	misfires = {}
	tested = []
	not_tested = []
	main_regex = re.compile(r"\s*if\s+__name__\s+==\s+('|\")__main__('|\")\s*:")
	test_regex = re.compile(r"[^#]*_tests\(")
	for item in os.listdir('.'):
		if item not in IGNORE_FILES and item.endswith('.py'):
			with open(item) as f:
				file_content = f.readlines()
			has_main = False
			has_tests = False
			for line in file_content:
				if main_regex.match(line):
					has_main = True
				if has_main and test_regex.match(line):
					has_tests = True
					tested.append(item)
					print(f'********** TESTING {item} ************')
					p = subprocess.Popen(['python3', item], stderr=subprocess.PIPE)
					p.wait()
					if p.returncode:
						misfires[os.path.join(os.getcwd(), item)] = p.stderr.read()
					break
			if not has_tests:		
				not_tested.append(item)
		elif os.path.isdir(item) and item in INCLUDE_DIRS:
			nextdirs.append(os.path.join(os.getcwd(), item))
	for d in nextdirs:
		mis, t, nt = runAllTests(d)
		misfires.update(mis)
		tested.extend(t)
		not_tested.extend(nt)
	return misfires, tested, not_tested


def testRunner():
	os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".") # You can just run tests in a specific dir if you want
	misfires, tested, not_tested = runAllTests(os.getcwd())
	print('\n+------------------------+')
	print('\nTESTED MODULES REPORT')
	print('\n+------------------------+')
	print(f'Number of modules tested: {len(tested)}')
	print(tested)
	print(f'Number of tests failed: {len(misfires)}')
	for fname, err in misfires.items():
		print(PurePath(fname).name)
		for line in re.split(r'\n+', err.decode('utf-8')):
			print(line)
	if len(misfires) > 0:
		raise Exception # Fail if there were errors.
	print('\n+------------------------+')
	print('\nUNTESTED MODULES REPORT')
	print('\n+------------------------+')
	print(f'Number of untested modules: {len(not_tested)}')
	print(not_tested)


if __name__ == "__main__"  :
	testRunner()
''' Walk the /omf/ directory, run _tests() in all modules. '''

import os, sys, subprocess, re, platform
from pathlib import PurePath, Path


# These files aren't supposed to have tests
IGNORE_FILES = ['runAllTests.py', 'install.py', 'setup.py', 'webProd.py', 'web.py', 'omfStats.py', '__init__.py', 'phaseId.py']
# Only search these directories
INCLUDE_DIRS = ['omf', 'models']
# Different platforms like to name the python binary differently
PY_BIN_NAME = 'python3'

if platform.system()=='Windows':
	NO_WINDOWS_SUPPORT = ['solarDisagg.py', 'cymeToGridlab.py', 'rfCoverage.py', 'solarEngineering.py', 'transmission.py', 'phaseBalance.py', 'forecastTool.py', 'network.py']
	PY_BIN_NAME = 'python'
	IGNORE_FILES.extend(NO_WINDOWS_SUPPORT)

def _print_header(header):
	print('\n+------------------------+')
	print(f'\n{header.upper()}')
	print('\n+------------------------+')

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
					p = subprocess.Popen([PY_BIN_NAME, item], stderr=subprocess.STDOUT)
					p.wait()
					if p.returncode:
						misfires[os.path.join(os.getcwd(), item)] = 'ERR'
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
	_print_header('regular tests report')
	print(f'Number of modules tested: {len(tested)}')
	print(tested)
	_print_header('failed tests report')
	print(f'Number of tests failed: {len(misfires)}')
	print(misfires)
	_print_header('untested modules report')
	print(f'Number of untested modules: {len(not_tested)}')
	print(not_tested, '\n')
	if len(misfires) > 0:
		sys.exit(1) # trigger build failure.

if __name__ == "__main__"  :
	testRunner()

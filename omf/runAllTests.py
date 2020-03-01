''' Walk the /omf/ directory, run _tests() in all modules. '''

import os, sys, subprocess, re
from pathlib import PurePath, Path


IGNORE_FILES = ['runAllTests.py', 'install.py', 'setup.py', 'webProd.py', 'web.py', 'omfStats.py', '__init__.py']
INCLUDE_DIRS = ['omf', 'models']


# https://stackoverflow.com/questions/11640447/variable-length-lookbehind-assertion-alternatives-for-regular-expressions
# NEEDS TO BE:
# 1) "_tests()" must EXIST underneath the main section
# 2) "#": cannot come BEFORE "_tests()" on the same line (it can come after)

def runAllTests(startingdir):
	os.chdir(startingdir)
	nextdirs = []
	the_errors = 0
	misfires = {}
	not_tested = []
	executed_test_signature = re.compile(r"if\s+__name__\s+==\s+('|\")__main__('|\")\s*:\n[^#]*_tests\(")
	for item in os.listdir('.'):
		if item not in IGNORE_FILES and item.endswith('.py'):
			with open(item) as f:
				file_content = f.read()
			executed_test_mo = executed_test_signature.search(file_content)
			if executed_test_mo:
				print(f'********** TESTING {item} ************')
				p = subprocess.Popen(['python3', item], stderr=subprocess.PIPE)
				p.wait()
				if p.returncode:
					the_errors += 1
					misfires[os.path.join(os.getcwd(), item)] = p.stderr.read()
			else:
				not_tested.append(item)
		elif os.path.isdir(item) and item in INCLUDE_DIRS:
			nextdirs.append(os.path.join(os.getcwd(), item))
	for d in nextdirs:
		e, m, nt = runAllTests(d)
		the_errors += e
		misfires.update(m)
		not_tested.extend(nt)
	return the_errors, misfires, not_tested


def testRunner():
	os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".") # You can just run tests in a specific dir if you want
	i, mis, not_tested = runAllTests(os.getcwd())
	print('\n+------------------------+')
	print('\nTEST RESULTS')
	print('\n+------------------------+')
	print(i, 'tests failed:\n\n')
	for fname, err in mis.items():
		print(PurePath(fname).name)
		for line in re.split(r'\n+', err.decode('utf-8')):
			print(line)
	if i > 0:
		raise Exception # Fail if there were errors.
	print('+------------------------+')
	print('NOT TESTED')
	print('+------------------------+')
	print(not_tested)


if __name__ == "__main__"  :
	testRunner()
''' Walk the /omf/ directory, run _tests() in all modules. '''

import os, sys, subprocess, re, platform
from pathlib import PurePath, Path


# These files aren't supposed to have tests
IGNORE_FILES = ['runAllTests.py', 'install.py', 'setup.py', 'webProd.py', 'web.py', 'omfStats.py', '__init__.py']
# Only search these directories
INCLUDE_DIRS = ['omf', 'models']
# 3/1/20: These 3 files cause GitHub Actions to hang indefinitely when run with this test harness, so they must be run in their own separate processes
# 3/9/20: added phaseBalance.py. Ideally, we would not spawn any subprocess. Instead, every file would simply be imported and have its _tests()
# function called
FILES_THAT_HANG = ['networkStructure.py', 'smartSwitching.py', 'forecastTool.py', 'phaseBalance.py', 'evInterconnection.py']
IGNORE_FILES.extend(FILES_THAT_HANG)


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
					# Workaround for Windows hanging with too many pipes.
					if platform.system()=='Windows':
						p = subprocess.Popen(['python3', item])
					else:
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
	_print_header('regular tests report')
	print(f'Number of modules tested: {len(tested)}')
	print(tested)
	print(f'Number of tests failed: {len(misfires)}')
	print(list(misfires.keys()), '\n')
	for fname, err in misfires.items():
		print(PurePath(fname).name)
		for line in re.split(r'\n+', err.decode('utf-8')):
			print(line)
	if len(misfires) > 0:
		raise Exception # Fail if there were errors.
	_print_header('untested modules report')
	print(f'Number of untested modules: {len(not_tested)}')
	print(not_tested, '\n')
	if len(FILES_THAT_HANG) > 0:
		_print_header('special tests report')
		print(f'Number of special tests: {len(FILES_THAT_HANG)}')
		print(FILES_THAT_HANG)
		print(f'See additional output for special tests results')


if __name__ == "__main__"  :
	testRunner()
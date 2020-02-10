''' Walk the /omf/ directory, run _tests() in all modules. '''

import os, sys, subprocess, re
from pathlib import PurePath, Path

IGNORE_DIRS = ["data", ".git", "static", "templates", "testFiles", "scratch"]
IGNORE_FILES = ["runAllTests.py"] # to avoid infinite loop.

def runAllTests(startingdir):
	os.chdir(startingdir)
	nextdirs = []
	the_errors = 0
	misfires = {}
	test_function_signature = re.compile(r'def\s+_tests\s*\(')
	main_function_signature = re.compile(r"if\s+__name__\s+==\s+'__main__'")
	for item in os.listdir('.'):
		if item not in IGNORE_FILES and item.endswith('.py'):
			with open(item) as f:
				file_content = f.readlines()
			has_main = None
			has_tests = False
			for idx, line in enumerate(file_content):
				test_mo = test_function_signature.search(line)
				main_mo = main_function_signature.search(line)
				if main_mo:
					has_main = True
				if test_mo:
					has_tests = True
			if has_tests and has_main:
				print(f'********** TESTING {item} ************')
				p = subprocess.Popen(['python3', item], stderr=subprocess.PIPE)
				p.wait()
				if p.returncode:
					the_errors += 1
					misfires[os.path.join(os.getcwd(), item)] = p.stderr.read()
		elif os.path.isdir(item) and item not in IGNORE_DIRS:
			nextdirs.append(os.path.join(os.getcwd(), item))
	for d in nextdirs:
		e, m = runAllTests(d)
		the_errors += e
		misfires.update(m)
	return the_errors, misfires


def testRunner():
	os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".") # You can just run tests in a specific dir if you want
	i, mis = runAllTests(os.getcwd())
	print("\n\n+------------------------+")
	print("\n\nTEST RESULTS")
	print("\n\n+------------------------+")
	print(i, "tests failed:\n\n")
	for fname, err in mis.items():
		print(PurePath(fname).name)
		for line in re.split(r'\n+', err.decode('utf-8')):
			print(line)
	if i > 0:
		raise Exception # Fail if there were errors.

if __name__ == "__main__":
	testRunner()
''' Walk the /omf/ directory, run _tests() in all modules. '''

import os, sys, subprocess

IGNORE_DIRS = ["data", ".git", "static", "templates", "testFiles", "scratch"]
IGNORE_FILES = ["runAllTests.py"] # to avoid infinite loop.

def runAllTests(startingdir):
	os.chdir(startingdir)
	nextdirs = []
	the_errors = 0
	misfires = {}
	for item in os.listdir("."):
		if item not in IGNORE_FILES and item.endswith(".py"):
			with open(item) as f:
				file_content = f.read()
			if 'def _tests():' in file_content:
				print("********** TESTING", item, "************")
				p = subprocess.Popen(["python3", item], stderr=subprocess.PIPE)
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
		print(fname)
		print(err, "\n\n")
	if i>0: raise Exception # Fail if there were errors.

if __name__ == "__main__":
	testRunner()
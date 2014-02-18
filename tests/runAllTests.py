#TODO: walk the /omf/ directory, run _tests() in all modules.

import os, sys

# Probably will eventually remove some of these,
# especially scratch and calibration
IGNORE_DIRS = [
    "calibration",
    "data",
    ".git",
    "scratch",
    "static",
    "templates",
    "tests",
    "uploads",
    "venv",
    ]

from subprocess import call

def runAllTests(startingdir):
    os.chdir(startingdir)
    sys.path.append(".")
    nextdirs = []
    ignorefiles = ["milToGridlab.py", "storage.py"]
    the_errors = 0
    misfires = []
    for item in os.listdir("."):
        if item not in ignorefiles and item.endswith(".py") and "def _tests():" in open(item).read():
            # the_errors += call(["python", item])
            x = call(["python", item])
            the_errors += x
            misfires += [os.path.join(os.getcwd(), item)] if x else []
        elif os.path.isdir(item) and item not in IGNORE_DIRS:
            nextdirs.append(os.path.join(os.getcwd(), item))
    for d in nextdirs:
        e, m = runAllTests(d)
        the_errors += e
        misfires += m
    return the_errors, misfires

if __name__ == "__main__":
    os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
    # print "There were", runAllTests(os.getcwd()), "errors"
    i, mis = runAllTests(os.getcwd())
    print "there were", i, "errors"
    for m in mis:
        print m
    

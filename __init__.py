''' The Open Modeling Framework for Power System Simulation. '''

__version__ = 0.1

import os, sys

# Make sure we're on the path.
omfDir = os.path.dirname(__file__)
sys.path.append(omfDir)

# Import sub-packages.
import feeder
import solvers
import models
import milToGridlab
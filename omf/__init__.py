''' The Open Modeling Framework for Power System Simulation. '''

__version__ = 0.1

import os as _os, sys as _sys

# Make sure we're on the path.
omfDir = _os.path.dirname(__file__)
_sys.path.append(omfDir)

# Import sub-packages.
import feeder
import solvers
import models
import milToGridlab
import weather
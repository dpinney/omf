#!/usr/bin/env python

import os, sys, imp

# Path magic.
myDir = os.path.dirname(__file__)
sys.path.append(myDir)

# Grab all our submodules and include them whenever we include this package:
__all__ = [x for x in os.listdir(myDir) if not x.startswith('__')]

# Import of all the sub-modules:
import gridlabd
import nrelsam
#!/usr/bin/env python

import os, sys

# Path magic.
myDir = os.path.dirname(__file__)
sys.path.append(myDir)

# Grab all our submodules and include them whenever we include this package:
__all__ = [x for x in os.listdir(myDir) if not x.startswith('__')]

# Neat little import of all the sub-modules in the __all__ variable:
map(lambda x:__import__(x), __all__)
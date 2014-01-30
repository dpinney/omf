#!/usr/bin/env python

import os

# Grab all our submodules and include them whenever we include this package:
__all__ = [x for x in os.listdir('solvers') if not x.startswith('__')]

# Neat little import of all the sub-modules in the __all__ variable:
map(lambda x:__import__('solvers.' + x), __all__)
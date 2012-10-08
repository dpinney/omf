#!/usr/bin/env python

import os

# Grab all our submodules and include them whenever we include this package:
fileNames = os.listdir('reports')
reports = filter(lambda x:not x.startswith('__') and x.endswith('.py'), fileNames)
cleanReports = map(lambda x:x.replace('.py',''), reports)
__all__ = cleanReports

# Neat little import of all the sub-modules in the __all__ variable:
map(lambda x:__import__('reports.' + x), __all__)
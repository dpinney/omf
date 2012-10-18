#!/usr/bin/env python

import os

# Grab all our submodules and include them whenever we include this package:
fileNames = os.listdir('reports')
reportNames = filter(lambda x:not x.startswith('__') and x.endswith('.py'), fileNames)
cleanReports = map(lambda x:x.replace('.py',''), reportNames)
__all__ = cleanReports

# Neat little import of all the sub-modules in the __all__ variable:
map(lambda x:__import__('reports.' + x), __all__)

# Store all the HTML input templates for the reports:
__templates__ = {reportName:globals()[reportName].configHtmlTemplate for reportName in __all__}
#!/usr/bin/env python

import os

# Grab all our submodules and include them whenever we include this package:
__all__ = [x.replace('.py','') for x in os.listdir('studies') if not x.startswith('__') and x.endswith('.py')]

# Neat little import of all the sub-modules in the __all__ variable:
map(lambda x:__import__('studies.' + x), __all__)

# Store all the HTML input templates for the studies:
# __templates__ = {reportName:globals()[reportName].configHtmlTemplate for reportName in __all__}
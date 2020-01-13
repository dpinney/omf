''' Container for all models. '''

import os, sys

# Make sure this module is on the path regardless of where its imported from.
_myDir = os.path.dirname(os.path.abspath(__file__))
#sys.path.append(_myDir)

# Grab all our submodules and include them whenever we include this package:
__all__ = [x.replace('.py','') for x in os.listdir(_myDir)
	if x.endswith('.py') and not x.startswith('__')]

# Import of all the sub-modules:
# We have to keep this line of code because of the use of getattr()
for name in __all__: exec('from omf.models import ' + name)

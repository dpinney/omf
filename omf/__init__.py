''' The Open Modeling Framework for Power System Simulation. '''

__version__ = 0.2

import os as _os
import time

# Our OMF location
omfDir = _os.path.dirname(__file__)

# Get sub-modules
mod_files = [x for x in _os.listdir(omfDir) if x.endswith('.py')]
good_mods = set([x[0:-3] for x in mod_files if x not in ['__init__.py', 'web.py', 'webProd.py']])

# Import modules
for mod in good_mods:
	# start = time.process_time()
	__import__(mod)
	# print('{:f}'.format(time.process_time() - start), mod)

# Import sub-packages.
import solvers
# import models